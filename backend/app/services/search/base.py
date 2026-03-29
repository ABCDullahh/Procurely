"""Abstract base class for search providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Standardized search result."""

    title: str
    url: str
    snippet: str
    position: int
    source_type: str = "SEARCH_RESULT"


@dataclass
class SearchConfig:
    """Configuration for search requests."""

    num_results: int = 10
    country: str | None = None
    language: str = "en"
    timeout_seconds: float = 30.0


class SearchProvider(ABC):
    """Abstract base class for search providers."""

    provider_name: str = "base"

    @abstractmethod
    async def search(
        self,
        query: str,
        config: SearchConfig | None = None,
    ) -> list[SearchResult]:
        """
        Perform web search.

        Args:
            query: Search query string
            config: Search configuration

        Returns:
            List of search results

        Raises:
            ProviderAuthError: Invalid API key
            ProviderRateLimitError: Rate limit exceeded
            ProviderTimeoutError: Request timed out
            ProviderResponseError: Unexpected response
        """
        pass

    def get_default_config(self) -> SearchConfig:
        """Get default configuration for this provider."""
        return SearchConfig()
