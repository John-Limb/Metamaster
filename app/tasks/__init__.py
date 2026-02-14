"""Celery tasks module - re-exports task functions from app.tasks module"""

# Import from the tasks module (not from this package)
# This avoids circular imports by importing from the parent module
import sys
from pathlib import Path
from importlib import util

from app.tasks.celery_app import celery_app

# Get the parent directory (app/)
app_dir = Path(__file__).parent.parent

# Import the tasks module directly while keeping it separate from the package
spec = util.spec_from_file_location("app_tasks_module", app_dir / "tasks.py")
tasks_module = util.module_from_spec(spec)
spec.loader.exec_module(tasks_module)


def _register_task_alias(task, alias):
    """Ensure Celery exposes a stable app.tasks.<alias> name."""

    desired_name = f"app.tasks.{alias}"
    current_name = getattr(task, "name", None)

    if current_name == desired_name:
        return

    # Remove the auto-registered entry that uses the synthetic module name
    if current_name in celery_app.tasks:
        celery_app.tasks.pop(current_name)

    task.name = desired_name
    celery_app.tasks[desired_name] = task


# Re-export the task functions
analyze_file = tasks_module.analyze_file
enrich_metadata = tasks_module.enrich_metadata
cleanup_cache = tasks_module.cleanup_cache
cleanup_queue = tasks_module.cleanup_queue
sync_metadata = tasks_module.sync_metadata
bulk_metadata_sync_task = tasks_module.bulk_metadata_sync_task
bulk_file_import_task = tasks_module.bulk_file_import_task
process_batch_item = tasks_module.process_batch_item
update_batch_progress = tasks_module.update_batch_progress
scan_new_media = tasks_module.scan_new_media
check_and_run_scan = tasks_module.check_and_run_scan

__all__ = [
    "analyze_file",
    "enrich_metadata",
    "cleanup_cache",
    "cleanup_queue",
    "sync_metadata",
    "bulk_metadata_sync_task",
    "bulk_file_import_task",
    "process_batch_item",
    "update_batch_progress",
    "scan_new_media",
    "check_and_run_scan",
]


# Restore the original Celery task names so existing beat schedules and callers keep working
for _alias in __all__:
    _register_task_alias(globals()[_alias], _alias)

del _alias
