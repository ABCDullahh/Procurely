"""Data providers package for multi-source data collection."""

from app.services.providers.base import (
    BaseScrapeProvider,
    BaseSearchProvider,
    ProviderResult,
    ProviderStatus,
    ProviderType,
    ScrapedPage,
    SearchResult,
)
from app.services.providers.registry import (
    ProviderFactory,
    register_scrape_provider,
    register_search_provider,
)

__all__ = [
    # Base classes
    "BaseSearchProvider",
    "BaseScrapeProvider",
    "ProviderResult",
    "ProviderStatus",
    "ProviderType",
    "ScrapedPage",
    "SearchResult",
    # Registry
    "ProviderFactory",
    "register_scrape_provider",
    "register_search_provider",
]
