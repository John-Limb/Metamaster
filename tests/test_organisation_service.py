"""Unit tests for OrganisationService path builders"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.domain.tv_shows.models import TVShow, Season, Episode, EpisodeFile
from app.domain.organisation.service import (
    build_movie_target_path,
    build_tv_target_path,
    get_preview,
    sanitize_filename,
)


@pytest.mark.parametrize("char", ['/', '\\', ':', '*', '?', '"', '<', '>', '|'])
def test_sanitize_removes_all_forbidden_chars(char):
    result = sanitize_filename(f"Show{char}Name")
    assert char not in result
    assert result == "Show Name"


def test_sanitize_empty_string():
    assert sanitize_filename('') == ''


def test_tv_target_path_jellyfin_no_episode_title():
    """Jellyfin format always omits episode title, even when None."""
    result = build_tv_target_path(
        base_dir='/media/tv',
        show_title='Dark',
        season_number=1,
        episode_number=1,
        episode_title=None,
        ext='.mkv',
        preset='jellyfin',
    )
    assert result == '/media/tv/Dark/Season 01/Dark S01E01.mkv'


# sanitize_filename
def test_sanitize_removes_invalid_chars():
    assert sanitize_filename('Show: Name') == 'Show Name'

def test_sanitize_strips_surrounding_whitespace():
    assert sanitize_filename('  Title  ') == 'Title'

def test_sanitize_collapses_double_spaces():
    assert sanitize_filename('A  B') == 'A B'


# build_movie_target_path — same for plex and jellyfin
def test_movie_target_path_plex():
    result = build_movie_target_path(
        base_dir='/media/movies',
        title='The Matrix',
        year=1999,
        ext='.mkv',
        preset='plex',
    )
    assert result == '/media/movies/The Matrix (1999)/The Matrix (1999).mkv'

def test_movie_target_path_jellyfin():
    result = build_movie_target_path(
        base_dir='/media/movies',
        title='The Matrix',
        year=1999,
        ext='.mkv',
        preset='jellyfin',
    )
    assert result == '/media/movies/The Matrix (1999)/The Matrix (1999).mkv'

def test_movie_target_path_no_year():
    result = build_movie_target_path(
        base_dir='/media/movies',
        title='Unknown Film',
        year=None,
        ext='.mp4',
        preset='plex',
    )
    assert result == '/media/movies/Unknown Film/Unknown Film.mp4'

def test_movie_target_path_sanitizes_colon():
    result = build_movie_target_path(
        base_dir='/media/movies',
        title='Batman: Forever',
        year=1995,
        ext='.mkv',
        preset='plex',
    )
    assert result == '/media/movies/Batman Forever (1995)/Batman Forever (1995).mkv'


# build_tv_target_path
def test_tv_target_path_plex_includes_title():
    result = build_tv_target_path(
        base_dir='/media/tv',
        show_title='Breaking Bad',
        season_number=1,
        episode_number=6,
        episode_title="Crazy Handful of Nothin'",
        ext='.mkv',
        preset='plex',
    )
    assert result == "/media/tv/Breaking Bad/Season 01/Breaking Bad - S01E06 - Crazy Handful of Nothin'.mkv"

def test_tv_target_path_jellyfin_omits_title():
    result = build_tv_target_path(
        base_dir='/media/tv',
        show_title='Breaking Bad',
        season_number=1,
        episode_number=6,
        episode_title="Crazy Handful of Nothin'",
        ext='.mkv',
        preset='jellyfin',
    )
    assert result == '/media/tv/Breaking Bad/Season 01/Breaking Bad S01E06.mkv'

def test_tv_target_path_plex_no_episode_title():
    """When episode title is None, Plex format omits the title suffix."""
    result = build_tv_target_path(
        base_dir='/media/tv',
        show_title='Some Show',
        season_number=2,
        episode_number=3,
        episode_title=None,
        ext='.mkv',
        preset='plex',
    )
    assert result == '/media/tv/Some Show/Season 02/Some Show - S02E03.mkv'

def test_tv_target_path_pads_numbers():
    result = build_tv_target_path(
        base_dir='/media/tv',
        show_title='Chernobyl',
        season_number=1,
        episode_number=1,
        episode_title='1:23:45',
        ext='.mkv',
        preset='plex',
    )
    # '1:23:45' has colons — they should be sanitized
    assert result == '/media/tv/Chernobyl/Season 01/Chernobyl - S01E01 - 1 23 45.mkv'


def test_build_movie_target_path_invalid_preset_still_works():
    """Unknown presets fall back to plex-style (non-jellyfin = plex branch)."""
    result = build_movie_target_path('/media/movies', 'Alien', 1979, '.mkv', 'unknown')
    assert result == '/media/movies/Alien (1979)/Alien (1979).mkv'


# ---------------------------------------------------------------------------
# get_preview — episode fields
# ---------------------------------------------------------------------------


@pytest.fixture
def preview_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def test_get_preview_episode_includes_show_and_season(preview_db):
    """Episode entries in get_preview include show_title and season_number."""
    show = TVShow(title="Breaking Bad")
    preview_db.add(show)
    preview_db.flush()

    season = Season(show_id=show.id, season_number=1)
    preview_db.add(season)
    preview_db.flush()

    episode = Episode(season_id=season.id, episode_number=1, title="Pilot")
    preview_db.add(episode)
    preview_db.flush()

    # Path that won't match the Plex target, so it appears in preview
    ef = EpisodeFile(episode_id=episode.id, file_path="/downloads/bb_s01e01.mkv")
    preview_db.add(ef)
    preview_db.commit()

    result = get_preview(preview_db, "plex")

    assert len(result["episodes"]) == 1
    ep = result["episodes"][0]
    assert ep["show_title"] == "Breaking Bad"
    assert ep["season_number"] == 1
