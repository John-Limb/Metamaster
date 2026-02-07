"""Comprehensive unit tests for SQLAlchemy database models"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.models import (
    Movie,
    MovieFile,
    TVShow,
    Season,
    Episode,
    EpisodeFile,
    APICache,
    FileQueue,
    TaskError,
    BatchOperation,
)
from app.database import Base


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


# ============================================================================
# Movie Model Tests
# ============================================================================


class TestMovieModel:
    """Tests for Movie model"""

    def test_create_movie(self, db_session):
        """Test creating a movie"""
        movie = Movie(
            title="The Matrix",
            year=1999,
            omdb_id="tt0133093",
            plot="A computer hacker learns about reality",
            rating=8.7,
            runtime=136,
            genres='["Sci-Fi", "Action"]',
        )
        db_session.add(movie)
        db_session.commit()

        retrieved = db_session.query(Movie).filter_by(title="The Matrix").first()
        assert retrieved is not None
        assert retrieved.year == 1999
        assert retrieved.rating == 8.7

    def test_movie_timestamps(self, db_session):
        """Test movie creation and update timestamps"""
        movie = Movie(title="Test Movie")
        db_session.add(movie)
        db_session.commit()

        assert movie.created_at is not None
        assert movie.updated_at is not None
        # Timestamps may differ by microseconds, so check they're close
        assert abs((movie.updated_at - movie.created_at).total_seconds()) < 0.01

    def test_movie_update_timestamp(self, db_session):
        """Test movie update timestamp changes"""
        movie = Movie(title="Test Movie")
        db_session.add(movie)
        db_session.commit()

        original_updated = movie.updated_at
        movie.rating = 8.5
        db_session.commit()

        assert movie.updated_at >= original_updated

    def test_movie_unique_omdb_id(self, db_session):
        """Test unique constraint on omdb_id"""
        movie1 = Movie(title="Movie 1", omdb_id="tt0133093")
        movie2 = Movie(title="Movie 2", omdb_id="tt0133093")

        db_session.add(movie1)
        db_session.commit()

        db_session.add(movie2)
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()

    def test_movie_optional_fields(self, db_session):
        """Test movie with optional fields"""
        movie = Movie(title="Minimal Movie")
        db_session.add(movie)
        db_session.commit()

        retrieved = db_session.query(Movie).filter_by(title="Minimal Movie").first()
        assert retrieved.year is None
        assert retrieved.rating is None
        assert retrieved.runtime is None


# ============================================================================
# MovieFile Model Tests
# ============================================================================


class TestMovieFileModel:
    """Tests for MovieFile model"""

    def test_create_movie_file(self, db_session):
        """Test creating a movie file"""
        movie = Movie(title="Test Movie")
        db_session.add(movie)
        db_session.commit()

        movie_file = MovieFile(
            movie_id=movie.id,
            file_path="/path/to/movie.mp4",
            file_size=1024000000,
            resolution="1920x1080",
            bitrate=5000,
            codec_video="h264",
            codec_audio="aac",
            duration=7200,
        )
        db_session.add(movie_file)
        db_session.commit()

        retrieved = (
            db_session.query(MovieFile)
            .filter_by(file_path="/path/to/movie.mp4")
            .first()
        )
        assert retrieved is not None
        assert retrieved.movie_id == movie.id
        assert retrieved.resolution == "1920x1080"

    def test_movie_file_relationship(self, db_session):
        """Test movie-file relationship"""
        movie = Movie(title="Test Movie")
        db_session.add(movie)
        db_session.commit()

        movie_file = MovieFile(movie_id=movie.id, file_path="/path/to/movie.mp4")
        db_session.add(movie_file)
        db_session.commit()

        retrieved_movie = db_session.query(Movie).filter_by(id=movie.id).first()
        assert len(retrieved_movie.files) == 1
        assert retrieved_movie.files[0].file_path == "/path/to/movie.mp4"

    def test_movie_file_cascade_delete(self, db_session):
        """Test cascade delete of movie files"""
        movie = Movie(title="Test Movie")
        db_session.add(movie)
        db_session.commit()

        movie_file = MovieFile(movie_id=movie.id, file_path="/path/to/movie.mp4")
        db_session.add(movie_file)
        db_session.commit()

        db_session.delete(movie)
        db_session.commit()

        orphaned_file = (
            db_session.query(MovieFile)
            .filter_by(file_path="/path/to/movie.mp4")
            .first()
        )
        assert orphaned_file is None

    def test_movie_file_unique_path(self, db_session):
        """Test unique constraint on file_path"""
        movie1 = Movie(title="Movie 1")
        movie2 = Movie(title="Movie 2")
        db_session.add_all([movie1, movie2])
        db_session.commit()

        file1 = MovieFile(movie_id=movie1.id, file_path="/path/to/file.mp4")
        file2 = MovieFile(movie_id=movie2.id, file_path="/path/to/file.mp4")

        db_session.add(file1)
        db_session.commit()

        db_session.add(file2)
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()


# ============================================================================
# TVShow Model Tests
# ============================================================================


class TestTVShowModel:
    """Tests for TVShow model"""

    def test_create_tv_show(self, db_session):
        """Test creating a TV show"""
        show = TVShow(
            title="Breaking Bad",
            tvdb_id="81189",
            plot="A chemistry teacher turns to cooking meth",
            rating=9.5,
            genres='["Drama", "Crime"]',
            status="Ended",
        )
        db_session.add(show)
        db_session.commit()

        retrieved = db_session.query(TVShow).filter_by(title="Breaking Bad").first()
        assert retrieved is not None
        assert retrieved.rating == 9.5
        assert retrieved.status == "Ended"

    def test_tv_show_unique_tvdb_id(self, db_session):
        """Test unique constraint on tvdb_id"""
        show1 = TVShow(title="Show 1", tvdb_id="81189")
        show2 = TVShow(title="Show 2", tvdb_id="81189")

        db_session.add(show1)
        db_session.commit()

        db_session.add(show2)
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()


# ============================================================================
# Season Model Tests
# ============================================================================


class TestSeasonModel:
    """Tests for Season model"""

    def test_create_season(self, db_session):
        """Test creating a season"""
        show = TVShow(title="Breaking Bad")
        db_session.add(show)
        db_session.commit()

        season = Season(show_id=show.id, season_number=1, tvdb_id="123456")
        db_session.add(season)
        db_session.commit()

        retrieved = db_session.query(Season).filter_by(season_number=1).first()
        assert retrieved is not None
        assert retrieved.show_id == show.id

    def test_season_relationship(self, db_session):
        """Test season-show relationship"""
        show = TVShow(title="Breaking Bad")
        db_session.add(show)
        db_session.commit()

        season = Season(show_id=show.id, season_number=1)
        db_session.add(season)
        db_session.commit()

        retrieved_show = db_session.query(TVShow).filter_by(id=show.id).first()
        assert len(retrieved_show.seasons) == 1
        assert retrieved_show.seasons[0].season_number == 1

    def test_season_cascade_delete(self, db_session):
        """Test cascade delete of seasons"""
        show = TVShow(title="Breaking Bad")
        db_session.add(show)
        db_session.commit()

        season = Season(show_id=show.id, season_number=1)
        db_session.add(season)
        db_session.commit()

        db_session.delete(show)
        db_session.commit()

        orphaned_season = db_session.query(Season).filter_by(season_number=1).first()
        assert orphaned_season is None


# ============================================================================
# Episode Model Tests
# ============================================================================


class TestEpisodeModel:
    """Tests for Episode model"""

    def test_create_episode(self, db_session):
        """Test creating an episode"""
        show = TVShow(title="Breaking Bad")
        db_session.add(show)
        db_session.commit()

        season = Season(show_id=show.id, season_number=1)
        db_session.add(season)
        db_session.commit()

        episode = Episode(
            season_id=season.id,
            episode_number=1,
            tvdb_id="123456",
            title="Pilot",
            plot="The beginning",
            air_date="2008-01-20",
            rating=8.5,
        )
        db_session.add(episode)
        db_session.commit()

        retrieved = db_session.query(Episode).filter_by(episode_number=1).first()
        assert retrieved is not None
        assert retrieved.title == "Pilot"
        assert retrieved.rating == 8.5

    def test_episode_unique_tvdb_id(self, db_session):
        """Test unique constraint on episode tvdb_id"""
        show = TVShow(title="Show")
        season = Season(show_id=1, season_number=1)
        db_session.add_all([show, season])
        db_session.commit()

        ep1 = Episode(season_id=season.id, episode_number=1, tvdb_id="123")
        ep2 = Episode(season_id=season.id, episode_number=2, tvdb_id="123")

        db_session.add(ep1)
        db_session.commit()

        db_session.add(ep2)
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()

    def test_episode_relationship(self, db_session):
        """Test episode-season relationship"""
        show = TVShow(title="Breaking Bad")
        db_session.add(show)
        db_session.commit()

        season = Season(show_id=show.id, season_number=1)
        db_session.add(season)
        db_session.commit()

        episode = Episode(season_id=season.id, episode_number=1)
        db_session.add(episode)
        db_session.commit()

        retrieved_season = db_session.query(Season).filter_by(id=season.id).first()
        assert len(retrieved_season.episodes) == 1


# ============================================================================
# EpisodeFile Model Tests
# ============================================================================


class TestEpisodeFileModel:
    """Tests for EpisodeFile model"""

    def test_create_episode_file(self, db_session):
        """Test creating an episode file"""
        show = TVShow(title="Breaking Bad")
        db_session.add(show)
        db_session.commit()

        season = Season(show_id=show.id, season_number=1)
        db_session.add(season)
        db_session.commit()

        episode = Episode(season_id=season.id, episode_number=1)
        db_session.add(episode)
        db_session.commit()

        episode_file = EpisodeFile(
            episode_id=episode.id,
            file_path="/path/to/episode.mp4",
            file_size=512000000,
            resolution="1920x1080",
            bitrate=4000,
        )
        db_session.add(episode_file)
        db_session.commit()

        retrieved = (
            db_session.query(EpisodeFile)
            .filter_by(file_path="/path/to/episode.mp4")
            .first()
        )
        assert retrieved is not None
        assert retrieved.episode_id == episode.id

    def test_episode_file_cascade_delete(self, db_session):
        """Test cascade delete of episode files"""
        show = TVShow(title="Show")
        season = Season(show_id=1, season_number=1)
        episode = Episode(season_id=1, episode_number=1)
        db_session.add_all([show, season, episode])
        db_session.commit()

        episode_file = EpisodeFile(
            episode_id=episode.id, file_path="/path/to/episode.mp4"
        )
        db_session.add(episode_file)
        db_session.commit()

        db_session.delete(episode)
        db_session.commit()

        orphaned_file = (
            db_session.query(EpisodeFile)
            .filter_by(file_path="/path/to/episode.mp4")
            .first()
        )
        assert orphaned_file is None


# ============================================================================
# APICache Model Tests
# ============================================================================


class TestAPICacheModel:
    """Tests for APICache model"""

    def test_create_api_cache(self, db_session):
        """Test creating API cache entry"""
        cache = APICache(
            api_type="omdb",
            query_key="tt0133093",
            response_data='{"title": "The Matrix"}',
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
        db_session.add(cache)
        db_session.commit()

        retrieved = db_session.query(APICache).filter_by(query_key="tt0133093").first()
        assert retrieved is not None
        assert retrieved.api_type == "omdb"

    def test_api_cache_expiration(self, db_session):
        """Test API cache expiration"""
        past = datetime.utcnow() - timedelta(days=1)
        future = datetime.utcnow() + timedelta(days=30)

        expired = APICache(
            api_type="omdb", query_key="expired", response_data="{}", expires_at=past
        )
        active = APICache(
            api_type="omdb", query_key="active", response_data="{}", expires_at=future
        )

        db_session.add_all([expired, active])
        db_session.commit()

        active_entries = (
            db_session.query(APICache)
            .filter(APICache.expires_at > datetime.utcnow())
            .all()
        )
        assert len(active_entries) == 1


# ============================================================================
# FileQueue Model Tests
# ============================================================================


class TestFileQueueModel:
    """Tests for FileQueue model"""

    def test_create_file_queue_entry(self, db_session):
        """Test creating file queue entry"""
        queue_entry = FileQueue(
            file_path="/path/to/file.mp4", status="pending", media_type="movie"
        )
        db_session.add(queue_entry)
        db_session.commit()

        retrieved = (
            db_session.query(FileQueue).filter_by(file_path="/path/to/file.mp4").first()
        )
        assert retrieved is not None
        assert retrieved.status == "pending"

    def test_file_queue_status_transitions(self, db_session):
        """Test file queue status transitions"""
        queue_entry = FileQueue(
            file_path="/path/to/file.mp4", status="pending", media_type="movie"
        )
        db_session.add(queue_entry)
        db_session.commit()

        queue_entry.status = "processing"
        db_session.commit()

        queue_entry.status = "completed"
        queue_entry.processed_at = datetime.utcnow()
        db_session.commit()

        retrieved = db_session.query(FileQueue).filter_by(id=queue_entry.id).first()
        assert retrieved.status == "completed"
        assert retrieved.processed_at is not None

    def test_file_queue_unique_path(self, db_session):
        """Test unique constraint on file_path"""
        entry1 = FileQueue(
            file_path="/path/to/file.mp4", status="pending", media_type="movie"
        )
        entry2 = FileQueue(
            file_path="/path/to/file.mp4", status="pending", media_type="movie"
        )

        db_session.add(entry1)
        db_session.commit()

        db_session.add(entry2)
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()


# ============================================================================
# TaskError Model Tests
# ============================================================================


class TestTaskErrorModel:
    """Tests for TaskError model"""

    def test_create_task_error(self, db_session):
        """Test creating task error"""
        error = TaskError(
            task_id="task123",
            task_name="app.tasks.analyze_file",
            error_message="File not found",
            error_traceback="Traceback...",
            severity="critical",
            retry_count=2,
        )
        db_session.add(error)
        db_session.commit()

        retrieved = db_session.query(TaskError).filter_by(task_id="task123").first()
        assert retrieved is not None
        assert retrieved.severity == "critical"
        assert retrieved.retry_count == 2

    def test_task_error_resolution(self, db_session):
        """Test task error resolution"""
        error = TaskError(
            task_id="task123",
            task_name="app.tasks.analyze_file",
            error_message="Error",
            severity="critical",
        )
        db_session.add(error)
        db_session.commit()

        error.resolved_at = datetime.utcnow()
        db_session.commit()

        retrieved = db_session.query(TaskError).filter_by(id=error.id).first()
        assert retrieved.resolved_at is not None

    def test_task_error_severity_levels(self, db_session):
        """Test different severity levels"""
        severities = ["critical", "warning", "info"]

        for i, severity in enumerate(severities):
            error = TaskError(
                task_id=f"task{i}",
                task_name="app.tasks.test",
                error_message="Test",
                severity=severity,
            )
            db_session.add(error)

        db_session.commit()

        critical_errors = (
            db_session.query(TaskError).filter_by(severity="critical").all()
        )
        assert len(critical_errors) == 1


# ============================================================================
# BatchOperation Model Tests
# ============================================================================


class TestBatchOperationModel:
    """Tests for BatchOperation model"""

    def test_create_batch_operation(self, db_session):
        """Test creating batch operation"""
        batch = BatchOperation(
            operation_type="metadata_sync",
            status="pending",
            total_items=100,
            completed_items=0,
            failed_items=0,
            progress_percentage=0.0,
        )
        db_session.add(batch)
        db_session.commit()

        retrieved = (
            db_session.query(BatchOperation)
            .filter_by(operation_type="metadata_sync")
            .first()
        )
        assert retrieved is not None
        assert retrieved.total_items == 100

    def test_batch_operation_progress(self, db_session):
        """Test batch operation progress tracking"""
        batch = BatchOperation(
            operation_type="file_import",
            status="running",
            total_items=100,
            completed_items=0,
        )
        db_session.add(batch)
        db_session.commit()

        batch.completed_items = 50
        batch.progress_percentage = 50.0
        db_session.commit()

        retrieved = db_session.query(BatchOperation).filter_by(id=batch.id).first()
        assert retrieved.progress_percentage == 50.0

    def test_batch_operation_completion(self, db_session):
        """Test batch operation completion"""
        batch = BatchOperation(
            operation_type="metadata_sync",
            status="running",
            total_items=100,
            completed_items=100,
            failed_items=0,
            progress_percentage=100.0,
        )
        db_session.add(batch)
        db_session.commit()

        batch.status = "completed"
        batch.completed_at = datetime.utcnow()
        db_session.commit()

        retrieved = db_session.query(BatchOperation).filter_by(id=batch.id).first()
        assert retrieved.status == "completed"
        assert retrieved.completed_at is not None

    def test_batch_operation_failure(self, db_session):
        """Test batch operation failure"""
        batch = BatchOperation(
            operation_type="file_import",
            status="failed",
            total_items=100,
            completed_items=50,
            failed_items=50,
            error_message="Import failed",
        )
        db_session.add(batch)
        db_session.commit()

        retrieved = db_session.query(BatchOperation).filter_by(id=batch.id).first()
        assert retrieved.status == "failed"
        assert retrieved.error_message == "Import failed"


# ============================================================================
# Model Relationship Tests
# ============================================================================


class TestModelRelationships:
    """Tests for model relationships and cascading"""

    def test_full_tv_show_hierarchy(self, db_session):
        """Test complete TV show hierarchy"""
        show = TVShow(title="Breaking Bad")
        db_session.add(show)
        db_session.commit()

        season = Season(show_id=show.id, season_number=1)
        db_session.add(season)
        db_session.commit()

        episode = Episode(season_id=season.id, episode_number=1, title="Pilot")
        db_session.add(episode)
        db_session.commit()

        episode_file = EpisodeFile(
            episode_id=episode.id, file_path="/path/to/episode.mp4"
        )
        db_session.add(episode_file)
        db_session.commit()

        # Verify hierarchy
        retrieved_show = db_session.query(TVShow).filter_by(id=show.id).first()
        assert len(retrieved_show.seasons) == 1
        assert len(retrieved_show.seasons[0].episodes) == 1
        assert len(retrieved_show.seasons[0].episodes[0].files) == 1

    def test_cascade_delete_full_hierarchy(self, db_session):
        """Test cascade delete through full hierarchy"""
        show = TVShow(title="Breaking Bad")
        db_session.add(show)
        db_session.commit()

        season = Season(show_id=show.id, season_number=1)
        db_session.add(season)
        db_session.commit()

        episode = Episode(season_id=season.id, episode_number=1)
        db_session.add(episode)
        db_session.commit()

        episode_file = EpisodeFile(episode_id=episode.id, file_path="/path/to/file.mp4")
        db_session.add(episode_file)
        db_session.commit()

        # Delete show
        db_session.delete(show)
        db_session.commit()

        # Verify cascade
        assert db_session.query(TVShow).filter_by(id=show.id).first() is None
        assert db_session.query(Season).filter_by(show_id=show.id).first() is None
        assert db_session.query(Episode).filter_by(season_id=season.id).first() is None
        assert (
            db_session.query(EpisodeFile).filter_by(episode_id=episode.id).first()
            is None
        )
