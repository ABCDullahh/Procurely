"""Schemas for data providers API."""

from pydantic import BaseModel


class DataProviderResponse(BaseModel):
    """Response schema for a data provider."""

    name: str
    provider_type: str  # SEARCH, SCRAPE, HYBRID
    display_name: str
    description: str | None
    requires_api_key: bool
    api_key_provider: str | None  # Reference to api_key.provider
    is_configured: bool  # True if API key is set (for providers that require it)
    is_enabled: bool
    is_default: bool
    is_free: bool


class ProvidersListResponse(BaseModel):
    """Response schema for listing all providers."""

    providers: list[DataProviderResponse]
    search_providers: list[str]
    scrape_providers: list[str]


class ProviderStatusResponse(BaseModel):
    """Response schema for provider status check."""

    provider: str
    status: str  # AVAILABLE, UNAVAILABLE, NOT_CONFIGURED
    message: str | None = None


class UpdateProviderRequest(BaseModel):
    """Request schema for updating provider settings."""

    is_enabled: bool | None = None
    is_default: bool | None = None
