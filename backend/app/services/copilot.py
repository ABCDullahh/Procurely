"""Copilot service for AI-assisted vendor analysis."""

import json
import logging
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import (
    ProcurementRequest,
    SearchRun,
    Vendor,
    VendorFieldEvidence,
    VendorMetrics,
    VendorSource,
)
from app.schemas.copilot import (
    ChatRequest,
    ChatResponse,
    Citation,
    CopilotAction,
    CopilotContext,
)
from app.services.llm import GeminiProvider, LLMProvider, OpenAIProvider

logger = logging.getLogger(__name__)


class CopilotError(Exception):
    """Base copilot error."""

    pass


class ConfigMissingError(CopilotError):
    """API key or config missing."""

    pass


def build_copilot_context(
    db: Session,
    run_id: int,
    vendor_ids: list[int] | None = None,
) -> CopilotContext:
    """Build context for copilot from run data."""
    # Get run and request
    run = db.query(SearchRun).filter(SearchRun.id == run_id).first()
    if not run:
        raise ValueError(f"Run {run_id} not found")

    request = (
        db.query(ProcurementRequest)
        .filter(ProcurementRequest.id == run.request_id)
        .first()
    )
    if not request:
        raise ValueError(f"Request for run {run_id} not found")

    # Get vendor IDs from this run
    run_vendor_ids_query = (
        db.query(VendorSource.vendor_id)
        .filter(VendorSource.search_run_id == run_id)
        .distinct()
    )

    # Filter to specific vendors if provided
    if vendor_ids:
        run_vendor_ids_query = run_vendor_ids_query.filter(
            VendorSource.vendor_id.in_(vendor_ids)
        )

    run_vendor_ids = [r[0] for r in run_vendor_ids_query.all()]

    # Counts
    vendors_count = len(run_vendor_ids)
    sources_count = (
        db.query(func.count(VendorSource.id))
        .filter(VendorSource.search_run_id == run_id)
        .scalar()
        or 0
    )

    # Average score
    avg_score = (
        db.query(func.avg(VendorMetrics.overall_score))
        .filter(VendorMetrics.search_run_id == run_id)
        .scalar()
    )

    # Top 10 vendors by score
    top_vendors_query = (
        db.query(Vendor, VendorMetrics)
        .join(VendorMetrics, Vendor.id == VendorMetrics.vendor_id)
        .filter(VendorMetrics.search_run_id == run_id)
        .filter(VendorMetrics.overall_score.isnot(None))
    )
    if vendor_ids:
        top_vendors_query = top_vendors_query.filter(Vendor.id.in_(vendor_ids))

    top_vendors_query = (
        top_vendors_query.order_by(VendorMetrics.overall_score.desc()).limit(10).all()
    )

    top_vendors = []
    for vendor, metrics in top_vendors_query:
        top_vendors.append(
            {
                "id": vendor.id,
                "name": vendor.name,
                "website": vendor.website,
                "industry": vendor.industry,
                "location": vendor.location,
                "overall_score": metrics.overall_score,
                "fit_score": metrics.fit_score,
                "trust_score": metrics.trust_score,
            }
        )

    # Evidence snippets (max 2 per top vendor for important fields)
    evidence_snippets = []
    important_fields = ["pricing", "features", "compliance", "support", "integration"]

    for vendor_data in top_vendors[:5]:  # Top 5 vendors
        vendor_evidence = (
            db.query(VendorFieldEvidence)
            .filter(VendorFieldEvidence.vendor_id == vendor_data["id"])
            .filter(VendorFieldEvidence.field_name.in_(important_fields))
            .limit(2)
            .all()
        )
        for ev in vendor_evidence:
            # Get source URL
            source = (
                db.query(VendorSource)
                .filter(VendorSource.vendor_id == vendor_data["id"])
                .first()
            )
            evidence_snippets.append(
                {
                    "vendor_id": vendor_data["id"],
                    "vendor_name": vendor_data["name"],
                    "field": ev.field_name,
                    "snippet": ev.raw_excerpt[:300] if ev.raw_excerpt else "",
                    "source_url": source.source_url if source else "",
                }
            )

    # Parse criteria (handle both list and JSON string)
    must_have = request.must_have_criteria or []
    nice_to_have = request.nice_to_have_criteria or []
    if isinstance(must_have, str):
        try:
            must_have = json.loads(must_have)
        except json.JSONDecodeError:
            must_have = []
    if isinstance(nice_to_have, str):
        try:
            nice_to_have = json.loads(nice_to_have)
        except json.JSONDecodeError:
            nice_to_have = []

    return CopilotContext(
        request_title=request.title,
        request_description=request.description,
        request_category=request.category,
        request_location=request.location,
        request_budget_min=request.budget_min,
        request_budget_max=request.budget_max,
        request_timeline=request.timeline,
        must_have_criteria=must_have,
        nice_to_have_criteria=nice_to_have,
        run_status=run.status,
        run_progress=run.progress_pct,
        vendors_count=vendors_count,
        sources_count=sources_count,
        avg_overall_score=round(avg_score, 1) if avg_score else None,
        top_vendors=top_vendors,
        evidence_snippets=evidence_snippets,
    )


