"""Vendor-related schemas."""

from datetime import datetime

from pydantic import BaseModel


class VendorAssetResponse(BaseModel):
    """Response for vendor asset."""

    id: int
    asset_type: str
    asset_url: str
    source_url: str | None
    mime_type: str | None
    width: int | None
    height: int | None
    priority: int
    fetched_at: datetime | None = None

    model_config = {"from_attributes": True}


class VendorSourceResponse(BaseModel):
    """Response for vendor source."""

    id: int
    source_url: str
    source_type: str
    source_category: str | None = None
    page_title: str | None = None
    content_summary: str | None = None
    fetch_status: str
    fetched_at: datetime

    model_config = {"from_attributes": True}


class VendorEvidenceResponse(BaseModel):
    """Response for vendor field evidence."""

    id: int
    field_name: str
    field_label: str | None = None
    field_value: str
    category: str | None = None
    evidence_url: str | None = None
    evidence_snippet: str | None = None
    source_title: str | None = None
    confidence: float
    extraction_method: str
    extracted_at: datetime

    model_config = {"from_attributes": True}


class VendorMetricsResponse(BaseModel):
    """Response for vendor metrics."""

    fit_score: float
    trust_score: float
    overall_score: float
    must_have_matched: int
    must_have_total: int
    nice_to_have_matched: int
    nice_to_have_total: int
    source_count: int
    evidence_count: int
    # DeepResearch quality fields
    quality_score: float | None = None
    price_score: float | None = None
    completeness_pct: float | None = None
    confidence_pct: float | None = None
    source_diversity: int | None = None
    research_depth: int | None = None
    price_competitiveness: float | None = None

    model_config = {"from_attributes": True}


# Structured data sections for procurement-grade display
class VendorStructuredData(BaseModel):
    """Structured procurement data for vendor."""

    # Summary section
    target_segment: str | None = None
    regions_served: str | None = None

    # Features section
    use_cases: list[str] | None = None
    key_features: list[str] | None = None
    differentiators: list[str] | None = None
    limitations: list[str] | None = None

    # Company section
    notable_customers: list[str] | None = None

    # Implementation section
    support_channels: str | None = None
    onboarding_time: str | None = None
    contract_terms: str | None = None
    data_hosting: str | None = None
    sso_saml: bool | None = None


class ShoppingProductResponse(BaseModel):
    """Response for a shopping product."""
    title: str
    price: float | None
    price_raw: str
    currency: str
    source: str
    link: str
    thumbnail: str | None = None
    rating: float | None = None
    reviews_count: int | None = None


class VendorShoppingData(BaseModel):
    """Shopping/pricing data for a vendor."""
    vendor_name: str | None = None
    products: list[ShoppingProductResponse] = []
    price_min: float | None = None
    price_max: float | None = None
    price_avg: float | None = None
    market_avg: float | None = None
    price_competitiveness: float | None = None
    sources: list[str] = []


class VendorResponse(BaseModel):
    """Response for a vendor."""

    id: int
    name: str
    website: str | None
    description: str | None
    location: str | None
    country: str | None
    industry: str | None
    founded_year: int | None
    employee_count: str | None
    email: str | None
    phone: str | None
    pricing_model: str | None
    pricing_details: str | None

    # New procurement fields
    security_compliance: str | None = None
    deployment: str | None = None
    integrations: str | None = None

    # Structured data (parsed from JSON)
    structured_data: VendorStructuredData | None = None

    # Shopping/pricing data from Google Shopping
    shopping_data: VendorShoppingData | None = None
    price_range_min: float | None = None
    price_range_max: float | None = None
    price_last_updated: datetime | None = None

    created_at: datetime
    updated_at: datetime

    # Computed fields
    logo_url: str | None = None
    metrics: VendorMetricsResponse | None = None

    model_config = {"from_attributes": True}


class VendorListResponse(BaseModel):
    """Response for list of vendors."""

    vendors: list[VendorResponse]
    total: int
    page: int
    page_size: int


class CategoryBenchmark(BaseModel):
    """Category pricing benchmark data."""
    category: str | None = None
    price_min: float | None = None
    price_max: float | None = None
    price_avg: float | None = None
    price_median: float | None = None
    sample_size: int = 0
    sources: list[str] = []


class SearchRunShoppingData(BaseModel):
    """Shopping data for a search run."""
    category_benchmark: CategoryBenchmark | None = None
    market_avg: float | None = None
    total_products: int = 0
    search_queries: list[str] = []


class PipelineLogEntry(BaseModel):
    """Single log entry from pipeline execution."""
    timestamp: str
    step: str
    level: str
    message: str
    data: dict | None = None


class TokenUsageEntry(BaseModel):
    """Token usage for a pipeline step."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    calls: int = 0
    model: str = ""


class SearchRunDetailResponse(BaseModel):
    """Detailed response for a search run."""

    id: int
    request_id: int
    status: str
    current_step: str | None
    progress_pct: int
    vendors_found: int
    sources_searched: int
    error_message: str | None
    # DeepResearch fields
    research_iterations: int = 1
    quality_assessment: dict | None = None
    shopping_data: SearchRunShoppingData | None = None
    # Pipeline logging and token tracking
    pipeline_logs: list[PipelineLogEntry] | None = None
    token_usage: dict[str, TokenUsageEntry] | None = None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
