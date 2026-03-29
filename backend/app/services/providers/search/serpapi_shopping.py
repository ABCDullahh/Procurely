"""SerpAPI Google Shopping provider - pricing and product data."""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import httpx

from app.services.errors import (
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderResponseError,
    ProviderTimeoutError,
)
from app.services.providers.base import BaseSearchProvider, ProviderType, SearchResult
from app.services.providers.registry import register_search_provider

logger = logging.getLogger(__name__)

SERPAPI_URL = "https://serpapi.com/search"


@dataclass
class ShoppingProduct:
    """Product data from Google Shopping."""

    title: str
    price: float | None  # Price in local currency
    price_raw: str  # Original price string
    currency: str
    source: str  # Merchant/store name
    link: str  # Product page URL
    thumbnail: str | None
    rating: float | None
    reviews_count: int | None
    position: int
    extracted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "price": self.price,
            "price_raw": self.price_raw,
            "currency": self.currency,
            "source": self.source,
            "link": self.link,
            "thumbnail": self.thumbnail,
            "rating": self.rating,
            "reviews_count": self.reviews_count,
            "position": self.position,
            "extracted_at": self.extracted_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class ShoppingResult:
    """Aggregated shopping results for a vendor/product search."""

    query: str
    vendor_name: str | None
    products: list[ShoppingProduct]
    price_min: float | None
    price_max: float | None
    price_avg: float | None
    total_results: int
    search_info: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "vendor_name": self.vendor_name,
            "products": [p.to_dict() for p in self.products],
            "price_min": self.price_min,
            "price_max": self.price_max,
            "price_avg": self.price_avg,
            "total_results": self.total_results,
            "search_info": self.search_info,
        }


