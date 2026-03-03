"""Tests for database optimization module"""

import time

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.application.db_optimization.service import (
    ConnectionPoolMonitor,
    DatabaseOptimizationService,
    IndexAnalyzer,
    QueryExecutionPlanAnalyzer,
    QueryPerformanceTracker,
)
from app.config import settings
from app.database import Base
from app.models import Movie, TVShow
from tests.db_utils import TEST_DATABASE_URL


# Test fixtures
@pytest.fixture
def test_db():
    """Create a test database"""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = SessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def test_engine():
    """Create a test engine"""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def sample_movies(test_db):
    """Create sample movie data"""
    movies = [
        Movie(
            title="Test Movie 1",
            year=2020,
            tmdb_id="tt0000001",
            plot="Test plot 1",
            rating=8.5,
            runtime=120,
            genres="Action,Drama",
        ),
        Movie(
            title="Test Movie 2",
            year=2021,
            tmdb_id="tt0000002",
            plot="Test plot 2",
            rating=7.5,
            runtime=110,
            genres="Comedy,Romance",
        ),
        Movie(
            title="Test Movie 3",
            year=2022,
            tmdb_id="tt0000003",
            plot="Test plot 3",
            rating=9.0,
            runtime=130,
            genres="Action,Sci-Fi",
        ),
    ]

    for movie in movies:
        test_db.add(movie)
    test_db.commit()

    return movies


@pytest.fixture
def sample_tv_shows(test_db):
    """Create sample TV show data"""
    shows = [
        TVShow(
            title="Test Show 1",
            tmdb_id="tt0000001",
            plot="Test plot 1",
            rating=8.5,
            genres="Drama,Crime",
            status="Continuing",
        ),
        TVShow(
            title="Test Show 2",
            tmdb_id="tt0000002",
            plot="Test plot 2",
            rating=7.5,
            genres="Comedy",
            status="Ended",
        ),
    ]

    for show in shows:
        test_db.add(show)
    test_db.commit()

    return shows


# Tests for QueryPerformanceTracker
class TestQueryPerformanceTracker:
    """Test query performance tracking"""

    def test_tracker_initialization(self):
        """Test tracker initialization"""
        tracker = QueryPerformanceTracker(slow_query_threshold=1.0)
        assert tracker.slow_query_threshold == 1.0
        assert tracker.total_queries == 0
        assert tracker.total_time == 0.0
        assert len(tracker.slow_queries) == 0

    def test_record_query(self):
        """Test recording a query"""
        tracker = QueryPerformanceTracker()
        query = "SELECT * FROM movies WHERE title = ?"

        tracker.record_query(query, 0.5)

        assert tracker.total_queries == 1
        assert tracker.total_time == 0.5
        assert len(tracker.query_stats) > 0

    def test_slow_query_detection(self):
        """Test slow query detection"""
        tracker = QueryPerformanceTracker(slow_query_threshold=0.5)

        # Record a fast query
        tracker.record_query("SELECT * FROM movies", 0.1)
        assert len(tracker.slow_queries) == 0

        # Record a slow query
        tracker.record_query("SELECT * FROM movies WHERE title LIKE ?", 1.0)
        assert len(tracker.slow_queries) == 1

    def test_query_stats_aggregation(self):
        """Test query statistics aggregation"""
        tracker = QueryPerformanceTracker()
        query = "SELECT * FROM movies WHERE year = ?"

        # Record multiple executions of the same query
        tracker.record_query(query, 0.1)
        tracker.record_query(query, 0.2)
        tracker.record_query(query, 0.15)

        stats = tracker.get_query_stats()
        assert stats["total_queries"] == 3
        assert stats["total_time"] == pytest.approx(0.45, rel=0.01)
        assert stats["avg_time"] == pytest.approx(0.15, rel=0.01)

    def test_get_slow_queries(self):
        """Test retrieving slow queries"""
        tracker = QueryPerformanceTracker(slow_query_threshold=0.5)

        for i in range(15):
            tracker.record_query(f"SELECT * FROM movies WHERE id = {i}", 1.0)

        slow_queries = tracker.get_slow_queries(limit=10)
        assert len(slow_queries) == 10

    def test_reset_tracker(self):
        """Test resetting tracker"""
        tracker = QueryPerformanceTracker()
        tracker.record_query("SELECT * FROM movies", 0.5)

        assert tracker.total_queries == 1

        tracker.reset()

        assert tracker.total_queries == 0
        assert tracker.total_time == 0.0
        assert len(tracker.slow_queries) == 0


