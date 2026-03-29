"""Query expansion step - generates search variations using LLM."""

import logging
from dataclasses import dataclass

from app.services.llm.base import LLMConfig, LLMProvider

logger = logging.getLogger(__name__)


@dataclass
class ExpandResult:
    """Result of query expansion with token tracking."""
    queries: list[str]
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    model: str = ""

# noqa: E501 - Line length exceptions for prompt templates
EXPAND_PROMPT = (
    "You are a procurement research assistant. Given a vendor search request, "
    "generate {num_queries} diverse search queries to find relevant vendors.\n\n"
    "Request Details:\n"
    "- Title: {title}\n"
    "- Description: {description}\n"
    "- Category: {category}\n"
    "- Keywords: {keywords}\n"
    "- Must-have criteria: {must_have}\n"
    "- Nice-to-have criteria: {nice_to_have}\n\n"
    "Generate {num_queries} search engine queries that will help find vendors "
    "matching these requirements. Each query should approach the search from "
    "a different angle:\n"
    "1. Direct product/service searches\n"
    "2. Industry + category searches\n"
    "3. Location-specific if relevant\n"
    "4. Competitor/alternative searches\n"
    "5. Review/comparison searches\n\n"
    "IMPORTANT RULES:\n"
    "1. Focus queries on finding ACTUAL VENDOR/SUPPLIER WEBSITES — not blog posts, reviews, or news articles\n"
    "2. Include company-specific terms: \"vendor\", \"supplier\", \"provider\", \"company\", \"PT\" (for Indonesia)\n"
    "3. Include purchase-intent terms: \"buy\", \"order\", \"pricing\", \"quote\", \"contact sales\"\n"
    "4. Include B2B directory terms: \"vendor directory\", \"supplier list\", \"B2B marketplace\"\n"
    "5. At least 2 queries should target specific vendor homepages (e.g., \"best [product] vendor [location]\")\n"
    "6. At least 1 query should target B2B platforms or directories\n\n"
    'Return as a JSON object: {{"queries": ["query1", "query2", ...]}}'
)


async def expand_queries(
    llm: LLMProvider,
    title: str,
    description: str,
    category: str,
    keywords: list[str],
    must_have: list[str],
    nice_to_have: list[str],
    num_queries: int = 5,
) -> list[str]:
    """
    Generate diverse search queries from procurement request.

    Args:
        llm: LLM provider for generation
        title: Request title
        description: Request description
        category: Product/service category
        keywords: List of keywords
        must_have: Required criteria
        nice_to_have: Optional criteria
        num_queries: Number of queries to generate

    Returns:
        List of search query strings
    """
    prompt = EXPAND_PROMPT.format(
        title=title,
        description=description,
        category=category,
        keywords=", ".join(keywords) if keywords else "none",
        must_have=", ".join(must_have) if must_have else "none",
        nice_to_have=", ".join(nice_to_have) if nice_to_have else "none",
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
    logger.info(f"Generated {len(queries)} search queries")
    return queries[:num_queries]


async def expand_queries_with_tracking(
    llm: LLMProvider,
    title: str,
    description: str,
    category: str,
    keywords: list[str],
    must_have: list[str],
    nice_to_have: list[str],
    num_queries: int = 5,
) -> ExpandResult:
    """
    Generate diverse search queries with token tracking.

    Args:
        llm: LLM provider for generation
        title: Request title
        description: Request description
        category: Product/service category
        keywords: List of keywords
        must_have: Required criteria
        nice_to_have: Optional criteria
        num_queries: Number of queries to generate

    Returns:
        ExpandResult with queries and token usage
    """
    prompt = EXPAND_PROMPT.format(
        title=title,
        description=description,
        category=category,
        keywords=", ".join(keywords) if keywords else "none",
        must_have=", ".join(must_have) if must_have else "none",
        nice_to_have=", ".join(nice_to_have) if nice_to_have else "none",
        num_queries=num_queries,
    )

    llm_result = await llm.extract_json_with_tokens(
        prompt,
        schema_hint='{"queries": ["string"]}',
        config=LLMConfig(
            model=llm.get_default_model(),
            temperature=0.7,
            max_tokens=100000,
            timeout_seconds=180,
        ),
    )

    queries = llm_result.data.get("queries", [])
    logger.info(f"Generated {len(queries)} search queries ({llm_result.total_tokens} tokens)")

    return ExpandResult(
        queries=queries[:num_queries],
        prompt_tokens=llm_result.prompt_tokens,
        completion_tokens=llm_result.completion_tokens,
        total_tokens=llm_result.total_tokens,
        model=llm_result.model,
    )