def build_copilot_prompt(context: CopilotContext, message: str, mode: str) -> str:
    """Build the LLM prompt with context."""
    vendors_text = ""
    for v in context.top_vendors:
        vendors_text += (
            f"- {v['name']} (Score: {v['overall_score']:.0f}, "
            f"Fit: {v.get('fit_score', 'N/A')}, Trust: {v.get('trust_score', 'N/A')}, "
            f"Industry: {v.get('industry', 'N/A')}, Location: {v.get('location', 'N/A')})\n"
        )

    evidence_text = ""
    for ev in context.evidence_snippets[:10]:
        evidence_text += (
            f"- {ev['vendor_name']} [{ev['field']}]: \"{ev['snippet'][:200]}...\" "
            f"(Source: {ev['source_url']})\n"
        )

    if mode == "insights":
        user_instruction = (
            "Generate a concise executive summary of the vendor search results. "
            "Highlight the top 3 vendors, key differentiators, potential risks, "
            "and recommended next steps."
        )
    else:
        user_instruction = message

    prompt = f"""You are a procurement AI assistant helping analyze vendor search results.

## Search Request
- Title: {context.request_title}
- Category: {context.request_category or 'N/A'}
- Location: {context.request_location or 'Any'}
- Budget: ${context.request_budget_min or 0:,} - ${context.request_budget_max or 0:,}
- Timeline: {context.request_timeline or 'N/A'}
- Must-have: {', '.join(context.must_have_criteria) or 'None'}
- Nice-to-have: {', '.join(context.nice_to_have_criteria) or 'None'}

## Search Results Summary
- Status: {context.run_status}
- Vendors Found: {context.vendors_count}
- Sources Scanned: {context.sources_count}
- Average Score: {context.avg_overall_score or 'N/A'}

## Top Vendors
{vendors_text or 'No vendors scored yet.'}

## Evidence Snippets
{evidence_text or 'No evidence available.'}

## User Question
{user_instruction}

## Instructions
1. Answer based ONLY on the context provided above.
2. If mentioning vendor facts, include the source URL as citation.
3. Be concise and actionable.
4. Suggest up to 2 relevant actions the user can take.

Respond with ONLY valid JSON in this exact format:
{{
  "answer": "Your answer here...",
  "citations": [
    {{
      "vendor_id": 123,
      "vendor_name": "Vendor Name",
      "source_url": "https://...",
      "snippet": "relevant quote",
      "field_name": "pricing"
    }}
  ],
  "suggested_actions": [
    {{
      "type": "OPEN_VENDOR",
      "label": "View top vendor details",
      "payload": {{"vendor_id": 123}}
    }}
  ]
}}

Valid action types: OPEN_VENDOR, COMPARE_TOP, CREATE_SHORTLIST, EXPORT_REPORT, OPEN_REPORTS
"""
    return prompt


def extract_json_from_response(text: str) -> dict[str, Any]:
    """Extract JSON from LLM response."""
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON in the text
    start_idx = text.find("{")
    end_idx = text.rfind("}") + 1
    if start_idx != -1 and end_idx > start_idx:
        try:
            return json.loads(text[start_idx:end_idx])
        except json.JSONDecodeError:
            pass

    # Return fallback
    return {
        "answer": text,
        "citations": [],
        "suggested_actions": [],
    }


