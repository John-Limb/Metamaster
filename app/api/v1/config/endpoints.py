"""Configuration check endpoints"""

import logging
import os
from datetime import datetime
from typing import List, Optional

from croniter import croniter
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import MOVIE_DIR, TV_DIR, settings
from app.infrastructure.cache.redis_cache import get_cache_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/config", tags=["Configuration"])


class ConfigurationItem(BaseModel):
    id: str
    name: str
    description: str
    severity: str  # 'critical' | 'important' | 'optional'
    status: str  # 'valid' | 'invalid' | 'checking'
    actionLabel: Optional[str] = None
    actionPath: Optional[str] = None


class ConfigurationState(BaseModel):
    items: List[ConfigurationItem]
    isComplete: bool
    lastChecked: str


def _can_list_dir(path: str) -> bool:
    """Attempt os.listdir and return False on PermissionError."""
    try:
        contents = os.listdir(path)
        logger.info(f"Path '{path}': exists=True, readable=True, items={len(contents)}")
        return True
    except PermissionError:
        logger.warning(f"Path '{path}': exists=True, readable=False (PermissionError on listdir)")
        return False


def check_path_exists(path: str) -> bool:
    """Check if a path exists, is a directory, and is readable"""
    if not path:
        logger.warning("Path is empty or None")
        return False
    exists = os.path.exists(path)
    is_dir = os.path.isdir(path) if exists else False
    readable = os.access(path, os.R_OK) if exists else False
    if exists and is_dir and readable:
        return _can_list_dir(path)
    logger.warning(f"Path '{path}': exists={exists}, is_dir={is_dir}, readable={readable}")
    return False


def _build_tmdb_token_item(token_set: bool) -> ConfigurationItem:
    """Build the TMDB Read Access Token configuration item."""
    token_desc = (
        "Long JWT for Bearer auth — get from TMDB Settings → API Read Access Token (v4 auth)"
    )
    if token_set:
        token_desc += " — active"
    return ConfigurationItem(
        id="api-keys-tmdb-token",
        name="TMDB Access Token",
        description=token_desc,
        severity="important",
        status="valid" if token_set else "invalid",
        actionLabel="Configure Token",
        actionPath="/settings?section=api-keys",
    )


def _build_tmdb_key_item(token_set: bool, key_set: bool) -> ConfigurationItem:
    """Build the TMDB v3 API Key configuration item."""
    if key_set and token_set:
        key_desc = "v3 API Key — present but not active (Access Token takes priority)"
    elif key_set:
        key_desc = "v3 API Key — active (set TMDB_READ_ACCESS_TOKEN to use Bearer auth instead)"
    else:
        key_desc = "v3 API Key — not set"
    return ConfigurationItem(
        id="api-keys-tmdb-key",
        name="TMDB API Key",
        description=key_desc,
        severity="optional" if token_set else "important",
        status="valid" if key_set else "invalid",
        actionLabel="Configure API Key",
        actionPath="/settings?section=api-keys",
    )


def _build_db_item(db_configured: bool) -> ConfigurationItem:
    """Build the database connection configuration item."""
    return ConfigurationItem(
        id="database-connection",
        name="Database Connection",
        description="Connection to the PostgreSQL database",
        severity="critical",
        status="valid" if db_configured else "invalid",
        actionLabel="Check Database",
        actionPath="/settings?section=database",
    )


def _build_path_items(
    movie_dir_exists: bool,
    tv_dir_exists: bool,
    paths_configured: bool,
    metadata_configured: bool,
) -> List[ConfigurationItem]:
    """Build configuration items for paths, monitoring, metadata, and storage."""
    return [
        ConfigurationItem(
            id="file-system-paths",
            name="File System Paths",
            description="Base paths for media library and downloads",
            severity="critical",
            status="valid" if paths_configured else "invalid",
            actionLabel="Configure Paths",
            actionPath="/settings?section=paths",
        ),
        ConfigurationItem(
            id="file-monitoring",
            name="File Monitoring",
            description="Watch configured directories for new media files",
            severity="important",
            status="valid" if paths_configured else "invalid",
            actionLabel="Enable Monitoring",
            actionPath="/settings?section=monitoring",
        ),
        ConfigurationItem(
            id="metadata-sources",
            name="Metadata Sources",
            description="Configured sources for fetching movie and TV show metadata",
            severity="important",
            status="valid" if metadata_configured else "invalid",
            actionLabel="Configure Sources",
            actionPath="/settings?section=metadata",
        ),
        ConfigurationItem(
            id="storage-location",
            name="Storage Location",
            description="Accessible storage location for media files",
            severity="important",
            status="valid" if paths_configured else "invalid",
            actionLabel="Check Storage",
            actionPath="/settings?section=storage",
        ),
    ]


