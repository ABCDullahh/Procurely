"""Schemas for API key management."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ApiKeyProvider(str, Enum):
    """Supported API key providers."""

    OPENAI = "OPENAI"
    GEMINI = "GEMINI"
    SEARCH_PROVIDER = "SEARCH_PROVIDER"


class ApiKeyResponse(BaseModel):
    """Response schema for API key (never includes raw value)."""

    provider: str
    masked_tail: str
    is_active: bool
    default_model: str | None = None
    updated_at: datetime
    updated_by_email: str

    model_config = {"from_attributes": True}


class ApiKeyListResponse(BaseModel):
    """Response for list of API keys."""

    keys: list[ApiKeyResponse]


class ApiKeySetRequest(BaseModel):
    """Request to set/update an API key."""

    value: str = Field(..., min_length=10, description="The raw API key value")
    default_model: str | None = Field(None, max_length=128, description="Default model to use")


class ApiKeyTestResponse(BaseModel):
    """Response from testing an API key connection."""

    ok: bool
    message: str
    provider: str
    latency_ms: int | None = None


class ProviderModel(BaseModel):
    """A model available from a provider."""

    id: str
    label: str
    supports: list[str] = Field(default_factory=lambda: ["text"])


class ProviderModelsResponse(BaseModel):
    """Response for available models from a provider."""

    provider: str
    models: list[ProviderModel]
    source: str = "live"  # "live" or "curated"
    fetched_at: datetime | None = None
