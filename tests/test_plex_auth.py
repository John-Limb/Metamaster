import httpx
import pytest
import respx

from app.infrastructure.external_apis.plex.auth import PlexAuth


@pytest.mark.unit
@respx.mock
def test_create_pin_returns_pin_id_and_code():
    respx.post("https://plex.tv/api/v2/pins").mock(
        return_value=httpx.Response(201, json={"id": 42, "code": "ABCD1234"})
    )
    auth = PlexAuth()
    pin_id, pin_code = auth.create_pin()
    assert pin_id == 42
    assert pin_code == "ABCD1234"


@pytest.mark.unit
@respx.mock
def test_poll_pin_returns_token_when_authenticated():
    respx.get("https://plex.tv/api/v2/pins/42").mock(
        return_value=httpx.Response(200, json={"authToken": "my-secret-token"})
    )
    auth = PlexAuth()
    token = auth.poll_pin(pin_id=42)
    assert token == "my-secret-token"


@pytest.mark.unit
@respx.mock
def test_poll_pin_returns_none_when_pending():
    respx.get("https://plex.tv/api/v2/pins/42").mock(
        return_value=httpx.Response(200, json={"authToken": None})
    )
    auth = PlexAuth()
    token = auth.poll_pin(pin_id=42)
    assert token is None


@pytest.mark.unit
def test_build_oauth_url_contains_pin_code():
    auth = PlexAuth()
    url = auth.build_oauth_url(pin_code="ABCD1234", redirect_uri="http://localhost/callback")
    assert "code=ABCD1234" in url
    assert "forwardUrl=" in url
