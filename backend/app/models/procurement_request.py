"""Procurement Request model for storing search requests."""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class RequestStatus(str, Enum):
    """Status of a procurement request."""

    DRAFT = "DRAFT"
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ProcurementRequest(Base):
    """Procurement request for vendor search."""

    __tablename__ = "procurement_requests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Core search parameters
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    keywords: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array of keywords
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Budget & timeline
    budget_min: Mapped[int | None] = mapped_column(nullable=True)
    budget_max: Mapped[int | None] = mapped_column(nullable=True)
    timeline: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Criteria (JSON objects)
    must_have_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    nice_to_have_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    # Selected data providers (JSON array: ["SERPER", "JINA_READER", "CRAWL4AI"])
    selected_providers: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Indonesia focus and research configuration
    locale: Mapped[str] = mapped_column(String(10), default="id_ID", nullable=False)
    country_code: Mapped[str] = mapped_column(String(2), default="ID", nullable=False)
    region_bias: Mapped[bool] = mapped_column(default=True, nullable=False)  # Prefer local vendors
    research_config: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON config

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20),
        default=RequestStatus.DRAFT.value,
        nullable=False,
        index=True,
    )

    # Chat-triggered requests (ephemeral = internal, not shown in user's request list)
    is_ephemeral: Mapped[bool] = mapped_column(default=False, nullable=False)
    source: Mapped[str] = mapped_column(String(20), default="FORM", nullable=False)  # FORM or CHAT

    # Ownership
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
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
    created_by = relationship("User", back_populates="procurement_requests")
    search_runs = relationship("SearchRun", back_populates="request", cascade="all, delete-orphan")
    shortlists = relationship("Shortlist", back_populates="request")

    def __repr__(self) -> str:
        return f"<ProcurementRequest id={self.id} title={self.title} status={self.status}>"
