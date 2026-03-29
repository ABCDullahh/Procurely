"""Shopping search step - fetches pricing data from Google Shopping and marketplaces."""

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from sqlalchemy.orm import Session

from app.services.errors import ConfigMissingError
from app.services.keys import get_active_api_key
from app.services.providers.search.serpapi_shopping import (
    SerpAPIShoppingProvider,
    ShoppingProduct,
)

logger = logging.getLogger(__name__)


# Indonesian marketplace-specific query patterns for better price discovery
MARKETPLACE_QUERY_PATTERNS = [
    "{vendor} {keyword} harga",  # Direct price query
    "{vendor} {keyword} tokopedia",  # Tokopedia
    "{vendor} {keyword} shopee",  # Shopee
    "{vendor} {keyword} bukalapak",  # Bukalapak
    "{keyword} indonesia harga",  # Generic Indonesian price
]


class ShoppingSearchStatus(str, Enum):
    """Status of shopping search operation."""
    SUCCESS = "SUCCESS"  # Found pricing data
    NO_API_KEY = "NO_API_KEY"  # SerpAPI not configured
    NO_RESULTS = "NO_RESULTS"  # Search worked but no prices found
    PARTIAL = "PARTIAL"  # Some vendors have pricing, some don't
    API_ERROR = "API_ERROR"  # API call failed


@dataclass
class VendorPricing:
    """Pricing data for a vendor."""

    vendor_name: str
    products: list[ShoppingProduct]
    price_min: float | None
    price_max: float | None
    price_avg: float | None
    market_avg: float | None  # Average across all vendors for comparison
    price_competitiveness: float  # 0-100 score
    sources: list[str]
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "vendor_name": self.vendor_name,
            "products": [p.to_dict() for p in self.products],
            "price_min": self.price_min,
            "price_max": self.price_max,
            "price_avg": self.price_avg,
            "market_avg": self.market_avg,
            "price_competitiveness": self.price_competitiveness,
            "sources": self.sources,
            "metadata": self.metadata,
        }


@dataclass
class ShoppingSearchResult:
    """Result from shopping search step."""

    status: ShoppingSearchStatus
    status_message: str | None
    vendor_pricing: dict[str, VendorPricing]  # vendor_name -> pricing
    category_pricing: dict[str, dict]  # category -> price stats
    market_avg: float | None
    total_products: int
    search_queries: list[str]
    errors: list[str]

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "status_message": self.status_message,
            "vendor_pricing": {
                k: v.to_dict() for k, v in self.vendor_pricing.items()
            },
            "category_pricing": self.category_pricing,
            "market_avg": self.market_avg,
            "total_products": self.total_products,
            "search_queries": self.search_queries,
            "errors": self.errors,
        }


