"""Comprehensive unit tests for FFProbeWrapper service"""

import pytest
import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from app.infrastructure.file_system.ffprobe_wrapper import FFProbeWrapper


class TestFFProbeWrapperInitialization:
    """Test FFProbeWrapper initialization and ffprobe availability check"""

    def test_initialization_with_ffprobe_available(self):
        """Test successful initialization when ffprobe is available"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            wrapper = FFProbeWrapper()
            assert wrapper is not None
            mock_run.assert_called_once()

    def test_initialization_fails_when_ffprobe_not_available(self):
        """Test initialization fails when ffprobe is not installed"""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("ffprobe not found")
            with pytest.raises(RuntimeError, match="FFProbe is not installed"):
                FFProbeWrapper()

    def test_initialization_fails_on_timeout(self):
        """Test initialization fails when ffprobe check times out"""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("ffprobe", 5)
            with pytest.raises(RuntimeError, match="FFProbe is not installed"):
                FFProbeWrapper()


class TestRunFFProbe:
    """Test internal _run_ffprobe method"""

    @pytest.fixture
    def wrapper(self):
        """Create FFProbeWrapper instance with mocked ffprobe check"""
        with patch("subprocess.run"):
            return FFProbeWrapper()

    def test_run_ffprobe_success(self, wrapper):
        """Test successful ffprobe execution"""
        test_file = Path("test.mp4")
        test_file.touch()

        try:
            mock_output = {
                "streams": [{"codec_type": "video", "width": 1920, "height": 1080}],
                "format": {"duration": "120.5"},
            }

            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(stdout=json.dumps(mock_output))
                result = wrapper._run_ffprobe(str(test_file))
                assert result == mock_output
        finally:
            test_file.unlink()

    def test_run_ffprobe_file_not_found(self, wrapper):
        """Test ffprobe with non-existent file"""
        with pytest.raises(FileNotFoundError, match="Media file not found"):
            wrapper._run_ffprobe("/nonexistent/file.mp4")

    def test_run_ffprobe_command_fails(self, wrapper):
        """Test ffprobe command failure"""
        test_file = Path("test.mp4")
        test_file.touch()

        try:
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = subprocess.CalledProcessError(
                    1, "ffprobe", stderr="Corrupted file"
                )
                with pytest.raises(RuntimeError, match="FFProbe failed to process file"):
                    wrapper._run_ffprobe(str(test_file))
        finally:
            test_file.unlink()

    def test_run_ffprobe_invalid_json(self, wrapper):
        """Test ffprobe with invalid JSON output"""
        test_file = Path("test.mp4")
        test_file.touch()

        try:
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(stdout="invalid json")
                with pytest.raises(RuntimeError, match="Failed to parse FFProbe output"):
                    wrapper._run_ffprobe(str(test_file))
        finally:
            test_file.unlink()

    def test_run_ffprobe_timeout(self, wrapper):
        """Test ffprobe command timeout"""
        test_file = Path("test.mp4")
        test_file.touch()

        try:
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = subprocess.TimeoutExpired("ffprobe", 30)
                with pytest.raises(RuntimeError, match="FFProbe command timed out"):
                    wrapper._run_ffprobe(str(test_file))
        finally:
            test_file.unlink()


class TestIsValidMediaFile:
    """Test media file validation"""

    @pytest.fixture
    def wrapper(self):
        """Create FFProbeWrapper instance with mocked ffprobe check"""
        with patch("subprocess.run"):
            return FFProbeWrapper()

    def test_is_valid_media_file_success(self, wrapper):
        """Test validation of valid media file"""
        test_file = Path("test.mp4")
        test_file.touch()

        try:
            with patch.object(wrapper, "_run_ffprobe") as mock_run:
                mock_run.return_value = {"streams": []}
                assert wrapper.is_valid_media_file(str(test_file)) is True
        finally:
            test_file.unlink()

    def test_is_valid_media_file_not_found(self, wrapper):
        """Test validation of non-existent file"""
        assert wrapper.is_valid_media_file("/nonexistent/file.mp4") is False

    def test_is_valid_media_file_corrupted(self, wrapper):
        """Test validation of corrupted file"""
        test_file = Path("test.mp4")
        test_file.touch()

        try:
            with patch.object(wrapper, "_run_ffprobe") as mock_run:
                mock_run.side_effect = RuntimeError("Corrupted file")
                assert wrapper.is_valid_media_file(str(test_file)) is False
        finally:
            test_file.unlink()


class TestResolutionExtraction:
    """Test resolution extraction functionality"""

    @pytest.fixture
    def wrapper(self):
        """Create FFProbeWrapper instance with mocked ffprobe check"""
        with patch("subprocess.run"):
            return FFProbeWrapper()

    def test_get_resolution_1080p(self, wrapper):
        """Test resolution extraction for 1080p video"""
        mock_output = {
            "streams": [{"codec_type": "video", "width": 1920, "height": 1080}],
            "format": {},
        }

        with patch.object(wrapper, "_run_ffprobe") as mock_run:
            mock_run.return_value = mock_output
            result = wrapper.get_resolution("test.mp4")
            assert result["width"] == 1920
            assert result["height"] == 1080
            assert result["label"] == "1080p"

    def test_get_resolution_720p(self, wrapper):
        """Test resolution extraction for 720p video"""
        mock_output = {
            "streams": [{"codec_type": "video", "width": 1280, "height": 720}],
            "format": {},
        }

        with patch.object(wrapper, "_run_ffprobe") as mock_run:
            mock_run.return_value = mock_output
            result = wrapper.get_resolution("test.mp4")
            assert result["label"] == "720p"

    def test_get_resolution_4k(self, wrapper):
        """Test resolution extraction for 4K video"""
        mock_output = {
            "streams": [{"codec_type": "video", "width": 3840, "height": 2160}],
            "format": {},
        }

        with patch.object(wrapper, "_run_ffprobe") as mock_run:
            mock_run.return_value = mock_output
            result = wrapper.get_resolution("test.mp4")
            assert result["label"] == "4K"

    def test_get_resolution_480p(self, wrapper):
        """Test resolution extraction for 480p video"""
        mock_output = {
            "streams": [{"codec_type": "video", "width": 854, "height": 480}],
            "format": {},
        }

        with patch.object(wrapper, "_run_ffprobe") as mock_run:
            mock_run.return_value = mock_output
            result = wrapper.get_resolution("test.mp4")
            assert result["label"] == "480p"

    def test_get_resolution_no_video_stream(self, wrapper):
        """Test resolution extraction when no video stream exists"""
        mock_output = {"streams": [{"codec_type": "audio"}], "format": {}}

        with patch.object(wrapper, "_run_ffprobe") as mock_run:
            mock_run.return_value = mock_output
            result = wrapper.get_resolution("test.mp4")
            assert "error" in result

    def test_get_resolution_missing_dimensions(self, wrapper):
        """Test resolution extraction when dimensions are missing"""
        mock_output = {"streams": [{"codec_type": "video"}], "format": {}}

        with patch.object(wrapper, "_run_ffprobe") as mock_run:
            mock_run.return_value = mock_output
            result = wrapper.get_resolution("test.mp4")
            assert "error" in result

    def test_get_resolution_custom_resolution(self, wrapper):
        """Test resolution extraction for non-standard resolution"""
        mock_output = {
            "streams": [{"codec_type": "video", "width": 1600, "height": 900}],
            "format": {},
        }

        with patch.object(wrapper, "_run_ffprobe") as mock_run:
            mock_run.return_value = mock_output
            result = wrapper.get_resolution("test.mp4")
            assert result["width"] == 1600
            assert result["height"] == 900
            assert result["label"] == "720p"  # Falls back to height-based matching

    def test_get_resolution_error_handling(self, wrapper):
        """Test resolution extraction error handling"""
        with patch.object(wrapper, "_run_ffprobe") as mock_run:
            mock_run.side_effect = RuntimeError("File error")
            result = wrapper.get_resolution("test.mp4")
            assert "error" in result


class TestBitrateExtraction:
    """Test bitrate extraction functionality"""

    @pytest.fixture
    def wrapper(self):
        """Create FFProbeWrapper instance with mocked ffprobe check"""
        with patch("subprocess.run"):
            return FFProbeWrapper()

    def test_get_bitrate_all_available(self, wrapper):
        """Test bitrate extraction when all bitrates are available"""
        mock_output = {
            "streams": [
                {"codec_type": "video", "bit_rate": "5000000"},
                {"codec_type": "audio", "bit_rate": "128000"},
            ],
            "format": {"bit_rate": "5128000"},
        }

        with patch.object(wrapper, "_run_ffprobe") as mock_run:
            mock_run.return_value = mock_output
            result = wrapper.get_bitrate("test.mp4")
            assert "5.1 Mbps" in result["total"]
            assert "5.0 Mbps" in result["video"]
            assert "128 kbps" in result["audio"]

    def test_get_bitrate_partial_available(self, wrapper):
        """Test bitrate extraction when only some bitrates are available"""
        mock_output = {
            "streams": [{"codec_type": "video", "bit_rate": "5000000"}],
            "format": {},
        }

        with patch.object(wrapper, "_run_ffprobe") as mock_run:
            mock_run.return_value = mock_output
            result = wrapper.get_bitrate("test.mp4")
            assert result["total"] == "Unknown"
            assert "5.0 Mbps" in result["video"]
            assert result["audio"] == "Unknown"

    def test_get_bitrate_none_available(self, wrapper):
        """Test bitrate extraction when no bitrates are available"""
        mock_output = {"streams": [{"codec_type": "video"}], "format": {}}

        with patch.object(wrapper, "_run_ffprobe") as mock_run:
            mock_run.return_value = mock_output
            result = wrapper.get_bitrate("test.mp4")
            assert result["total"] == "Unknown"
            assert result["video"] == "Unknown"
            assert result["audio"] == "Unknown"

    def test_format_bitrate_mbps(self, wrapper):
        """Test bitrate formatting for Mbps"""
        result = wrapper._format_bitrate(5_500_000)
        assert result == "5.5 Mbps"

    def test_format_bitrate_kbps(self, wrapper):
        """Test bitrate formatting for kbps"""
        result = wrapper._format_bitrate(256_000)
        assert result == "256 kbps"

    def test_format_bitrate_bps(self, wrapper):
        """Test bitrate formatting for bps"""
        result = wrapper._format_bitrate(500)
        assert result == "500 bps"

    def test_get_bitrate_error_handling(self, wrapper):
        """Test bitrate extraction error handling"""
        with patch.object(wrapper, "_run_ffprobe") as mock_run:
            mock_run.side_effect = RuntimeError("File error")
            result = wrapper.get_bitrate("test.mp4")
            assert "error" in result


class TestCodecDetection:
    """Test codec detection functionality"""

    @pytest.fixture
    def wrapper(self):
        """Create FFProbeWrapper instance with mocked ffprobe check"""
        with patch("subprocess.run"):
            return FFProbeWrapper()

    def test_get_codecs_h264_aac(self, wrapper):
        """Test codec detection for H.264 video and AAC audio"""
        mock_output = {
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "h264",
                    "profile": "High",
                    "level": 40,
                },
                {"codec_type": "audio", "codec_name": "aac"},
            ],
            "format": {},
        }

        with patch.object(wrapper, "_run_ffprobe") as mock_run:
            mock_run.return_value = mock_output
            result = wrapper.get_codecs("test.mp4")
            assert result["video"] == "h264"
            assert result["audio"] == "aac"
            assert result["profile"] == "High"
            assert result["level"] == 40

    def test_get_codecs_h265_opus(self, wrapper):
        """Test codec detection for H.265 video and Opus audio"""
        mock_output = {
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "hevc",
                    "profile": "Main",
                    "level": 120,
                },
                {"codec_type": "audio", "codec_name": "opus"},
            ],
            "format": {},
        }

        with patch.object(wrapper, "_run_ffprobe") as mock_run:
            mock_run.return_value = mock_output
            result = wrapper.get_codecs("test.mp4")
            assert result["video"] == "hevc"
            assert result["audio"] == "opus"

    def test_get_codecs_vp9_flac(self, wrapper):
        """Test codec detection for VP9 video and FLAC audio"""
        mock_output = {
            "streams": [
                {"codec_type": "video", "codec_name": "vp9"},
                {"codec_type": "audio", "codec_name": "flac"},
            ],
            "format": {},
        }

        with patch.object(wrapper, "_run_ffprobe") as mock_run:
            mock_run.return_value = mock_output
            result = wrapper.get_codecs("test.mp4")
            assert result["video"] == "vp9"
            assert result["audio"] == "flac"

    def test_get_codecs_no_video_stream(self, wrapper):
        """Test codec detection when no video stream exists"""
        mock_output = {
            "streams": [{"codec_type": "audio", "codec_name": "aac"}],
            "format": {},
        }

        with patch.object(wrapper, "_run_ffprobe") as mock_run:
            mock_run.return_value = mock_output
            result = wrapper.get_codecs("test.mp4")
            assert result["video"] == "Unknown"
            assert result["audio"] == "aac"

    def test_get_codecs_no_audio_stream(self, wrapper):
        """Test codec detection when no audio stream exists"""
        mock_output = {
            "streams": [{"codec_type": "video", "codec_name": "h264"}],
            "format": {},
        }

        with patch.object(wrapper, "_run_ffprobe") as mock_run:
            mock_run.return_value = mock_output
            result = wrapper.get_codecs("test.mp4")
            assert result["video"] == "h264"
            assert result["audio"] == "Unknown"

    def test_get_codecs_error_handling(self, wrapper):
        """Test codec detection error handling"""
        with patch.object(wrapper, "_run_ffprobe") as mock_run:
            mock_run.side_effect = RuntimeError("File error")
            result = wrapper.get_codecs("test.mp4")
            assert "error" in result


class TestDurationExtraction:
    """Test duration extraction functionality"""

    @pytest.fixture
    def wrapper(self):
        """Create FFProbeWrapper instance with mocked ffprobe check"""
        with patch("subprocess.run"):
            return FFProbeWrapper()

    def test_get_duration_success(self, wrapper):
        """Test successful duration extraction"""
        mock_output = {"streams": [], "format": {"duration": "120.5"}}

        with patch.object(wrapper, "_run_ffprobe") as mock_run:
            mock_run.return_value = mock_output
            result = wrapper.get_duration("test.mp4")
            assert result == 120.5

    def test_get_duration_integer(self, wrapper):
        """Test duration extraction with integer value"""
        mock_output = {"streams": [], "format": {"duration": "3600"}}

        with patch.object(wrapper, "_run_ffprobe") as mock_run:
            mock_run.return_value = mock_output
            result = wrapper.get_duration("test.mp4")
            assert result == 3600.0

    def test_get_duration_missing(self, wrapper):
        """Test duration extraction when duration is missing"""
        mock_output = {"streams": [], "format": {}}

        with patch.object(wrapper, "_run_ffprobe") as mock_run:
            mock_run.return_value = mock_output
            result = wrapper.get_duration("test.mp4")
            assert result == -1.0

    def test_get_duration_error_handling(self, wrapper):
        """Test duration extraction error handling"""
        with patch.object(wrapper, "_run_ffprobe") as mock_run:
            mock_run.side_effect = RuntimeError("File error")
            result = wrapper.get_duration("test.mp4")
            assert result == -1.0


class TestFrameRateExtraction:
    """Test frame rate extraction functionality"""

    @pytest.fixture
    def wrapper(self):
        """Create FFProbeWrapper instance with mocked ffprobe check"""
        with patch("subprocess.run"):
            return FFProbeWrapper()

    def test_get_frame_rate_from_r_frame_rate(self, wrapper):
        """Test frame rate extraction from r_frame_rate"""
        mock_output = {
            "streams": [{"codec_type": "video", "r_frame_rate": "30/1"}],
            "format": {},
        }

        with patch.object(wrapper, "_run_ffprobe") as mock_run:
            mock_run.return_value = mock_output
            result = wrapper.get_frame_rate("test.mp4")
            assert result == 30.0

    def test_get_frame_rate_from_avg_frame_rate(self, wrapper):
        """Test frame rate extraction from avg_frame_rate"""
        mock_output = {
            "streams": [{"codec_type": "video", "avg_frame_rate": "24000/1001"}],
            "format": {},
        }

        with patch.object(wrapper, "_run_ffprobe") as mock_run:
            mock_run.return_value = mock_output
            result = wrapper.get_frame_rate("test.mp4")
            assert abs(result - 23.976) < 0.01

    def test_get_frame_rate_60fps(self, wrapper):
        """Test frame rate extraction for 60fps"""
        mock_output = {
            "streams": [{"codec_type": "video", "r_frame_rate": "60/1"}],
            "format": {},
        }

        with patch.object(wrapper, "_run_ffprobe") as mock_run:
            mock_run.return_value = mock_output
            result = wrapper.get_frame_rate("test.mp4")
            assert result == 60.0

    def test_get_frame_rate_no_video_stream(self, wrapper):
        """Test frame rate extraction when no video stream exists"""
        mock_output = {"streams": [{"codec_type": "audio"}], "format": {}}

        with patch.object(wrapper, "_run_ffprobe") as mock_run:
            mock_run.return_value = mock_output
            result = wrapper.get_frame_rate("test.mp4")
            assert result == -1.0

    def test_get_frame_rate_missing(self, wrapper):
        """Test frame rate extraction when frame rate is missing"""
        mock_output = {"streams": [{"codec_type": "video"}], "format": {}}

        with patch.object(wrapper, "_run_ffprobe") as mock_run:
            mock_run.return_value = mock_output
            result = wrapper.get_frame_rate("test.mp4")
            assert result == -1.0

    def test_get_frame_rate_error_handling(self, wrapper):
        """Test frame rate extraction error handling"""
        with patch.object(wrapper, "_run_ffprobe") as mock_run:
            mock_run.side_effect = RuntimeError("File error")
            result = wrapper.get_frame_rate("test.mp4")
            assert result == -1.0


class TestComprehensiveMetadata:
    """Test comprehensive metadata extraction"""

    @pytest.fixture
    def wrapper(self):
        """Create FFProbeWrapper instance with mocked ffprobe check"""
        with patch("subprocess.run"):
            return FFProbeWrapper()

    def test_get_metadata_complete(self, wrapper):
        """Test comprehensive metadata extraction"""
        mock_output = {
            "streams": [
                {
                    "index": 0,
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": 1920,
                    "height": 1080,
                    "r_frame_rate": "30/1",
                    "bit_rate": "5000000",
                    "profile": "High",
                    "level": 40,
                },
                {
                    "index": 1,
                    "codec_type": "audio",
                    "codec_name": "aac",
                    "sample_rate": "48000",
                    "channels": 2,
                    "bit_rate": "128000",
                },
            ],
            "format": {"duration": "120.5", "bit_rate": "5128000"},
        }

        with patch.object(wrapper, "_run_ffprobe") as mock_run:
            mock_run.return_value = mock_output
            result = wrapper.get_metadata("test.mp4")

            assert "resolution" in result
            assert "bitrate" in result
            assert "codecs" in result
            assert "duration" in result
            assert "frame_rate" in result
            assert "streams" in result
            assert result["duration"] == 120.5
            assert result["frame_rate"] == 30.0

    def test_get_metadata_error_handling(self, wrapper):
        """Test comprehensive metadata extraction error handling"""
        with patch.object(wrapper, "_run_ffprobe") as mock_run:
            mock_run.side_effect = RuntimeError("File error")
            result = wrapper.get_metadata("test.mp4")

            assert "error" in result
            assert result["duration"] == -1.0
            assert result["frame_rate"] == -1.0


class TestResolutionLabelDetection:
    """Test resolution label detection logic"""

    @pytest.fixture
    def wrapper(self):
        """Create FFProbeWrapper instance with mocked ffprobe check"""
        with patch("subprocess.run"):
            return FFProbeWrapper()

    def test_resolution_label_8k(self, wrapper):
        """Test 8K resolution label detection"""
        label = wrapper._get_resolution_label(7680, 4320)
        assert label == "8K"

    def test_resolution_label_4k_dci(self, wrapper):
        """Test 4K DCI resolution label detection"""
        label = wrapper._get_resolution_label(4096, 2160)
        assert label == "4K DCI"

    def test_resolution_label_4k(self, wrapper):
        """Test 4K resolution label detection"""
        label = wrapper._get_resolution_label(3840, 2160)
        assert label == "4K"

    def test_resolution_label_1440p(self, wrapper):
        """Test 1440p resolution label detection"""
        label = wrapper._get_resolution_label(2560, 1440)
        assert label == "1440p"

    def test_resolution_label_1080p(self, wrapper):
        """Test 1080p resolution label detection"""
        label = wrapper._get_resolution_label(1920, 1080)
        assert label == "1080p"

    def test_resolution_label_720p(self, wrapper):
        """Test 720p resolution label detection"""
        label = wrapper._get_resolution_label(1280, 720)
        assert label == "720p"

    def test_resolution_label_480p(self, wrapper):
        """Test 480p resolution label detection"""
        label = wrapper._get_resolution_label(854, 480)
        assert label == "480p"

    def test_resolution_label_360p(self, wrapper):
        """Test 360p resolution label detection"""
        label = wrapper._get_resolution_label(640, 360)
        assert label == "360p"

    def test_resolution_label_240p(self, wrapper):
        """Test 240p resolution label detection"""
        label = wrapper._get_resolution_label(426, 240)
        assert label == "240p"

    def test_resolution_label_non_standard_16_9(self, wrapper):
        """Test non-standard 16:9 resolution label detection"""
        label = wrapper._get_resolution_label(1600, 900)
        assert label == "720p"

    def test_resolution_label_non_standard_4_3(self, wrapper):
        """Test non-standard 4:3 resolution label detection"""
        label = wrapper._get_resolution_label(1024, 768)
        assert label == "720p"
