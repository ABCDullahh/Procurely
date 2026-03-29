"""VendorMetrics model for scores and computed metrics."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class VendorMetrics(Base):
    """Computed metrics and scores for a vendor."""

    __tablename__ = "vendor_metrics"

    __table_args__ = (
        UniqueConstraint("vendor_id", "search_run_id", name="uq_vendor_run_metrics"),
        Index("ix_vendor_metrics_vendor_id", "vendor_id"),
        Index("ix_vendor_metrics_search_run_id", "search_run_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    vendor_id: Mapped[int] = mapped_column(
        ForeignKey("vendors.id"), nullable=False
    )
    search_run_id: Mapped[int] = mapped_column(
        ForeignKey("search_runs.id"), nullable=False
    )

    # Scores (0-100)
    fit_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    trust_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    quality_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # Research quality
    price_score: Mapped[float] = mapped_column(Float, default=50.0, nullable=False)  # Pricing competitiveness
    overall_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Criteria matching
    must_have_matched: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    must_have_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    nice_to_have_matched: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    nice_to_have_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Source quality
    source_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    evidence_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # DeepResearch quality metrics
    completeness_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    confidence_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    source_diversity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    research_depth: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    price_competitiveness: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Timestamps
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    vendor = relationship("Vendor", back_populates="metrics")
    search_run = relationship("SearchRun", back_populates="vendor_metrics")

    def __repr__(self) -> str:
        return f"<VendorMetrics vendor_id={self.vendor_id} overall={self.overall_score}>"
