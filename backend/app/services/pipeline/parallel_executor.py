"""Parallel execution engine for multi-provider data collection."""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.services.providers.base import (
    ProviderResult,
    ProviderStatus,
    ProviderType,
    ScrapedPage,
    SearchResult,
)
from app.services.providers.registry import ProviderFactory

logger = logging.getLogger(__name__)

# Non-vendor domains to skip during URL pre-filtering
SKIP_DOMAINS = {
    "youtube.com", "youtu.be", "tiktok.com", "instagram.com", "facebook.com",
    "twitter.com", "x.com", "reddit.com", "quora.com", "medium.com",
    "wikipedia.org", "blogspot.com", "wordpress.com",
    "tribunnews.com", "kompas.com", "detik.com", "liputan6.com",
    "tempo.co", "cnnindonesia.com", "kumparan.com",
    "linkedin.com",  # unless /company/
    "pinterest.com", "flickr.com",
}

# Domains likely to be vendors/suppliers — prioritize these
BOOST_DOMAINS = {
    "indotrading.com", "ralali.com", "tokopedia.com", "bukalapak.com",
    "shopee.co.id", "alibaba.com", "made-in-china.com",
    "bhinneka.com", "monotaro.id",
}


def filter_urls(urls: list[str]) -> list[str]:
    """Remove non-vendor URLs and prioritize vendor-likely domains."""
    filtered = []
    boosted = []

    for url in urls:
        try:
            domain = urlparse(url).netloc.lower()
            # Remove www.
            if domain.startswith("www."):
                domain = domain[4:]

            # Skip known non-vendor domains
            if any(skip in domain for skip in SKIP_DOMAINS):
                # Exception: linkedin.com/company/ pages ARE vendors
                if "linkedin.com" in domain and "/company/" in url:
                    filtered.append(url)
                continue

            # Boost known vendor/marketplace domains
            if any(boost in domain for boost in BOOST_DOMAINS):
                boosted.append(url)
            elif domain.endswith(".co.id") or domain.endswith(".id"):
                boosted.append(url)  # Indonesian domains get priority
            else:
                filtered.append(url)
        except Exception:
            filtered.append(url)

    # Boosted first, then rest
    return boosted + filtered


@dataclass
class ParallelExecutionResult:
    """Result of parallel multi-provider execution."""

    search_results: list[SearchResult] = field(default_factory=list)
    scraped_pages: list[ScrapedPage] = field(default_factory=list)
    provider_results: list[ProviderResult] = field(default_factory=list)
    total_urls: int = 0
    unique_urls: int = 0
    total_pages_scraped: int = 0
    execution_time_ms: int = 0


