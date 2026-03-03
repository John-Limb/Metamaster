"""Celery-friendly metrics helper functions."""

from __future__ import annotations

from prometheus_client import Counter, Histogram

task_counter = Counter(
    "celery_task_executions_total",
    "Total Celery task executions",
    ["task_name", "status"],
)

task_duration = Histogram(
    "celery_task_duration_seconds",
    "Celery task duration in seconds",
    ["task_name"],
    buckets=(0.1, 0.5, 1, 2.5, 5, 10, 30, 60, 120, 300),
)


class TaskMetricsRecorder:
    """Context manager for recording task metrics."""

    def __init__(self, task_name: str):
        self.task_name = task_name
        self._timer = None

    def __enter__(self):
        self._timer = task_duration.labels(task_name=self.task_name).time()
        self._timer.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb):
        if self._timer:
            self._timer.__exit__(exc_type, exc, tb)
        status = "error" if exc_type else "success"
        task_counter.labels(task_name=self.task_name, status=status).inc()
        return False
