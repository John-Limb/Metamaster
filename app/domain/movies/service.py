"""Movie domain service - re-export from app.services_impl"""

from app.services_impl import MovieService, CacheService

__all__ = ["MovieService", "CacheService"]
