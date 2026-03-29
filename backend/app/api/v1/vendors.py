"""Runs and Vendors API endpoints."""

import json

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, DbSession
from app.models.procurement_request import ProcurementRequest
from app.models.search_run import SearchRun
from app.models.vendor import Vendor
from app.models.vendor_asset import VendorAsset
from app.models.vendor_evidence import VendorFieldEvidence
from app.models.vendor_metrics import VendorMetrics
from app.models.vendor_source import VendorSource
from app.schemas.vendor import (
    SearchRunDetailResponse,
    VendorAssetResponse,
    VendorEvidenceResponse,
    VendorListResponse,
    VendorMetricsResponse,
    VendorResponse,
    VendorSourceResponse,
)

router = APIRouter(tags=["runs", "vendors"])


def _vendor_to_response(vendor: Vendor) -> VendorResponse:
    """Convert Vendor model to response with computed fields."""
    from app.schemas.vendor import ShoppingProductResponse, VendorShoppingData, VendorStructuredData

    # Get primary logo
    logo_url = None
    if vendor.assets:
        logo_assets = [a for a in vendor.assets if a.asset_type == "LOGO"]
        if logo_assets:
            logo_assets.sort(key=lambda x: x.priority)
            logo_url = logo_assets[0].asset_url

    # Get metrics with DeepResearch quality fields
    metrics_resp = None
    if vendor.metrics:
        metrics_resp = VendorMetricsResponse(
            fit_score=vendor.metrics.fit_score,
            trust_score=vendor.metrics.trust_score,
            overall_score=vendor.metrics.overall_score,
            must_have_matched=vendor.metrics.must_have_matched,
            must_have_total=vendor.metrics.must_have_total,
            nice_to_have_matched=vendor.metrics.nice_to_have_matched,
            nice_to_have_total=vendor.metrics.nice_to_have_total,
            source_count=vendor.metrics.source_count,
            evidence_count=vendor.metrics.evidence_count,
            # DeepResearch quality fields
            quality_score=vendor.metrics.quality_score,
            price_score=vendor.metrics.price_score,
            completeness_pct=vendor.metrics.completeness_pct,
            confidence_pct=vendor.metrics.confidence_pct,
            source_diversity=vendor.metrics.source_diversity,
            research_depth=vendor.metrics.research_depth,
            price_competitiveness=vendor.metrics.price_competitiveness,
        )

    # Parse structured data if present
    structured = None
    if vendor.structured_data:
        try:
            data = json.loads(vendor.structured_data)
            structured = VendorStructuredData(**data)
        except (json.JSONDecodeError, TypeError):
            structured = None

    # Parse shopping data if present
    shopping = None
    if vendor.shopping_data:
        try:
            data = json.loads(vendor.shopping_data)
            products = []
            for p in data.get("products", [])[:10]:  # Limit to 10 products
                products.append(ShoppingProductResponse(
                    title=p.get("title", ""),
                    price=p.get("price"),
                    price_raw=p.get("price_raw", ""),
                    currency=p.get("currency", "IDR"),
                    source=p.get("source", ""),
                    link=p.get("link", ""),
                    thumbnail=p.get("thumbnail"),
                    rating=p.get("rating"),
                    reviews_count=p.get("reviews_count"),
                ))
            shopping = VendorShoppingData(
                vendor_name=data.get("vendor_name"),
                products=products,
                price_min=data.get("price_min"),
                price_max=data.get("price_max"),
                price_avg=data.get("price_avg"),
                market_avg=data.get("market_avg"),
                price_competitiveness=data.get("price_competitiveness"),
                sources=data.get("sources", []),
            )
        except (json.JSONDecodeError, TypeError):
            shopping = None

    return VendorResponse(
        id=vendor.id,
        name=vendor.name,
        website=vendor.website,
        description=vendor.description,
        location=vendor.location,
        country=vendor.country,
        industry=vendor.industry,
        founded_year=vendor.founded_year,
        employee_count=vendor.employee_count,
        email=vendor.email,
        phone=vendor.phone,
        pricing_model=vendor.pricing_model,
        pricing_details=vendor.pricing_details,
        security_compliance=vendor.security_compliance,
        deployment=vendor.deployment,
        integrations=vendor.integrations,
        structured_data=structured,
        shopping_data=shopping,
        price_range_min=vendor.price_range_min,
        price_range_max=vendor.price_range_max,
        price_last_updated=vendor.price_last_updated,
        created_at=vendor.created_at,
        updated_at=vendor.updated_at,
        logo_url=logo_url,
        metrics=metrics_resp,
    )



# -------------------- RUNS ENDPOINTS --------------------


