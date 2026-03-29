"""Admin audit logs endpoints."""


from fastapi import APIRouter, Query

from app.api.deps import AdminUser, DbSession
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogListResponse, AuditLogResponse

router = APIRouter(prefix="/audit-logs", tags=["admin-audit-logs"])


def _audit_log_to_response(log: AuditLog) -> AuditLogResponse:
    """Convert AuditLog model to response schema."""
    return AuditLogResponse(
        id=log.id,
        actor_email=log.actor.email,
        action=log.action,
        target_type=log.target_type,
        target_id=log.target_id,
        metadata_json=log.metadata_json,
        created_at=log.created_at,
    )


@router.get("", response_model=AuditLogListResponse)
def list_audit_logs(
    db: DbSession,
    current_user: AdminUser,
    action: str | None = Query(None, description="Filter by action type"),
    target_type: str | None = Query(None, description="Filter by target type"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> AuditLogListResponse:
    """List audit logs with filters and pagination."""
    query = db.query(AuditLog)

    if action:
        query = query.filter(AuditLog.action == action)
    if target_type:
        query = query.filter(AuditLog.target_type == target_type)

    # Get total count
    total = query.count()

    # Apply pagination and ordering
    logs = (
        query.order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return AuditLogListResponse(
        logs=[_audit_log_to_response(log) for log in logs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{log_id}", response_model=AuditLogResponse)
def get_audit_log(
    log_id: int,
    db: DbSession,
    current_user: AdminUser,
) -> AuditLogResponse:
    """Get a specific audit log entry."""
    log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
    if not log:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found",
        )
    return _audit_log_to_response(log)
