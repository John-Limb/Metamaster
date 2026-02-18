"""Tests for the PatternRecognitionService"""

import pytest
from app.application.pattern_recognition.service import PatternRecognitionService


@pytest.fixture
def service():
    """Create a PatternRecognitionService instance for testing"""
    return PatternRecognitionService()


class TestMoviePatternMatching:
    """Tests for movie pattern matching"""

    def test_movie_title_year_parentheses(self, service):
        """Test movie pattern: Title (Year)"""
        result = service.classify_file("The Matrix (1999).mp4")
        assert result["type"] == "movie"
        assert result["title"] == "The Matrix"
        assert result["year"] == 1999
        assert result["confidence"] == "high"
        assert result["pattern_matched"] == "title_year_brackets"

    def test_movie_title_year_brackets(self, service):
        """Test movie pattern: Title [Year]"""
        result = service.classify_file("Inception [2010].mkv")
        assert result["type"] == "movie"
        assert result["title"] == "Inception"
        assert result["year"] == 2010
        assert result["confidence"] == "high"

    def test_movie_title_year_space(self, service):
        """Test movie pattern: Title Year (space separated)"""
        result = service.classify_file("Interstellar 2014.mp4")
        assert result["type"] == "movie"
        assert result["title"] == "Interstellar"
        assert result["year"] == 2014
        assert result["confidence"] == "high"

    def test_movie_title_with_multiple_words(self, service):
        """Test movie with multi-word title"""
        result = service.classify_file("The Lord of the Rings (2001).mp4")
        assert result["type"] == "movie"
        assert result["title"] == "The Lord of the Rings"
        assert result["year"] == 2001

    def test_movie_title_with_dots_separator(self, service):
        """Test movie with dots as separators"""
        result = service.classify_file("The.Dark.Knight.2008.mp4")
        assert result["type"] == "movie"
        assert result["title"] == "The Dark Knight"
        assert result["year"] == 2008

    def test_movie_title_with_hyphens(self, service):
        """Test movie with hyphens as separators"""
        result = service.classify_file("The-Shawshank-Redemption-1994.mkv")
        assert result["type"] == "movie"
        assert result["title"] == "The Shawshank Redemption"
        assert result["year"] == 1994

    def test_movie_title_with_underscores(self, service):
        """Test movie with underscores as separators"""
        result = service.classify_file("Pulp_Fiction_1994.avi")
        assert result["type"] == "movie"
        assert result["title"] == "Pulp Fiction"
        assert result["year"] == 1994

    def test_movie_title_mixed_separators(self, service):
        """Test movie with mixed separators"""
        result = service.classify_file("The.Matrix-Reloaded_2003.mp4")
        assert result["type"] == "movie"
        assert result["title"] == "The Matrix Reloaded"
        assert result["year"] == 2003

    def test_movie_extract_movie_info(self, service):
        """Test extract_movie_info method"""
        info = service.extract_movie_info("Avatar (2009).mp4")
        assert info["title"] == "Avatar"
        assert info["year"] == 2009
        assert info["confidence"] == "high"

    def test_movie_is_movie_true(self, service):
        """Test is_movie returns True for movie files"""
        assert service.is_movie("Titanic (1997).mp4") is True
        assert service.is_movie("Gladiator 2000.mkv") is True

    def test_movie_is_movie_false(self, service):
        """Test is_movie returns False for non-movie files"""
        assert service.is_movie("Breaking Bad S01E01.mp4") is False
        assert service.is_movie("Random File.mp4") is False

    def test_movie_year_validation(self, service):
        """Test that invalid years are rejected"""
        # Year too old
        result = service.classify_file("Some Movie (1234).mp4")
        assert result["type"] == "movie"
        # Should not match as movie due to invalid year
        # Falls back to default classification

    def test_movie_without_year(self, service):
        """Test movie classification without year (fallback)"""
        result = service.classify_file("Some Random Movie.mp4")
        assert result["type"] == "movie"
        assert result["confidence"] == "low"


