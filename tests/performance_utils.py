"""Performance testing utilities for benchmarking and profiling"""

import time
import psutil
import os
from contextlib import contextmanager
from functools import wraps
from typing import Callable, Any, Dict, List
from dataclasses import dataclass, field
from datetime import datetime
import statistics


@dataclass
class PerformanceMetrics:
    """Container for performance metrics"""

    name: str
    execution_time: float
    memory_used: float
    cpu_percent: float
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime = field(default_factory=datetime.now)
    iterations: int = 1
    throughput: float = 0.0

    def __post_init__(self):
        if self.iterations > 0:
            self.throughput = (
                self.iterations / self.execution_time if self.execution_time > 0 else 0
            )


class PerformanceProfiler:
    """Utility for profiling performance metrics"""

    def __init__(self):
        self.metrics: List[PerformanceMetrics] = []
        self.process = psutil.Process(os.getpid())

    def get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        return self.process.memory_info().rss / 1024 / 1024

    def get_cpu_percent(self) -> float:
        """Get current CPU usage percentage"""
        return self.process.cpu_percent(interval=0.1)

    @contextmanager
    def measure(self, name: str, iterations: int = 1):
        """Context manager for measuring performance"""
        start_memory = self.get_memory_usage()
        start_cpu = self.get_cpu_percent()
        start_time = time.time()

        try:
            yield
        finally:
            end_time = time.time()
            end_memory = self.get_memory_usage()
            end_cpu = self.get_cpu_percent()

            execution_time = end_time - start_time
            memory_used = max(0, end_memory - start_memory)

            metrics = PerformanceMetrics(
                name=name,
                execution_time=execution_time,
                memory_used=memory_used,
                cpu_percent=end_cpu,
                iterations=iterations,
            )
            self.metrics.append(metrics)

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics"""
        if not self.metrics:
            return {}

        execution_times = [m.execution_time for m in self.metrics]
        memory_used = [m.memory_used for m in self.metrics]
        throughputs = [m.throughput for m in self.metrics]

        return {
            "total_measurements": len(self.metrics),
            "avg_execution_time": statistics.mean(execution_times),
            "min_execution_time": min(execution_times),
            "max_execution_time": max(execution_times),
            "avg_memory_used": statistics.mean(memory_used),
            "max_memory_used": max(memory_used),
            "avg_throughput": statistics.mean(throughputs) if throughputs else 0,
        }

    def clear(self):
        """Clear all metrics"""
        self.metrics = []


def timing_decorator(func: Callable) -> Callable:
    """Decorator to measure function execution time"""

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"{func.__name__} took {execution_time:.4f} seconds")
        return result

    return wrapper


def memory_decorator(func: Callable) -> Callable:
    """Decorator to measure function memory usage"""

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        process = psutil.Process(os.getpid())
        start_memory = process.memory_info().rss / 1024 / 1024
        result = func(*args, **kwargs)
        end_memory = process.memory_info().rss / 1024 / 1024
        memory_used = end_memory - start_memory
        print(f"{func.__name__} used {memory_used:.2f} MB")
        return result

    return wrapper


@contextmanager
def measure_time(name: str = "Operation"):
    """Context manager to measure execution time"""
    start_time = time.time()
    try:
        yield
    finally:
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"{name} took {execution_time:.4f} seconds")


@contextmanager
def measure_memory(name: str = "Operation"):
    """Context manager to measure memory usage"""
    process = psutil.Process(os.getpid())
    start_memory = process.memory_info().rss / 1024 / 1024
    try:
        yield
    finally:
        end_memory = process.memory_info().rss / 1024 / 1024
        memory_used = end_memory - start_memory
        print(f"{name} used {memory_used:.2f} MB")


@contextmanager
def measure_cpu(name: str = "Operation"):
    """Context manager to measure CPU usage"""
    process = psutil.Process(os.getpid())
    start_cpu = process.cpu_percent(interval=0.1)
    try:
        yield
    finally:
        end_cpu = process.cpu_percent(interval=0.1)
        print(f"{name} CPU usage: {end_cpu:.2f}%")


class ResponseTimeAnalyzer:
    """Analyzer for response time percentiles"""

    def __init__(self):
        self.response_times: List[float] = []

    def add_response_time(self, response_time: float):
        """Add a response time measurement"""
        self.response_times.append(response_time)

    def get_percentile(self, percentile: float) -> float:
        """Get response time at given percentile (0-100)"""
        if not self.response_times:
            return 0.0
        sorted_times = sorted(self.response_times)
        index = int((percentile / 100) * len(sorted_times))
        return sorted_times[min(index, len(sorted_times) - 1)]

    def get_statistics(self) -> Dict[str, float]:
        """Get response time statistics"""
        if not self.response_times:
            return {}

        return {
            "count": len(self.response_times),
            "min": min(self.response_times),
            "max": max(self.response_times),
            "mean": statistics.mean(self.response_times),
            "median": statistics.median(self.response_times),
            "stdev": (statistics.stdev(self.response_times) if len(self.response_times) > 1 else 0),
            "p50": self.get_percentile(50),
            "p95": self.get_percentile(95),
            "p99": self.get_percentile(99),
        }

    def clear(self):
        """Clear all response times"""
        self.response_times = []


class ThroughputMeasurer:
    """Measurer for throughput (requests/operations per second)"""

    def __init__(self):
        self.operations: List[float] = []

    def add_operation(self, duration: float):
        """Add an operation with its duration"""
        self.operations.append(duration)

    def get_throughput(self) -> float:
        """Get throughput in operations per second"""
        if not self.operations:
            return 0.0
        total_time = sum(self.operations)
        return len(self.operations) / total_time if total_time > 0 else 0.0

    def get_statistics(self) -> Dict[str, float]:
        """Get throughput statistics"""
        if not self.operations:
            return {}

        return {
            "total_operations": len(self.operations),
            "total_time": sum(self.operations),
            "throughput_ops_per_sec": self.get_throughput(),
            "avg_operation_time": statistics.mean(self.operations),
        }

    def clear(self):
        """Clear all operations"""
        self.operations = []


class CacheHitRateAnalyzer:
    """Analyzer for cache hit/miss rates"""

    def __init__(self):
        self.hits = 0
        self.misses = 0

    def record_hit(self):
        """Record a cache hit"""
        self.hits += 1

    def record_miss(self):
        """Record a cache miss"""
        self.misses += 1

    def get_hit_rate(self) -> float:
        """Get cache hit rate as percentage"""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0

    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.hits + self.misses
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total": total,
            "hit_rate": self.get_hit_rate(),
            "miss_rate": 100 - self.get_hit_rate(),
        }

    def clear(self):
        """Clear all statistics"""
        self.hits = 0
        self.misses = 0


class ConcurrencyTester:
    """Tester for concurrent operations"""

    def __init__(self):
        self.operation_times: List[float] = []
        self.errors: List[str] = []

    def add_operation_time(self, duration: float):
        """Add operation duration"""
        self.operation_times.append(duration)

    def add_error(self, error: str):
        """Add error message"""
        self.errors.append(error)

    def get_statistics(self) -> Dict[str, Any]:
        """Get concurrency statistics"""
        if not self.operation_times:
            return {}

        return {
            "total_operations": len(self.operation_times),
            "successful_operations": len(self.operation_times),
            "failed_operations": len(self.errors),
            "avg_operation_time": statistics.mean(self.operation_times),
            "min_operation_time": min(self.operation_times),
            "max_operation_time": max(self.operation_times),
            "success_rate": (
                (len(self.operation_times) / (len(self.operation_times) + len(self.errors)) * 100)
                if (len(self.operation_times) + len(self.errors)) > 0
                else 0
            ),
        }

    def clear(self):
        """Clear all statistics"""
        self.operation_times = []
        self.errors = []


class PerformanceComparator:
    """Comparator for performance metrics across runs"""

    def __init__(self):
        self.baseline: Dict[str, float] = {}
        self.current: Dict[str, float] = {}

    def set_baseline(self, metrics: Dict[str, float]):
        """Set baseline metrics"""
        self.baseline = metrics.copy()

    def set_current(self, metrics: Dict[str, float]):
        """Set current metrics"""
        self.current = metrics.copy()

    def get_improvement(self, metric_name: str) -> float:
        """Get improvement percentage for a metric (positive = improvement)"""
        if metric_name not in self.baseline or metric_name not in self.current:
            return 0.0

        baseline_value = self.baseline[metric_name]
        current_value = self.current[metric_name]

        if baseline_value == 0:
            return 0.0

        # For metrics where lower is better (time, memory)
        if "time" in metric_name.lower() or "memory" in metric_name.lower():
            return ((baseline_value - current_value) / baseline_value) * 100

        # For metrics where higher is better (throughput, hit_rate)
        return ((current_value - baseline_value) / baseline_value) * 100

    def get_comparison_report(self) -> Dict[str, Any]:
        """Get comparison report"""
        report = {}
        for metric_name in self.baseline.keys():
            if metric_name in self.current:
                improvement = self.get_improvement(metric_name)
                report[metric_name] = {
                    "baseline": self.baseline[metric_name],
                    "current": self.current[metric_name],
                    "improvement_percent": improvement,
                }
        return report
