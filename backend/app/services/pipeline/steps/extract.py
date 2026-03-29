"""Vendor extraction step - extracts vendor info from page content using LLM."""

import logging
import re
from dataclasses import dataclass, field
from typing import Callable

from app.services.errors import ProviderTokenLimitError
from app.services.llm.base import LLMConfig, LLMProvider
from app.services.pipeline.steps.fetch import FetchedPage
from app.services.providers.base import ScrapedPage

logger = logging.getLogger(__name__)


@dataclass
class TokenUsage:
    """Token usage statistics."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    calls: int = 0
    model: str = ""


@dataclass
class ExtractionResult:
    """Result of extraction with token usage."""
    vendors: list["ExtractedVendor"] = field(default_factory=list)
    token_usage: TokenUsage = field(default_factory=TokenUsage)
    pages_processed: int = 0
    pages_failed: int = 0

# Content size limits (characters) - tunable constants
CONTENT_MAX_CHARS_INITIAL = 60000  # First attempt: smaller to avoid MAX_TOKENS
CONTENT_MAX_CHARS_RETRY = 30000   # Retry with even smaller if MAX_TOKENS
CONTENT_KEYWORDS = [
    # Pricing keywords (highest priority)
    "pricing", "price", "cost", "harga", "rp", "idr", "$", "usd",
    "plan", "subscription", "per unit", "per pcs", "mulai dari", "starting",
    # Security
    "security", "compliance", "soc2", "iso27001", "gdpr", "hipaa",
    # Technical
    "integrate", "api", "cloud", "saas", "on-premise",
    # Contact
    "support", "sla", "contact", "demo", "trial",
    # Company
    "about", "team", "founded", "employee", "headquarter",
]

# Prompt template for procurement-grade extraction
EXTRACT_PROMPT = """You are analyzing a web page to extract vendor information for a procurement search.

Page URL: {url}
Page Title: {title}
Page Content (truncated):
{content}

Search Context:
- Looking for: {category}
- Requirements: {requirements}

TASK: Extract comprehensive vendor information for procurement evaluation.
If a field is not found, set it to null. Be thorough but accurate.

Return JSON with this EXACT structure:
{{
  "is_vendor": true/false,
  "vendor": {{
    "name": "Company name",
    "website": "Main website URL",
    "description": "2-3 sentence summary of what they do",
    "industry": "Primary industry/sector",
    "location": "HQ city and region",
    "country": "Country",
    "founded_year": 2015,
    "employee_count": "50-200 or 1000+",
    "email": "Contact email",
    "phone": "Contact phone",
    "pricing_model": "subscription/usage-based/one-time/per-unit/contact-sales",
    "pricing_details": "IMPORTANT: Extract actual numeric prices! Examples: 'Rp 2.500.000/unit', '$500/month', 'Starting from Rp 1jt'. If no price found, write 'Contact for pricing'",
    "price_range_min": "Lowest price found as number (e.g. 2500000)",
    "price_range_max": "Highest price found as number",
    "price_currency": "IDR/USD/EUR",
    "security_compliance": "SOC2, ISO27001, GDPR, HIPAA etc. if mentioned",
    "deployment": "cloud/on-premise/hybrid",
    "integrations": "Key integrations (CRM, Slack, APIs)",
    "target_segment": "SMB/mid-market/enterprise",
    "regions_served": "Global/US/APAC/specific countries",
    "use_cases": ["Use case 1", "Use case 2"],
    "key_features": ["Feature 1", "Feature 2", "Feature 3"],
    "differentiators": ["What makes them unique"],
    "limitations": ["Any noted limitations or red flags"],
    "notable_customers": ["Customer 1", "Customer 2"],
    "support_channels": "Email, chat, phone, dedicated CSM",
    "onboarding_time": "Days/weeks if mentioned",
    "contract_terms": "Monthly/annual, cancellation notes",
    "data_hosting": "AWS/GCP/Azure, regions",
    "sso_saml": true/false/null
  }},
  "evidence": [
    {{
      "field": "field_name",
      "label": "Human Readable Field Name",
      "category": "summary|pricing|security|company|features|implementation",
      "value": "extracted value",
      "snippet": "exact quoted text from page supporting this",
      "confidence": 0.95
    }}
  ]
}}

