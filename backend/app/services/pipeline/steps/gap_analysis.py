"""Gap analysis step - identifies missing information for iterative research."""

import logging
from dataclasses import dataclass
from typing import Any

from app.services.llm.base import LLMConfig, LLMProvider

logger = logging.getLogger(__name__)

# Critical fields that should be present for vendor evaluation
CRITICAL_FIELDS = [
    "pricing_model",
    "pricing_details",
    "deployment_options",
    "security_compliance",
    "founded_year",
    "team_size",
    "customer_references",
    "technical_requirements",
    "support_options",
    "geographic_coverage",
]

# Weights for gap severity (higher = more important)
FIELD_WEIGHTS = {
    "pricing_model": 1.0,
    "pricing_details": 0.9,
    "security_compliance": 0.9,
    "deployment_options": 0.8,
    "customer_references": 0.7,
    "founded_year": 0.5,
    "team_size": 0.5,
    "technical_requirements": 0.7,
    "support_options": 0.6,
    "geographic_coverage": 0.5,
}


@dataclass
class FieldGap:
    """Information about a missing or incomplete field."""

    field_name: str
    current_value: Any
    confidence: float  # 0-1, how confident we are in current value
    importance: float  # 0-1, how important this field is
    suggested_queries: list[str]  # Follow-up queries to fill this gap

    def to_dict(self) -> dict:
        return {
            "field_name": self.field_name,
            "current_value": self.current_value,
            "confidence": self.confidence,
            "importance": self.importance,
            "suggested_queries": self.suggested_queries,
        }


@dataclass
class VendorGaps:
    """Gap analysis results for a single vendor."""

    vendor_name: str
    gaps: list[FieldGap]
    completeness_score: float  # 0-100
    confidence_score: float  # 0-100
    needs_iteration: bool  # Should we do another research iteration?
    priority_queries: list[str]  # Top queries for follow-up research

    def to_dict(self) -> dict:
        return {
            "vendor_name": self.vendor_name,
            "gaps": [g.to_dict() for g in self.gaps],
            "completeness_score": self.completeness_score,
            "confidence_score": self.confidence_score,
            "needs_iteration": self.needs_iteration,
            "priority_queries": self.priority_queries,
        }


@dataclass
class GapAnalysisResult:
    """Complete gap analysis result."""

    vendor_gaps: dict[str, VendorGaps]  # vendor_name -> gaps
    follow_up_queries: list[str]  # All suggested follow-up queries
    needs_iteration: bool  # Should pipeline iterate?
    overall_completeness: float  # Average completeness across vendors
    overall_confidence: float  # Average confidence across vendors

    def to_dict(self) -> dict:
        return {
            "vendor_gaps": {k: v.to_dict() for k, v in self.vendor_gaps.items()},
            "follow_up_queries": self.follow_up_queries,
            "needs_iteration": self.needs_iteration,
            "overall_completeness": self.overall_completeness,
            "overall_confidence": self.overall_confidence,
        }


