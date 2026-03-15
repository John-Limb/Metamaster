"""FastAPI router for Plex collection and playlist endpoints."""

import logging
from typing import List

import yaml
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.auth.endpoints import get_current_user
from app.api.v1.plex.collection_schemas import (
    CollectionCreate,
    CollectionResponse,
    CollectionSetResponse,
    CollectionSetUpdate,
    CollectionUpdate,
    PlaylistCreate,
    PlaylistResponse,
    PlaylistUpdate,
    YamlImportRequest,
)
from app.core.database import get_db
from app.domain.plex.collection_builder import BuilderResolver
from app.domain.plex.collection_models import (
    BuilderType,
    PlexCollection,
    PlexCollectionSet,
    PlexPlaylist,
    SetType,
)
from app.domain.plex.collection_service import PlexCollectionService
from app.domain.plex.models import PlexConnection
from app.domain.plex.playlist_service import PlexPlaylistService
from app.domain.plex.service import get_or_cache_library_ids
from app.infrastructure.external_apis.plex.client import PlexClient
from app.infrastructure.external_apis.plex.collection_client import PlexCollectionClient
from app.infrastructure.external_apis.plex.playlist_client import PlexPlaylistClient

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/plex", tags=["plex-collections"])


def _get_active_connection(db: Session) -> PlexConnection:
    conn = db.query(PlexConnection).filter(PlexConnection.is_active.is_(True)).first()
    if conn is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active Plex connection",
        )
    return conn


def _make_clients(conn: PlexConnection):
    plex_client = PlexClient(server_url=conn.server_url, token=conn.token)
    machine_id = plex_client.get_machine_identifier()
    cc = PlexCollectionClient(server_url=conn.server_url, token=conn.token, machine_id=machine_id)
    pc = PlexPlaylistClient(server_url=conn.server_url, token=conn.token, machine_id=machine_id)
    return plex_client, cc, pc


def _make_services(
    db: Session, conn: PlexConnection, cc: PlexCollectionClient, pc: PlexPlaylistClient
):
    movie_section_id, tv_section_id = get_or_cache_library_ids(db, conn)
    resolver = BuilderResolver(db=db, connection_id=conn.id)
    coll_svc = PlexCollectionService(
        db=db,
        collection_client=cc,
        resolver=resolver,
        movie_section_id=movie_section_id,
        tv_section_id=tv_section_id,
    )
    playlist_svc = PlexPlaylistService(db=db, playlist_client=pc, resolver=resolver)
    return coll_svc, playlist_svc


# ---------------------------------------------------------------------------
# Collection endpoints
# ---------------------------------------------------------------------------


