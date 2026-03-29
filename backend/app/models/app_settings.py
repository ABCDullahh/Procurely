"""
AppSettings model for storing application-wide configuration.
"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _utc_now() -> datetime:
    """Return current UTC time for SQLite compatibility."""
    return datetime.now(timezone.utc)


class AppSettings(Base):
    """Key-value store for application settings."""

    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        onupdate=_utc_now,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<AppSettings key={self.key} value={self.value[:50]}>"