async def analyze_gaps(
    vendors: list[dict],
    llm: LLMProvider,
    gap_threshold: float = 0.6,
    min_confidence: float = 0.5,
) -> GapAnalysisResult:
    """
    Analyze vendor data to identify information gaps.

    This implements the "OBSERVE" phase of DeepResearch:
    1. Examines each vendor's extracted data
    2. Identifies missing critical fields
    3. Evaluates confidence in existing data
    4. Generates targeted follow-up queries

    Args:
        vendors: List of extracted vendor data dicts
        llm: LLM provider for query generation
        gap_threshold: Completeness threshold below which iteration is needed
        min_confidence: Minimum acceptable confidence score

    Returns:
        GapAnalysisResult with gaps and follow-up suggestions
    """
    vendor_gaps: dict[str, VendorGaps] = {}
    all_queries: list[str] = []

    for vendor_data in vendors:
        # Support both ExtractedVendor objects and dicts
        if hasattr(vendor_data, 'name'):
            vendor_name = vendor_data.name
        else:
            vendor_name = vendor_data.get("name", "Unknown")

        gaps = []
        total_weight = 0
        filled_weight = 0

        # Check each critical field
        for field_name in CRITICAL_FIELDS:
            weight = FIELD_WEIGHTS.get(field_name, 0.5)
            total_weight += weight

            # Support both ExtractedVendor objects and dicts
            if hasattr(vendor_data, 'data'):
                value = vendor_data.data.get(field_name)
            else:
                value = vendor_data.get(field_name)
            confidence = _estimate_confidence(vendor_data, field_name)

            if not value or confidence < min_confidence:
                # This is a gap
                gap = FieldGap(
                    field_name=field_name,
                    current_value=value,
                    confidence=confidence,
                    importance=weight,
                    suggested_queries=_generate_field_queries(vendor_name, field_name),
                )
                gaps.append(gap)
            else:
                filled_weight += weight * confidence

        # Calculate scores
        completeness = (filled_weight / total_weight * 100) if total_weight > 0 else 0

        # Calculate average confidence of filled fields
        filled_confidences = []
        for f in CRITICAL_FIELDS:
            # Support both ExtractedVendor objects and dicts
            if hasattr(vendor_data, 'data'):
                has_value = vendor_data.data.get(f)
            else:
                has_value = vendor_data.get(f)
            if has_value:
                filled_confidences.append(_estimate_confidence(vendor_data, f))
        confidence_score = (
            sum(filled_confidences) / len(filled_confidences) * 100
            if filled_confidences
            else 0
        )

        # Determine if this vendor needs more research
        needs_iteration = completeness < (gap_threshold * 100) or len(gaps) > 3

        # Get priority queries (top 3 most important gaps)
        sorted_gaps = sorted(gaps, key=lambda g: g.importance, reverse=True)
        priority_queries = []
        for gap in sorted_gaps[:3]:
            priority_queries.extend(gap.suggested_queries[:2])

        vendor_gaps[vendor_name] = VendorGaps(
            vendor_name=vendor_name,
            gaps=gaps,
            completeness_score=completeness,
            confidence_score=confidence_score,
            needs_iteration=needs_iteration,
            priority_queries=priority_queries,
        )

        all_queries.extend(priority_queries)

    # Calculate overall metrics
    overall_completeness = (
        sum(vg.completeness_score for vg in vendor_gaps.values()) / len(vendor_gaps)
        if vendor_gaps
        else 0
    )
    overall_confidence = (
        sum(vg.confidence_score for vg in vendor_gaps.values()) / len(vendor_gaps)
        if vendor_gaps
        else 0
    )

    # Determine if pipeline should iterate
    needs_iteration = any(vg.needs_iteration for vg in vendor_gaps.values())

    # Use LLM to refine follow-up queries
    if needs_iteration and all_queries:
        # Support both ExtractedVendor objects and dicts
        vendor_names = [
            v.name if hasattr(v, 'name') else v.get("name", "Unknown")
            for v in vendors
        ]
        refined_queries = await _refine_queries_with_llm(
            llm=llm,
            raw_queries=list(set(all_queries))[:20],
            vendors=vendor_names,
        )
        all_queries = refined_queries

    logger.info(
        f"Gap analysis: {len(vendor_gaps)} vendors, "
        f"completeness={overall_completeness:.1f}%, "
        f"needs_iteration={needs_iteration}"
    )

    return GapAnalysisResult(
        vendor_gaps=vendor_gaps,
        follow_up_queries=list(set(all_queries))[:15],  # Limit to 15 queries
        needs_iteration=needs_iteration,
        overall_completeness=overall_completeness,
        overall_confidence=overall_confidence,
    )


def _estimate_confidence(vendor_data, field_name: str) -> float:
    """
    Estimate confidence in a field value based on evidence.

    Checks:
    - Is the value present and non-empty?
    - Is there evidence supporting this value?
    - How many sources mention this?

    Supports both ExtractedVendor objects and dicts.
    """
    # Support both ExtractedVendor objects and dicts
    if hasattr(vendor_data, 'data'):
        value = vendor_data.data.get(field_name)
    else:
        value = vendor_data.get(field_name)

    if not value:
        return 0.0

    # Check evidence if available
    if hasattr(vendor_data, 'evidence'):
        evidence = vendor_data.evidence
    else:
        evidence = vendor_data.get("evidence", [])
    field_evidence = [e for e in evidence if e.get("field") == field_name]

    if field_evidence:
        # Average confidence from evidence
        confidences = [e.get("confidence", 0.5) for e in field_evidence]
        return sum(confidences) / len(confidences)

    # Check if value seems substantial
    if isinstance(value, str):
        if len(value) > 50:
            return 0.7  # Detailed value
        elif len(value) > 10:
            return 0.5  # Brief value
        else:
            return 0.3  # Very short, might be placeholder

    if isinstance(value, (list, dict)):
        if len(value) > 0:
            return 0.6
        return 0.3

    return 0.5  # Default middle confidence


