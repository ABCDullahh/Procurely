"""User model for authentication and authorization."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.api_key import ApiKey
    from app.models.audit_log import AuditLog
    from app.models.procurement_request import ProcurementRequest
    from app.models.shortlist import Shortlist


class UserRole(str, Enum):
    """User roles for RBAC."""

    ADMIN = "admin"
    MEMBER = "member"


class User(Base):
    """User model for authentication."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(50), default=UserRole.MEMBER.value, nullable=False)
    tier: Mapped[str] = mapped_column(String(20), default="free", nullable=False)
    # "free" = 1 search allowed, "paid" = unlimited, "admin" = unlimited + admin access
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    api_keys_updated: Mapped[list["ApiKey"]] = relationship(
        "ApiKey", back_populates="updated_by"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="actor"
    )
    procurement_requests: Mapped[list["ProcurementRequest"]] = relationship(
        "ProcurementRequest", back_populates="created_by"
    )
    shortlists: Mapped[list["Shortlist"]] = relationship(
        "Shortlist", back_populates="creator"
    )

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == UserRole.ADMIN.value
