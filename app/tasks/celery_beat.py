"""Celery Beat scheduler configuration for periodic tasks"""

from celery.schedules import crontab

# Define the beat schedule for periodic tasks
beat_schedule = {
    "cleanup_cache": {
        "task": "app.tasks.cleanup_cache",
        "schedule": crontab(hour=2, minute=0),
        "options": {
            "queue": "media_processing",
        },
    },
    "sync_metadata": {
        "task": "app.tasks.sync_metadata",
        "schedule": crontab(day_of_week=0, hour=3, minute=0),
        "options": {
            "queue": "external_api",
        },
    },
    "cleanup_queue": {
        "task": "app.tasks.cleanup_queue",
        "schedule": crontab(hour=2, minute=30),
        "options": {
            "queue": "media_processing",
        },
    },
    "check_and_run_scan": {
        "task": "app.tasks.check_and_run_scan",
        "schedule": crontab(),  # every minute
        "options": {
            "queue": "default",
        },
    },
    "retry_failed_enrichment": {
        "task": "app.tasks.retry_failed_enrichment",
        "schedule": crontab(minute=0, hour="*/2"),  # every 2 hours
        "options": {
            "queue": "external_api",
        },
    },
    "enrich_file_technical_metadata": {
        "task": "app.tasks.enrich_file_technical_metadata",
        "schedule": crontab(minute="*/10"),  # every 10 minutes
        "options": {
            "queue": "media_processing",
        },
    },
}
