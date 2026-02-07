"""Task error handling and notification service"""

import logging
import traceback
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import TaskError

logger = logging.getLogger(__name__)


class TaskErrorHandler:
    """Handles task failures, logging, and notifications"""

    # Severity levels
    SEVERITY_CRITICAL = "critical"
    SEVERITY_WARNING = "warning"
    SEVERITY_INFO = "info"

    # Critical tasks that impact core functionality
    CRITICAL_TASKS = {
        "app.tasks.analyze_file",
        "app.tasks.enrich_metadata",
    }

    # Warning tasks that impact non-critical features
    WARNING_TASKS = {
        "app.tasks.cleanup_cache",
        "app.tasks.cleanup_queue",
    }

    @staticmethod
    def _determine_severity(task_name: str) -> str:
        """Determine error severity based on task name"""
        if task_name in TaskErrorHandler.CRITICAL_TASKS:
            return TaskErrorHandler.SEVERITY_CRITICAL
        elif task_name in TaskErrorHandler.WARNING_TASKS:
            return TaskErrorHandler.SEVERITY_WARNING
        else:
            return TaskErrorHandler.SEVERITY_INFO

    @staticmethod
    def handle_task_failure(
        task_id: str,
        task_name: str,
        exception: Exception,
        tb: Optional[str] = None,
        retry_count: int = 0,
    ) -> None:
        """
        Handle task failure by logging and storing error information.

        Args:
            task_id: Celery task ID
            task_name: Name of the task
            exception: The exception that was raised
            tb: Traceback string (optional)
            retry_count: Number of retries attempted
        """
        try:
            error_message = str(exception)
            error_traceback = tb or traceback.format_exc()
            severity = TaskErrorHandler._determine_severity(task_name)

            # Log the error
            TaskErrorHandler.log_task_error(
                task_id=task_id,
                task_name=task_name,
                error_details={
                    "error_message": error_message,
                    "error_traceback": error_traceback,
                    "severity": severity,
                    "retry_count": retry_count,
                },
            )

            # Store error in database
            TaskErrorHandler._store_error_in_db(
                task_id=task_id,
                task_name=task_name,
                error_message=error_message,
                error_traceback=error_traceback,
                severity=severity,
                retry_count=retry_count,
            )

            # Send notification
            TaskErrorHandler.notify_failure(
                task_id=task_id,
                task_name=task_name,
                error_message=error_message,
                severity=severity,
            )

        except Exception as e:
            logger.error(
                f"Error in handle_task_failure for task {task_id}: {str(e)}",
                exc_info=True,
            )

    @staticmethod
    def notify_failure(
        task_id: str,
        task_name: str,
        error_message: str,
        severity: str,
    ) -> None:
        """
        Send notifications for task failures.

        Args:
            task_id: Celery task ID
            task_name: Name of the task
            error_message: Error message
            severity: Error severity level
        """
        try:
            # Log notification
            log_level = (
                logging.ERROR
                if severity == TaskErrorHandler.SEVERITY_CRITICAL
                else logging.WARNING
            )
            logger.log(
                log_level,
                f"Task failure notification - Task: {task_name} (ID: {task_id}), "
                f"Severity: {severity}, Error: {error_message}",
            )

            # TODO: Add email/webhook notifications here if configured
            # For now, we rely on logging and database storage

        except Exception as e:
            logger.error(
                f"Error sending notification for task {task_id}: {str(e)}",
                exc_info=True,
            )

    @staticmethod
    def log_task_error(
        task_id: str,
        task_name: str,
        error_details: dict,
    ) -> None:
        """
        Log task error with structured information.

        Args:
            task_id: Celery task ID
            task_name: Name of the task
            error_details: Dictionary with error details
        """
        try:
            error_message = error_details.get("error_message", "Unknown error")
            severity = error_details.get("severity", TaskErrorHandler.SEVERITY_INFO)
            retry_count = error_details.get("retry_count", 0)

            logger.error(
                f"Task error - Task: {task_name} (ID: {task_id}), "
                f"Severity: {severity}, Retries: {retry_count}, "
                f"Error: {error_message}"
            )

        except Exception as e:
            logger.error(
                f"Error logging task error for {task_id}: {str(e)}",
                exc_info=True,
            )

    @staticmethod
    def _store_error_in_db(
        task_id: str,
        task_name: str,
        error_message: str,
        error_traceback: str,
        severity: str,
        retry_count: int,
    ) -> None:
        """
        Store error information in database for audit trail.

        Args:
            task_id: Celery task ID
            task_name: Name of the task
            error_message: Error message
            error_traceback: Full traceback
            severity: Error severity level
            retry_count: Number of retries attempted
        """
        db: Optional[Session] = None
        try:
            db = SessionLocal()

            # Check if error already exists for this task
            existing_error = (
                db.query(TaskError).filter(TaskError.task_id == task_id).first()
            )

            if existing_error:
                # Update existing error record
                existing_error.error_message = error_message
                existing_error.error_traceback = error_traceback
                existing_error.retry_count = retry_count
                existing_error.severity = severity
            else:
                # Create new error record
                task_error = TaskError(
                    task_id=task_id,
                    task_name=task_name,
                    error_message=error_message,
                    error_traceback=error_traceback,
                    severity=severity,
                    retry_count=retry_count,
                    created_at=datetime.utcnow(),
                )
                db.add(task_error)

            db.commit()
            logger.debug(f"Task error stored in database for task {task_id}")

        except Exception as e:
            logger.error(
                f"Error storing task error in database for {task_id}: {str(e)}",
                exc_info=True,
            )
            if db:
                db.rollback()
        finally:
            if db:
                db.close()

    @staticmethod
    def mark_error_resolved(task_id: str) -> None:
        """
        Mark a task error as resolved.

        Args:
            task_id: Celery task ID
        """
        db: Optional[Session] = None
        try:
            db = SessionLocal()

            error = db.query(TaskError).filter(TaskError.task_id == task_id).first()

            if error:
                error.resolved_at = datetime.utcnow()
                db.commit()
                logger.info(f"Task error marked as resolved for task {task_id}")

        except Exception as e:
            logger.error(
                f"Error marking task error as resolved for {task_id}: {str(e)}",
                exc_info=True,
            )
            if db:
                db.rollback()
        finally:
            if db:
                db.close()

    @staticmethod
    def get_recent_errors(
        severity: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[TaskError], int]:
        """
        Get recent task errors from database.

        Args:
            severity: Optional severity filter
            limit: Number of errors to return
            offset: Offset for pagination

        Returns:
            Tuple of (errors list, total count)
        """
        db: Optional[Session] = None
        try:
            db = SessionLocal()

            query = db.query(TaskError)

            if severity:
                query = query.filter(TaskError.severity == severity)

            total = query.count()
            errors = (
                query.order_by(TaskError.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            return errors, total

        except Exception as e:
            logger.error(f"Error retrieving task errors: {str(e)}", exc_info=True)
            return [], 0
        finally:
            if db:
                db.close()

    @staticmethod
    def get_error_by_id(error_id: int) -> Optional[TaskError]:
        """
        Get a specific task error by ID.

        Args:
            error_id: Task error ID

        Returns:
            TaskError object or None if not found
        """
        db: Optional[Session] = None
        try:
            db = SessionLocal()
            error = db.query(TaskError).filter(TaskError.id == error_id).first()
            return error

        except Exception as e:
            logger.error(
                f"Error retrieving task error {error_id}: {str(e)}", exc_info=True
            )
            return None
        finally:
            if db:
                db.close()
