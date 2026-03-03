"""Storage analytics API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domain.storage.service import StorageService

try:
    from app.tasks import enrich_file_technical_metadata
except (ImportError, AttributeError):
    enrich_file_technical_metadata = None  # type: ignore[assignment]

router = APIRouter(prefix="/storage", tags=["storage"])


def _get_service(db: Session = Depends(get_db)) -> StorageService:
    return StorageService(db)


@router.get("/summary")
def get_storage_summary(service: StorageService = Depends(_get_service)):
    """Storage summary for dashboard widget — disk stats + library breakdown."""
    return service.get_summary()


@router.get("/files")
def get_storage_files(
    page: int = Query(1, ge=1),
    pageSize: int = Query(50, ge=1, le=200, alias="pageSize"),
    sortBy: str = Query("size_bytes", alias="sortBy"),
    sortDir: str = Query("desc", pattern="^(asc|desc)$", alias="sortDir"),
    mediaType: Optional[str] = Query(None, alias="mediaType"),
    codec: Optional[str] = None,
    resolutionTier: Optional[str] = Query(None, alias="resolutionTier"),
    efficiencyTier: Optional[str] = Query(None, alias="efficiencyTier"),
    service: StorageService = Depends(_get_service),
):
    """Paginated, sortable file list with efficiency analytics."""
    return service.get_files(
        page=page,
        page_size=pageSize,
        sort_by=sortBy,
        sort_dir=sortDir,
        media_type=mediaType,
        codec=codec,
        resolution_tier=resolutionTier,
        efficiency_tier=efficiencyTier,
    )


@router.post("/scan-technical", status_code=202)
def trigger_technical_scan():
    """Trigger background FFprobe enrichment for files missing technical metadata."""
    enrich_file_technical_metadata.delay()
    return {"message": "Technical metadata scan queued"}
