"""Dashboard schemas."""

from pydantic import BaseModel


class RequestStats(BaseModel):
    """Stats for a request status category."""

    count: int
    label: str


class RecentRequest(BaseModel):
    """Recent request summary for dashboard."""

    id: int
    title: str
    status: str
    category: str
    vendors_found: int
    updated_at: str


class DashboardResponse(BaseModel):
    """Dashboard aggregated stats response."""

    total_requests: int
    requests_by_status: dict[str, int]
    total_vendors_found: int
    recent_requests: list[RecentRequest]
    active_runs: int
    completed_count: int = 0
