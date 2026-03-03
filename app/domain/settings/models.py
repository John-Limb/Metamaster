"""AppSetting model for server-side key/value settings"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String

from app.core.database import Base


class AppSetting(Base):
    """Generic key/value store for server-side application settings."""

    __tablename__ = "app_settings"

    key = Column(String(100), primary_key=True, nullable=False)
    value = Column(String(500), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
