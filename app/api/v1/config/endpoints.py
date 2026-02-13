"""Configuration check endpoints"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
import logging
from datetime import datetime

from app.core.config import settings, MOVIE_DIR, TV_DIR

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
    
    # Check OMDB API Key
    omdb_configured = bool(settings.omdb_api_key and settings.omdb_api_key != "your_omdb_api_key_here")
    items.append(ConfigurationItem(
        id="api-keys-omdb",
        name="OMDB API Key",
        description="API key for fetching movie metadata from OMDB",
        severity="critical",
        status="valid" if omdb_configured else "invalid",
        actionLabel="Configure API Key",
        actionPath="/settings?section=api-keys",
    ))
    
    # Check TVDB API Key
    tvdb_configured = bool(settings.tvdb_api_key and settings.tvdb_api_key != "your_tvdb_api_key_here")
    items.append(ConfigurationItem(
        id="api-keys-tvdb",
        name="TVDB API Key",
        description="API key for fetching TV show metadata from TVDB",
        severity="critical",
        status="valid" if tvdb_configured else "invalid",
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
    metadata_configured = omdb_configured or tvdb_configured
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
    - api-keys-omdb
    - api-keys-tvdb
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
