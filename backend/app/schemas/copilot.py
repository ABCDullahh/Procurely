"""Copilot schemas for AI chat with context."""

from typing import Literal

from pydantic import BaseModel, Field


class Citation(BaseModel):
    """Citation from vendor evidence."""

    vendor_id: int | None = None
    vendor_name: str | None = None
    source_url: str
    snippet: str
    field_name: str | None = None


class CopilotAction(BaseModel):
    """Suggested action from copilot."""

    type: Literal[
        "OPEN_VENDOR",
        "COMPARE_TOP",
        "CREATE_SHORTLIST",
        "EXPORT_REPORT",
        "OPEN_REPORTS",
    ]
    label: str
    payload: dict = Field(default_factory=dict)


class ChatRequest(BaseModel):
    """Request to copilot chat endpoint."""

    run_id: int
    message: str
    vendor_ids: list[int] | None = None
    mode: Literal["ask", "insights"] = "ask"


class ChatResponse(BaseModel):
    """Response from copilot chat."""

    answer: str
    citations: list[Citation] = Field(default_factory=list)
    suggested_actions: list[CopilotAction] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class CopilotContext(BaseModel):
    """Internal context for copilot prompt building."""

    request_title: str
    request_description: str | None
    request_category: str | None
    request_location: str | None
    request_budget_min: int | None
    request_budget_max: int | None
    request_timeline: str | None
    must_have_criteria: list[str]
    nice_to_have_criteria: list[str]
    run_status: str
    run_progress: int | None
    vendors_count: int
    sources_count: int
    avg_overall_score: float | None
    top_vendors: list[dict]  # name, website, score, industry, location
    evidence_snippets: list[dict]  # vendor_name, field, snippet, source_url
