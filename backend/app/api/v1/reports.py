"""Reports API endpoints for generating and managing reports."""

import json
from datetime import datetime
from html import escape

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func

from app.api.deps import CurrentUser, DbSession
from app.api.v1.analytics import get_run_with_rbac
from app.models import (
    ProcurementRequest,
    Report,
    SearchRun,
    Vendor,
    VendorMetrics,
    VendorSource,
)
from app.schemas.analytics import (
    ReportDetailResponse,
    ReportListResponse,
    ReportResponse,
)

router = APIRouter(tags=["reports"])


def _parse_json_field(value, default=None):
    """Safely parse JSON field that might be string or already parsed."""
    if value is None:
        return default if default is not None else []
    if isinstance(value, (list, dict)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return default if default is not None else []
    return default if default is not None else []


def _format_currency(value, currency="Rp"):
    """Format number as currency."""
    if value is None or value == 0:
        return None
    try:
        return f"{currency} {value:,.0f}".replace(",", ".")
    except (ValueError, TypeError):
        return None


def generate_html_report(
    db: DbSession,
    run: SearchRun,
    request: ProcurementRequest,
) -> str:
    """Generate a beautiful HTML report for vendor discovery results."""

    # Get vendor stats
    vendor_ids_subq = (
        db.query(VendorSource.vendor_id)
        .filter(VendorSource.search_run_id == run.id)
        .distinct()
        .subquery()
    )

    vendors_count = (
        db.query(func.count(Vendor.id))
        .filter(Vendor.id.in_(db.query(vendor_ids_subq)))
        .scalar()
        or 0
    )

    sources_count = (
        db.query(func.count(VendorSource.id))
        .filter(VendorSource.search_run_id == run.id)
        .scalar()
        or 0
    )

    # Average scores
    avg_scores = (
        db.query(
            func.avg(VendorMetrics.fit_score).label("avg_fit"),
            func.avg(VendorMetrics.trust_score).label("avg_trust"),
            func.avg(VendorMetrics.overall_score).label("avg_overall"),
            func.avg(VendorMetrics.quality_score).label("avg_quality"),
        )
        .filter(VendorMetrics.search_run_id == run.id)
        .first()
    )

    avg_fit = f"{avg_scores.avg_fit:.0f}" if avg_scores.avg_fit else "-"
    avg_trust = f"{avg_scores.avg_trust:.0f}" if avg_scores.avg_trust else "-"
    avg_overall = f"{avg_scores.avg_overall:.0f}" if avg_scores.avg_overall else "-"

    # Top vendors
    top_vendors = (
        db.query(Vendor, VendorMetrics)
        .join(VendorMetrics, Vendor.id == VendorMetrics.vendor_id)
        .filter(VendorMetrics.search_run_id == run.id)
        .filter(VendorMetrics.overall_score.isnot(None))
        .order_by(VendorMetrics.overall_score.desc())
        .limit(15)
        .all()
    )

    # Build vendor cards HTML
    vendor_cards_html = ""
    for i, (vendor, metrics) in enumerate(top_vendors, 1):
        overall = f"{metrics.overall_score:.0f}" if metrics.overall_score else "-"
        fit = f"{metrics.fit_score:.0f}" if metrics.fit_score else "-"
        trust = f"{metrics.trust_score:.0f}" if metrics.trust_score else "-"

        # Pricing
        pricing_html = ""
        if vendor.pricing_details:
            pricing_text = vendor.pricing_details[:150]
            if len(vendor.pricing_details) > 150:
                pricing_text += "..."
            pricing_html = f'<div class="vendor-pricing">💰 {escape(pricing_text)}</div>'

        # Price range
        price_range = ""
        if vendor.price_range_min or vendor.price_range_max:
            min_p = _format_currency(vendor.price_range_min) or "-"
            max_p = _format_currency(vendor.price_range_max) or "-"
            price_range = f'<span class="price-badge">{min_p} - {max_p}</span>'

        # Description
        desc = ""
        if vendor.description:
            desc_text = vendor.description[:200]
            if len(vendor.description) > 200:
                desc_text += "..."
            desc = f'<p class="vendor-desc">{escape(desc_text)}</p>'

        # Contact
        contact_parts = []
        if vendor.email:
            contact_parts.append(f"📧 {escape(vendor.email)}")
        if vendor.phone:
            contact_parts.append(f"📞 {escape(vendor.phone)}")
        contact_html = f'<div class="vendor-contact">{" &nbsp;|&nbsp; ".join(contact_parts)}</div>' if contact_parts else ""

        # Website
        website_html = ""
        if vendor.website:
            website_html = f'<a href="{escape(vendor.website)}" target="_blank" class="vendor-website">🔗 {escape(vendor.website)}</a>'

        vendor_cards_html += f"""
        <div class="vendor-card">
            <div class="vendor-rank">#{i}</div>
            <div class="vendor-main">
                <div class="vendor-header">
                    <h3 class="vendor-name">{escape(vendor.name)}</h3>
                    <div class="vendor-scores">
                        <span class="score score-overall" title="Overall Score">{overall}</span>
                        <span class="score score-fit" title="Fit Score">{fit}</span>
                        <span class="score score-trust" title="Trust Score">{trust}</span>
                    </div>
                </div>
                <div class="vendor-meta">
                    {f'<span class="meta-location">📍 {escape(vendor.location)}</span>' if vendor.location else ''}
                    {f'<span class="meta-industry">🏢 {escape(vendor.industry)}</span>' if vendor.industry else ''}
                    {price_range}
                </div>
                {desc}
                {pricing_html}
                {contact_html}
                {website_html}
            </div>
        </div>
        """

    # Duration
    duration = "-"
    if run.started_at and run.completed_at:
        duration_sec = int((run.completed_at - run.started_at).total_seconds())
        if duration_sec >= 60:
            duration = f"{duration_sec // 60}m {duration_sec % 60}s"
        else:
            duration = f"{duration_sec}s"

    # Keywords - properly parse JSON
    keywords_list = _parse_json_field(request.keywords, [])
    keywords_html = ""
    if keywords_list:
        keywords_html = " ".join(f'<span class="keyword-tag">{escape(str(k))}</span>' for k in keywords_list)
    else:
        keywords_html = '<span class="text-muted">No keywords specified</span>'

    # Budget
    budget_html = "Not specified"
    if request.budget_min or request.budget_max:
        min_b = _format_currency(request.budget_min) or "-"
        max_b = _format_currency(request.budget_max) or "-"
        budget_html = f"{min_b} — {max_b}"

    # Criteria - properly parse JSON
    must_have_list = _parse_json_field(request.must_have_criteria, [])
    nice_to_have_list = _parse_json_field(request.nice_to_have_criteria, [])

    must_have_html = ""
    if must_have_list:
        for item in must_have_list:
            must_have_html += f'<li>✓ {escape(str(item))}</li>'
    else:
        must_have_html = '<li class="text-muted">None specified</li>'

    nice_to_have_html = ""
    if nice_to_have_list:
        for item in nice_to_have_list:
            nice_to_have_html += f'<li>○ {escape(str(item))}</li>'
    else:
        nice_to_have_html = '<li class="text-muted">None specified</li>'

    generated_at = datetime.now().strftime("%d %B %Y, %H:%M")

    # Generate complete HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(request.title)} - Vendor Report</title>
    <style>
        :root {{
            --primary: #dc143c;
            --primary-light: #fee2e2;
            --primary-dark: #991b1b;
            --success: #059669;
            --warning: #d97706;
            --info: #0284c7;
            --gray-50: #f9fafb;
            --gray-100: #f3f4f6;
            --gray-200: #e5e7eb;
            --gray-300: #d1d5db;
            --gray-500: #6b7280;
            --gray-700: #374151;
            --gray-900: #111827;
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #fef2f2 0%, #fff 50%, #fef2f2 100%);
            color: var(--gray-900);
            line-height: 1.6;
            min-height: 100vh;
        }}

        .report-container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            box-shadow: 0 0 60px rgba(220, 20, 60, 0.1);
        }}

        /* Header */
        .report-header {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            padding: 48px 40px;
            position: relative;
            overflow: hidden;
        }}

        .report-header::before {{
            content: '';
            position: absolute;
            top: -50%;
            right: -20%;
            width: 60%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        }}

        .report-header h1 {{
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 8px;
            position: relative;
        }}

        .report-header .subtitle {{
            opacity: 0.9;
            font-size: 15px;
            position: relative;
        }}

        .header-meta {{
            display: flex;
            gap: 24px;
            margin-top: 24px;
            flex-wrap: wrap;
            position: relative;
        }}

        .header-meta span {{
            font-size: 13px;
            opacity: 0.85;
        }}

        /* Content */
        .report-content {{
            padding: 40px;
        }}

        .section {{
            margin-bottom: 40px;
        }}

        .section-title {{
            font-size: 20px;
            font-weight: 600;
            color: var(--primary);
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 2px solid var(--primary-light);
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        /* KPI Grid */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
        }}

        .kpi-card {{
            background: var(--gray-50);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            border: 1px solid var(--gray-200);
        }}

        .kpi-value {{
            font-size: 36px;
            font-weight: 700;
            color: var(--primary);
            line-height: 1.2;
        }}

        .kpi-label {{
            font-size: 12px;
            color: var(--gray-500);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-top: 4px;
        }}

        /* Details Grid */
        .details-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
        }}

        .detail-item {{
            background: var(--gray-50);
            padding: 16px 20px;
            border-radius: 10px;
        }}

        .detail-label {{
            font-size: 12px;
            color: var(--gray-500);
            text-transform: uppercase;
            letter-spacing: 0.3px;
            margin-bottom: 6px;
        }}

        .detail-value {{
            font-weight: 500;
            color: var(--gray-700);
        }}

        .keyword-tag {{
            display: inline-block;
            background: var(--primary-light);
            color: var(--primary);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 13px;
            margin: 2px;
        }}

        /* Criteria */
        .criteria-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 24px;
        }}

        .criteria-box h4 {{
            font-size: 14px;
            font-weight: 600;
            color: var(--gray-700);
            margin-bottom: 12px;
        }}

        .criteria-box ul {{
            list-style: none;
        }}

        .criteria-box li {{
            padding: 8px 0;
            border-bottom: 1px solid var(--gray-100);
            font-size: 14px;
        }}

        .criteria-box li:last-child {{
            border-bottom: none;
        }}

        .text-muted {{
            color: var(--gray-500);
            font-style: italic;
        }}

        /* Vendor Cards */
        .vendors-list {{
            display: flex;
            flex-direction: column;
            gap: 16px;
        }}

        .vendor-card {{
            display: flex;
            border: 1px solid var(--gray-200);
            border-radius: 12px;
            overflow: hidden;
            transition: all 0.2s;
        }}

        .vendor-card:hover {{
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            border-color: var(--primary-light);
        }}

        .vendor-rank {{
            background: var(--primary);
            color: white;
            padding: 20px 16px;
            font-weight: 700;
            font-size: 16px;
            display: flex;
            align-items: flex-start;
            justify-content: center;
            min-width: 60px;
        }}

        .vendor-main {{
            flex: 1;
            padding: 16px 20px;
        }}

        .vendor-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 8px;
        }}

        .vendor-name {{
            font-size: 18px;
            font-weight: 600;
            color: var(--gray-900);
        }}

        .vendor-scores {{
            display: flex;
            gap: 6px;
        }}

        .score {{
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
        }}

        .score-overall {{
            background: #dcfce7;
            color: #166534;
        }}

        .score-fit {{
            background: #dbeafe;
            color: #1e40af;
        }}

        .score-trust {{
            background: #fef3c7;
            color: #92400e;
        }}

        .vendor-meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-bottom: 10px;
            font-size: 13px;
            color: var(--gray-500);
        }}

        .price-badge {{
            background: #fef3c7;
            color: #92400e;
            padding: 2px 10px;
            border-radius: 12px;
            font-weight: 500;
        }}

        .vendor-desc {{
            font-size: 14px;
            color: var(--gray-600);
            margin-bottom: 8px;
            line-height: 1.5;
        }}

        .vendor-pricing {{
            font-size: 13px;
            color: var(--success);
            margin-bottom: 6px;
        }}

        .vendor-contact {{
            font-size: 13px;
            color: var(--gray-500);
            margin-bottom: 6px;
        }}

        .vendor-website {{
            font-size: 13px;
            color: var(--primary);
            text-decoration: none;
        }}

        .vendor-website:hover {{
            text-decoration: underline;
        }}

        /* Footer */
        .report-footer {{
            text-align: center;
            padding: 24px 40px;
            background: var(--gray-50);
            border-top: 1px solid var(--gray-200);
            color: var(--gray-500);
            font-size: 13px;
        }}

        .report-footer strong {{
            color: var(--primary);
        }}

        /* Print styles */
        @media print {{
            body {{ background: white; }}
            .report-container {{ box-shadow: none; }}
            .vendor-card {{ break-inside: avoid; }}
        }}

        @media (max-width: 768px) {{
            .kpi-grid {{ grid-template-columns: repeat(2, 1fr); }}
            .details-grid {{ grid-template-columns: 1fr; }}
            .criteria-grid {{ grid-template-columns: 1fr; }}
            .vendor-header {{ flex-direction: column; gap: 8px; }}
        }}
    </style>
