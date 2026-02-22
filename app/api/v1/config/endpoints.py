"""Configuration check endpoints"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
import logging
from datetime import datetime
from croniter import croniter

from app.core.config import settings, MOVIE_DIR, TV_DIR
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


def check_path_exists(path: str) -> bool:
    """Check if a path exists, is a directory, and is readable"""
    if not path:
        logger.warning("Path is empty or None")
        return False
    exists = os.path.exists(path)
    is_dir = os.path.isdir(path) if exists else False
    readable = os.access(path, os.R_OK) if exists else False
    if exists and is_dir and readable:
        try:
            contents = os.listdir(path)
            logger.info(f"Path '{path}': exists=True, readable=True, items={len(contents)}")
        except PermissionError:
            logger.warning(f"Path '{path}': exists=True, readable=False (PermissionError on listdir)")
            return False
    else:
        logger.warning(f"Path '{path}': exists={exists}, is_dir={is_dir}, readable={readable}")
    return exists and is_dir and readable


@router.get("/check", response_model=ConfigurationState)
async def check_configuration():
    """
    Check all configuration items and return their status.
    
    This endpoint checks:
    - OMDB API Key
    - TVDB API Key
    - Database Connection
    - File System Paths (MOVIE_DIR, TV_DIR)
    """
    items = []

    # Check TMDB API Key (covers both movies and TV shows)
    tmdb_configured = bool(settings.tmdb_api_key and settings.tmdb_api_key != "your_tmdb_api_key_here")
    items.append(ConfigurationItem(
        id="api-keys-tmdb",
        name="TMDB API Key",
        description="API key for fetching movie and TV show metadata from The Movie Database",
        severity="important",
        status="valid" if tmdb_configured else "invalid",
        actionLabel="Configure API Key",
        actionPath="/settings?section=api-keys",
    ))
    
    # Check Database Connection (we'll verify it's configured in settings)
    db_configured = bool(settings.database_url)
    items.append(ConfigurationItem(
        id="database-connection",
        name="Database Connection",
        description="Connection to the PostgreSQL database",
        severity="critical",
        status="valid" if db_configured else "invalid",
        actionLabel="Check Database",
        actionPath="/settings?section=database",
    ))
    
    # Check File System Paths
    movie_dir_exists = check_path_exists(MOVIE_DIR)
    tv_dir_exists = check_path_exists(TV_DIR)
    paths_configured = movie_dir_exists or tv_dir_exists

    logger.info(f"File system paths check: movie_dir={MOVIE_DIR} (exists={movie_dir_exists}), tv_dir={TV_DIR} (exists={tv_dir_exists})")
    
    items.append(ConfigurationItem(
        id="file-system-paths",
        name="File System Paths",
        description="Base paths for media library and downloads",
        severity="critical",
        status="valid" if paths_configured else "invalid",
        actionLabel="Configure Paths",
        actionPath="/settings?section=paths",
    ))
    
    # File Monitoring (optional, depends on paths)
    items.append(ConfigurationItem(
        id="file-monitoring",
        name="File Monitoring",
        description="Watch configured directories for new media files",
        severity="important",
        status="valid" if paths_configured else "invalid",
        actionLabel="Enable Monitoring",
        actionPath="/settings?section=monitoring",
    ))
    
    # Metadata Sources
    metadata_configured = tmdb_configured
    items.append(ConfigurationItem(
        id="metadata-sources",
        name="Metadata Sources",
        description="Configured sources for fetching movie and TV show metadata",
        severity="important",
        status="valid" if metadata_configured else "invalid",
        actionLabel="Configure Sources",
        actionPath="/settings?section=metadata",
    ))
    
    # Storage Location
    items.append(ConfigurationItem(
        id="storage-location",
        name="Storage Location",
        description="Accessible storage location for media files",
        severity="important",
        status="valid" if paths_configured else "invalid",
        actionLabel="Check Storage",
        actionPath="/settings?section=storage",
    ))
    
    # Calculate isComplete - only critical items must be valid
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
