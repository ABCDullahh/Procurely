"""Procurement request CRUD endpoints."""

import asyncio
import json
import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request, status

from app.api.deps import CurrentUser, DbSession
from app.core.rate_limit import check_ip_rate_limit, check_llm_daily_limit
from app.core.database import SessionLocal
from app.models.procurement_request import ProcurementRequest, RequestStatus
from app.models.search_run import SearchRun
from app.schemas.procurement_request import (
    KeywordGenerationRequest,
    KeywordGenerationResponse,
    ProcurementRequestCreate,
    ProcurementRequestListResponse,
    ProcurementRequestResponse,
    ProcurementRequestUpdate,
    SearchRunResponse,
)
from app.services.keyword_generator import generate_keywords_from_text
from app.services.pipeline.runner import PipelineRunner

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/requests", tags=["procurement-requests"])


# Default providers to use when not specified
DEFAULT_PROVIDERS = ["SERPER", "JINA_READER"]


@router.post("/generate-keywords", response_model=KeywordGenerationResponse)
async def generate_keywords(
    data: KeywordGenerationRequest,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
) -> KeywordGenerationResponse:
    """Generate search keywords from title and description using LLM."""
    check_ip_rate_limit(request, max_requests=10, window_seconds=60, endpoint_tag="keywords")
    check_llm_daily_limit()
    keywords = await generate_keywords_from_text(
        db=db,
        title=data.title,
        description=data.description,
        category=data.category,
    )
    return KeywordGenerationResponse(keywords=keywords)


def run_pipeline_background(run_id: int, use_deep_research: bool = True) -> None:
    """Run pipeline in background thread with new DB session.

    Args:
        run_id: The SearchRun ID to execute
        use_deep_research: If True, uses the DeepResearch-enhanced pipeline with
                          Indonesia focus, iterative gap analysis, shopping search,
                          and quality assessment. Defaults to True.
    """
    logger.info("TASK STARTED: run_id=%d, use_deep_research=%s", run_id, use_deep_research)

    db = SessionLocal()
    try:
        logger.info("Starting %s pipeline for run %d",
                     "DeepResearch" if use_deep_research else "legacy", run_id)

        runner = PipelineRunner(db, run_id)
        if use_deep_research:
            asyncio.run(runner.run_deep_research_pipeline())
        else:
            asyncio.run(runner.run_pipeline())

        logger.info("TASK COMPLETED: run_id=%d", run_id)
    except Exception as e:
        logger.exception("TASK FAILED: run_id=%d, error=%s", run_id, e)
    finally:
        db.close()



def _request_to_response(
    request: ProcurementRequest,
    latest_run: SearchRun | None = None,
) -> ProcurementRequestResponse:
    """Convert ProcurementRequest model to response schema."""
    # Parse research config if present
    research_config = None
    if request.research_config:
        try:
            research_config = json.loads(request.research_config)
        except (json.JSONDecodeError, TypeError):
            pass

    def _safe_json_loads(value: str | None, default=None):
        """Safely parse a JSON string, returning default on failure."""
        if not value:
            return default
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Malformed JSON in DB field: %s", value[:100] if value else "")
            return default

    return ProcurementRequestResponse(
        id=request.id,
        title=request.title,
        description=request.description,
        category=request.category,
        keywords=_safe_json_loads(request.keywords, default=[]),
        location=request.location,
        budget_min=request.budget_min,
        budget_max=request.budget_max,
        timeline=request.timeline,
        must_have_criteria=_safe_json_loads(request.must_have_criteria),
        nice_to_have_criteria=_safe_json_loads(request.nice_to_have_criteria),
        selected_providers=_safe_json_loads(request.selected_providers),
        locale=getattr(request, 'locale', 'id_ID') or 'id_ID',
        country_code=getattr(request, 'country_code', 'ID') or 'ID',
        region_bias=getattr(request, 'region_bias', True),
        research_config=research_config,
        status=request.status,
        created_by_email=request.created_by.email,
        created_at=request.created_at,
        updated_at=request.updated_at,
        latest_run_status=latest_run.status if latest_run else None,
        vendors_found=latest_run.vendors_found if latest_run else 0,
    )


