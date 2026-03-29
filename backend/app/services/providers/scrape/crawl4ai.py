"""Crawl4AI provider - Self-hosted LLM-friendly web crawler."""

import asyncio
import hashlib
import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from app.services.providers.base import BaseScrapeProvider, ScrapedPage
from app.services.providers.registry import register_scrape_provider

logger = logging.getLogger(__name__)

# Default Crawl4AI service URL
DEFAULT_CRAWL4AI_URL = "http://localhost:11235"


@register_scrape_provider("CRAWL4AI")
class Crawl4AIProvider(BaseScrapeProvider):
    """
    Crawl4AI - Self-hosted LLM-friendly web crawler.

    Features:
    - JavaScript rendering (Playwright-based)
    - Clean markdown output
    - LLM extraction support
    - 50K+ GitHub stars
    - Full data sovereignty

    Requires Docker service to be running.
    Docs: https://docs.crawl4ai.com/

    Docker command:
        docker run -d -p 11235:11235 unclecode/crawl4ai:latest
    """

    provider_name = "CRAWL4AI"

    def __init__(self, base_url: str | None = None):
        """
        Initialize Crawl4AI provider.

        Args:
            base_url: Crawl4AI service URL (default: http://localhost:11235)
        """
        self.base_url = base_url or DEFAULT_CRAWL4AI_URL
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(120.0, connect=10.0),  # Longer timeout for JS rendering
        )

    async def scrape(self, url: str, **kwargs: Any) -> ScrapedPage:
        """
        Scrape single URL using Crawl4AI.

        Args:
            url: URL to scrape
            **kwargs:
                bypass_cache: Skip cache (default False)
                wait_for: CSS selector to wait for
                js_code: JavaScript to execute before scraping

        Returns:
            ScrapedPage with markdown content or error
        """
        fetched_at = datetime.now(timezone.utc)

        try:
            # Build request payload
            payload = {
                "urls": [url],
                "word_count_threshold": 10,
                "exclude_external_links": True,
                "process_iframes": False,
                "remove_overlay_elements": True,
                "bypass_cache": kwargs.get("bypass_cache", False),
            }

            # Optional: wait for element
            if "wait_for" in kwargs:
                payload["wait_for"] = kwargs["wait_for"]

            # Optional: execute JS
            if "js_code" in kwargs:
                payload["js_code"] = kwargs["js_code"]

            response = await self.client.post(
                f"{self.base_url}/crawl",
                json=payload,
            )

            if response.status_code != 200:
                return self._error_result(
                    url, fetched_at, f"HTTP {response.status_code}: {response.text[:200]}"
                )

            data = response.json()

            # Handle response format
            if isinstance(data, dict) and "results" in data:
                results = data.get("results", [])
                if not results:
                    return self._error_result(url, fetched_at, "No results returned")
                result = results[0]
            elif isinstance(data, list) and len(data) > 0:
                result = data[0]
            else:
                return self._error_result(url, fetched_at, f"Unexpected response format: {type(data)}")

            # Check if crawl was successful
            if not result.get("success", False):
                error_msg = result.get("error") or result.get("error_message") or "Unknown error"
                return self._error_result(url, fetched_at, error_msg)

            # Get content - prefer markdown, fallback to cleaned_html
            content = result.get("markdown", "") or result.get("cleaned_html", "") or ""
            content_format = "markdown" if result.get("markdown") else "html"

            if not content:
                return self._error_result(url, fetched_at, "No content extracted")

            # Generate content hash
            content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

            return ScrapedPage(
                url=url,
                title=result.get("title"),
                content=content,
                content_format=content_format,
                content_hash=content_hash,
                status="SUCCESS",
                error=None,
                source_provider=self.provider_name,
                fetched_at=fetched_at,
                metadata={
                    "word_count": result.get("word_count", len(content.split())),
                    "links_count": len(result.get("links", [])),
                    "images_count": len(result.get("images", [])),
                    "crawl_time_ms": result.get("crawl_time_ms"),
                },
            )

        except httpx.TimeoutException:
            logger.warning(f"Crawl4AI timeout for {url}")
            return self._error_result(url, fetched_at, "Request timed out after 120 seconds", "TIMEOUT")

        except httpx.ConnectError as e:
            logger.error(f"Crawl4AI connection error (is service running?): {e}")
            return self._error_result(
                url,
                fetched_at,
                f"Crawl4AI service not available at {self.base_url}. "
                "Make sure Docker container is running.",
                "SERVICE_UNAVAILABLE",
            )

        except Exception as e:
            logger.error(f"Crawl4AI unexpected error for {url}: {e}")
            return self._error_result(url, fetched_at, str(e)[:500])

    def _error_result(
        self,
        url: str,
        fetched_at: datetime,
        error: str,
        status: str = "FAILED",
    ) -> ScrapedPage:
        """Create an error result."""
        return ScrapedPage(
            url=url,
            title=None,
            content="",
            content_format="markdown",
            content_hash="",
            status=status,
            error=error,
            source_provider=self.provider_name,
            fetched_at=fetched_at,
        )

    async def scrape_batch(
        self,
        urls: list[str],
        max_concurrent: int = 3,  # Lower default due to heavier processing
        **kwargs: Any,
    ) -> list[ScrapedPage]:
        """
        Scrape multiple URLs concurrently.

        Note: Crawl4AI is heavier than simple HTTP scraping due to JS rendering,
        so we use a lower default concurrency.

        Args:
            urls: List of URLs to scrape
            max_concurrent: Maximum concurrent requests (default 3)

        Returns:
            List of ScrapedPage results
        """
        results: list[ScrapedPage] = []

        # Process in batches
        for i in range(0, len(urls), max_concurrent):
            batch = urls[i : i + max_concurrent]
            tasks = [self.scrape(url, **kwargs) for url in batch]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)

        success = sum(1 for r in results if r.status == "SUCCESS")
        logger.info(f"Crawl4AI: scraped {success}/{len(urls)} pages successfully")

        return results

    async def check_health(self) -> bool:
        """
        Check if Crawl4AI service is available.

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            response = await self.client.get(f"{self.base_url}/health", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()
