"""Audit Log model for tracking admin actions."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AuditLog(Base):
    """Audit log for tracking admin actions."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    actor_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[str] = mapped_column(String(100), nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationship
    actor = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog action={self.action} actor={self.actor_user_id}>"


# Action constants
class AuditAction:
    """Audit action constants."""

    API_KEY_SET = "API_KEY_SET"
    API_KEY_ROTATE = "API_KEY_ROTATE"
    API_KEY_TEST = "API_KEY_TEST"
    API_KEY_DELETE = "API_KEY_DELETE"
    USER_CREATE = "USER_CREATE"
    USER_UPDATE = "USER_UPDATE"
    USER_DELETE = "USER_DELETE"
