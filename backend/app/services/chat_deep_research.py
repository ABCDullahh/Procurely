"""Chat DeepResearch service for triggering web search from chat when no vendors found."""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.procurement_request import ProcurementRequest, RequestStatus
from app.models.search_run import SearchRun
from app.models.vendor import Vendor
from app.models.vendor_asset import VendorAsset
from app.models.vendor_metrics import VendorMetrics
from app.models.vendor_source import VendorSource
from app.services.pipeline.runner import PipelineRunner

logger = logging.getLogger(__name__)


# Default providers for chat-triggered searches (faster config)
CHAT_DEFAULT_PROVIDERS = ["SERPER", "JINA_READER"]

# Fast research config for chat (less iterations, faster results)
CHAT_RESEARCH_CONFIG = {
    "max_iterations": 1,  # Faster for chat
    "gap_threshold": 0.5,
    "include_shopping": True,
    "enabled": True,
}


@dataclass
class ChatResearchResult:
    """Result from chat-triggered research."""

    request_id: int
    run_id: int
    status: str
    current_step: str | None
    progress_pct: int
    vendors_found: int
    partial_vendors: list[dict] | None
    error_message: str | None


def run_chat_pipeline_background(run_id: int) -> None:
    """Run pipeline in background thread with new DB session for chat.

    Uses DeepResearch with fast config (1 iteration).
    """
    db = SessionLocal()
    try:
        runner = PipelineRunner(db, run_id)
        logger.info(f"Starting chat DeepResearch pipeline for run {run_id}")
        asyncio.run(runner.run_deep_research_pipeline())
    except Exception as e:
        logger.exception(f"Chat pipeline failed: {e}")
        # Mark run as failed
        run = db.query(SearchRun).filter(SearchRun.id == run_id).first()
        if run:
            run.status = "FAILED"
            run.error_message = str(e)
            db.commit()
    finally:
        db.close()


async def create_ephemeral_request(
    db: Session,
    user_id: int,
    category: str,
    keywords: list[str],
    location: str | None = None,
    budget_max: int | None = None,
) -> tuple[ProcurementRequest, SearchRun]:
    """Create an internal (ephemeral) request for chat-triggered research.

    Args:
        db: Database session
        user_id: User ID triggering the search
        category: Product/service category
        keywords: Search keywords
        location: Optional location filter
        budget_max: Optional max budget

    Returns:
        Tuple of (ProcurementRequest, SearchRun)
    """
    # Create ephemeral request (not shown in user's main list)
    request = ProcurementRequest(
        title=f"Chat: {category or keywords[0] if keywords else 'Search'}",
        description=f"Auto-generated from chat search for: {', '.join(keywords)}",
        category=category or "Other",
        keywords=json.dumps(keywords),
        location=location,
        budget_max=budget_max,
        selected_providers=json.dumps(CHAT_DEFAULT_PROVIDERS),
        research_config=json.dumps(CHAT_RESEARCH_CONFIG),
        locale="id_ID",
        country_code="ID",
        region_bias=True,
        status=RequestStatus.PENDING.value,
        created_by_user_id=user_id,
        is_ephemeral=True,
        source="CHAT",
    )
    db.add(request)
    db.commit()
    db.refresh(request)

    # Create search run
    search_run = SearchRun(
        request_id=request.id,
        status="QUEUED",
        current_step="initializing",
        progress_pct=0,
    )
    db.add(search_run)
    db.commit()
    db.refresh(search_run)

    logger.info(f"Created ephemeral request {request.id} with run {search_run.id}")

    return request, search_run


async def start_chat_research(
    db: Session,
    user_id: int,
    category: str,
    keywords: list[str],
    location: str | None = None,
    budget_max: int | None = None,
) -> ChatResearchResult:
    """Start a chat-triggered DeepResearch pipeline.

    This creates an ephemeral request and starts the search pipeline
    in the background.

    Args:
        db: Database session
        user_id: User ID
        category: Search category
        keywords: Search keywords
        location: Optional location
        budget_max: Optional budget

    Returns:
        ChatResearchResult with initial status
    """
    from concurrent.futures import ThreadPoolExecutor

    # Create ephemeral request and run
    request, run = await create_ephemeral_request(
        db=db,
        user_id=user_id,
        category=category,
        keywords=keywords,
        location=location,
        budget_max=budget_max,
    )

    # Start pipeline in background thread
    executor = ThreadPoolExecutor(max_workers=1)
    executor.submit(run_chat_pipeline_background, run.id)
    executor.shutdown(wait=False)

    return ChatResearchResult(
        request_id=request.id,
        run_id=run.id,
        status="QUEUED",
        current_step="initializing",
        progress_pct=0,
        vendors_found=0,
        partial_vendors=None,
        error_message=None,
    )


