"""Quality assessment step - evaluates research quality and vendor data completeness."""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from statistics import mean
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Fields used for completeness scoring
ASSESSMENT_FIELDS = [
    "name",
    "description",
    "website",
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
    "products_services",
]

# Weights for different quality factors
QUALITY_WEIGHTS = {
    "completeness": 0.30,
    "confidence": 0.30,
    "source_diversity": 0.15,
    "source_freshness": 0.15,
    "research_depth": 0.10,
}


@dataclass
class QualityReport:
    """Quality assessment for a single vendor."""

    vendor_name: str
    completeness_score: float  # 0-100: % of fields filled
    confidence_score: float  # 0-100: avg evidence confidence
    source_diversity: int  # Number of unique source domains
    freshness_score: float  # 0-100: how recent sources are
    research_depth: int  # Number of iterations used
    evidence_count: int  # Total evidence pieces
    overall_quality: float  # Weighted combination
    grade: str  # A, B, C, D, F
    issues: list[str]  # Quality issues found
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "vendor_name": self.vendor_name,
            "completeness_score": self.completeness_score,
            "confidence_score": self.confidence_score,
            "source_diversity": self.source_diversity,
            "freshness_score": self.freshness_score,
            "research_depth": self.research_depth,
            "evidence_count": self.evidence_count,
            "overall_quality": self.overall_quality,
            "grade": self.grade,
            "issues": self.issues,
            "metadata": self.metadata,
        }


@dataclass
class ResearchQualityReport:
    """Overall research quality report."""

    vendor_reports: dict[str, QualityReport]
    overall_quality: float
    overall_grade: str
    total_sources: int
    unique_domains: int
    research_iterations: int
    summary: str
    recommendations: list[str]

    def to_dict(self) -> dict:
        return {
            "vendor_reports": {k: v.to_dict() for k, v in self.vendor_reports.items()},
            "overall_quality": self.overall_quality,
            "overall_grade": self.overall_grade,
            "total_sources": self.total_sources,
            "unique_domains": self.unique_domains,
            "research_iterations": self.research_iterations,
            "summary": self.summary,
            "recommendations": self.recommendations,
        }


def assess_vendor_quality(
    vendor_data: dict,
    sources: list[dict],
    evidence: list[dict],
    research_iterations: int = 1,
) -> QualityReport:
    """
    Assess quality of research data for a single vendor.

    Evaluates:
    - Completeness: How many required fields are filled
    - Confidence: Average confidence of evidence
    - Source diversity: Number of unique domains
    - Freshness: How recent the sources are
    - Depth: Number of research iterations

    Args:
        vendor_data: Vendor information dict
        sources: List of source URLs/info
        evidence: List of evidence pieces
        research_iterations: Number of iterations used

    Returns:
        QualityReport with scores and grade
    """
    vendor_name = vendor_data.get("name", "Unknown")
    issues = []

    # 1. Calculate completeness
    filled_fields = 0
    for field_name in ASSESSMENT_FIELDS:
        value = vendor_data.get(field_name)
        if value and str(value).strip():
            filled_fields += 1

    completeness_score = (filled_fields / len(ASSESSMENT_FIELDS)) * 100

    if completeness_score < 50:
        issues.append(f"Low completeness ({completeness_score:.0f}%)")

    # 2. Calculate confidence
    confidences = []
    for e in evidence:
        conf = e.get("confidence")
        if isinstance(conf, (int, float)):
            confidences.append(conf)

    if confidences:
        confidence_score = mean(confidences) * 100
    else:
        confidence_score = 50  # Default if no evidence
        issues.append("No evidence with confidence scores")

    if confidence_score < 60:
        issues.append(f"Low confidence ({confidence_score:.0f}%)")

    # 3. Calculate source diversity
    domains = set()
    for source in sources:
        url = source.get("url") if isinstance(source, dict) else str(source)
        try:
            domain = urlparse(url).netloc
            if domain:
                domains.add(domain.lower())
        except Exception:
            pass

    source_diversity = len(domains)

    if source_diversity < 2:
        issues.append("Limited source diversity")

    # 4. Calculate freshness
    freshness_score = _calculate_freshness(sources)

    if freshness_score < 50:
        issues.append("Sources may be outdated")

    # 5. Research depth bonus
    depth_bonus = min(research_iterations * 10, 30)  # Max 30 points

    # Calculate overall quality score
    overall_quality = (
        completeness_score * QUALITY_WEIGHTS["completeness"]
        + confidence_score * QUALITY_WEIGHTS["confidence"]
        + min(source_diversity * 10, 20) * QUALITY_WEIGHTS["source_diversity"]
        + freshness_score * QUALITY_WEIGHTS["source_freshness"]
        + depth_bonus * QUALITY_WEIGHTS["research_depth"]
    )

    overall_quality = min(overall_quality, 100)

    # Assign grade
    grade = _score_to_grade(overall_quality)

    return QualityReport(
        vendor_name=vendor_name,
        completeness_score=completeness_score,
        confidence_score=confidence_score,
        source_diversity=source_diversity,
        freshness_score=freshness_score,
        research_depth=research_iterations,
        evidence_count=len(evidence),
        overall_quality=overall_quality,
        grade=grade,
        issues=issues,
        metadata={
            "fields_filled": filled_fields,
            "fields_total": len(ASSESSMENT_FIELDS),
            "domains": list(domains),
        },
    )


