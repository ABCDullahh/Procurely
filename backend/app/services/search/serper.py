"""Serper.dev search provider implementation."""

import logging

import httpx

from app.services.errors import (
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderResponseError,
    ProviderTimeoutError,
)
from app.services.search.base import SearchConfig, SearchProvider, SearchResult

logger = logging.getLogger(__name__)

SERPER_API_URL = "https://google.serper.dev/search"


class SerperProvider(SearchProvider):
    """Serper.dev search provider using httpx."""

    provider_name = "SEARCH_PROVIDER"

    def __init__(self, api_key: str):
        """Initialize with API key."""
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
        config: SearchConfig | None = None,
    ) -> list[SearchResult]:
        """Perform web search using Serper API."""
        cfg = config or self.get_default_config()

        payload = {
            "q": query,
            "num": cfg.num_results,
            "hl": cfg.language,
        }
        if cfg.country:
            payload["gl"] = cfg.country

        try:
            response = await self.client.post(
                SERPER_API_URL,
                json=payload,
                timeout=cfg.timeout_seconds,
            )
        except httpx.TimeoutException:
            raise ProviderTimeoutError(self.provider_name, cfg.timeout_seconds)
        except httpx.RequestError as e:
            raise ProviderResponseError(self.provider_name, 0, str(e))

        if response.status_code == 401 or response.status_code == 403:
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
                    source_type="SEARCH_RESULT",
                )
            )

        return results

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