class ParallelExecutor:
    """
    Execute multiple providers in parallel for data collection.

    This engine enables running multiple search and scrape providers
    simultaneously to maximize data coverage and quality.
    """

    def __init__(
        self,
        db: Session,
        run_id: int,
        on_progress: Callable[[str, int], None] | None = None,
    ):
        """
        Initialize parallel executor.

        Args:
            db: Database session for API key lookup
            run_id: SearchRun ID for tracking
            on_progress: Optional callback for progress updates (step_name, percent)
        """
        self.db = db
        self.run_id = run_id
        self.factory = ProviderFactory(db)
        self.on_progress = on_progress or (lambda step, pct: None)

    async def execute_search(
        self,
        queries: list[str],
        search_providers: list[str],
        results_per_query: int = 10,
    ) -> list[ProviderResult]:
        """
        Execute search across multiple providers in parallel.

        Args:
            queries: List of search queries
            search_providers: List of provider names (e.g., ["SERPER", "TAVILY"])
            results_per_query: Max results per query

        Returns:
            List of ProviderResult from each provider
        """

        async def run_search_provider(provider_name: str) -> ProviderResult:
            started = datetime.now(timezone.utc)
            try:
                provider = self.factory.get_search_provider(provider_name)
                all_results: list[SearchResult] = []

                for query in queries:
                    try:
                        results = await provider.search(query, num_results=results_per_query)
                        all_results.extend(results)
                    except Exception as e:
                        logger.warning(f"{provider_name} failed for query '{query[:30]}...': {e}")
                        # Continue with other queries

                await provider.close()

                completed = datetime.now(timezone.utc)
                return ProviderResult(
                    provider_name=provider_name,
                    provider_type=ProviderType.SEARCH,
                    status=ProviderStatus.COMPLETED,
                    data=[r.to_dict() for r in all_results],
                    started_at=started,
                    completed_at=completed,
                    execution_time_ms=int((completed - started).total_seconds() * 1000),
                    metadata={"total_results": len(all_results)},
                )

            except Exception as e:
                logger.error(f"Search provider {provider_name} failed: {e}")
                return ProviderResult(
                    provider_name=provider_name,
                    provider_type=ProviderType.SEARCH,
                    status=ProviderStatus.FAILED,
                    data=[],
                    error=str(e),
                    started_at=started,
                    completed_at=datetime.now(timezone.utc),
                )

        # Execute all search providers in parallel
        logger.info(f"Starting parallel search with providers: {search_providers}")
        tasks = [run_search_provider(name) for name in search_providers]
        results = await asyncio.gather(*tasks)

        # Log summary
        completed = sum(1 for r in results if r.status == ProviderStatus.COMPLETED)
        logger.info(f"Search complete: {completed}/{len(search_providers)} providers succeeded")

        return list(results)

    async def execute_scrape(
        self,
        urls: list[str],
        scrape_providers: list[str],
        max_concurrent: int = 5,
    ) -> list[ProviderResult]:
        """
        Execute scraping across multiple providers in parallel.

        Each provider scrapes all URLs independently.
        No deduplication - we keep all content for richer data.

        Args:
            urls: List of URLs to scrape
            scrape_providers: List of provider names (e.g., ["JINA_READER", "CRAWL4AI"])
            max_concurrent: Max concurrent requests per provider

        Returns:
            List of ProviderResult from each provider
        """

        async def run_scrape_provider(provider_name: str) -> ProviderResult:
            started = datetime.now(timezone.utc)
            try:
                provider = self.factory.get_scrape_provider(provider_name)
                pages = await provider.scrape_batch(urls, max_concurrent=max_concurrent)
                await provider.close()

                completed = datetime.now(timezone.utc)
                success_count = sum(1 for p in pages if p.status == "SUCCESS")

                return ProviderResult(
                    provider_name=provider_name,
                    provider_type=ProviderType.SCRAPE,
                    status=ProviderStatus.COMPLETED,
                    data=[p.to_dict() for p in pages],
                    started_at=started,
                    completed_at=completed,
                    execution_time_ms=int((completed - started).total_seconds() * 1000),
                    metadata={
                        "total_pages": len(pages),
                        "success_count": success_count,
                        "failed_count": len(pages) - success_count,
                    },
                )

            except Exception as e:
                logger.error(f"Scrape provider {provider_name} failed: {e}")
                return ProviderResult(
                    provider_name=provider_name,
                    provider_type=ProviderType.SCRAPE,
                    status=ProviderStatus.FAILED,
                    data=[],
                    error=str(e),
                    started_at=started,
                    completed_at=datetime.now(timezone.utc),
                )

        # Execute all scrape providers in parallel
        logger.info(f"Starting parallel scrape with providers: {scrape_providers}")
        tasks = [run_scrape_provider(name) for name in scrape_providers]
        results = await asyncio.gather(*tasks)

        # Log summary
        completed = sum(1 for r in results if r.status == ProviderStatus.COMPLETED)
        logger.info(f"Scrape complete: {completed}/{len(scrape_providers)} providers succeeded")

        return list(results)

    async def execute_full_pipeline(
        self,
        queries: list[str],
        search_providers: list[str],
        scrape_providers: list[str],
        results_per_query: int = 10,
        max_concurrent_scrape: int = 5,
    ) -> ParallelExecutionResult:
        """
        Execute full search + scrape pipeline with multiple providers.

        Flow:
        1. Run all search providers in parallel
        2. Collect ALL URLs (no dedup - different providers may yield different content)
        3. Run all scrape providers in parallel on all URLs
        4. Aggregate all scraped pages (no dedup - keep all content)

        Args:
            queries: Search queries
            search_providers: List of search provider names
            scrape_providers: List of scrape provider names
            results_per_query: Max results per query
            max_concurrent_scrape: Max concurrent scrape requests per provider

        Returns:
            ParallelExecutionResult with all collected data
        """
        start_time = datetime.now(timezone.utc)

        # Step 1: Parallel search
        self.on_progress("PARALLEL_SEARCH", 10)
        search_results = await self.execute_search(queries, search_providers, results_per_query)

        # Collect ALL URLs from all search providers (no dedup)
        all_urls: list[str] = []
        all_search_items: list[SearchResult] = []

        for result in search_results:
            if result.status == ProviderStatus.COMPLETED:
                for item in result.data:
                    url = item.get("url", "")
                    if url:
                        all_urls.append(url)
                        all_search_items.append(
                            SearchResult(
                                url=item.get("url", ""),
                                title=item.get("title", ""),
                                snippet=item.get("snippet", ""),
                                position=item.get("position", 0),
                                source_provider=item.get("source_provider", "unknown"),
                            )
                        )

        # Pre-filter: remove blogs, news, social media
        pre_filter_count = len(all_urls)
        all_urls = filter_urls(all_urls)
        if len(all_urls) < pre_filter_count:
            logger.info(
                f"URL pre-filter: {pre_filter_count} -> {len(all_urls)} "
                f"(removed {pre_filter_count - len(all_urls)} non-vendor URLs)"
            )

        # Limit URLs to balance between coverage and cost
        MAX_URLS = 20  # Reduced from 30 since we pre-filtered junk
        if len(all_urls) > MAX_URLS:
            logger.info(f"Limiting URLs from {len(all_urls)} to {MAX_URLS}")
            all_urls = all_urls[:MAX_URLS]

        logger.info(
            f"Search complete: {len(all_urls)} URLs from {len(search_providers)} providers "
            "(keeping all for richer content)"
        )

        if not all_urls:
            logger.warning("No URLs found from search, returning empty result")
            return ParallelExecutionResult(
                search_results=all_search_items,
                scraped_pages=[],
                provider_results=search_results,
                total_urls=0,
                unique_urls=0,
                total_pages_scraped=0,
                execution_time_ms=int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000),
            )

        # Step 2: Parallel scrape
        self.on_progress("PARALLEL_SCRAPE", 40)
        scrape_results = await self.execute_scrape(
            all_urls, scrape_providers, max_concurrent_scrape
        )

        # Aggregate scraped pages (keep ALL - no dedup)
        scraped_pages = self._aggregate_scraped_pages(scrape_results)

        end_time = datetime.now(timezone.utc)

        return ParallelExecutionResult(
            search_results=all_search_items,
            scraped_pages=scraped_pages,
            provider_results=search_results + scrape_results,
            total_urls=len(all_urls),
            unique_urls=len(set(all_urls)),
            total_pages_scraped=len([p for p in scraped_pages if p.status == "SUCCESS"]),
            execution_time_ms=int((end_time - start_time).total_seconds() * 1000),
        )

    def _aggregate_scraped_pages(self, results: list[ProviderResult]) -> list[ScrapedPage]:
        """
        Aggregate scraped pages from multiple providers.

        Strategy: Keep ALL pages from all providers (no dedup).
        Different providers may yield:
        - Different content quality (Jina = clean markdown, Crawl4AI = JS-rendered)
        - Different data extraction (one might capture pricing, another might capture features)
        - Redundancy for reliability (if one fails, others may succeed)

        LLM will process all content and extract the most complete vendor info.
        """
        aggregated: list[ScrapedPage] = []

        for result in results:
            if result.status == ProviderStatus.COMPLETED:
                for page_data in result.data:
                    page = ScrapedPage.from_dict(page_data)
                    if page.status == "SUCCESS" and page.content:
                        aggregated.append(page)

        logger.info(f"Aggregated {len(aggregated)} pages from all providers (no dedup)")
        return aggregated
