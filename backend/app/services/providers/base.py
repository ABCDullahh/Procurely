"""Base classes for data providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ProviderType(str, Enum):
    """Type of data provider."""

    SEARCH = "SEARCH"
    SCRAPE = "SCRAPE"
    HYBRID = "HYBRID"


class ProviderStatus(str, Enum):
    """Status of provider execution."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class ProviderResult:
    """Result from a single provider execution."""

    provider_name: str
    provider_type: ProviderType
    status: ProviderStatus
    data: list[dict]
    error: str | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    execution_time_ms: int = 0
    metadata: dict = field(default_factory=dict)


@dataclass
class SearchResult:
    """Standardized search result from any search provider."""

    url: str
    title: str
    snippet: str
    position: int
    source_provider: str

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "url": self.url,
            "title": self.title,
            "snippet": self.snippet,
            "position": self.position,
            "source_provider": self.source_provider,
        }


@dataclass
class ScrapedPage:
    """Standardized scraped page from any scrape provider."""

    url: str
    title: str | None
    content: str
    content_format: str  # text, markdown, html
    content_hash: str
    status: str  # SUCCESS, FAILED, TIMEOUT, BLOCKED
    error: str | None
    source_provider: str
    fetched_at: datetime
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "url": self.url,
            "title": self.title,
            "content": self.content,
            "content_format": self.content_format,
            "content_hash": self.content_hash,
            "status": self.status,
            "error": self.error,
            "source_provider": self.source_provider,
            "fetched_at": self.fetched_at.isoformat() if self.fetched_at else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScrapedPage":
        """Create from dictionary."""
        fetched_at = data.get("fetched_at")
        if isinstance(fetched_at, str):
            fetched_at = datetime.fromisoformat(fetched_at.replace("Z", "+00:00"))
        elif fetched_at is None:
            fetched_at = datetime.now(timezone.utc)

        return cls(
            url=data.get("url", ""),
            title=data.get("title"),
            content=data.get("content", ""),
            content_format=data.get("content_format", "text"),
            content_hash=data.get("content_hash", ""),
            status=data.get("status", "FAILED"),
            error=data.get("error"),
            source_provider=data.get("source_provider", "unknown"),
            fetched_at=fetched_at,
            metadata=data.get("metadata", {}),
        )


class BaseSearchProvider(ABC):
    """Abstract base class for search providers."""

    provider_name: str = "base_search"
    provider_type = ProviderType.SEARCH

    @abstractmethod
    async def search(
        self,
        query: str,
        num_results: int = 10,
        **kwargs: Any,
    ) -> list[SearchResult]:
        """
        Perform web search.

        Args:
            query: Search query string
            num_results: Maximum number of results to return
            **kwargs: Additional provider-specific parameters

        Returns:
            List of SearchResult objects
        """
        pass

    async def close(self) -> None:
        """Close any resources (HTTP clients, etc.)."""
        pass


class BaseScrapeProvider(ABC):
    """Abstract base class for scraping providers."""

    provider_name: str = "base_scrape"
    provider_type = ProviderType.SCRAPE

    @abstractmethod
    async def scrape(
        self,
        url: str,
        **kwargs: Any,
    ) -> ScrapedPage:
        """
        Scrape a single URL.

        Args:
            url: URL to scrape
            **kwargs: Additional provider-specific parameters

        Returns:
            ScrapedPage with content or error
        """
        pass

    @abstractmethod
    async def scrape_batch(
        self,
        urls: list[str],
        max_concurrent: int = 5,
        **kwargs: Any,
    ) -> list[ScrapedPage]:
        """
        Scrape multiple URLs concurrently.

        Args:
            urls: List of URLs to scrape
            max_concurrent: Maximum concurrent requests
            **kwargs: Additional provider-specific parameters

        Returns:
            List of ScrapedPage results
        """
        pass

    async def close(self) -> None:
        """Close any resources (HTTP clients, etc.)."""
        pass
