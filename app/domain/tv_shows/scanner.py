"""TV show file discovery and FFprobe analysis."""

import logging
import re
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings, TV_DIR
from app.domain.files.models import FileItem
from app.domain.tv_shows.models import TVShow, Season, Episode, EpisodeFile
from app.domain.movies.scanner import get_ffprobe, probe_file
from app.services_impl import TVDBService
from app.tasks.async_helpers import run_async

logger = logging.getLogger(__name__)

# Pattern: S01E02, s01e02, S1E2, etc.
SEASON_EPISODE_RE = re.compile(r'[Ss](\d{1,2})[Ee](\d{1,3})')

# Pattern for season directory: "Season 1", "Season 01", "season1"
SEASON_DIR_RE = re.compile(r'[Ss]eason\s*(\d{1,2})', re.IGNORECASE)

# Pattern for episode in filename without season: "E02", "e02", "EP02"
EPISODE_ONLY_RE = re.compile(r'[Ee][Pp]?(\d{1,3})')


def parse_tv_filename(file_path: str) -> tuple[str | None, int | None, int | None]:
    """Parse show name, season number, and episode number from a file path.

    Supports:
    - Inline: Show.Name.S01E02.1080p.mkv
    - Directory-based: Show Name/Season 1/E02 - Title.mp4
    """
    path = Path(file_path)
    filename = path.stem

    # Try inline SxxExx pattern first
    match = SEASON_EPISODE_RE.search(filename)
    if match:
        season_num = int(match.group(1))
        episode_num = int(match.group(2))
        # Show name is everything before the SxxExx pattern
        show_name = filename[:match.start()].replace('.', ' ').replace('_', ' ').strip()
        show_name = re.sub(r'\s+', ' ', show_name).strip(' -')
        if show_name:
            return show_name, season_num, episode_num

    # Try directory-based structure: parent dirs may contain season info
    parts = path.parts
    season_num = None
    episode_num = None
    show_name = None

    for part in parts:
        season_match = SEASON_DIR_RE.search(part)
        if season_match:
            season_num = int(season_match.group(1))
            # Show name is typically the directory above the season directory
            idx = parts.index(part)
            if idx > 0:
                candidate = parts[idx - 1]
                # Skip if it's a root-level media directory
                if candidate not in ('tv', 'media', ''):
                    show_name = candidate

    # Try to get episode number from filename
    ep_match = EPISODE_ONLY_RE.search(filename)
    if ep_match:
        episode_num = int(ep_match.group(1))

    # If we still don't have inline SxxExx, also check filename for it
    if season_num is not None and episode_num is not None and show_name:
        return show_name, season_num, episode_num

    return None, None, None


def create_tv_shows_from_files(db: Session) -> int:
    """Create TVShow/Season/Episode/EpisodeFile records for video files under TV_DIR.

    Runs FFprobe on each new file. Returns the number of episode files created.
    """
    video_extensions = {ext.lower() for ext in settings.watch_extensions}
    tv_dir_resolved = str(Path(TV_DIR).resolve())
    ffprobe = get_ffprobe()

    existing_paths = {row[0] for row in db.query(EpisodeFile.file_path).all()}

    tv_files = (
        db.query(FileItem)
        .filter(FileItem.type == "file", FileItem.path.startswith(tv_dir_resolved))
        .all()
    )

    created = 0
    # Cache lookups to avoid repeated queries
    show_cache: dict[str, TVShow] = {}
    season_cache: dict[tuple[int, int], Season] = {}

    for fi in tv_files:
        ext = Path(fi.path).suffix.lower()
        if ext not in video_extensions:
            continue
        if fi.path in existing_paths:
            continue

        show_name, season_num, episode_num = parse_tv_filename(fi.path)
        if not show_name or season_num is None or episode_num is None:
            logger.debug(f"Could not parse TV show info from: {fi.path}")
            continue

        # Get or create TVShow
        show_name_lower = show_name.lower()
        if show_name_lower in show_cache:
            show = show_cache[show_name_lower]
        else:
            show = db.query(TVShow).filter(TVShow.title.ilike(show_name)).first()
            if not show:
                show = TVShow(title=show_name)
                db.add(show)
                db.flush()
            show_cache[show_name_lower] = show

        # Get or create Season
        season_key = (show.id, season_num)
        if season_key in season_cache:
            season = season_cache[season_key]
        else:
            season = (
                db.query(Season)
                .filter(Season.show_id == show.id, Season.season_number == season_num)
                .first()
            )
            if not season:
                season = Season(show_id=show.id, season_number=season_num)
                db.add(season)
                db.flush()
            season_cache[season_key] = season

        # Get or create Episode
        episode = (
            db.query(Episode)
            .filter(Episode.season_id == season.id, Episode.episode_number == episode_num)
            .first()
        )
        if not episode:
            episode = Episode(season_id=season.id, episode_number=episode_num)
            db.add(episode)
            db.flush()

        # Create EpisodeFile with FFprobe data
        probe_data = probe_file(ffprobe, fi.path) if ffprobe else {}
        episode_file = EpisodeFile(
            episode_id=episode.id,
            file_path=fi.path,
            file_size=fi.size,
            resolution=probe_data.get("resolution"),
            codec_video=probe_data.get("codec_video"),
            codec_audio=probe_data.get("codec_audio"),
            bitrate=probe_data.get("bitrate"),
            duration=probe_data.get("duration"),
        )
        db.add(episode_file)
        existing_paths.add(fi.path)
        created += 1

    if created:
        db.commit()
        logger.info(f"Created {created} episode file record(s) from synced files")

    return created


