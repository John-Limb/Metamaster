"""Shared scanning helpers for movie file discovery and FFprobe analysis."""

import logging
import re
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import MOVIE_DIR, settings
from app.domain.files.models import FileItem
from app.domain.movies.models import Movie, MovieFile
from app.infrastructure.file_system.ffprobe_wrapper import FFProbeWrapper
from app.services_impl import TMDBService
from app.tasks.async_helpers import run_async

logger = logging.getLogger(__name__)


def title_from_filename(filename: str) -> tuple[str, int | None]:
    """Extract a human-readable title and optional year from a video filename.

    Examples:
        'The.Matrix.1999.1080p.mkv' -> ('The Matrix', 1999)
        'Inception (2010).mp4'       -> ('Inception', 2010)
        'my_movie.avi'               -> ('My Movie', None)
    """
    stem = Path(filename).stem

    year = None
    year_match = re.search(r"[\.\s\(](\d{4})[\.\s\)]", stem)
    if year_match:
        candidate = int(year_match.group(1))
        if 1900 <= candidate <= 2099:
            year = candidate
            stem = stem[: year_match.start()]

    title = stem.replace(".", " ").replace("_", " ").strip()
    title = re.sub(r"\s+", " ", title)
    return title, year


_IMDB_BRACE_PATTERN = re.compile(r"\{imdb-(?P<id>tt\d{7,8})\}", re.IGNORECASE)
_IMDB_PAREN_PATTERN = re.compile(r"\((?P<id>tt\d{7,8})\)")
_IMDB_BARE_PATTERN = re.compile(r"\b(?P<id>tt\d{7,8})\b")
_TMDB_PATTERN = re.compile(r"\{tmdb-(?P<id>\d+)\}", re.IGNORECASE)

_IMDB_PATTERNS = [_IMDB_BRACE_PATTERN, _IMDB_PAREN_PATTERN, _IMDB_BARE_PATTERN]


def extract_external_id_from_path(file_path: str) -> str | None:
    """Parse an IMDB or TMDB ID embedded in a file path or parent folder name.

    Checks the filename stem and the immediate parent directory name.
    Returns the ID string (e.g. 'tt1375666' or '1396'), or None if not found.
    Priority: TMDB pattern > IMDB patterns.
    """
    path = Path(file_path)
    candidates = [path.stem, path.parent.name]
    for text in candidates:
        m = _TMDB_PATTERN.search(text)
        if m:
            return m.group("id")
        for pattern in _IMDB_PATTERNS:
            m = pattern.search(text)
            if m:
                return m.group("id")
    return None


def get_ffprobe() -> FFProbeWrapper | None:
    """Attempt to initialise FFProbeWrapper; return None if ffprobe is missing."""
    try:
        return FFProbeWrapper()
    except RuntimeError:
        logger.warning("ffprobe not available — skipping media analysis")
        return None


def probe_file(ffprobe: FFProbeWrapper, file_path: str) -> dict:
    """Run FFprobe on a single file and return MovieFile-compatible fields.

    Returns an empty dict on any error so callers can safely unpack.
    """
    try:
        metadata = ffprobe.get_metadata(file_path)
        if "error" in metadata:
            logger.warning(f"FFprobe error for {file_path}: {metadata['error']}")
            return {}

        resolution = metadata.get("resolution", {})
        codecs = metadata.get("codecs", {})
        bitrate = metadata.get("bitrate", {})
        duration = metadata.get("duration", -1)

        result = {}

        w = resolution.get("width")
        h = resolution.get("height")
        if w and h:
            result["resolution"] = f"{w}x{h}"

        if codecs.get("video") and codecs["video"] != "Unknown":
            result["codec_video"] = codecs["video"]
        if codecs.get("audio") and codecs["audio"] != "Unknown":
            result["codec_audio"] = codecs["audio"]

        total_br = bitrate.get("total", "")
        if isinstance(total_br, str) and total_br != "Unknown":
            try:
                if "Mbps" in total_br:
                    result["bitrate"] = int(float(total_br.replace(" Mbps", "")) * 1000)
                elif "kbps" in total_br:
                    result["bitrate"] = int(float(total_br.replace(" kbps", "")))
            except (ValueError, TypeError):
                pass

        if isinstance(duration, (int, float)) and duration > 0:
            result["duration"] = int(duration)

        # Extract audio channel count
        audio_stream = next(
            (
                s
                for s in metadata.get("streams", {})
                if isinstance(s, dict) and s.get("codec_type") == "audio"
            ),
            None,
        )
        if audio_stream and audio_stream.get("channels"):
            try:
                result["audio_channels"] = int(audio_stream["channels"])
            except (ValueError, TypeError):
                pass

        return result
    except Exception as e:
        logger.warning(f"FFprobe failed for {file_path}: {e}")
        return {}


