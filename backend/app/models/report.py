"""Report model for storing generated reports."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _utc_now() -> datetime:
    """Return current UTC datetime for default values."""
    return datetime.now(timezone.utc)


class Report(Base):
    """Generated HTML report for a search run."""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("search_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    format: Mapped[str] = mapped_column(
        String(20), nullable=False, default="HTML"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="COMPLETED"
    )
    html_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        nullable=False,
        index=True,
    )

    # Relationships
    run: Mapped["SearchRun"] = relationship("SearchRun")  # noqa: F821
    creator: Mapped["User"] = relationship("User")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Report id={self.id} run_id={self.run_id} format={self.format}>"
