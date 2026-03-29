"""Copilot API endpoint for AI-assisted vendor analysis."""

from fastapi import APIRouter, HTTPException, Request, status

from app.api.deps import CurrentUser, DbSession
from app.core.rate_limit import check_ip_rate_limit, check_llm_daily_limit
from app.models import ProcurementRequest, SearchRun
from app.schemas.copilot import ChatRequest, ChatResponse
from app.services.copilot import (
    ConfigMissingError,
    CopilotError,
    run_copilot_chat,
)

router = APIRouter(prefix="/copilot", tags=["copilot"])


def get_run_with_rbac(run_id: int, db: DbSession, user_id: int) -> SearchRun:
    """Get run with RBAC check via request ownership."""
    run = db.query(SearchRun).filter(SearchRun.id == run_id).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    # Check ownership via procurement request
    request = (
        db.query(ProcurementRequest)
        .filter(ProcurementRequest.id == run.request_id)
        .first()
    )
    if not request or request.created_by_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return run


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
) -> ChatResponse:
    """Chat with the copilot about vendor search results."""
    # Rate limits: 10 req/min per IP + 200/day global
    check_ip_rate_limit(request, max_requests=10, window_seconds=60, endpoint_tag="copilot")
    remaining = check_llm_daily_limit()

    # RBAC check
    get_run_with_rbac(payload.run_id, db, current_user.id)

    try:
        response = await run_copilot_chat(db, payload.run_id, payload)
        return response
    except ConfigMissingError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"AI service not configured: {str(e)}",
        ) from e
    except CopilotError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
