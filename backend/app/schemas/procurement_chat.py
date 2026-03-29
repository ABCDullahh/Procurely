"""Procurement Chat schemas for conversational AI search."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class VendorCardData(BaseModel):
    """Vendor data for rich card display."""

    id: int
    name: str
    website: str | None = None
    logo_url: str | None = None
    industry: str | None = None
    location: str | None = None
    country: str | None = None
    description: str | None = None
    overall_score: float | None = None
    fit_score: float | None = None
    trust_score: float | None = None
    pricing_model: str | None = None
    pricing_details: str | None = None
    employee_count: str | None = None
    founded_year: int | None = None
    criteria_matched: list[str] = Field(default_factory=list)
    criteria_partial: list[str] = Field(default_factory=list)
    criteria_missing: list[str] = Field(default_factory=list)


class ComparisonRow(BaseModel):
    """Row in comparison table."""

    metric: str
    values: dict[str, Any]  # vendor_id -> value
    best_vendor_id: int | None = None


class ComparisonData(BaseModel):
    """Data for comparison table."""

    vendors: list[VendorCardData]
    rows: list[ComparisonRow]


class FilterChip(BaseModel):
    """Clickable filter suggestion."""

    id: str
    label: str
    icon: str | None = None
    filter_type: str  # location, compliance, support, pricing, etc.
    filter_value: str


class SearchProgressStep(BaseModel):
    """Step in search progress."""

    id: str
    label: str
    status: Literal["pending", "active", "completed", "failed"]
    details: str | None = None


class SearchProgressData(BaseModel):
    """Real-time search progress."""

    steps: list[SearchProgressStep]
    current_step: str
    progress_pct: int
    vendors_found: int = 0
    sources_searched: int = 0
    estimated_time_remaining: str | None = None


class EvidenceItem(BaseModel):
    """Evidence snippet with source."""

    vendor_id: int
    vendor_name: str
    field: str
    value: str
    snippet: str
    source_url: str
    confidence: float


class SuggestedQuery(BaseModel):
    """AI-suggested follow-up query."""

    text: str
    type: Literal["refine", "compare", "explain", "action"]


# Enhanced card data schemas
class InsightData(BaseModel):
    """Key insight for procurement decisions."""

    type: Literal["recommendation", "trend", "warning", "highlight"]
    title: str
    description: str
    action: str | None = None


class StatData(BaseModel):
    """Quick statistic display."""

    label: str
    value: str | int
    change: str | None = None
    change_type: Literal["positive", "negative", "neutral"] | None = None
    icon: str | None = None


class CategoryData(BaseModel):
    """Category/industry breakdown."""

    name: str
    count: int
    percentage: float
    color: str | None = None


class PricingData(BaseModel):
    """Pricing overview for vendors."""

    vendor_name: str
    vendor_id: int
    pricing_model: str
    pricing_details: str | None = None
    has_free_tier: bool = False
    starting_price: str | None = None


class ChatAction(BaseModel):
    """Executable action from chat."""

    type: Literal[
        "VIEW_VENDOR",
        "ADD_TO_SHORTLIST",
        "COMPARE_VENDORS",
        "EXPORT_CSV",
        "GENERATE_REPORT",
        "APPLY_FILTER",
        "START_SEARCH",
        "REFINE_SEARCH",
        "CREATE_REQUEST",
        "START_DEEP_RESEARCH",  # Trigger web search from chat
        "CANCEL_RESEARCH",  # Cancel ongoing research
    ]
    label: str
    payload: dict = Field(default_factory=dict)
    variant: Literal["primary", "secondary", "outline", "ghost"] = "secondary"
    icon: str | None = None


class ProcurementChatRequest(BaseModel):
    """Request to procurement chat endpoint."""

    message: str
    conversation_id: str | None = None
    context: dict | None = None  # current filters, criteria, etc.
    mode: Literal["search", "refine", "compare", "explain", "create"] = "search"
    run_id: int | None = None  # if analyzing existing run
    vendor_ids: list[int] | None = None  # if focused on specific vendors


class ConversationContext(BaseModel):
    """Extracted context from conversation for follow-up messages."""

    category: str | None = None
    keywords: list[str] = Field(default_factory=list)
    budget: str | None = None
    location: str | None = None
    requirements: list[str] = Field(default_factory=list)


class ProcurementChatResponse(BaseModel):
    """Response from procurement chat with rich content."""

    message_id: str
    conversation_id: str

    # Main response
    response_type: Literal[
        "text",
        "vendors",
        "comparison",
        "progress",
        "evidence",
        "criteria_builder",
        "chart",
        "gathering_info",
        "deep_research",  # DeepResearch in progress from chat
        "error",
    ]
    text_content: str  # Always present, markdown formatted

    # Rich data (based on response_type)
    vendors: list[VendorCardData] | None = None
    comparison: ComparisonData | None = None
    progress: SearchProgressData | None = None
    evidence: list[EvidenceItem] | None = None
    chart_data: dict | None = None

    # Interactive elements
    filter_chips: list[FilterChip] = Field(default_factory=list)
    suggested_queries: list[SuggestedQuery] = Field(default_factory=list)
    actions: list[ChatAction] = Field(default_factory=list)

    # Enhanced card data for professional display
    insights: list[InsightData] = Field(default_factory=list)
    quick_stats: list[StatData] = Field(default_factory=list)
    categories: list[CategoryData] = Field(default_factory=list)
    pricing_overview: list[PricingData] = Field(default_factory=list)

    # Conversation context for follow-up messages
    context: ConversationContext | None = None

    # Metadata
    run_id: int | None = None
    request_id: int | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}


class ConversationMessage(BaseModel):
    """Single message in conversation history."""

    id: str
    role: Literal["user", "assistant"]
    content: str
    response_type: str | None = None
    data: dict | None = None
    timestamp: datetime


class ConversationHistory(BaseModel):
    """Full conversation history."""

    conversation_id: str
    messages: list[ConversationMessage]
    context: dict | None = None
    created_at: datetime
    updated_at: datetime


# ============ Chat Research Schemas ============

class StartResearchRequest(BaseModel):
    """Request to start DeepResearch from chat."""

    category: str
    keywords: list[str]
    location: str | None = None
    budget_max: int | None = None
    conversation_id: str | None = None


class ResearchStatusResponse(BaseModel):
    """Status of a chat-triggered research run."""

    request_id: int
    run_id: int
    status: Literal["QUEUED", "RUNNING", "COMPLETED", "FAILED", "CANCELLED"]
    current_step: str | None = None
    progress_pct: int = 0
    vendors_found: int = 0
    partial_vendors: list[VendorCardData] | None = None
    error_message: str | None = None
    is_complete: bool = False


class CancelResearchResponse(BaseModel):
    """Response from cancelling research."""

    success: bool
    message: str
