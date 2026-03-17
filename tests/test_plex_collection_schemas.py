import pytest

from app.infrastructure.external_apis.plex.collection_schemas import (
    CollectionDefinition,
    CollectionsYaml,
    DecadeBuilder,
    GenreBuilder,
    PlaylistDefinition,
    StaticItem,
    StaticItemsBuilder,
    TmdbCollectionBuilder,
)


@pytest.mark.unit
def test_static_item_defaults_type_to_movie():
    item = StaticItem(tmdb_id="123")
    assert item.item_type == "movie"


@pytest.mark.unit
def test_static_items_builder_roundtrip():
    b = StaticItemsBuilder(
        items=[StaticItem(tmdb_id="1"), StaticItem(tmdb_id="2", item_type="tv_show")]
    )
    assert len(b.items) == 2
    assert b.builder_type == "static_items"


@pytest.mark.unit
def test_tmdb_collection_builder():
    b = TmdbCollectionBuilder(tmdb_collection_id="131292")
    assert b.builder_type == "tmdb_collection"
    assert b.tmdb_collection_id == "131292"


@pytest.mark.unit
def test_genre_builder_schema():
    b = GenreBuilder(genre="Action")
    assert b.builder_type == "genre"
    assert b.genre == "Action"


@pytest.mark.unit
def test_decade_builder_schema():
    b = DecadeBuilder(decade=2000)
    assert b.builder_type == "decade"
    assert b.decade == 2000


@pytest.mark.unit
def test_collection_definition_requires_name():
    with pytest.raises(Exception):
        CollectionDefinition()


@pytest.mark.unit
def test_playlist_definition_only_accepts_static_items():
    b = StaticItemsBuilder(items=[StaticItem(tmdb_id="1")])
    p = PlaylistDefinition(name="My List", builder=b)
    assert p.name == "My List"


@pytest.mark.unit
def test_collections_yaml_parses_both_sections():
    raw = {
        "collections": {
            "MCU": {
                "name": "MCU",
                "description": "Marvel",
                "sort_title": "!001",
                "builder": {"builder_type": "tmdb_collection", "tmdb_collection_id": "131292"},
            }
        },
        "playlists": {
            "Weekend": {
                "name": "Weekend",
                "builder": {
                    "builder_type": "static_items",
                    "items": [{"tmdb_id": "1"}],
                },
            }
        },
    }
    parsed = CollectionsYaml.model_validate(raw)
    assert "MCU" in parsed.collections
    assert "Weekend" in parsed.playlists


@pytest.mark.unit
def test_collection_response_includes_content_type():
    """CollectionResponse must expose content_type."""
    from app.api.v1.plex.collection_schemas import CollectionResponse

    fields = CollectionResponse.model_fields
    assert "content_type" in fields, "content_type missing from CollectionResponse"
    import typing

    annotation = fields["content_type"].annotation
    args = typing.get_args(annotation)
    assert type(None) in args, "content_type must be Optional (allow None)"