def assess_research_quality(
    vendors: list[dict],
    all_sources: list[dict],
    research_iterations: int = 1,
) -> ResearchQualityReport:
    """
    Assess overall research quality across all vendors.

    Args:
        vendors: List of vendor data dicts
        all_sources: All sources collected
        research_iterations: Number of research iterations

    Returns:
        ResearchQualityReport with overall assessment
    """
    vendor_reports: dict[str, QualityReport] = {}
    all_domains = set()

    for vendor in vendors:
        vendor_name = vendor.get("name", "Unknown")

        # Get sources and evidence for this vendor
        vendor_sources = vendor.get("sources", [])
        if not isinstance(vendor_sources, list):
            vendor_sources = []

        vendor_evidence = vendor.get("evidence", [])
        if not isinstance(vendor_evidence, list):
            vendor_evidence = []

        # Assess this vendor
        report = assess_vendor_quality(
            vendor_data=vendor,
            sources=vendor_sources,
            evidence=vendor_evidence,
            research_iterations=research_iterations,
        )
        vendor_reports[vendor_name] = report

        # Collect domains
        all_domains.update(report.metadata.get("domains", []))

    # Calculate overall metrics
    if vendor_reports:
        overall_quality = mean(r.overall_quality for r in vendor_reports.values())
    else:
        overall_quality = 0

    overall_grade = _score_to_grade(overall_quality)

    # Generate recommendations
    recommendations = _generate_recommendations(vendor_reports)

    # Generate summary
    summary = _generate_summary(vendor_reports, overall_quality, research_iterations)

    return ResearchQualityReport(
        vendor_reports=vendor_reports,
        overall_quality=overall_quality,
        overall_grade=overall_grade,
        total_sources=len(all_sources),
        unique_domains=len(all_domains),
        research_iterations=research_iterations,
        summary=summary,
        recommendations=recommendations,
    )


def _calculate_freshness(sources: list[dict]) -> float:
    """
    Calculate freshness score based on source dates.

    Returns 0-100 score where:
    - 100 = All sources from last 30 days
    - 50 = Sources from last year
    - 0 = Sources older than 2 years or no dates
    """
    if not sources:
        return 50  # Default neutral

    now = datetime.now(timezone.utc)
    freshness_scores = []

    for source in sources:
        date_str = None
        if isinstance(source, dict):
            date_str = source.get("fetched_at") or source.get("date")

        if not date_str:
            freshness_scores.append(50)  # Unknown date = neutral
            continue

        try:
            if isinstance(date_str, str):
                source_date = datetime.fromisoformat(
                    date_str.replace("Z", "+00:00")
                )
            elif isinstance(date_str, datetime):
                source_date = date_str
            else:
                freshness_scores.append(50)
                continue

            days_old = (now - source_date).days

            if days_old < 30:
                freshness_scores.append(100)
            elif days_old < 90:
                freshness_scores.append(85)
            elif days_old < 180:
                freshness_scores.append(70)
            elif days_old < 365:
                freshness_scores.append(50)
            elif days_old < 730:
                freshness_scores.append(30)
            else:
                freshness_scores.append(10)

        except Exception:
            freshness_scores.append(50)

    return mean(freshness_scores) if freshness_scores else 50


