"""Data provider model for tracking available data sources."""

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from app.core.database import Base


class DataProviderType(str, Enum):
    """Type of data provider."""

    SEARCH = "SEARCH"
    SCRAPE = "SCRAPE"
    HYBRID = "HYBRID"


class DataProvider(Base):
    """
    Data provider configuration.

    Stores metadata about available search and scrape providers.
    Used to populate the provider selector in the UI.
    """

    __tablename__ = "data_provider"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    provider_type = Column(String(20), nullable=False)  # SEARCH, SCRAPE, HYBRID
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    requires_api_key = Column(Boolean, default=False)
    api_key_provider = Column(String(50), nullable=True)  # Reference to api_key.provider
    is_enabled = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    is_free = Column(Boolean, default=False)
    config_json = Column(Text, nullable=True)  # Provider-specific config
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        return f"<DataProvider {self.name}>"


class SearchRunProvider(Base):
    """
    Tracks which providers were used in a search run.

    Records execution status and timing for each provider.
    """

    __tablename__ = "search_run_provider"

    id = Column(Integer, primary_key=True, index=True)
    search_run_id = Column(Integer, nullable=False, index=True)
    provider_name = Column(String(50), nullable=False)
    provider_type = Column(String(20), nullable=False)
    status = Column(String(20), default="PENDING")  # PENDING, RUNNING, COMPLETED, FAILED
    results_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<SearchRunProvider {self.provider_name} run={self.search_run_id}>"


# Default providers to seed in database
DEFAULT_PROVIDERS = [
    {
        "name": "SERPER",
        "provider_type": "SEARCH",
        "display_name": "Google Search (Serper)",
        "description": "Google Search results via Serper.dev API. Fast and reliable.",
        "requires_api_key": True,
        "api_key_provider": "SEARCH_PROVIDER",
        "is_default": True,
        "is_free": False,
    },
    {
        "name": "TAVILY",
        "provider_type": "SEARCH",
        "display_name": "Tavily AI Search",
        "description": "AI-optimized search for RAG applications. Cleaner results.",
        "requires_api_key": True,
        "api_key_provider": "TAVILY",
        "is_default": False,
        "is_free": False,
    },
    {
        "name": "JINA_READER",
        "provider_type": "SCRAPE",
        "display_name": "Jina Reader",
        "description": "FREE. Converts URLs to clean, LLM-ready markdown. No API key needed.",
        "requires_api_key": False,
        "api_key_provider": None,
        "is_default": True,
        "is_free": True,
    },
    {
        "name": "CRAWL4AI",
        "provider_type": "SCRAPE",
        "display_name": "Crawl4AI",
        "description": "Self-hosted crawler with JavaScript rendering. Requires Docker.",
        "requires_api_key": False,
        "api_key_provider": None,
        "is_default": False,
        "is_free": True,
    },
    {
        "name": "HTTPX",
        "provider_type": "SCRAPE",
        "display_name": "Basic HTTP (Legacy)",
        "description": "Simple HTTP scraper. No JS rendering. Best for static sites.",
        "requires_api_key": False,
        "api_key_provider": None,
        "is_default": False,
        "is_free": True,
    },
    {
        "name": "FIRECRAWL",
        "provider_type": "HYBRID",
        "display_name": "Firecrawl",
        "description": "Premium scraping with LLM-ready output. Both search and scrape.",
        "requires_api_key": True,
        "api_key_provider": "FIRECRAWL",
        "is_default": False,
        "is_free": False,
    },
    {
        "name": "SERPAPI_SHOPPING",
        "provider_type": "SEARCH",
        "display_name": "Google Shopping (SerpAPI)",
        "description": "Google Shopping product and pricing data via SerpAPI. For vendor pricing comparison.",
        "requires_api_key": True,
        "api_key_provider": "SERPAPI",
        "is_default": False,
        "is_free": False,
    },
]
