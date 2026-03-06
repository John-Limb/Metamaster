import httpx
import pytest
import respx

from app.infrastructure.external_apis.plex.client import PlexClient
from app.infrastructure.external_apis.plex.schemas import PlexLibrarySection, PlexMediaItem


@pytest.mark.unit
def test_plex_library_section_parses():
    data = {"key": "1", "title": "Movies", "type": "movie"}
    section = PlexLibrarySection(**data)
    assert section.key == "1"
    assert section.title == "Movies"
    assert section.type == "movie"


@pytest.mark.unit
def test_plex_media_item_parses_with_guid():
    data = {
        "ratingKey": "123",
        "title": "The Matrix",
        "year": 1999,
        "viewCount": 2,
        "lastViewedAt": 1700000000,
        "Guid": [{"id": "tmdb://603"}],
    }
    item = PlexMediaItem(**data)
    assert item.rating_key == "123"
    assert item.tmdb_id == "603"
    assert item.view_count == 2


@pytest.mark.unit
def test_plex_media_item_missing_guid_returns_none():
    data = {"ratingKey": "456", "title": "Unknown", "Guid": []}
    item = PlexMediaItem(**data)
    assert item.tmdb_id is None


@pytest.mark.unit
def test_plex_media_item_non_tmdb_guid_returns_none():
    data = {
        "ratingKey": "789",
        "title": "Some Movie",
        "Guid": [{"id": "imdb://tt0133093"}],
    }
    item = PlexMediaItem(**data)
    assert item.tmdb_id is None


@pytest.mark.unit
@respx.mock
def test_get_library_sections_returns_sections():
    respx.get("http://plex:32400/library/sections").mock(
        return_value=httpx.Response(
            200,
            json={
                "MediaContainer": {
                    "Directory": [
                        {"key": "1", "title": "Movies", "type": "movie"},
                        {"key": "2", "title": "TV Shows", "type": "show"},
                    ]
                }
            },
        )
    )
    client = PlexClient(server_url="http://plex:32400", token="fake-token")
    sections = client.get_library_sections()
    assert len(sections) == 2
    assert sections[0].title == "Movies"


@pytest.mark.unit
@respx.mock
def test_refresh_library_section_calls_correct_url():
    respx.get("http://plex:32400/library/sections/1/refresh").mock(return_value=httpx.Response(200))
    client = PlexClient(server_url="http://plex:32400", token="fake-token")
    client.refresh_library_section(section_id="1")  # should not raise


@pytest.mark.unit
@respx.mock
def test_find_item_by_tmdb_id_returns_rating_key():
    respx.get("http://plex:32400/library/sections/1/all", params={"type": 1}).mock(
        return_value=httpx.Response(
            200,
            json={
                "MediaContainer": {
                    "Metadata": [
                        {
                            "ratingKey": "99",
                            "title": "The Matrix",
                            "Guid": [{"id": "tmdb://603"}],
                        }
                    ]
                }
            },
        )
    )
    client = PlexClient(server_url="http://plex:32400", token="fake-token")
    key = client.find_rating_key_by_tmdb_id(section_id="1", tmdb_id="603")
    assert key == "99"


@pytest.mark.unit
@respx.mock
def test_find_item_by_tmdb_id_returns_none_when_not_found():
    respx.get("http://plex:32400/library/sections/1/all", params={"type": 1}).mock(
        return_value=httpx.Response(
            200,
            json={"MediaContainer": {"Metadata": []}},
        )
    )
    client = PlexClient(server_url="http://plex:32400", token="fake-token")
    key = client.find_rating_key_by_tmdb_id(section_id="1", tmdb_id="999")
    assert key is None


@pytest.mark.unit
@respx.mock
def test_find_item_by_tmdb_id_uses_provided_media_type():
    respx.get("http://plex:32400/library/sections/2/all", params={"type": 4}).mock(
        return_value=httpx.Response(
            200,
            json={
                "MediaContainer": {
                    "Metadata": [
                        {
                            "ratingKey": "55",
                            "title": "Breaking Bad",
                            "Guid": [{"id": "tmdb://1396"}],
                        }
                    ]
                }
            },
        )
    )
    client = PlexClient(server_url="http://plex:32400", token="fake-token")
    key = client.find_rating_key_by_tmdb_id(section_id="2", tmdb_id="1396", media_type=4)
    assert key == "55"


@pytest.mark.unit
@respx.mock
def test_get_all_items_with_watch_status():
    respx.get("http://plex:32400/library/sections/1/all").mock(
        return_value=httpx.Response(
            200,
            json={
                "MediaContainer": {
                    "Metadata": [
                        {
                            "ratingKey": "1",
                            "title": "Movie A",
                            "viewCount": 3,
                            "lastViewedAt": 1700000000,
                            "Guid": [{"id": "tmdb://100"}],
                        }
                    ]
                }
            },
        )
    )
    client = PlexClient(server_url="http://plex:32400", token="fake-token")
    items = client.get_all_items(section_id="1", media_type=1)
    assert items[0].view_count == 3
    assert items[0].tmdb_id == "100"
