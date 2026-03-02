"""FFProbe wrapper service for extracting technical metadata from media files"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, Optional, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ResolutionInfo:
    """Resolution information"""

    width: int
    height: int
    label: str


class FFProbeWrapper:
    """Wrapper around FFProbe for extracting media metadata"""

    # Standard resolution labels mapping (exact matches)
    RESOLUTION_LABELS = {
        (7680, 4320): "8K",
        (4096, 2160): "4K DCI",
        (3840, 2160): "4K",
        (2560, 1440): "1440p",
        (1920, 1080): "1080p",
        (1280, 720): "720p",
        (854, 480): "480p",
        (640, 360): "360p",
        (426, 240): "240p",
    }

    # Height thresholds for fallback label matching (descending order)
    RESOLUTION_THRESHOLDS = [
        (2160, "4K"),
        (1440, "1440p"),
        (1080, "1080p"),
        (720, "720p"),
        (480, "480p"),
        (360, "360p"),
    ]

    def __init__(self):
        """Initialize FFProbeWrapper and verify ffprobe is available"""
        self._verify_ffprobe_available()

    @staticmethod
    def _verify_ffprobe_available() -> None:
        """Verify that ffprobe is installed and available on the system"""
        try:
            subprocess.run(["ffprobe", "-version"], capture_output=True, check=True, timeout=5)
            logger.info("FFProbe is available on the system")
        except (
            subprocess.CalledProcessError,
            FileNotFoundError,
            subprocess.TimeoutExpired,
        ) as e:
            error_msg = (
                "FFProbe is not installed or not available on the system. "
                "Please install FFmpeg (which includes ffprobe) to use this service. "
                "On macOS: brew install ffmpeg, On Ubuntu: sudo apt-get install ffmpeg"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def _run_ffprobe(self, file_path: str) -> Dict[str, Any]:
        """
        Internal method to run ffprobe command and return JSON output

        Args:
            file_path: Path to the media file

        Returns:
            Dictionary containing ffprobe output

        Raises:
            FileNotFoundError: If file does not exist
            RuntimeError: If ffprobe command fails
        """
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"Media file not found: {file_path}")

        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_format",
                    "-show_streams",
                    "-of",
                    "json",
                    str(file_path_obj),
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=30,
            )
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            error_msg = f"FFProbe failed to process file: {file_path}. Error: {e.stderr}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse FFProbe output for file: {file_path}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        except subprocess.TimeoutExpired:
            error_msg = f"FFProbe command timed out for file: {file_path}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def is_valid_media_file(self, file_path: str) -> bool:
        """
        Validate if file is a readable media file

        Args:
            file_path: Path to the file to validate

        Returns:
            True if file is valid media, False otherwise
        """
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                logger.warning(f"File does not exist: {file_path}")
                return False

            # Try to run ffprobe
            self._run_ffprobe(file_path)
            return True
        except (FileNotFoundError, RuntimeError) as e:
            logger.warning(f"File validation failed for {file_path}: {e}")
            return False

    def get_resolution(self, file_path: str) -> Dict[str, Any]:
        """
        Extract video resolution information

        Args:
            file_path: Path to the media file

        Returns:
            Dictionary with width, height, and label
        """
        try:
            data = self._run_ffprobe(file_path)
            streams = data.get("streams", [])

            # Find video stream
            video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)

            if not video_stream:
                return {"error": "No video stream found"}

            width = video_stream.get("width")
            height = video_stream.get("height")

            if not width or not height:
                return {"error": "Resolution information not available"}

            # Determine resolution label
            label = self._get_resolution_label(width, height)

            return {"width": width, "height": height, "label": label}
        except (FileNotFoundError, RuntimeError) as e:
            return {"error": str(e)}

    def _get_resolution_label(self, width: int, height: int) -> str:
        """
        Determine standard resolution label from width and height

        Args:
            width: Video width in pixels
            height: Video height in pixels

        Returns:
            Resolution label (e.g., "1080p", "720p")
        """
        if (width, height) in self.RESOLUTION_LABELS:
            return self.RESOLUTION_LABELS[(width, height)]

        for min_height, label in self.RESOLUTION_THRESHOLDS:
            if height >= min_height:
                return label

        return f"{height}p"

    def get_bitrate(self, file_path: str) -> Dict[str, Any]:
        """
        Extract bitrate information

        Args:
            file_path: Path to the media file

        Returns:
            Dictionary with total, video, and audio bitrate
        """
        try:
            data = self._run_ffprobe(file_path)
            streams = data.get("streams", [])
            format_info = data.get("format", {})

            total_bitrate = format_info.get("bit_rate")
            video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
            audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

            return {
                "total": self._format_bitrate(int(total_bitrate)) if total_bitrate else "Unknown",
                "video": self._get_stream_bitrate(video_stream),
                "audio": self._get_stream_bitrate(audio_stream),
            }
        except (FileNotFoundError, RuntimeError) as e:
            return {"error": str(e)}

    def _get_stream_bitrate(self, stream: Optional[Dict[str, Any]]) -> str:
        """Return formatted bitrate for a stream, or 'Unknown' if unavailable."""
        if stream and stream.get("bit_rate"):
            return self._format_bitrate(int(stream["bit_rate"]))
        return "Unknown"

    @staticmethod
    def _format_bitrate(bitrate_bps: int) -> str:
        """
        Format bitrate in human-readable format

        Args:
            bitrate_bps: Bitrate in bits per second

        Returns:
            Formatted bitrate string (e.g., "5.5 Mbps", "256 kbps")
        """
        if bitrate_bps >= 1_000_000:
            return f"{bitrate_bps / 1_000_000:.1f} Mbps"
        elif bitrate_bps >= 1_000:
            return f"{bitrate_bps / 1_000:.0f} kbps"
        else:
            return f"{bitrate_bps} bps"

    def get_codecs(self, file_path: str) -> Dict[str, Any]:
        """
        Extract codec information

        Args:
            file_path: Path to the media file

        Returns:
            Dictionary with video and audio codec information
        """
        try:
            data = self._run_ffprobe(file_path)
            streams = data.get("streams", [])

            result = {}

            # Get video codec
            video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
            if video_stream:
                result["video"] = video_stream.get("codec_name", "Unknown")
                result["profile"] = video_stream.get("profile", "Unknown")
                result["level"] = video_stream.get("level", "Unknown")
            else:
                result["video"] = "Unknown"
                result["profile"] = "Unknown"
                result["level"] = "Unknown"

            # Get audio codec
            audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)
            if audio_stream:
                result["audio"] = audio_stream.get("codec_name", "Unknown")
            else:
                result["audio"] = "Unknown"

            return result
        except (FileNotFoundError, RuntimeError) as e:
            return {"error": str(e)}

    def get_duration(self, file_path: str) -> float:
        """
        Extract media file duration

        Args:
            file_path: Path to the media file

        Returns:
            Duration in seconds, or -1 if error occurs
        """
        try:
            data = self._run_ffprobe(file_path)
            format_info = data.get("format", {})
            duration = format_info.get("duration")

            if duration:
                return float(duration)
            else:
                logger.warning(f"Duration not available for file: {file_path}")
                return -1.0
        except (FileNotFoundError, RuntimeError, ValueError) as e:
            logger.error(f"Failed to extract duration from {file_path}: {e}")
            return -1.0

    @staticmethod
    def _parse_frame_rate(rate_str: Optional[str]) -> Optional[float]:
        """Parse a 'num/den' frame rate string, returning float or None."""
        if not rate_str:
            return None
        parts = rate_str.split("/")
        if len(parts) != 2:
            return None
        try:
            return float(parts[0]) / float(parts[1])
        except (ValueError, ZeroDivisionError):
            return None

    def get_frame_rate(self, file_path: str) -> float:
        """
        Extract video frame rate (fps)

        Args:
            file_path: Path to the media file

        Returns:
            Frame rate in fps, or -1 if error occurs
        """
        try:
            data = self._run_ffprobe(file_path)
            video_stream = next(
                (s for s in data.get("streams", []) if s.get("codec_type") == "video"),
                None,
            )
            if not video_stream:
                logger.warning(f"No video stream found in file: {file_path}")
                return -1.0

            fps = self._parse_frame_rate(
                video_stream.get("r_frame_rate")
            ) or self._parse_frame_rate(video_stream.get("avg_frame_rate"))
            if fps is None:
                logger.warning(f"Frame rate not available for file: {file_path}")
                return -1.0
            return fps
        except (FileNotFoundError, RuntimeError) as e:
            logger.error(f"Failed to extract frame rate from {file_path}: {e}")
            return -1.0

    def get_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract comprehensive metadata from media file

        Args:
            file_path: Path to the media file

        Returns:
            Dictionary containing all metadata
        """
        try:
            data = self._run_ffprobe(file_path)
            streams = data.get("streams", [])

            # Extract all components
            resolution = self.get_resolution(file_path)
            bitrate = self.get_bitrate(file_path)
            codecs = self.get_codecs(file_path)
            duration = self.get_duration(file_path)
            frame_rate = self.get_frame_rate(file_path)

            # Build comprehensive metadata
            metadata = {
                "resolution": resolution,
                "bitrate": bitrate,
                "codecs": codecs,
                "duration": duration,
                "frame_rate": frame_rate,
                "streams": self._extract_stream_info(streams),
            }

            return metadata
        except (FileNotFoundError, RuntimeError) as e:
            return {
                "error": str(e),
                "resolution": {"error": str(e)},
                "bitrate": {"error": str(e)},
                "codecs": {"error": str(e)},
                "duration": -1.0,
                "frame_rate": -1.0,
                "streams": [],
            }

    @staticmethod
    def _extract_stream_info(streams: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract relevant information from streams

        Args:
            streams: List of stream dictionaries from ffprobe

        Returns:
            List of simplified stream information
        """
        stream_info = []
        for stream in streams:
            info = {
                "index": stream.get("index"),
                "codec_type": stream.get("codec_type"),
                "codec_name": stream.get("codec_name"),
            }

            if stream.get("codec_type") == "video":
                info["width"] = stream.get("width")
                info["height"] = stream.get("height")
                info["r_frame_rate"] = stream.get("r_frame_rate")
                info["bit_rate"] = stream.get("bit_rate")

            elif stream.get("codec_type") == "audio":
                info["sample_rate"] = stream.get("sample_rate")
                info["channels"] = stream.get("channels")
                info["bit_rate"] = stream.get("bit_rate")

            stream_info.append(info)

        return stream_info
