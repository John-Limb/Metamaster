"""TV show file discovery and FFprobe analysis."""

import logging
import re
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import TV_DIR, settings
from app.domain.files.models import FileItem
from app.domain.movies.scanner import extract_external_id_from_path, get_ffprobe, probe_file
from app.domain.tv_shows.models import Episode, EpisodeFile, Season, TVShow
from app.services_impl import TMDBService
from app.tasks.async_helpers import run_async

logger = logging.getLogger(__name__)

# Pattern: S01E02, s01e02, S1E2, etc.
SEASON_EPISODE_RE = re.compile(r"[Ss](\d{1,2})[Ee](\d{1,3})")

# Pattern for season directory: "Season 1", "Season 01", "season1"
SEASON_DIR_RE = re.compile(r"[Ss]eason\s*(\d{1,2})", re.IGNORECASE)

# Pattern for episode in filename without season: "E02", "e02", "EP02"
EPISODE_ONLY_RE = re.compile(r"[Ee][Pp]?(\d{1,3})")


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
        show_name = filename[: match.start()].replace(".", " ").replace("_", " ").strip()
        show_name = re.sub(r"\s+", " ", show_name).strip(" -")
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
                if candidate not in ("tv", "media", ""):
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

    # Backfill: mark any FileItem as indexed if an EpisodeFile already references its path
    indexed_paths = {row[0] for row in db.query(EpisodeFile.file_path).all()}
    backfilled = (
        db.query(FileItem)
        .filter(FileItem.is_indexed.is_(False), FileItem.path.in_(indexed_paths))
        .update({"is_indexed": True}, synchronize_session=False)
    )
    if backfilled:
        db.commit()
        logger.info(f"[TV] Backfilled is_indexed=True on {backfilled} existing FileItem(s)")

    existing_paths = indexed_paths

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

        logger.info(f"[TV] Detected: {fi.name}")

        show_name, season_num, episode_num = parse_tv_filename(fi.path)
        if not show_name or season_num is None or episode_num is None:
            logger.debug(f"[TV] Could not parse show info from: {fi.name} — skipping")
            continue

        ep_label = f"S{season_num:02d}E{episode_num:02d}"
        logger.info(f"[TV] Parsed: '{show_name}' {ep_label}")

        # Get or create TVShow
        show_name_lower = show_name.lower()
        if show_name_lower in show_cache:
            show = show_cache[show_name_lower]
        else:
            show = db.query(TVShow).filter(TVShow.title.ilike(show_name)).first()
            if not show:
                detected_id = extract_external_id_from_path(fi.path)
                if detected_id:
                    logger.info(f"[TV] TMDB/external ID detected in path: {detected_id}")
                show = TVShow(
                    title=show_name,
                    enrichment_status="local_only",
                    detected_external_id=detected_id,
                )
                db.add(show)
                db.flush()
                logger.info(f"[TV] New show created: '{show_name}' (ID: {show.id})")
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
        if probe_data:
            resolution = probe_data.get("resolution", "?")
            video = probe_data.get("codec_video", "?")
            audio = probe_data.get("codec_audio", "?")
            logger.info(f"[TV] FFprobe: {resolution}, {video}/{audio}")
        else:
            logger.debug(f"[TV] FFprobe skipped or unavailable for: {fi.name}")

        episode_file = EpisodeFile(
            episode_id=episode.id,
            file_path=fi.path,
            file_size=fi.size,
            resolution=probe_data.get("resolution"),
            codec_video=probe_data.get("codec_video"),
            codec_audio=probe_data.get("codec_audio"),
            audio_channels=probe_data.get("audio_channels"),
            bitrate=probe_data.get("bitrate"),
            duration=probe_data.get("duration"),
        )
        db.add(episode_file)
        fi.is_indexed = True
        existing_paths.add(fi.path)
        created += 1
        logger.info(f"[TV] Episode file created: '{show_name}' {ep_label}")

    if created:
        db.commit()
        logger.info(f"[TV] {created} new episode file(s) saved to database")

    return created


