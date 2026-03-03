"""Movie domain service - re-export from app.services_impl"""

from app.services_impl import CacheService, MovieService

__all__ = ["MovieService", "CacheService"]
