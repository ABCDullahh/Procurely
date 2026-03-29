"""
Demo seed script for local development.
Seeds database with sample data for testing.

Usage:
    cd backend
    python -m app.scripts.seed_demo
"""

import json
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.core.security import get_password_hash
from app.models import (
    ProcurementRequest,
    Report,
    SearchRun,
    Shortlist,
    ShortlistItem,
    User,
    Vendor,
    VendorFieldEvidence,
    VendorMetrics,
    VendorSource,
)


def seed_demo(db: Session) -> None:
    """Seed demo data. Idempotent - checks for existing data."""
    print("🌱 Starting demo seed...")

    # Check if demo user exists
    demo_user = db.query(User).filter(User.email == "demo@procurely.ai").first()
    if demo_user:
        print("✅ Demo data already exists. Skipping seed.")
        return

    # === Users ===
    print("  Creating users...")
    admin_user = User(
        email=settings.default_admin_email,
        password_hash=get_password_hash(settings.default_admin_password),
        full_name="Admin User",
        role="admin",
        is_active=True,
    )
    demo_user = User(
        email="demo@procurely.ai",
        password_hash=get_password_hash(settings.default_admin_password),
        full_name="Demo User",
        role="member",
        is_active=True,
    )
    db.add_all([admin_user, demo_user])
    db.commit()
    db.refresh(demo_user)

    # === Procurement Request ===
    print("  Creating procurement request...")
    request = ProcurementRequest(
        title="Enterprise CRM Solution",
        description="Looking for a modern CRM platform to manage customer relationships, sales pipeline, and marketing automation for a team of 50+ users.",
        category="Software",
        location="United States",
        budget_min=5000,
        budget_max=50000,
        timeline="Q1 2025",
        keywords=json.dumps(["CRM", "sales automation", "customer management", "pipeline"]),
        must_have_criteria=json.dumps([
            "Email integration",
            "Sales pipeline management",
            "Contact management",
            "Reporting & analytics",
        ]),
        nice_to_have_criteria=json.dumps([
            "AI-powered insights",
            "Mobile app",
            "API access",
            "Custom workflows",
        ]),
        status="RUNNING",
        created_by_user_id=demo_user.id,
    )
    db.add(request)
    db.commit()
    db.refresh(request)

    # === Search Run ===
    print("  Creating search run...")
    run = SearchRun(
        request_id=request.id,
        status="COMPLETED",
        current_step="DONE",
        progress_pct=100,
        vendors_found=5,
        sources_searched=15,
        started_at=datetime.utcnow() - timedelta(minutes=5),
        completed_at=datetime.utcnow(),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    # === Vendors ===
    print("  Creating vendors...")
    vendors_data = [
        {
            "name": "Salesforce",
            "website": "https://salesforce.com",
            "description": "World's #1 CRM platform with comprehensive sales, service, and marketing solutions.",
            "location": "San Francisco, CA",
            "country": "United States",
            "industry": "Enterprise Software",
            "email": "sales@salesforce.com",
            "phone": "+1-800-667-6389",
            "employee_count": 70000,
            "founded_year": 1999,
            "score": 92,
            "fit": 90,
            "trust": 94,
        },
        {
            "name": "HubSpot",
            "website": "https://hubspot.com",
            "description": "All-in-one CRM platform for marketing, sales, and customer service.",
            "location": "Cambridge, MA",
            "country": "United States",
            "industry": "Marketing Tech",
            "email": "sales@hubspot.com",
            "phone": "+1-888-482-7768",
            "employee_count": 7000,
            "founded_year": 2006,
            "score": 88,
            "fit": 86,
            "trust": 90,
        },
        {
            "name": "Pipedrive",
            "website": "https://pipedrive.com",
            "description": "Sales-focused CRM designed to help small sales teams manage pipelines.",
            "location": "Tallinn",
            "country": "Estonia",
            "industry": "SaaS",
            "email": "sales@pipedrive.com",
            "phone": "+1-646-583-0002",
            "employee_count": 1000,
            "founded_year": 2010,
            "score": 84,
            "fit": 82,
            "trust": 86,
        },
        {
            "name": "Zoho CRM",
            "website": "https://zoho.com/crm",
            "description": "Feature-rich CRM with strong automation and customization options.",
            "location": "Chennai",
            "country": "India",
            "industry": "Enterprise Software",
            "email": "sales@zoho.com",
            "phone": "+1-877-834-4428",
            "employee_count": 12000,
            "founded_year": 1996,
            "score": 80,
            "fit": 78,
            "trust": 82,
        },
        {
            "name": "Freshsales",
            "website": "https://freshworks.com/crm",
            "description": "AI-powered CRM for high-velocity sales teams with built-in phone and email.",
            "location": "San Mateo, CA",
            "country": "United States",
            "industry": "SaaS",
            "email": "sales@freshworks.com",
            "phone": "+1-866-832-3090",
            "employee_count": 5000,
            "founded_year": 2010,
            "score": 76,
            "fit": 74,
            "trust": 78,
        },
    ]

    created_vendors = []
    for vdata in vendors_data:
        vendor = Vendor(
            name=vdata["name"],
            website=vdata["website"],
            description=vdata["description"],
            location=vdata["location"],
            country=vdata["country"],
            industry=vdata["industry"],
            email=vdata["email"],
            phone=vdata["phone"],
            employee_count=vdata["employee_count"],
            founded_year=vdata["founded_year"],
        )
        db.add(vendor)
        db.commit()
        db.refresh(vendor)
        created_vendors.append((vendor, vdata))

        # Add source
        source = VendorSource(
            vendor_id=vendor.id,
            search_run_id=run.id,
            source_url=vdata["website"],
            source_type="WEB",
            crawled_at=datetime.utcnow(),
        )
        db.add(source)

        # Add metrics
        metrics = VendorMetrics(
            vendor_id=vendor.id,
            search_run_id=run.id,
            overall_score=float(vdata["score"]),
            fit_score=float(vdata["fit"]),
            trust_score=float(vdata["trust"]),
            relevance_score=float(vdata["score"] - 5),
            criteria_met=json.dumps(["Email integration", "Sales pipeline"]),
            criteria_missing=json.dumps([]),
        )
        db.add(metrics)

        # Add evidence
        evidence = VendorFieldEvidence(
            vendor_id=vendor.id,
            field_name="pricing",
            raw_excerpt=f"{vdata['name']} offers enterprise pricing starting at $25/user/month with volume discounts available.",
            extracted_value="$25/user/month",
            confidence_score=0.85,
        )
        db.add(evidence)

    db.commit()

    # === Report ===
    print("  Creating report...")
    report_html = f"""
    <html>
    <head><title>Vendor Analysis Report</title></head>
    <body>
        <h1>Vendor Analysis: Enterprise CRM Solution</h1>
        <p>Generated: {datetime.utcnow().isoformat()}</p>
        <h2>Top Vendors</h2>
        <ol>
            <li>Salesforce (Score: 92)</li>
            <li>HubSpot (Score: 88)</li>
            <li>Pipedrive (Score: 84)</li>
        </ol>
    </body>
    </html>
    """
    report = Report(
        search_run_id=run.id,
        title="Enterprise CRM Vendor Analysis",
        html_content=report_html,
        generated_by_user_id=demo_user.id,
    )
    db.add(report)
    db.commit()

    # === Shortlist ===
    print("  Creating shortlist...")
    shortlist = Shortlist(
        name="Top CRM Candidates",
        description="Our top 3 picks for CRM evaluation",
        created_by_user_id=demo_user.id,
    )
    db.add(shortlist)
    db.commit()
    db.refresh(shortlist)

    # Add top 3 vendors to shortlist
    for i, (vendor, _) in enumerate(created_vendors[:3]):
        item = ShortlistItem(
            shortlist_id=shortlist.id,
            vendor_id=vendor.id,
            position=i,
            notes=f"Ranked #{i+1} by AI scoring",
        )
        db.add(item)
    db.commit()

    print("✅ Demo seed complete!")
    print(f"   Demo login: demo@procurely.ai / (see .env)")
    print(f"   Admin login: {settings.default_admin_email} / (see .env)")


def main():
    """Main entry point."""
    # Create tables if needed
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        seed_demo(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
