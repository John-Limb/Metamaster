"""Unit tests for app.tasks.plex_collections Celery tasks."""

from unittest.mock import MagicMock, patch

BASE = "app.tasks.plex_collections"


def _make_conn(connection_id: int = 1) -> MagicMock:
    conn = MagicMock()
    conn.id = connection_id
    conn.server_url = "http://plex:32400"
    conn.token = "fake-token"
    return conn


def _make_item(enabled: bool, id_: int = 1) -> MagicMock:
    item = MagicMock()
    item.id = id_
    item.enabled = enabled
    return item


def _make_db(conn: MagicMock, items: list) -> MagicMock:
    """
    Build a db mock that returns `conn` from the first query chain
    (used for PlexConnection lookup) and `items` from the second
    query chain (used for PlexCollection / PlexPlaylist listing).
    """
    db = MagicMock()

    conn_chain = MagicMock()
    conn_chain.filter.return_value.first.return_value = conn

    items_chain = MagicMock()
    items_chain.filter.return_value.all.return_value = items

    db.query.side_effect = [conn_chain, items_chain]
    return db


@patch(f"{BASE}.PlexCollectionService")
@patch(f"{BASE}.PlexPlaylistService")
@patch(f"{BASE}.BuilderResolver")
@patch(f"{BASE}.get_or_cache_library_ids", return_value=("1", "2"))
@patch(f"{BASE}.PlexPlaylistClient")
@patch(f"{BASE}.PlexCollectionClient")
@patch(f"{BASE}.PlexClient")
@patch(f"{BASE}.get_db")
def test_push_all_collections_pushes_enabled_only(
    mock_get_db,
    MockPlexClient,
    MockCollectionClient,
    MockPlaylistClient,
    mock_get_library_ids,
    MockBuilderResolver,
    MockPlaylistService,
    MockCollectionService,
):
    """push_all_collections calls push_collection for each enabled collection only."""
    from app.tasks.plex_collections import push_all_collections

    conn = _make_conn()
    enabled_col = _make_item(enabled=True, id_=10)
    # Only enabled collections are returned by the filtered DB query
    db = _make_db(conn, [enabled_col])
    mock_get_db.return_value = iter([db])

    mock_coll_svc = MagicMock()
    MockCollectionService.return_value = mock_coll_svc
    MockPlexClient.return_value.get_machine_identifier.return_value = "machine-abc"

    push_all_collections(connection_id=1)

    mock_coll_svc.push_collection.assert_called_once_with(enabled_col)
    db.close.assert_called_once()


@patch(f"{BASE}.PlexCollectionService")
@patch(f"{BASE}.PlexPlaylistService")
@patch(f"{BASE}.BuilderResolver")
@patch(f"{BASE}.get_or_cache_library_ids", return_value=("1", "2"))
@patch(f"{BASE}.PlexPlaylistClient")
@patch(f"{BASE}.PlexCollectionClient")
@patch(f"{BASE}.PlexClient")
@patch(f"{BASE}.get_db")
def test_pull_all_collections_is_unconditional(
    mock_get_db,
    MockPlexClient,
    MockCollectionClient,
    MockPlaylistClient,
    mock_get_library_ids,
    MockBuilderResolver,
    MockPlaylistService,
    MockCollectionService,
):
    """pull_all_collections calls pull_collections regardless of enabled flag."""
    from app.tasks.plex_collections import pull_all_collections

    conn = _make_conn()
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = conn
    mock_get_db.return_value = iter([db])

    mock_coll_svc = MagicMock()
    MockCollectionService.return_value = mock_coll_svc
    MockPlexClient.return_value.get_machine_identifier.return_value = "machine-abc"

    pull_all_collections(connection_id=1)

    mock_coll_svc.pull_collections.assert_called_once_with(1)
    db.close.assert_called_once()


@patch(f"{BASE}.PlexCollectionService")
@patch(f"{BASE}.PlexPlaylistService")
@patch(f"{BASE}.BuilderResolver")
@patch(f"{BASE}.get_or_cache_library_ids", return_value=("1", "2"))
@patch(f"{BASE}.PlexPlaylistClient")
@patch(f"{BASE}.PlexCollectionClient")
@patch(f"{BASE}.PlexClient")
@patch(f"{BASE}.get_db")
def test_push_all_playlists_pushes_enabled_only(
    mock_get_db,
    MockPlexClient,
    MockCollectionClient,
    MockPlaylistClient,
    mock_get_library_ids,
    MockBuilderResolver,
    MockPlaylistService,
    MockCollectionService,
):
    """push_all_playlists calls push_playlist for each enabled playlist only."""
    from app.tasks.plex_collections import push_all_playlists

    conn = _make_conn()
    enabled_pl = _make_item(enabled=True, id_=20)
    db = _make_db(conn, [enabled_pl])
    mock_get_db.return_value = iter([db])

    mock_playlist_svc = MagicMock()
    MockPlaylistService.return_value = mock_playlist_svc
    MockPlexClient.return_value.get_machine_identifier.return_value = "machine-abc"

    push_all_playlists(connection_id=1)

    mock_playlist_svc.push_playlist.assert_called_once_with(enabled_pl)
    db.close.assert_called_once()


@patch(f"{BASE}.PlexCollectionService")
@patch(f"{BASE}.PlexPlaylistService")
@patch(f"{BASE}.BuilderResolver")
@patch(f"{BASE}.get_or_cache_library_ids", return_value=("1", "2"))
@patch(f"{BASE}.PlexPlaylistClient")
@patch(f"{BASE}.PlexCollectionClient")
@patch(f"{BASE}.PlexClient")
@patch(f"{BASE}.get_db")
def test_pull_all_playlists_is_unconditional(
    mock_get_db,
    MockPlexClient,
    MockCollectionClient,
    MockPlaylistClient,
    mock_get_library_ids,
    MockBuilderResolver,
    MockPlaylistService,
    MockCollectionService,
):
    """pull_all_playlists calls pull_playlists regardless of enabled flag."""
    from app.tasks.plex_collections import pull_all_playlists

    conn = _make_conn()
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = conn
    mock_get_db.return_value = iter([db])

    mock_playlist_svc = MagicMock()
    MockPlaylistService.return_value = mock_playlist_svc
    MockPlexClient.return_value.get_machine_identifier.return_value = "machine-abc"

    pull_all_playlists(connection_id=1)

    mock_playlist_svc.pull_playlists.assert_called_once_with(1)
    db.close.assert_called_once()


@patch(f"{BASE}.DefaultCollectionManager")
@patch(f"{BASE}.get_db")
def test_run_collection_discovery_calls_manager(
    mock_get_db,
    MockDefaultCollectionManager,
):
    """run_collection_discovery calls all three discover methods on DefaultCollectionManager."""
    from app.tasks.plex_collections import run_collection_discovery

    conn = _make_conn()
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = conn
    mock_get_db.return_value = iter([db])

    mock_manager = MagicMock()
    MockDefaultCollectionManager.return_value = mock_manager

    run_collection_discovery(connection_id=1)

    MockDefaultCollectionManager.assert_called_once_with(db=db, connection_id=1)
    mock_manager.discover_franchises.assert_called_once()
    mock_manager.discover_genres.assert_called_once()
    mock_manager.discover_decades.assert_called_once()
    db.close.assert_called_once()
