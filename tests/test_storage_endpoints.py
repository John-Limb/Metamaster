"""Tests for /storage API endpoints."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app, raise_server_exceptions=False)

SUMMARY_PAYLOAD = {
    "disk": {
        "total_bytes": 4_000_000_000_000,
        "used_bytes": 2_000_000_000_000,
        "available_bytes": 2_000_000_000_000,
    },
    "library": {"movies_bytes": 1_400_000_000_000, "tv_bytes": 600_000_000_000, "other_bytes": 0},
    "potential_savings_bytes": 800_000_000_000,
    "files_analyzed": 100,
    "files_pending_analysis": 5,
}

FILES_PAYLOAD = {
    "total": 1,
    "items": [
        {
            "id": 1,
            "name": "test.mkv",
            "media_type": "movie",
            "size_bytes": 30_000_000_000,
            "duration_seconds": 7200,
            "video_codec": "h264",
            "video_width": 1920,
            "video_height": 1080,
            "mb_per_min": 254.0,
            "resolution_tier": "1080p",
            "efficiency_tier": "large",
            "estimated_savings_bytes": 26_000_000_000,
        }
    ],
}


def test_get_summary_returns_200():
    with patch("app.api.v1.storage.endpoints.StorageService") as MockService:
        MockService.return_value.get_summary.return_value = SUMMARY_PAYLOAD
        response = client.get("/api/v1/storage/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["disk"]["total_bytes"] == 4_000_000_000_000
    assert data["library"]["movies_bytes"] == 1_400_000_000_000
    assert data["files_analyzed"] == 100


def test_get_files_returns_200():
    with patch("app.api.v1.storage.endpoints.StorageService") as MockService:
        MockService.return_value.get_files.return_value = FILES_PAYLOAD
        response = client.get("/api/v1/storage/files")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "test.mkv"


def test_get_files_passes_query_params():
    with patch("app.api.v1.storage.endpoints.StorageService") as MockService:
        MockService.return_value.get_files.return_value = {"total": 0, "items": []}
        client.get(
            "/api/v1/storage/files?page=2&pageSize=25&sortBy=mb_per_min&sortDir=asc&mediaType=movie"
        )
        MockService.return_value.get_files.assert_called_once_with(
            page=2,
            page_size=25,
            sort_by="mb_per_min",
            sort_dir="asc",
            media_type="movie",
            codec=None,
            resolution_tier=None,
            efficiency_tier=None,
            watched_status=None,
        )


def test_get_files_passes_watched_status():
    with patch("app.api.v1.storage.endpoints.StorageService") as MockService:
        MockService.return_value.get_files.return_value = {"total": 0, "items": []}
        client.get("/api/v1/storage/files?watchedStatus=unwatched")
        MockService.return_value.get_files.assert_called_once_with(
            page=1,
            page_size=50,
            sort_by="size_bytes",
            sort_dir="desc",
            media_type=None,
            codec=None,
            resolution_tier=None,
            efficiency_tier=None,
            watched_status="unwatched",
        )


def test_get_summary_includes_unwatched_size_keys():
    summary_with_unwatched = {
        **SUMMARY_PAYLOAD,
        "unwatched_movie_size_bytes": 500_000_000_000,
        "unwatched_tv_size_bytes": 200_000_000_000,
    }
    with patch("app.api.v1.storage.endpoints.StorageService") as MockService:
        MockService.return_value.get_summary.return_value = summary_with_unwatched
        response = client.get("/api/v1/storage/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["unwatched_movie_size_bytes"] == 500_000_000_000
    assert data["unwatched_tv_size_bytes"] == 200_000_000_000


def test_scan_technical_returns_202():
    with patch("app.api.v1.storage.endpoints.enrich_file_technical_metadata") as mock_task:
        response = client.post("/api/v1/storage/scan-technical")
    assert response.status_code == 202
    mock_task.delay.assert_called_once()
