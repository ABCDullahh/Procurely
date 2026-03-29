"""Research configuration and quality assessment schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ResearchConfig(BaseModel):
    """Configuration for DeepResearch pipeline.

    Controls iteration behavior, quality thresholds, and feature toggles.
    """

    enabled: bool = Field(
        default=True,
        description="Enable DeepResearch pipeline (iterative research, gap analysis)",
    )
    max_iterations: int = Field(
        default=2,
        ge=1,
        le=5,
        description="Maximum research iterations (1-5)",
    )
    gap_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Threshold for gap analysis (0-1). Higher = stricter quality requirements",
    )
    include_shopping: bool = Field(
        default=True,
        description="Include Google Shopping price search",
    )
    region_bias: bool = Field(
        default=True,
        description="Prefer vendors from target region (e.g., Indonesia)",
    )
    location: str | None = Field(
        default="Indonesia",
        description="Target location for vendor search",
    )


class ResearchConfigUpdate(BaseModel):
    """Partial update for research configuration."""

    enabled: bool | None = None
    max_iterations: int | None = Field(default=None, ge=1, le=5)
    gap_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    include_shopping: bool | None = None
    region_bias: bool | None = None
    location: str | None = None


class LocaleConfig(BaseModel):
    """Locale configuration for Indonesia-focused search."""

    locale: str = Field(default="id_ID", description="Locale code (e.g., id_ID, en_US)")
    country_code: str = Field(default="ID", description="ISO country code (e.g., ID, US)")
    region_bias: bool = Field(default=True, description="Prefer local vendors")


class VendorQualityReport(BaseModel):
    """Quality assessment for a single vendor."""

    vendor_name: str
    completeness_score: float = Field(ge=0, le=100)
    confidence_score: float = Field(ge=0, le=100)
    source_diversity: int = Field(ge=0)
    freshness_score: float = Field(ge=0, le=100)
    research_depth: int = Field(ge=1)
    overall_quality: float = Field(ge=0, le=100)
    grade: Literal["A", "B", "C", "D", "F"]
    missing_fields: list[str] = []
    recommendations: list[str] = []


class ResearchQualityReport(BaseModel):
    """Overall research quality assessment."""

    run_id: int
    total_vendors: int
    avg_completeness: float
    avg_confidence: float
    total_sources: int
    unique_domains: int
    research_iterations: int
    overall_quality: float
    overall_grade: Literal["A", "B", "C", "D", "F"]
    vendor_reports: list[VendorQualityReport] = []
    assessed_at: datetime


class ShoppingPricing(BaseModel):
    """Pricing data from Google Shopping."""

    vendor_name: str
    products_found: int
    min_price: float | None
    max_price: float | None
    avg_price: float | None
    currency: str = "USD"
    market_position: Literal["below_market", "at_market", "above_market"] | None = None
    competitiveness: float | None = Field(
        default=None,
        description="Ratio to market average (< 1.0 = cheaper, > 1.0 = more expensive)",
    )


class ShoppingSearchResult(BaseModel):
    """Results from Google Shopping search."""

    total_products: int
    vendor_pricing: list[ShoppingPricing] = []
    market_avg: float | None = None
    category: str | None = None
    searched_at: datetime


class GapAnalysisResult(BaseModel):
    """Results from gap analysis step."""

    vendor_name: str
    missing_fields: list[str]
    low_confidence_fields: list[str]
    completeness_pct: float
    needs_more_research: bool
    suggested_queries: list[str] = []


class ResearchIterationSummary(BaseModel):
    """Summary of a single research iteration."""

    iteration: int
    queries_executed: int
    pages_scraped: int
    new_vendors_found: int
    gaps_filled: int
    completeness_before: float
    completeness_after: float


class DeepResearchSummary(BaseModel):
    """Complete summary of DeepResearch execution."""

    run_id: int
    request_id: int
    total_iterations: int
    total_vendors: int
    total_sources: int
    quality_grade: Literal["A", "B", "C", "D", "F"]
    shopping_enabled: bool
    shopping_products_found: int
    iterations: list[ResearchIterationSummary] = []
    quality_report: ResearchQualityReport | None = None
    shopping_result: ShoppingSearchResult | None = None
    started_at: datetime
    completed_at: datetime | None = None
    duration_seconds: float | None = None
