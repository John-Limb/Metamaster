"""Organisation service — file rename/move logic for Plex/Jellyfin standards."""

import logging
import re
import shutil
from pathlib import Path

from sqlalchemy.orm import Session, selectinload

from app.core.config import MOVIE_DIR, TV_DIR
from app.domain.movies.models import Movie, MovieFile
from app.domain.tv_shows.models import Episode, EpisodeFile, Season, TVShow

logger = logging.getLogger(__name__)

VALID_PRESETS = ("plex", "jellyfin")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def sanitize_filename(name: str) -> str:
    """Remove filesystem-unsafe characters and normalise whitespace."""
    sanitized = re.sub(r'[/\\:*?"<>|\x00]', " ", name)
    sanitized = re.sub(r"\s+", " ", sanitized)
    sanitized = sanitized.strip()
    return sanitized.rstrip(". ")


def build_movie_target_path(
    base_dir: str,
    title: str,
    year: int | None,
    ext: str,
    preset: str,
) -> str:
    """Return the target absolute path for a movie file.

    Both Plex and Jellyfin use the same movie format:
        {base_dir}/{Title} ({Year})/{Title} ({Year}).ext
    If year is None the parenthetical is omitted.
    """
    clean_title = sanitize_filename(title)
    folder_name = f"{clean_title} ({year})" if year else clean_title
    filename = f"{folder_name}{ext}"
    return str(Path(base_dir) / folder_name / filename)


def build_tv_target_path(
    base_dir: str,
    show_title: str,
    season_number: int,
    episode_number: int,
    episode_title: str | None,
    ext: str,
    preset: str,
) -> str:
    """Return the target absolute path for a TV episode file.

    Plex:     {base_dir}/{Show}/Season NN/{Show} - SNNENN - {Title}.ext
    Jellyfin: {base_dir}/{Show}/Season NN/{Show} SNNENN.ext
    """
    clean_show = sanitize_filename(show_title)
    season_dir = f"Season {season_number:02d}"
    ep_code = f"S{season_number:02d}E{episode_number:02d}"

    if preset == "jellyfin":
        filename = f"{clean_show} {ep_code}{ext}"
    else:  # plex
        if episode_title:
            clean_ep_title = sanitize_filename(episode_title)
            filename = f"{clean_show} - {ep_code} - {clean_ep_title}{ext}"
        else:
            filename = f"{clean_show} - {ep_code}{ext}"

    return str(Path(base_dir) / clean_show / season_dir / filename)


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


def get_conformance_stats(db: Session, preset: str) -> dict:
    """Return counts of how many files match/need-rename/unenriched per media type.

    Does NOT touch the filesystem — pure DB query.
    """
    if preset not in VALID_PRESETS:
        raise ValueError(f"Invalid preset '{preset}'. Must be one of {VALID_PRESETS}")

    movie_match = movie_rename = movie_unenriched = 0
    ep_match = ep_rename = ep_unenriched = 0

    for movie in db.query(Movie).options(selectinload(Movie.files)).all():
        if not movie.files:
            movie_unenriched += 1
            continue
        if not movie.title:
            movie_unenriched += 1
            continue
        for mf in movie.files:
            ext = Path(mf.file_path).suffix.lower()
            target = build_movie_target_path(MOVIE_DIR, movie.title, movie.year, ext, preset)
            if Path(mf.file_path).resolve() == Path(target).resolve():
                movie_match += 1
            else:
                movie_rename += 1

    for show in (
        db.query(TVShow)
        .options(
            selectinload(TVShow.seasons).selectinload(Season.episodes).selectinload(Episode.files)
        )
        .all()
    ):
        for season in show.seasons:
            for episode in season.episodes:
                if not episode.files:
                    ep_unenriched += 1
                    continue
                for ef in episode.files:
                    ext = Path(ef.file_path).suffix.lower()
                    target = build_tv_target_path(
                        TV_DIR,
                        show.title,
                        season.season_number,
                        episode.episode_number,
                        episode.title,
                        ext,
                        preset,
                    )
                    if Path(ef.file_path).resolve() == Path(target).resolve():
                        ep_match += 1
                    else:
                        ep_rename += 1

    return {
        "movies_match": movie_match,
        "movies_need_rename": movie_rename,
        "movies_unenriched": movie_unenriched,
        "episodes_match": ep_match,
        "episodes_need_rename": ep_rename,
        "episodes_unenriched": ep_unenriched,
    }