async def run_copilot_chat(
    db: Session,
    run_id: int,
    payload: ChatRequest,
) -> ChatResponse:
    """Run copilot chat with LLM based on AI config settings."""
    from app.models.app_settings import AppSettings
    from app.services.errors import ConfigMissingError as KeyMissingError
    from app.services.keys import get_active_api_key_with_model

    def get_setting(key: str, default: str = "") -> str:
        setting = db.query(AppSettings).filter(AppSettings.key == key).first()
        return setting.value if setting else default

    # Build context
    context = build_copilot_context(db, run_id, payload.vendor_ids)

    # Build prompt
    prompt = build_copilot_prompt(context, payload.message, payload.mode)

    # Get configured LLM provider and model for Copilot
    llm_provider = get_setting("llm.copilot.provider", "GEMINI")
    llm_model = get_setting("llm.copilot.model", "")

    provider: LLMProvider
    provider_name = llm_provider
    model_used = llm_model

    # Create provider based on config (NO silent fallback)
    if llm_provider == "OPENAI":
        try:
            openai_key, default_model = get_active_api_key_with_model(db, "OPENAI")
            model_to_use = llm_model or default_model or "gpt-4o-mini"
            provider = OpenAIProvider(openai_key, default_model=model_to_use)
            model_used = model_to_use
            logger.info(f"Copilot using provider={provider_name} model={model_used}")
        except KeyMissingError:
            raise ConfigMissingError(
                "OPENAI API key not configured for Copilot. "
                "Go to Admin → API Keys to add OPENAI key, "
                "or change AI Config → Copilot LLM to use GEMINI."
            )
    elif llm_provider == "GEMINI":
        try:
            gemini_key, default_model = get_active_api_key_with_model(db, "GEMINI")
            model_to_use = llm_model or default_model or "gemini-2.5-flash"
            provider = GeminiProvider(gemini_key, default_model=model_to_use)
            model_used = model_to_use
            logger.info(f"Copilot using provider={provider_name} model={model_used}")
        except KeyMissingError:
            raise ConfigMissingError(
                "GEMINI API key not configured for Copilot. "
                "Go to Admin → API Keys to add GEMINI key, "
                "or change AI Config → Copilot LLM to use OPENAI."
            )
    else:
        raise ConfigMissingError(
            f"Unknown Copilot LLM provider '{llm_provider}'. "
            "Go to Admin → AI Configuration to select OPENAI or GEMINI."
        )

    # Call LLM with improved error handling
    try:
        llm_response = await provider.complete_text(prompt)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"LLM call failed: provider={provider_name} model={model_used} error={error_msg}")

        # Check for MAX_TOKENS / truncated response
        if "MAX_TOKENS" in error_msg or "max_tokens" in error_msg.lower():
            raise CopilotError(
                "Response was truncated (token limit hit). Try asking a shorter or more specific question."
            ) from e
        # Check for empty/missing parts (Gemini specific)
        elif "no parts" in error_msg.lower() or "empty text" in error_msg.lower():
            raise CopilotError(
                "AI returned an empty response. Try rephrasing your question or selecting a different model in Admin → API Keys."
            ) from e
        # Check for model not found errors
        elif "not found" in error_msg.lower() or "404" in error_msg:
            raise CopilotError(
                f"Model '{model_used}' not available. Go to Admin → API Keys → {provider_name} → "
                f"Fetch models and select a valid model."
            ) from e
        elif "401" in error_msg or "unauthorized" in error_msg.lower():
            raise CopilotError(
                f"API key for {provider_name} is invalid. Go to Admin → API Keys to update it."
            ) from e
        elif "429" in error_msg or "rate" in error_msg.lower():
            raise CopilotError(
                f"{provider_name} rate limit exceeded. Please wait a moment and try again."
            ) from e
        elif "safety" in error_msg.lower() or "blocked" in error_msg.lower():
            raise CopilotError(
                "Response was blocked by safety filters. Try rephrasing your question."
            ) from e
        else:
            raise CopilotError(
                f"AI service error: {error_msg[:200]}. Try again or check Admin → API Keys."
            ) from e

    # Extract text content from LLMResponse object
    # complete_text returns LLMResponse object, not string
    from app.services.llm.base import LLMResponse as LLMResponseType
    if isinstance(llm_response, LLMResponseType):
        response_text = llm_response.content
    elif isinstance(llm_response, str):
        response_text = llm_response
    else:
        logger.error(f"Unexpected response type: {type(llm_response)}")
        raise CopilotError(
            "Unexpected AI response format. Try again or check Admin → API Keys."
        )

    # Parse response
    result = extract_json_from_response(response_text)

    # Build citations
    citations = []
    for c in result.get("citations", []):
        citations.append(
            Citation(
                vendor_id=c.get("vendor_id"),
                vendor_name=c.get("vendor_name"),
                source_url=c.get("source_url", ""),
                snippet=c.get("snippet", ""),
                field_name=c.get("field_name"),
            )
        )

    # Build actions
    actions = []
    valid_types = {
        "OPEN_VENDOR",
        "COMPARE_TOP",
        "CREATE_SHORTLIST",
        "EXPORT_REPORT",
        "OPEN_REPORTS",
    }
    for a in result.get("suggested_actions", []):
        if a.get("type") in valid_types:
            actions.append(
                CopilotAction(
                    type=a["type"],
                    label=a.get("label", a["type"]),
                    payload=a.get("payload", {}),
                )
            )

    return ChatResponse(
        answer=result.get("answer", "I couldn't generate a response."),
        citations=citations,
        suggested_actions=actions,
    )
