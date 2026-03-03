"""SQLAlchemy ORM models for common/shared entities"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Index, Integer, String, Text

from app.core.database import Base


class APICache(Base):
    """API response cache"""

    __tablename__ = "api_cache"

    id = Column(Integer, primary_key=True, index=True)
    api_type = Column(String(20), nullable=False)  # "tmdb"
    query_key = Column(String(255), nullable=False)
    response_data = Column(Text, nullable=False)  # JSON response
    expires_at = Column(DateTime, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_api_cache_type_key", "api_type", "query_key"),
        Index("idx_api_cache_expires", "expires_at"),
    )


class FileQueue(Base):
    """File processing queue"""

    __tablename__ = "file_queue"

    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String(500), unique=True, nullable=False)
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    media_type = Column(String(20))  # "movie" or "tv_show"
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)

    __table_args__ = (
        Index("idx_file_queue_status", "status"),
        Index("idx_file_queue_created", "created_at"),
    )


class TaskError(Base):
    """Task error tracking and audit trail"""

    __tablename__ = "task_errors"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(255), nullable=False)
    task_name = Column(String(255), nullable=False)
    error_message = Column(Text, nullable=False)
    error_traceback = Column(Text)
    severity = Column(String(20), nullable=False)  # critical, warning, info
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_task_errors_task_id", "task_id"),
        Index("idx_task_errors_created", "created_at"),
        Index("idx_task_errors_severity", "severity"),
    )


class BatchOperation(Base):
    """Batch operation tracking and progress monitoring"""

    __tablename__ = "batch_operations"

    id = Column(Integer, primary_key=True, index=True)
    operation_type = Column(String(50), nullable=False)  # "metadata_sync", "file_import"
    status = Column(
        String(20), nullable=False, default="pending"
    )  # pending, running, completed, failed, cancelled
    total_items = Column(Integer, nullable=False)
    completed_items = Column(Integer, default=0)
    failed_items = Column(Integer, default=0)
    progress_percentage = Column(Float, default=0.0)
    eta = Column(DateTime, nullable=True)  # Estimated time of completion
    error_message = Column(Text, nullable=True)
    operation_metadata = Column(Text, nullable=True)  # JSON for operation-specific data
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_batch_operations_status", "status"),
        Index("idx_batch_operations_type", "operation_type"),
        Index("idx_batch_operations_created", "created_at"),
    )