# ---------------------------------------------------------------------------
# Preview
# ---------------------------------------------------------------------------


def get_preview(db: Session, preset: str) -> dict:
    """Return lists of proposed renames for movies and episodes.

    Only includes files where current path != target path.
    """
    if preset not in VALID_PRESETS:
        raise ValueError(f"Invalid preset '{preset}'. Must be one of {VALID_PRESETS}")

    movies = []
    episodes = []

    for movie in db.query(Movie).options(selectinload(Movie.files)).all():
        if not movie.title or not movie.files:
            continue
        for mf in movie.files:
            ext = Path(mf.file_path).suffix.lower()
            target = build_movie_target_path(MOVIE_DIR, movie.title, movie.year, ext, preset)
            if Path(mf.file_path).resolve() != Path(target).resolve():
                movies.append(
                    {
                        "file_id": mf.id,
                        "file_type": "movie",
                        "current_path": mf.file_path,
                        "target_path": target,
                    }
                )

    for show in (
        db.query(TVShow)
        .options(
            selectinload(TVShow.seasons).selectinload(Season.episodes).selectinload(Episode.files)
        )
        .all()
    ):
        for season in show.seasons:
            for episode in season.episodes:
                if not episode.files:
                    continue
                for ef in episode.files:
                    ext = Path(ef.file_path).suffix.lower()
                    target = build_tv_target_path(
                        TV_DIR,
                        show.title,
                        season.season_number,
                        episode.episode_number,
                        episode.title,
                        ext,
                        preset,
                    )
                    if Path(ef.file_path).resolve() != Path(target).resolve():
                        episodes.append(
                            {
                                "file_id": ef.id,
                                "file_type": "episode",
                                "current_path": ef.file_path,
                                "target_path": target,
                                "show_title": show.title,
                                "season_number": season.season_number,
                            }
                        )

    return {"movies": movies, "episodes": episodes}


# ---------------------------------------------------------------------------
# Settings persistence
# ---------------------------------------------------------------------------


def get_saved_preset(db: Session) -> str:
    """Return the saved organisation preset, defaulting to 'plex'."""
    from app.domain.settings.models import AppSetting

    setting = db.query(AppSetting).filter(AppSetting.key == "organisation_preset").first()
    return setting.value if setting else "plex"


def save_preset(db: Session, preset: str) -> None:
    """Persist the organisation preset to the app_settings table."""
    from app.domain.settings.models import AppSetting

    setting = db.query(AppSetting).filter(AppSetting.key == "organisation_preset").first()
    if setting:
        setting.value = preset
    else:
        db.add(AppSetting(key="organisation_preset", value=preset))
    db.commit()


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------


def apply_renames(db: Session, items: list[dict]) -> dict:
    """Execute a list of rename operations.

    Each item: {"file_id": int, "file_type": "movie"|"episode", "target_path": str}

    Returns {"success": int, "failed": int, "errors": list[str]}
    """
    success = 0
    failed = 0
    errors = []

    for item in items:
        file_id = item["file_id"]
        file_type = item["file_type"]
        target = item["target_path"]

        try:
            if file_type == "movie":
                record = db.query(MovieFile).filter(MovieFile.id == file_id).first()
            elif file_type == "episode":
                record = db.query(EpisodeFile).filter(EpisodeFile.id == file_id).first()
            else:
                errors.append(f"Unknown file_type '{file_type}' for file {file_id}")
                failed += 1
                continue

            if not record:
                errors.append(f"File record {file_id} not found")
                failed += 1
                continue

            src = Path(record.file_path)
            dst = Path(target)

            if not src.exists():
                errors.append(f"Source file not found: {src}")
                failed += 1
                continue

            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            record.file_path = str(dst)
            success += 1
            logger.info(f"[Organisation] Renamed: {src} -> {dst}")

        except Exception as e:
            errors.append(f"Failed to rename file {file_id}: {e}")
            failed += 1
            logger.error(f"[Organisation] Error renaming file {file_id}: {e}")

    if success:
        db.commit()

    return {"success": success, "failed": failed, "errors": errors}
