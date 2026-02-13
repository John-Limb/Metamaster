"""API v1 routers - centralized export"""

from app.api.v1.movies.endpoints import router as movies_router
from app.api.v1.tv_shows.endpoints import router as tv_shows_router
from app.api.v1.cache.endpoints import router as cache_router
from app.api.v1.tasks.endpoints import router as tasks_router
from app.api.v1.health.endpoints import router as health_router
from app.api.v1.auth import router as auth_router

__all__ = [
    "movies_router",
    "tv_shows_router",
    "cache_router",
    "tasks_router",
    "health_router",
    "auth_router",
]
