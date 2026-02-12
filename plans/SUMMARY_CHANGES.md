### Summary of Key Fixes

- **Celery task names restored:** `app/tasks/__init__.py` now assigns legacy `app.tasks.*` names to each task so existing beat schedules (see [`app/tasks/celery_beat.py`](app/tasks/celery_beat.py:1)) and external callers keep working despite the module refactor.
- **Backward-compatibility shims:** Added [`app/config.py`](app/config.py:1) and [`app/database.py`](app/database.py:1) to re-export the relocated settings and database utilities, keeping the large test suite and tooling unblocked.
