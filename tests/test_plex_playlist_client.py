from unittest.mock import patch

import pytest

from app.infrastructure.external_apis.plex.playlist_client import PlexPlaylistClient


@pytest.mark.unit
def test_get_playlists_returns_list():
    pc = PlexPlaylistClient(server_url="http://plex:32400", token="tok", machine_id="abc")
    payload = {
        "MediaContainer": {
            "Metadata": [
                {"ratingKey": "20", "title": "Weekend"},
            ]
        }
    }
    with patch.object(pc, "_get", return_value=payload):
        result = pc.get_playlists()
    assert len(result) == 1
    assert result[0]["ratingKey"] == "20"


@pytest.mark.unit
def test_get_playlist_item_keys():
    pc = PlexPlaylistClient(server_url="http://plex:32400", token="tok", machine_id="abc")
    payload = {"MediaContainer": {"Metadata": [{"ratingKey": "3"}, {"ratingKey": "4"}]}}
    with patch.object(pc, "_get", return_value=payload):
        result = pc.get_playlist_item_keys("20")
    assert result == ["3", "4"]


@pytest.mark.unit
def test_create_playlist_returns_key():
    pc = PlexPlaylistClient(server_url="http://plex:32400", token="tok", machine_id="abc")
    payload = {"MediaContainer": {"Metadata": [{"ratingKey": "99"}]}}
    with patch.object(pc, "_post", return_value=payload):
        with patch.object(pc, "add_item_to_playlist"):
            key = pc.create_playlist(title="Weekend", rating_keys=["3", "4"])
    assert key == "99"


@pytest.mark.unit
def test_delete_playlist_calls_correct_path():
    pc = PlexPlaylistClient(server_url="http://plex:32400", token="tok", machine_id="abc")
    with patch.object(pc, "_delete") as mock_del:
        pc.delete_playlist("20")
    mock_del.assert_called_once_with("/playlists/20")


@pytest.mark.unit
def test_item_uri_format():
    pc = PlexPlaylistClient(server_url="http://plex:32400", token="tok", machine_id="abc123")
    assert pc._item_uri("42") == "server://abc123/com.plexapp.plugins.library/library/metadata/42"