@router.get("/runs/{run_id}", response_model=SearchRunDetailResponse)
def get_run(
    run_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> SearchRunDetailResponse:
    """Get search run status by ID."""
    from app.schemas.vendor import CategoryBenchmark, SearchRunShoppingData

    run = (
        db.query(SearchRun)
        .join(ProcurementRequest, SearchRun.request_id == ProcurementRequest.id)
        .filter(
            SearchRun.id == run_id,
            ProcurementRequest.created_by_user_id == current_user.id,
        )
        .first()
    )
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    # Parse quality assessment
    quality_assessment = None
    if run.quality_assessment:
        try:
            quality_assessment = json.loads(run.quality_assessment)
        except (json.JSONDecodeError, TypeError):
            quality_assessment = None

    # Parse shopping data
    shopping_data_resp = None
    if run.shopping_data:
        try:
            data = json.loads(run.shopping_data)
            category_benchmark = None
            if data.get("category_benchmark"):
                cb = data["category_benchmark"]
                category_benchmark = CategoryBenchmark(
                    category=cb.get("category"),
                    price_min=cb.get("price_min"),
                    price_max=cb.get("price_max"),
                    price_avg=cb.get("price_avg"),
                    price_median=cb.get("price_median"),
                    sample_size=cb.get("sample_size", 0),
                    sources=cb.get("sources", []),
                )
            shopping_data_resp = SearchRunShoppingData(
                category_benchmark=category_benchmark,
                market_avg=data.get("market_avg"),
                total_products=data.get("total_products", 0),
                search_queries=data.get("search_queries", []),
            )
        except (json.JSONDecodeError, TypeError):
            shopping_data_resp = None

    # Parse pipeline logs
    pipeline_logs = None
    if run.pipeline_logs:
        try:
            pipeline_logs = json.loads(run.pipeline_logs)
        except (json.JSONDecodeError, TypeError):
            pipeline_logs = None

    # Parse token usage
    token_usage = None
    if run.token_usage:
        try:
            token_usage = json.loads(run.token_usage)
        except (json.JSONDecodeError, TypeError):
            token_usage = None

    return SearchRunDetailResponse(
        id=run.id,
        request_id=run.request_id,
        status=run.status,
        current_step=run.current_step,
        progress_pct=run.progress_pct,
        vendors_found=run.vendors_found,
        sources_searched=run.sources_searched,
        error_message=run.error_message,
        research_iterations=run.research_iterations,
        quality_assessment=quality_assessment,
        shopping_data=shopping_data_resp,
        pipeline_logs=pipeline_logs,
        token_usage=token_usage,
        started_at=run.started_at,
        completed_at=run.completed_at,
        created_at=run.created_at,
    )


@router.post("/runs/{run_id}/cancel", response_model=SearchRunDetailResponse)
def cancel_run(
    run_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> SearchRunDetailResponse:
    """Cancel an active search run.

    Only QUEUED or RUNNING runs can be cancelled.
    """
    from datetime import datetime, timezone

    run = (
        db.query(SearchRun)
        .join(ProcurementRequest, SearchRun.request_id == ProcurementRequest.id)
        .filter(
            SearchRun.id == run_id,
            ProcurementRequest.created_by_user_id == current_user.id,
        )
        .first()
    )
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    # Check if run can be cancelled
    if run.status not in ("QUEUED", "RUNNING"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel {run.status} run. Only QUEUED/RUNNING allowed.",
        )

    # Update run status
    run.status = "CANCELLED"
    run.error_message = "Cancelled by user"
    run.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(run)

    return SearchRunDetailResponse(
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


@router.get("/runs/{run_id}/vendors", response_model=VendorListResponse)
def list_run_vendors(
    run_id: int,
    db: DbSession,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query(
        "overall_score",
        pattern="^(overall_score|fit_score|trust_score|name|created_at)$",
    ),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    q: str | None = Query(None, description="Search by vendor name or website"),
) -> VendorListResponse:
    """List vendors discovered in a search run."""
    # Verify run ownership
    run = (
        db.query(SearchRun)
        .join(ProcurementRequest, SearchRun.request_id == ProcurementRequest.id)
        .filter(
            SearchRun.id == run_id,
            ProcurementRequest.created_by_user_id == current_user.id,
        )
        .first()
    )
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    # Query vendors via sources
    vendor_ids = (
        db.query(VendorSource.vendor_id)
        .filter(VendorSource.search_run_id == run_id)
        .distinct()
        .subquery()
    )

    query = db.query(Vendor).filter(Vendor.id.in_(db.query(vendor_ids)))

    # Search filter
    if q:
        search_term = f"%{q}%"
        query = query.filter(
            (Vendor.name.ilike(search_term)) | (Vendor.website.ilike(search_term))
        )

    total = query.count()

    # Sorting
    if sort_by in ("overall_score", "fit_score", "trust_score"):
        query = query.outerjoin(VendorMetrics, Vendor.id == VendorMetrics.vendor_id)
        if sort_by == "overall_score":
            order_col = VendorMetrics.overall_score
        elif sort_by == "fit_score":
            order_col = VendorMetrics.fit_score
        else:
            order_col = VendorMetrics.trust_score
    elif sort_by == "name":
        order_col = Vendor.name
    else:
        order_col = Vendor.created_at

    if sort_order == "desc":
        query = query.order_by(order_col.desc().nullslast())
    else:
        query = query.order_by(order_col.asc().nullsfirst())

    vendors = query.offset((page - 1) * page_size).limit(page_size).all()

    return VendorListResponse(
        vendors=[_vendor_to_response(v) for v in vendors],
        total=total,
        page=page,
        page_size=page_size,
    )


# -------------------- VENDORS ENDPOINTS --------------------


@router.get("/vendors/{vendor_id}", response_model=VendorResponse)
def get_vendor(
    vendor_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> VendorResponse:
    """Get vendor by ID."""
    # Verify user has access via any of their runs
    has_access = (
        db.query(VendorSource)
        .join(SearchRun, VendorSource.search_run_id == SearchRun.id)
        .join(ProcurementRequest, SearchRun.request_id == ProcurementRequest.id)
        .filter(
            VendorSource.vendor_id == vendor_id,
            ProcurementRequest.created_by_user_id == current_user.id,
        )
        .first()
    )
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found",
        )

    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found",
        )

    return _vendor_to_response(vendor)


@router.get("/vendors/{vendor_id}/evidence", response_model=list[VendorEvidenceResponse])
def get_vendor_evidence(
    vendor_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> list[VendorEvidenceResponse]:
    """Get all evidence for a vendor's extracted fields."""
    # Verify access
    has_access = (
        db.query(VendorSource)
        .join(SearchRun, VendorSource.search_run_id == SearchRun.id)
        .join(ProcurementRequest, SearchRun.request_id == ProcurementRequest.id)
        .filter(
            VendorSource.vendor_id == vendor_id,
            ProcurementRequest.created_by_user_id == current_user.id,
        )
        .first()
    )
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found",
        )

    evidence = (
        db.query(VendorFieldEvidence)
        .filter(VendorFieldEvidence.vendor_id == vendor_id)
        .order_by(VendorFieldEvidence.field_name)
        .all()
    )

    return [
        VendorEvidenceResponse(
            id=e.id,
            field_name=e.field_name,
            field_value=e.field_value,
            evidence_url=e.evidence_url,
            evidence_snippet=e.evidence_snippet,
            confidence=e.confidence,
            extraction_method=e.extraction_method,
            extracted_at=e.extracted_at,
        )
        for e in evidence
    ]


@router.get("/vendors/{vendor_id}/sources", response_model=list[VendorSourceResponse])
def get_vendor_sources(
    vendor_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> list[VendorSourceResponse]:
    """Get all sources for a vendor."""
    # Verify access
    has_access = (
        db.query(VendorSource)
        .join(SearchRun, VendorSource.search_run_id == SearchRun.id)
        .join(ProcurementRequest, SearchRun.request_id == ProcurementRequest.id)
        .filter(
            VendorSource.vendor_id == vendor_id,
            ProcurementRequest.created_by_user_id == current_user.id,
        )
        .first()
    )
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found",
        )

    sources = (
        db.query(VendorSource)
        .filter(VendorSource.vendor_id == vendor_id)
        .order_by(VendorSource.fetched_at.desc())
        .all()
    )

    return [
        VendorSourceResponse(
            id=s.id,
            source_url=s.source_url,
            source_type=s.source_type,
            page_title=s.page_title,
            fetch_status=s.fetch_status,
            fetched_at=s.fetched_at,
        )
        for s in sources
    ]


@router.get("/vendors/{vendor_id}/assets", response_model=list[VendorAssetResponse])
def get_vendor_assets(
    vendor_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> list[VendorAssetResponse]:
    """Get all assets (logos, etc.) for a vendor."""
    # Verify access
    has_access = (
        db.query(VendorSource)
        .join(SearchRun, VendorSource.search_run_id == SearchRun.id)
        .join(ProcurementRequest, SearchRun.request_id == ProcurementRequest.id)
        .filter(
            VendorSource.vendor_id == vendor_id,
            ProcurementRequest.created_by_user_id == current_user.id,
        )
        .first()
    )
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found",
        )

    assets = (
        db.query(VendorAsset)
        .filter(VendorAsset.vendor_id == vendor_id)
        .order_by(VendorAsset.priority)
        .all()
    )

    return [
        VendorAssetResponse(
            id=a.id,
            asset_type=a.asset_type,
            asset_url=a.asset_url,
            source_url=a.source_url,
            mime_type=a.mime_type,
            width=a.width,
            height=a.height,
            priority=a.priority,
        )
        for a in assets
    ]
