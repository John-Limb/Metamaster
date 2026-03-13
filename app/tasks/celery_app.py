"""Celery application configuration and initialization"""

import logging

from celery import Celery
from celery.signals import task_failure, task_postrun, task_prerun, task_retry, task_revoked
from kombu import Exchange, Queue

from app.core.config import settings
from app.tasks.celery_beat import beat_schedule

logger = logging.getLogger(__name__)

# Create Celery app instance
celery_app = Celery(
    "media_management",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.enrichment",
        "app.tasks.plex",
    ],
)

# Configure Celery settings
celery_app.conf.update(
    # Broker and result backend
    broker_url=settings.celery_broker_url,
    result_backend=settings.celery_result_backend,
    # Task serialization
    task_serializer=settings.celery_task_serializer,
    result_serializer=settings.celery_result_serializer,
    accept_content=settings.celery_accept_content,
    # Task execution settings
    task_track_started=settings.celery_task_track_started,
    task_time_limit=settings.celery_task_time_limit,
    task_soft_time_limit=settings.celery_task_soft_time_limit,
    # Task routing
    task_routes={
        "app.tasks.process_media_file": {"queue": "media_processing"},
        "app.tasks.extract_metadata": {"queue": "metadata_extraction"},
        "app.tasks.fetch_external_data": {"queue": "external_api"},
        "app.tasks.retry_failed_enrichment": {"queue": "external_api"},
        "app.tasks.plex.*": {"queue": "external_api"},
    },
    # Queue configuration
    task_queues=(
        Queue(
            "default",
            Exchange("default", type="direct"),
            routing_key="default",
        ),
        Queue(
            "media_processing",
            Exchange("media_processing", type="direct"),
            routing_key="media_processing",
        ),
        Queue(
            "metadata_extraction",
            Exchange("metadata_extraction", type="direct"),
            routing_key="metadata_extraction",
        ),
        Queue(
            "external_api",
            Exchange("external_api", type="direct"),
            routing_key="external_api",
        ),
    ),
    # Retry configuration with exponential backoff
    task_autoretry_for=(Exception,),
    task_max_retries=3,
    task_default_retry_delay=60,  # 1 minute
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_persistent=True,
    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    # Beat schedule for periodic tasks
    beat_schedule=beat_schedule,
)


# Signal handlers for task lifecycle
@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, **kwargs):
    """Log task execution start"""
    logger.info(f"Task {task.name} (ID: {task_id}) started")


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, state=None, **kwargs):
    """Log task execution completion"""
    logger.info(f"Task {task.name} (ID: {task_id}) completed with state: {state}")


@task_failure.connect
def task_failure_handler(
    sender=None,
    task_id=None,
    exception=None,
    args=None,
    kwargs=None,
    traceback=None,
    einfo=None,
    **kw,
):
    """Handle task failure - called when a task fails after all retries"""
    try:
        from app.infrastructure.monitoring.error_handler import TaskErrorHandler

        task_name = sender.name if sender else "unknown"
        tb_str = traceback if isinstance(traceback, str) else str(einfo) if einfo else None

        logger.error(
            f"Task failure handler triggered - Task: {task_name} (ID: {task_id}), "
            f"Exception: {str(exception)}"
        )

        # Handle the task failure
        TaskErrorHandler.handle_task_failure(
            task_id=task_id,
            task_name=task_name,
            exception=exception,
            tb=tb_str,
            retry_count=sender.request.retries if hasattr(sender, "request") else 0,
        )

    except Exception as e:
        logger.error(f"Error in task_failure_handler: {str(e)}", exc_info=True)


@task_retry.connect
def task_retry_handler(sender=None, task_id=None, reason=None, einfo=None, **kw):
    """Handle task retry - called when a task is retried due to failure"""
    try:
        task_name = sender.name if sender else "unknown"

        logger.warning(
            f"Task retry handler triggered - Task: {task_name} (ID: {task_id}), "
            f"Reason: {str(reason)}"
        )

        # Log retry event for debugging
        logger.debug(
            f"Task {task_name} (ID: {task_id}) is being retried. Exception info: {str(einfo)}"
        )

    except Exception as e:
        logger.error(f"Error in task_retry_handler: {str(e)}", exc_info=True)


@task_revoked.connect
def task_revoked_handler(
    sender=None, task_id=None, terminated=None, signum=None, expired=None, **kw
):
    """Handle task revocation - called when a task is cancelled/revoked"""
    try:
        task_name = sender.name if sender else "unknown"
        reason = "terminated" if terminated else "expired" if expired else "revoked"

        logger.warning(
            f"Task revoked handler triggered - Task: {task_name} (ID: {task_id}), "
            f"Reason: {reason}"
        )

    except Exception as e:
        logger.error(f"Error in task_revoked_handler: {str(e)}", exc_info=True)


def get_celery_app():
    """Get the Celery app instance"""
    return celery_app
