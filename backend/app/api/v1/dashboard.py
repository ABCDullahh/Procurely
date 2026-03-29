"""Dashboard endpoint - aggregated stats for current user."""

import logging

from fastapi import APIRouter
from sqlalchemy import func

from app.api.deps import CurrentUser, DbSession
from app.core.redis import cache_delete, cache_get, cache_set
from app.models.procurement_request import ProcurementRequest
from app.models.search_run import SearchRun

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("")
def get_dashboard(
    db: DbSession,
    current_user: CurrentUser,
):
    """Get aggregated dashboard stats for the current user."""
    from app.schemas.dashboard import DashboardResponse, RecentRequest

    # Check cache first (TTL 5 minutes)
    cache_key = f"dashboard:{current_user.id}"
    cached = cache_get(cache_key)
    if cached:
        logger.debug("Dashboard cache hit for user %s", current_user.id)
        return DashboardResponse(**cached)

    # Get all requests for user
    user_requests = db.query(ProcurementRequest).filter(
        ProcurementRequest.created_by_user_id == current_user.id
    )

    total_requests = user_requests.count()

    # Build derived status counts from latest run status
    # We need to iterate through requests and get their actual status
    status_counts: dict[str, int] = {}
    all_requests = user_requests.all()
    for req in all_requests:
        latest_run = (
            db.query(SearchRun)
            .filter(SearchRun.request_id == req.id)
            .order_by(SearchRun.created_at.desc())
            .first()
        )
        # Derive display status from run or fallback to request status
        if latest_run:
            display_status = latest_run.status
        else:
            display_status = req.status

        status_counts[display_status] = status_counts.get(display_status, 0) + 1

    # Get total vendors found across all runs
    total_vendors_subq = (
        db.query(func.coalesce(func.sum(SearchRun.vendors_found), 0))
        .join(ProcurementRequest, SearchRun.request_id == ProcurementRequest.id)
        .filter(ProcurementRequest.created_by_user_id == current_user.id)
        .scalar()
    )
    total_vendors_found = total_vendors_subq or 0

    # Count completed requests (runs with COMPLETED status)
    completed_count = (
        db.query(func.count(func.distinct(SearchRun.request_id)))
        .join(ProcurementRequest, SearchRun.request_id == ProcurementRequest.id)
        .filter(
            ProcurementRequest.created_by_user_id == current_user.id,
            SearchRun.status == "COMPLETED",
        )
        .scalar()
    ) or 0

    # Get active runs count
    active_runs = (
        db.query(SearchRun)
        .join(ProcurementRequest, SearchRun.request_id == ProcurementRequest.id)
        .filter(
            ProcurementRequest.created_by_user_id == current_user.id,
            SearchRun.status.in_(["QUEUED", "RUNNING"]),
        )
        .count()
    )

    # Get recent requests (last 5)
    recent = (
        user_requests.order_by(ProcurementRequest.updated_at.desc())
        .limit(5)
        .all()
    )

    # Get latest run for each recent request
    recent_requests = []
    for req in recent:
        latest_run = (
            db.query(SearchRun)
            .filter(SearchRun.request_id == req.id)
            .order_by(SearchRun.created_at.desc())
            .first()
        )
        # Derive display status from latest run if available
        if latest_run:
            display_status = latest_run.status
        else:
            display_status = req.status

        recent_requests.append(
            RecentRequest(
                id=req.id,
                title=req.title,
                status=display_status,
                category=req.category,
                vendors_found=latest_run.vendors_found if latest_run else 0,
                updated_at=req.updated_at.isoformat(),
            )
        )

    response = DashboardResponse(
        total_requests=total_requests,
        requests_by_status=status_counts,
        total_vendors_found=total_vendors_found,
        recent_requests=recent_requests,
        active_runs=active_runs,
        completed_count=completed_count,
    )

    # Cache for 5 minutes (300 seconds)
    cache_set(cache_key, response.model_dump(), ttl=300)

    return response
