"""VendorFieldEvidence model for tracking extraction provenance."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class VendorFieldEvidence(Base):
    """Evidence for an extracted vendor field value."""

    __tablename__ = "vendor_field_evidence"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), nullable=False, index=True)
    source_id: Mapped[int | None] = mapped_column(
        ForeignKey("vendor_sources.id"), nullable=True, index=True
    )

    # Field being evidenced
    field_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    field_label: Mapped[str | None] = mapped_column(String(100), nullable=True)  # Human-readable
    field_value: Mapped[str] = mapped_column(Text, nullable=False)

    # Evidence category for grouping in UI
    # Values: summary, pricing, security, company, implementation, features
    category: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)

    # Evidence details
    evidence_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    evidence_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_title: Mapped[str | None] = mapped_column(String(500), nullable=True)  # Page title
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    # Extraction metadata
    extraction_method: Mapped[str] = mapped_column(
        String(50), default="LLM", nullable=False
    )  # LLM, REGEX, MANUAL

    # Timestamps
    extracted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    vendor = relationship("Vendor", back_populates="evidence")
    source = relationship("VendorSource")

    def __repr__(self) -> str:
        return f"<VendorFieldEvidence field={self.field_name} vendor_id={self.vendor_id}>"
