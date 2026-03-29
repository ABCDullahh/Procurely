"""Indonesia-focused query expansion step - adds Indonesian vendor focus to searches."""

import logging
from typing import Optional

from app.services.llm.base import LLMConfig, LLMProvider

logger = logging.getLogger(__name__)

# Major Indonesian cities for location-based searches
INDONESIA_CITIES = [
    "Jakarta",
    "Surabaya",
    "Bandung",
    "Medan",
    "Semarang",
    "Makassar",
    "Tangerang",
    "Bekasi",
    "Depok",
    "Palembang",
]

# Common Indonesian business terms
INDONESIA_TERMS = {
    "vendor": ["vendor", "penyedia", "supplier", "pemasok", "distributor", "importir", "agen resmi"],
    "company": ["perusahaan", "PT", "CV", "UD", "produsen", "grosir", "toko"],
    "service": ["jasa", "layanan", "service"],
    "product": ["produk", "barang", "komoditas", "katalog produk", "harga grosir"],
    "marketplace": ["tokopedia seller", "bukalapak", "indotrading", "ralali"],
    "directory": ["daftar supplier", "direktori vendor", "daftar perusahaan"],
}

INDONESIA_EXPAND_PROMPT = (
    "You are a procurement research assistant specializing in Indonesian vendors. "
    "Given a vendor search request, generate {num_queries} diverse search queries "
    "specifically focused on finding Indonesian vendors and suppliers.\n\n"
    "Request Details:\n"
    "- Title: {title}\n"
    "- Description: {description}\n"
    "- Category: {category}\n"
    "- Keywords: {keywords}\n"
    "- Must-have criteria: {must_have}\n"
    "- Nice-to-have criteria: {nice_to_have}\n"
    "- Preferred Location: {location}\n\n"
    "Generate {num_queries} search queries that:\n"
    "1. Target Indonesian companies (use 'Indonesia', 'Jakarta', major cities)\n"
    "2. Use Indonesian business terms (PT, vendor, penyedia, supplier, distributor, importir, produsen, grosir, toko, agen resmi)\n"
    "3. Include '.co.id', '.id' domain hints where relevant\n"
    "4. Mix English and Indonesian keywords\n"
    "5. Look for industry associations and directories in Indonesia\n"
    "6. Search for local representatives of international vendors\n"
    "7. Target Indonesian B2B marketplaces and directories (indotrading, ralali, tokopedia seller, bukalapak)\n"
    "8. Use Indonesian procurement terms: 'daftar supplier', 'katalog produk', 'harga grosir'\n\n"
    "Example query patterns:\n"
    "- '[category] vendor Indonesia Jakarta'\n"
    "- 'PT [category] supplier Surabaya'\n"
    "- 'penyedia jasa [category] Indonesia'\n"
    "- '[category] site:.co.id OR site:.id'\n"
    "- 'daftar perusahaan [category] Indonesia'\n"
    "- 'distributor [category] Indonesia harga grosir'\n"
    "- '[category] indotrading OR ralali supplier'\n"
    "- 'importir [category] Jakarta agen resmi'\n"
    "- 'daftar supplier [category] Indonesia katalog produk'\n\n"
    'Return as a JSON object: {{"queries": ["query1", "query2", ...]}}'
)


async def expand_queries_indonesia(
    llm: LLMProvider,
    title: str,
    description: str,
    category: str,
    keywords: list[str],
    must_have: list[str],
    nice_to_have: list[str],
    location: Optional[str] = None,
    num_queries: int = 8,
) -> list[str]:
    """
    Generate Indonesia-focused search queries from procurement request.

    This generates queries specifically targeting Indonesian vendors,
    using Indonesian business terms and location modifiers.

    Args:
        llm: LLM provider for generation
        title: Request title
        description: Request description
        category: Product/service category
        keywords: List of keywords
        must_have: Required criteria
        nice_to_have: Optional criteria
        location: Preferred location (city/region)
        num_queries: Number of queries to generate

    Returns:
        List of Indonesia-focused search query strings
    """
    prompt = INDONESIA_EXPAND_PROMPT.format(
        title=title,
        description=description,
        category=category,
        keywords=", ".join(keywords) if keywords else "none",
        must_have=", ".join(must_have) if must_have else "none",
        nice_to_have=", ".join(nice_to_have) if nice_to_have else "none",
        location=location or "Indonesia (any city)",
        num_queries=num_queries,
    )

    result = await llm.extract_json(
        prompt,
        schema_hint='{"queries": ["string"]}',
        config=LLMConfig(
            model=llm.get_default_model(),
            temperature=0.7,
            max_tokens=100000,
            timeout_seconds=180,
        ),
    )

    queries = result.get("queries", [])
    logger.info(f"Generated {len(queries)} Indonesia-focused search queries")
    return queries[:num_queries]


