"""Database optimization utilities for performance analysis and monitoring"""

import logging
import time
from typing import Dict, List, Any
from datetime import datetime
from sqlalchemy import text, event, inspect
from sqlalchemy.orm import Session
from sqlalchemy.pool import Pool

logger = logging.getLogger(__name__)


class QueryPerformanceTracker:
    """Track and analyze query performance metrics"""

    def __init__(self, slow_query_threshold: float = 1.0):
        """
        Initialize query performance tracker.

        Args:
            slow_query_threshold: Time in seconds to consider a query as slow
        """
        self.slow_query_threshold = slow_query_threshold
        self.slow_queries: List[Dict[str, Any]] = []
        self.query_stats: Dict[str, Dict[str, Any]] = {}
        self.total_queries = 0
        self.total_time = 0.0

    def record_query(self, query: str, execution_time: float, success: bool = True):
        """
        Record a query execution.

        Args:
            query: SQL query string
            execution_time: Time taken to execute in seconds
            success: Whether query executed successfully
        """
        self.total_queries += 1
        self.total_time += execution_time

        # Normalize query for grouping
        normalized_query = self._normalize_query(query)

        if normalized_query not in self.query_stats:
            self.query_stats[normalized_query] = {
                "count": 0,
                "total_time": 0.0,
                "min_time": float("inf"),
                "max_time": 0.0,
                "avg_time": 0.0,
                "last_executed": None,
            }

        stats = self.query_stats[normalized_query]
        stats["count"] += 1
        stats["total_time"] += execution_time
        stats["min_time"] = min(stats["min_time"], execution_time)
        stats["max_time"] = max(stats["max_time"], execution_time)
        stats["avg_time"] = stats["total_time"] / stats["count"]
        stats["last_executed"] = datetime.utcnow()

        # Track slow queries
        if execution_time > self.slow_query_threshold:
            self.slow_queries.append(
                {
                    "query": query,
                    "execution_time": execution_time,
                    "timestamp": datetime.utcnow(),
                    "success": success,
                }
            )

            # Keep only last 100 slow queries
            if len(self.slow_queries) > 100:
                self.slow_queries = self.slow_queries[-100:]

            logger.warning(
                f"Slow query detected ({execution_time:.3f}s): {query[:100]}..."
            )

    def get_slow_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the most recent slow queries"""
        return self.slow_queries[-limit:]

    def get_query_stats(self) -> Dict[str, Any]:
        """Get overall query statistics"""
        return {
            "total_queries": self.total_queries,
            "total_time": self.total_time,
            "avg_time": (
                self.total_time / self.total_queries if self.total_queries > 0 else 0
            ),
            "query_stats": self.query_stats,
            "slow_query_count": len(self.slow_queries),
        }

    def reset(self):
        """Reset all statistics"""
        self.slow_queries = []
        self.query_stats = {}
        self.total_queries = 0
        self.total_time = 0.0

    @staticmethod
    def _normalize_query(query: str) -> str:
        """Normalize query for grouping similar queries"""
        # Remove parameter values and normalize whitespace
        import re

        normalized = re.sub(r"\?", "?", query)
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized.strip()[:200]  # Keep first 200 chars


class ConnectionPoolMonitor:
    """Monitor database connection pool statistics"""

    def __init__(self):
        """Initialize connection pool monitor"""
        self.pool_stats_history: List[Dict[str, Any]] = []
        self.max_history = 1000

    def record_pool_stats(self, pool: Pool):
        """
        Record current connection pool statistics.

        Args:
            pool: SQLAlchemy connection pool
        """
        try:
            stats = {
                "timestamp": datetime.utcnow(),
                "pool_size": pool.size() if hasattr(pool, "size") else None,
                "checked_out": (
                    pool.checkedout() if hasattr(pool, "checkedout") else None
                ),
                "overflow": pool.overflow() if hasattr(pool, "overflow") else None,
                "total_connections": (
                    pool.size() + pool.overflow()
                    if hasattr(pool, "size") and hasattr(pool, "overflow")
                    else None
                ),
            }

            self.pool_stats_history.append(stats)

            # Keep only last N records
            if len(self.pool_stats_history) > self.max_history:
                self.pool_stats_history = self.pool_stats_history[-self.max_history :]

            return stats
        except Exception as e:
            logger.error(f"Error recording pool stats: {e}")
            return None

    def get_pool_stats(self, pool: Pool) -> Dict[str, Any]:
        """Get current connection pool statistics"""
        try:
            current_stats = self.record_pool_stats(pool)

            if not current_stats:
                return {}

            # Calculate averages from history
            if self.pool_stats_history:
                checked_out_values = [
                    s["checked_out"]
                    for s in self.pool_stats_history
                    if s["checked_out"] is not None
                ]
                overflow_values = [
                    s["overflow"]
                    for s in self.pool_stats_history
                    if s["overflow"] is not None
                ]

                avg_checked_out = (
                    sum(checked_out_values) / len(checked_out_values)
                    if checked_out_values
                    else 0
                )
                avg_overflow = (
                    sum(overflow_values) / len(overflow_values)
                    if overflow_values
                    else 0
                )
            else:
                avg_checked_out = 0
                avg_overflow = 0

            return {
                "current": current_stats,
                "average_checked_out": avg_checked_out,
                "average_overflow": avg_overflow,
                "history_size": len(self.pool_stats_history),
            }
        except Exception as e:
            logger.error(f"Error getting pool stats: {e}")
            return {}

    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get pool statistics history"""
        return self.pool_stats_history[-limit:]


