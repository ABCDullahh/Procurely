"""Schemas for audit log endpoints."""

from datetime import datetime

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    """Response schema for audit log entry."""

    id: int
    actor_email: str
    action: str
    target_type: str
    target_id: str | None
    metadata_json: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    """Response for paginated audit logs."""

    logs: list[AuditLogResponse]
    total: int
    page: int
    page_size: int


class AuditLogFilters(BaseModel):
    """Filters for audit log queries."""

    action: str | None = None
    target_type: str | None = None
    actor_user_id: int | None = None
    page: int = 1
    page_size: int = 20
