"""FastAPI router for Plex integration endpoints"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.auth.endpoints import get_current_user
from app.api.v1.plex.schemas import (
    PlexConnectionCreate,
    PlexOAuthInitResponse,
    PlexSyncTriggerResponse,
)
from app.core.database import get_db
from app.domain.movies.models import Movie
from app.domain.plex.models import PlexConnection, PlexSyncRecord, PlexSyncStatus
from app.domain.plex.schemas import PlexConnectionResponse
from app.domain.tv_shows.models import Episode
from app.infrastructure.external_apis.plex.auth import PlexAuth
from app.tasks.plex import lock_plex_match, poll_plex_watched_status

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/plex", tags=["plex"])


@router.get("/connection", response_model=PlexConnectionResponse)
def get_connection(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Get the active Plex connection."""
    conn = db.query(PlexConnection).filter(PlexConnection.is_active.is_(True)).first()
    if conn is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No active Plex connection"
        )
    return conn


@router.post("/connection", response_model=PlexConnectionResponse, status_code=201)
def create_connection(
    payload: PlexConnectionCreate,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Create or replace the Plex connection using a manual token."""
    existing = db.query(PlexConnection).first()
    if existing:
        db.delete(existing)
        db.flush()

    conn = PlexConnection(
        server_url=payload.server_url,
        token=payload.token,
        is_active=True,
    )
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return conn


@router.delete("/connection", status_code=204)
def delete_connection(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Remove the Plex connection."""
    conn = db.query(PlexConnection).first()
    if conn:
        db.delete(conn)
        db.commit()


@router.get("/oauth/initiate", response_model=PlexOAuthInitResponse)
def oauth_initiate(
    redirect_uri: str,
    _: object = Depends(get_current_user),
):
    """Begin OAuth pin flow. Returns URL for user to visit and pin_id to poll."""
    auth = PlexAuth()
    pin_id, pin_code = auth.create_pin()
    oauth_url = auth.build_oauth_url(pin_code=pin_code, redirect_uri=redirect_uri)
    logger.info("Plex OAuth: initiated pin_id=%s", pin_id)
    return PlexOAuthInitResponse(oauth_url=oauth_url, pin_id=pin_id)


@router.get("/oauth/callback")
def oauth_callback(
    pin_id: int,
    server_url: str,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Poll for OAuth token after user authorises. Creates PlexConnection on success."""
    auth = PlexAuth()
    token = auth.poll_pin(pin_id=pin_id)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail="Authorisation pending — user has not approved yet",
        )

    existing = db.query(PlexConnection).first()
    if existing:
        db.delete(existing)
        db.flush()

    conn = PlexConnection(server_url=server_url, token=token, is_active=True)
    db.add(conn)
    db.commit()
    db.refresh(conn)
    logger.info("Plex OAuth: connection established server=%s", server_url)
    return PlexConnectionResponse.model_validate(conn)


@router.post("/sync", response_model=PlexSyncTriggerResponse, status_code=202)
def trigger_full_sync(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Dispatch a full Plex sync (watched status pull)."""
    conn = db.query(PlexConnection).filter(PlexConnection.is_active.is_(True)).first()
    if conn is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No active Plex connection"
        )

    task = poll_plex_watched_status.delay(conn.id)
    logger.info("Plex: manual sync dispatched task_id=%s", task.id)
    return PlexSyncTriggerResponse(task_id=task.id, message="Plex sync dispatched")


@router.get("/health")
def get_plex_health(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Return Plex sync health: not_found items and connection status."""
    not_found = (
        db.query(PlexSyncRecord)
        .filter(PlexSyncRecord.sync_status == PlexSyncStatus.NOT_FOUND)
        .all()
    )
    conn = db.query(PlexConnection).filter(PlexConnection.is_active.is_(True)).first()

    return {
        "connected": conn is not None,
        "not_found_count": len(not_found),
        "not_found_items": [
            {
                "id": r.id,
                "item_type": r.item_type,
                "item_id": r.item_id,
                "last_error": r.last_error,
            }
            for r in not_found
        ],
    }


def _get_tmdb_id_for_record(db: Session, item_type: str, item_id: int) -> Optional[str]:
    """Look up the TMDB ID from the source model for the given item."""
    if item_type == "movie":
        item = db.query(Movie).filter(Movie.id == item_id).first()
        return str(item.tmdb_id) if item and item.tmdb_id else None
    if item_type in ("tv_show", "episode"):
        item = db.query(Episode).filter(Episode.id == item_id).first()
        return str(item.tmdb_id) if item and item.tmdb_id else None
    return None


@router.post("/sync/{sync_record_id}", status_code=202)
def resync_item(
    sync_record_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Re-queue a single not_found item for Plex match resolution."""
    record = db.query(PlexSyncRecord).filter(PlexSyncRecord.id == sync_record_id).first()
    if record is None:
        raise HTTPException(status_code=404, detail="Sync record not found")

    item_type_str: str = record.item_type  # type: ignore[assignment]
    item_id_int: int = record.item_id  # type: ignore[assignment]
    tmdb_id = _get_tmdb_id_for_record(db, item_type_str, item_id_int)

    record.sync_status = PlexSyncStatus.PENDING  # type: ignore[assignment]
    db.commit()

    if tmdb_id:
        task = lock_plex_match.delay(
            record.item_type, record.item_id, tmdb_id, record.connection_id
        )
        return {"task_id": task.id, "message": "Re-sync queued"}

    return {"task_id": None, "message": "Status reset to pending — will sync on next poll"}
