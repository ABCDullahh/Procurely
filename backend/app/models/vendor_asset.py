"""VendorAsset model for logos and other media."""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AssetType(str, Enum):
    """Type of vendor asset."""

    LOGO = "LOGO"
    FAVICON = "FAVICON"
    SCREENSHOT = "SCREENSHOT"
    BANNER = "BANNER"
    OTHER = "OTHER"


class VendorAsset(Base):
    """Media assets associated with a vendor."""

    __tablename__ = "vendor_assets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), nullable=False, index=True)

    # Asset details
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False)
    asset_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Metadata
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Priority for display (lower = higher priority)
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)

    # Timestamps
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    vendor = relationship("Vendor", back_populates="assets")

    def __repr__(self) -> str:
        return f"<VendorAsset type={self.asset_type} vendor_id={self.vendor_id}>"
