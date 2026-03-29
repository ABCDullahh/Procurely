"""Logo fetching step - finds and downloads vendor logos."""

import logging
from dataclasses import dataclass

import httpx

from app.services.pipeline.steps.score import ScoredVendor

logger = logging.getLogger(__name__)


@dataclass
class LogoResult:
    """Result of logo fetch attempt."""

    vendor_name: str
    logo_url: str | None
    source_url: str | None
    priority: int  # Lower is better


async def try_clearbit_logo(domain: str) -> str | None:
    """Try to get logo from Clearbit (free, no API key required)."""
    url = f"https://logo.clearbit.com/{domain}"
    timeout = httpx.Timeout(3.0, connect=2.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.head(url)
            if response.status_code == 200:
                return url
    except Exception:
        pass
    return None


async def try_favicon(domain: str) -> str | None:
    """Try to get favicon from domain."""
    url = f"https://{domain}/favicon.ico"
    timeout = httpx.Timeout(3.0, connect=2.0)
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.head(url)
            if response.status_code == 200:
                return url
    except Exception:
        pass
    return None


def extract_domain(url: str | None) -> str | None:
    """Extract domain from URL."""
    if not url:
        return None
    url = url.lower().strip()
    for prefix in ["https://", "http://", "www."]:
        if url.startswith(prefix):
            url = url[len(prefix):]
    return url.split("/")[0]


async def fetch_logo_for_vendor(vendor: ScoredVendor) -> LogoResult:
    """
    Attempt to fetch logo for a vendor.

    Tries in order:
    1. Clearbit logo API
    2. Favicon fallback

    Logo failures never crash the pipeline — returns empty result on error.

    Args:
        vendor: Scored vendor to fetch logo for

    Returns:
        LogoResult with best available logo
    """
    try:
        domain = extract_domain(vendor.vendor.data.get("website"))

        if not domain:
            return LogoResult(
                vendor_name=vendor.vendor.name,
                logo_url=None,
                source_url=None,
                priority=999,
            )

        # Try Clearbit first (higher quality)
        clearbit_url = await try_clearbit_logo(domain)
        if clearbit_url:
            return LogoResult(
                vendor_name=vendor.vendor.name,
                logo_url=clearbit_url,
                source_url=f"https://{domain}",
                priority=1,
            )

        # Try favicon as fallback
        favicon_url = await try_favicon(domain)
        if favicon_url:
            return LogoResult(
                vendor_name=vendor.vendor.name,
                logo_url=favicon_url,
                source_url=f"https://{domain}",
                priority=2,
            )

        return LogoResult(
            vendor_name=vendor.vendor.name,
            logo_url=None,
            source_url=None,
            priority=999,
        )
    except Exception as e:
        logger.warning(f"Logo fetch failed for {vendor.vendor.name}, skipping: {e}")
        return LogoResult(
            vendor_name=vendor.vendor.name,
            logo_url=None,
            source_url=None,
            priority=999,
        )


async def fetch_logos(
    vendors: list[ScoredVendor],
    max_concurrent: int = 10,
) -> list[LogoResult]:
    """
    Fetch logos for all vendors.

    Args:
        vendors: List of scored vendors
        max_concurrent: Max concurrent requests

    Returns:
        List of logo results
    """
    import asyncio

    results: list[LogoResult] = []

    # Process in batches
    for i in range(0, len(vendors), max_concurrent):
        batch = vendors[i : i + max_concurrent]
        tasks = [fetch_logo_for_vendor(v) for v in batch]
        batch_results = await asyncio.gather(*tasks)
        results.extend(batch_results)

    found_count = sum(1 for r in results if r.logo_url)
    logger.info(f"Found logos for {found_count}/{len(vendors)} vendors")

    return results