EVIDENCE GUIDELINES:
- Include evidence for EVERY field you extract (where text exists)
- category values: summary, pricing, security, company, features, implementation
- confidence: 0.9-1.0 for direct quotes, 0.6-0.8 for inferred, 0.3-0.5 for uncertain
- snippet should be the EXACT text from the page (max 200 chars)

If this is NOT a vendor page (news article, directory listing), return:
{{"is_vendor": false, "vendor": null, "evidence": []}}"""

# Batch extraction constants
BATCH_SIZE = 3  # Number of pages per LLM call
BATCH_CONTENT_MAX_CHARS = 20000  # Per-page char limit within a batch (smaller to fit 3 pages)

EXTRACT_BATCH_PROMPT = """You are analyzing {n} web pages to extract vendor information for a procurement search.

For EACH page below, extract vendor information independently.
Return a JSON array with one entry per page — even pages that are NOT vendor pages.

Search Context:
- Looking for: {category}
- Requirements: {requirements}

{pages_content}

TASK: For EACH page above, extract comprehensive vendor information for procurement evaluation.
If a field is not found, set it to null. Be thorough but accurate.

Return a JSON array with EXACTLY {n} entries, one per page, in the SAME order as above.
Each entry must have this EXACT structure:
{{
  "page_url": "the URL of this page",
  "is_vendor": true/false,
  "vendor": {{
    "name": "Company name",
    "website": "Main website URL",
    "description": "2-3 sentence summary of what they do",
    "industry": "Primary industry/sector",
    "location": "HQ city and region",
    "country": "Country",
    "founded_year": 2015,
    "employee_count": "50-200 or 1000+",
    "email": "Contact email",
    "phone": "Contact phone",
    "pricing_model": "subscription/usage-based/one-time/per-unit/contact-sales",
    "pricing_details": "IMPORTANT: Extract actual numeric prices! Examples: 'Rp 2.500.000/unit', '$500/month', 'Starting from Rp 1jt'. If no price found, write 'Contact for pricing'",
    "price_range_min": "Lowest price found as number (e.g. 2500000)",
    "price_range_max": "Highest price found as number",
    "price_currency": "IDR/USD/EUR",
    "security_compliance": "SOC2, ISO27001, GDPR, HIPAA etc. if mentioned",
    "deployment": "cloud/on-premise/hybrid",
    "integrations": "Key integrations (CRM, Slack, APIs)",
    "target_segment": "SMB/mid-market/enterprise",
    "regions_served": "Global/US/APAC/specific countries",
    "use_cases": ["Use case 1", "Use case 2"],
    "key_features": ["Feature 1", "Feature 2", "Feature 3"],
    "differentiators": ["What makes them unique"],
    "limitations": ["Any noted limitations or red flags"],
    "notable_customers": ["Customer 1", "Customer 2"],
    "support_channels": "Email, chat, phone, dedicated CSM",
    "onboarding_time": "Days/weeks if mentioned",
    "contract_terms": "Monthly/annual, cancellation notes",
    "data_hosting": "AWS/GCP/Azure, regions",
    "sso_saml": true/false/null
  }},
  "evidence": [
    {{
      "field": "field_name",
      "label": "Human Readable Field Name",
      "category": "summary|pricing|security|company|features|implementation",
      "value": "extracted value",
      "snippet": "exact quoted text from page supporting this",
      "confidence": 0.95
    }}
  ]
}}

EVIDENCE GUIDELINES:
- Include evidence for EVERY field you extract (where text exists)
- category values: summary, pricing, security, company, features, implementation
- confidence: 0.9-1.0 for direct quotes, 0.6-0.8 for inferred, 0.3-0.5 for uncertain
- snippet should be the EXACT text from the page (max 200 chars)