class TestTVShowPatternMatching:
    """Tests for TV show pattern matching"""

    def test_tv_show_standard_format_uppercase(self, service):
        """Test TV show pattern: S01E01"""
        result = service.classify_file("Breaking Bad S01E01.mp4")
        assert result["type"] == "tv_show"
        assert result["show_name"] == "Breaking Bad"
        assert result["season"] == 1
        assert result["episode"] == 1
        assert result["confidence"] == "high"
        assert result["pattern_matched"] == "standard_sxxexx"

    def test_tv_show_standard_format_lowercase(self, service):
        """Test TV show pattern: s01e01"""
        result = service.classify_file("Game of Thrones s08e06.mkv")
        assert result["type"] == "tv_show"
        assert result["show_name"] == "Game of Thrones"
        assert result["season"] == 8
        assert result["episode"] == 6

    def test_tv_show_mixed_case(self, service):
        """Test TV show pattern: S01e01 (mixed case)"""
        result = service.classify_file("The Office S09E23.mp4")
        assert result["type"] == "tv_show"
        assert result["show_name"] == "The Office"
        assert result["season"] == 9
        assert result["episode"] == 23

    def test_tv_show_number_x_format(self, service):
        """Test TV show pattern: 1x01"""
        result = service.classify_file("Friends 10x18.mp4")
        assert result["type"] == "tv_show"
        assert result["show_name"] == "Friends"
        assert result["season"] == 10
        assert result["episode"] == 18
        assert result["pattern_matched"] == "number_x_format"

    def test_tv_show_season_episode_text(self, service):
        """Test TV show pattern: Season 1 Episode 1"""
        result = service.classify_file("Stranger Things Season 1 Episode 1.mp4")
        assert result["type"] == "tv_show"
        assert result["show_name"] == "Stranger Things"
        assert result["season"] == 1
        assert result["episode"] == 1
        assert result["pattern_matched"] == "season_episode_text"

    def test_tv_show_with_dots_separator(self, service):
        """Test TV show with dots as separators"""
        result = service.classify_file("The.Crown.S02E10.mkv")
        assert result["type"] == "tv_show"
        assert result["show_name"] == "The Crown"
        assert result["season"] == 2
        assert result["episode"] == 10

    def test_tv_show_with_hyphens(self, service):
        """Test TV show with hyphens as separators"""
        result = service.classify_file("Westworld - S01E01.mp4")
        assert result["type"] == "tv_show"
        assert result["show_name"] == "Westworld"
        assert result["season"] == 1
        assert result["episode"] == 1

    def test_tv_show_with_underscores(self, service):
        """Test TV show with underscores as separators"""
        result = service.classify_file("The_Mandalorian_S02E08.mkv")
        assert result["type"] == "tv_show"
        assert result["show_name"] == "The Mandalorian"
        assert result["season"] == 2
        assert result["episode"] == 8

    def test_tv_show_mixed_separators(self, service):
        """Test TV show with mixed separators"""
        result = service.classify_file("The.Office-S07_E01.mp4")
        assert result["type"] == "tv_show"
        assert result["show_name"] == "The Office"
        assert result["season"] == 7
        assert result["episode"] == 1

    def test_tv_show_double_digit_season_episode(self, service):
        """Test TV show with double-digit season and episode"""
        result = service.classify_file("Supernatural S15E19.mp4")
        assert result["type"] == "tv_show"
        assert result["season"] == 15
        assert result["episode"] == 19

    def test_tv_show_single_digit_season_episode(self, service):
        """Test TV show with single-digit season and episode"""
        result = service.classify_file("Sherlock S4E3.mp4")
        assert result["type"] == "tv_show"
        assert result["season"] == 4
        assert result["episode"] == 3

    def test_tv_show_extract_tv_show_info(self, service):
        """Test extract_tv_show_info method"""
        info = service.extract_tv_show_info("Narcos S02E09.mp4")
        assert info["show_name"] == "Narcos"
        assert info["season"] == 2
        assert info["episode"] == 9
        assert info["confidence"] == "high"

    def test_tv_show_is_tv_show_true(self, service):
        """Test is_tv_show returns True for TV show files"""
        assert service.is_tv_show("Breaking Bad S01E01.mp4") is True
        assert service.is_tv_show("Friends 10x18.mp4") is True

    def test_tv_show_is_tv_show_false(self, service):
        """Test is_tv_show returns False for non-TV show files"""
        assert service.is_tv_show("The Matrix (1999).mp4") is False
        assert service.is_tv_show("Random File.mp4") is False

    def test_tv_show_with_year_in_name(self, service):
        """Test TV show that has a year in the name"""
        result = service.classify_file("Doctor Who 2005 S01E01.mp4")
        assert result["type"] == "tv_show"
        assert result["season"] == 1
        assert result["episode"] == 1

    def test_tv_show_long_name(self, service):
        """Test TV show with long multi-word name"""
        result = service.classify_file("It's Always Sunny in Philadelphia S15E01.mp4")
        assert result["type"] == "tv_show"
        assert result["show_name"] == "It's Always Sunny in Philadelphia"
        assert result["season"] == 15
        assert result["episode"] == 1


