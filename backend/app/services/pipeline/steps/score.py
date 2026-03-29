"""Vendor scoring step - calculates fit and trust scores."""

import logging
from dataclasses import dataclass

from app.services.pipeline.steps.extract import ExtractedVendor

logger = logging.getLogger(__name__)


@dataclass
class ScoredVendor:
    """Vendor with computed scores."""

    vendor: ExtractedVendor
    fit_score: float
    trust_score: float
    quality_score: float
    overall_score: float
    must_have_matched: int
    must_have_total: int
    nice_to_have_matched: int
    nice_to_have_total: int


def calculate_fit_score(
    vendor: ExtractedVendor,
    must_have: list[str],
    nice_to_have: list[str],
) -> tuple[float, int, int, int, int]:
    """
    Calculate how well vendor matches requirements.

    Returns:
        Tuple of (score, must_matched, must_total, nice_matched, nice_total)
    """
    # Combine all vendor text for matching
    # Use (... or "") to handle both missing keys and None values
    vendor_text = " ".join([
        (vendor.name or "").lower(),
        (vendor.data.get("description") or "").lower(),
        (vendor.data.get("industry") or "").lower(),
        " ".join(str(ev.get("snippet") or "").lower() for ev in vendor.evidence),
    ])

    # Check must-have criteria
    must_matched = 0
    must_total = len(must_have)
    for criterion in must_have:
        keywords = criterion.lower().split()
        if all(kw in vendor_text for kw in keywords):
            must_matched += 1

    # Check nice-to-have criteria
    nice_matched = 0
    nice_total = len(nice_to_have)
    for criterion in nice_to_have:
        keywords = criterion.lower().split()
        if all(kw in vendor_text for kw in keywords):
            nice_matched += 1

    # Calculate score (must-have weighted 70%, nice-to-have 30%)
    must_score = (must_matched / must_total * 100) if must_total > 0 else 50
    nice_score = (nice_matched / nice_total * 100) if nice_total > 0 else 50

    fit_score = must_score * 0.7 + nice_score * 0.3

    return fit_score, must_matched, must_total, nice_matched, nice_total


def calculate_trust_score(vendor: ExtractedVendor) -> float:
    """
    Calculate trust score based on data completeness and source quality.

    Returns:
        Trust score 0-100
    """
    score = 50.0  # Base score

    # Award points for complete data
    if vendor.data.get("website"):
        score += 10
    if vendor.data.get("description"):
        score += 5
    if vendor.data.get("email"):
        score += 5
    if vendor.data.get("phone"):
        score += 5
    if vendor.data.get("location"):
        score += 5
    if vendor.data.get("industry"):
        score += 5
    if vendor.data.get("employee_count"):
        score += 5

    # Award points for evidence
    evidence_count = len(vendor.evidence)
    score += min(evidence_count * 2, 10)

    return min(score, 100)


def score_vendors(
    vendors: list[ExtractedVendor],
    must_have: list[str],
    nice_to_have: list[str],
) -> list[ScoredVendor]:
    """
    Score all vendors and sort by overall score.

    Args:
        vendors: List of extracted vendors
        must_have: Required criteria
        nice_to_have: Optional criteria

    Returns:
        Sorted list of scored vendors (highest first)
    """
    scored: list[ScoredVendor] = []

    for vendor in vendors:
        fit, must_m, must_t, nice_m, nice_t = calculate_fit_score(
            vendor, must_have, nice_to_have
        )
        trust = calculate_trust_score(vendor)

        # Quality bonus: evidence count and confidence boost the score
        quality = 50.0  # base
        if vendor.evidence:
            ev_count = len(vendor.evidence)
            avg_conf = sum(e.get("confidence", 0.5) for e in vendor.evidence) / max(ev_count, 1)
            quality = min(100, 30 + ev_count * 2 + avg_conf * 40)

        # Overall: 45% fit + 30% trust + 25% quality
        overall = fit * 0.45 + trust * 0.30 + quality * 0.25

        scored.append(
            ScoredVendor(
                vendor=vendor,
                fit_score=round(fit, 1),
                trust_score=round(trust, 1),
                quality_score=round(quality, 1),
                overall_score=round(overall, 1),
                must_have_matched=must_m,
                must_have_total=must_t,
                nice_to_have_matched=nice_m,
                nice_to_have_total=nice_t,
            )
        )

    # Sort by overall score descending
    scored.sort(key=lambda x: x.overall_score, reverse=True)

    logger.info(f"Scored {len(scored)} vendors")
    return scored