@router.get("/collections", response_model=List[CollectionResponse])
def list_collections(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """List all PlexCollections for the active connection."""
    conn = _get_active_connection(db)
    return db.query(PlexCollection).filter(PlexCollection.connection_id == conn.id).all()


@router.post("/collections", response_model=CollectionResponse, status_code=201)
def create_collection(
    payload: CollectionCreate,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Create a new PlexCollection (disabled by default)."""
    conn = _get_active_connection(db)
    coll = PlexCollection(
        connection_id=conn.id,
        name=payload.name,
        description=payload.description,
        sort_title=payload.sort_title,
        builder_type=payload.builder_type,
        builder_config=payload.builder_config,
        enabled=False,
        is_default=False,
    )
    db.add(coll)
    db.commit()
    db.refresh(coll)
    return coll


@router.post("/collections/pull", status_code=200)
def pull_collections(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Pull all collections from Plex into DB (unconditional)."""
    conn = _get_active_connection(db)
    _, cc, pc = _make_clients(conn)
    coll_svc, _ = _make_services(db, conn, cc, pc)
    coll_svc.pull_collections(connection_id=conn.id)
    return {"status": "ok", "message": "Collections pulled from Plex"}


@router.post("/collections/export")
def export_collections(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Export all collections as a YAML string."""
    conn = _get_active_connection(db)
    colls = db.query(PlexCollection).filter(PlexCollection.connection_id == conn.id).all()
    payload = {
        "collections": {
            c.name: {
                "description": c.description,
                "sort_title": c.sort_title,
                "builder_type": c.builder_type,
                "builder_config": c.builder_config,
            }
            for c in colls
        }
    }
    return {"yaml_content": yaml.dump(payload, allow_unicode=True)}


@router.get("/collections/{collection_id}", response_model=CollectionResponse)
def get_collection(
    collection_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Get a single PlexCollection by ID."""
    coll = db.query(PlexCollection).filter(PlexCollection.id == collection_id).first()
    if coll is None:
        raise HTTPException(status_code=404, detail="Collection not found")
    return coll


@router.patch("/collections/{collection_id}", response_model=CollectionResponse)
def update_collection(
    collection_id: int,
    payload: CollectionUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Update fields on a PlexCollection."""
    coll = db.query(PlexCollection).filter(PlexCollection.id == collection_id).first()
    if coll is None:
        raise HTTPException(status_code=404, detail="Collection not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(coll, field, value)
    db.commit()
    db.refresh(coll)
    return coll


@router.delete("/collections/{collection_id}", status_code=204)
def delete_collection(
    collection_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Delete a PlexCollection from the DB."""
    coll = db.query(PlexCollection).filter(PlexCollection.id == collection_id).first()
    if coll is None:
        raise HTTPException(status_code=404, detail="Collection not found")
    db.delete(coll)
    db.commit()


@router.post("/collections/{collection_id}/push", status_code=200)
def push_collection(
    collection_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Push a single enabled collection to Plex."""
    coll = db.query(PlexCollection).filter(PlexCollection.id == collection_id).first()
    if coll is None:
        raise HTTPException(status_code=404, detail="Collection not found")
    if not coll.enabled:
        raise HTTPException(status_code=400, detail="Collection is not enabled for push")
    conn = _get_active_connection(db)
    _, cc, pc = _make_clients(conn)
    coll_svc, _ = _make_services(db, conn, cc, pc)
    coll_svc.push_collection(coll)
    return {"status": "ok", "plex_rating_key": coll.plex_rating_key}


# ---------------------------------------------------------------------------
# Playlist endpoints
# ---------------------------------------------------------------------------


@router.get("/playlists", response_model=List[PlaylistResponse])
def list_playlists(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """List all PlexPlaylists for the active connection."""
    conn = _get_active_connection(db)
    return db.query(PlexPlaylist).filter(PlexPlaylist.connection_id == conn.id).all()


@router.post("/playlists", response_model=PlaylistResponse, status_code=201)
def create_playlist(
    payload: PlaylistCreate,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Create a new PlexPlaylist (disabled by default)."""
    conn = _get_active_connection(db)
    pl = PlexPlaylist(
        connection_id=conn.id,
        name=payload.name,
        description=payload.description,
        builder_config=payload.builder_config,
        enabled=False,
    )
    db.add(pl)
    db.commit()
    db.refresh(pl)
    return pl


@router.post("/playlists/pull", status_code=200)
def pull_playlists(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Pull all playlists from Plex into DB (unconditional)."""
    conn = _get_active_connection(db)
    _, cc, pc = _make_clients(conn)
    _, playlist_svc = _make_services(db, conn, cc, pc)
    playlist_svc.pull_playlists(connection_id=conn.id)
    return {"status": "ok", "message": "Playlists pulled from Plex"}


@router.get("/playlists/{playlist_id}", response_model=PlaylistResponse)
def get_playlist(
    playlist_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Get a single PlexPlaylist by ID."""
    pl = db.query(PlexPlaylist).filter(PlexPlaylist.id == playlist_id).first()
    if pl is None:
        raise HTTPException(status_code=404, detail="Playlist not found")
    return pl


@router.patch("/playlists/{playlist_id}", response_model=PlaylistResponse)
def update_playlist(
    playlist_id: int,
    payload: PlaylistUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Update fields on a PlexPlaylist."""
    pl = db.query(PlexPlaylist).filter(PlexPlaylist.id == playlist_id).first()
    if pl is None:
        raise HTTPException(status_code=404, detail="Playlist not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(pl, field, value)
    db.commit()
    db.refresh(pl)
    return pl


@router.delete("/playlists/{playlist_id}", status_code=204)
def delete_playlist(
    playlist_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Delete a PlexPlaylist from the DB."""
    pl = db.query(PlexPlaylist).filter(PlexPlaylist.id == playlist_id).first()
    if pl is None:
        raise HTTPException(status_code=404, detail="Playlist not found")
    db.delete(pl)
    db.commit()


# ---------------------------------------------------------------------------
# YAML import endpoint
# ---------------------------------------------------------------------------


def _extract_builder(builder) -> tuple:
    """Convert AnyBuilder to (BuilderType, dict) for DB storage."""
    from app.infrastructure.external_apis.plex.collection_schemas import (
        DecadeBuilder,
        GenreBuilder,
        TmdbCollectionBuilder,
    )

    if isinstance(builder, TmdbCollectionBuilder):
        return BuilderType.TMDB_COLLECTION, {"tmdb_collection_id": builder.tmdb_collection_id}
    if isinstance(builder, GenreBuilder):
        return BuilderType.GENRE, {"genre": builder.genre}
    if isinstance(builder, DecadeBuilder):
        return BuilderType.DECADE, {"decade": builder.decade}
    return BuilderType.STATIC_ITEMS, {"items": [i.model_dump() for i in builder.items]}


def _build_playlist_config(defn) -> dict:
    """Extract builder_config dict from a PlaylistDefinition."""
    items = defn.builder.items if hasattr(defn.builder, "items") else []
    return {"items": [i.model_dump() for i in items]}


def _create_collections(db: Session, connection_id: int, collections: dict) -> list:
    """Persist parsed collection definitions and return list of names."""
    created = []
    for name, defn in collections.items():
        builder_type, builder_config = _extract_builder(defn.builder)
        coll = PlexCollection(
            connection_id=connection_id,
            name=name,
            description=defn.description,
            sort_title=defn.sort_title,
            builder_type=builder_type,
            builder_config=builder_config,
            enabled=False,
            is_default=False,
        )
        db.add(coll)
        created.append(name)
    return created


def _create_playlists(db: Session, connection_id: int, playlists: dict) -> list:
    """Persist parsed playlist definitions and return list of names."""
    created = []
    for name, defn in playlists.items():
        pl = PlexPlaylist(
            connection_id=connection_id,
            name=name,
            description=defn.description,
            builder_config=_build_playlist_config(defn),
            enabled=False,
        )
        db.add(pl)
        created.append(name)
    return created


@router.post("/collections/import", status_code=201)
def import_yaml(
    payload: YamlImportRequest,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Parse Kometa YAML and create collection/playlist DB records."""
    from app.infrastructure.external_apis.plex.collection_schemas import CollectionsYaml

    conn = _get_active_connection(db)
    try:
        raw = yaml.safe_load(payload.yaml_content)
    except yaml.YAMLError as exc:
        raise HTTPException(status_code=422, detail=f"Invalid YAML: {exc}")

    parsed = CollectionsYaml.model_validate(raw)
    created_collections = _create_collections(db, conn.id, parsed.collections or {})
    created_playlists = _create_playlists(db, conn.id, parsed.playlists or {})
    db.commit()
    return {
        "collections_created": created_collections,
        "playlists_created": created_playlists,
    }


# ---------------------------------------------------------------------------
# Collection set endpoints
# ---------------------------------------------------------------------------


@router.get("/sets", response_model=list[CollectionSetResponse])
def list_collection_sets(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """List all PlexCollectionSets for the active connection."""
    conn = _get_active_connection(db)
    return db.query(PlexCollectionSet).filter(PlexCollectionSet.connection_id == conn.id).all()


@router.patch("/sets/{set_type}", response_model=CollectionSetResponse)
def update_collection_set(
    set_type: SetType,
    payload: CollectionSetUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Toggle the enabled flag on a PlexCollectionSet."""
    conn = _get_active_connection(db)
    cs = (
        db.query(PlexCollectionSet)
        .filter(
            PlexCollectionSet.connection_id == conn.id,
            PlexCollectionSet.set_type == set_type,
        )
        .first()
    )
    if cs is None:
        raise HTTPException(status_code=404, detail="Collection set not found")
    cs.enabled = payload.enabled
    db.commit()
    db.refresh(cs)
    return cs


@router.post("/discover", status_code=202)
def trigger_discovery(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Dispatch the run_collection_discovery Celery task for the active connection."""
    conn = _get_active_connection(db)
    from app.tasks.plex_collections import run_collection_discovery

    task = run_collection_discovery.delay(conn.id)
    return {"task_id": task.id, "message": "Collection discovery dispatched"}


# ---------------------------------------------------------------------------
# Playlist push endpoint
# ---------------------------------------------------------------------------


@router.post("/playlists/{playlist_id}/push", status_code=200)
def push_playlist(
    playlist_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """Push a single enabled playlist to Plex."""
    pl = db.query(PlexPlaylist).filter(PlexPlaylist.id == playlist_id).first()
    if pl is None:
        raise HTTPException(status_code=404, detail="Playlist not found")
    if not pl.enabled:
        raise HTTPException(status_code=400, detail="Playlist is not enabled for push")
    conn = _get_active_connection(db)
    _, cc, pc = _make_clients(conn)
    _, playlist_svc = _make_services(db, conn, cc, pc)
    playlist_svc.push_playlist(pl)
    return {"status": "ok", "plex_rating_key": pl.plex_rating_key}
