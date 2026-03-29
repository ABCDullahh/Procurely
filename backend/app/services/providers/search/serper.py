"""Serper.dev search provider - Google Search API."""

import logging
from typing import Any

import httpx

from app.services.errors import (
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderResponseError,
    ProviderTimeoutError,
)
from app.services.providers.base import BaseSearchProvider, SearchResult
from app.services.providers.registry import register_search_provider

logger = logging.getLogger(__name__)

SERPER_API_URL = "https://google.serper.dev/search"


@register_search_provider("SERPER")
class SerperSearchProvider(BaseSearchProvider):
    """
    Serper.dev search provider - Google Search results.

    Features:
    - Real Google Search results
    - Fast response times
    - Multiple result types (organic, news, images)

    Docs: https://serper.dev/
    """

    provider_name = "SERPER"

    def __init__(self, api_key: str):
        """
        Initialize Serper provider.

        Args:
            api_key: Serper API key
        """
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            headers={
                "X-API-KEY": api_key,
                "Content-Type": "application/json",
            },
        )

    async def search(
        self,
        query: str,
        num_results: int = 10,
        **kwargs: Any,
    ) -> list[SearchResult]:
        """
        Perform Google search using Serper API.

        Args:
            query: Search query string
            num_results: Maximum results to return
            **kwargs:
                country: Country code (e.g., "us", "id")
                language: Language code (e.g., "en", "id")

        Returns:
            List of SearchResult objects
        """
        payload = {
            "q": query,
            "num": num_results,
            "hl": kwargs.get("language", "en"),
        }

        if "country" in kwargs:
            payload["gl"] = kwargs["country"]

        try:
            response = await self.client.post(
                SERPER_API_URL,
                json=payload,
                timeout=kwargs.get("timeout", 30.0),
            )

        except httpx.TimeoutException:
            raise ProviderTimeoutError(self.provider_name, 30.0)
        except httpx.RequestError as e:
            raise ProviderResponseError(self.provider_name, 0, str(e))

        if response.status_code in (401, 403):
            raise ProviderAuthError(self.provider_name, "Invalid API key")
        if response.status_code == 429:
            raise ProviderRateLimitError(self.provider_name, None)
        if response.status_code != 200:
            raise ProviderResponseError(
                self.provider_name,
                response.status_code,
                response.text[:500],
            )

        data = response.json()
        results: list[SearchResult] = []

        # Parse organic results
        for idx, item in enumerate(data.get("organic", [])):
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    position=idx + 1,
                    source_provider=self.provider_name,
                )
            )

        logger.info(f"Serper: found {len(results)} results for '{query[:50]}...'")
        return results

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()
