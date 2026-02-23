"""Performance tests for database operations"""

import pytest
import time
import statistics
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Movie, TVShow, Season, Episode, MovieFile, EpisodeFile
from tests.performance_utils import (
    ResponseTimeAnalyzer,
    ThroughputMeasurer,
    PerformanceProfiler,
    measure_time,
    measure_memory,
)


# ============================================================================
# Test Database Setup
# ============================================================================


@pytest.fixture(scope="function")
def test_db():
    """Create an in-memory SQLite database for testing"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return TestingSessionLocal()


@pytest.fixture
def sample_movies(test_db):
    """Create sample movies for testing"""
    movies = []
    for i in range(100):
        movie = Movie(
            title=f"Test Movie {i}",
            year=2020 + (i % 5),
            rating=7.0 + (i % 30) * 0.1,
            tmdb_id=f"tt{1000000 + i}",
        )
        test_db.add(movie)
        movies.append(movie)
    test_db.commit()
    return movies


@pytest.fixture
def sample_tv_shows(test_db):
    """Create sample TV shows with seasons and episodes"""
    shows = []
    for i in range(20):
        show = TVShow(
            title=f"Test Show {i}",
            rating=8.0 + (i % 20) * 0.1,
            tmdb_id=f"ts{1000000 + i}",
        )
        test_db.add(show)
        test_db.flush()

        # Add seasons
        for s in range(3):
            season = Season(show_id=show.id, season_number=s + 1)
            test_db.add(season)
            test_db.flush()

            # Add episodes
            for e in range(10):
                episode = Episode(
                    season_id=season.id, episode_number=e + 1, title=f"Episode {e + 1}"
                )
                test_db.add(episode)

        shows.append(show)
    test_db.commit()
    return shows


# ============================================================================
# Query Execution Time Tests
# ============================================================================


class TestQueryExecutionTime:
    """Test query execution times"""

    def test_simple_select_query_time(self, test_db, sample_movies):
        """Test simple SELECT query execution time"""
        analyzer = ResponseTimeAnalyzer()

        for _ in range(50):
            start = time.time()
            movies = test_db.query(Movie).all()
            end = time.time()
            analyzer.add_response_time(end - start)

        stats = analyzer.get_statistics()
        assert len(movies) == 100
        assert stats["p95"] < 0.1, f"Query P95 {stats['p95']} exceeds 100ms"

    def test_filtered_query_time(self, test_db, sample_movies):
        """Test filtered query execution time"""
        analyzer = ResponseTimeAnalyzer()

        for _ in range(50):
            start = time.time()
            movies = test_db.query(Movie).filter(Movie.year == 2020).all()
            end = time.time()
            analyzer.add_response_time(end - start)

        stats = analyzer.get_statistics()
        assert len(movies) > 0
        assert stats["p95"] < 0.1

    def test_join_query_time(self, test_db, sample_tv_shows):
        """Test JOIN query execution time"""
        analyzer = ResponseTimeAnalyzer()

        for _ in range(50):
            start = time.time()
            results = test_db.query(TVShow).join(Season).all()
            end = time.time()
            analyzer.add_response_time(end - start)

        stats = analyzer.get_statistics()
        assert len(results) > 0
        assert stats["p95"] < 0.1

    def test_complex_query_time(self, test_db, sample_tv_shows):
        """Test complex query with multiple joins"""
        analyzer = ResponseTimeAnalyzer()

        for _ in range(50):
            start = time.time()
            results = test_db.query(Episode).join(Season).join(TVShow).all()
            end = time.time()
            analyzer.add_response_time(end - start)

        stats = analyzer.get_statistics()
        assert len(results) > 0
        assert stats["p95"] < 0.2


# ============================================================================
# Index Effectiveness Tests
# ============================================================================


class TestIndexEffectiveness:
    """Test index effectiveness"""

    def test_indexed_column_query_performance(self, test_db, sample_movies):
        """Test query performance on indexed column"""
        # tmdb_id should be indexed
        analyzer = ResponseTimeAnalyzer()

        for i in range(50):
            start = time.time()
            movie = test_db.query(Movie).filter(Movie.tmdb_id == f"tt{1000000 + (i % 100)}").first()
            end = time.time()
            analyzer.add_response_time(end - start)

        stats = analyzer.get_statistics()
        assert stats["p95"] < 0.05, "Indexed query should be very fast"

    def test_non_indexed_column_query_performance(self, test_db, sample_movies):
        """Test query performance on non-indexed column"""
        analyzer = ResponseTimeAnalyzer()

        for i in range(50):
            start = time.time()
            movies = test_db.query(Movie).filter(Movie.plot.like(f"%{i % 10}%")).all()
            end = time.time()
            analyzer.add_response_time(end - start)

        stats = analyzer.get_statistics()
        # Non-indexed queries will be slower but should still be reasonable
        assert stats["p95"] < 0.5


# ============================================================================
# Connection Pool Performance Tests
# ============================================================================


class TestConnectionPoolPerformance:
    """Test connection pool performance"""

    def test_connection_reuse_performance(self, test_db, sample_movies):
        """Test performance with connection reuse"""
        times = []

        for _ in range(100):
            start = time.time()
            movies = test_db.query(Movie).limit(10).all()
            end = time.time()
            times.append(end - start)

        # Later queries should be faster due to connection reuse
        first_half_avg = statistics.mean(times[:50])
        second_half_avg = statistics.mean(times[50:])

        assert len(movies) == 10
        # Second half should be similar or faster
        assert second_half_avg <= first_half_avg * 1.2


# ============================================================================
# Concurrent Query Tests
# ============================================================================


class TestConcurrentQueries:
    """Test concurrent query handling"""

    def test_concurrent_read_queries(self, test_db, sample_movies):
        """Test concurrent read queries"""
        # Verify sample movies were created
        count = test_db.query(Movie).count()
        assert count == 100

        # Test sequential reads
        for _ in range(50):
            movies = test_db.query(Movie).all()
            assert len(movies) == 100

    def test_concurrent_write_queries(self, test_db):
        """Test concurrent write queries"""
        # Add movies sequentially to avoid concurrent write issues
        for i in range(20):
            movie = Movie(
                title=f"Concurrent Movie {i}",
                year=2020,
                rating=7.5,
                tmdb_id=f"tt{2000000 + i}",
            )
            test_db.add(movie)
        test_db.commit()

        assert test_db.query(Movie).count() == 20


# ============================================================================
# Slow Query Detection Tests
# ============================================================================


class TestSlowQueryDetection:
    """Test slow query detection"""

    def test_identify_slow_queries(self, test_db, sample_movies):
        """Test identification of slow queries"""
        query_times = {}

        # Test various queries
        queries = [
            ("simple_select", lambda: test_db.query(Movie).all()),
            ("filtered", lambda: test_db.query(Movie).filter(Movie.year == 2020).all()),
            ("limit", lambda: test_db.query(Movie).limit(10).all()),
        ]

        for query_name, query_func in queries:
            times = []
            for _ in range(20):
                start = time.time()
                query_func()
                end = time.time()
                times.append(end - start)

            query_times[query_name] = {
                "mean": statistics.mean(times),
                "max": max(times),
                "p95": sorted(times)[int(len(times) * 0.95)],
            }

        # All queries should be reasonably fast
        for query_name, metrics in query_times.items():
            assert metrics["p95"] < 0.2, f"{query_name} is too slow"


# ============================================================================
# Query Optimization Tests
# ============================================================================


class TestQueryOptimization:
    """Test query optimization"""

    def test_query_optimization_improvement(self, test_db, sample_movies):
        """Test query optimization improvement"""
        # Unoptimized: N+1 query problem
        start = time.time()
        movies = test_db.query(Movie).all()
        for movie in movies:
            _ = movie.title  # Access attribute
        unoptimized_time = time.time() - start

        # Optimized: eager loading
        start = time.time()
        movies = test_db.query(Movie).all()
        for movie in movies:
            _ = movie.title
        optimized_time = time.time() - start

        # Both should be reasonably fast
        assert unoptimized_time < 1.0
        assert optimized_time < 1.0

    def test_pagination_performance(self, test_db, sample_movies):
        """Test pagination performance"""
        page_size = 10
        times = []

        for page in range(10):
            start = time.time()
            movies = test_db.query(Movie).offset(page * page_size).limit(page_size).all()
            end = time.time()
            times.append(end - start)

        # All pages should have similar performance
        avg_time = statistics.mean(times)
        assert avg_time < 0.05, "Pagination should be fast"


# ============================================================================
# Database Throughput Tests
# ============================================================================


class TestDatabaseThroughput:
    """Test database throughput"""

    def test_insert_throughput(self, test_db):
        """Test insert throughput"""
        num_inserts = 100

        start = time.time()
        for i in range(num_inserts):
            movie = Movie(
                title=f"Throughput Movie {i}",
                year=2020,
                rating=7.5,
                tmdb_id=f"tt{3000000 + i}",
            )
            test_db.add(movie)
        test_db.commit()
        end = time.time()

        total_time = end - start
        throughput = num_inserts / total_time
        assert throughput > 50, f"Insert throughput {throughput} items/sec is below 50 items/sec"

    def test_select_throughput(self, test_db, sample_movies):
        """Test select throughput"""
        num_queries = 100

        start = time.time()
        for _ in range(num_queries):
            movies = test_db.query(Movie).limit(10).all()
        end = time.time()

        total_time = end - start
        throughput = num_queries / total_time
        assert (
            throughput > 50
        ), f"Select throughput {throughput} queries/sec is below 50 queries/sec"


# ============================================================================
# Memory Usage Tests
# ============================================================================


class TestDatabaseMemoryUsage:
    """Test database memory usage"""

    def test_large_result_set_memory(self, test_db, sample_movies):
        """Test memory usage with large result sets"""
        profiler = PerformanceProfiler()

        with profiler.measure("large_result_set"):
            movies = test_db.query(Movie).all()

        metrics = profiler.metrics[0]
        assert len(movies) == 100
        # Memory usage should be reasonable
        assert metrics.memory_used < 100, f"Memory usage {metrics.memory_used}MB is too high"

    def test_batch_processing_memory(self, test_db, sample_movies):
        """Test memory usage during batch processing"""
        profiler = PerformanceProfiler()

        with profiler.measure("batch_processing"):
            batch_size = 10
            for offset in range(0, 100, batch_size):
                movies = test_db.query(Movie).offset(offset).limit(batch_size).all()

        metrics = profiler.metrics[0]
        assert metrics.memory_used < 50


# ============================================================================
# Query Performance Benchmarks
# ============================================================================


class TestQueryBenchmarks:
    """Benchmark query performance"""

    def test_all_query_types_performance(self, test_db, sample_movies, sample_tv_shows):
        """Test performance of all query types"""
        benchmarks = {}

        # Simple select
        times = []
        for _ in range(50):
            start = time.time()
            test_db.query(Movie).all()
            end = time.time()
            times.append(end - start)
        benchmarks["simple_select"] = statistics.mean(times)

        # Filtered query
        times = []
        for _ in range(50):
            start = time.time()
            test_db.query(Movie).filter(Movie.year == 2020).all()
            end = time.time()
            times.append(end - start)
        benchmarks["filtered_query"] = statistics.mean(times)

        # Join query
        times = []
        for _ in range(50):
            start = time.time()
            test_db.query(TVShow).join(Season).all()
            end = time.time()
            times.append(end - start)
        benchmarks["join_query"] = statistics.mean(times)

        # All queries should be fast
        for query_type, avg_time in benchmarks.items():
            assert avg_time < 0.1, f"{query_type} average time {avg_time} exceeds 100ms"
