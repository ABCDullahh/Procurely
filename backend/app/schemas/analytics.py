"""Analytics schemas for run statistics and reporting."""

from datetime import datetime

from pydantic import BaseModel, Field


class LocationDistribution(BaseModel):
    """Vendor count by location."""

    location: str
    count: int


class IndustryDistribution(BaseModel):
    """Vendor count by industry."""

    industry: str
    count: int


class ScoreBucket(BaseModel):
    """Score distribution bucket."""

    range: str  # e.g., "0-20", "21-40"
    count: int


class TopVendor(BaseModel):
    """Top vendor summary."""

    id: int
    name: str
    website: str | None
    overall_score: float | None
    fit_score: float | None
    trust_score: float | None
    location: str | None
    industry: str | None


class RunSummary(BaseModel):
    """Run execution summary."""

    status: str
    started_at: datetime | None
    completed_at: datetime | None
    duration_sec: int | None


class Totals(BaseModel):
    """Aggregate totals."""

    vendors_count: int
    sources_count: int


class AverageScores(BaseModel):
    """Average score metrics."""

    avg_fit: float | None
    avg_trust: float | None
    avg_overall: float | None


class PricingDataItem(BaseModel):
    """Pricing comparison data for a vendor."""

    name: str
    price_min: float | None
    price_max: float | None
    pricing_model: str | None


class CriteriaDataItem(BaseModel):
    """Criteria matching data for a vendor."""

    name: str
    must_have_matched: int
    must_have_total: int
    nice_to_have_matched: int
    nice_to_have_total: int
    quality_score: float
    completeness_pct: float
    confidence_pct: float


class ScoreBreakdown(BaseModel):
    """Average score breakdown."""

    avg_fit: float
    avg_trust: float
    avg_quality: float
    avg_overall: float


class Distributions(BaseModel):
    """Distribution breakdowns."""

    vendors_by_location: list[LocationDistribution] = Field(default_factory=list)
    vendors_by_industry: list[IndustryDistribution] = Field(default_factory=list)
    score_distribution: list[ScoreBucket] = Field(default_factory=list)
    average_scores: AverageScores


class AnalyticsResponse(BaseModel):
    """Complete analytics response for a run."""

    run_summary: RunSummary
    totals: Totals
    distributions: Distributions
    top_vendors: list[TopVendor] = Field(default_factory=list)
    pricing_data: list[PricingDataItem] = Field(default_factory=list)
    criteria_matching: list[CriteriaDataItem] = Field(default_factory=list)
    score_breakdown: ScoreBreakdown | None = None

    model_config = {"from_attributes": True}


# Export/Report schemas
class ReportResponse(BaseModel):
    """Report metadata response."""

    id: int
    run_id: int
    format: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportDetailResponse(ReportResponse):
    """Report with HTML content."""

    html_content: str | None


class ReportListResponse(BaseModel):
    """List of reports."""

    reports: list[ReportResponse]
    total: int