def get_research_status(db: Session, run_id: int) -> ChatResearchResult | None:
    """Get current status of a chat research run.

    Includes partial vendors as they are discovered.

    Args:
        db: Database session
        run_id: Search run ID

    Returns:
        ChatResearchResult with current status and partial vendors
    """
    run = db.query(SearchRun).filter(SearchRun.id == run_id).first()
    if not run:
        return None

    # Get partial vendors if any discovered
    partial_vendors = None
    if run.vendors_found and run.vendors_found > 0:
        partial_vendors = get_run_vendors(db, run_id, limit=10)

    return ChatResearchResult(
        request_id=run.request_id,
        run_id=run.id,
        status=run.status,
        current_step=run.current_step,
        progress_pct=run.progress_pct or 0,
        vendors_found=run.vendors_found or 0,
        partial_vendors=partial_vendors,
        error_message=run.error_message,
    )


def get_run_vendors(db: Session, run_id: int, limit: int = 10) -> list[dict]:
    """Get vendors from a run with their data.

    Args:
        db: Database session
        run_id: Search run ID
        limit: Max vendors to return

    Returns:
        List of vendor data dictionaries
    """
    # Get vendors from this run
    vendors_query = (
        db.query(Vendor, VendorMetrics)
        .join(VendorSource, Vendor.id == VendorSource.vendor_id)
        .outerjoin(
            VendorMetrics,
            (VendorMetrics.vendor_id == Vendor.id)
            & (VendorMetrics.search_run_id == run_id),
        )
        .filter(VendorSource.search_run_id == run_id)
        .order_by(VendorMetrics.overall_score.desc().nullslast())
        .limit(limit)
        .all()
    )

    vendors = []
    for vendor, metrics in vendors_query:
        # Get logo
        logo = (
            db.query(VendorAsset)
            .filter(VendorAsset.vendor_id == vendor.id, VendorAsset.asset_type == "LOGO")
            .order_by(VendorAsset.priority)
            .first()
        )

        vendors.append({
            "id": vendor.id,
            "name": vendor.name,
            "website": vendor.website,
            "logo_url": logo.asset_url if logo else None,
            "industry": vendor.industry,
            "location": vendor.location,
            "country": vendor.country,
            "description": vendor.description[:200] if vendor.description else None,
            "overall_score": metrics.overall_score if metrics else None,
            "fit_score": metrics.fit_score if metrics else None,
            "trust_score": metrics.trust_score if metrics else None,
            "pricing_model": vendor.pricing_model,
            "pricing_details": vendor.pricing_details,
        })

    return vendors


async def cancel_research(db: Session, run_id: int) -> bool:
    """Cancel an ongoing chat research.

    Args:
        db: Database session
        run_id: Search run ID

    Returns:
        True if cancelled successfully
    """
    run = db.query(SearchRun).filter(SearchRun.id == run_id).first()
    if not run:
        return False

    if run.status in ["QUEUED", "RUNNING"]:
        run.status = "CANCELLED"
        run.error_message = "Cancelled by user"
        db.commit()
        return True

    return False


def should_trigger_deep_research(
    db_vendor_count: int,
    avg_score: float | None = None,
    threshold_count: int = 3,
    threshold_score: float = 50.0,
) -> bool:
    """Determine if DeepResearch should be triggered.

    Triggers when:
    - Less than threshold_count vendors found in DB
    - OR average score is below threshold_score

    Args:
        db_vendor_count: Number of vendors found in database
        avg_score: Average overall score of found vendors
        threshold_count: Minimum vendors needed (default 3)
        threshold_score: Minimum average score (default 50)

    Returns:
        True if DeepResearch should be triggered
    """
    if db_vendor_count < threshold_count:
        return True

    if avg_score is not None and avg_score < threshold_score:
        return True

    return False