@router.get("/check", response_model=ConfigurationState)
async def check_configuration():
    """
    Check all configuration items and return their status.

    This endpoint checks:
    - TMDB API credentials
    - Database Connection
    - File System Paths (MOVIE_DIR, TV_DIR)
    """
    token_set = bool(settings.tmdb_read_access_token)
    key_set = bool(settings.tmdb_api_key and settings.tmdb_api_key != "your_tmdb_api_key_here")
    db_configured = bool(settings.database_url)

    movie_dir_exists = check_path_exists(MOVIE_DIR)
    tv_dir_exists = check_path_exists(TV_DIR)
    paths_configured = movie_dir_exists or tv_dir_exists
    metadata_configured = token_set or key_set

    logger.info(
        f"File system paths check: movie_dir={MOVIE_DIR} (exists={movie_dir_exists}),"
        f" tv_dir={TV_DIR} (exists={tv_dir_exists})"
    )

    items: List[ConfigurationItem] = [
        _build_tmdb_token_item(token_set),
        _build_tmdb_key_item(token_set, key_set),
        _build_db_item(db_configured),
        *_build_path_items(movie_dir_exists, tv_dir_exists, paths_configured, metadata_configured),
    ]

    critical_items = [item for item in items if item.severity == "critical"]
    is_complete = all(item.status == "valid" for item in critical_items)

    return ConfigurationState(
        items=items,
        isComplete=is_complete,
        lastChecked=datetime.now().isoformat(),
    )


@router.get("/check/{item_id}", response_model=ConfigurationItem)
async def check_configuration_item(item_id: str):
    """
    Check a specific configuration item by ID.

    Valid item IDs:
    - api-keys-tmdb
    - database-connection
    - file-system-paths
    - file-monitoring
    - metadata-sources
    - storage-location
    """
    # Get full configuration state
    config_state = await check_configuration()

    # Find the requested item
    for item in config_state.items:
        if item.id == item_id:
            return item

    raise HTTPException(status_code=404, detail=f"Configuration item '{item_id}' not found")


class ScanScheduleResponse(BaseModel):
    schedule: str


class ScanScheduleUpdate(BaseModel):
    schedule: str


SCAN_SCHEDULE_REDIS_KEY = "config:media_scan_schedule"


@router.get("/scan-schedule", response_model=ScanScheduleResponse)
async def get_scan_schedule():
    """Return the current media scan cron schedule."""
    cache = get_cache_service()
    schedule = None
    if cache.is_connected():
        schedule = cache.redis_client.get(SCAN_SCHEDULE_REDIS_KEY)
    if not schedule:
        schedule = settings.media_scan_schedule
    return ScanScheduleResponse(schedule=schedule)


@router.put("/scan-schedule", response_model=ScanScheduleResponse)
async def set_scan_schedule(body: ScanScheduleUpdate):
    """Validate and store a new media scan cron schedule."""
    if not croniter.is_valid(body.schedule):
        raise HTTPException(status_code=400, detail="Invalid cron expression")

    cache = get_cache_service()
    if not cache.is_connected():
        raise HTTPException(status_code=503, detail="Redis is unavailable")

    cache.redis_client.set(SCAN_SCHEDULE_REDIS_KEY, body.schedule)
    logger.info(f"Media scan schedule updated to: {body.schedule}")
    return ScanScheduleResponse(schedule=body.schedule)
