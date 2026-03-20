"""Plex HTTP client methods for collections."""

import logging
from typing import Any, Dict, List, Optional

import httpx

from app.infrastructure.external_apis.plex.client import _PLEX_HEADERS

logger = logging.getLogger(__name__)

_COLLECTION_TYPE = "18"  # Plex media type for collections


class PlexCollectionClient:
    """HTTP client for Plex collection management."""

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

    def get_collections(self, section_id: str) -> List[Dict[str, Any]]:
        """Return raw Plex collection metadata dicts for a library section."""
        data = self._get(f"/library/sections/{section_id}/collections")
        return data.get("MediaContainer", {}).get("Metadata", [])

    def get_collection_item_keys(self, collection_key: str) -> List[str]:
        """Return ratingKeys of all items in a collection."""
        data = self._get(f"/library/metadata/{collection_key}/children")
        items = data.get("MediaContainer", {}).get("Metadata", [])
        return [item["ratingKey"] for item in items]

    def create_collection(self, section_id: str, title: str, rating_keys: List[str]) -> str:
        """Create a Plex collection with the given items. Returns its ratingKey."""
        first_uri = self._item_uri(rating_keys[0]) if rating_keys else ""
        data = self._post(
            "/library/collections",
            params={
                "type": _COLLECTION_TYPE,
                "title": title,
                "smart": "0",
                "sectionId": section_id,
                "uri": first_uri,
            },
        )
        key: str = data["MediaContainer"]["Metadata"][0]["ratingKey"]
        for rk in rating_keys[1:]:
            self.add_item_to_collection(collection_key=key, rating_key=rk)
        return key

    def update_collection_metadata(
        self,
        collection_key: str,
        title: str,
        description: Optional[str],
        sort_title: Optional[str],
    ) -> None:
        params: dict = {"title": title, "type": _COLLECTION_TYPE}
        if description is not None:
            params["summary"] = description
        if sort_title is not None:
            params["titleSort"] = sort_title
        self._put(f"/library/metadata/{collection_key}", params=params)

    def add_item_to_collection(self, collection_key: str, rating_key: str) -> None:
        self._put(
            f"/library/metadata/{collection_key}/items",
            params={"uri": self._item_uri(rating_key)},
        )

    def remove_item_from_collection(self, collection_key: str, item_key: str) -> None:
        self._delete(f"/library/metadata/{collection_key}/items/{item_key}")

    def delete_collection(self, collection_key: str) -> None:
        self._delete(f"/library/metadata/{collection_key}")