</head>
<body>
    <div class="report-container">
        <div class="report-header">
            <h1>{escape(request.title)}</h1>
            <p class="subtitle">Vendor Discovery Report</p>
            <div class="header-meta">
                <span>📅 {generated_at}</span>
                <span>🏷️ {escape(request.category or 'General')}</span>
                <span>📍 {escape(request.location or 'Indonesia')}</span>
            </div>
        </div>

        <div class="report-content">
            <!-- Summary Section -->
            <div class="section">
                <h2 class="section-title">📊 Search Results Summary</h2>
                <div class="kpi-grid">
                    <div class="kpi-card">
                        <div class="kpi-value">{vendors_count}</div>
                        <div class="kpi-label">Vendors Found</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-value">{sources_count}</div>
                        <div class="kpi-label">Sources Scanned</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-value">{avg_overall}</div>
                        <div class="kpi-label">Avg. Score</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-value">{duration}</div>
                        <div class="kpi-label">Search Time</div>
                    </div>
                </div>
            </div>

            <!-- Request Details -->
            <div class="section">
                <h2 class="section-title">📋 Request Details</h2>
                <div class="details-grid">
                    <div class="detail-item">
                        <div class="detail-label">Search Keywords</div>
                        <div class="detail-value">{keywords_html}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Budget Range</div>
                        <div class="detail-value">{budget_html}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Timeline</div>
                        <div class="detail-value">{escape(request.timeline or 'Not specified')}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Score Breakdown</div>
                        <div class="detail-value">Fit: {avg_fit} &nbsp;|&nbsp; Trust: {avg_trust}</div>
                    </div>
                </div>
            </div>

            <!-- Evaluation Criteria -->
            <div class="section">
                <h2 class="section-title">✅ Evaluation Criteria</h2>
                <div class="criteria-grid">
                    <div class="criteria-box">
                        <h4>Must-Have Requirements</h4>
                        <ul>{must_have_html}</ul>
                    </div>
                    <div class="criteria-box">
                        <h4>Nice-to-Have Features</h4>
                        <ul>{nice_to_have_html}</ul>
                    </div>
                </div>
            </div>

            <!-- Vendors List -->
            <div class="section">
                <h2 class="section-title">🏆 Top {len(top_vendors)} Vendors</h2>
                <div class="vendors-list">
                    {vendor_cards_html if vendor_cards_html else '<p class="text-muted" style="text-align:center;padding:40px;">No vendors found for this search.</p>'}
                </div>
            </div>
        </div>

        <div class="report-footer">
            <strong>Procurely</strong> — AI-Powered Vendor Discovery Platform<br>
            Report generated on {generated_at}
        </div>
    </div>
