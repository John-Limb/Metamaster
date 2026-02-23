"""Celery tasks module - re-exports task functions from app.tasks module"""

# Import from the tasks module (not from this package)
# This avoids circular imports by importing from the parent module
from importlib import util
from pathlib import Path

from app.tasks.celery_app import celery_app
from app.core.database import SessionLocal
from app.infrastructure.file_system.ffprobe_wrapper import FFProbeWrapper
from app.tasks.enrichment import (
    enrich_movie_external,
    enrich_tv_show_external,
    retry_failed_enrichment,
)
from app.core.logging_config import get_logger as _get_logger

_logger = _get_logger(__name__)

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


@celery_app.task(bind=True, max_retries=0)
def enrich_file_technical_metadata(self, batch_size: int = 50):
    """Populate duration_seconds, video_codec, video_width, video_height on FileItems.

    Processes files with null duration_seconds in batches. Chains itself
    if more files remain after this batch.

    Args:
        batch_size: Maximum number of files to process in this invocation.
    """
    from app.domain.files.models import FileItem

    db = SessionLocal()
    try:
        files = (
            db.query(FileItem)
            .filter(
                FileItem.type == "file",
                FileItem.duration_seconds.is_(None),
            )
            .limit(batch_size)
            .all()
        )

        if not files:
            _logger.info("enrich_file_technical_metadata: no files pending — done")
            return {"status": "complete", "processed": 0}

        ffprobe = FFProbeWrapper()
        processed = 0

        for file_item in files:
            try:
                duration = ffprobe.get_duration(file_item.path)
                codecs = ffprobe.get_codecs(file_item.path)
                resolution = ffprobe.get_resolution(file_item.path)

                file_item.duration_seconds = int(duration) if duration > 0 else None
                file_item.video_codec = codecs.get("video") if "error" not in codecs else None
                file_item.video_width = (
                    resolution.get("width") if "error" not in resolution else None
                )
                file_item.video_height = (
                    resolution.get("height") if "error" not in resolution else None
                )
                processed += 1
            except Exception as exc:
                _logger.warning(
                    f"enrich_file_technical_metadata: skipping {file_item.path}: {exc}"
                )

        db.commit()

        # Check for remaining files and chain next batch
        remaining = (
            db.query(FileItem)
            .filter(FileItem.type == "file", FileItem.duration_seconds.is_(None))
            .count()
        )

        if remaining > 0:
            _logger.info(
                f"enrich_file_technical_metadata: {remaining} files remain, chaining next batch"
            )
            enrich_file_technical_metadata.delay(batch_size=batch_size)

        return {"status": "success", "processed": processed, "remaining": remaining}
    finally:
        db.close()

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
    "enrich_file_technical_metadata",
    "retry_failed_enrichment",
    "enrich_movie_external",
    "enrich_tv_show_external",
]

# Celery task aliases — only register Celery task objects (not plain helper functions)
_celery_task_aliases = [
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
    "retry_failed_enrichment",
]

# Restore the original Celery task names so existing beat schedules and callers keep working
for _alias in _celery_task_aliases:
    _register_task_alias(globals()[_alias], _alias)

del _alias