class IndexAnalyzer:
    """Analyze and recommend database indexes"""

    @staticmethod
    def get_table_indexes(db: Session, table_name: str) -> List[Dict[str, Any]]:
        """
        Get all indexes for a table.

        Args:
            db: Database session
            table_name: Name of the table

        Returns:
            List of index information
        """
        try:
            inspector = inspect(db.bind)
            indexes = inspector.get_indexes(table_name)
            return indexes
        except Exception as e:
            logger.error(f"Error getting indexes for table {table_name}: {e}")
            return []

    @staticmethod
    def get_all_indexes(db: Session) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all indexes for all tables.

        Args:
            db: Database session

        Returns:
            Dictionary mapping table names to their indexes
        """
        try:
            inspector = inspect(db.bind)
            tables = inspector.get_table_names()

            all_indexes = {}
            for table in tables:
                all_indexes[table] = inspector.get_indexes(table)

            return all_indexes
        except Exception as e:
            logger.error(f"Error getting all indexes: {e}")
            return {}

    @staticmethod
    def recommend_indexes(db: Session) -> List[Dict[str, Any]]:
        """
        Recommend indexes based on common query patterns.

        Args:
            db: Database session

        Returns:
            List of index recommendations
        """
        recommendations = []

        # Recommend indexes for frequently searched/filtered columns
        recommendations.extend(
            [
                {
                    "table": "movies",
                    "columns": ["title"],
                    "reason": "Frequently used in search queries",
                    "priority": "high",
                },
                {
                    "table": "movies",
                    "columns": ["genre"],
                    "reason": "Frequently used for filtering",
                    "priority": "high",
                },
                {
                    "table": "movies",
                    "columns": ["rating"],
                    "reason": "Frequently used for filtering",
                    "priority": "medium",
                },
                {
                    "table": "movies",
                    "columns": ["year"],
                    "reason": "Frequently used for filtering",
                    "priority": "medium",
                },
                {
                    "table": "tv_shows",
                    "columns": ["title"],
                    "reason": "Frequently used in search queries",
                    "priority": "high",
                },
                {
                    "table": "tv_shows",
                    "columns": ["genre"],
                    "reason": "Frequently used for filtering",
                    "priority": "high",
                },
                {
                    "table": "tv_shows",
                    "columns": ["rating"],
                    "reason": "Frequently used for filtering",
                    "priority": "medium",
                },
                {
                    "table": "tv_shows",
                    "columns": ["status"],
                    "reason": "Frequently used for filtering",
                    "priority": "medium",
                },
                {
                    "table": "movies",
                    "columns": ["title", "year"],
                    "reason": "Common filter combination",
                    "priority": "medium",
                    "composite": True,
                },
                {
                    "table": "tv_shows",
                    "columns": ["title", "status"],
                    "reason": "Common filter combination",
                    "priority": "medium",
                    "composite": True,
                },
            ]
        )

        return recommendations


class QueryExecutionPlanAnalyzer:
    """Analyze query execution plans"""

    @staticmethod
    def explain_query(db: Session, query: str) -> Dict[str, Any]:
        """
        Get execution plan for a query.

        Args:
            db: Database session
            query: SQL query to analyze

        Returns:
            Execution plan information
        """
        try:
            # For SQLite
            if db.bind.dialect.name == "sqlite":
                result = db.execute(text(f"EXPLAIN QUERY PLAN {query}")).fetchall()
                return {
                    "dialect": "sqlite",
                    "plan": [dict(row._mapping) for row in result],
                }

            # For PostgreSQL
            elif db.bind.dialect.name == "postgresql":
                result = db.execute(text(f"EXPLAIN {query}")).fetchall()
                return {
                    "dialect": "postgresql",
                    "plan": [row[0] for row in result],
                }

            else:
                return {
                    "error": f"Execution plan analysis not supported for {db.bind.dialect.name}"
                }
        except Exception as e:
            logger.error(f"Error analyzing query execution plan: {e}")
            return {"error": str(e)}

    @staticmethod
    def analyze_slow_query(db: Session, query: str) -> Dict[str, Any]:
        """
        Analyze a slow query and provide optimization suggestions.

        Args:
            db: Database session
            query: SQL query to analyze

        Returns:
            Analysis and suggestions
        """
        analysis = {
            "query": query,
            "execution_plan": QueryExecutionPlanAnalyzer.explain_query(db, query),
            "suggestions": [],
        }

        # Add suggestions based on query patterns
        if "SELECT *" in query.upper():
            analysis["suggestions"].append(
                "Consider selecting only needed columns instead of SELECT *"
            )

        if "LIKE" in query.upper() and "%" in query:
            analysis["suggestions"].append(
                "LIKE queries with leading wildcards cannot use indexes efficiently"
            )

        if "OR" in query.upper():
            analysis["suggestions"].append(
                "Consider using IN clause instead of multiple OR conditions"
            )

        if "NOT IN" in query.upper():
            analysis["suggestions"].append(
                "Consider using LEFT JOIN with NULL check instead of NOT IN"
            )

        return analysis


class DatabaseOptimizationService:
    """Main service for database optimization"""

    _instance = None
    _query_tracker = None
    _pool_monitor = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._query_tracker = QueryPerformanceTracker()
            cls._pool_monitor = ConnectionPoolMonitor()
        return cls._instance

    @classmethod
    def get_instance(cls) -> "DatabaseOptimizationService":
        """Get singleton instance"""
        return cls()

    @classmethod
    def get_query_tracker(cls) -> QueryPerformanceTracker:
        """Get query performance tracker"""
        # Ensure singleton is initialized before returning tracker
        if cls._query_tracker is None:
            cls()
        return cls._query_tracker

    @classmethod
    def get_pool_monitor(cls) -> ConnectionPoolMonitor:
        """Get connection pool monitor"""
        # Ensure singleton is initialized before returning monitor
        if cls._pool_monitor is None:
            cls()
        return cls._pool_monitor

    @staticmethod
    def setup_query_logging(engine):
        """
        Setup query logging for the engine.

        Args:
            engine: SQLAlchemy engine
        """
        tracker = DatabaseOptimizationService.get_query_tracker()

        # Add null check with logging
        if tracker is None:
            logger.warning("Query tracker is None, skipping query logging setup")
            return

        @event.listens_for(engine, "before_cursor_execute")
        def receive_before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            conn.info.setdefault("query_start_time", []).append(time.time())

        @event.listens_for(engine, "after_cursor_execute")
        def receive_after_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            total_time = time.time() - conn.info["query_start_time"].pop(-1)
            # Get fresh tracker reference in case it was reinitialized
            current_tracker = DatabaseOptimizationService.get_query_tracker()
            if current_tracker is not None:
                current_tracker.record_query(statement, total_time)

    @staticmethod
    def setup_pool_monitoring(engine):
        """
        Setup connection pool monitoring for the engine.

        Args:
            engine: SQLAlchemy engine
        """
        monitor = DatabaseOptimizationService.get_pool_monitor()

        # Add null check with logging
        if monitor is None:
            logger.warning("Pool monitor is None, skipping pool monitoring setup")
            return

        @event.listens_for(engine.pool.__class__, "connect", propagate=True)
        def receive_connect(dbapi_conn, connection_record):
            # Get fresh monitor reference in case it was reinitialized
            current_monitor = DatabaseOptimizationService.get_pool_monitor()
            if current_monitor is not None:
                current_monitor.record_pool_stats(engine.pool)

        @event.listens_for(engine.pool.__class__, "checkout", propagate=True)
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            # Get fresh monitor reference in case it was reinitialized
            current_monitor = DatabaseOptimizationService.get_pool_monitor()
            if current_monitor is not None:
                current_monitor.record_pool_stats(engine.pool)

        @event.listens_for(engine.pool.__class__, "checkin", propagate=True)
        def receive_checkin(dbapi_conn, connection_record):
            # Get fresh monitor reference in case it was reinitialized
            current_monitor = DatabaseOptimizationService.get_pool_monitor()
            if current_monitor is not None:
                current_monitor.record_pool_stats(engine.pool)

    @staticmethod
    def get_optimization_report(db: Session, engine) -> Dict[str, Any]:
        """
        Generate comprehensive optimization report.

        Args:
            db: Database session
            engine: SQLAlchemy engine

        Returns:
            Optimization report
        """
        tracker = DatabaseOptimizationService.get_query_tracker()
        monitor = DatabaseOptimizationService.get_pool_monitor()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "query_performance": tracker.get_query_stats(),
            "slow_queries": tracker.get_slow_queries(limit=10),
            "connection_pool": monitor.get_pool_stats(engine.pool),
            "index_recommendations": IndexAnalyzer.recommend_indexes(db),
            "all_indexes": IndexAnalyzer.get_all_indexes(db),
        }
