"""
Shortlist models for vendor shortlisting feature.
"""
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.procurement_request import ProcurementRequest
    from app.models.user import User
    from app.models.vendor import Vendor


def _utc_now() -> datetime:
    """Return current UTC time for SQLite compatibility."""
    return datetime.now(timezone.utc)


class Shortlist(Base):
    """Represents a vendor shortlist created by a user."""

    __tablename__ = "shortlists"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    request_id: Mapped[int | None] = mapped_column(
        ForeignKey("procurement_requests.id"), nullable=True, index=True
    )
    created_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        onupdate=_utc_now,
        nullable=False,
    )

    # Relationships
    request: Mapped["ProcurementRequest | None"] = relationship(
        "ProcurementRequest", back_populates="shortlists"
    )
    creator: Mapped["User"] = relationship("User", back_populates="shortlists")
    items: Mapped[list["ShortlistItem"]] = relationship(
        "ShortlistItem",
        back_populates="shortlist",
        cascade="all, delete-orphan",
        order_by="ShortlistItem.position",
    )

    def __repr__(self) -> str:
        return f"<Shortlist id={self.id} name={self.name}>"


class ShortlistItem(Base):
    """Represents a vendor in a shortlist with position and notes."""

    __tablename__ = "shortlist_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    shortlist_id: Mapped[int] = mapped_column(
        ForeignKey("shortlists.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False
    )

    # Relationships
    shortlist: Mapped["Shortlist"] = relationship("Shortlist", back_populates="items")
    vendor: Mapped["Vendor"] = relationship("Vendor")

    __table_args__ = (
        UniqueConstraint("shortlist_id", "vendor_id", name="uq_shortlist_vendor"),
    )

    def __repr__(self) -> str:
        return f"<ShortlistItem id={self.id} shortlist={self.shortlist_id} vendor={self.vendor_id}>"