@router.get("", response_model=ProcurementRequestListResponse)
def list_requests(
    db: DbSession,
    current_user: CurrentUser,
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    include_ephemeral: bool = Query(False),
) -> ProcurementRequestListResponse:
    """List procurement requests for current user."""
    from sqlalchemy import and_, func

    # RUN_STATUSES are statuses that come from SearchRun, not ProcurementRequest
    RUN_STATUSES = {"RUNNING", "COMPLETED", "FAILED", "QUEUED", "CANCELLED"}

    base_query = db.query(ProcurementRequest).filter(
        ProcurementRequest.created_by_user_id == current_user.id
    )

    # Filter out ephemeral (chat-generated) requests by default
    if not include_ephemeral:
        base_query = base_query.filter(ProcurementRequest.is_ephemeral == False)

    # Handle status filter - some statuses need to filter by SearchRun
    if status_filter:
        if status_filter in RUN_STATUSES:
            # Filter by latest SearchRun status using subquery
            # Get request IDs where the latest run has the specified status
            latest_run_subq = (
                db.query(
                    SearchRun.request_id,
                    func.max(SearchRun.id).label("max_id")
                )
                .group_by(SearchRun.request_id)
                .subquery()
            )

            request_ids_with_status = (
                db.query(SearchRun.request_id)
                .join(
                    latest_run_subq,
                    and_(
                        SearchRun.request_id == latest_run_subq.c.request_id,
                        SearchRun.id == latest_run_subq.c.max_id
                    )
                )
                .filter(SearchRun.status == status_filter)
                .all()
            )
            request_ids = [r[0] for r in request_ids_with_status]

            if request_ids:
                base_query = base_query.filter(ProcurementRequest.id.in_(request_ids))
            else:
                # No matching requests, return empty
                return ProcurementRequestListResponse(
                    requests=[],
                    total=0,
                    page=page,
                    page_size=page_size,
                )
        else:
            # Filter by ProcurementRequest.status (DRAFT, PENDING)
            base_query = base_query.filter(ProcurementRequest.status == status_filter)

    total = base_query.count()
    requests = (
        base_query.order_by(ProcurementRequest.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # Get latest run per request using a subquery (avoids fetching all runs)
    request_ids = [r.id for r in requests]
    latest_runs: dict[int, SearchRun] = {}
    if request_ids:
        latest_run_subq = (
            db.query(
                SearchRun.request_id,
                func.max(SearchRun.id).label("max_id"),
            )
            .filter(SearchRun.request_id.in_(request_ids))
            .group_by(SearchRun.request_id)
            .subquery()
        )
        runs = (
            db.query(SearchRun)
            .join(
                latest_run_subq,
                and_(
                    SearchRun.request_id == latest_run_subq.c.request_id,
                    SearchRun.id == latest_run_subq.c.max_id,
                ),
            )
            .all()
        )
        for run in runs:
            latest_runs[run.request_id] = run

    return ProcurementRequestListResponse(
        requests=[
            _request_to_response(r, latest_runs.get(r.id)) for r in requests
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=ProcurementRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_request(
    data: ProcurementRequestCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> ProcurementRequestResponse:
    """Create a new procurement request.

    Keywords are auto-generated from title/description if not provided.
    Smart defaults are applied for locale, region_bias, and providers.
    """
    # Auto-generate keywords if not provided
    keywords = data.keywords
    if (not keywords or len(keywords) == 0) and data.auto_generate_keywords:
        logger.info(f"Auto-generating keywords for: {data.title}")
        keywords = await generate_keywords_from_text(
            db=db,
            title=data.title,
            description=data.description,
            category=data.category,
        )

    # Ensure we have at least one keyword
    if not keywords or len(keywords) == 0:
        if data.category:
            keywords = [data.category.lower()]
        else:
            keywords = ["general"]

    # Apply default providers if not specified
    selected_providers = data.selected_providers
    if not selected_providers or len(selected_providers) == 0:
        selected_providers = DEFAULT_PROVIDERS

    # Build research config with defaults if not provided
    research_config = None
    if data.research_config:
        research_config = json.dumps(data.research_config.model_dump())
    else:
        # Apply smart defaults
        research_config = json.dumps({
            "max_iterations": 2,
            "gap_threshold": 0.6,
            "include_shopping": True,
        })

    request = ProcurementRequest(
        title=data.title,
        description=data.description,
        category=data.category,
        keywords=json.dumps(keywords),
        location=data.location,
        budget_min=data.budget_min,
        budget_max=data.budget_max,
        timeline=data.timeline,
        must_have_criteria=(
            json.dumps(data.must_have_criteria) if data.must_have_criteria else None
        ),
        nice_to_have_criteria=(
            json.dumps(data.nice_to_have_criteria) if data.nice_to_have_criteria else None
        ),
        selected_providers=json.dumps(selected_providers),
        locale=data.locale,
        country_code=data.country_code,
        region_bias=data.region_bias,
        research_config=research_config,
        status=RequestStatus.DRAFT.value,
        created_by_user_id=current_user.id,
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return _request_to_response(request)


@router.get("/{request_id}", response_model=ProcurementRequestResponse)
def get_request(
    request_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> ProcurementRequestResponse:
    """Get a procurement request by ID."""
    request = (
        db.query(ProcurementRequest)
        .filter(
            ProcurementRequest.id == request_id,
            ProcurementRequest.created_by_user_id == current_user.id,
        )
        .first()
    )
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found",
        )

    # Get latest run
    latest_run = (
        db.query(SearchRun)
        .filter(SearchRun.request_id == request_id)
        .order_by(SearchRun.created_at.desc())
        .first()
    )

    return _request_to_response(request, latest_run)


@router.put("/{request_id}", response_model=ProcurementRequestResponse)
def update_request(
    request_id: int,
    data: ProcurementRequestUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> ProcurementRequestResponse:
    """Update a procurement request."""
    request = (
        db.query(ProcurementRequest)
        .filter(
            ProcurementRequest.id == request_id,
            ProcurementRequest.created_by_user_id == current_user.id,
        )
        .first()
    )
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found",
        )

    # Only allow updates to DRAFT requests
    if request.status != RequestStatus.DRAFT.value and data.status is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only update draft requests",
        )

    # Fields that must be JSON-serializable lists
    _json_list_fields = {"keywords", "must_have_criteria", "nice_to_have_criteria", "selected_providers"}

    # Apply updates
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field in _json_list_fields and value is not None:
            # Validate that the value is a proper list before serializing
            if not isinstance(value, list):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Field '{field}' must be a list",
                )
            try:
                setattr(request, field, json.dumps(value))
            except (TypeError, ValueError) as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Field '{field}' contains non-serializable data: {exc}",
                )
        elif field == "status" and value is not None:
            setattr(request, field, value.value)
        else:
            setattr(request, field, value)

    db.commit()
    db.refresh(request)
    return _request_to_response(request)


@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_request(
    request_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """Delete a procurement request."""
    request = (
        db.query(ProcurementRequest)
        .filter(
            ProcurementRequest.id == request_id,
            ProcurementRequest.created_by_user_id == current_user.id,
        )
        .first()
    )
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found",
        )

    db.delete(request)
    db.commit()


@router.post("/{request_id}/submit", response_model=ProcurementRequestResponse)
async def submit_request(
    request_id: int,
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
) -> ProcurementRequestResponse:
    """Submit a draft request to start the search pipeline."""
    check_ip_rate_limit(request, max_requests=5, window_seconds=60, endpoint_tag="submit")
    check_llm_daily_limit()
    request = (
        db.query(ProcurementRequest)
        .filter(
            ProcurementRequest.id == request_id,
            ProcurementRequest.created_by_user_id == current_user.id,
        )
        .first()
    )
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found",
        )

    if request.status != RequestStatus.DRAFT.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only submit draft requests",
        )

    # Check tier limits
    if current_user.role != "admin" and getattr(current_user, 'tier', 'free') == "free":
        # Count completed + running searches for this user
        search_count = db.query(SearchRun).join(ProcurementRequest).filter(
            ProcurementRequest.created_by_user_id == current_user.id,
            SearchRun.status.in_(["COMPLETED", "RUNNING", "PENDING", "QUEUED"])
        ).count()
        if search_count >= 1:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Free tier allows 1 search only. Contact us for unlimited access.",
            )

    # Update status to pending
    request.status = RequestStatus.PENDING.value

    # Create a search run
    search_run = SearchRun(
        request_id=request_id,
        status="QUEUED",
    )
    db.add(search_run)
    db.commit()
    db.refresh(request)
    db.refresh(search_run)

    # Determine if we should use DeepResearch pipeline
    # DeepResearch is used by default, but can be disabled via research_config
    use_deep_research = True
    if request.research_config:
        try:
            config = json.loads(request.research_config)
            # Allow explicit disable via research_config
            use_deep_research = config.get("enabled", True)
        except (json.JSONDecodeError, TypeError):
            pass

    # Start pipeline in background
    # NOTE: Background tasks are in-process and will be lost on crash.
    # For production, consider using a persistent task queue (e.g., Celery + Redis).
    logger.info("SUBMIT: Adding background task for run %d, use_deep_research=%s",
                search_run.id, use_deep_research)
    background_tasks.add_task(run_pipeline_background, search_run.id, use_deep_research)
    logger.info("SUBMIT: Background task added for run %d", search_run.id)

    return _request_to_response(request, search_run)


@router.get("/{request_id}/runs", response_model=list[SearchRunResponse])
def list_request_runs(
    request_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> list[SearchRunResponse]:
    """List all search runs for a request."""
    request = (
        db.query(ProcurementRequest)
        .filter(
            ProcurementRequest.id == request_id,
            ProcurementRequest.created_by_user_id == current_user.id,
        )
        .first()
    )
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found",
        )

    runs = (
        db.query(SearchRun)
        .filter(SearchRun.request_id == request_id)
        .order_by(SearchRun.created_at.desc())
        .all()
    )

    return [
        SearchRunResponse(
            id=run.id,
            request_id=run.request_id,
            status=run.status,
            current_step=run.current_step,
            progress_pct=run.progress_pct,
            vendors_found=run.vendors_found,
            sources_searched=run.sources_searched,
            error_message=run.error_message,
            started_at=run.started_at,
            completed_at=run.completed_at,
            created_at=run.created_at,
        )
        for run in runs
    ]
