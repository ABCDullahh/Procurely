"""SearchRun model for tracking pipeline executions."""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SearchRunStatus(str, Enum):
    """Status of a search run."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class SearchRun(Base):
    """Search run for tracking pipeline execution."""

    __tablename__ = "search_runs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("procurement_requests.id"), nullable=False)

    # Pipeline state
    status: Mapped[str] = mapped_column(
        String(20),
        default=SearchRunStatus.QUEUED.value,
        nullable=False,
        index=True,
    )
    current_step: Mapped[str | None] = mapped_column(String(50), nullable=True)
    progress_pct: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Results summary
    vendors_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sources_searched: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Error tracking
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # DeepResearch tracking
    research_iterations: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    research_queries: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list of queries per iteration
    gap_analysis: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON gap analysis results
    quality_assessment: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON quality report
    shopping_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON shopping/pricing data

    # Pipeline logging and token tracking
    pipeline_logs: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array of log entries
    token_usage: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON object with token counts per step

    # Timestamps
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    request = relationship("ProcurementRequest", back_populates="search_runs")
    vendor_sources = relationship(
        "VendorSource", back_populates="search_run", cascade="all, delete-orphan"
    )
    vendor_metrics = relationship(
        "VendorMetrics", back_populates="search_run", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<SearchRun id={self.id} status={self.status}>"
