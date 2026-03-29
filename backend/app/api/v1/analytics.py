"""Analytics API endpoints for run statistics and reporting."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import case, func

from app.api.deps import CurrentUser, DbSession
from app.models import (
    ProcurementRequest,
    SearchRun,
    Vendor,
    VendorMetrics,
    VendorSource,
)
from app.schemas.analytics import (
    AnalyticsResponse,
    AverageScores,
    CriteriaDataItem,
    Distributions,
    IndustryDistribution,
    LocationDistribution,
    PricingDataItem,
    RunSummary,
    ScoreBucket,
    ScoreBreakdown,
    TopVendor,
    Totals,
)

router = APIRouter(prefix="/runs", tags=["analytics"])


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


@router.get("/{run_id}/analytics", response_model=AnalyticsResponse)
def get_run_analytics(
    run_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> AnalyticsResponse:
    """Get analytics for a search run."""
    run = get_run_with_rbac(run_id, db, current_user.id)

    # Run summary
    duration_sec = None
    if run.started_at and run.completed_at:
        duration_sec = int((run.completed_at - run.started_at).total_seconds())

    run_summary = RunSummary(
        status=run.status,
        started_at=run.started_at,
        completed_at=run.completed_at,
        duration_sec=duration_sec,
    )

    # Get vendor IDs for this run via VendorSource
    vendor_ids_subq = (
        db.query(VendorSource.vendor_id)
        .filter(VendorSource.search_run_id == run_id)
        .distinct()
        .subquery()
    )

    # Totals
    vendors_count = (
        db.query(func.count(Vendor.id))
        .filter(Vendor.id.in_(db.query(vendor_ids_subq)))
        .scalar()
        or 0
    )

    sources_count = (
        db.query(func.count(VendorSource.id))
        .filter(VendorSource.search_run_id == run_id)
        .scalar()
        or 0
    )

    totals = Totals(vendors_count=vendors_count, sources_count=sources_count)

    # Vendors by location (top 10)
    location_dist = (
        db.query(
            Vendor.location.label("location"),
            func.count(Vendor.id).label("count"),
        )
        .filter(Vendor.id.in_(db.query(vendor_ids_subq)))
        .filter(Vendor.location.isnot(None))
        .filter(Vendor.location != "")
        .group_by(Vendor.location)
        .order_by(func.count(Vendor.id).desc())
        .limit(10)
        .all()
    )
    vendors_by_location = [
        LocationDistribution(location=row.location or "Unknown", count=row.count)
        for row in location_dist
    ]

    # Vendors by industry (top 10)
    industry_dist = (
        db.query(
            Vendor.industry.label("industry"),
            func.count(Vendor.id).label("count"),
        )
        .filter(Vendor.id.in_(db.query(vendor_ids_subq)))
        .filter(Vendor.industry.isnot(None))
        .filter(Vendor.industry != "")
        .group_by(Vendor.industry)
        .order_by(func.count(Vendor.id).desc())
        .limit(10)
        .all()
    )
    vendors_by_industry = [
        IndustryDistribution(industry=row.industry or "Unknown", count=row.count)
        for row in industry_dist
    ]

    # Score distribution (buckets: 0-20, 21-40, 41-60, 61-80, 81-100)
    score_buckets = (
        db.query(
            case(
                (VendorMetrics.overall_score <= 20, "0-20"),
                (VendorMetrics.overall_score <= 40, "21-40"),
                (VendorMetrics.overall_score <= 60, "41-60"),
                (VendorMetrics.overall_score <= 80, "61-80"),
                else_="81-100",
            ).label("range"),
            func.count(VendorMetrics.id).label("count"),
        )
        .filter(VendorMetrics.search_run_id == run_id)
        .filter(VendorMetrics.overall_score.isnot(None))
        .group_by("range")
        .all()
    )

    # Ensure all buckets exist
    bucket_order = ["0-20", "21-40", "41-60", "61-80", "81-100"]
    bucket_map = {row.range: row.count for row in score_buckets}
    score_distribution = [
        ScoreBucket(range=r, count=bucket_map.get(r, 0)) for r in bucket_order
    ]

    # Average scores
    avg_scores = (
        db.query(
            func.avg(VendorMetrics.fit_score).label("avg_fit"),
            func.avg(VendorMetrics.trust_score).label("avg_trust"),
            func.avg(VendorMetrics.overall_score).label("avg_overall"),
        )
        .filter(VendorMetrics.search_run_id == run_id)
        .first()
    )

    average_scores = AverageScores(
        avg_fit=round(avg_scores.avg_fit, 1) if avg_scores.avg_fit else None,
        avg_trust=round(avg_scores.avg_trust, 1) if avg_scores.avg_trust else None,
        avg_overall=round(avg_scores.avg_overall, 1) if avg_scores.avg_overall else None,
    )

    distributions = Distributions(
        vendors_by_location=vendors_by_location,
        vendors_by_industry=vendors_by_industry,
        score_distribution=score_distribution,
        average_scores=average_scores,
    )

    # Top 5 vendors by overall score
    top_vendors_query = (
        db.query(Vendor, VendorMetrics)
        .join(VendorMetrics, Vendor.id == VendorMetrics.vendor_id)
        .filter(VendorMetrics.search_run_id == run_id)
        .filter(VendorMetrics.overall_score.isnot(None))
        .order_by(VendorMetrics.overall_score.desc())
        .limit(5)
        .all()
    )

    top_vendors = [
        TopVendor(
            id=vendor.id,
            name=vendor.name,
            website=vendor.website,
            overall_score=metrics.overall_score,
            fit_score=metrics.fit_score,
            trust_score=metrics.trust_score,
            location=vendor.location,
            industry=vendor.industry,
        )
        for vendor, metrics in top_vendors_query
    ]

    # Pricing comparison data
    vendors = (
        db.query(Vendor)
        .filter(Vendor.id.in_(db.query(vendor_ids_subq)))
        .all()
    )
    pricing_data = []
    for v in vendors:
        if v.price_range_min or v.price_range_max:
            pricing_data.append(
                PricingDataItem(
                    name=v.name,
                    price_min=v.price_range_min,
                    price_max=v.price_range_max,
                    pricing_model=v.pricing_model,
                )
            )

    # Criteria matching per vendor
    vendor_metrics = (
        db.query(VendorMetrics)
        .filter(VendorMetrics.search_run_id == run_id)
        .all()
    )
    criteria_data = []
    for vm in vendor_metrics:
        criteria_data.append(
            CriteriaDataItem(
                name=vm.vendor.name if hasattr(vm, "vendor") and vm.vendor else "Unknown",
                must_have_matched=vm.must_have_matched,
                must_have_total=vm.must_have_total,
                nice_to_have_matched=vm.nice_to_have_matched,
                nice_to_have_total=vm.nice_to_have_total,
                quality_score=vm.quality_score,
                completeness_pct=vm.completeness_pct,
                confidence_pct=vm.confidence_pct,
            )
        )

    # Score breakdown (avg fit, trust, quality, overall)
    metrics = vendor_metrics
    score_breakdown = ScoreBreakdown(
        avg_fit=round(sum(m.fit_score or 0 for m in metrics) / max(len(metrics), 1), 1),
        avg_trust=round(sum(m.trust_score or 0 for m in metrics) / max(len(metrics), 1), 1),
        avg_quality=round(sum(m.quality_score or 0 for m in metrics) / max(len(metrics), 1), 1),
        avg_overall=round(sum(m.overall_score or 0 for m in metrics) / max(len(metrics), 1), 1),
    ) if metrics else None

    return AnalyticsResponse(
        run_summary=run_summary,
        totals=totals,
        distributions=distributions,
        top_vendors=top_vendors,
        pricing_data=pricing_data,
        criteria_matching=criteria_data,
        score_breakdown=score_breakdown,
    )
