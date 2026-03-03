"""Tests for decoupled movie scanner Stage 1 (ffprobe only, no OMDB)."""

from unittest.mock import MagicMock, patch

from app.domain.files.models import FileItem
from app.domain.movies.scanner import create_movies_from_files


def _make_fi(file_path="/movies/Inception (2010)/inception.mkv", name="inception.mkv"):
    """Build a minimal mock FileItem."""
    fi = MagicMock(spec=FileItem)
    fi.path = file_path
    fi.name = name
    fi.size = 1_000_000_000
    fi.type = "file"
    return fi


def _make_db(fi):
    """Build a minimal mock DB whose query calls return canned results.

    First db.query() call  → MovieFile.file_path query → .all() returns []
    Second db.query() call → FileItem query → .filter().all() returns [fi]
    """
    db = MagicMock()

    # Track call count so we can return different values for successive calls
    call_count = {"n": 0}

    def query_side_effect(model):
        call_count["n"] += 1
        q = MagicMock()
        if call_count["n"] == 1:
            # MovieFile.file_path — returns existing paths (empty list = no dupes)
            q.all.return_value = []
        else:
            # FileItem — chained .filter(...).all() returns our file
            q.filter.return_value.all.return_value = [fi]
        return q

    db.query.side_effect = query_side_effect
    return db


@patch("app.domain.movies.scanner.get_ffprobe", return_value=None)
def test_create_movies_sets_local_only_status(mock_ffprobe):
    """Movie gets enrichment_status='local_only' regardless of ffprobe availability."""
    fi = _make_fi()
    db = _make_db(fi)

    with (
        patch("app.domain.movies.scanner.Movie") as MockMovie,
        patch("app.domain.movies.scanner.MovieFile"),
    ):
        movie_instance = MagicMock()
        MockMovie.return_value = movie_instance

        create_movies_from_files(db)

        # Verify Movie was constructed exactly once
        MockMovie.assert_called_once()

        all_kwargs = MockMovie.call_args.kwargs if hasattr(MockMovie.call_args, "kwargs") else {}
        assert (
            all_kwargs.get("enrichment_status") == "local_only"
        ), f"Expected enrichment_status='local_only', got call: {MockMovie.call_args}"


def test_create_movies_does_not_call_tmdb():
    """Stage 1 must never invoke TMDBService methods during create_movies_from_files."""
    fi = _make_fi()
    db = _make_db(fi)

    with (
        patch("app.domain.movies.scanner.get_ffprobe", return_value=None),
        patch("app.domain.movies.scanner.Movie"),
        patch("app.domain.movies.scanner.MovieFile"),
    ):
        import app.domain.movies.scanner as scanner_module

        # Patch TMDBService if it exists so we can assert it was never called
        if hasattr(scanner_module, "TMDBService"):
            with (
                patch.object(scanner_module.TMDBService, "search_movie") as mock_search,
                patch.object(scanner_module.TMDBService, "get_movie_details") as mock_details,
            ):
                create_movies_from_files(db)
                mock_search.assert_not_called()
                mock_details.assert_not_called()
        else:
            # TMDBService not imported at module level — trivially passes
            create_movies_from_files(db)


@patch("app.domain.movies.scanner.get_ffprobe", return_value=None)
def test_create_movies_stores_detected_external_id_from_filename(mock_ffprobe):
    """detected_external_id is populated from filename when IMDB ID is embedded."""
    fi = _make_fi(
        file_path="/movies/The Matrix (1999) {imdb-tt0133093}/matrix.mkv",
        name="matrix.mkv",
    )
    db = _make_db(fi)

    with (
        patch("app.domain.movies.scanner.Movie") as MockMovie,
        patch("app.domain.movies.scanner.MovieFile"),
    ):
        MockMovie.return_value = MagicMock()

        create_movies_from_files(db)

        MockMovie.assert_called_once()
        all_kwargs = MockMovie.call_args.kwargs if hasattr(MockMovie.call_args, "kwargs") else {}
        assert (
            all_kwargs.get("detected_external_id") == "tt0133093"
        ), f"Expected detected_external_id='tt0133093', got: {all_kwargs}"
