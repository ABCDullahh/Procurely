"""Jina Reader provider - FREE, LLM-optimized markdown extraction."""

import asyncio
import hashlib
import logging
from datetime import datetime, timezone

import httpx

from app.services.providers.base import BaseScrapeProvider, ScrapedPage
from app.services.providers.registry import register_scrape_provider

logger = logging.getLogger(__name__)


@register_scrape_provider("JINA_READER")
class JinaReaderProvider(BaseScrapeProvider):
    """
    Jina Reader API - FREE, production-ready.

    Converts any URL to clean, LLM-ready markdown.
    Simply prefix URL with https://r.jina.ai/

    Features:
    - No API key required (free tier)
    - Clean markdown output (67% fewer tokens than HTML)
    - Image alt text generation
    - Links summary
    - Fast response times

    Docs: https://jina.ai/reader/
    """

    provider_name = "JINA_READER"
    BASE_URL = "https://r.jina.ai"

    def __init__(self):
        """Initialize Jina Reader provider."""
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=10.0),
            follow_redirects=True,
            headers={
                "User-Agent": "ProcurelyBot/1.0 (https://procurely.dev)",
            },
        )

    async def scrape(self, url: str, **kwargs) -> ScrapedPage:
        """
        Scrape single URL using Jina Reader.

        Args:
            url: URL to scrape

        Returns:
            ScrapedPage with markdown content or error
        """
        fetched_at = datetime.now(timezone.utc)

        try:
            # Jina Reader: just prefix the URL
            reader_url = f"{self.BASE_URL}/{url}"

            response = await self.client.get(
                reader_url,
                headers={
                    "Accept": "text/markdown",
                    # Note: x-with-generated-alt and x-with-links-summary require API key
                    # Using free tier without these premium features
                },
            )

            if response.status_code == 429:
                return ScrapedPage(
                    url=url,
                    title=None,
                    content="",
                    content_format="markdown",
                    content_hash="",
                    status="RATE_LIMITED",
                    error="Jina Reader rate limit exceeded",
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

            content = response.text

            # Extract title from markdown (first # heading)
            title = None
            for line in content.split("\n"):
                if line.startswith("# "):
                    title = line[2:].strip()[:500]  # Limit title length
                    break

            # Generate content hash
            content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

            # Calculate word count
            word_count = len(content.split())

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
                    "reader_url": reader_url,
                },
            )

        except httpx.TimeoutException:
            logger.warning(f"Jina Reader timeout for {url}")
            return ScrapedPage(
                url=url,
                title=None,
                content="",
                content_format="markdown",
                content_hash="",
                status="TIMEOUT",
                error="Request timed out after 60 seconds",
                source_provider=self.provider_name,
                fetched_at=fetched_at,
            )

        except httpx.ConnectError as e:
            logger.error(f"Jina Reader connection error for {url}: {e}")
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
            logger.error(f"Jina Reader unexpected error for {url}: {e}")
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
        **kwargs,
    ) -> list[ScrapedPage]:
        """
        Scrape multiple URLs concurrently.

        Args:
            urls: List of URLs to scrape
            max_concurrent: Maximum concurrent requests (default 5 to be nice to API)

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
            f"Jina Reader: scraped {success}/{len(urls)} pages successfully"
        )

        return results

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()