@register_search_provider("SERPAPI_SHOPPING")
class SerpAPIShoppingProvider(BaseSearchProvider):
    """
    SerpAPI Google Shopping provider for pricing data.

    Uses SerpAPI to search Google Shopping and extract:
    - Product prices from various merchants
    - Price ranges for vendor products
    - Product ratings and reviews
    - Merchant/source information

    Docs: https://serpapi.com/google-shopping-api
    """

    provider_name = "SERPAPI_SHOPPING"
    provider_type = ProviderType.SEARCH

    def __init__(self, api_key: str):
        """
        Initialize SerpAPI Shopping provider.

        Args:
            api_key: SerpAPI key
        """
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
        )

    async def search(
        self,
        query: str,
        num_results: int = 10,
        **kwargs: Any,
    ) -> list[SearchResult]:
        """
        Search Google Shopping for products.

        This implements the BaseSearchProvider interface,
        returning standard SearchResult objects. For rich
        shopping data, use search_shopping() instead.

        Args:
            query: Search query
            num_results: Maximum results
            **kwargs:
                country: Country code (default: "id" for Indonesia)
                location: Specific location for prices

        Returns:
            List of SearchResult objects
        """
        shopping_result = await self.search_shopping(
            query=query,
            vendor_name=None,
            num_results=num_results,
            **kwargs,
        )

        # Convert to standard SearchResult format
        results = []
        for product in shopping_result.products:
            results.append(
                SearchResult(
                    url=product.link,
                    title=f"{product.title} - {product.price_raw}",
                    snippet=f"From {product.source}. {product.price_raw}",
                    position=product.position,
                    source_provider=self.provider_name,
                )
            )

        return results

    async def search_shopping(
        self,
        query: str,
        vendor_name: str | None = None,
        num_results: int = 20,
        **kwargs: Any,
    ) -> ShoppingResult:
        """
        Search Google Shopping with full product/pricing data.

        Args:
            query: Search query
            vendor_name: Optional vendor name to extract from results
            num_results: Maximum number of products
            **kwargs:
                country: Country code (default: "id" for Indonesia)
                location: Specific location
                currency: Currency for prices

        Returns:
            ShoppingResult with products and price statistics
        """
        params = {
            "engine": "google_shopping",
            "q": query,
            "api_key": self.api_key,
            "num": min(num_results, 100),  # API max is 100
            "gl": kwargs.get("country", "id"),  # Default Indonesia
            "hl": kwargs.get("language", "id"),
        }

        if "location" in kwargs:
            params["location"] = kwargs["location"]

        try:
            response = await self.client.get(
                SERPAPI_URL,
                params=params,
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
        products = self._parse_shopping_results(data)

        # Calculate price statistics
        prices = [p.price for p in products if p.price is not None]
        price_min = min(prices) if prices else None
        price_max = max(prices) if prices else None
        price_avg = sum(prices) / len(prices) if prices else None

        result = ShoppingResult(
            query=query,
            vendor_name=vendor_name,
            products=products[:num_results],
            price_min=price_min,
            price_max=price_max,
            price_avg=price_avg,
            total_results=len(products),
            search_info=data.get("search_information", {}),
        )

        logger.info(
            f"SerpAPI Shopping: found {len(products)} products for '{query[:50]}', "
            f"price range: {price_min} - {price_max}"
        )

        return result

    def _parse_shopping_results(self, data: dict) -> list[ShoppingProduct]:
        """Parse SerpAPI response into ShoppingProduct objects."""
        products = []

        # Parse shopping_results array
        for idx, item in enumerate(data.get("shopping_results", [])):
            price_raw = item.get("price", "")
            price = self._extract_price(price_raw)
            currency = self._extract_currency(price_raw)

            product = ShoppingProduct(
                title=item.get("title", ""),
                price=price,
                price_raw=price_raw,
                currency=currency,
                source=item.get("source", "Unknown"),
                link=item.get("link", ""),
                thumbnail=item.get("thumbnail"),
                rating=item.get("rating"),
                reviews_count=item.get("reviews"),
                position=idx + 1,
                metadata={
                    "product_id": item.get("product_id"),
                    "extensions": item.get("extensions", []),
                    "delivery": item.get("delivery"),
                },
            )
            products.append(product)

        return products

    def _extract_price(self, price_str: str) -> float | None:
        """Extract numeric price from price string."""
        if not price_str:
            return None

        # Remove currency symbols and clean up
        import re

        # Match patterns like "Rp 1.234.567" or "$123.45" or "123,45"
        # Indonesian format uses . as thousand separator
        cleaned = re.sub(r"[^\d.,]", "", price_str)

        if not cleaned:
            return None

        # Handle Indonesian format (1.234.567)
        if cleaned.count(".") > 1:
            cleaned = cleaned.replace(".", "")
        elif "," in cleaned and "." in cleaned:
            # European format: 1.234,56
            cleaned = cleaned.replace(".", "").replace(",", ".")
        elif "," in cleaned:
            # Could be 1,234.56 or 1234,56
            if len(cleaned.split(",")[-1]) == 2:
                # Likely decimal comma
                cleaned = cleaned.replace(",", ".")
            else:
                # Thousand separator
                cleaned = cleaned.replace(",", "")

        try:
            return float(cleaned)
        except ValueError:
            return None

    def _extract_currency(self, price_str: str) -> str:
        """Extract currency from price string."""
        if not price_str:
            return "IDR"

        price_lower = price_str.lower()
        if "rp" in price_lower or "idr" in price_lower:
            return "IDR"
        elif "$" in price_str or "usd" in price_lower:
            return "USD"
        elif "€" in price_str or "eur" in price_lower:
            return "EUR"

        return "IDR"  # Default to IDR for Indonesia focus

    async def get_vendor_pricing(
        self,
        vendor_name: str,
        product_keywords: list[str],
        max_products_per_keyword: int = 5,
    ) -> dict:
        """
        Get pricing data for a specific vendor.

        Searches multiple product keywords and aggregates results
        to build a pricing profile for the vendor.

        Args:
            vendor_name: Name of the vendor
            product_keywords: List of product/category keywords
            max_products_per_keyword: Max products per search

        Returns:
            Dict with vendor pricing summary
        """
        all_products = []

        for keyword in product_keywords[:5]:  # Limit keywords to avoid rate limits
            query = f"{vendor_name} {keyword}"
            try:
                result = await self.search_shopping(
                    query=query,
                    vendor_name=vendor_name,
                    num_results=max_products_per_keyword,
                )
                all_products.extend(result.products)
            except Exception as e:
                logger.warning(f"Shopping search failed for '{query}': {e}")
                continue

        # Calculate overall statistics
        prices = [p.price for p in all_products if p.price is not None]

        return {
            "vendor_name": vendor_name,
            "products": [p.to_dict() for p in all_products],
            "total_products": len(all_products),
            "price_min": min(prices) if prices else None,
            "price_max": max(prices) if prices else None,
            "price_avg": sum(prices) / len(prices) if prices else None,
            "sources": list(set(p.source for p in all_products)),
        }

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()
