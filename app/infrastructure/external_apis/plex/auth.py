"""Plex OAuth pin flow and manual token helpers"""

import logging
from typing import Optional, Tuple
from urllib.parse import urlencode

import httpx

logger = logging.getLogger(__name__)

_PLEX_TV_BASE = "https://plex.tv/api/v2"
_PLEX_HEADERS = {
    "Accept": "application/json",
    "X-Plex-Client-Identifier": "metamaster",
    "X-Plex-Product": "MetaMaster",
}


class PlexAuth:
    """Handles Plex OAuth pin flow for token acquisition"""

    def create_pin(self) -> Tuple[int, str]:
        """Request a new OAuth pin. Returns (pin_id, pin_code)."""
        logger.info("Plex OAuth: creating pin")
        with httpx.Client(timeout=10) as client:
            response = client.post(
                f"{_PLEX_TV_BASE}/pins",
                headers=_PLEX_HEADERS,
                json={"strong": True},
            )
        response.raise_for_status()
        data = response.json()
        logger.info("Plex OAuth: pin created id=%s", data["id"])
        return data["id"], data["code"]

    def poll_pin(self, pin_id: int) -> Optional[str]:
        """Check if the pin has been authenticated. Returns token or None."""
        logger.info("Plex OAuth: polling pin id=%s", pin_id)
        with httpx.Client(timeout=10) as client:
            response = client.get(
                f"{_PLEX_TV_BASE}/pins/{pin_id}",
                headers=_PLEX_HEADERS,
            )
        response.raise_for_status()
        token = response.json().get("authToken")
        if token:
            logger.info("Plex OAuth: pin %s authenticated", pin_id)
        return token or None

    def build_oauth_url(self, pin_code: str, redirect_uri: str) -> str:
        """Build the plex.tv OAuth redirect URL for the user to visit."""
        params = urlencode({"code": pin_code, "forwardUrl": redirect_uri})
        return f"https://app.plex.tv/auth#?{params}"