def enrich_new_tv_shows(db: Session) -> int:
    """Search TVDB for TV shows missing a tvdb_id and populate metadata.

    Returns the number of shows successfully enriched.
    """
    shows = db.query(TVShow).filter(TVShow.tvdb_id.is_(None)).all()
    if not shows:
        return 0

    existing_tvdb_ids = {
        row[0] for row in db.query(TVShow.tvdb_id).filter(TVShow.tvdb_id.isnot(None)).all()
    }

    enriched = 0
    for show in shows:
        try:
            # Step 1: Search TVDB by title
            search_raw = run_async(TVDBService.search_show(db, show.title))
            if not search_raw:
                continue
            search_parsed = TVDBService.parse_tvdb_search_response(search_raw)
            if not search_parsed or not search_parsed.get("search_results"):
                continue

            tvdb_id = search_parsed["search_results"][0].get("tvdb_id")
            if not tvdb_id or tvdb_id in existing_tvdb_ids:
                continue

            # Step 2: Fetch full details
            detail_raw = run_async(TVDBService.get_series_details(db, tvdb_id))
            if not detail_raw:
                show.tvdb_id = tvdb_id
                existing_tvdb_ids.add(tvdb_id)
                enriched += 1
                continue

            detail = TVDBService.parse_tvdb_series_response(detail_raw)
            if not detail:
                show.tvdb_id = tvdb_id
                existing_tvdb_ids.add(tvdb_id)
                enriched += 1
                continue

            # Step 3: Update fields
            show.tvdb_id = tvdb_id
            show.plot = detail.get("plot", show.plot)
            show.rating = detail.get("rating", show.rating)
            show.genres = detail.get("genres", show.genres)
            show.status = detail.get("status", show.status)
            existing_tvdb_ids.add(tvdb_id)
            enriched += 1
        except Exception:
            logger.warning(f"Failed to enrich TV show {show.id} ({show.title})", exc_info=True)

    if enriched:
        db.commit()
        logger.info(f"Enriched {enriched} TV show(s) with TVDB metadata")
    return enriched


def probe_episode_file(db: Session, episode_id: int) -> Episode:
    """Run FFprobe on the primary file for a given episode and update its EpisodeFile record."""
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    if not episode:
        raise ValueError(f"Episode {episode_id} not found")

    episode_file = db.query(EpisodeFile).filter(EpisodeFile.episode_id == episode_id).first()
    if not episode_file:
        raise ValueError(f"No file associated with episode {episode_id}")

    ffprobe = get_ffprobe()
    if not ffprobe:
        raise RuntimeError("ffprobe is not available on this system")

    probe_data = probe_file(ffprobe, episode_file.file_path)
    if probe_data:
        for field, value in probe_data.items():
            setattr(episode_file, field, value)
        db.commit()
        db.refresh(episode)

    return episode