async def search_shopping_prices(
    db: Session,
    vendor_names: list[str],
    product_keywords: list[str],
    category: str | None = None,
    max_products_per_vendor: int = 10,
) -> ShoppingSearchResult:
    """
    Search Google Shopping for vendor pricing data.

    This step:
    1. For each vendor, searches Google Shopping with product keywords
    2. Collects pricing data from multiple merchants
    3. Calculates price ranges and market averages
    4. Generates price competitiveness scores

    Args:
        db: Database session
        vendor_names: List of vendor names to search for
        product_keywords: Product/category keywords to include
        category: Category name for context
        max_products_per_vendor: Max products to fetch per vendor

    Returns:
        ShoppingSearchResult with pricing data
    """
    # Get SerpAPI key
    try:
        api_key = get_active_api_key(db, "SERPAPI")
    except ConfigMissingError:
        logger.warning(
            "SERPAPI key not configured, skipping shopping search. "
            "Product pricing will rely on LLM extraction only."
        )
        return ShoppingSearchResult(
            status=ShoppingSearchStatus.NO_API_KEY,
            status_message=(
                "Google Shopping API (SerpAPI) not configured. "
                "Add SERPAPI key in Admin > API Keys for marketplace pricing."
            ),
            vendor_pricing={},
            category_pricing={},
            market_avg=None,
            total_products=0,
            search_queries=[],
            errors=["SERPAPI key not configured"],
        )

    provider = SerpAPIShoppingProvider(api_key=api_key)
    vendor_pricing: dict[str, VendorPricing] = {}
    all_products: list[ShoppingProduct] = []
    search_queries: list[str] = []
    errors: list[str] = []

    try:
        # Search for each vendor
        tasks = []
        for vendor_name in vendor_names[:10]:  # Limit to 10 vendors
            tasks.append(
                _search_vendor_products(
                    provider=provider,
                    vendor_name=vendor_name,
                    keywords=product_keywords,
                    max_products=max_products_per_vendor,
                )
            )

        # Execute concurrently with rate limiting
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for vendor_name, result in zip(vendor_names[:10], results):
            if isinstance(result, Exception):
                errors.append(f"{vendor_name}: {str(result)}")
                continue

            products, queries = result
            if products:
                all_products.extend(products)
                search_queries.extend(queries)

                # Calculate vendor pricing
                prices = [p.price for p in products if p.price is not None]
                vendor_pricing[vendor_name] = VendorPricing(
                    vendor_name=vendor_name,
                    products=products,
                    price_min=min(prices) if prices else None,
                    price_max=max(prices) if prices else None,
                    price_avg=sum(prices) / len(prices) if prices else None,
                    market_avg=None,  # Will be set after all vendors processed
                    price_competitiveness=50.0,  # Will be recalculated
                    sources=list(set(p.source for p in products)),
                )

        # Calculate market average
        all_prices = [p.price for p in all_products if p.price is not None]
        market_avg = sum(all_prices) / len(all_prices) if all_prices else None

        # Update competitiveness scores
        if market_avg:
            for vp in vendor_pricing.values():
                vp.market_avg = market_avg
                if vp.price_avg:
                    # Score based on how vendor compares to market
                    # Lower price = higher score
                    ratio = vp.price_avg / market_avg
                    if ratio < 0.8:
                        vp.price_competitiveness = 90.0  # Very competitive
                    elif ratio < 0.95:
                        vp.price_competitiveness = 75.0  # Competitive
                    elif ratio < 1.05:
                        vp.price_competitiveness = 50.0  # Average
                    elif ratio < 1.2:
                        vp.price_competitiveness = 35.0  # Above market
                    else:
                        vp.price_competitiveness = 20.0  # Premium pricing

        # Build category pricing summary
        category_pricing = {}
        if category and all_products:
            category_pricing[category] = {
                "min": min(all_prices) if all_prices else None,
                "max": max(all_prices) if all_prices else None,
                "avg": market_avg,
                "sample_size": len(all_prices),
            }

        # Determine status
        if len(vendor_pricing) == 0:
            status = ShoppingSearchStatus.NO_RESULTS
            status_message = "No pricing data found from Google Shopping"
        elif len(vendor_pricing) < len(vendor_names[:10]):
            status = ShoppingSearchStatus.PARTIAL
            status_message = f"Found pricing for {len(vendor_pricing)}/{min(len(vendor_names), 10)} vendors"
        else:
            status = ShoppingSearchStatus.SUCCESS
            status_message = f"Found pricing for {len(vendor_pricing)} vendors"

        logger.info(f"Shopping search completed: {status.value} - {status_message}")

        return ShoppingSearchResult(
            status=status,
            status_message=status_message,
            vendor_pricing=vendor_pricing,
            category_pricing=category_pricing,
            market_avg=market_avg,
            total_products=len(all_products),
            search_queries=list(set(search_queries)),
            errors=errors,
        )

    finally:
        await provider.close()


async def _search_vendor_products(
    provider: SerpAPIShoppingProvider,
    vendor_name: str,
    keywords: list[str],
    max_products: int,
) -> tuple[list[ShoppingProduct], list[str]]:
    """
    Search products for a single vendor.

    Args:
        provider: SerpAPI provider instance
        vendor_name: Vendor name to search
        keywords: Product keywords
        max_products: Maximum products to return

    Returns:
        Tuple of (products, queries used)
    """
    all_products = []
    queries = []

    # Try vendor name + each keyword
    for keyword in keywords[:3]:  # Limit to 3 keywords per vendor
        query = f"{vendor_name} {keyword}"
        queries.append(query)

        try:
            result = await provider.search_shopping(
                query=query,
                vendor_name=vendor_name,
                num_results=max_products // 3 + 1,
            )
            all_products.extend(result.products)
        except Exception as e:
            logger.warning(f"Shopping search failed for '{query}': {e}")

        # Small delay to avoid rate limiting
        await asyncio.sleep(0.2)

    # Deduplicate by link
    seen_links = set()
    unique_products = []
    for p in all_products:
        if p.link not in seen_links:
            seen_links.add(p.link)
            unique_products.append(p)

    return unique_products[:max_products], queries


async def get_category_price_benchmark(
    db: Session,
    category: str,
    sample_keywords: list[str],
) -> dict[str, Any]:
    """
    Get price benchmarks for a category.

    Searches without vendor names to establish market pricing baseline.

    Args:
        db: Database session
        category: Category name
        sample_keywords: Sample product keywords

    Returns:
        Dict with category pricing benchmarks
    """
    try:
        api_key = get_active_api_key(db, "SERPAPI")
    except ConfigMissingError:
        return {"error": "SERPAPI key not configured"}

    provider = SerpAPIShoppingProvider(api_key=api_key)
    all_products = []

    try:
        for keyword in sample_keywords[:3]:
            query = f"{category} {keyword}"
            try:
                result = await provider.search_shopping(
                    query=query,
                    num_results=20,
                )
                all_products.extend(result.products)
            except Exception as e:
                logger.warning(f"Category benchmark search failed: {e}")
            await asyncio.sleep(0.2)

        prices = [p.price for p in all_products if p.price is not None]

        return {
            "category": category,
            "price_min": min(prices) if prices else None,
            "price_max": max(prices) if prices else None,
            "price_avg": sum(prices) / len(prices) if prices else None,
            "price_median": sorted(prices)[len(prices) // 2] if prices else None,
            "sample_size": len(prices),
            "sources": list(set(p.source for p in all_products)),
        }

    finally:
        await provider.close()
