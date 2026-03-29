"""Web search step - searches for vendors using SearchProvider."""

import logging
from dataclasses import dataclass

from app.services.search.base import SearchConfig, SearchProvider, SearchResult

logger = logging.getLogger(__name__)


@dataclass
class SearchSummary:
    """Summary of search results."""

    query: str
    results: list[SearchResult]
    total_found: int


async def search_web(
    search_provider: SearchProvider,
    queries: list[str],
    results_per_query: int = 10,
    country: str | None = None,
) -> list[SearchSummary]:
    """
    Execute web searches for all queries.

    Args:
        search_provider: Search provider to use
        queries: List of search queries
        results_per_query: Number of results per query
        country: Optional country code for localized results

    Returns:
        List of SearchSummary objects with results for each query
    """
    summaries: list[SearchSummary] = []

    for query in queries:
        try:
            results = await search_provider.search(
                query,
                config=SearchConfig(
                    num_results=results_per_query,
                    country=country,
                ),
            )
            summaries.append(
                SearchSummary(
                    query=query,
                    results=results,
                    total_found=len(results),
                )
            )
            logger.info(f"Query '{query[:50]}...' returned {len(results)} results")
        except Exception as e:
            logger.error(f"Search failed for query '{query[:50]}...': {e}")
            summaries.append(
                SearchSummary(query=query, results=[], total_found=0)
            )

    total_results = sum(s.total_found for s in summaries)
    logger.info(f"Completed {len(queries)} searches with {total_results} total results")
    return summaries


def dedupe_urls(summaries: list[SearchSummary]) -> list[str]:
    """
    Extract unique URLs from search results.

    Args:
        summaries: List of search summaries

    Returns:
        List of unique URLs to fetch
    """
    seen_urls: set[str] = set()
    unique_urls: list[str] = []

    for summary in summaries:
        for result in summary.results:
            url = result.url.strip().rstrip("/")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_urls.append(result.url)

    logger.info(f"Deduplicated to {len(unique_urls)} unique URLs")
    return unique_urls