def _score_to_grade(score: float) -> str:
    """Convert numeric score to letter grade."""
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"


def _generate_recommendations(vendor_reports: dict[str, QualityReport]) -> list[str]:
    """Generate actionable recommendations based on quality reports."""
    recommendations = []

    # Analyze common issues
    low_completeness_count = sum(
        1 for r in vendor_reports.values() if r.completeness_score < 60
    )
    low_confidence_count = sum(
        1 for r in vendor_reports.values() if r.confidence_score < 60
    )
    low_diversity_count = sum(
        1 for r in vendor_reports.values() if r.source_diversity < 2
    )

    total = len(vendor_reports)

    if total > 0:
        if low_completeness_count / total > 0.5:
            recommendations.append(
                "Many vendors have incomplete data. Consider adding more product/service "
                "keywords to find detailed information."
            )

        if low_confidence_count / total > 0.5:
            recommendations.append(
                "Evidence confidence is low for many vendors. Enable additional "
                "search providers or increase research iterations."
            )

        if low_diversity_count / total > 0.5:
            recommendations.append(
                "Source diversity is limited. Consider using multiple search "
                "and scrape providers to get varied perspectives."
            )

    # Vendor-specific recommendations
    for name, report in vendor_reports.items():
        if report.grade == "F":
            recommendations.append(
                f"Vendor '{name}' has very low quality data. "
                "Manual research may be needed."
            )

    return recommendations[:5]  # Limit to 5 recommendations


def _generate_summary(
    vendor_reports: dict[str, QualityReport],
    overall_quality: float,
    iterations: int,
) -> str:
    """Generate human-readable quality summary."""
    total = len(vendor_reports)
    if total == 0:
        return "No vendors to assess."

    grade_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    for report in vendor_reports.values():
        grade_counts[report.grade] += 1

    good = grade_counts["A"] + grade_counts["B"]
    fair = grade_counts["C"]
    poor = grade_counts["D"] + grade_counts["F"]

    summary_parts = [
        f"Assessed {total} vendors after {iterations} research iteration(s).",
        f"Overall quality: {overall_quality:.0f}% ({_score_to_grade(overall_quality)}).",
    ]

    if good > 0:
        summary_parts.append(f"{good} vendor(s) with good data quality.")
    if poor > 0:
        summary_parts.append(f"{poor} vendor(s) need additional research.")

    return " ".join(summary_parts)


def calculate_enhanced_score(
    vendor_data: dict,
    quality_report: QualityReport,
    pricing_data: dict | None,
    fit_score: float,
    trust_score: float,
) -> dict:
    """
    Calculate enhanced vendor score including quality and pricing factors.

    This replaces the simple fit+trust scoring with a comprehensive score
    that includes research quality and pricing competitiveness.

    Args:
        vendor_data: Vendor information
        quality_report: Quality assessment
        pricing_data: Pricing data from shopping search
        fit_score: Original fit score (0-100)
        trust_score: Original trust score (0-100)

    Returns:
        Dict with detailed score breakdown
    """
    # Quality score from assessment
    quality_score = quality_report.overall_quality

    # Pricing score (if available)
    price_score = 50  # Default neutral
    if pricing_data and pricing_data.get("price_competitiveness"):
        price_score = pricing_data["price_competitiveness"]

    # Calculate weighted overall score
    weights = {
        "fit": 0.35,
        "trust": 0.25,
        "quality": 0.25,
        "price": 0.15,
    }

    overall = (
        fit_score * weights["fit"]
        + trust_score * weights["trust"]
        + quality_score * weights["quality"]
        + price_score * weights["price"]
    )

    return {
        "fit_score": fit_score,
        "trust_score": trust_score,
        "quality_score": quality_score,
        "price_score": price_score,
        "overall_score": overall,
        "grade": _score_to_grade(overall),
        "weights": weights,
        "quality_details": {
            "completeness": quality_report.completeness_score,
            "confidence": quality_report.confidence_score,
            "source_diversity": quality_report.source_diversity,
            "research_depth": quality_report.research_depth,
        },
        "pricing_details": pricing_data if pricing_data else None,
    }
