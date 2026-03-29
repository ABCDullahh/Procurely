"""Procurement Chat API endpoint for conversational AI search."""

from fastapi import APIRouter, HTTPException, Request, status

from app.api.deps import CurrentUser, DbSession
from app.core.rate_limit import check_ip_rate_limit, check_llm_daily_limit
from app.schemas.procurement_chat import (
    CancelResearchResponse,
    ProcurementChatRequest,
    ProcurementChatResponse,
    ResearchStatusResponse,
    StartResearchRequest,
    VendorCardData,
)
from app.services.chat_deep_research import (
    cancel_research,
    get_research_status,
    start_chat_research,
)
from app.services.procurement_chat import (
    ConfigMissingError,
    ProcurementChatError,
    process_chat_message,
)

router = APIRouter(prefix="/procurement-chat", tags=["procurement-chat"])


@router.post("/message", response_model=ProcurementChatResponse)
async def send_message(
    payload: ProcurementChatRequest,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
) -> ProcurementChatResponse:
    """Send a message to the procurement chat assistant."""
    # Rate limits: 10 req/min per IP + 200/day global
    check_ip_rate_limit(request, max_requests=10, window_seconds=60, endpoint_tag="chat")
    check_llm_daily_limit()

    try:
        response = await process_chat_message(
            db=db,
            user_id=current_user.id,
            payload=payload,
        )
        return response
    except ConfigMissingError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"AI service not configured: {str(e)}",
        ) from e
    except ProcurementChatError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}",
        ) from e


@router.post("/research/start", response_model=ResearchStatusResponse)
async def start_research(
    payload: StartResearchRequest,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
) -> ResearchStatusResponse:
    """Start a DeepResearch pipeline from chat."""
    # Rate limits: 5 req/min per IP + 200/day global (research is heavy)
    check_ip_rate_limit(request, max_requests=5, window_seconds=60, endpoint_tag="research")
    check_llm_daily_limit()

    try:
        result = await start_chat_research(
            db=db,
            user_id=current_user.id,
            category=payload.category,
            keywords=payload.keywords,
            location=payload.location,
            budget_max=payload.budget_max,
        )

        return ResearchStatusResponse(
            request_id=result.request_id,
            run_id=result.run_id,
            status=result.status,
            current_step=result.current_step,
            progress_pct=result.progress_pct,
            vendors_found=result.vendors_found,
            partial_vendors=None,
            error_message=result.error_message,
            is_complete=False,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start research: {str(e)}",
        ) from e


@router.get("/research/{run_id}/status", response_model=ResearchStatusResponse)
async def get_research_status_endpoint(
    run_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> ResearchStatusResponse:
    """Get the current status of a chat research run.

    Returns progress and partial vendors as they are discovered.
    """
    result = get_research_status(db, run_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research run not found",
        )

    # Convert partial vendors to VendorCardData
    partial_vendors = None
    if result.partial_vendors:
        partial_vendors = [
            VendorCardData(
                id=v["id"],
                name=v["name"],
                website=v.get("website"),
                logo_url=v.get("logo_url"),
                industry=v.get("industry"),
                location=v.get("location"),
                country=v.get("country"),
                description=v.get("description"),
                overall_score=v.get("overall_score"),
                fit_score=v.get("fit_score"),
                trust_score=v.get("trust_score"),
                pricing_model=v.get("pricing_model"),
                pricing_details=v.get("pricing_details"),
            )
            for v in result.partial_vendors
        ]

    return ResearchStatusResponse(
        request_id=result.request_id,
        run_id=result.run_id,
        status=result.status,
        current_step=result.current_step,
        progress_pct=result.progress_pct,
        vendors_found=result.vendors_found,
        partial_vendors=partial_vendors,
        error_message=result.error_message,
        is_complete=result.status in ["COMPLETED", "FAILED", "CANCELLED"],
    )


@router.post("/research/{run_id}/cancel", response_model=CancelResearchResponse)
async def cancel_research_endpoint(
    run_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> CancelResearchResponse:
    """Cancel an ongoing chat research run."""
    success = await cancel_research(db, run_id)

    if success:
        return CancelResearchResponse(
            success=True,
            message="Research cancelled successfully",
        )
    else:
        return CancelResearchResponse(
            success=False,
            message="Research could not be cancelled (may already be complete)",
        )
