"""Task monitoring and management API endpoints"""

from fastapi import APIRouter, HTTPException, Query
from celery.result import AsyncResult
from datetime import datetime
from typing import Optional, List
import logging

from app.tasks.celery_app import celery_app
from app.core.database import SessionLocal
from app.schemas import (
    TaskStatusResponse,
    TaskRetryResponse,
    TaskListResponse,
    TaskListItemResponse,
    TaskCancelResponse,
    TaskErrorResponse,
    PaginatedTaskErrorResponse,
    BatchOperationCreate,
    BatchOperationResponse,
    PaginatedBatchOperationResponse,
    BatchProgressUpdate,
)
from app.infrastructure.monitoring.error_handler import TaskErrorHandler
from app.application.batch_operations.service import BatchOperationService
from app.tasks import bulk_metadata_sync_task, bulk_file_import_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Get task status and result.

    - **task_id**: Celery task ID (string)

    Returns task status (pending/started/success/failure/retry), result, and error message if failed.
    """
    logger.info(f"Fetching status for task: {task_id}")

    try:
        result = AsyncResult(task_id, app=celery_app)

        # Get task info
        task_info = result.info

        # Determine timestamps
        created_at = None
        updated_at = None

        # Try to get timestamps from task info if available
        if isinstance(task_info, dict):
            created_at = task_info.get("created_at")
            updated_at = task_info.get("updated_at")

        # If timestamps are strings, parse them
        if created_at and isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                created_at = None

        if updated_at and isinstance(updated_at, str):
            try:
                updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                updated_at = None

        # Build response based on task state
        response_data = {
            "task_id": task_id,
            "status": result.state.lower(),
            "result": None,
            "error": None,
            "created_at": created_at,
            "updated_at": updated_at,
        }

        # Handle different task states
        if result.state == "SUCCESS":
            response_data["result"] = result.result if result.result else None
        elif result.state == "FAILURE":
            response_data["error"] = str(result.info) if result.info else "Task failed"
        elif result.state == "RETRY":
            response_data["error"] = str(result.info) if result.info else "Task is being retried"
        elif result.state == "STARTED":
            response_data["result"] = result.info if isinstance(result.info, dict) else None

        return TaskStatusResponse(**response_data)

    except Exception as e:
        logger.error(f"Error fetching task status for {task_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching task status: {str(e)}")


@router.post("/{task_id}/retry", response_model=TaskRetryResponse)
async def retry_task(task_id: str):
    """
    Retry a failed task.

    - **task_id**: Celery task ID (string)

    Only allows retry if task status is "failure". Returns new task_id for the retry attempt.
    """
    logger.info(f"Attempting to retry task: {task_id}")

    try:
        result = AsyncResult(task_id, app=celery_app)

        # Check if task is in a failed state
        if result.state not in ["FAILURE", "RETRY"]:
            logger.warning(f"Cannot retry task {task_id} with state {result.state}")
            raise HTTPException(
                status_code=400,
                detail=f"Task cannot be retried. Current state: {result.state}. Only failed tasks can be retried.",
            )

        # Get the original task name and args
        # Note: This requires task_track_started to be enabled and proper task configuration
        task_name = result.name if hasattr(result, "name") else None

        if not task_name:
            logger.error(f"Cannot determine task name for {task_id}")
            raise HTTPException(
                status_code=400, detail="Cannot retry task: task name not available"
            )

        # Get the task function from celery app
        task_func = celery_app.tasks.get(task_name)

        if not task_func:
            logger.error(f"Task function {task_name} not found in celery app")
            raise HTTPException(status_code=400, detail=f"Task function {task_name} not found")

        # Retry the task with default args (empty)
        # In a real scenario, you might want to store original args in the result backend
        new_result = task_func.apply_async()
        new_task_id = new_result.id

        logger.info(f"Task {task_id} retried successfully. New task ID: {new_task_id}")

        return TaskRetryResponse(
            success=True,
            message="Task retry initiated successfully",
            original_task_id=task_id,
            new_task_id=new_task_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrying task {task_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrying task: {str(e)}")


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    status: Optional[str] = Query(
        None, description="Filter by status (pending/started/success/failure/retry)"
    ),
    limit: int = Query(50, ge=1, le=100, description="Items per page (1-100, default: 50)"),
    offset: int = Query(0, ge=0, description="Offset from start (default: 0)"),
):
    """
    List recent tasks with optional filtering.

    - **status**: Optional filter by task status (pending/started/success/failure/retry)
    - **limit**: Number of items per page (1-100, default: 50)
    - **offset**: Offset from start (default: 0)

    Returns paginated list of tasks with metadata and total count.
    """
    logger.info(f"Listing tasks with status={status}, limit={limit}, offset={offset}")

    try:
        # Validate status parameter if provided
        valid_statuses = ["pending", "started", "success", "failure", "retry"]
        if status and status.lower() not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
            )

        # Get active tasks from celery
        inspect = celery_app.control.inspect()

        # Get all active tasks
        active_tasks = inspect.active() or {}
        scheduled_tasks = inspect.scheduled() or {}
        reserved_tasks = inspect.reserved() or {}

        # Combine all tasks
        all_tasks_dict = {}

        # Process active tasks
        for worker, tasks in active_tasks.items():
            for task in tasks:
                task_id = task.get("id")
                if task_id:
                    all_tasks_dict[task_id] = {
                        "status": "started",
                        "created_at": task.get("time_start"),
                    }

        # Process scheduled tasks
        for worker, tasks in scheduled_tasks.items():
            for task in tasks:
                task_id = task.get("request", {}).get("id")
                if task_id:
                    all_tasks_dict[task_id] = {
                        "status": "pending",
                        "created_at": None,
                    }

        # Process reserved tasks
        for worker, tasks in reserved_tasks.items():
            for task in tasks:
                task_id = task.get("id")
                if task_id and task_id not in all_tasks_dict:
                    all_tasks_dict[task_id] = {
                        "status": "pending",
                        "created_at": None,
                    }

        # Filter by status if provided
        if status:
            status_lower = status.lower()
            all_tasks_dict = {
                task_id: task_info
                for task_id, task_info in all_tasks_dict.items()
                if task_info["status"] == status_lower
            }

        # Get total count
        total = len(all_tasks_dict)

        # Apply pagination
        task_ids = list(all_tasks_dict.keys())[offset : offset + limit]

        # Build response items
        items = []
        for task_id in task_ids:
            task_info = all_tasks_dict[task_id]

            # Get detailed result for timestamp info
            result = AsyncResult(task_id, app=celery_app)

            # Parse created_at if available
            created_at = task_info.get("created_at")
            if created_at and isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    created_at = None

            items.append(
                TaskListItemResponse(
                    task_id=task_id,
                    status=task_info["status"],
                    created_at=created_at,
                    updated_at=None,
                )
            )

        logger.info(f"Retrieved {len(items)} tasks (total: {total})")

        return TaskListResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing tasks: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listing tasks: {str(e)}")


@router.delete("/{task_id}", response_model=TaskCancelResponse)
async def cancel_task(task_id: str):
    """
    Cancel/revoke a task.

    - **task_id**: Celery task ID (string)

    Only allows cancellation if task is not already completed.
    Returns success/failure status.
    """
    logger.info(f"Attempting to cancel task: {task_id}")

    try:
        result = AsyncResult(task_id, app=celery_app)

        # Check if task is already completed
        if result.state in ["SUCCESS", "FAILURE"]:
            logger.warning(f"Cannot cancel task {task_id} with state {result.state}")
            raise HTTPException(
                status_code=400,
                detail=f"Task cannot be cancelled. Current state: {result.state}. Only pending or running tasks can be cancelled.",
            )

        # Revoke the task
        celery_app.control.revoke(task_id, terminate=True)

        logger.info(f"Task {task_id} cancelled successfully")

        return TaskCancelResponse(
            success=True,
            message="Task cancelled successfully",
            task_id=task_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling task {task_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error cancelling task: {str(e)}")


@router.get("/errors", response_model=PaginatedTaskErrorResponse)
async def list_task_errors(
    severity: Optional[str] = Query(None, description="Filter by severity (critical/warning/info)"),
    limit: int = Query(50, ge=1, le=100, description="Items per page (1-100, default: 50)"),
    offset: int = Query(0, ge=0, description="Offset from start (default: 0)"),
):
    """
    List recent task errors with optional filtering.

    - **severity**: Optional filter by error severity (critical/warning/info)
    - **limit**: Number of items per page (1-100, default: 50)
    - **offset**: Offset from start (default: 0)

    Returns paginated list of task errors with details and total count.
    """
    logger.info(f"Listing task errors with severity={severity}, limit={limit}, offset={offset}")

    try:
        # Validate severity parameter if provided
        valid_severities = ["critical", "warning", "info"]
        if severity and severity.lower() not in valid_severities:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid severity. Must be one of: {', '.join(valid_severities)}",
            )

        # Get errors from database
        errors, total = TaskErrorHandler.get_recent_errors(
            severity=severity.lower() if severity else None,
            limit=limit,
            offset=offset,
        )

        # Convert to response models
        items = [TaskErrorResponse.model_validate(error) for error in errors]

        logger.info(f"Retrieved {len(items)} task errors (total: {total})")

        return PaginatedTaskErrorResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing task errors: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listing task errors: {str(e)}")


@router.get("/errors/{error_id}", response_model=TaskErrorResponse)
async def get_task_error(error_id: int):
    """
    Get details of a specific task error.

    - **error_id**: Task error ID (integer)

    Returns detailed information about the task error including full traceback.
    """
    logger.info(f"Fetching task error details: {error_id}")

    try:
        error = TaskErrorHandler.get_error_by_id(error_id)

        if not error:
            logger.warning(f"Task error not found: {error_id}")
            raise HTTPException(status_code=404, detail=f"Task error not found: {error_id}")

        return TaskErrorResponse.model_validate(error)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching task error {error_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching task error: {str(e)}")


# ============================================================================
# Batch Operations Endpoints
# ============================================================================


@router.post("/batch/metadata-sync", response_model=BatchOperationResponse)
async def start_metadata_sync_batch(request: BatchOperationCreate):
    """
    Start bulk metadata sync operation.

    - **operation_type**: Must be "metadata_sync"
    - **media_ids**: List of movie or TV show IDs to sync
    - **media_type**: Type of media ("movie" or "tv_show")

    Returns batch operation details with ID for tracking progress.
    """
    logger.info(f"Starting metadata sync batch with {len(request.media_ids or [])} items")

    try:
        # Validate operation type
        if request.operation_type != "metadata_sync":
            raise HTTPException(
                status_code=400,
                detail="Invalid operation_type for metadata sync endpoint",
            )

        # Validate media_ids
        if not request.media_ids or len(request.media_ids) == 0:
            raise HTTPException(status_code=400, detail="media_ids list cannot be empty")

        if not all(isinstance(mid, int) and mid > 0 for mid in request.media_ids):
            raise HTTPException(status_code=400, detail="All media_ids must be positive integers")

        # Validate media_type
        if not request.media_type or request.media_type not in ["movie", "tv_show"]:
            raise HTTPException(status_code=400, detail="media_type must be 'movie' or 'tv_show'")

        db = SessionLocal()
        try:
            service = BatchOperationService(db)

            # Create batch operation
            batch_op = service.create_batch_operation(
                operation_type="metadata_sync",
                total_items=len(request.media_ids),
                metadata={"media_type": request.media_type},
            )

            # Start async task
            task = bulk_metadata_sync_task.delay(batch_op.id, request.media_ids, request.media_type)

            logger.info(f"Started metadata sync batch {batch_op.id} with task {task.id}")

            return BatchOperationResponse.model_validate(batch_op)
        finally:
            db.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting metadata sync batch: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error starting metadata sync batch: {str(e)}")


@router.post("/batch/file-import", response_model=BatchOperationResponse)
async def start_file_import_batch(request: BatchOperationCreate):
    """
    Start bulk file import operation.

    - **operation_type**: Must be "file_import"
    - **file_paths**: List of file paths to import
    - **media_type**: Type of media ("movie" or "tv_show")

    Returns batch operation details with ID for tracking progress.
    """
    logger.info(f"Starting file import batch with {len(request.file_paths or [])} files")

    try:
        # Validate operation type
        if request.operation_type != "file_import":
            raise HTTPException(
                status_code=400,
                detail="Invalid operation_type for file import endpoint",
            )

        # Validate file_paths
        if not request.file_paths or len(request.file_paths) == 0:
            raise HTTPException(status_code=400, detail="file_paths list cannot be empty")

        if not all(isinstance(fp, str) and len(fp) > 0 for fp in request.file_paths):
            raise HTTPException(status_code=400, detail="All file_paths must be non-empty strings")

        # Validate media_type
        if not request.media_type or request.media_type not in ["movie", "tv_show"]:
            raise HTTPException(status_code=400, detail="media_type must be 'movie' or 'tv_show'")

        db = SessionLocal()
        try:
            service = BatchOperationService(db)

            # Create batch operation
            batch_op = service.create_batch_operation(
                operation_type="file_import",
                total_items=len(request.file_paths),
                metadata={"media_type": request.media_type},
            )

            # Start async task
            task = bulk_file_import_task.delay(batch_op.id, request.file_paths, request.media_type)

            logger.info(f"Started file import batch {batch_op.id} with task {task.id}")

            return BatchOperationResponse.model_validate(batch_op)
        finally:
            db.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting file import batch: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error starting file import batch: {str(e)}")


@router.get("/batch/{batch_id}", response_model=BatchOperationResponse)
async def get_batch_operation(batch_id: int):
    """
    Get batch operation status and progress.

    - **batch_id**: Batch operation ID

    Returns current status, progress percentage, ETA, and error details if applicable.
    """
    logger.info(f"Fetching batch operation: {batch_id}")

    try:
        db = SessionLocal()
        try:
            service = BatchOperationService(db)
            batch_op = service.get_batch_operation(batch_id)

            if not batch_op:
                logger.warning(f"Batch operation not found: {batch_id}")
                raise HTTPException(
                    status_code=404, detail=f"Batch operation not found: {batch_id}"
                )

            return BatchOperationResponse.model_validate(batch_op)
        finally:
            db.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching batch operation {batch_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching batch operation: {str(e)}")


@router.get("/batch", response_model=PaginatedBatchOperationResponse)
async def list_batch_operations(
    operation_type: Optional[str] = Query(None, description="Filter by operation type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Offset from start"),
):
    """
    List all batch operations with optional filtering.

    - **operation_type**: Optional filter by operation type (metadata_sync, file_import)
    - **status**: Optional filter by status (pending, running, completed, failed, cancelled)
    - **limit**: Number of items per page (1-100, default: 50)
    - **offset**: Offset from start (default: 0)

    Returns paginated list of batch operations.
    """
    logger.info(
        f"Listing batch operations: operation_type={operation_type}, status={status}, limit={limit}, offset={offset}"
    )

    try:
        db = SessionLocal()
        try:
            service = BatchOperationService(db)
            operations, total = service.list_batch_operations(
                operation_type=operation_type, status=status, limit=limit, offset=offset
            )

            items = [BatchOperationResponse.model_validate(op) for op in operations]

            return PaginatedBatchOperationResponse(
                items=items, total=total, limit=limit, offset=offset
            )
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error listing batch operations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listing batch operations: {str(e)}")


@router.delete("/batch/{batch_id}", response_model=TaskCancelResponse)
async def cancel_batch_operation(batch_id: int):
    """
    Cancel batch operation.

    - **batch_id**: Batch operation ID

    Cancels the batch operation and stops processing. Returns success/failure status.
    """
    logger.info(f"Cancelling batch operation: {batch_id}")

    try:
        db = SessionLocal()
        try:
            service = BatchOperationService(db)
            batch_op = service.cancel_batch_operation(batch_id)

            if not batch_op:
                logger.warning(f"Batch operation not found: {batch_id}")
                raise HTTPException(
                    status_code=404, detail=f"Batch operation not found: {batch_id}"
                )

            return TaskCancelResponse(
                success=True,
                message="Batch operation cancelled successfully",
                task_id=str(batch_id),
            )
        finally:
            db.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling batch operation {batch_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error cancelling batch operation: {str(e)}")


@router.get("/batch/{batch_id}/progress", response_model=BatchOperationResponse)
async def get_batch_progress(batch_id: int):
    """
    Get real-time progress updates for batch operation.

    - **batch_id**: Batch operation ID

    Returns current progress percentage, ETA, completed/failed item counts.
    """
    logger.info(f"Fetching batch progress: {batch_id}")

    try:
        db = SessionLocal()
        try:
            service = BatchOperationService(db)
            batch_op = service.get_batch_operation(batch_id)

            if not batch_op:
                logger.warning(f"Batch operation not found: {batch_id}")
                raise HTTPException(
                    status_code=404, detail=f"Batch operation not found: {batch_id}"
                )

            return BatchOperationResponse.model_validate(batch_op)
        finally:
            db.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching batch progress {batch_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching batch progress: {str(e)}")
