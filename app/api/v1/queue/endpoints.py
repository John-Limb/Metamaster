"""Queue management API endpoints"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging

from app.core.database import SessionLocal
from app.infrastructure.file_system.queue_manager import FileQueueManager
from app.schemas import (
    QueueStatsResponse,
    QueueTaskResponse,
    PaginatedQueueTaskResponse,
    QueueOperationResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/queue", tags=["queue"])


def _get_queue_manager():
    """Create a FileQueueManager with a new database session."""
    db = SessionLocal()
    return FileQueueManager(session=db), db


def _map_media_type_to_task_type(media_type: str) -> str:
    """Map media_type from DB to frontend task type."""
    mapping = {
        "movie": "analyze",
        "tv_show": "analyze",
    }
    return mapping.get(media_type, "process")


@router.get("/stats", response_model=QueueStatsResponse)
async def get_queue_stats():
    """Get queue statistics including counts by status."""
    try:
        manager, db = _get_queue_manager()
        try:
            stats = manager.get_queue_stats()
            return QueueStatsResponse(
                totalTasks=stats["total"],
                pendingTasks=stats["pending"],
                processingTasks=stats["processing"],
                completedTasks=stats["completed"],
                failedTasks=stats["failed"],
            )
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error fetching queue stats: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching queue stats: {str(e)}")


@router.get("/tasks", response_model=PaginatedQueueTaskResponse)
async def get_queue_tasks(
    page: int = Query(1, ge=1, description="Page number"),
    pageSize: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
):
    """Get paginated list of queue tasks."""
    try:
        db = SessionLocal()
        try:
            from app.models import FileQueue

            query = db.query(FileQueue)

            if status:
                valid_statuses = ["pending", "processing", "completed", "failed"]
                if status not in valid_statuses:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
                    )
                query = query.filter(FileQueue.status == status)

            total = query.count()
            offset = (page - 1) * pageSize
            tasks = query.order_by(FileQueue.created_at.desc()).offset(offset).limit(pageSize).all()

            items = [
                QueueTaskResponse(
                    id=str(task.id),
                    type=_map_media_type_to_task_type(task.media_type),
                    status=task.status,
                    progress=100.0 if task.status == "completed" else 0.0,
                    createdAt=task.created_at,
                    updatedAt=task.processed_at,
                    error=task.error_message,
                )
                for task in tasks
            ]

            return PaginatedQueueTaskResponse(
                items=items,
                total=total,
                page=page,
                pageSize=pageSize,
            )
        finally:
            db.close()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching queue tasks: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching queue tasks: {str(e)}")


@router.get("/tasks/{task_id}", response_model=QueueTaskResponse)
async def get_queue_task(task_id: str):
    """Get details of a specific queue task."""
    try:
        manager, db = _get_queue_manager()
        try:
            file_status = manager.get_file_status(int(task_id))
            return QueueTaskResponse(
                id=str(file_status["id"]),
                type=_map_media_type_to_task_type(file_status["media_type"]),
                status=file_status["status"],
                progress=100.0 if file_status["status"] == "completed" else 0.0,
                createdAt=file_status["created_at"],
                updatedAt=file_status["processed_at"],
                error=file_status["error_message"],
            )
        finally:
            db.close()
    except RuntimeError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=f"Queue task not found: {task_id}")
        raise HTTPException(status_code=500, detail=str(e))
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid task ID")
    except Exception as e:
        logger.error(f"Error fetching queue task {task_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching queue task: {str(e)}")


@router.get("/tasks/{task_id}/progress")
async def get_task_progress(task_id: str):
    """Get progress for a specific queue task."""
    try:
        manager, db = _get_queue_manager()
        try:
            file_status = manager.get_file_status(int(task_id))
            progress = 100.0 if file_status["status"] == "completed" else 0.0
            return {"progress": progress, "status": file_status["status"]}
        finally:
            db.close()
    except RuntimeError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=f"Queue task not found: {task_id}")
        raise HTTPException(status_code=500, detail=str(e))
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid task ID")
    except Exception as e:
        logger.error(f"Error fetching task progress {task_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching task progress: {str(e)}")


@router.post("/tasks/{task_id}/retry", response_model=QueueTaskResponse)
async def retry_queue_task(task_id: str):
    """Retry a failed queue task."""
    try:
        manager, db = _get_queue_manager()
        try:
            success = manager.retry_failed_file(int(task_id))
            if not success:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot retry task. Task not found or not in failed status.",
                )
            file_status = manager.get_file_status(int(task_id))
            return QueueTaskResponse(
                id=str(file_status["id"]),
                type=_map_media_type_to_task_type(file_status["media_type"]),
                status=file_status["status"],
                progress=0.0,
                createdAt=file_status["created_at"],
                updatedAt=file_status["processed_at"],
                error=file_status["error_message"],
            )
        finally:
            db.close()
    except HTTPException:
        raise
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid task ID")
    except Exception as e:
        logger.error(f"Error retrying queue task {task_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrying queue task: {str(e)}")


@router.post("/tasks/{task_id}/cancel", response_model=QueueOperationResponse)
async def cancel_queue_task(task_id: str):
    """Cancel a pending or processing queue task."""
    try:
        db = SessionLocal()
        try:
            from app.models import FileQueue

            task = db.query(FileQueue).filter(FileQueue.id == int(task_id)).first()
            if not task:
                raise HTTPException(status_code=404, detail=f"Queue task not found: {task_id}")

            if task.status in ("completed", "failed"):
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot cancel task with status: {task.status}",
                )

            task.status = "failed"
            task.error_message = "Cancelled by user"
            db.commit()

            return QueueOperationResponse(
                success=True,
                message="Task cancelled successfully",
            )
        finally:
            db.close()
    except HTTPException:
        raise
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid task ID")
    except Exception as e:
        logger.error(f"Error cancelling queue task {task_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error cancelling queue task: {str(e)}")


@router.post("/clear-completed", response_model=QueueOperationResponse)
async def clear_completed_tasks():
    """Clear completed tasks from the queue."""
    try:
        db = SessionLocal()
        try:
            from app.models import FileQueue

            deleted_count = (
                db.query(FileQueue)
                .filter(FileQueue.status == "completed")
                .delete()
            )
            db.commit()
            return QueueOperationResponse(
                success=True,
                message=f"Cleared {deleted_count} completed tasks",
            )
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error clearing completed tasks: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error clearing completed tasks: {str(e)}")