def _generate_field_queries(vendor_name: str, field_name: str) -> list[str]:
    """Generate search queries to fill a specific gap."""
    query_templates = {
        "pricing_model": [
            f"{vendor_name} pricing plans cost",
            f"{vendor_name} subscription pricing monthly annual",
            f"berapa harga {vendor_name}",  # Indonesian: "how much is..."
        ],
        "pricing_details": [
            f"{vendor_name} price list 2024 2025",
            f"{vendor_name} quote pricing Indonesia",
        ],
        "deployment_options": [
            f"{vendor_name} cloud on-premise deployment",
            f"{vendor_name} installation requirements",
        ],
        "security_compliance": [
            f"{vendor_name} security certifications SOC ISO",
            f"{vendor_name} data security compliance",
        ],
        "founded_year": [
            f"{vendor_name} company history founded",
            f"{vendor_name} about us company info",
        ],
        "team_size": [
            f"{vendor_name} employees team size linkedin",
            f"{vendor_name} company size headcount",
        ],
        "customer_references": [
            f"{vendor_name} customer testimonials case studies",
            f"{vendor_name} clients reviews",
        ],
        "technical_requirements": [
            f"{vendor_name} system requirements specifications",
            f"{vendor_name} technical documentation",
        ],
        "support_options": [
            f"{vendor_name} customer support 24/7",
            f"{vendor_name} technical support Indonesia",
        ],
        "geographic_coverage": [
            f"{vendor_name} offices locations Indonesia",
            f"{vendor_name} service availability Asia Pacific",
        ],
    }

    return query_templates.get(field_name, [f"{vendor_name} {field_name}"])


async def _refine_queries_with_llm(
    llm: LLMProvider,
    raw_queries: list[str],
    vendors: list[str],
) -> list[str]:
    """Use LLM to consolidate and improve follow-up queries."""
    prompt = f"""You are a procurement research assistant. Given these raw search queries
and vendor names, consolidate and improve them into effective search queries.

Vendors: {', '.join(vendors[:5])}

Raw queries:
{chr(10).join(f'- {q}' for q in raw_queries[:15])}

Generate 5-10 optimized search queries that will:
1. Find missing vendor information efficiently
2. Target Indonesian sources where possible (add Indonesia, Jakarta, etc.)
3. Combine related queries to reduce redundancy
4. Focus on the most critical missing information

Return as JSON: {{"queries": ["query1", "query2", ...]}}"""

    try:
        result = await llm.extract_json(
            prompt,
            schema_hint='{"queries": ["string"]}',
            config=LLMConfig(model=llm.get_default_model(), temperature=0.3),
        )
        return result.get("queries", raw_queries[:10])
    except Exception as e:
        logger.warning(f"LLM query refinement failed: {e}")
        return raw_queries[:10]


async def generate_gap_summary(
    gap_result: GapAnalysisResult,
    llm: LLMProvider,
) -> str:
    """
    Generate human-readable summary of gap analysis.

    Used for reports and user feedback.
    """
    if not gap_result.vendor_gaps:
        return "No vendors to analyze."

    # Build summary data
    vendor_summaries = []
    for name, gaps in gap_result.vendor_gaps.items():
        missing = [g.field_name for g in gaps.gaps[:5]]
        vendor_summaries.append({
            "name": name,
            "completeness": f"{gaps.completeness_score:.0f}%",
            "missing": missing,
        })

    prompt = f"""Summarize this vendor research gap analysis in 2-3 sentences for a procurement team.

Overall completeness: {gap_result.overall_completeness:.0f}%
Needs more research: {gap_result.needs_iteration}

Vendor details:
{chr(10).join(f"- {v['name']}: {v['completeness']} complete, missing: {', '.join(v['missing'][:3])}" for v in vendor_summaries[:5])}

Write a concise, professional summary."""

    try:
        result = await llm.generate(
            prompt,
            config=LLMConfig(model=llm.get_default_model(), temperature=0.3),
        )
        return result.strip()
    except Exception as e:
        logger.warning(f"Summary generation failed: {e}")
        return (
            f"Analyzed {len(gap_result.vendor_gaps)} vendors. "
            f"Overall completeness: {gap_result.overall_completeness:.0f}%. "
            f"{'Additional research recommended.' if gap_result.needs_iteration else 'Data collection complete.'}"
        )
