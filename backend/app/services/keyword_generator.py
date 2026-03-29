"""Keyword generation service for procurement requests."""

import json
import logging
import re

from sqlalchemy.orm import Session

from app.services.errors import ConfigMissingError
from app.services.keys import get_active_api_key
from app.services.llm.base import LLMConfig
from app.services.llm.openai import OpenAIProvider
from app.services.llm.gemini import GeminiProvider

logger = logging.getLogger(__name__)

KEYWORD_EXTRACTION_PROMPT = """Extract 3-5 relevant search keywords from this procurement request.

Title: {title}
Description: {description}
Category: {category}

Guidelines:
- Extract the most important product/service terms
- Include both specific and general terms
- Include relevant Indonesian terms if the context suggests Indonesia
- Focus on searchable terms that would find vendors
- Return ONLY a JSON array of strings, no explanation

Example output: ["office furniture", "meja kantor", "ergonomic desk", "standing desk"]

Keywords:"""


async def generate_keywords_from_text(
    db: Session,
    title: str,
    description: str | None,
    category: str,
) -> list[str]:
    """
    Use LLM to extract relevant search keywords from title and description.

    Args:
        db: Database session
        title: Request title
        description: Optional description
        category: Product/service category

    Returns:
        List of 3-5 keywords
    """
    # Get LLM provider
    provider = await _get_llm_provider(db)
    if not provider:
        # Fallback: simple keyword extraction without LLM
        return _extract_keywords_simple(title, description, category)

    try:
        prompt = KEYWORD_EXTRACTION_PROMPT.format(
            title=title,
            description=description or "Not provided",
            category=category,
        )

        response = await provider.complete_text(
            prompt=prompt,
            config=LLMConfig(
                model=provider.get_default_model(),
                temperature=0.9,
                max_tokens=100000,
                timeout_seconds=120,
            ),
        )

        # Parse JSON response
        keywords = _parse_keywords_response(response.content)

        if keywords:
            logger.info(f"Generated {len(keywords)} keywords for '{title}'")
            return keywords[:5]  # Max 5 keywords

    except Exception as e:
        logger.warning(f"LLM keyword generation failed: {e}")

    # Fallback to simple extraction
    return _extract_keywords_simple(title, description, category)


async def _get_llm_provider(db: Session):
    """Get available LLM provider (OpenAI or Gemini)."""
    # Try OpenAI first
    try:
        api_key = get_active_api_key(db, "OPENAI")
        return OpenAIProvider(api_key=api_key)
    except ConfigMissingError:
        pass

    # Try Gemini as fallback
    try:
        api_key = get_active_api_key(db, "GEMINI")
        return GeminiProvider(api_key=api_key)
    except ConfigMissingError:
        pass

    logger.warning("No LLM provider available for keyword generation")
    return None


def _parse_keywords_response(response: str) -> list[str]:
    """Parse LLM response to extract keywords list."""
    # Try to find JSON array in response
    try:
        # Look for array pattern
        match = re.search(r'\[([^\]]+)\]', response)
        if match:
            array_str = f"[{match.group(1)}]"
            keywords = json.loads(array_str)
            if isinstance(keywords, list):
                return [str(k).strip() for k in keywords if k]
    except json.JSONDecodeError:
        pass

    # Fallback: split by common delimiters
    lines = response.strip().split('\n')
    keywords = []
    for line in lines:
        # Remove bullet points, numbers, etc.
        clean = re.sub(r'^[\s\-\*\d\.]+', '', line).strip()
        clean = clean.strip('"\'')
        if clean and len(clean) > 1:
            keywords.append(clean)

    return keywords[:5]


def _extract_keywords_simple(
    title: str,
    description: str | None,
    category: str,
) -> list[str]:
    """
    Simple keyword extraction without LLM.
    Extracts significant words from title and description.
    """
    # Combine text
    text = f"{title} {description or ''} {category}".lower()

    # Common stop words
    stop_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
        "be", "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "must", "shall", "can", "need",
        "yang", "dan", "atau", "untuk", "dengan", "dari", "ke", "di", "ini",
        "itu", "adalah", "akan", "sudah", "juga", "saya", "kami", "kita",
    }

    # Extract words
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text)

    # Filter and deduplicate
    seen = set()
    keywords = []
    for word in words:
        if word not in stop_words and word not in seen:
            seen.add(word)
            keywords.append(word)

    # Return first 5 significant words
    return keywords[:5] if keywords else [category.lower()]