class TestFallbackClassification:
    """Tests for fallback classification"""

    def test_fallback_tv_indicators(self, service):
        """Test fallback classification with TV indicators"""
        result = service.classify_file("Some Show Season 1.mp4")
        assert result["type"] == "tv_show"
        assert result["confidence"] == "low"
        assert result["pattern_matched"] == "fallback_tv_indicators"

    def test_fallback_episode_indicator(self, service):
        """Test fallback classification with episode indicator"""
        result = service.classify_file("Some Show Episode 5.mp4")
        assert result["type"] == "tv_show"
        assert result["confidence"] == "low"

    def test_fallback_default_movie(self, service):
        """Test fallback classification defaults to movie"""
        result = service.classify_file("Random File Name.mp4")
        assert result["type"] == "movie"
        assert result["confidence"] == "low"
        assert result["pattern_matched"] == "fallback_default"

    def test_fallback_with_special_characters(self, service):
        """Test fallback classification with special characters"""
        result = service.classify_file("Some-File_Name.With.Dots.mp4")
        assert result["type"] == "movie"
        assert result["confidence"] == "low"


class TestEdgeCases:
    """Tests for edge cases and special scenarios"""

    def test_file_with_path(self, service):
        """Test classification with full file path"""
        result = service.classify_file("/path/to/movies/The Matrix (1999).mp4")
        assert result["type"] == "movie"
        assert result["title"] == "The Matrix"
        assert result["year"] == 1999

    def test_file_with_multiple_extensions(self, service):
        """Test file with multiple extensions"""
        result = service.classify_file("Breaking Bad S01E01.tar.mp4")
        assert result["type"] == "tv_show"
        assert result["show_name"] == "Breaking Bad"

    def test_movie_with_apostrophe(self, service):
        """Test movie title with apostrophe"""
        result = service.classify_file("It's a Wonderful Life (1946).mp4")
        assert result["type"] == "movie"
        assert result["title"] == "It's a Wonderful Life"
        assert result["year"] == 1946

    def test_tv_show_with_apostrophe(self, service):
        """Test TV show name with apostrophe"""
        result = service.classify_file("It's Always Sunny S01E01.mp4")
        assert result["type"] == "tv_show"
        assert result["show_name"] == "It's Always Sunny"

    def test_movie_with_colon(self, service):
        """Test movie title with colon"""
        result = service.classify_file("Star Wars: A New Hope (1977).mp4")
        assert result["type"] == "movie"
        assert result["title"] == "Star Wars: A New Hope"
        assert result["year"] == 1977

    def test_tv_show_with_colon(self, service):
        """Test TV show name with colon"""
        result = service.classify_file("Doctor Who: The Eleventh Hour S05E01.mp4")
        assert result["type"] == "tv_show"
        assert result["season"] == 5
        assert result["episode"] == 1

    def test_movie_year_at_end_with_dot(self, service):
        """Test movie year at end with dot separator"""
        result = service.classify_file("Inception.2010.mp4")
        assert result["type"] == "movie"
        assert result["title"] == "Inception"
        assert result["year"] == 2010

    def test_tv_show_priority_over_movie(self, service):
        """Test that TV show patterns take priority over movie patterns"""
        # File that could match both patterns
        result = service.classify_file("Breaking Bad 2008 S01E01.mp4")
        assert result["type"] == "tv_show"
        assert result["season"] == 1
        assert result["episode"] == 1

    def test_empty_filename(self, service):
        """Test with empty filename"""
        result = service.classify_file(".mp4")
        assert result["type"] in ["movie", "tv_show"]

    def test_filename_with_only_extension(self, service):
        """Test filename with only extension"""
        result = service.classify_file("mp4")
        assert result["type"] in ["movie", "tv_show"]

    def test_movie_with_leading_zeros(self, service):
        """Test movie year with leading zeros (should not match)"""
        result = service.classify_file("Some Movie (0999).mp4")
        # Year 0999 is too old, should not match as movie
        assert result["type"] == "movie"

    def test_tv_show_leading_zeros(self, service):
        """Test TV show with leading zeros in season/episode"""
        result = service.classify_file("Show Name S01E01.mp4")
        assert result["type"] == "tv_show"
        assert result["season"] == 1
        assert result["episode"] == 1

    def test_tv_show_no_leading_zeros(self, service):
        """Test TV show without leading zeros"""
        result = service.classify_file("Show Name S1E1.mp4")
        assert result["type"] == "tv_show"
        assert result["season"] == 1
        assert result["episode"] == 1

    def test_classification_result_to_dict(self, service):
        """Test that classification result properly converts to dict"""
        result = service.classify_file("The Matrix (1999).mp4")
        assert isinstance(result, dict)
        assert "type" in result
        assert "confidence" in result
        assert "pattern_matched" in result

    def test_movie_extract_returns_empty_for_tv_show(self, service):
        """Test that extract_movie_info returns empty dict for TV shows"""
        info = service.extract_movie_info("Breaking Bad S01E01.mp4")
        assert info == {}

    def test_tv_show_extract_returns_empty_for_movie(self, service):
        """Test that extract_tv_show_info returns empty dict for movies"""
        info = service.extract_tv_show_info("The Matrix (1999).mp4")
        assert info == {}

    def test_multiple_years_in_filename(self, service):
        """Test filename with multiple years"""
        result = service.classify_file("Movie 2000 2001 (1999).mp4")
        assert result["type"] == "movie"
        assert result["year"] == 1999

    def test_tv_show_multiple_season_episode_patterns(self, service):
        """Test TV show with multiple season/episode patterns"""
        result = service.classify_file("Show S01E01 1x01.mp4")
        assert result["type"] == "tv_show"
        # Should match the first pattern found

    def test_case_insensitive_matching(self, service):
        """Test that matching is case insensitive"""
        result1 = service.classify_file("Breaking Bad S01E01.mp4")
        result2 = service.classify_file("Breaking Bad s01e01.mp4")
        result3 = service.classify_file("Breaking Bad S01e01.mp4")

        assert result1["type"] == result2["type"] == result3["type"] == "tv_show"
        assert result1["season"] == result2["season"] == result3["season"] == 1
        assert result1["episode"] == result2["episode"] == result3["episode"] == 1

    def test_movie_with_numbers_in_title(self, service):
        """Test movie with numbers in title"""
        result = service.classify_file("2001: A Space Odyssey (1968).mp4")
        assert result["type"] == "movie"
        assert result["year"] == 1968

    def test_tv_show_with_numbers_in_name(self, service):
        """Test TV show with numbers in name"""
        result = service.classify_file("24 S01E01.mp4")
        assert result["type"] == "tv_show"
        assert result["show_name"] == "24"
        assert result["season"] == 1
        assert result["episode"] == 1