def enrich_new_tv_shows(db: Session) -> int:
    """Search TMDB for TV shows missing a tmdb_id and populate metadata.

    Returns the number of shows successfully enriched.
    """
    shows = db.query(TVShow).filter(TVShow.tmdb_id.is_(None)).all()
    if not shows:
        return 0

    existing_tmdb_ids = {
        row[0] for row in db.query(TVShow.tmdb_id).filter(TVShow.tmdb_id.isnot(None)).all()
    }

    enriched = 0
    for show in shows:
        try:
            logger.info(f"[TV] Enriching: '{show.title}'")

            # Step 1: Search TMDB by title
            logger.info(f"[TV] TMDB search: '{show.title}'")
            search_raw = run_async(TMDBService.search_show(db, show.title))
            if not search_raw:
                logger.info(f"[TV] TMDB: no results for '{show.title}'")
                continue
            search_parsed = TMDBService.parse_series_search_response(search_raw)
            if not search_parsed or not search_parsed.get("search_results"):
                logger.info(f"[TV] TMDB: no match for '{show.title}'")
                continue

            tmdb_id = search_parsed["search_results"][0].get("tmdb_id")
            if not tmdb_id or tmdb_id in existing_tmdb_ids:
                logger.debug(f"[TV] TMDB: duplicate or missing ID for '{show.title}' — skipping")
                continue

            logger.info(f"[TV] TMDB match: '{show.title}' → {tmdb_id}")

            # Step 2: Fetch full details
            logger.info(f"[TV] TMDB fetching details: {tmdb_id}")
            detail_raw = run_async(TMDBService.get_series_details(db, tmdb_id))
            if not detail_raw:
                show.tmdb_id = tmdb_id
                existing_tmdb_ids.add(tmdb_id)
                enriched += 1
                continue

            detail = TMDBService.parse_series_response(detail_raw)
            if not detail:
                show.tmdb_id = tmdb_id
                existing_tmdb_ids.add(tmdb_id)
                enriched += 1
                continue

            # Step 3: Update fields
            show.tmdb_id = tmdb_id
            show.plot = detail.get("plot", show.plot)
            show.rating = detail.get("rating", show.rating)
            show.genres = detail.get("genres", show.genres)
            show.status = detail.get("status", show.status)
            poster = detail.get("poster")
            if poster:
                show.poster_url = poster
            existing_tmdb_ids.add(tmdb_id)
            enriched += 1

            rating_str = f"★{show.rating}" if show.rating else "no rating"
            genres_str = ", ".join(show.genres) if isinstance(show.genres, list) else str(show.genres or "")
            logger.info(f"[TV] Enriched: '{show.title}' — {rating_str}, {genres_str}")

        except Exception:
            logger.warning(f"[TV] Failed to enrich '{show.title}' (ID: {show.id})", exc_info=True)

    if enriched:
        db.commit()
        logger.info(f"[TV] {enriched} show(s) enriched with TMDB metadata")
    return enriched


def probe_unscanned_episodes(db: Session) -> int:
    """Run FFprobe on episode files that are missing resolution or audio_channels data.

    Returns the number of files scanned.
    """
    ffprobe = get_ffprobe()
    if not ffprobe:
        return 0

    unscanned = (
        db.query(EpisodeFile)
        .filter(
            (EpisodeFile.resolution.is_(None))
            | (EpisodeFile.resolution == "")
            | (EpisodeFile.audio_channels.is_(None))
        )
        .all()
    )
    if not unscanned:
        return 0

    scanned = 0
    for episode_file in unscanned:
        probe_data = probe_file(ffprobe, episode_file.file_path)
        if probe_data:
            for field, value in probe_data.items():
                setattr(episode_file, field, value)
            scanned += 1

    if scanned:
        db.commit()
        logger.info(f"FFprobe scanned {scanned} previously unscanned episode file(s)")
    return scanned


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
