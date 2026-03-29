"""Scrape providers package - web scraping implementations."""

# Import providers to trigger registration
from app.services.providers.scrape.crawl4ai import Crawl4AIProvider
from app.services.providers.scrape.firecrawl_provider import FirecrawlProvider
from app.services.providers.scrape.httpx_provider import HttpxProvider
from app.services.providers.scrape.jina_reader import JinaReaderProvider

__all__ = [
    "JinaReaderProvider",
    "Crawl4AIProvider",
    "FirecrawlProvider",
    "HttpxProvider",
]