</body>
</html>"""

    return html


@router.post("/runs/{run_id}/export", response_model=ReportResponse)
def export_run_report(
    run_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> ReportResponse:
    """Generate and store an HTML report for a run."""
    run = get_run_with_rbac(run_id, db, current_user.id)

    # Get the procurement request
    request = (
        db.query(ProcurementRequest)
        .filter(ProcurementRequest.id == run.request_id)
        .first()
    )
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found",
        )

    # Generate HTML content
    html_content = generate_html_report(db, run, request)

    # Create report record
    report = Report(
        run_id=run_id,
        created_by_user_id=current_user.id,
        format="HTML",
        status="COMPLETED",
        html_content=html_content,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return ReportResponse(
        id=report.id,
        run_id=report.run_id,
        format=report.format,
        status=report.status,
        created_at=report.created_at,
    )


@router.get("/reports", response_model=ReportListResponse)
def list_reports(
    db: DbSession,
    current_user: CurrentUser,
) -> ReportListResponse:
    """List reports created by the current user."""
    reports = (
        db.query(Report)
        .filter(Report.created_by_user_id == current_user.id)
        .order_by(Report.created_at.desc())
        .all()
    )

    return ReportListResponse(
        reports=[
            ReportResponse(
                id=r.id,
                run_id=r.run_id,
                format=r.format,
                status=r.status,
                created_at=r.created_at,
            )
            for r in reports
        ],
        total=len(reports),
    )


@router.get("/reports/{report_id}", response_model=ReportDetailResponse)
def get_report(
    report_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> ReportDetailResponse:
    """Get report details including HTML content."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    # RBAC: only owner can access
    if report.created_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return ReportDetailResponse(
        id=report.id,
        run_id=report.run_id,
        format=report.format,
        status=report.status,
        created_at=report.created_at,
        html_content=report.html_content,
    )


@router.delete("/reports/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_report(
    report_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> None:
    """Delete a report. Only the owner can delete."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    # RBAC: only owner can delete
    if report.created_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    db.delete(report)
    db.commit()
