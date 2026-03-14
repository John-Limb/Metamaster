"""Plex Media Server HTTP API client"""

import logging
from typing import List, Optional

import httpx

from app.infrastructure.external_apis.plex.schemas import PlexLibrarySection, PlexMediaItem

logger = logging.getLogger(__name__)

_PLEX_HEADERS = {
    "Accept": "application/json",
    "X-Plex-Client-Identifier": "metamaster",
    "X-Plex-Product": "MetaMaster",
}


class PlexClient:
    """Raw HTTP client for the Plex Media Server API"""

    def __init__(self, server_url: str, token: str):
        self._base = server_url.rstrip("/")
        self._token = token

    def _headers(self) -> dict:
        return {**_PLEX_HEADERS, "X-Plex-Token": self._token}

    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        url = f"{self._base}{path}"
        logger.info("Plex API GET %s params=%s", url, params)
        with httpx.Client(timeout=10) as client:
            response = client.get(url, headers=self._headers(), params=params)
        logger.info("Plex API response %s %s", url, response.status_code)
        response.raise_for_status()
        if not response.content:
            return {}
        result: dict = response.json()
        return result

    def get_library_sections(self) -> List[PlexLibrarySection]:
        data = self._get("/library/sections")
        directories = data.get("MediaContainer", {}).get("Directory", [])
        return [PlexLibrarySection(**d) for d in directories]

    def refresh_library_section(self, section_id: str) -> None:
        self._get(f"/library/sections/{section_id}/refresh")

    def find_rating_key_by_tmdb_id(
        self, section_id: str, tmdb_id: str, media_type: int = 1
    ) -> Optional[str]:
        items = self.get_all_items(section_id=section_id, media_type=media_type)
        for item in items:
            if item.tmdb_id == tmdb_id:
                return item.rating_key
        return None

    def find_by_title_year(
        self,
        section_id: str,
        title: str,
        year: Optional[int],
        media_type: int = 1,
    ) -> Optional[PlexMediaItem]:
        """Find a Plex item by title and year. Returns first match, or None."""
        data = self._get(
            f"/library/sections/{section_id}/all",
            params={"type": media_type, "title": title},
        )
        for raw in data.get("MediaContainer", {}).get("Metadata", []):
            item = PlexMediaItem(**raw)
            if year is None or item.year == year:
                return item
        return None

    def get_all_items(self, section_id: str, media_type: int) -> List[PlexMediaItem]:
        data = self._get(
            f"/library/sections/{section_id}/all",
            params={"type": media_type},
        )
        metadata = data.get("MediaContainer", {}).get("Metadata", [])
        return [PlexMediaItem(**m) for m in metadata]

    def _put(self, path: str, params: Optional[dict] = None) -> None:
        url = f"{self._base}{path}"
        logger.info("Plex API PUT %s params=%s", url, params)
        with httpx.Client(timeout=10) as http:
            response = http.put(url, headers=self._headers(), params=params)
        response.raise_for_status()

    def fix_match(self, rating_key: str, tmdb_id: str, title: str) -> None:
        """Push our TMDB ID to Plex to correct its match."""
        self._put(
            f"/library/metadata/{rating_key}/match",
            params={"guid": f"tmdb://{tmdb_id}", "name": title},
        )

    def get_machine_identifier(self) -> str:
        """Return the Plex server machine identifier (needed for item URIs)."""
        data = self._get("/")
        return data["MediaContainer"]["machineIdentifier"]