def create_movies_from_files(db: Session) -> int:
    """Create Movie records for video files under MOVIE_DIR that lack one.

    Also runs FFprobe on each new file to populate technical metadata.
    """
    video_extensions = {ext.lower() for ext in settings.watch_extensions}
    movie_dir_resolved = str(Path(MOVIE_DIR).resolve())

    ffprobe = get_ffprobe()

    # Backfill: mark any FileItem as indexed if a MovieFile already references its path
    indexed_paths = {row[0] for row in db.query(MovieFile.file_path).all()}
    backfilled = (
        db.query(FileItem)
        .filter(FileItem.is_indexed.is_(False), FileItem.path.in_(indexed_paths))
        .update({"is_indexed": True}, synchronize_session=False)
    )
    if backfilled:
        db.commit()
        logger.info(f"[Movie] Backfilled is_indexed=True on {backfilled} existing FileItem(s)")

    existing_paths = indexed_paths

    movie_files = (
        db.query(FileItem)
        .filter(
            FileItem.type == "file",
            FileItem.path.startswith(movie_dir_resolved),
        )
        .all()
    )

    created = 0
    for fi in movie_files:
        ext = Path(fi.path).suffix.lower()
        if ext not in video_extensions:
            continue
        if fi.path in existing_paths:
            continue

        logger.info(f"[Movie] Detected: {fi.name}")

        title, year = title_from_filename(fi.name)
        if not title:
            logger.debug(f"[Movie] Could not parse title from: {fi.name} — skipping")
            continue

        year_str = str(year) if year else "unknown year"
        logger.info(f"[Movie] Parsed: '{title}' ({year_str})")

        detected_id = extract_external_id_from_path(fi.path)
        if detected_id:
            logger.info(f"[Movie] External ID detected in path: {detected_id}")

        movie = Movie(
            title=title,
            year=year,
            enrichment_status="local_only",
            detected_external_id=detected_id,
        )
        db.add(movie)
        db.flush()

        probe_data = probe_file(ffprobe, fi.path) if ffprobe else {}
        if probe_data:
            resolution = probe_data.get("resolution", "?")
            video = probe_data.get("codec_video", "?")
            audio = probe_data.get("codec_audio", "?")
            logger.info(f"[Movie] FFprobe: {resolution}, {video}/{audio}")
        else:
            logger.debug(f"[Movie] FFprobe skipped or unavailable for: {fi.name}")

        movie_file = MovieFile(
            movie_id=movie.id,
            file_path=fi.path,
            file_size=fi.size,
            resolution=probe_data.get("resolution"),
            codec_video=probe_data.get("codec_video"),
            codec_audio=probe_data.get("codec_audio"),
            audio_channels=probe_data.get("audio_channels"),
            bitrate=probe_data.get("bitrate"),
            duration=probe_data.get("duration"),
        )
        db.add(movie_file)
        fi.is_indexed = True
        existing_paths.add(fi.path)
        created += 1
        logger.info(f"[Movie] Record created: '{title}' (ID: {movie.id})")

    if created:
        db.commit()
        logger.info(f"[Movie] {created} new record(s) saved to database")
    return created


