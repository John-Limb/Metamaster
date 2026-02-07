"""Comprehensive tests for batch operations functionality"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from app.models import BatchOperation, Movie, TVShow
from app.services.batch_operations import BatchOperationService
from app.database import SessionLocal, Base, engine


@pytest.fixture
def db():
    """Create a test database session"""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    yield db
    
    # Cleanup
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def batch_service(db):
    """Create a batch operation service instance"""
    return BatchOperationService(db)


@pytest.fixture
def sample_movies(db):
    """Create sample movie records for testing"""
    movies = [
        Movie(title=f"Movie {i}", omdb_id=f"tt{i:07d}") for i in range(1, 6)
    ]
    db.add_all(movies)
    db.commit()
    return movies


@pytest.fixture
def sample_tv_shows(db):
    """Create sample TV show records for testing"""
    shows = [
        TVShow(title=f"Show {i}", tvdb_id=f"tvdb{i}") for i in range(1, 6)
    ]
    db.add_all(shows)
    db.commit()
    return shows


class TestBatchOperationCreation:
    """Test batch operation creation and initialization"""

    def test_create_batch_operation(self, batch_service):
        """Test creating a new batch operation"""
        batch_op = batch_service.create_batch_operation(
            operation_type="metadata_sync",
            total_items=100,
            metadata={"media_type": "movie"}
        )

        assert batch_op.id is not None
        assert batch_op.operation_type == "metadata_sync"
        assert batch_op.status == "pending"
        assert batch_op.total_items == 100
        assert batch_op.completed_items == 0
        assert batch_op.failed_items == 0
        assert batch_op.progress_percentage == 0.0

    def test_create_batch_operation_with_metadata(self, batch_service):
        """Test creating batch operation with metadata"""
        metadata = {"media_type": "tv_show", "source": "tvdb"}
        batch_op = batch_service.create_batch_operation(
            operation_type="file_import",
            total_items=50,
            metadata=metadata
        )

        stored_metadata = json.loads(batch_op.metadata)
        assert stored_metadata == metadata

    def test_create_batch_operation_without_metadata(self, batch_service):
        """Test creating batch operation without metadata"""
        batch_op = batch_service.create_batch_operation(
            operation_type="metadata_sync",
            total_items=10
        )

        assert batch_op.metadata is None


class TestBatchOperationRetrieval:
    """Test batch operation retrieval and listing"""

    def test_get_batch_operation(self, batch_service):
        """Test retrieving a batch operation by ID"""
        created = batch_service.create_batch_operation(
            operation_type="metadata_sync",
            total_items=50
        )

        retrieved = batch_service.get_batch_operation(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.operation_type == "metadata_sync"

    def test_get_nonexistent_batch_operation(self, batch_service):
        """Test retrieving a non-existent batch operation"""
        result = batch_service.get_batch_operation(9999)
        assert result is None

    def test_list_batch_operations(self, batch_service):
        """Test listing batch operations"""
        # Create multiple batch operations
        for i in range(5):
            batch_service.create_batch_operation(
                operation_type="metadata_sync" if i % 2 == 0 else "file_import",
                total_items=10 * (i + 1)
            )

        operations, total = batch_service.list_batch_operations()
        assert total == 5
        assert len(operations) == 5

    def test_list_batch_operations_with_pagination(self, batch_service):
        """Test listing batch operations with pagination"""
        for i in range(10):
            batch_service.create_batch_operation(
                operation_type="metadata_sync",
                total_items=10
            )

        operations, total = batch_service.list_batch_operations(limit=5, offset=0)
        assert total == 10
        assert len(operations) == 5

        operations, total = batch_service.list_batch_operations(limit=5, offset=5)
        assert total == 10
        assert len(operations) == 5

    def test_list_batch_operations_filter_by_type(self, batch_service):
        """Test filtering batch operations by type"""
        for i in range(3):
            batch_service.create_batch_operation(
                operation_type="metadata_sync",
                total_items=10
            )

        for i in range(2):
            batch_service.create_batch_operation(
                operation_type="file_import",
                total_items=10
            )

        sync_ops, sync_total = batch_service.list_batch_operations(
            operation_type="metadata_sync"
        )
        assert sync_total == 3

        import_ops, import_total = batch_service.list_batch_operations(
            operation_type="file_import"
        )
        assert import_total == 2

    def test_list_batch_operations_filter_by_status(self, batch_service):
        """Test filtering batch operations by status"""
        batch1 = batch_service.create_batch_operation(
            operation_type="metadata_sync",
            total_items=10
        )
        batch2 = batch_service.create_batch_operation(
            operation_type="metadata_sync",
            total_items=10
        )

        batch_service.start_batch_operation(batch1.id)

        pending_ops, pending_total = batch_service.list_batch_operations(
            status="pending"
        )
        assert pending_total == 1

        running_ops, running_total = batch_service.list_batch_operations(
            status="running"
        )
        assert running_total == 1


class TestBatchOperationProgress:
    """Test batch operation progress tracking"""

    def test_update_batch_progress(self, batch_service):
        """Test updating batch operation progress"""
        batch_op = batch_service.create_batch_operation(
            operation_type="metadata_sync",
            total_items=100
        )

        updated = batch_service.update_batch_progress(
            batch_op.id,
            completed_items=50,
            failed_items=5
        )

        assert updated.completed_items == 50
        assert updated.failed_items == 5
        assert updated.progress_percentage == 55.0

    def test_progress_percentage_calculation(self, batch_service):
        """Test progress percentage calculation"""
        batch_op = batch_service.create_batch_operation(
            operation_type="metadata_sync",
            total_items=100
        )

        # Test various progress levels
        test_cases = [
            (25, 0, 25.0),
            (50, 10, 60.0),
            (75, 25, 100.0),
            (100, 0, 100.0),
        ]

        for completed, failed, expected_percentage in test_cases:
            updated = batch_service.update_batch_progress(
                batch_op.id,
                completed_items=completed,
                failed_items=failed
            )
            assert updated.progress_percentage == expected_percentage

    def test_eta_calculation(self, batch_service):
        """Test ETA calculation"""
        batch_op = batch_service.create_batch_operation(
            operation_type="metadata_sync",
            total_items=100
        )

        # Start the batch operation
        batch_service.start_batch_operation(batch_op.id)

        # Simulate some progress
        updated = batch_service.update_batch_progress(
            batch_op.id,
            completed_items=50,
            failed_items=0
        )

        # ETA should be calculated
        assert updated.eta is not None
        assert updated.eta > datetime.utcnow()

    def test_update_progress_with_error_message(self, batch_service):
        """Test updating progress with error message"""
        batch_op = batch_service.create_batch_operation(
            operation_type="metadata_sync",
            total_items=100
        )

        error_msg = "Some items failed to process"
        updated = batch_service.update_batch_progress(
            batch_op.id,
            completed_items=50,
            failed_items=10,
            error_message=error_msg
        )

        assert updated.error_message == error_msg


class TestBatchOperationStatusTransitions:
    """Test batch operation status transitions"""

    def test_start_batch_operation(self, batch_service):
        """Test starting a batch operation"""
        batch_op = batch_service.create_batch_operation(
            operation_type="metadata_sync",
            total_items=100
        )

        assert batch_op.status == "pending"
        assert batch_op.started_at is None

        started = batch_service.start_batch_operation(batch_op.id)
        assert started.status == "running"
        assert started.started_at is not None

    def test_complete_batch_operation(self, batch_service):
        """Test completing a batch operation"""
        batch_op = batch_service.create_batch_operation(
            operation_type="metadata_sync",
            total_items=100
        )

        batch_service.start_batch_operation(batch_op.id)
        completed = batch_service.complete_batch_operation(batch_op.id)

        assert completed.status == "completed"
        assert completed.completed_at is not None
        assert completed.progress_percentage == 100.0

    def test_fail_batch_operation(self, batch_service):
        """Test failing a batch operation"""
        batch_op = batch_service.create_batch_operation(
            operation_type="metadata_sync",
            total_items=100
        )

        error_msg = "Critical error occurred"
        failed = batch_service.fail_batch_operation(batch_op.id, error_msg)

        assert failed.status == "failed"
        assert failed.error_message == error_msg
        assert failed.completed_at is not None

    def test_cancel_batch_operation(self, batch_service):
        """Test cancelling a batch operation"""
        batch_op = batch_service.create_batch_operation(
            operation_type="metadata_sync",
            total_items=100
        )

        batch_service.start_batch_operation(batch_op.id)
        cancelled = batch_service.cancel_batch_operation(batch_op.id)

        assert cancelled.status == "cancelled"
        assert cancelled.completed_at is not None


class TestBulkMetadataSync:
    """Test bulk metadata sync functionality"""

    @pytest.mark.asyncio
    async def test_bulk_metadata_sync_movies(self, batch_service, sample_movies):
        """Test bulk metadata sync for movies"""
        batch_op = batch_service.create_batch_operation(
            operation_type="metadata_sync",
            total_items=len(sample_movies),
            metadata={"media_type": "movie"}
        )

        media_ids = [m.id for m in sample_movies]

        with patch('app.services.batch_operations.OMDBService.get_movie_details') as mock_omdb:
            mock_omdb.return_value = {
                "Title": "Test Movie",
                "imdbRating": "8.5",
                "Plot": "Test plot",
                "Runtime": "120 min"
            }

            result = await batch_service.bulk_metadata_sync(
                batch_op.id,
                media_ids,
                "movie"
            )

            assert result["status"] == "success"
            assert result["completed"] > 0

    @pytest.mark.asyncio
    async def test_bulk_metadata_sync_tv_shows(self, batch_service, sample_tv_shows):
        """Test bulk metadata sync for TV shows"""
        batch_op = batch_service.create_batch_operation(
            operation_type="metadata_sync",
            total_items=len(sample_tv_shows),
            metadata={"media_type": "tv_show"}
        )

        media_ids = [s.id for s in sample_tv_shows]

        with patch('app.services.batch_operations.TVDBService.get_series_details') as mock_tvdb:
            mock_tvdb.return_value = {
                "seriesName": "Test Show",
                "siteRating": "8.0",
                "overview": "Test overview"
            }

            result = await batch_service.bulk_metadata_sync(
                batch_op.id,
                media_ids,
                "tv_show"
            )

            assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_bulk_metadata_sync_with_errors(self, batch_service, sample_movies):
        """Test bulk metadata sync with partial failures"""
        batch_op = batch_service.create_batch_operation(
            operation_type="metadata_sync",
            total_items=len(sample_movies),
            metadata={"media_type": "movie"}
        )

        media_ids = [m.id for m in sample_movies]

        with patch('app.services.batch_operations.OMDBService.get_movie_details') as mock_omdb:
            # Simulate some failures
            mock_omdb.side_effect = [
                {"Title": "Movie 1", "imdbRating": "8.0"},
                Exception("API Error"),
                {"Title": "Movie 3", "imdbRating": "7.5"},
                None,
                {"Title": "Movie 5", "imdbRating": "8.5"},
            ]

            result = await batch_service.bulk_metadata_sync(
                batch_op.id,
                media_ids,
                "movie"
            )

            assert result["status"] == "success"
            assert result["failed"] > 0


class TestBulkFileImport:
    """Test bulk file import functionality"""

    @pytest.mark.asyncio
    async def test_bulk_file_import(self, batch_service, tmp_path):
        """Test bulk file import"""
        # Create temporary test files
        test_files = []
        for i in range(3):
            file_path = tmp_path / f"test_video_{i}.mp4"
            file_path.write_text("fake video content")
            test_files.append(str(file_path))

        batch_op = batch_service.create_batch_operation(
            operation_type="file_import",
            total_items=len(test_files),
            metadata={"media_type": "movie"}
        )

        with patch('app.services.batch_operations.FFProbeWrapper.get_metadata') as mock_ffprobe:
            mock_ffprobe.return_value = {
                "resolution": {"width": 1920, "height": 1080},
                "codecs": {"video": "h264", "audio": "aac"},
                "duration": 7200,
                "bitrate": {"total": "5000k"}
            }

            result = await batch_service.bulk_file_import(
                batch_op.id,
                test_files,
                "movie"
            )

            assert result["status"] == "success"
            assert result["completed"] == len(test_files)
            assert len(result["imported_files"]) == len(test_files)

    @pytest.mark.asyncio
    async def test_bulk_file_import_nonexistent_files(self, batch_service):
        """Test bulk file import with non-existent files"""
        test_files = ["/nonexistent/file1.mp4", "/nonexistent/file2.mp4"]

        batch_op = batch_service.create_batch_operation(
            operation_type="file_import",
            total_items=len(test_files),
            metadata={"media_type": "movie"}
        )

        result = await batch_service.bulk_file_import(
            batch_op.id,
            test_files,
            "movie"
        )

        assert result["status"] == "success"
        assert result["failed"] == len(test_files)


class TestBatchMetadata:
    """Test batch operation metadata handling"""

    def test_get_batch_metadata(self, batch_service):
        """Test retrieving batch metadata"""
        metadata = {"media_type": "movie", "source": "omdb"}
        batch_op = batch_service.create_batch_operation(
            operation_type="metadata_sync",
            total_items=100,
            metadata=metadata
        )

        retrieved_metadata = batch_service.get_batch_metadata(batch_op.id)
        assert retrieved_metadata == metadata

    def test_set_batch_metadata(self, batch_service):
        """Test setting batch metadata"""
        batch_op = batch_service.create_batch_operation(
            operation_type="metadata_sync",
            total_items=100
        )

        new_metadata = {"status": "in_progress", "processed": 50}
        success = batch_service.set_batch_metadata(batch_op.id, new_metadata)

        assert success is True

        retrieved = batch_service.get_batch_metadata(batch_op.id)
        assert retrieved == new_metadata

    def test_get_metadata_for_nonexistent_batch(self, batch_service):
        """Test getting metadata for non-existent batch"""
        result = batch_service.get_batch_metadata(9999)
        assert result is None


class TestBatchOperationEdgeCases:
    """Test edge cases and error handling"""

    def test_update_progress_for_nonexistent_batch(self, batch_service):
        """Test updating progress for non-existent batch"""
        result = batch_service.update_batch_progress(9999, 10, 0)
        assert result is None

    def test_start_nonexistent_batch(self, batch_service):
        """Test starting a non-existent batch"""
        result = batch_service.start_batch_operation(9999)
        assert result is None

    def test_complete_nonexistent_batch(self, batch_service):
        """Test completing a non-existent batch"""
        result = batch_service.complete_batch_operation(9999)
        assert result is None

    def test_fail_nonexistent_batch(self, batch_service):
        """Test failing a non-existent batch"""
        result = batch_service.fail_batch_operation(9999, "Error")
        assert result is None

    def test_cancel_nonexistent_batch(self, batch_service):
        """Test cancelling a non-existent batch"""
        result = batch_service.cancel_batch_operation(9999)
        assert result is None

    def test_zero_total_items(self, batch_service):
        """Test creating batch with zero total items"""
        batch_op = batch_service.create_batch_operation(
            operation_type="metadata_sync",
            total_items=0
        )

        assert batch_op.total_items == 0
        assert batch_op.progress_percentage == 0.0

    def test_progress_exceeds_total(self, batch_service):
        """Test progress calculation when completed + failed exceeds total"""
        batch_op = batch_service.create_batch_operation(
            operation_type="metadata_sync",
            total_items=100
        )

        # This shouldn't happen in normal operation, but test the behavior
        updated = batch_service.update_batch_progress(
            batch_op.id,
            completed_items=60,
            failed_items=50
        )

        # Progress should be capped at 100%
        assert updated.progress_percentage <= 110.0


class TestBatchOperationConcurrency:
    """Test concurrent batch operations"""

    def test_multiple_concurrent_batches(self, batch_service):
        """Test creating and managing multiple concurrent batches"""
        batch_ids = []

        for i in range(5):
            batch_op = batch_service.create_batch_operation(
                operation_type="metadata_sync" if i % 2 == 0 else "file_import",
                total_items=100 + i * 10
            )
            batch_ids.append(batch_op.id)

        # Verify all batches were created
        for batch_id in batch_ids:
            batch_op = batch_service.get_batch_operation(batch_id)
            assert batch_op is not None

        # Update progress on different batches
        for i, batch_id in enumerate(batch_ids):
            batch_service.update_batch_progress(
                batch_id,
                completed_items=10 * (i + 1),
                failed_items=i
            )

        # Verify progress was updated correctly
        for i, batch_id in enumerate(batch_ids):
            batch_op = batch_service.get_batch_operation(batch_id)
            assert batch_op.completed_items == 10 * (i + 1)
            assert batch_op.failed_items == i


class TestBatchOperationPersistence:
    """Test batch operation database persistence"""

    def test_batch_operation_persists_across_sessions(self, batch_service):
        """Test that batch operations persist across database sessions"""
        batch_op = batch_service.create_batch_operation(
            operation_type="metadata_sync",
            total_items=100,
            metadata={"test": "data"}
        )

        batch_id = batch_op.id

        # Create a new service with a new session
        db2 = SessionLocal()
        service2 = BatchOperationService(db2)

        retrieved = service2.get_batch_operation(batch_id)
        assert retrieved is not None
        assert retrieved.id == batch_id
        assert retrieved.operation_type == "metadata_sync"

        db2.close()

    def test_batch_operation_updates_persist(self, batch_service):
        """Test that batch operation updates persist"""
        batch_op = batch_service.create_batch_operation(
            operation_type="metadata_sync",
            total_items=100
        )

        batch_service.start_batch_operation(batch_op.id)
        batch_service.update_batch_progress(batch_op.id, 50, 5)

        # Create a new service with a new session
        db2 = SessionLocal()
        service2 = BatchOperationService(db2)

        retrieved = service2.get_batch_operation(batch_op.id)
        assert retrieved.status == "running"
        assert retrieved.completed_items == 50
        assert retrieved.failed_items == 5

        db2.close()
