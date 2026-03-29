"""Firecrawl scrape provider — premium JS-capable scraping."""

import asyncio
import hashlib
import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from app.services.providers.base import BaseScrapeProvider, ScrapedPage
from app.services.providers.registry import register_scrape_provider

logger = logging.getLogger(__name__)

FIRECRAWL_API_URL = "https://api.firecrawl.dev/v1/scrape"


@register_scrape_provider("FIRECRAWL")
class FirecrawlProvider(BaseScrapeProvider):
    """
    Scrape provider using Firecrawl API for JS-rendered, LLM-ready markdown.

    Features:
    - JavaScript rendering
    - Clean markdown output (LLM-optimized)
    - Main content extraction (strips nav, footer, ads)
    - Premium quality scraping

    Requires API key from https://firecrawl.dev
    """

    provider_name = "FIRECRAWL"

    def __init__(self, api_key: str):
        """
        Initialize Firecrawl provider.

        Args:
            api_key: Firecrawl API key
        """
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=5.0),
            follow_redirects=True,
        )

    async def scrape(self, url: str, **kwargs: Any) -> ScrapedPage:
        """
        Scrape a URL using Firecrawl API.

        Args:
            url: URL to scrape

        Returns:
            ScrapedPage with markdown content or error
        """
        fetched_at = datetime.now(timezone.utc)

        try:
            response = await self.client.post(
                FIRECRAWL_API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "url": url,
                    "formats": ["markdown"],
                    "onlyMainContent": True,
                    "timeout": 25000,
                },
            )

            if response.status_code == 429:
                logger.warning(f"Firecrawl rate limited for {url}")
                return ScrapedPage(
                    url=url,
                    title=None,
                    content="",
                    content_format="markdown",
                    content_hash="",
                    status="RATE_LIMITED",
                    error="Firecrawl rate limit exceeded",
                    source_provider=self.provider_name,
                    fetched_at=fetched_at,
                )

            if response.status_code != 200:
                return ScrapedPage(
                    url=url,
                    title=None,
                    content="",
                    content_format="markdown",
                    content_hash="",
                    status="FAILED",
                    error=f"HTTP {response.status_code}",
                    source_provider=self.provider_name,
                    fetched_at=fetched_at,
                )

            data = response.json()

            # Firecrawl v1 returns data.markdown
            content = ""
            title = None
            if data.get("success") and data.get("data"):
                content = data["data"].get("markdown", "")
                title = data["data"].get("metadata", {}).get("title")

            if not content:
                return ScrapedPage(
                    url=url,
                    title=title,
                    content="",
                    content_format="markdown",
                    content_hash="",
                    status="FAILED",
                    error="No content extracted",
                    source_provider=self.provider_name,
                    fetched_at=fetched_at,
                )

            # Generate content hash
            content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
            word_count = len(content.split())

            metadata_raw = data.get("data", {}).get("metadata", {})

            return ScrapedPage(
                url=url,
                title=title,
                content=content,
                content_format="markdown",
                content_hash=content_hash,
                status="SUCCESS",
                error=None,
                source_provider=self.provider_name,
                fetched_at=fetched_at,
                metadata={
                    "content_length": len(content),
                    "word_count": word_count,
                    "source_url": metadata_raw.get("sourceURL", url),
                    "status_code": metadata_raw.get("statusCode", 200),
                },
            )

        except httpx.TimeoutException:
            logger.warning(f"Firecrawl timeout for {url}")
            return ScrapedPage(
                url=url,
                title=None,
                content="",
                content_format="markdown",
                content_hash="",
                status="TIMEOUT",
                error="Request timed out after 30 seconds",
                source_provider=self.provider_name,
                fetched_at=fetched_at,
            )

        except httpx.ConnectError as e:
            logger.error(f"Firecrawl connection error for {url}: {e}")
            return ScrapedPage(
                url=url,
                title=None,
                content="",
                content_format="markdown",
                content_hash="",
                status="FAILED",
                error=f"Connection error: {str(e)[:200]}",
                source_provider=self.provider_name,
                fetched_at=fetched_at,
            )

        except Exception as e:
            logger.error(f"Firecrawl unexpected error for {url}: {e}")
            return ScrapedPage(
                url=url,
                title=None,
                content="",
                content_format="markdown",
                content_hash="",
                status="FAILED",
                error=str(e)[:500],
                source_provider=self.provider_name,
                fetched_at=fetched_at,
            )

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
            max_concurrent: Maximum concurrent requests (default 5)

        Returns:
            List of ScrapedPage results
        """
        results: list[ScrapedPage] = []

        # Process in batches to respect rate limits
        for i in range(0, len(urls), max_concurrent):
            batch = urls[i : i + max_concurrent]
            tasks = [self.scrape(url, **kwargs) for url in batch]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)

            # Small delay between batches to avoid rate limiting
            if i + max_concurrent < len(urls):
                await asyncio.sleep(0.5)

        success = sum(1 for r in results if r.status == "SUCCESS")
        logger.info(
            f"Firecrawl: scraped {success}/{len(urls)} pages successfully"
        )

        return results

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()
