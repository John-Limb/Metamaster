from unittest.mock import patch

import pytest

from app.infrastructure.external_apis.plex.client import PlexClient
from app.infrastructure.external_apis.plex.collection_client import PlexCollectionClient


@pytest.mark.unit
def test_get_machine_identifier_parses_response():
    client = PlexClient(server_url="http://plex:32400", token="tok")
    with patch.object(
        client, "_get", return_value={"MediaContainer": {"machineIdentifier": "abc123"}}
    ):
        result = client.get_machine_identifier()
    assert result == "abc123"


@pytest.mark.unit
def test_build_item_uri():
    cc = PlexCollectionClient(server_url="http://plex:32400", token="tok", machine_id="abc")
    assert cc._item_uri("99") == "server://abc/com.plexapp.plugins.library/library/metadata/99"


@pytest.mark.unit
def test_get_collections_returns_list():
    cc = PlexCollectionClient(server_url="http://plex:32400", token="tok", machine_id="abc")
    payload = {
        "MediaContainer": {
            "Metadata": [
                {"ratingKey": "10", "title": "MCU", "summary": "Marvel"},
            ]
        }
    }
    with patch.object(cc, "_get", return_value=payload):
        result = cc.get_collections(section_id="1")
    assert len(result) == 1
    assert result[0]["ratingKey"] == "10"


@pytest.mark.unit
def test_get_collection_item_keys():
    cc = PlexCollectionClient(server_url="http://plex:32400", token="tok", machine_id="abc")
    payload = {
        "MediaContainer": {
            "Metadata": [
                {"ratingKey": "5"},
                {"ratingKey": "6"},
            ]
        }
    }
    with patch.object(cc, "_get", return_value=payload):
        result = cc.get_collection_item_keys("10")
    assert result == ["5", "6"]


@pytest.mark.unit
def test_create_collection_posts_and_returns_key():
    cc = PlexCollectionClient(server_url="http://plex:32400", token="tok", machine_id="abc")
    payload = {"MediaContainer": {"Metadata": [{"ratingKey": "99"}]}}
    with patch.object(cc, "_post", return_value=payload) as mock_post:
        with patch.object(cc, "add_item_to_collection"):
            key = cc.create_collection(section_id="1", title="MCU", rating_keys=["5", "6"])
    assert key == "99"
    mock_post.assert_called_once()


@pytest.mark.unit
def test_delete_collection_calls_correct_path():
    cc = PlexCollectionClient(server_url="http://plex:32400", token="tok", machine_id="abc")
    with patch.object(cc, "_delete") as mock_del:
        cc.delete_collection("10")
    mock_del.assert_called_once_with("/library/metadata/10")