For pages that are NOT vendor pages (news article, directory listing), return:
{{"page_url": "...", "is_vendor": false, "vendor": null, "evidence": []}}"""


def truncate_content_smart(content: str, max_chars: int) -> str:
    """
    Truncate content intelligently for LLM extraction.
    
    Strategy:
    1. Normalize whitespace
    2. Prioritize sections with procurement-relevant keywords
    3. Keep head + keyword sections + tail if too long
    """
    if not content:
        return ""

    # Normalize whitespace
    content = re.sub(r'\s+', ' ', content).strip()

    if len(content) <= max_chars:
        return content

    # Find keyword-rich sections
    sentences = re.split(r'[.!?\n]+', content)
    scored_sentences = []

    for i, sentence in enumerate(sentences):
        score = sum(1 for kw in CONTENT_KEYWORDS if kw.lower() in sentence.lower())
        scored_sentences.append((i, sentence, score))

    # Sort by score descending, then by position
    scored_sentences.sort(key=lambda x: (-x[2], x[0]))

    # Build result: always include first 3 sentences (intro)
    result_sentences = sentences[:3] if len(sentences) >= 3 else sentences[:]
    result_length = sum(len(s) for s in result_sentences)

    # Add high-scoring sentences until limit
    for idx, sentence, score in scored_sentences:
        if idx < 3:  # Already included
            continue
        if result_length + len(sentence) + 2 > max_chars * 0.9:
            break
        result_sentences.append(sentence)
        result_length += len(sentence) + 2

    # Add last 2 sentences if room
    if len(sentences) > 5 and result_length < max_chars * 0.85:
        result_sentences.extend(sentences[-2:])

    result = ". ".join(result_sentences)
    return result[:max_chars]


@dataclass
class ExtractedVendor:
    """Extracted vendor with evidence."""

    name: str
    source_url: str
    source_title: str | None
    data: dict
    evidence: list[dict]
    extraction_error: str | None = None  # Track partial extraction issues


async def extract_vendors(
    llm: LLMProvider,
    pages: list[FetchedPage],
    category: str,
    requirements: list[str],
) -> list[ExtractedVendor]:
    """
    Extract vendor information from fetched pages.

    Args:
        llm: LLM provider for extraction
        pages: List of fetched pages
        category: Product/service category
        requirements: Search requirements

    Returns:
        List of extracted vendors
    
    Notes:
        - Per-URL failures do NOT kill the entire run
        - Token limit errors trigger retry with smaller content
        - Partial results are still returned
    """
    vendors: list[ExtractedVendor] = []
    failed_urls = 0
    total_urls = len([p for p in pages if p.status == "SUCCESS" and p.content])

    for page in pages:
        if page.status != "SUCCESS" or not page.content:
            continue

        extraction_error = None
        content_limit = CONTENT_MAX_CHARS_INITIAL
        retry_count = 0
        max_retries = 1  # Retry once with smaller content on token limit

        while retry_count <= max_retries:
            try:
                truncated_content = truncate_content_smart(page.content, content_limit)

                prompt = EXTRACT_PROMPT.format(
                    url=page.url,
                    title=page.title or "Unknown",
                    content=truncated_content,
                    category=category,
                    requirements=", ".join(requirements) if requirements else "none",
                )

                result = await llm.extract_json(
                    prompt,
                    config=LLMConfig(
                        model=llm.get_default_model(),
                        temperature=0.1,
                        max_tokens=100000,  # Slightly higher for richer schema
                    ),
                )

                if result.get("is_vendor") and result.get("vendor"):
                    vendor_data = result["vendor"]
                    if vendor_data.get("name"):
                        vendors.append(
                            ExtractedVendor(
                                name=vendor_data["name"],
                                source_url=page.url,
                                source_title=page.title,
                                data=vendor_data,
                                evidence=result.get("evidence", []),
                                extraction_error=extraction_error,
                            )
                        )
                        logger.info(
                            f"Extracted vendor: {vendor_data['name']} from {page.url}"
                        )
                break  # Success - exit retry loop

            except ProviderTokenLimitError as e:
                retry_count += 1
                if retry_count <= max_retries:
                    logger.warning(
                        f"Token limit hit for {page.url}, retrying with smaller content "
                        f"({content_limit} -> {CONTENT_MAX_CHARS_RETRY} chars)"
                    )
                    content_limit = CONTENT_MAX_CHARS_RETRY
                    extraction_error = "token_limit_reduced"
                else:
                    failed_urls += 1
                    logger.warning(f"Failed to extract from {page.url} after retry: {e}")
                    break

            except Exception as e:
                failed_urls += 1
                logger.warning(f"Failed to extract from {page.url}: {e}")
                break

    # Log summary
    success_count = len(vendors)
    logger.info(
        f"Extraction complete: {success_count} vendors from {total_urls} pages "
        f"({failed_urls} failed)"
    )

    # Only fail the run if ALL URLs failed
    if total_urls > 0 and failed_urls == total_urls:
        logger.error("All URL extractions failed - run may have configuration issues")

    return vendors


async def extract_vendors_from_pages(
    llm: LLMProvider,
    pages: list[ScrapedPage],
    category: str,
    requirements: list[str],
) -> list[ExtractedVendor]:
    """
    Extract vendor information from scraped pages (new provider system).

    Args:
        llm: LLM provider for extraction
        pages: List of ScrapedPage from multi-provider system
        category: Product/service category
        requirements: Search requirements

    Returns:
        List of extracted vendors

    Notes:
        - Per-URL failures do NOT kill the entire run
        - Token limit errors trigger retry with smaller content
        - Partial results are still returned
        - This function works with the new ScrapedPage type from providers
    """
    result = await extract_vendors_with_tracking(llm, pages, category, requirements)
    return result.vendors


async def extract_vendors_with_tracking(
    llm: LLMProvider,
    pages: list[ScrapedPage],
    category: str,
    requirements: list[str],
    log_callback: Callable[[str, str, str, dict | None], None] | None = None,
) -> ExtractionResult:
    """
    Extract vendor information from scraped pages with token tracking.

    Args:
        llm: LLM provider for extraction
        pages: List of ScrapedPage from multi-provider system
        category: Product/service category
        requirements: Search requirements
        log_callback: Optional callback for logging (step, level, message, data)

    Returns:
        ExtractionResult with vendors and token usage
    """
    vendors: list[ExtractedVendor] = []
    token_usage = TokenUsage(model=llm.get_default_model())
    failed_urls = 0
    total_urls = len([p for p in pages if p.status == "SUCCESS" and p.content])

    def log(level: str, message: str, data: dict | None = None):
        if log_callback:
            log_callback("EXTRACT", level, message, data)
        log_fn = getattr(logger, level, logger.info)
        log_fn(message)

    log("info", f"Starting extraction from {total_urls} pages", {
        "total_pages": len(pages),
        "valid_pages": total_urls,
        "category": category,
    })

    # Filter to valid pages only
    valid_pages = [p for p in pages if p.status == "SUCCESS" and p.content]

    # Batch pages into groups of BATCH_SIZE for fewer LLM calls
    batches = [valid_pages[i:i + BATCH_SIZE] for i in range(0, len(valid_pages), BATCH_SIZE)]

    log("info", f"Processing {len(valid_pages)} pages in {len(batches)} batches (batch_size={BATCH_SIZE})", {
        "batch_count": len(batches),
        "batch_size": BATCH_SIZE,
    })

    for batch_idx, batch in enumerate(batches):
        if len(batch) == 1:
            # Single page — use original single-page prompt (more efficient)
            page = batch[0]
            extraction_error = None
            content_limit = CONTENT_MAX_CHARS_INITIAL
            retry_count = 0
            max_retries = 1

            log("debug", f"Batch {batch_idx + 1}/{len(batches)}: single page {page.url[:80]}...", {
                "url": page.url,
                "provider": page.source_provider,
                "content_length": len(page.content),
            })

            while retry_count <= max_retries:
                try:
                    truncated_content = truncate_content_smart(page.content, content_limit)

                    prompt = EXTRACT_PROMPT.format(
                        url=page.url,
                        title=page.title or "Unknown",
                        content=truncated_content,
                        category=category,
                        requirements=", ".join(requirements) if requirements else "none",
                    )

                    llm_result = await llm.extract_json_with_tokens(
                        prompt,
                        config=LLMConfig(
                            model=llm.get_default_model(),
                            temperature=0.1,
                            max_tokens=100000,
                        ),
                    )

                    token_usage.prompt_tokens += llm_result.prompt_tokens
                    token_usage.completion_tokens += llm_result.completion_tokens
                    token_usage.total_tokens += llm_result.total_tokens
                    token_usage.calls += 1

                    result = llm_result.data

                    if result.get("is_vendor") and result.get("vendor"):
                        vendor_data = result["vendor"]
                        if vendor_data.get("name"):
                            vendors.append(
                                ExtractedVendor(
                                    name=vendor_data["name"],
                                    source_url=page.url,
                                    source_title=page.title,
                                    data=vendor_data,
                                    evidence=result.get("evidence", []),
                                    extraction_error=extraction_error,
                                )
                            )
                            log("info", f"Extracted vendor: {vendor_data['name']}", {
                                "vendor_name": vendor_data["name"],
                                "url": page.url,
                                "provider": page.source_provider,
                                "tokens_used": llm_result.total_tokens,
                            })
                    else:
                        log("debug", f"No vendor found on page: {page.url[:60]}...", {
                            "url": page.url,
                            "is_vendor": result.get("is_vendor"),
                        })
                    break  # Success

                except ProviderTokenLimitError as e:
                    retry_count += 1
                    if retry_count <= max_retries:
                        log("warning", f"Token limit hit, retrying with smaller content", {
                            "url": page.url,
                            "old_limit": content_limit,
                            "new_limit": CONTENT_MAX_CHARS_RETRY,
                        })
                        content_limit = CONTENT_MAX_CHARS_RETRY
                        extraction_error = "token_limit_reduced"
                    else:
                        failed_urls += 1
                        log("error", f"Failed after retry: {str(e)[:100]}", {
                            "url": page.url, "error": str(e),
                        })
                        break

                except Exception as e:
                    failed_urls += 1
                    log("error", f"Extraction failed: {str(e)[:100]}", {
                        "url": page.url, "error": str(e),
                        "error_type": type(e).__name__,
                    })
                    break

        else:
            # Multi-page batch — use batch prompt to save LLM calls
            batch_urls = [p.url for p in batch]
            log("debug", f"Batch {batch_idx + 1}/{len(batches)}: {len(batch)} pages", {
                "urls": [u[:80] for u in batch_urls],
            })

            # Build combined pages content
            pages_content_parts = []
            for i, page in enumerate(batch):
                truncated = truncate_content_smart(page.content, BATCH_CONTENT_MAX_CHARS)
                pages_content_parts.append(
                    f"--- PAGE {i + 1} ---\n"
                    f"URL: {page.url}\n"
                    f"Title: {page.title or 'Unknown'}\n"
                    f"Content:\n{truncated}\n"
                    f"--- END PAGE {i + 1} ---"
                )
            pages_content = "\n\n".join(pages_content_parts)

            retry_count = 0
            max_retries = 1
            content_limit = BATCH_CONTENT_MAX_CHARS

            while retry_count <= max_retries:
                try:
                    # Rebuild pages content if retrying with smaller limit
                    if retry_count > 0:
                        pages_content_parts = []
                        for i, page in enumerate(batch):
                            truncated = truncate_content_smart(page.content, content_limit)
                            pages_content_parts.append(
                                f"--- PAGE {i + 1} ---\n"
                                f"URL: {page.url}\n"
                                f"Title: {page.title or 'Unknown'}\n"
                                f"Content:\n{truncated}\n"
                                f"--- END PAGE {i + 1} ---"
                            )
                        pages_content = "\n\n".join(pages_content_parts)

                    prompt = EXTRACT_BATCH_PROMPT.format(
                        n=len(batch),
                        category=category,
                        requirements=", ".join(requirements) if requirements else "none",
                        pages_content=pages_content,
                    )

                    llm_result = await llm.extract_json_with_tokens(
                        prompt,
                        config=LLMConfig(
                            model=llm.get_default_model(),
                            temperature=0.1,
                            max_tokens=100000,
                        ),
                    )

                    token_usage.prompt_tokens += llm_result.prompt_tokens
                    token_usage.completion_tokens += llm_result.completion_tokens
                    token_usage.total_tokens += llm_result.total_tokens
                    token_usage.calls += 1

                    result_data = llm_result.data

                    # Handle response: could be a list or a dict with a list
                    results_list = []
                    if isinstance(result_data, list):
                        results_list = result_data
                    elif isinstance(result_data, dict):
                        # LLM might wrap in {"results": [...]} or {"vendors": [...]}
                        for key in ("results", "vendors", "pages", "data"):
                            if isinstance(result_data.get(key), list):
                                results_list = result_data[key]
                                break
                        if not results_list:
                            # Single result wrapped in dict — treat as single
                            results_list = [result_data]

                    # Process each result, matching back to pages
                    for i, page in enumerate(batch):
                        if i < len(results_list):
                            entry = results_list[i]
                        else:
                            log("warning", f"Batch result missing entry for page {i+1}: {page.url[:60]}")
                            failed_urls += 1
                            continue

                        if entry.get("is_vendor") and entry.get("vendor"):
                            vendor_data = entry["vendor"]
                            if vendor_data.get("name"):
                                vendors.append(
                                    ExtractedVendor(
                                        name=vendor_data["name"],
                                        source_url=page.url,
                                        source_title=page.title,
                                        data=vendor_data,
                                        evidence=entry.get("evidence", []),
                                        extraction_error=None,
                                    )
                                )
                                log("info", f"Extracted vendor: {vendor_data['name']} (batch)", {
                                    "vendor_name": vendor_data["name"],
                                    "url": page.url,
                                    "provider": page.source_provider,
                                    "batch_idx": batch_idx,
                                })
                        else:
                            log("debug", f"No vendor found on page (batch): {page.url[:60]}...", {
                                "url": page.url,
                                "is_vendor": entry.get("is_vendor"),
                            })

                    break  # Success

                except ProviderTokenLimitError as e:
                    retry_count += 1
                    if retry_count <= max_retries:
                        # Reduce per-page content limit and retry
                        content_limit = BATCH_CONTENT_MAX_CHARS // 2
                        log("warning", f"Token limit hit on batch, retrying with smaller content", {
                            "batch_urls": [u[:60] for u in batch_urls],
                            "new_limit": content_limit,
                        })
                    else:
                        # Fall back to single-page extraction for this batch
                        log("warning", f"Batch extraction failed after retry, falling back to single-page", {
                            "batch_urls": [u[:60] for u in batch_urls],
                            "error": str(e)[:100],
                        })
                        for page in batch:
                            try:
                                truncated_content = truncate_content_smart(page.content, CONTENT_MAX_CHARS_RETRY)
                                prompt = EXTRACT_PROMPT.format(
                                    url=page.url,
                                    title=page.title or "Unknown",
                                    content=truncated_content,
                                    category=category,
                                    requirements=", ".join(requirements) if requirements else "none",
                                )
                                fallback_result = await llm.extract_json_with_tokens(
                                    prompt,
                                    config=LLMConfig(
                                        model=llm.get_default_model(),
                                        temperature=0.1,
                                        max_tokens=100000,
                                    ),
                                )
                                token_usage.prompt_tokens += fallback_result.prompt_tokens
                                token_usage.completion_tokens += fallback_result.completion_tokens
                                token_usage.total_tokens += fallback_result.total_tokens
                                token_usage.calls += 1

                                r = fallback_result.data
                                if r.get("is_vendor") and r.get("vendor"):
                                    vd = r["vendor"]
                                    if vd.get("name"):
                                        vendors.append(
                                            ExtractedVendor(
                                                name=vd["name"],
                                                source_url=page.url,
                                                source_title=page.title,
                                                data=vd,
                                                evidence=r.get("evidence", []),
                                                extraction_error="batch_fallback",
                                            )
                                        )
                                        log("info", f"Extracted vendor (fallback): {vd['name']}", {
                                            "vendor_name": vd["name"],
                                            "url": page.url,
                                        })
                            except Exception as fallback_err:
                                failed_urls += 1
                                log("error", f"Fallback extraction failed: {str(fallback_err)[:100]}", {
                                    "url": page.url,
                                })
                        break

                except Exception as e:
                    failed_urls += len(batch)
                    log("error", f"Batch extraction failed: {str(e)[:100]}", {
                        "batch_urls": [u[:60] for u in batch_urls],
                        "error": str(e),
                        "error_type": type(e).__name__,
                    })
                    break

    # Log summary
    log("info", f"Extraction complete: {len(vendors)} vendors extracted", {
        "vendors_found": len(vendors),
        "pages_processed": total_urls,
        "pages_failed": failed_urls,
        "total_tokens": token_usage.total_tokens,
        "prompt_tokens": token_usage.prompt_tokens,
        "completion_tokens": token_usage.completion_tokens,
        "llm_calls": token_usage.calls,
        "batches_used": len(batches),
    })

    return ExtractionResult(
        vendors=vendors,
        token_usage=token_usage,
        pages_processed=total_urls,
        pages_failed=failed_urls,
    )

