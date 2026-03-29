"""API Key model for storing encrypted provider keys."""

from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ApiKeyProvider(str, Enum):
    """Supported API key providers."""

    OPENAI = "OPENAI"
    GEMINI = "GEMINI"
    SEARCH_PROVIDER = "SEARCH_PROVIDER"
    TAVILY = "TAVILY"
    FIRECRAWL = "FIRECRAWL"
    SERPAPI = "SERPAPI"  # For Google Shopping integration


class ApiKey(Base):
    """API Key model for storing encrypted provider credentials."""

    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    provider: Mapped[str] = mapped_column(
        String(50), index=True, nullable=False  # Not unique - allows historical keys
    )
    encrypted_value: Mapped[str] = mapped_column(Text, nullable=False)
    masked_tail: Mapped[str] = mapped_column(String(10), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    default_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    updated_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )

    # Relationship
    updated_by = relationship("User", back_populates="api_keys_updated")

    def __repr__(self) -> str:
        return f"<ApiKey provider={self.provider} active={self.is_active}>"