# Tests for ConnectionPoolMonitor
class TestConnectionPoolMonitor:
    """Test connection pool monitoring"""

    def test_monitor_initialization(self):
        """Test monitor initialization"""
        monitor = ConnectionPoolMonitor()
        assert len(monitor.pool_stats_history) == 0
        assert monitor.max_history == 1000

    def test_record_pool_stats(self, test_engine):
        """Test recording pool statistics"""
        monitor = ConnectionPoolMonitor()

        stats = monitor.record_pool_stats(test_engine.pool)

        assert stats is not None
        assert "timestamp" in stats
        assert len(monitor.pool_stats_history) == 1

    def test_pool_stats_history_limit(self, test_engine):
        """Test pool stats history limit"""
        monitor = ConnectionPoolMonitor()
        monitor.max_history = 10

        for _ in range(20):
            monitor.record_pool_stats(test_engine.pool)

        assert len(monitor.pool_stats_history) <= 10

    def test_get_pool_stats(self, test_engine):
        """Test getting pool statistics"""
        monitor = ConnectionPoolMonitor()

        # Record some stats
        for _ in range(5):
            monitor.record_pool_stats(test_engine.pool)

        stats = monitor.get_pool_stats(test_engine.pool)

        assert "current" in stats
        assert "average_checked_out" in stats
        assert "average_overflow" in stats
        assert "history_size" in stats

    def test_get_history(self, test_engine):
        """Test retrieving history"""
        monitor = ConnectionPoolMonitor()

        for _ in range(20):
            monitor.record_pool_stats(test_engine.pool)

        history = monitor.get_history(limit=10)
        assert len(history) == 10


# Tests for IndexAnalyzer
class TestIndexAnalyzer:
    """Test index analysis"""

    def test_get_table_indexes(self, test_db):
        """Test getting table indexes"""
        indexes = IndexAnalyzer.get_table_indexes(test_db, "movies")
        assert isinstance(indexes, list)

    def test_get_all_indexes(self, test_db):
        """Test getting all indexes"""
        all_indexes = IndexAnalyzer.get_all_indexes(test_db)
        assert isinstance(all_indexes, dict)
        assert len(all_indexes) > 0

    def test_recommend_indexes(self, test_db):
        """Test index recommendations"""
        recommendations = IndexAnalyzer.recommend_indexes(test_db)

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

        # Check that recommendations have required fields
        for rec in recommendations:
            assert "table" in rec
            assert "columns" in rec
            assert "reason" in rec
            assert "priority" in rec


# Tests for QueryExecutionPlanAnalyzer
class TestQueryExecutionPlanAnalyzer:
    """Test query execution plan analysis"""

    def test_analyze_slow_query(self, test_db):
        """Test analyzing a slow query"""
        query = "SELECT * FROM movies WHERE title LIKE '%test%'"
        analysis = QueryExecutionPlanAnalyzer.analyze_slow_query(test_db, query)

        assert "query" in analysis
        assert "execution_plan" in analysis
        assert "suggestions" in analysis
        assert isinstance(analysis["suggestions"], list)

    def test_query_optimization_suggestions(self, test_db):
        """Test query optimization suggestions"""
        # Test SELECT * suggestion
        query = "SELECT * FROM movies"
        analysis = QueryExecutionPlanAnalyzer.analyze_slow_query(test_db, query)
        assert any("SELECT *" in s for s in analysis["suggestions"])

        # Test LIKE suggestion
        query = "SELECT title FROM movies WHERE title LIKE '%test%'"
        analysis = QueryExecutionPlanAnalyzer.analyze_slow_query(test_db, query)
        assert any("LIKE" in s for s in analysis["suggestions"])

    def test_explain_query_postgresql(self, test_db):
        """Test explaining a query on PostgreSQL"""
        query = "SELECT * FROM movies WHERE title = 'Test'"
        plan = QueryExecutionPlanAnalyzer.explain_query(test_db, query)

        assert "dialect" in plan
        assert plan["dialect"] == "postgresql"


# Tests for DatabaseOptimizationService
class TestDatabaseOptimizationService:
    """Test database optimization service"""

    def test_singleton_instance(self):
        """Test singleton pattern"""
        service1 = DatabaseOptimizationService.get_instance()
        service2 = DatabaseOptimizationService.get_instance()

        assert service1 is service2

    def test_get_query_tracker(self):
        """Test getting query tracker"""
        tracker = DatabaseOptimizationService.get_query_tracker()
        assert isinstance(tracker, QueryPerformanceTracker)

    def test_get_pool_monitor(self):
        """Test getting pool monitor"""
        monitor = DatabaseOptimizationService.get_pool_monitor()
        assert isinstance(monitor, ConnectionPoolMonitor)

    def test_setup_query_logging(self, test_engine):
        """Test setting up query logging"""
        # This should not raise an exception
        DatabaseOptimizationService.setup_query_logging(test_engine)

    def test_setup_pool_monitoring(self, test_engine):
        """Test setting up pool monitoring"""
        # This should not raise an exception
        DatabaseOptimizationService.setup_pool_monitoring(test_engine)

    def test_get_optimization_report(self, test_db, test_engine):
        """Test generating optimization report"""
        report = DatabaseOptimizationService.get_optimization_report(test_db, test_engine)

        assert "timestamp" in report
        assert "query_performance" in report
        assert "slow_queries" in report
        assert "connection_pool" in report
        assert "index_recommendations" in report
        assert "all_indexes" in report


