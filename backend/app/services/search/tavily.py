"""Tavily search provider for AI-optimized web search."""

import logging
from typing import Any

import httpx

from app.services.errors import (
    ProviderAuthError,
    ProviderError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)
from app.services.search.base import SearchProvider, SearchResult

logger = logging.getLogger(__name__)


class TavilyProvider(SearchProvider):
    """Tavily AI Search API provider.
    
    Tavily is optimized for RAG and AI applications, providing
    cleaner, more relevant results for LLM context building.
    """

    def __init__(self, api_key: str):
        """Initialize with Tavily API key."""
        self.api_key = api_key
        self.base_url = "https://api.tavily.com"
        self.client = httpx.AsyncClient(timeout=30.0)

    async def search(
        self,
        query: str,
        num_results: int = 10,
        **kwargs: Any,
    ) -> list[SearchResult]:
        """
        Search using Tavily AI Search API.

        Args:
            query: Search query string
            num_results: Maximum results to return
            **kwargs: Additional parameters (search_depth, include_domains, etc.)

        Returns:
            List of SearchResult objects
        """
        try:
            # Tavily search endpoint
            response = await self.client.post(
                f"{self.base_url}/search",
                json={
                    "api_key": self.api_key,
                    "query": query,
                    "max_results": num_results,
                    "search_depth": kwargs.get("search_depth", "advanced"),
                    "include_answer": False,
                    "include_raw_content": False,
                },
            )

            if response.status_code == 401:
                raise ProviderAuthError("TAVILY", "Invalid API key")
            elif response.status_code == 429:
                raise ProviderRateLimitError("TAVILY", "Rate limit exceeded")
            elif response.status_code >= 400:
                raise ProviderError(
                    "TAVILY",
                    f"API error: {response.status_code} - {response.text[:200]}",
                )

            data = response.json()
            results = []

            for idx, item in enumerate(data.get("results", [])):
                results.append(
                    SearchResult(
                        url=item.get("url", ""),
                        title=item.get("title", ""),
                        snippet=item.get("content", ""),
                        position=idx + 1,
                        source_type="tavily",
                    )
                )

            logger.info(f"Tavily search returned {len(results)} results for: {query[:50]}")
            return results

        except httpx.TimeoutException as e:
            raise ProviderTimeoutError("TAVILY") from e
        except httpx.RequestError as e:
            raise ProviderError("TAVILY", f"Request failed: {str(e)}") from e

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