def enrich_new_movies(db: Session) -> int:
    """Search TMDB for movies missing a tmdb_id and populate metadata.

    Returns the number of movies successfully enriched.
    """
    movies = db.query(Movie).filter(Movie.tmdb_id.is_(None)).all()
    if not movies:
        return 0

    # Collect existing tmdb_ids to avoid unique-constraint violations
    existing_tmdb_ids = {
        row[0] for row in db.query(Movie.tmdb_id).filter(Movie.tmdb_id.isnot(None)).all()
    }

    enriched = 0
    for movie in movies:
        try:
            year_str = str(movie.year) if movie.year else "unknown year"
            logger.info(f"[Movie] Enriching: '{movie.title}' ({year_str})")

            # Step 1: Search TMDB by title/year
            logger.info(f"[Movie] TMDB search: '{movie.title}'")
            search_raw = run_async(TMDBService.search_movie(db, movie.title, movie.year))
            if not search_raw:
                logger.info(f"[Movie] TMDB: no results for '{movie.title}'")
                continue
            search_parsed = TMDBService.parse_movie_search_response(search_raw)
            if not search_parsed or not search_parsed.get("search_results"):
                logger.info(f"[Movie] TMDB: no match for '{movie.title}'")
                continue

            tmdb_id = search_parsed["search_results"][0].get("tmdb_id")
            if not tmdb_id or tmdb_id in existing_tmdb_ids:
                logger.debug(f"[Movie] TMDB: duplicate or missing ID for '{movie.title}' — skipping")
                continue

            logger.info(f"[Movie] TMDB match: '{movie.title}' → {tmdb_id}")

            # Step 2: Fetch full details
            logger.info(f"[Movie] TMDB fetching details: {tmdb_id}")
            detail_raw = run_async(TMDBService.get_movie_details(db, tmdb_id))
            if not detail_raw:
                movie.tmdb_id = tmdb_id
                existing_tmdb_ids.add(tmdb_id)
                enriched += 1
                continue

            detail = TMDBService.parse_movie_details_response(detail_raw)
            if not detail:
                movie.tmdb_id = tmdb_id
                existing_tmdb_ids.add(tmdb_id)
                enriched += 1
                continue

            # Step 3: Update fields
            movie.tmdb_id = tmdb_id
            movie.plot = detail.get("plot", movie.plot)
            movie.rating = detail.get("rating", movie.rating)
            movie.runtime = detail.get("runtime", movie.runtime)
            movie.genres = detail.get("genres", movie.genres)
            poster = detail.get("poster")
            if poster:
                movie.poster_url = poster
            existing_tmdb_ids.add(tmdb_id)
            enriched += 1

            rating_str = f"★{movie.rating}" if movie.rating else "no rating"
            genres_str = ", ".join(movie.genres) if isinstance(movie.genres, list) else str(movie.genres or "")
            logger.info(f"[Movie] Enriched: '{movie.title}' — {rating_str}, {genres_str}")

        except Exception:
            logger.warning(f"[Movie] Failed to enrich '{movie.title}' (ID: {movie.id})", exc_info=True)

    if enriched:
        db.commit()
        logger.info(f"[Movie] {enriched} movie(s) enriched with TMDB metadata")
    return enriched


def probe_unscanned_movies(db: Session) -> int:
    """Run FFprobe on movie files that are missing resolution or audio_channels data.

    Returns the number of files scanned.
    """
    ffprobe = get_ffprobe()
    if not ffprobe:
        return 0

    unscanned = (
        db.query(MovieFile)
        .filter(
            (MovieFile.resolution.is_(None))
            | (MovieFile.resolution == "")
            | (MovieFile.audio_channels.is_(None))
        )
        .all()
    )
    if not unscanned:
        return 0

    scanned = 0
    for movie_file in unscanned:
        probe_data = probe_file(ffprobe, movie_file.file_path)
        if probe_data:
            for field, value in probe_data.items():
                setattr(movie_file, field, value)
            scanned += 1

    if scanned:
        db.commit()
        logger.info(f"FFprobe scanned {scanned} previously unscanned movie file(s)")
    return scanned


def probe_movie_file(db: Session, movie_id: int) -> Movie:
    """Run FFprobe on the primary file for a given movie and update its MovieFile record.

    Raises ValueError if the movie or its file is not found.
    Raises RuntimeError if ffprobe is not available.
    """
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise ValueError(f"Movie {movie_id} not found")

    movie_file = db.query(MovieFile).filter(MovieFile.movie_id == movie_id).first()
    if not movie_file:
        raise ValueError(f"No file associated with movie {movie_id}")

    ffprobe = get_ffprobe()
    if not ffprobe:
        raise RuntimeError("ffprobe is not available on this system")

    probe_data = probe_file(ffprobe, movie_file.file_path)
    if probe_data:
        for field, value in probe_data.items():
            setattr(movie_file, field, value)
        db.commit()
        db.refresh(movie)

    return movie
