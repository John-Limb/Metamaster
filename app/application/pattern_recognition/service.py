"""Pattern recognition service for classifying media files as movies or TV shows"""

import re
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """Data class for classification results"""

    type: str  # "movie" or "tv_show"
    title: Optional[str] = None
    show_name: Optional[str] = None
    year: Optional[int] = None
    season: Optional[int] = None
    episode: Optional[int] = None
    confidence: str = "medium"  # "high", "medium", "low"
    pattern_matched: str = "none"

    def to_dict(self) -> Dict:
        """Convert to dictionary, excluding None values"""
        result = {
            "type": self.type,
            "confidence": self.confidence,
            "pattern_matched": self.pattern_matched,
        }

        if self.title:
            result["title"] = self.title
        if self.show_name:
            result["show_name"] = self.show_name
        if self.year:
            result["year"] = self.year
        if self.season is not None:
            result["season"] = self.season
        if self.episode is not None:
            result["episode"] = self.episode

        return result


class PatternRecognitionService:
    """Service for recognizing and classifying media files based on filename patterns"""

    # Regex patterns for TV show detection
    TV_SHOW_PATTERNS = [
        # Standard format: S01E01, s01e01, etc. (with optional separators before)
        r"[._-]?[Ss](\d{1,2})[._-]?[Ee](\d{1,2})",
        # Format: Season 1 Episode 1
        r"[Ss]eason\s+(\d{1,2})\s+[Ee]pisode\s+(\d{1,2})",
        # Format: 1x01, 1x1
        r"(\d{1,2})x(\d{1,2})",
    ]

    # Regex patterns for movie detection (Title Year)
    MOVIE_PATTERNS = [
        # Format: Title (Year) or Title [Year]
        r"(.+?)\s*[\(\[](\d{4})[\)\]]",
        # Format: Title Year (with various separators, including dots/hyphens/underscores)
        r"(.+?)[._-](\d{4})(?:[._-]|$)",
        # Format: Title Year (space separated)
        r"(.+?)\s+(\d{4})\s*(?:\.|$)",
    ]

    def __init__(self):
        """Initialize the pattern recognition service"""
        self.tv_show_regex = [re.compile(pattern) for pattern in self.TV_SHOW_PATTERNS]
        self.movie_regex = [re.compile(pattern) for pattern in self.MOVIE_PATTERNS]

    def classify_file(self, filename: str) -> Dict:
        """
        Classify a file as a movie or TV show based on filename patterns.

        Args:
            filename: The filename to classify (can include path)

        Returns:
            Dictionary with classification result containing:
            - type: "movie" or "tv_show"
            - title/show_name: Extracted name
            - year: For movies (if present)
            - season/episode: For TV shows (if present)
            - confidence: "high", "medium", or "low"
            - pattern_matched: Which pattern was matched
        """
        # Extract just the filename without extension
        base_name = Path(filename).stem

        # Try TV show patterns first (more specific)
        tv_result = self._match_tv_show_pattern(base_name)
        if tv_result:
            return tv_result.to_dict()

        # Try movie patterns
        movie_result = self._match_movie_pattern(base_name)
        if movie_result:
            return movie_result.to_dict()

        # Fallback classification
        fallback_result = self._fallback_classification(base_name)
        return fallback_result.to_dict()

    def extract_movie_info(self, filename: str) -> Dict:
        """
        Extract movie-specific information from filename.

        Args:
            filename: The filename to extract info from

        Returns:
            Dictionary with movie info (title, year) or empty dict if not a movie
        """
        base_name = Path(filename).stem
        result = self._match_movie_pattern(base_name)

        if result:
            return {
                "title": result.title,
                "year": result.year,
                "confidence": result.confidence,
            }
        return {}

    def extract_tv_show_info(self, filename: str) -> Dict:
        """
        Extract TV show-specific information from filename.

        Args:
            filename: The filename to extract info from

        Returns:
            Dictionary with TV show info (show_name, season, episode) or empty dict if not a TV show
        """
        base_name = Path(filename).stem
        result = self._match_tv_show_pattern(base_name)

        if result:
            return {
                "show_name": result.show_name,
                "season": result.season,
                "episode": result.episode,
                "confidence": result.confidence,
            }
        return {}

    def is_movie(self, filename: str) -> bool:
        """
        Quick check if a file is likely a movie.

        Args:
            filename: The filename to check

        Returns:
            True if file matches movie patterns, False otherwise
        """
        base_name = Path(filename).stem
        return self._match_movie_pattern(base_name) is not None

    def is_tv_show(self, filename: str) -> bool:
        """
        Quick check if a file is likely a TV show.

        Args:
            filename: The filename to check

        Returns:
            True if file matches TV show patterns, False otherwise
        """
        base_name = Path(filename).stem
        return self._match_tv_show_pattern(base_name) is not None

    def _match_tv_show_pattern(self, filename: str) -> Optional[ClassificationResult]:
        """
        Try to match TV show patterns in filename.

        Args:
            filename: The filename to match

        Returns:
            ClassificationResult if matched, None otherwise
        """
        for pattern_idx, regex in enumerate(self.tv_show_regex):
            match = regex.search(filename)
            if match:
                season, episode = self._extract_season_episode(match, pattern_idx)

                # Extract show name (everything before the season/episode indicator)
                show_name = self._extract_show_name_from_tv(filename, match)

                confidence = "high" if season and episode else "medium"
                pattern_name = self._get_tv_pattern_name(pattern_idx)

                return ClassificationResult(
                    type="tv_show",
                    show_name=show_name,
                    season=season,
                    episode=episode,
                    confidence=confidence,
                    pattern_matched=pattern_name,
                )

        return None

    def _match_movie_pattern(self, filename: str) -> Optional[ClassificationResult]:
        """
        Try to match movie patterns in filename.

        Args:
            filename: The filename to match

        Returns:
            ClassificationResult if matched, None otherwise
        """
        for pattern_idx, regex in enumerate(self.movie_regex):
            match = regex.search(filename)
            if match:
                title, year = self._extract_title_year(match, pattern_idx)

                # Validate year is reasonable (between 1800 and current year + 10)
                if year and (year < 1800 or year > 2100):
                    continue

                confidence = "high" if year else "medium"
                pattern_name = self._get_movie_pattern_name(pattern_idx)

                return ClassificationResult(
                    type="movie",
                    title=title,
                    year=year,
                    confidence=confidence,
                    pattern_matched=pattern_name,
                )

        return None

    def _fallback_classification(self, filename: str) -> ClassificationResult:
        """
        Fallback classification when no patterns match.

        Args:
            filename: The filename to classify

        Returns:
            ClassificationResult with fallback classification
        """
        # Check for any season/episode indicators
        if re.search(r"[Ss]eason|[Ee]pisode|[Ss]\d{1,2}[Ee]\d{1,2}|\d{1,2}x\d{1,2}", filename):
            return ClassificationResult(
                type="tv_show",
                show_name=self._clean_filename(filename),
                confidence="low",
                pattern_matched="fallback_tv_indicators",
            )

        # Default to movie classification
        return ClassificationResult(
            type="movie",
            title=self._clean_filename(filename),
            confidence="low",
            pattern_matched="fallback_default",
        )

    def _extract_season_episode(
        self, match, pattern_idx: int
    ) -> Tuple[Optional[int], Optional[int]]:
        """
        Extract season and episode numbers from regex match.

        Args:
            match: Regex match object
            pattern_idx: Index of the pattern used

        Returns:
            Tuple of (season, episode) or (None, None)
        """
        try:
            season = int(match.group(1))
            episode = int(match.group(2))
            return season, episode
        except (IndexError, ValueError):
            return None, None

    def _extract_title_year(self, match, pattern_idx: int) -> Tuple[Optional[str], Optional[int]]:
        """
        Extract title and year from regex match.

        Args:
            match: Regex match object
            pattern_idx: Index of the pattern used

        Returns:
            Tuple of (title, year) or (None, None)
        """
        try:
            title = match.group(1).strip()
            year_str = match.group(2)
            year = int(year_str) if year_str else None

            # Clean up title
            title = self._clean_title(title)

            return title, year
        except (IndexError, ValueError):
            return None, None

    def _extract_show_name_from_tv(self, filename: str, match) -> str:
        """
        Extract show name from TV show filename.

        Args:
            filename: The full filename
            match: Regex match object

        Returns:
            Cleaned show name
        """
        # Get the position where the match starts
        match_start = match.start()

        # Extract everything before the match
        show_name = filename[:match_start].strip()

        # Clean up the show name
        show_name = self._clean_filename(show_name)

        return show_name if show_name else "Unknown"

    def _clean_title(self, title: str) -> str:
        """
        Clean up a movie title by removing extra separators and whitespace.

        Args:
            title: The title to clean

        Returns:
            Cleaned title
        """
        # Replace common separators with spaces
        title = re.sub(r"[._-]+", " ", title)
        # Remove extra whitespace
        title = re.sub(r"\s+", " ", title).strip()
        return title

    def _clean_filename(self, filename: str) -> str:
        """
        Clean up a filename by removing extra separators and whitespace.

        Args:
            filename: The filename to clean

        Returns:
            Cleaned filename
        """
        # Replace common separators with spaces
        filename = re.sub(r"[._-]+", " ", filename)
        # Remove extra whitespace
        filename = re.sub(r"\s+", " ", filename).strip()
        return filename

    def _get_tv_pattern_name(self, pattern_idx: int) -> str:
        """Get the name of the TV pattern matched."""
        names = [
            "standard_sxxexx",
            "season_episode_text",
            "number_x_format",
        ]
        return names[pattern_idx] if pattern_idx < len(names) else "unknown"

    def _get_movie_pattern_name(self, pattern_idx: int) -> str:
        """Get the name of the movie pattern matched."""
        names = [
            "title_year_brackets",
            "title_year_separators",
            "title_year_space",
        ]
        return names[pattern_idx] if pattern_idx < len(names) else "unknown"
