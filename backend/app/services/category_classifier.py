"""Category classifier for product vs service detection.

This module determines if a procurement category is product-based (physical goods)
or service-based (software, consulting, etc.). Product categories REQUIRE pricing
data from Google Shopping or marketplace APIs.
"""

import logging
from enum import Enum

logger = logging.getLogger(__name__)


class CategoryType(str, Enum):
    """Category type classification."""
    PRODUCT = "PRODUCT"  # Physical goods - pricing REQUIRED
    SERVICE = "SERVICE"  # Software, consulting - pricing optional
    MIXED = "MIXED"      # Could be either


# Product categories - physical goods that MUST have pricing
PRODUCT_KEYWORDS = {
    # Furniture (EN/ID)
    "furniture", "mebel", "meja", "kursi", "lemari", "rak", "sofa",
    "cabinet", "desk", "chair", "table", "shelving", "partisi",
    # Electronics
    "electronics", "elektronik", "laptop", "komputer", "computer",
    "printer", "monitor", "server", "networking", "switch", "router",
    "projector", "tv", "television", "speaker", "headphone",
    # Office supplies
    "atk", "alat tulis", "stationery", "office supplies", "kertas",
    "paper", "toner", "cartridge", "alat kantor",
    # Hardware
    "hardware", "perangkat keras", "spare part", "komponen",
    # Equipment / Machinery
    "equipment", "peralatan", "mesin", "machinery", "alat berat",
    "genset", "generator", "ac", "air conditioner", "cctv",
    # Construction materials
    "material", "bahan bangunan", "building materials", "semen",
    "besi", "keramik", "cat", "paint",
    # Vehicles
    "kendaraan", "vehicle", "mobil", "motor", "truck", "forklift",
    # Miscellaneous products
    "solar panel", "panel surya", "battery", "baterai", "ups",
}

# Service categories - may not have pricing
SERVICE_KEYWORDS = {
    # Software
    "software", "saas", "aplikasi", "application", "platform",
    "cloud", "hosting", "erp", "crm", "hris",
    # Consulting
    "consulting", "konsultan", "konsultasi", "advisory",
    # Training
    "training", "pelatihan", "sertifikasi", "certification",
    # IT Services
    "maintenance", "pemeliharaan", "support", "managed service",
    "outsourcing", "sistem informasi", "development", "integration",
    # Professional services
    "audit", "legal", "hukum", "akuntan", "accounting",
    "recruitment", "hr services", "security service",
}


def is_product_category(
    category: str | None,
    title: str | None = None,
    keywords: list[str] | None = None,
) -> bool:
    """
    Determine if a category represents physical products.

    Product categories REQUIRE pricing data from marketplace/shopping APIs.

    Args:
        category: Category name (e.g., "Furniture", "Software")
        title: Request title for additional context
        keywords: Request keywords

    Returns:
        True if category is product-based (requires pricing)
    """
    category_type = get_category_type(category, title, keywords)
    return category_type == CategoryType.PRODUCT


def get_category_type(
    category: str | None,
    title: str | None = None,
    keywords: list[str] | None = None,
) -> CategoryType:
    """
    Classify category as PRODUCT, SERVICE, or MIXED.

    Args:
        category: Category name
        title: Request title
        keywords: Request keywords

    Returns:
        CategoryType enum
    """
    # Combine all text for analysis
    text_parts = []
    if category:
        text_parts.append(category.lower())
    if title:
        text_parts.append(title.lower())
    if keywords:
        text_parts.extend([k.lower() for k in keywords])

    combined_text = " ".join(text_parts)

    # Count matches
    product_matches = sum(1 for kw in PRODUCT_KEYWORDS if kw in combined_text)
    service_matches = sum(1 for kw in SERVICE_KEYWORDS if kw in combined_text)

    logger.debug(
        f"Category analysis: product_matches={product_matches}, "
        f"service_matches={service_matches}, text='{combined_text[:50]}...'"
    )

    # Determine type
    if product_matches > 0 and service_matches == 0:
        return CategoryType.PRODUCT
    elif service_matches > 0 and product_matches == 0:
        return CategoryType.SERVICE
    elif product_matches > service_matches:
        return CategoryType.PRODUCT
    elif service_matches > product_matches:
        return CategoryType.SERVICE
    else:
        # Default to mixed when unclear
        return CategoryType.MIXED


def get_marketplace_queries(
    product_name: str,
    category: str | None = None,
    location: str | None = None,
) -> list[str]:
    """
    Generate marketplace-specific search queries for Indonesian e-commerce.

    Args:
        product_name: Product to search for
        category: Optional category for context
        location: Optional location (e.g., "Jakarta")

    Returns:
        List of search queries optimized for marketplace pricing
    """
    queries = []

    # Clean product name
    product = product_name.strip()

    # Indonesian marketplace queries
    marketplaces = ["tokopedia", "shopee", "bukalapak", "blibli"]

    for mp in marketplaces:
        queries.append(f"{product} harga {mp}")

    # Price-focused queries
    queries.extend([
        f"{product} harga terbaru",
        f"{product} price list",
        f"jual {product} murah",
        f"beli {product} online",
    ])

    # Add location if provided
    if location:
        queries.append(f"{product} {location} harga")

    # Add category context
    if category:
        queries.append(f"{product} {category.lower()} harga")

    return queries


def requires_shopping_search(
    category: str | None,
    title: str | None = None,
    keywords: list[str] | None = None,
) -> tuple[bool, str]:
    """
    Determine if shopping/marketplace search is required for this request.

    Returns:
        Tuple of (required: bool, reason: str)
    """
    category_type = get_category_type(category, title, keywords)

    if category_type == CategoryType.PRODUCT:
        return True, "Product category - marketplace pricing required"
    elif category_type == CategoryType.MIXED:
        return True, "Mixed category - marketplace pricing recommended"
    else:
        return False, "Service category - pricing from vendor website sufficient"