# Integration tests
class TestDatabaseOptimizationIntegration:
    """Integration tests for database optimization"""

    def test_query_tracking_with_database_operations(self, test_db, sample_movies):
        """Test query tracking with actual database operations"""
        tracker = DatabaseOptimizationService.get_query_tracker()
        _ = tracker.total_queries

        # Perform a query
        movies = test_db.query(Movie).filter(Movie.year == 2020).all()

        assert len(movies) > 0

    def test_slow_query_detection_with_complex_query(self, test_db, sample_movies):
        """Test slow query detection with complex queries"""
        tracker = DatabaseOptimizationService.get_query_tracker()

        # Simulate a slow query
        tracker.record_query(
            "SELECT m.*, COUNT(f.id) FROM movies m"
            " LEFT JOIN movie_files f ON m.id = f.movie_id GROUP BY m.id",
            2.5,
        )

        slow_queries = tracker.get_slow_queries()
        assert len(slow_queries) > 0

    def test_index_recommendations_for_search(self, test_db):
        """Test index recommendations for search operations"""
        recommendations = IndexAnalyzer.recommend_indexes(test_db)

        # Check that search-related indexes are recommended
        search_recommendations = [r for r in recommendations if "search" in r["reason"].lower()]
        assert len(search_recommendations) > 0

    def test_index_recommendations_for_filtering(self, test_db):
        """Test index recommendations for filtering operations"""
        recommendations = IndexAnalyzer.recommend_indexes(test_db)

        # Check that filter-related indexes are recommended
        filter_recommendations = [r for r in recommendations if "filter" in r["reason"].lower()]
        assert len(filter_recommendations) > 0

    def test_composite_index_recommendations(self, test_db):
        """Test composite index recommendations"""
        recommendations = IndexAnalyzer.recommend_indexes(test_db)

        # Check that composite indexes are recommended
        composite_recommendations = [r for r in recommendations if r.get("composite", False)]
        assert len(composite_recommendations) > 0


# Performance tests
class TestDatabaseOptimizationPerformance:
    """Performance tests for database optimization"""

    def test_query_tracker_performance(self):
        """Test query tracker performance with many queries"""
        tracker = QueryPerformanceTracker()

        start_time = time.time()

        for i in range(1000):
            tracker.record_query(f"SELECT * FROM movies WHERE id = {i}", 0.001)

        elapsed_time = time.time() - start_time

        # Should complete in reasonable time (< 1 second)
        assert elapsed_time < 1.0
        assert tracker.total_queries == 1000

    def test_pool_monitor_performance(self, test_engine):
        """Test pool monitor performance with many recordings"""
        monitor = ConnectionPoolMonitor()

        start_time = time.time()

        for _ in range(1000):
            monitor.record_pool_stats(test_engine.pool)

        elapsed_time = time.time() - start_time

        # Should complete in reasonable time (< 1 second)
        assert elapsed_time < 1.0
        assert len(monitor.pool_stats_history) <= monitor.max_history


# Configuration tests
class TestDatabaseOptimizationConfiguration:
    """Test database optimization configuration"""

    def test_config_pool_settings(self):
        """Test pool configuration settings"""
        assert hasattr(settings, "db_pool_size")
        assert hasattr(settings, "db_max_overflow")
        assert hasattr(settings, "db_pool_recycle")
        assert hasattr(settings, "db_pool_timeout")
        assert hasattr(settings, "db_pool_pre_ping")

    def test_config_query_settings(self):
        """Test query configuration settings"""
        assert hasattr(settings, "db_slow_query_threshold")
        assert hasattr(settings, "db_query_logging_enabled")

    def test_pool_size_configuration(self):
        """Test pool size configuration"""
        assert settings.db_pool_size > 0
        assert settings.db_max_overflow >= 0

    def test_slow_query_threshold_configuration(self):
        """Test slow query threshold configuration"""
        assert settings.db_slow_query_threshold > 0
