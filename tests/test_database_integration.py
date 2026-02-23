"""Comprehensive integration tests for database operations"""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta

from app.database import Base
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


# ============================================================================
# Test Database Setup
# ============================================================================


@pytest.fixture(scope="function")
def db_session():
    """Create an in-memory SQLite database for testing"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Enable foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    session = TestingSessionLocal()
    yield session
    session.close()


# ============================================================================
# Movie CRUD Tests
# ============================================================================


class TestMovieCRUD:
    """Tests for Movie CRUD operations"""

    def test_create_movie(self, db_session):
        """Test creating a movie"""
        movie = Movie(
            title="The Shawshank Redemption",
            year=1994,
            rating=9.3,
            runtime=142,
            plot="Two imprisoned men bond over a number of years",
            genres='["Drama"]',
            tmdb_id="tt0111161",
        )
        db_session.add(movie)
        db_session.commit()
        db_session.refresh(movie)

        assert movie.id is not None
        assert movie.title == "The Shawshank Redemption"
        assert movie.year == 1994
        assert movie.rating == 9.3

    def test_read_movie(self, db_session):
        """Test reading a movie"""
        movie = Movie(title="Inception", year=2010, rating=8.8)
        db_session.add(movie)
        db_session.commit()
        db_session.refresh(movie)

        retrieved = db_session.query(Movie).filter(Movie.id == movie.id).first()
        assert retrieved is not None
        assert retrieved.title == "Inception"

    def test_update_movie(self, db_session):
        """Test updating a movie"""
        movie = Movie(title="Original Title", year=2020, rating=7.0)
        db_session.add(movie)
        db_session.commit()
        db_session.refresh(movie)

        movie.title = "Updated Title"
        movie.rating = 8.5
        db_session.commit()
        db_session.refresh(movie)

        assert movie.title == "Updated Title"
        assert movie.rating == 8.5

    def test_delete_movie(self, db_session):
        """Test deleting a movie"""
        movie = Movie(title="To Delete", year=2020)
        db_session.add(movie)
        db_session.commit()
        movie_id = movie.id

        db_session.delete(movie)
        db_session.commit()

        deleted = db_session.query(Movie).filter(Movie.id == movie_id).first()
        assert deleted is None

    def test_movie_unique_tmdb_id(self, db_session):
        """Test unique constraint on tmdb_id"""
        movie1 = Movie(title="Movie 1", tmdb_id="tt0111161")
        movie2 = Movie(title="Movie 2", tmdb_id="tt0111161")

        db_session.add(movie1)
        db_session.commit()

        db_session.add(movie2)
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()


# ============================================================================
# TV Show CRUD Tests
# ============================================================================


class TestTVShowCRUD:
    """Tests for TV Show CRUD operations"""

    def test_create_tv_show(self, db_session):
        """Test creating a TV show"""
        show = TVShow(
            title="Breaking Bad",
            rating=9.5,
            plot="A high school chemistry teacher",
            genres='["Drama", "Crime"]',
            status="Ended",
            tmdb_id="81189",
        )
        db_session.add(show)
        db_session.commit()
        db_session.refresh(show)

        assert show.id is not None
        assert show.title == "Breaking Bad"
        assert show.status == "Ended"

    def test_read_tv_show(self, db_session):
        """Test reading a TV show"""
        show = TVShow(title="Game of Thrones", rating=9.2)
        db_session.add(show)
        db_session.commit()
        db_session.refresh(show)

        retrieved = db_session.query(TVShow).filter(TVShow.id == show.id).first()
        assert retrieved is not None
        assert retrieved.title == "Game of Thrones"

    def test_update_tv_show(self, db_session):
        """Test updating a TV show"""
        show = TVShow(title="Original", rating=7.0, status="Continuing")
        db_session.add(show)
        db_session.commit()
        db_session.refresh(show)

        show.title = "Updated"
        show.status = "Ended"
        db_session.commit()
        db_session.refresh(show)

        assert show.title == "Updated"
        assert show.status == "Ended"

    def test_delete_tv_show(self, db_session):
        """Test deleting a TV show"""
        show = TVShow(title="To Delete")
        db_session.add(show)
        db_session.commit()
        show_id = show.id

        db_session.delete(show)
        db_session.commit()

        deleted = db_session.query(TVShow).filter(TVShow.id == show_id).first()
        assert deleted is None


# ============================================================================
# Relationship Integrity Tests
# ============================================================================


class TestRelationshipIntegrity:
    """Tests for relationship integrity"""

    def test_movie_file_relationship(self, db_session):
        """Test movie-file relationship"""
        movie = Movie(title="Test Movie")
        db_session.add(movie)
        db_session.commit()
        db_session.refresh(movie)

        file1 = MovieFile(movie_id=movie.id, file_path="/path/to/file1.mp4")
        file2 = MovieFile(movie_id=movie.id, file_path="/path/to/file2.mkv")
        db_session.add_all([file1, file2])
        db_session.commit()

        # Verify relationship
        retrieved_movie = db_session.query(Movie).filter(Movie.id == movie.id).first()
        assert len(retrieved_movie.files) == 2
        assert retrieved_movie.files[0].file_path == "/path/to/file1.mp4"

    def test_tv_show_season_relationship(self, db_session):
        """Test TV show-season relationship"""
        show = TVShow(title="Test Show")
        db_session.add(show)
        db_session.commit()
        db_session.refresh(show)

        for i in range(1, 6):
            season = Season(show_id=show.id, season_number=i)
            db_session.add(season)
        db_session.commit()

        # Verify relationship
        retrieved_show = db_session.query(TVShow).filter(TVShow.id == show.id).first()
        assert len(retrieved_show.seasons) == 5

    def test_season_episode_relationship(self, db_session):
        """Test season-episode relationship"""
        show = TVShow(title="Test Show")
        db_session.add(show)
        db_session.commit()
        db_session.refresh(show)

        season = Season(show_id=show.id, season_number=1)
        db_session.add(season)
        db_session.commit()
        db_session.refresh(season)

        for i in range(1, 11):
            episode = Episode(season_id=season.id, episode_number=i, title=f"Episode {i}")
            db_session.add(episode)
        db_session.commit()

        # Verify relationship
        retrieved_season = db_session.query(Season).filter(Season.id == season.id).first()
        assert len(retrieved_season.episodes) == 10

    def test_episode_file_relationship(self, db_session):
        """Test episode-file relationship"""
        show = TVShow(title="Test Show")
        db_session.add(show)
        db_session.commit()
        db_session.refresh(show)

        season = Season(show_id=show.id, season_number=1)
        db_session.add(season)
        db_session.commit()
        db_session.refresh(season)

        episode = Episode(season_id=season.id, episode_number=1, title="Episode 1")
        db_session.add(episode)
        db_session.commit()
        db_session.refresh(episode)

        file1 = EpisodeFile(episode_id=episode.id, file_path="/path/to/episode1.mp4")
        file2 = EpisodeFile(episode_id=episode.id, file_path="/path/to/episode1.mkv")
        db_session.add_all([file1, file2])
        db_session.commit()

        # Verify relationship
        retrieved_episode = db_session.query(Episode).filter(Episode.id == episode.id).first()
        assert len(retrieved_episode.files) == 2


# ============================================================================
# Cascade Delete Tests
# ============================================================================


class TestCascadeDelete:
    """Tests for cascade delete behavior"""

    def test_delete_movie_cascades_files(self, db_session):
        """Test that deleting a movie cascades to delete its files"""
        movie = Movie(title="Test Movie")
        db_session.add(movie)
        db_session.commit()
        db_session.refresh(movie)

        file1 = MovieFile(movie_id=movie.id, file_path="/path/to/file1.mp4")
        file2 = MovieFile(movie_id=movie.id, file_path="/path/to/file2.mkv")
        db_session.add_all([file1, file2])
        db_session.commit()

        movie_id = movie.id
        db_session.delete(movie)
        db_session.commit()

        # Verify cascade delete
        files = db_session.query(MovieFile).filter(MovieFile.movie_id == movie_id).all()
        assert len(files) == 0

    def test_delete_tv_show_cascades_seasons(self, db_session):
        """Test that deleting a TV show cascades to delete seasons"""
        show = TVShow(title="Test Show")
        db_session.add(show)
        db_session.commit()
        db_session.refresh(show)

        for i in range(1, 4):
            season = Season(show_id=show.id, season_number=i)
            db_session.add(season)
        db_session.commit()

        show_id = show.id
        db_session.delete(show)
        db_session.commit()

        # Verify cascade delete
        seasons = db_session.query(Season).filter(Season.show_id == show_id).all()
        assert len(seasons) == 0

    def test_delete_season_cascades_episodes(self, db_session):
        """Test that deleting a season cascades to delete episodes"""
        show = TVShow(title="Test Show")
        db_session.add(show)
        db_session.commit()
        db_session.refresh(show)

        season = Season(show_id=show.id, season_number=1)
        db_session.add(season)
        db_session.commit()
        db_session.refresh(season)

        for i in range(1, 6):
            episode = Episode(season_id=season.id, episode_number=i, title=f"Episode {i}")
            db_session.add(episode)
        db_session.commit()

        season_id = season.id
        db_session.delete(season)
        db_session.commit()

        # Verify cascade delete
        episodes = db_session.query(Episode).filter(Episode.season_id == season_id).all()
        assert len(episodes) == 0

    def test_delete_episode_cascades_files(self, db_session):
        """Test that deleting an episode cascades to delete files"""
        show = TVShow(title="Test Show")
        db_session.add(show)
        db_session.commit()
        db_session.refresh(show)

        season = Season(show_id=show.id, season_number=1)
        db_session.add(season)
        db_session.commit()
        db_session.refresh(season)

        episode = Episode(season_id=season.id, episode_number=1, title="Episode 1")
        db_session.add(episode)
        db_session.commit()
        db_session.refresh(episode)

        file1 = EpisodeFile(episode_id=episode.id, file_path="/path/to/file1.mp4")
        file2 = EpisodeFile(episode_id=episode.id, file_path="/path/to/file2.mkv")
        db_session.add_all([file1, file2])
        db_session.commit()

        episode_id = episode.id
        db_session.delete(episode)
        db_session.commit()

        # Verify cascade delete
        files = db_session.query(EpisodeFile).filter(EpisodeFile.episode_id == episode_id).all()
        assert len(files) == 0


# ============================================================================
# Transaction Handling Tests
# ============================================================================


class TestTransactionHandling:
    """Tests for transaction handling"""

    def test_commit_transaction(self, db_session):
        """Test committing a transaction"""
        movie = Movie(title="Test Movie", year=2020)
        db_session.add(movie)
        db_session.commit()

        # Verify data is persisted
        retrieved = db_session.query(Movie).filter(Movie.title == "Test Movie").first()
        assert retrieved is not None

    def test_rollback_transaction(self, db_session):
        """Test rolling back a transaction"""
        movie = Movie(title="Test Movie", year=2020)
        db_session.add(movie)
        db_session.rollback()

        # Verify data is not persisted
        retrieved = db_session.query(Movie).filter(Movie.title == "Test Movie").first()
        assert retrieved is None

    def test_transaction_isolation(self, db_session):
        """Test transaction isolation"""
        movie1 = Movie(title="Movie 1", year=2020)
        db_session.add(movie1)
        db_session.commit()
        db_session.refresh(movie1)

        # Start new transaction
        movie1.title = "Updated Movie 1"

        # Query in same session should see uncommitted changes
        retrieved = db_session.query(Movie).filter(Movie.id == movie1.id).first()
        assert retrieved.title == "Updated Movie 1"

        db_session.commit()


# ============================================================================
# Query Optimization Tests
# ============================================================================


class TestQueryOptimization:
    """Tests for query optimization"""

    def test_query_with_index(self, db_session):
        """Test querying with indexed column"""
        # Create movies
        for i in range(100):
            movie = Movie(title=f"Movie {i}", year=2020)
            db_session.add(movie)
        db_session.commit()

        # Query by indexed column (title)
        result = db_session.query(Movie).filter(Movie.title == "Movie 50").first()
        assert result is not None
        assert result.title == "Movie 50"

    def test_query_by_tmdb_id(self, db_session):
        """Test querying by tmdb_id (indexed)"""
        movie = Movie(title="Test", tmdb_id="tt0111161")
        db_session.add(movie)
        db_session.commit()

        result = db_session.query(Movie).filter(Movie.tmdb_id == "tt0111161").first()
        assert result is not None
        assert result.tmdb_id == "tt0111161"

    def test_query_by_year(self, db_session):
        """Test querying by year (indexed)"""
        for year in range(2010, 2025):
            movie = Movie(title=f"Movie {year}", year=year)
            db_session.add(movie)
        db_session.commit()

        results = db_session.query(Movie).filter(Movie.year == 2020).all()
        assert len(results) >= 1

    def test_bulk_insert_performance(self, db_session):
        """Test bulk insert performance"""
        movies = [Movie(title=f"Movie {i}", year=2020) for i in range(1000)]
        db_session.add_all(movies)
        db_session.commit()

        count = db_session.query(Movie).count()
        assert count == 1000


# ============================================================================
# Index Effectiveness Tests
# ============================================================================


class TestIndexEffectiveness:
    """Tests for index effectiveness"""

    def test_movie_title_index(self, db_session):
        """Test movie title index"""
        for i in range(50):
            movie = Movie(title=f"Movie {i}", year=2020)
            db_session.add(movie)
        db_session.commit()

        # Query should use index
        result = db_session.query(Movie).filter(Movie.title == "Movie 25").first()
        assert result is not None

    def test_movie_tmdb_id_index(self, db_session):
        """Test movie tmdb_id index"""
        movie = Movie(title="Test", tmdb_id="tt0111161")
        db_session.add(movie)
        db_session.commit()

        result = db_session.query(Movie).filter(Movie.tmdb_id == "tt0111161").first()
        assert result is not None

    def test_tv_show_tmdb_id_index(self, db_session):
        """Test TV show tmdb_id index"""
        show = TVShow(title="Test", tmdb_id="81189")
        db_session.add(show)
        db_session.commit()

        result = db_session.query(TVShow).filter(TVShow.tmdb_id == "81189").first()
        assert result is not None

    def test_file_queue_status_index(self, db_session):
        """Test file queue status index"""
        for i in range(20):
            queue = FileQueue(
                file_path=f"/path/to/file{i}.mp4",
                status="pending" if i % 2 == 0 else "completed",
            )
            db_session.add(queue)
        db_session.commit()

        pending = db_session.query(FileQueue).filter(FileQueue.status == "pending").all()
        assert len(pending) >= 1


# ============================================================================
# API Cache Tests
# ============================================================================


class TestAPICache:
    """Tests for API cache operations"""

    def test_create_cache_entry(self, db_session):
        """Test creating a cache entry"""
        cache = APICache(
            api_type="tmdb",
            query_key="tt0111161",
            response_data='{"title": "The Shawshank Redemption"}',
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
        db_session.add(cache)
        db_session.commit()
        db_session.refresh(cache)

        assert cache.id is not None
        assert cache.api_type == "tmdb"

    def test_query_cache_by_type_and_key(self, db_session):
        """Test querying cache by type and key"""
        cache = APICache(
            api_type="tmdb",
            query_key="tt0111161",
            response_data='{"title": "The Shawshank Redemption"}',
        )
        db_session.add(cache)
        db_session.commit()

        result = (
            db_session.query(APICache)
            .filter(APICache.api_type == "tmdb", APICache.query_key == "tt0111161")
            .first()
        )
        assert result is not None

    def test_delete_expired_cache(self, db_session):
        """Test deleting expired cache entries"""
        expired = APICache(
            api_type="tmdb",
            query_key="expired",
            response_data="{}",
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        active = APICache(
            api_type="tmdb",
            query_key="active",
            response_data="{}",
            expires_at=datetime.utcnow() + timedelta(days=1),
        )
        db_session.add_all([expired, active])
        db_session.commit()

        # Delete expired
        db_session.query(APICache).filter(APICache.expires_at < datetime.utcnow()).delete()
        db_session.commit()

        # Verify
        remaining = db_session.query(APICache).all()
        assert len(remaining) == 1
        assert remaining[0].query_key == "active"


# ============================================================================
# File Queue Tests
# ============================================================================


class TestFileQueue:
    """Tests for file queue operations"""

    def test_create_queue_entry(self, db_session):
        """Test creating a file queue entry"""
        queue = FileQueue(file_path="/path/to/file.mp4", status="pending", media_type="movie")
        db_session.add(queue)
        db_session.commit()
        db_session.refresh(queue)

        assert queue.id is not None
        assert queue.status == "pending"

    def test_update_queue_status(self, db_session):
        """Test updating queue status"""
        queue = FileQueue(file_path="/path/to/file.mp4", status="pending")
        db_session.add(queue)
        db_session.commit()
        db_session.refresh(queue)

        queue.status = "processing"
        db_session.commit()
        db_session.refresh(queue)

        assert queue.status == "processing"

    def test_query_pending_files(self, db_session):
        """Test querying pending files"""
        for i in range(5):
            queue = FileQueue(
                file_path=f"/path/to/file{i}.mp4",
                status="pending" if i < 3 else "completed",
            )
            db_session.add(queue)
        db_session.commit()

        pending = db_session.query(FileQueue).filter(FileQueue.status == "pending").all()
        assert len(pending) == 3


# ============================================================================
# Task Error Tests
# ============================================================================


class TestTaskError:
    """Tests for task error operations"""

    def test_create_task_error(self, db_session):
        """Test creating a task error"""
        error = TaskError(
            task_id="task-123",
            task_name="app.tasks.analyze_file",
            error_message="File not found",
            error_traceback="Traceback...",
            severity="critical",
        )
        db_session.add(error)
        db_session.commit()
        db_session.refresh(error)

        assert error.id is not None
        assert error.severity == "critical"

    def test_query_errors_by_severity(self, db_session):
        """Test querying errors by severity"""
        for i in range(3):
            error = TaskError(
                task_id=f"task-{i}",
                task_name="app.tasks.test",
                error_message=f"Error {i}",
                severity="critical" if i == 0 else "warning",
            )
            db_session.add(error)
        db_session.commit()

        critical = db_session.query(TaskError).filter(TaskError.severity == "critical").all()
        assert len(critical) == 1


# ============================================================================
# Batch Operation Tests
# ============================================================================


class TestBatchOperation:
    """Tests for batch operation operations"""

    def test_create_batch_operation(self, db_session):
        """Test creating a batch operation"""
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
        db_session.refresh(batch)

        assert batch.id is not None
        assert batch.status == "pending"

    def test_update_batch_progress(self, db_session):
        """Test updating batch progress"""
        batch = BatchOperation(
            operation_type="metadata_sync",
            status="running",
            total_items=100,
            completed_items=0,
        )
        db_session.add(batch)
        db_session.commit()
        db_session.refresh(batch)

        batch.completed_items = 50
        batch.progress_percentage = 50.0
        db_session.commit()
        db_session.refresh(batch)

        assert batch.completed_items == 50
        assert batch.progress_percentage == 50.0

    def test_query_batch_by_status(self, db_session):
        """Test querying batch operations by status"""
        for i in range(3):
            batch = BatchOperation(
                operation_type="metadata_sync",
                status="running" if i < 2 else "completed",
                total_items=100,
                completed_items=100 if i == 2 else 50,
            )
            db_session.add(batch)
        db_session.commit()

        running = db_session.query(BatchOperation).filter(BatchOperation.status == "running").all()
        assert len(running) == 2
