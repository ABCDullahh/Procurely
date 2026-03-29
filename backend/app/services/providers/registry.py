"""Provider registry and factory for creating provider instances."""

import logging
from typing import Type

from sqlalchemy.orm import Session

from app.services.errors import ConfigMissingError
from app.services.keys import get_active_api_key
from app.services.providers.base import (
    BaseScrapeProvider,
    BaseSearchProvider,
)

logger = logging.getLogger(__name__)

# Global provider registries
_search_providers: dict[str, Type[BaseSearchProvider]] = {}
_scrape_providers: dict[str, Type[BaseScrapeProvider]] = {}


def register_search_provider(name: str):
    """
    Decorator to register a search provider class.

    Usage:
        @register_search_provider("SERPER")
        class SerperProvider(BaseSearchProvider):
            ...
    """

    def decorator(cls: Type[BaseSearchProvider]):
        _search_providers[name] = cls
        logger.debug(f"Registered search provider: {name}")
        return cls

    return decorator


def register_scrape_provider(name: str):
    """
    Decorator to register a scrape provider class.

    Usage:
        @register_scrape_provider("JINA_READER")
        class JinaReaderProvider(BaseScrapeProvider):
            ...
    """

    def decorator(cls: Type[BaseScrapeProvider]):
        _scrape_providers[name] = cls
        logger.debug(f"Registered scrape provider: {name}")
        return cls

    return decorator


def get_registered_search_providers() -> list[str]:
    """Get list of registered search provider names."""
    return list(_search_providers.keys())


def get_registered_scrape_providers() -> list[str]:
    """Get list of registered scrape provider names."""
    return list(_scrape_providers.keys())


class ProviderFactory:
    """Factory for creating provider instances with proper configuration."""

    def __init__(self, db: Session):
        """
        Initialize factory with database session.

        Args:
            db: SQLAlchemy database session for API key lookup
        """
        self.db = db

    def get_search_provider(self, name: str) -> BaseSearchProvider:
        """
        Create and return a search provider instance.

        Args:
            name: Provider name (e.g., "SERPER", "TAVILY")

        Returns:
            Configured search provider instance

        Raises:
            ValueError: If provider not registered
            ConfigMissingError: If required API key not configured
        """
        # Lazy load providers to avoid circular imports
        if not _search_providers:
            from app.services.providers.search import serper  # noqa: F401
            from app.services.providers.search import tavily  # noqa: F401
            from app.services.providers.search import serpapi_shopping  # noqa: F401

        if name not in _search_providers:
            raise ValueError(
                f"Unknown search provider: {name}. "
                f"Available: {list(_search_providers.keys())}"
            )

        cls = _search_providers[name]

        # Get API key based on provider
        if name == "SERPER":
            try:
                api_key = get_active_api_key(self.db, "SEARCH_PROVIDER")
                return cls(api_key)
            except ConfigMissingError:
                raise ConfigMissingError(
                    f"SEARCH_PROVIDER API key not configured for {name}. "
                    "Go to Admin -> API Keys to add a Serper API key."
                )
        elif name == "TAVILY":
            try:
                api_key = get_active_api_key(self.db, "TAVILY")
                return cls(api_key)
            except ConfigMissingError:
                raise ConfigMissingError(
                    "TAVILY API key not configured. "
                    "Go to Admin -> API Keys to add a Tavily API key."
                )
        else:
            # Provider doesn't require API key
            return cls()

    def get_scrape_provider(self, name: str) -> BaseScrapeProvider:
        """
        Create and return a scrape provider instance.

        Args:
            name: Provider name (e.g., "JINA_READER", "CRAWL4AI", "HTTPX")

        Returns:
            Configured scrape provider instance

        Raises:
            ValueError: If provider not registered
            ConfigMissingError: If required API key not configured
        """
        # Lazy load providers to avoid circular imports
        if not _scrape_providers:
            from app.services.providers.scrape import jina_reader  # noqa: F401
            from app.services.providers.scrape import crawl4ai  # noqa: F401
            from app.services.providers.scrape import httpx_provider  # noqa: F401
            from app.services.providers.scrape import firecrawl_provider  # noqa: F401

        if name not in _scrape_providers:
            raise ValueError(
                f"Unknown scrape provider: {name}. "
                f"Available: {list(_scrape_providers.keys())}"
            )

        cls = _scrape_providers[name]

        # Get API key based on provider
        if name == "FIRECRAWL":
            try:
                api_key = get_active_api_key(self.db, "FIRECRAWL")
                return cls(api_key)
            except ConfigMissingError:
                raise ConfigMissingError(
                    "FIRECRAWL API key not configured. "
                    "Go to Admin -> API Keys to add a Firecrawl API key."
                )
        else:
            # JINA_READER, CRAWL4AI, HTTPX don't require API keys
            return cls()

    def get_available_providers(self) -> dict:
        """
        Get dictionary of all available providers.

        Returns:
            Dict with "search" and "scrape" keys containing provider lists
        """
        return {
            "search": list(_search_providers.keys()),
            "scrape": list(_scrape_providers.keys()),
        }

    def is_provider_configured(self, name: str) -> bool:
        """
        Check if a provider is properly configured (API key available if needed).

        Args:
            name: Provider name

        Returns:
            True if provider can be used, False otherwise
        """
        # Providers that require API keys
        key_requirements = {
            "SERPER": "SEARCH_PROVIDER",
            "TAVILY": "TAVILY",
            "FIRECRAWL": "FIRECRAWL",
        }

        if name not in key_requirements:
            # Provider doesn't require API key
            return True

        try:
            get_active_api_key(self.db, key_requirements[name])
            return True
        except ConfigMissingError:
            return False
