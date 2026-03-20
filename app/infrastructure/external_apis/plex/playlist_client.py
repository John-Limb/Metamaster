"""Plex HTTP client methods for playlists."""

import logging
from typing import Any, Dict, List, Optional

import httpx

from app.infrastructure.external_apis.plex.client import _PLEX_HEADERS

logger = logging.getLogger(__name__)


class PlexPlaylistClient:
    """HTTP client for Plex playlist management."""

    def __init__(self, server_url: str, token: str, machine_id: str = ""):
        self._base = server_url.rstrip("/")
        self._token = token
        self._machine_id = machine_id

    def _headers(self) -> dict:
        return {**_PLEX_HEADERS, "X-Plex-Token": self._token}

    def _item_uri(self, rating_key: str) -> str:
        if not self._machine_id:
            raise ValueError("machine_id is required for item URI operations")
        return (
            f"server://{self._machine_id}"
            "/com.plexapp.plugins.library"
            f"/library/metadata/{rating_key}"
        )

    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        url = f"{self._base}{path}"
        with httpx.Client(timeout=15) as http:
            r = http.get(url, headers=self._headers(), params=params)
        r.raise_for_status()
        return r.json() if r.content else {}

    def _post(self, path: str, params: Optional[dict] = None) -> dict:
        url = f"{self._base}{path}"
        with httpx.Client(timeout=15) as http:
            r = http.post(url, headers=self._headers(), params=params)
        r.raise_for_status()
        return r.json() if r.content else {}

    def _put(self, path: str, params: Optional[dict] = None) -> None:
        url = f"{self._base}{path}"
        with httpx.Client(timeout=15) as http:
            r = http.put(url, headers=self._headers(), params=params)
        r.raise_for_status()

    def _delete(self, path: str) -> None:
        url = f"{self._base}{path}"
        with httpx.Client(timeout=15) as http:
            r = http.delete(url, headers=self._headers())
        r.raise_for_status()

    def get_playlists(self) -> List[Dict[str, Any]]:
        data = self._get("/playlists", params={"playlistType": "video"})
        return data.get("MediaContainer", {}).get("Metadata", [])

    def get_playlist_item_keys(self, playlist_key: str) -> List[str]:
        data = self._get(f"/playlists/{playlist_key}/items")
        items = data.get("MediaContainer", {}).get("Metadata", [])
        return [item["ratingKey"] for item in items]

    def create_playlist(self, title: str, rating_keys: List[str]) -> str:
        """Create a video playlist with the given items. Returns its ratingKey."""
        first_uri = self._item_uri(rating_keys[0]) if rating_keys else ""
        data = self._post(
            "/playlists",
            params={"type": "video", "smart": "0", "title": title, "uri": first_uri},
        )
        key: str = data["MediaContainer"]["Metadata"][0]["ratingKey"]
        for rk in rating_keys[1:]:
            self.add_item_to_playlist(playlist_key=key, rating_key=rk)
        return key

    def update_playlist_metadata(
        self, playlist_key: str, title: str, description: Optional[str]
    ) -> None:
        params: dict = {"title": title}
        if description is not None:
            params["summary"] = description
        self._put(f"/playlists/{playlist_key}", params=params)

    def add_item_to_playlist(self, playlist_key: str, rating_key: str) -> None:
        self._put(
            f"/playlists/{playlist_key}/items",
            params={"uri": self._item_uri(rating_key)},
        )

    def remove_item_from_playlist(self, playlist_key: str, item_key: str) -> None:
        self._delete(f"/playlists/{playlist_key}/items/{item_key}")

    def delete_playlist(self, playlist_key: str) -> None:
        self._delete(f"/playlists/{playlist_key}")
