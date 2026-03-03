"""API routers package"""

from app.api.v1.cache import endpoints as cache
from app.api.v1.files import endpoints as files
from app.api.v1.health import endpoints as health
from app.api.v1.movies import endpoints as movies
from app.api.v1.tasks import endpoints as tasks
from app.api.v1.tv_shows import endpoints as tv_shows

__all__ = ["health", "movies", "tv_shows", "cache", "tasks", "files"]
