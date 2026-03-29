"""Tavily search provider - AI-optimized web search."""

import logging
from typing import Any

import httpx

from app.services.errors import (
    ProviderAuthError,
    ProviderError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)
from app.services.providers.base import BaseSearchProvider, SearchResult
from app.services.providers.registry import register_search_provider

logger = logging.getLogger(__name__)


@register_search_provider("TAVILY")
class TavilySearchProvider(BaseSearchProvider):
    """
    Tavily AI Search API provider.

    Tavily is optimized for RAG and AI applications, providing
    cleaner, more relevant results for LLM context building.

    Features:
    - AI-optimized results
    - Clean content extraction
    - Advanced search depth options

    Docs: https://docs.tavily.com/
    """

    provider_name = "TAVILY"

    def __init__(self, api_key: str):
        """
        Initialize Tavily provider.

        Args:
            api_key: Tavily API key
        """
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
            **kwargs:
                search_depth: "basic" or "advanced" (default: "advanced")
                include_domains: List of domains to include
                exclude_domains: List of domains to exclude

        Returns:
            List of SearchResult objects
        """
        try:
            payload = {
                "api_key": self.api_key,
                "query": query,
                "max_results": num_results,
                "search_depth": kwargs.get("search_depth", "advanced"),
                "include_answer": False,
                "include_raw_content": False,
            }

            if "include_domains" in kwargs:
                payload["include_domains"] = kwargs["include_domains"]
            if "exclude_domains" in kwargs:
                payload["exclude_domains"] = kwargs["exclude_domains"]

            response = await self.client.post(
                f"{self.base_url}/search",
                json=payload,
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
            results: list[SearchResult] = []

            for idx, item in enumerate(data.get("results", [])):
                results.append(
                    SearchResult(
                        url=item.get("url", ""),
                        title=item.get("title", ""),
                        snippet=item.get("content", ""),
                        position=idx + 1,
                        source_provider=self.provider_name,
                    )
                )

            logger.info(f"Tavily: found {len(results)} results for '{query[:50]}...'")
            return results

        except httpx.TimeoutException:
            raise ProviderTimeoutError("TAVILY", 30.0)
        except httpx.RequestError as e:
            raise ProviderError("TAVILY", f"Request failed: {str(e)}")

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()
