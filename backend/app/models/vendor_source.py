"""VendorSource model for tracking where vendor data was found."""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SourceType(str, Enum):
    """Type of source where vendor was discovered."""

    SEARCH_RESULT = "SEARCH_RESULT"
    WEBSITE = "WEBSITE"
    LINKEDIN = "LINKEDIN"
    CRUNCHBASE = "CRUNCHBASE"
    G2 = "G2"
    CAPTERRA = "CAPTERRA"
    OTHER = "OTHER"


class SourceCategory(str, Enum):
    """Category of source content for grouping."""

    OFFICIAL = "OFFICIAL"       # Main website, about page
    PRICING = "PRICING"         # Pricing pages
    SECURITY = "SECURITY"       # Security, compliance, trust pages
    DOCS = "DOCS"               # Documentation, help center
    REVIEWS = "REVIEWS"         # Review sites (G2, Capterra)
    NEWS = "NEWS"               # News, blog articles
    OTHER = "OTHER"


class VendorSource(Base):
    """Source where vendor information was extracted from."""

    __tablename__ = "vendor_sources"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), nullable=False, index=True)
    search_run_id: Mapped[int] = mapped_column(
        ForeignKey("search_runs.id"), nullable=False, index=True
    )

    # Source details
    source_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    source_type: Mapped[str] = mapped_column(
        String(50), default=SourceType.SEARCH_RESULT.value, nullable=False
    )
    page_title: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Source category for grouping in UI
    source_category: Mapped[str | None] = mapped_column(
        String(50), default=SourceCategory.OTHER.value, nullable=True, index=True
    )

    # Brief summary of what this source contributed
    content_summary: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Raw content
    raw_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)  # SHA256

    # Status
    fetch_status: Mapped[str] = mapped_column(String(20), default="SUCCESS", nullable=False)
    fetch_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    vendor = relationship("Vendor", back_populates="sources")
    search_run = relationship("SearchRun", back_populates="vendor_sources")

    def __repr__(self) -> str:
        return f"<VendorSource id={self.id} url={self.source_url[:50]}>"