def add_indonesia_modifiers(
    base_queries: list[str],
    location: Optional[str] = None,
    max_additional: int = 5,
) -> list[str]:
    """
    Add Indonesia-specific modifiers to existing queries.

    This takes base queries and creates additional Indonesia-focused
    variations without using an LLM.

    Args:
        base_queries: Original search queries
        location: Specific location preference
        max_additional: Maximum additional queries to add

    Returns:
        List of modified queries with Indonesia focus
    """
    indonesia_queries = []
    location_term = location or "Indonesia"

    for query in base_queries[:3]:  # Take top 3 base queries
        # Add location modifier
        indonesia_queries.append(f"{query} {location_term}")

        # Add Indonesian domain hint
        indonesia_queries.append(f"{query} site:.co.id OR site:.id")

        # Add vendor/supplier terms
        indonesia_queries.append(f"vendor {query} Indonesia")

    # Add general Indonesian business directory searches
    if base_queries:
        first_query = base_queries[0]
        indonesia_queries.extend([
            f"daftar perusahaan {first_query} Indonesia",
            f"PT supplier {first_query} Jakarta Surabaya",
            f"distributor {first_query} Indonesia indotrading OR ralali",
            f"daftar supplier {first_query} Indonesia katalog produk harga grosir",
        ])

    return indonesia_queries[:max_additional]


async def expand_with_indonesia_focus(
    llm: LLMProvider,
    title: str,
    description: str,
    category: str,
    keywords: list[str],
    must_have: list[str],
    nice_to_have: list[str],
    location: Optional[str] = None,
    region_bias: bool = True,
    num_base_queries: int = 5,
    num_indonesia_queries: int = 5,
) -> list[str]:
    """
    Combine base queries with Indonesia-focused queries.

    This generates both general queries and Indonesia-specific queries,
    then combines them for comprehensive vendor search.

    Args:
        llm: LLM provider
        title: Request title
        description: Request description
        category: Product/service category
        keywords: List of keywords
        must_have: Required criteria
        nice_to_have: Optional criteria
        location: Preferred location
        region_bias: If True, prioritize Indonesia queries
        num_base_queries: Number of general queries
        num_indonesia_queries: Number of Indonesia-specific queries

    Returns:
        Combined list of search queries
    """
    from app.services.pipeline.steps.expand import expand_queries

    # Generate base queries
    base_queries = await expand_queries(
        llm=llm,
        title=title,
        description=description,
        category=category,
        keywords=keywords,
        must_have=must_have,
        nice_to_have=nice_to_have,
        num_queries=num_base_queries,
    )

    # Generate Indonesia-focused queries
    indonesia_queries = await expand_queries_indonesia(
        llm=llm,
        title=title,
        description=description,
        category=category,
        keywords=keywords,
        must_have=must_have,
        nice_to_have=nice_to_have,
        location=location,
        num_queries=num_indonesia_queries,
    )

    # Combine with region bias preference
    if region_bias:
        # Put Indonesia queries first
        all_queries = indonesia_queries + base_queries
    else:
        # Interleave for balanced coverage
        all_queries = []
        for i in range(max(len(base_queries), len(indonesia_queries))):
            if i < len(base_queries):
                all_queries.append(base_queries[i])
            if i < len(indonesia_queries):
                all_queries.append(indonesia_queries[i])

    # Deduplicate while preserving order
    seen = set()
    unique_queries = []
    for q in all_queries:
        q_lower = q.lower()
        if q_lower not in seen:
            seen.add(q_lower)
            unique_queries.append(q)

    logger.info(
        f"Combined {len(unique_queries)} queries "
        f"({len(base_queries)} base + {len(indonesia_queries)} Indonesia-focused)"
    )

    return unique_queries
