"""Vendor model for storing discovered vendors."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.vendor_asset import VendorAsset
    from app.models.vendor_evidence import VendorFieldEvidence
    from app.models.vendor_metrics import VendorMetrics
    from app.models.vendor_source import VendorSource


class Vendor(Base):
    """Vendor discovered from procurement search."""

    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Company info
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(200), nullable=True)
    founded_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    employee_count: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Contact
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Pricing
    pricing_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pricing_details: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Security and compliance
    security_compliance: Mapped[str | None] = mapped_column(Text, nullable=True)
    deployment: Mapped[str | None] = mapped_column(String(200), nullable=True)
    integrations: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Structured procurement data (JSON for rich sections)
    # Contains: summary, target_segment, regions, use_cases, key_features,
    # differentiators, limitations, contract_terms, compliance_claims,
    # data_hosting, notable_customers, support_channels, etc.
    structured_data: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Shopping/pricing data from Google Shopping integration (JSON)
    # Contains: products, prices, currency, market_position
    shopping_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    price_range_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_range_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_last_updated: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    sources: Mapped[list["VendorSource"]] = relationship(
        "VendorSource", back_populates="vendor", cascade="all, delete-orphan"
    )
    evidence: Mapped[list["VendorFieldEvidence"]] = relationship(
        "VendorFieldEvidence", back_populates="vendor", cascade="all, delete-orphan"
    )
    metrics: Mapped["VendorMetrics | None"] = relationship(
        "VendorMetrics", back_populates="vendor", uselist=False, cascade="all, delete-orphan"
    )
    assets: Mapped[list["VendorAsset"]] = relationship(
        "VendorAsset", back_populates="vendor", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Vendor id={self.id} name={self.name}>"
