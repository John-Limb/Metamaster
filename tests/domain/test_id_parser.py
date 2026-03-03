"""Tests for external ID parsing from file paths and folder names."""

import pytest
from app.domain.movies.scanner import extract_external_id_from_path


@pytest.mark.parametrize(
    "path,expected",
    [
        # Plex/Jellyfin brace convention in folder
        ("/movies/Inception (2010) {imdb-tt1375666}/Inception.mkv", "tt1375666"),
        # Brace convention in filename
        ("/movies/Interstellar {imdb-tt0816692}.mkv", "tt0816692"),
        # Parenthesis style
        ("/movies/Dune (tt1160419)/dune.mkv", "tt1160419"),
        # Bare ID in folder name
        ("/movies/The Matrix (1999) tt0133093/matrix.mkv", "tt0133093"),
        # TMDB style in folder (Plex/Jellyfin brace convention)
        ("/tv/Breaking Bad {tmdb-1396}/S01E01.mkv", "1396"),
        # No ID present — returns None
        ("/movies/Some Random Movie (2020)/movie.mkv", None),
    ],
)
def test_extract_external_id_from_path(path, expected):
    assert extract_external_id_from_path(path) == expected