class TestConfidenceLevels:
    """Tests for confidence level assignment"""

    def test_movie_high_confidence_with_year(self, service):
        """Test movie has high confidence when year is present"""
        result = service.classify_file("The Matrix (1999).mp4")
        assert result["confidence"] == "high"

    def test_tv_show_high_confidence_with_season_episode(self, service):
        """Test TV show has high confidence when season and episode are present"""
        result = service.classify_file("Breaking Bad S01E01.mp4")
        assert result["confidence"] == "high"

    def test_fallback_low_confidence(self, service):
        """Test fallback classification has low confidence"""
        result = service.classify_file("Random File.mp4")
        assert result["confidence"] == "low"

    def test_fallback_tv_low_confidence(self, service):
        """Test fallback TV classification has low confidence"""
        result = service.classify_file("Some Show Season 1.mp4")
        assert result["confidence"] == "low"


class TestPatternNames:
    """Tests for pattern name identification"""

    def test_movie_pattern_name_brackets(self, service):
        """Test movie pattern name for brackets format"""
        result = service.classify_file("The Matrix (1999).mp4")
        assert result["pattern_matched"] == "title_year_brackets"

    def test_movie_pattern_name_space(self, service):
        """Test movie pattern name for space format"""
        result = service.classify_file("Inception 2010.mp4")
        assert result["pattern_matched"] == "title_year_space"

    def test_tv_show_pattern_name_standard(self, service):
        """Test TV show pattern name for standard format"""
        result = service.classify_file("Breaking Bad S01E01.mp4")
        assert result["pattern_matched"] == "standard_sxxexx"

    def test_tv_show_pattern_name_text(self, service):
        """Test TV show pattern name for text format"""
        result = service.classify_file("Show Season 1 Episode 1.mp4")
        assert result["pattern_matched"] == "season_episode_text"

    def test_tv_show_pattern_name_number_x(self, service):
        """Test TV show pattern name for number x format"""
        result = service.classify_file("Show 1x01.mp4")
        assert result["pattern_matched"] == "number_x_format"
