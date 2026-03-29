"""Schemas for procurement requests."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class RequestStatus(str, Enum):
    """Status of a procurement request."""

    DRAFT = "DRAFT"
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ResearchConfigInput(BaseModel):
    """Research configuration for DeepResearch pipeline."""

    max_iterations: int = Field(default=2, ge=1, le=5)
    gap_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    include_shopping: bool = True


class KeywordGenerationRequest(BaseModel):
    """Schema for generating keywords from title/description."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    category: str = Field(..., min_length=1, max_length=100)


class KeywordGenerationResponse(BaseModel):
    """Response for keyword generation."""

    keywords: list[str]


class ProcurementRequestCreate(BaseModel):
    """Schema for creating a procurement request."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    category: str = Field(..., min_length=1, max_length=100)
    # Keywords now optional - will be auto-generated if not provided
    keywords: list[str] | None = None
    auto_generate_keywords: bool = True  # Auto-generate if keywords empty
    location: str | None = None
    budget_max: int | None = Field(None, ge=0)  # Simplified: only max budget
    # Keep these for backwards compatibility but not required
    budget_min: int | None = Field(None, ge=0)
    timeline: str | None = Field(None, max_length=100)
    must_have_criteria: list[str] | None = None
    nice_to_have_criteria: list[str] | None = None
    selected_providers: list[str] | None = None
    # Indonesia focus settings (smart defaults)
    locale: str = Field(default="id_ID", max_length=10)
    country_code: str = Field(default="ID", max_length=2)
    region_bias: bool = True
    research_config: ResearchConfigInput | None = None


class ProcurementRequestUpdate(BaseModel):
    """Schema for updating a procurement request."""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    category: str | None = Field(None, min_length=1, max_length=100)
    keywords: list[str] | None = None
    location: str | None = None
    budget_min: int | None = Field(None, ge=0)
    budget_max: int | None = Field(None, ge=0)
    timeline: str | None = Field(None, max_length=100)
    must_have_criteria: list[str] | None = None
    nice_to_have_criteria: list[str] | None = None
    selected_providers: list[str] | None = None
    locale: str | None = Field(None, max_length=10)
    country_code: str | None = Field(None, max_length=2)
    region_bias: bool | None = None
    research_config: ResearchConfigInput | None = None
    status: RequestStatus | None = None


class ProcurementRequestResponse(BaseModel):
    """Response schema for a procurement request."""

    id: int
    title: str
    description: str | None
    category: str
    keywords: list[str]
    location: str | None
    budget_min: int | None
    budget_max: int | None
    timeline: str | None
    must_have_criteria: list[str] | None
    nice_to_have_criteria: list[str] | None
    selected_providers: list[str] | None
    locale: str = "id_ID"
    country_code: str = "ID"
    region_bias: bool = True
    research_config: dict | None = None
    status: str
    created_by_email: str
    created_at: datetime
    updated_at: datetime
    latest_run_status: str | None = None
    vendors_found: int = 0

    model_config = {"from_attributes": True}


class ProcurementRequestListResponse(BaseModel):
    """Response for list of procurement requests."""

    requests: list[ProcurementRequestResponse]
    total: int
    page: int
    page_size: int


class PipelineLogEntry(BaseModel):
    """Single log entry from pipeline execution."""
    timestamp: str
    step: str
    level: str
    message: str
    data: dict | None = None


class TokenUsageEntry(BaseModel):
    """Token usage for a pipeline step."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    calls: int
    model: str


class SearchRunResponse(BaseModel):
    """Response schema for a search run."""

    id: int
    request_id: int
    status: str
    current_step: str | None
    progress_pct: int
    vendors_found: int
    sources_searched: int
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    pipeline_logs: list[PipelineLogEntry] | None = None
    token_usage: dict[str, TokenUsageEntry] | None = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_json(cls, run):
        """Create response from ORM with JSON parsing."""
        import json
        data = {
            "id": run.id,
            "request_id": run.request_id,
            "status": run.status,
            "current_step": run.current_step,
            "progress_pct": run.progress_pct,
            "vendors_found": run.vendors_found,
            "sources_searched": run.sources_searched,
            "error_message": run.error_message,
            "started_at": run.started_at,
            "completed_at": run.completed_at,
            "created_at": run.created_at,
            "pipeline_logs": None,
            "token_usage": None,
        }
        if run.pipeline_logs:
            try:
                data["pipeline_logs"] = json.loads(run.pipeline_logs)
            except Exception:
                pass
        if run.token_usage:
            try:
                data["token_usage"] = json.loads(run.token_usage)
            except Exception:
                pass
        return cls(**data)
