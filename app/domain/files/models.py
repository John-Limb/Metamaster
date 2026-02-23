"""SQLAlchemy ORM models for File entities"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, BigInteger, DateTime, Boolean, Index
from app.core.database import Base


class FileItem(Base):
    """File entity for tracked media files"""

    __tablename__ = "file_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False)
    path = Column(String(1000), nullable=False, unique=True, index=True)
    type = Column(String(20), nullable=False)  # 'file' or 'directory'
    size = Column(BigInteger)  # in bytes
    mime_type = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_indexed = Column(Boolean, default=False)
    metadata_json = Column(Text)  # JSON metadata stored as string
    duration_seconds = Column(Integer, nullable=True)   # seconds from FFprobe
    video_codec = Column(String(20), nullable=True)     # e.g. 'h264', 'hevc', 'av1'
    video_width = Column(Integer, nullable=True)         # e.g. 1920
    video_height = Column(Integer, nullable=True)        # e.g. 1080

    __table_args__ = (
        Index("idx_file_items_type", "type"),
        Index("idx_file_items_parent_path", "path"),
        Index("idx_file_items_is_indexed", "is_indexed"),
    )
