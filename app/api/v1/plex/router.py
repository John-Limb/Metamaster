"""FastAPI router for Plex integration endpoints"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.auth.endpoints import get_current_user
from app.api.v1.plex.schemas import (
    PlexConnectionCreate,
    PlexMismatchItem,
    PlexOAuthInitResponse,
    PlexResolveRequest,
    PlexSyncTriggerResponse,
)
from app.core.database import get_db
from app.domain.movies.models import Movie
from app.domain.plex.models import PlexConnection, PlexSyncRecord, PlexSyncStatus
from app.domain.plex.schemas import PlexConnectionResponse
from app.domain.tv_shows.models import Episode, TVShow
from app.infrastructure.external_apis.plex.auth import PlexAuth
from app.infrastructure.external_apis.plex.client import PlexClient
from app.tasks.enrichment import enrich_movie_external
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
    """Poll for OAuth token after user authorises. Creates PlexConnection on success.

    Returns {"status": "pending"} (200) while the user hasn't approved yet so the
    frontend can keep polling without treating a non-2xx as a hard failure.
    Returns {"status": "connected", ...connection} once the token is obtained.
    """
    auth = PlexAuth()
    token = auth.poll_pin(pin_id=pin_id)
    if not token:
        return {"status": "pending"}

    existing = db.query(PlexConnection).first()
    if existing:
        db.delete(existing)
        db.flush()

    conn = PlexConnection(server_url=server_url, token=token, is_active=True)
    db.add(conn)
    db.commit()
    db.refresh(conn)
    logger.info("Plex OAuth: connection established server=%s", server_url)
    conn_data = PlexConnectionResponse.model_validate(conn).model_dump(mode="json")
    return {"status": "connected", **conn_data}


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


def _get_title_for_record(db: Session, item_type: str, item_id: int) -> Optional[str]:
    """Look up the title from the source model for the given item."""
    if item_type == "movie":
        item = db.query(Movie).filter(Movie.id == item_id).first()
        return item.title if item else None
    if item_type == "tv_show":
        item = db.query(TVShow).filter(TVShow.id == item_id).first()
        return item.title if item else None
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


@router.get("/mismatches", response_model=list[PlexMismatchItem])
def list_mismatches(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Return all sync records with TMDB mismatch between MetaMaster and Plex."""
    records = (
        db.query(PlexSyncRecord).filter(PlexSyncRecord.sync_status == PlexSyncStatus.MISMATCH).all()
    )
    return [
        PlexMismatchItem(
            id=r.id,
            item_type=r.item_type,
            item_id=r.item_id,
            plex_rating_key=r.plex_rating_key,
            plex_tmdb_id=r.plex_tmdb_id,
        )
        for r in records
    ]


@router.post("/mismatches/{record_id}/resolve")
def resolve_mismatch(
    record_id: int,
    payload: PlexResolveRequest,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Resolve a TMDB mismatch. trust='metamaster' pushes our ID to Plex;
    trust='plex' updates our DB and re-triggers enrichment."""
    record = db.query(PlexSyncRecord).filter(PlexSyncRecord.id == record_id).first()
    if record is None:
        raise HTTPException(status_code=404, detail="Sync record not found")
    if record.sync_status != PlexSyncStatus.MISMATCH:
        raise HTTPException(status_code=400, detail="Record is not in MISMATCH state")

    if payload.trust == "metamaster":
        _resolve_trust_metamaster(db, record)
    elif payload.trust == "plex":
        _resolve_trust_plex(db, record)
    else:
        raise HTTPException(status_code=422, detail="trust must be 'metamaster' or 'plex'")

    return {"status": "resolved"}


def _resolve_trust_metamaster(db: Session, record: PlexSyncRecord) -> None:
    """Push our TMDB ID to Plex to fix their match."""
    conn = db.query(PlexConnection).filter(PlexConnection.id == record.connection_id).first()
    our_tmdb_id = _get_tmdb_id_for_record(db, record.item_type, record.item_id)
    title = _get_title_for_record(db, record.item_type, record.item_id)
    if conn and our_tmdb_id and title:
        plex = PlexClient(server_url=conn.server_url, token=conn.token)
        plex.fix_match(rating_key=record.plex_rating_key, tmdb_id=our_tmdb_id, title=title)
    record.plex_tmdb_id = None  # type: ignore[assignment]
    record.sync_status = PlexSyncStatus.SYNCED  # type: ignore[assignment]
    db.commit()


def _resolve_trust_plex(db: Session, record: PlexSyncRecord) -> None:
    """Accept Plex's TMDB ID: update our item and re-trigger enrichment."""
    plex_tmdb_id = record.plex_tmdb_id
    item_type: str = record.item_type  # type: ignore[assignment]
    item_id: int = record.item_id  # type: ignore[assignment]

    if item_type == "movie":
        item = db.query(Movie).filter(Movie.id == item_id).first()
        if item:
            item.tmdb_id = plex_tmdb_id  # type: ignore[assignment]
            db.flush()
            enrich_movie_external(item_id)
    elif item_type == "tv_show":
        item = db.query(TVShow).filter(TVShow.id == item_id).first()
        if item:
            item.tmdb_id = plex_tmdb_id  # type: ignore[assignment]
            db.flush()

    record.plex_tmdb_id = None  # type: ignore[assignment]
    record.sync_status = PlexSyncStatus.SYNCED  # type: ignore[assignment]
    db.commit()
