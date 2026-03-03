"""Enrichment status dashboard endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domain.movies.models import Movie
from app.domain.tv_shows.models import TVShow

router = APIRouter(prefix="/enrichment", tags=["Enrichment"])

PENDING_STATUSES = (
    "local_only",
    "external_failed",
    "not_found",
    "pending_local",
    "pending_external",
)


@router.get("/pending")
async def get_pending_enrichment(db: Session = Depends(get_db)):
    """Return all movies and TV shows that need enrichment attention."""
    movies = db.query(Movie).filter(Movie.enrichment_status.in_(PENDING_STATUSES)).all()
    tv_shows = db.query(TVShow).filter(TVShow.enrichment_status.in_(PENDING_STATUSES)).all()
    return {
        "movies": [
            {
                "id": m.id,
                "title": m.title,
                "year": m.year,
                "enrichment_status": m.enrichment_status,
                "enrichment_error": m.enrichment_error,
                "detected_external_id": m.detected_external_id,
                "manual_external_id": m.manual_external_id,
            }
            for m in movies
        ],
        "tv_shows": [
            {
                "id": s.id,
                "title": s.title,
                "enrichment_status": s.enrichment_status,
                "enrichment_error": s.enrichment_error,
                "detected_external_id": s.detected_external_id,
                "manual_external_id": s.manual_external_id,
            }
            for s in tv_shows
        ],
        "total": len(movies) + len(tv_shows),
    }
