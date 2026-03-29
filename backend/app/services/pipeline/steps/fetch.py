"""Page fetching step - retrieves web page content."""

import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class FetchedPage:
    """Fetched page content and metadata."""

    url: str
    title: str | None
    content: str
    content_hash: str
    status: str  # SUCCESS, FAILED, TIMEOUT
    error: str | None
    fetched_at: datetime


async def fetch_page(
    client: httpx.AsyncClient,
    url: str,
    timeout: float = 15.0,
) -> FetchedPage:
    """
    Fetch a single page and extract text content.

    Args:
        client: httpx AsyncClient
        url: URL to fetch
        timeout: Request timeout in seconds

    Returns:
        FetchedPage with content or error
    """
    fetched_at = datetime.now(timezone.utc)

    try:
        response = await client.get(
            url,
            timeout=timeout,
            follow_redirects=True,
        )

        if response.status_code != 200:
            return FetchedPage(
                url=url,
                title=None,
                content="",
                content_hash="",
                status="FAILED",
                error=f"HTTP {response.status_code}",
                fetched_at=fetched_at,
            )

        # Parse HTML and extract text
        soup = BeautifulSoup(response.text, "html.parser")

        # Get title
        title = None
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)[:500]

        # Remove scripts and styles
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()

        # Extract text
        text = soup.get_text(separator=" ", strip=True)
        # Limit content size
        text = text[:50000]

        content_hash = hashlib.sha256(text.encode()).hexdigest()[:16]

        return FetchedPage(
            url=url,
            title=title,
            content=text,
            content_hash=content_hash,
            status="SUCCESS",
            error=None,
            fetched_at=fetched_at,
        )

    except httpx.TimeoutException:
        return FetchedPage(
            url=url,
            title=None,
            content="",
            content_hash="",
            status="TIMEOUT",
            error="Request timed out",
            fetched_at=fetched_at,
        )
    except Exception as e:
        return FetchedPage(
            url=url,
            title=None,
            content="",
            content_hash="",
            status="FAILED",
            error=str(e)[:500],
            fetched_at=fetched_at,
        )


async def fetch_pages(
    urls: list[str],
    max_concurrent: int = 5,
    timeout: float = 15.0,
) -> list[FetchedPage]:
    """
    Fetch multiple pages concurrently.

    Args:
        urls: List of URLs to fetch
        max_concurrent: Max concurrent requests
        timeout: Per-request timeout

    Returns:
        List of FetchedPage results
    """
    import asyncio

    results: list[FetchedPage] = []

    async with httpx.AsyncClient(
        headers={
            "User-Agent": (
                "Mozilla/5.0 (compatible; ProcurelyBot/1.0; "
                "+https://procurely.dev/bot)"
            )
        },
        follow_redirects=True,
    ) as client:
        # Process in batches
        for i in range(0, len(urls), max_concurrent):
            batch = urls[i : i + max_concurrent]
            tasks = [fetch_page(client, url, timeout) for url in batch]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)

    success_count = sum(1 for r in results if r.status == "SUCCESS")
    logger.info(f"Fetched {success_count}/{len(urls)} pages successfully")

    return results
