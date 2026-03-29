"""Legacy HTTPX provider - Basic HTTP scraping with BeautifulSoup."""

import asyncio
import hashlib
import logging
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

from app.services.providers.base import BaseScrapeProvider, ScrapedPage
from app.services.providers.registry import register_scrape_provider

logger = logging.getLogger(__name__)


@register_scrape_provider("HTTPX")
class HttpxProvider(BaseScrapeProvider):
    """
    Legacy HTTP scraper using httpx + BeautifulSoup.

    This is the original implementation from the codebase.
    Best for simple static HTML pages.

    Limitations:
    - No JavaScript rendering
    - No anti-bot bypass
    - Basic HTML parsing only
    """

    provider_name = "HTTPX"

    def __init__(self):
        """Initialize HTTPX provider."""
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(15.0, connect=10.0),
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (compatible; ProcurelyBot/1.0; "
                    "+https://procurely.dev/bot)"
                ),
            },
        )

    async def scrape(self, url: str, **kwargs) -> ScrapedPage:
        """
        Scrape single URL using httpx and BeautifulSoup.

        Args:
            url: URL to scrape

        Returns:
            ScrapedPage with text content or error
        """
        fetched_at = datetime.now(timezone.utc)

        try:
            response = await self.client.get(url)

            if response.status_code != 200:
                return ScrapedPage(
                    url=url,
                    title=None,
                    content="",
                    content_format="text",
                    content_hash="",
                    status="FAILED",
                    error=f"HTTP {response.status_code}",
                    source_provider=self.provider_name,
                    fetched_at=fetched_at,
                )

            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")

            # Extract title
            title = None
            title_tag = soup.find("title")
            if title_tag:
                title = title_tag.get_text(strip=True)[:500]

            # Remove unwanted elements
            for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
                element.decompose()

            # Extract text
            text = soup.get_text(separator=" ", strip=True)

            # Limit content size
            text = text[:50000]

            # Generate hash
            content_hash = hashlib.sha256(text.encode()).hexdigest()[:16]

            return ScrapedPage(
                url=url,
                title=title,
                content=text,
                content_format="text",
                content_hash=content_hash,
                status="SUCCESS",
                error=None,
                source_provider=self.provider_name,
                fetched_at=fetched_at,
                metadata={
                    "content_length": len(text),
                    "word_count": len(text.split()),
                },
            )

        except httpx.TimeoutException:
            return ScrapedPage(
                url=url,
                title=None,
                content="",
                content_format="text",
                content_hash="",
                status="TIMEOUT",
                error="Request timed out",
                source_provider=self.provider_name,
                fetched_at=fetched_at,
            )

        except Exception as e:
            logger.error(f"HTTPX error for {url}: {e}")
            return ScrapedPage(
                url=url,
                title=None,
                content="",
                content_format="text",
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
        **kwargs,
    ) -> list[ScrapedPage]:
        """
        Scrape multiple URLs concurrently.

        Args:
            urls: List of URLs to scrape
            max_concurrent: Maximum concurrent requests

        Returns:
            List of ScrapedPage results
        """
        results: list[ScrapedPage] = []

        for i in range(0, len(urls), max_concurrent):
            batch = urls[i : i + max_concurrent]
            tasks = [self.scrape(url, **kwargs) for url in batch]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)

        success = sum(1 for r in results if r.status == "SUCCESS")
        logger.info(f"HTTPX: scraped {success}/{len(urls)} pages successfully")

        return results

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()
