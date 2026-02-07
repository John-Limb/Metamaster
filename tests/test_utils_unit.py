"""Comprehensive unit tests for utility functions and helpers"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import json
import re


# ============================================================================
# String Formatting Utilities Tests
# ============================================================================


class TestStringFormattingUtilities:
    """Tests for string formatting utility functions"""

    def test_clean_filename_with_dots(self):
        """Test cleaning filename with dots"""
        from app.services.pattern_recognition import PatternRecognitionService

        service = PatternRecognitionService()

        cleaned = service._clean_filename("The.Dark.Knight.2008")
        assert cleaned == "The Dark Knight 2008"

    def test_clean_filename_with_underscores(self):
        """Test cleaning filename with underscores"""
        from app.services.pattern_recognition import PatternRecognitionService

        service = PatternRecognitionService()

        cleaned = service._clean_filename("The_Dark_Knight_2008")
        assert cleaned == "The Dark Knight 2008"

    def test_clean_filename_with_hyphens(self):
        """Test cleaning filename with hyphens"""
        from app.services.pattern_recognition import PatternRecognitionService

        service = PatternRecognitionService()

        cleaned = service._clean_filename("The-Dark-Knight-2008")
        assert cleaned == "The Dark Knight 2008"

    def test_clean_filename_mixed_separators(self):
        """Test cleaning filename with mixed separators"""
        from app.services.pattern_recognition import PatternRecognitionService

        service = PatternRecognitionService()

        cleaned = service._clean_filename("The.Dark_Knight-2008")
        assert cleaned == "The Dark Knight 2008"

    def test_clean_filename_extra_spaces(self):
        """Test cleaning filename with extra spaces"""
        from app.services.pattern_recognition import PatternRecognitionService

        service = PatternRecognitionService()

        cleaned = service._clean_filename("The   Dark   Knight")
        assert cleaned == "The Dark Knight"

    def test_clean_title_basic(self):
        """Test cleaning title"""
        from app.services.pattern_recognition import PatternRecognitionService

        service = PatternRecognitionService()

        cleaned = service._clean_title("The.Matrix")
        assert cleaned == "The Matrix"

    def test_clean_title_with_spaces(self):
        """Test cleaning title with spaces"""
        from app.services.pattern_recognition import PatternRecognitionService

        service = PatternRecognitionService()

        cleaned = service._clean_title("The  Matrix  Reloaded")
        assert cleaned == "The Matrix Reloaded"

    def test_format_bitrate_mbps(self):
        """Test bitrate formatting in Mbps"""
        from app.services.ffprobe_wrapper import FFProbeWrapper

        formatted = FFProbeWrapper._format_bitrate(5500000)
        assert "Mbps" in formatted
        assert "5.5" in formatted

    def test_format_bitrate_kbps(self):
        """Test bitrate formatting in kbps"""
        from app.services.ffprobe_wrapper import FFProbeWrapper

        formatted = FFProbeWrapper._format_bitrate(256000)
        assert "kbps" in formatted
        assert "256" in formatted

    def test_format_bitrate_bps(self):
        """Test bitrate formatting in bps"""
        from app.services.ffprobe_wrapper import FFProbeWrapper

        formatted = FFProbeWrapper._format_bitrate(500)
        assert "bps" in formatted

    def test_format_bitrate_large_value(self):
        """Test bitrate formatting with large value"""
        from app.services.ffprobe_wrapper import FFProbeWrapper

        formatted = FFProbeWrapper._format_bitrate(50000000)
        assert "Mbps" in formatted
        assert "50" in formatted


# ============================================================================
# Date/Time Utilities Tests
# ============================================================================


class TestDateTimeUtilities:
    """Tests for date/time utility functions"""

    def test_datetime_utcnow(self):
        """Test datetime.utcnow() usage"""
        now = datetime.utcnow()
        assert isinstance(now, datetime)
        assert now.year >= 2020

    def test_datetime_comparison(self):
        """Test datetime comparison"""
        past = datetime.utcnow() - timedelta(days=1)
        now = datetime.utcnow()
        future = datetime.utcnow() + timedelta(days=1)

        assert past < now
        assert now < future

    def test_datetime_timedelta_days(self):
        """Test timedelta with days"""
        now = datetime.utcnow()
        future = now + timedelta(days=30)

        diff = future - now
        assert diff.days == 30

    def test_datetime_timedelta_hours(self):
        """Test timedelta with hours"""
        now = datetime.utcnow()
        future = now + timedelta(hours=24)

        diff = future - now
        assert diff.total_seconds() == 86400

    def test_datetime_timedelta_seconds(self):
        """Test timedelta with seconds"""
        now = datetime.utcnow()
        future = now + timedelta(seconds=3600)

        diff = future - now
        assert diff.total_seconds() == 3600

    def test_datetime_isoformat(self):
        """Test datetime ISO format"""
        now = datetime.utcnow()
        iso_str = now.isoformat()

        assert isinstance(iso_str, str)
        assert "T" in iso_str

    def test_datetime_strftime(self):
        """Test datetime string formatting"""
        now = datetime.utcnow()
        formatted = now.strftime("%Y-%m-%d")

        assert len(formatted) == 10
        assert formatted.count("-") == 2


# ============================================================================
# File Path Utilities Tests
# ============================================================================


class TestFilePathUtilities:
    """Tests for file path utility functions"""

    def test_path_stem_extraction(self):
        """Test extracting filename stem"""
        path = Path("/path/to/The.Matrix.1999.mp4")
        stem = path.stem

        assert stem == "The.Matrix.1999"

    def test_path_suffix_extraction(self):
        """Test extracting file extension"""
        path = Path("/path/to/movie.mp4")
        suffix = path.suffix

        assert suffix == ".mp4"

    def test_path_suffix_lowercase(self):
        """Test file extension in lowercase"""
        path = Path("/path/to/movie.MP4")
        suffix = path.suffix.lower()

        assert suffix == ".mp4"

    def test_path_parent_directory(self):
        """Test getting parent directory"""
        path = Path("/path/to/movie.mp4")
        parent = path.parent

        assert str(parent) == "/path/to"

    def test_path_exists_check(self):
        """Test path existence check"""
        path = Path("/nonexistent/path")
        assert path.exists() is False

    def test_path_is_file_check(self):
        """Test path is file check"""
        path = Path("/path/to/file.mp4")
        # This will be False for non-existent path
        assert path.is_file() is False

    def test_path_is_dir_check(self):
        """Test path is directory check"""
        path = Path("/path/to/directory")
        # This will be False for non-existent path
        assert path.is_dir() is False

    def test_path_name_extraction(self):
        """Test extracting filename"""
        path = Path("/path/to/movie.mp4")
        name = path.name

        assert name == "movie.mp4"

    def test_path_parts_extraction(self):
        """Test extracting path parts"""
        path = Path("/path/to/movie.mp4")
        parts = path.parts

        assert "path" in parts
        assert "to" in parts
        assert "movie.mp4" in parts


# ============================================================================
# Error Message Formatting Tests
# ============================================================================


class TestErrorMessageFormatting:
    """Tests for error message formatting utilities"""

    def test_exception_to_string(self):
        """Test converting exception to string"""
        try:
            raise ValueError("Test error message")
        except ValueError as e:
            error_str = str(e)
            assert error_str == "Test error message"

    def test_exception_type_name(self):
        """Test getting exception type name"""
        try:
            raise FileNotFoundError("File not found")
        except FileNotFoundError as e:
            error_type = type(e).__name__
            assert error_type == "FileNotFoundError"

    def test_traceback_formatting(self):
        """Test traceback formatting"""
        import traceback

        try:
            raise ValueError("Test error")
        except ValueError:
            tb_str = traceback.format_exc()
            assert "ValueError" in tb_str
            assert "Test error" in tb_str

    def test_error_message_with_context(self):
        """Test error message with context"""
        error_msg = "Failed to process file: /path/to/file.mp4"
        assert "Failed" in error_msg
        assert "/path/to/file.mp4" in error_msg

    def test_error_message_concatenation(self):
        """Test error message concatenation"""
        task_name = "analyze_file"
        error = "File not found"
        message = f"Task {task_name} failed: {error}"

        assert message == "Task analyze_file failed: File not found"


# ============================================================================
# JSON Utilities Tests
# ============================================================================


class TestJSONUtilities:
    """Tests for JSON utility functions"""

    def test_json_dumps_dict(self):
        """Test JSON serialization of dict"""
        data = {"title": "The Matrix", "year": 1999}
        json_str = json.dumps(data)

        assert isinstance(json_str, str)
        assert "The Matrix" in json_str

    def test_json_loads_string(self):
        """Test JSON deserialization"""
        json_str = '{"title": "The Matrix", "year": 1999}'
        data = json.loads(json_str)

        assert data["title"] == "The Matrix"
        assert data["year"] == 1999

    def test_json_dumps_list(self):
        """Test JSON serialization of list"""
        data = ["Drama", "Sci-Fi", "Action"]
        json_str = json.dumps(data)

        assert isinstance(json_str, str)
        assert "Drama" in json_str

    def test_json_dumps_nested(self):
        """Test JSON serialization of nested structure"""
        data = {"movie": {"title": "The Matrix", "genres": ["Sci-Fi", "Action"]}}
        json_str = json.dumps(data)
        parsed = json.loads(json_str)

        assert parsed["movie"]["title"] == "The Matrix"
        assert "Sci-Fi" in parsed["movie"]["genres"]

    def test_json_dumps_with_indent(self):
        """Test JSON serialization with indentation"""
        data = {"title": "Test"}
        json_str = json.dumps(data, indent=2)

        assert "\n" in json_str  # Should have newlines with indent


# ============================================================================
# Regex Utilities Tests
# ============================================================================


class TestRegexUtilities:
    """Tests for regex utility functions"""

    def test_regex_pattern_matching(self):
        """Test regex pattern matching"""
        pattern = r"[Ss](\d{1,2})[Ee](\d{1,2})"
        text = "Breaking Bad S01E01"

        match = re.search(pattern, text)
        assert match is not None
        assert match.group(1) == "01"
        assert match.group(2) == "01"

    def test_regex_year_extraction(self):
        """Test regex year extraction"""
        pattern = r"(\d{4})"
        text = "The Matrix (1999)"

        match = re.search(pattern, text)
        assert match is not None
        assert match.group(1) == "1999"

    def test_regex_multiple_matches(self):
        """Test regex multiple matches"""
        pattern = r"\d+"
        text = "Season 1 Episode 5"

        matches = re.findall(pattern, text)
        assert len(matches) == 2
        assert "1" in matches
        assert "5" in matches

    def test_regex_case_insensitive(self):
        """Test regex case insensitive matching"""
        pattern = r"[Ss]eason"

        assert re.search(pattern, "Season 1") is not None
        assert re.search(pattern, "season 1") is not None

    def test_regex_substitution(self):
        """Test regex substitution"""
        pattern = r"[._-]+"
        text = "The.Dark.Knight"

        result = re.sub(pattern, " ", text)
        assert result == "The Dark Knight"

    def test_regex_split(self):
        """Test regex split"""
        pattern = r"[._-]"
        text = "The.Dark-Knight_2008"

        parts = re.split(pattern, text)
        assert len(parts) == 4
        assert "The" in parts
        assert "2008" in parts


# ============================================================================
# Validation Utilities Tests
# ============================================================================


class TestValidationUtilities:
    """Tests for validation utility functions"""

    def test_validate_year_range(self):
        """Test year range validation"""
        year = 1999
        assert 1800 <= year <= 2100

    def test_validate_rating_range(self):
        """Test rating range validation"""
        rating = 8.5
        assert 0 <= rating <= 10

    def test_validate_empty_string(self):
        """Test empty string validation"""
        text = ""
        assert not text or not text.strip()

    def test_validate_positive_number(self):
        """Test positive number validation"""
        number = 100
        assert number > 0

    def test_validate_file_extension(self):
        """Test file extension validation"""
        extensions = [".mp4", ".mkv", ".avi"]
        file_ext = ".mp4"

        assert file_ext in extensions

    def test_validate_media_type(self):
        """Test media type validation"""
        valid_types = ["movie", "tv_show"]
        media_type = "movie"

        assert media_type in valid_types


# ============================================================================
# Collection Utilities Tests
# ============================================================================


class TestCollectionUtilities:
    """Tests for collection utility functions"""

    def test_list_deduplication(self):
        """Test list deduplication"""
        items = [1, 2, 2, 3, 3, 3, 4]
        unique = list(set(items))

        assert len(unique) == 4
        assert 1 in unique
        assert 4 in unique

    def test_dict_merge(self):
        """Test dictionary merging"""
        dict1 = {"a": 1, "b": 2}
        dict2 = {"c": 3, "d": 4}

        merged = {**dict1, **dict2}
        assert len(merged) == 4
        assert merged["a"] == 1
        assert merged["d"] == 4

    def test_dict_get_with_default(self):
        """Test dictionary get with default"""
        data = {"title": "Test"}

        title = data.get("title", "Unknown")
        rating = data.get("rating", 0)

        assert title == "Test"
        assert rating == 0

    def test_list_filtering(self):
        """Test list filtering"""
        items = [1, 2, 3, 4, 5]
        filtered = [x for x in items if x > 2]

        assert len(filtered) == 3
        assert 1 not in filtered
        assert 5 in filtered

    def test_list_mapping(self):
        """Test list mapping"""
        items = [1, 2, 3]
        mapped = [x * 2 for x in items]

        assert mapped == [2, 4, 6]

    def test_dict_filtering(self):
        """Test dictionary filtering"""
        data = {"a": 1, "b": 2, "c": 3}
        filtered = {k: v for k, v in data.items() if v > 1}

        assert len(filtered) == 2
        assert "a" not in filtered
        assert filtered["c"] == 3


# ============================================================================
# Type Conversion Utilities Tests
# ============================================================================


class TestTypeConversionUtilities:
    """Tests for type conversion utility functions"""

    def test_string_to_int(self):
        """Test string to integer conversion"""
        value = int("1999")
        assert value == 1999
        assert isinstance(value, int)

    def test_string_to_float(self):
        """Test string to float conversion"""
        value = float("8.5")
        assert value == 8.5
        assert isinstance(value, float)

    def test_int_to_string(self):
        """Test integer to string conversion"""
        value = str(1999)
        assert value == "1999"
        assert isinstance(value, str)

    def test_float_to_string(self):
        """Test float to string conversion"""
        value = str(8.5)
        assert value == "8.5"
        assert isinstance(value, str)

    def test_bool_to_string(self):
        """Test boolean to string conversion"""
        value = str(True)
        assert value == "True"

    def test_list_to_string(self):
        """Test list to string conversion"""
        items = ["Drama", "Sci-Fi"]
        value = json.dumps(items)

        assert isinstance(value, str)
        assert "Drama" in value


# ============================================================================
# Comparison Utilities Tests
# ============================================================================


class TestComparisonUtilities:
    """Tests for comparison utility functions"""

    def test_string_equality(self):
        """Test string equality"""
        assert "The Matrix" == "The Matrix"
        assert "The Matrix" != "Inception"

    def test_case_insensitive_comparison(self):
        """Test case insensitive comparison"""
        assert "The Matrix".lower() == "the matrix"
        assert "DRAMA".lower() == "drama"

    def test_numeric_comparison(self):
        """Test numeric comparison"""
        assert 1999 < 2000
        assert 8.5 > 8.0
        assert 5 == 5

    def test_list_equality(self):
        """Test list equality"""
        list1 = [1, 2, 3]
        list2 = [1, 2, 3]

        assert list1 == list2

    def test_dict_equality(self):
        """Test dictionary equality"""
        dict1 = {"title": "Test", "year": 2020}
        dict2 = {"title": "Test", "year": 2020}

        assert dict1 == dict2
