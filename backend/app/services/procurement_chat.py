"""Procurement Chat service for conversational AI-powered vendor search."""

import json
import logging
import uuid
from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import (
    SearchRun,
    Vendor,
    VendorAsset,
    VendorMetrics,
    VendorSource,
)
from app.schemas.procurement_chat import (
    CategoryData,
    ChatAction,
    ComparisonData,
    ComparisonRow,
    ConversationContext,
    EvidenceItem,
    FilterChip,
    InsightData,
    PricingData,
    ProcurementChatRequest,
    ProcurementChatResponse,
    SearchProgressData,
    SearchProgressStep,
    StatData,
    SuggestedQuery,
    VendorCardData,
)
from app.services.llm import GeminiProvider, LLMProvider, OpenAIProvider
from app.services.chat_deep_research import (
    should_trigger_deep_research,
    start_chat_research,
    get_research_status,
)

logger = logging.getLogger(__name__)


class ProcurementChatError(Exception):
    """Base procurement chat error."""
    pass


class ConfigMissingError(ProcurementChatError):
    """API key or config missing."""
    pass


# ============ Helper Functions ============

def get_vendor_card_data(
    db: Session, vendor: Vendor, run_id: int | None = None
) -> VendorCardData:
    """Build VendorCardData from vendor model."""
    # Get metrics
    metrics = None
    if run_id:
        metrics = (
            db.query(VendorMetrics)
            .filter(
                VendorMetrics.vendor_id == vendor.id,
                VendorMetrics.search_run_id == run_id,
            )
            .first()
        )
    if not metrics:
        metrics = (
            db.query(VendorMetrics)
            .filter(VendorMetrics.vendor_id == vendor.id)
            .order_by(VendorMetrics.id.desc())
            .first()
        )

    # Get logo
    logo = (
        db.query(VendorAsset)
        .filter(VendorAsset.vendor_id == vendor.id, VendorAsset.asset_type == "LOGO")
        .order_by(VendorAsset.priority)
        .first()
    )

    return VendorCardData(
        id=vendor.id,
        name=vendor.name,
        website=vendor.website,
        logo_url=logo.asset_url if logo else None,
        industry=vendor.industry,
        location=vendor.location,
        country=vendor.country,
        description=vendor.description[:200] if vendor.description else None,
        overall_score=metrics.overall_score if metrics else None,
        fit_score=metrics.fit_score if metrics else None,
        trust_score=metrics.trust_score if metrics else None,
        pricing_model=vendor.pricing_model,
        pricing_details=vendor.pricing_details,
        employee_count=vendor.employee_count,
        founded_year=vendor.founded_year,
        criteria_matched=[],
        criteria_partial=[],
        criteria_missing=[],
    )


def search_vendors_by_keywords(
    db: Session,
    keywords: list[str],
    location: str | None = None,
    limit: int = 10,
) -> list[VendorCardData]:
    """Search vendors in database by keywords."""
    query = db.query(Vendor)

    # Build search conditions
    conditions = []
    for keyword in keywords:
        keyword_pattern = f"%{keyword}%"
        conditions.append(
            or_(
                Vendor.name.ilike(keyword_pattern),
                Vendor.industry.ilike(keyword_pattern),
                Vendor.description.ilike(keyword_pattern),
            )
        )

    if conditions:
        query = query.filter(or_(*conditions))

    # Filter by location if provided
    if location:
        location_pattern = f"%{location}%"
        query = query.filter(
            or_(
                Vendor.location.ilike(location_pattern),
                Vendor.country.ilike(location_pattern),
            )
        )

    # Get vendors with metrics
    vendors = query.limit(limit).all()

    result = []
    for vendor in vendors:
        card = get_vendor_card_data(db, vendor)
        result.append(card)

    # Sort by overall_score if available
    result.sort(key=lambda v: v.overall_score or 0, reverse=True)

    return result


def get_top_vendors(
    db: Session,
    run_id: int,
    limit: int = 5,
    filters: dict | None = None,
) -> list[VendorCardData]:
    """Get top vendors from a run with optional filters."""
    query = (
        db.query(Vendor, VendorMetrics)
        .join(VendorSource, Vendor.id == VendorSource.vendor_id)
        .join(VendorMetrics, Vendor.id == VendorMetrics.vendor_id)
        .filter(VendorSource.search_run_id == run_id)
        .filter(VendorMetrics.search_run_id == run_id)
    )

    if filters:
        if filters.get("location"):
            query = query.filter(
                Vendor.location.ilike(f"%{filters['location']}%")
                | Vendor.country.ilike(f"%{filters['location']}%")
            )
        if filters.get("industry"):
            query = query.filter(Vendor.industry.ilike(f"%{filters['industry']}%"))
        if filters.get("min_score"):
            query = query.filter(VendorMetrics.overall_score >= filters["min_score"])

    results = (
        query.order_by(VendorMetrics.overall_score.desc()).limit(limit).all()
    )

    vendors = []
    for vendor, metrics in results:
        card = get_vendor_card_data(db, vendor, run_id)
        vendors.append(card)

    return vendors


def build_comparison_data(
    db: Session, vendor_ids: list[int], run_id: int | None = None
) -> ComparisonData:
    """Build comparison table data for vendors."""
    vendors = []
    for vid in vendor_ids:
        vendor = db.query(Vendor).filter(Vendor.id == vid).first()
        if vendor:
            vendors.append(get_vendor_card_data(db, vendor, run_id))

    metrics = [
        ("Overall Score", "overall_score"),
        ("Fit Score", "fit_score"),
        ("Trust Score", "trust_score"),
        ("Pricing Model", "pricing_model"),
        ("Location", "location"),
        ("Industry", "industry"),
        ("Employees", "employee_count"),
    ]

    rows = []
    for label, field in metrics:
        values = {}
        best_val = None
        best_id = None

        for v in vendors:
            val = getattr(v, field, None)
            values[str(v.id)] = val

            if field.endswith("_score") and val is not None:
                if best_val is None or val > best_val:
                    best_val = val
                    best_id = v.id

        rows.append(
            ComparisonRow(
                metric=label,
                values=values,
                best_vendor_id=best_id,
            )
        )

    return ComparisonData(vendors=vendors, rows=rows)


def get_run_progress(db: Session, run_id: int) -> SearchProgressData:
    """Get current progress of a search run."""
    run = db.query(SearchRun).filter(SearchRun.id == run_id).first()
    if not run:
        return SearchProgressData(
            steps=[],
            current_step="unknown",
            progress_pct=0,
        )

    step_order = [
        ("expand", "Expanding queries", 10),
        ("search", "Searching web", 25),
        ("fetch", "Fetching pages", 40),
        ("extract", "Extracting vendors", 60),
        ("dedup", "Removing duplicates", 70),
        ("score", "Scoring vendors", 80),
        ("logo", "Fetching logos", 90),
        ("save", "Saving results", 95),
        ("done", "Completed", 100),
    ]

    steps = []
    current = run.current_step or ""
    progress = run.progress_pct or 0

    for step_id, label, threshold in step_order:
        if progress >= threshold:
            status = "completed"
        elif step_id == current or progress >= threshold - 10:
            status = "active"
        else:
            status = "pending"

        if run.status == "FAILED" and step_id == current:
            status = "failed"

        steps.append(
            SearchProgressStep(
                id=step_id,
                label=label,
                status=status,
                details=None,
            )
        )

    return SearchProgressData(
        steps=steps,
        current_step=current,
        progress_pct=progress,
        vendors_found=run.vendors_found or 0,
        sources_searched=run.sources_searched or 0,
        estimated_time_remaining=None,
    )


# ============ Card Data Generators ============

def generate_insights(
    db: Session, run_id: int | None, vendors: list[VendorCardData] | None
) -> list[InsightData]:
    """Generate key insights for procurement decisions."""
    insights = []
    if not vendors:
        return insights

    top_vendor = max(vendors, key=lambda v: v.overall_score or 0, default=None)
    if top_vendor and top_vendor.overall_score:
        if top_vendor.overall_score >= 70:
            insights.append(
                InsightData(
                    type="recommendation",
                    title="Rekomendasi Teratas",
                    description=f"{top_vendor.name} mendapat skor tertinggi ({top_vendor.overall_score:.0f}%).",
                    action=f"Lihat detail {top_vendor.name}",
                )
            )

    pricing_models = set(v.pricing_model for v in vendors if v.pricing_model)
    if len(pricing_models) > 1:
        insights.append(
            InsightData(
                type="highlight",
                title="Variasi Pricing",
                description=f"Tersedia {len(pricing_models)} model pricing berbeda.",
                action="Bandingkan pricing",
            )
        )

    countries = set(v.country for v in vendors if v.country)
    if len(countries) > 1:
        insights.append(
            InsightData(
                type="trend",
                title="Opsi Lokasi",
                description=f"Vendor tersedia dari {len(countries)} negara.",
            )
        )

    return insights[:3]


def generate_quick_stats(
    db: Session, run_id: int | None, vendors: list[VendorCardData] | None
) -> list[StatData]:
    """Generate quick statistics for display."""
    stats = []

    if vendors:
        stats.append(
            StatData(
                label="Vendor Ditemukan",
                value=len(vendors),
                icon="building",
            )
        )

        scores = [v.overall_score for v in vendors if v.overall_score]
        if scores:
            avg_score = sum(scores) / len(scores)
            stats.append(
                StatData(
                    label="Rata-rata Skor",
                    value=f"{avg_score:.0f}%",
                    icon="chart",
                )
            )

            top_score = max(scores)
            stats.append(
                StatData(
                    label="Skor Tertinggi",
                    value=f"{top_score:.0f}%",
                    change_type="positive" if top_score >= 70 else "neutral",
                    icon="trophy",
                )
            )

        industries = set(v.industry for v in vendors if v.industry)
        stats.append(
            StatData(
                label="Industri",
                value=len(industries),
                icon="layers",
            )
        )

    return stats[:4]


def generate_category_breakdown(
    db: Session, run_id: int | None, vendors: list[VendorCardData] | None
) -> list[CategoryData]:
    """Generate category/industry breakdown."""
    if not vendors:
        return []

    industry_counts: dict[str, int] = {}
    for v in vendors:
        industry = v.industry or "Lainnya"
        industry_counts[industry] = industry_counts.get(industry, 0) + 1

    total = len(vendors)
    categories = []
    colors = ["#dc143c", "#4f46e5", "#059669", "#d97706", "#7c3aed", "#0891b2"]

    for i, (name, count) in enumerate(
        sorted(industry_counts.items(), key=lambda x: -x[1])
    ):
        categories.append(
            CategoryData(
                name=name,
                count=count,
                percentage=round((count / total) * 100, 1),
                color=colors[i % len(colors)],
            )
        )

    return categories[:6]


def generate_pricing_overview(
    db: Session, vendors: list[VendorCardData] | None
) -> list[PricingData]:
    """Generate pricing overview for vendors."""
    if not vendors:
        return []

    pricing_data = []
    for v in vendors:
        if v.pricing_model:
            pricing_data.append(
                PricingData(
                    vendor_name=v.name,
                    vendor_id=v.id,
                    pricing_model=v.pricing_model,
                    pricing_details=v.pricing_details,
                    has_free_tier="free" in (v.pricing_model or "").lower()
                    or "gratis" in (v.pricing_details or "").lower(),
                    starting_price=None,
                )
            )

    return pricing_data[:5]


def generate_filter_chips(keywords: list[str], location: str | None) -> list[FilterChip]:
    """Generate filter chips based on search context."""
    chips = []

    if location:
        chips.append(
            FilterChip(
                id="filter-location",
                label=f"Lokasi: {location}",
                icon="map-pin",
                filter_type="location",
                filter_value=location,
            )
        )

    chips.append(
        FilterChip(
            id="filter-indonesia",
            label="Indonesia",
            icon="flag",
            filter_type="location",
            filter_value="Indonesia",
        )
    )
    chips.append(
        FilterChip(
            id="filter-global",
            label="Global",
            icon="globe",
            filter_type="location",
            filter_value="Global",
        )
    )
    chips.append(
        FilterChip(
            id="filter-soc2",
            label="SOC 2",
            icon="shield",
            filter_type="compliance",
            filter_value="SOC 2",
        )
    )

    return chips[:4]


def generate_suggested_queries(
    response_type: str,
    keywords: list[str],
    has_vendors: bool
) -> list[SuggestedQuery]:
    """Generate follow-up query suggestions."""
    suggestions = []

    if response_type == "vendors" and has_vendors:
        suggestions = [
            SuggestedQuery(text="Bandingkan top 3 vendor", type="compare"),
            SuggestedQuery(text="Filter vendor Indonesia saja", type="refine"),
            SuggestedQuery(text="Lihat detail pricing", type="explain"),
            SuggestedQuery(text="Buat shortlist", type="action"),
        ]
    elif response_type == "comparison":
        suggestions = [
            SuggestedQuery(text="Kenapa ini yang terbaik?", type="explain"),
            SuggestedQuery(text="Export ke CSV", type="action"),
        ]
    elif response_type == "gathering_info":
        suggestions = [
            SuggestedQuery(text="Budget sekitar $500-1000/bulan", type="refine"),
            SuggestedQuery(text="Lokasi di Indonesia", type="refine"),
            SuggestedQuery(text="Perlu SOC 2 compliance", type="refine"),
        ]
    else:
        keyword_str = " ".join(keywords) if keywords else "CRM"
        suggestions = [
            SuggestedQuery(text=f"Cari vendor {keyword_str}", type="refine"),
            SuggestedQuery(text="Lihat semua kategori", type="refine"),
        ]

    return suggestions[:4]


# ============ LLM Intent Analysis ============

async def analyze_user_intent(
    provider: LLMProvider,
    message: str,
    context: dict | None,
) -> dict:
    """Use LLM to analyze user intent and extract information."""

    context_str = ""
    if context:
        if context.get("category"):
            context_str += f"- Kategori yang sudah diketahui: {context['category']}\n"
        if context.get("budget"):
            context_str += f"- Budget yang sudah diketahui: {context['budget']}\n"
        if context.get("location"):
            context_str += f"- Lokasi yang sudah diketahui: {context['location']}\n"
        if context.get("requirements"):
            context_str += f"- Requirements: {context['requirements']}\n"

    prompt = f"""Kamu adalah AI procurement assistant. Analisis pesan user berikut dan extract informasi.

Pesan User: "{message}"

Konteks Sebelumnya:
{context_str if context_str else "Belum ada konteks"}

Berikan response dalam format JSON STRICT (tanpa markdown, tanpa code block):
{{
    "intent": "search|compare|question|greeting|other",
    "category": "kategori produk/vendor yang dicari (jika ada)",
    "keywords": ["keyword1", "keyword2"],
    "budget": "budget yang disebutkan (jika ada)",
    "location": "lokasi yang disebutkan (jika ada)",
    "requirements": ["requirement1", "requirement2"],
    "needs_clarification": true/false,
    "clarification_question": "pertanyaan klarifikasi jika perlu"
}}

Contoh:
- "vendor solar" -> intent: search, category: "solar/energy", keywords: ["solar", "panel surya"]
- "carikan supplier panel surya Jakarta budget 500 juta" -> intent: search, category: "solar panel", keywords: ["panel surya", "supplier"], budget: "500 juta", location: "Jakarta"
- "cari meja kantor" -> intent: search, category: "furniture", keywords: ["meja kantor"]
- "bandingkan vendor A dan B" -> intent: compare
- "halo" -> intent: greeting
- "apa itu procurement?" -> intent: question

Penting:
- Jika user menyebut produk/layanan/vendor, SELALU set intent: search
- Jika ada kata "cari", "carikan", "supplier", "vendor", "beli", "butuh" -> intent: search
- Extract category dan keywords dari pesan user
- Jika budget/lokasi sudah disebutkan, extract langsung (jangan set needs_clarification)
- needs_clarification hanya true jika user hanya bilang 1 kata tanpa konteks"""

    try:
        response = await provider.complete_text(prompt)
        response_text = response.content if hasattr(response, "content") else str(response)

        # Clean up response - remove markdown code blocks if present
        response_text = response_text.strip()
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

        return json.loads(response_text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        # Return default intent
        return {
            "intent": "search",
            "category": None,
            "keywords": message.lower().split()[:3],
            "budget": None,
            "location": None,
            "requirements": [],
            "needs_clarification": True,
            "clarification_question": "Bisa ceritakan lebih detail tentang kebutuhan Anda? Misalnya budget dan lokasi yang diinginkan?"
        }
    except Exception as e:
        logger.error(f"LLM error in intent analysis: {e}")
        # Fallback: assume search intent and extract keywords from message
        words = message.lower().split()[:5]
        return {
            "intent": "search",
            "category": None,
            "keywords": words,
            "budget": None,
            "location": None,
            "requirements": [],
            "needs_clarification": False,
            "clarification_question": None
        }


async def generate_vendor_summary(
    provider: LLMProvider,
    vendors: list[VendorCardData],
    category: str | None,
    location: str | None,
) -> str:
    """Generate natural language summary of vendor search results."""

    if not vendors:
        return "Maaf, saya tidak menemukan vendor yang sesuai dengan kriteria Anda. Coba perluas pencarian atau ubah kriteria."

    vendor_info = []
    for i, v in enumerate(vendors[:5], 1):
        info = f"{i}. **{v.name}**"
        if v.industry:
            info += f" ({v.industry})"
        if v.overall_score:
            info += f" - Skor: {v.overall_score:.0f}%"
        if v.location or v.country:
            loc = v.location or v.country
            info += f" - {loc}"
        vendor_info.append(info)

    vendors_str = "\n".join(vendor_info)

    prompt = f"""Buat ringkasan singkat hasil pencarian vendor dalam bahasa Indonesia yang natural dan profesional.

Kategori yang dicari: {category or 'Tidak spesifik'}
Lokasi filter: {location or 'Semua lokasi'}
Jumlah vendor ditemukan: {len(vendors)}

Vendor yang ditemukan:
{vendors_str}

Buat ringkasan 2-3 kalimat yang:
1. Menyebutkan jumlah vendor ditemukan
2. Highlight vendor terbaik
3. Berikan saran singkat untuk langkah selanjutnya

Jangan gunakan format list atau bullet. Tulis dalam paragraf singkat."""

    try:
        response = await provider.complete_text(prompt)
        return response.content if hasattr(response, "content") else str(response)
    except Exception as e:
        logger.error(f"LLM error in summary generation: {e}")
        # Fallback response
        top = vendors[0] if vendors else None
        if top:
            return f"Ditemukan **{len(vendors)} vendor** yang sesuai. Rekomendasi teratas adalah **{top.name}**{f' dengan skor {top.overall_score:.0f}%' if top.overall_score else ''}. Anda bisa membandingkan vendor atau melihat detail lebih lanjut."
        return f"Ditemukan **{len(vendors)} vendor** yang sesuai dengan pencarian Anda."


# ============ Main Processing Function ============

async def process_chat_message(
    db: Session,
    user_id: int,
    payload: ProcurementChatRequest,
) -> ProcurementChatResponse:
    """Process a procurement chat message and generate response."""
    from app.models.app_settings import AppSettings
    from app.services.errors import ConfigMissingError as KeyMissingError
    from app.services.keys import get_active_api_key_with_model

    def get_setting(key: str, default: str = "") -> str:
        setting = db.query(AppSettings).filter(AppSettings.key == key).first()
        return setting.value if setting else default

    # Generate IDs
    message_id = str(uuid.uuid4())
    conversation_id = payload.conversation_id or str(uuid.uuid4())

    # Get LLM provider
    llm_provider_name = get_setting("llm.ai_search.provider", "OPENAI")
    llm_model = get_setting("llm.ai_search.model", "gpt-4o-mini")

    provider: LLMProvider
    if llm_provider_name == "OPENAI":
        try:
            openai_key, default_model = get_active_api_key_with_model(db, "OPENAI")
            model_to_use = llm_model or default_model or "gpt-4o-mini"
            provider = OpenAIProvider(openai_key, default_model=model_to_use)
        except KeyMissingError:
            raise ConfigMissingError(
                "OPENAI API key not configured. Go to Admin → API Keys."
            )
    else:
        try:
            gemini_key, default_model = get_active_api_key_with_model(db, "GEMINI")
            model_to_use = llm_model or default_model or "gemini-2.5-flash"
            provider = GeminiProvider(gemini_key, default_model=model_to_use)
        except KeyMissingError:
            raise ConfigMissingError(
                "GEMINI API key not configured. Go to Admin → API Keys."
            )

    logger.info(f"AI Search chat processing message: {payload.message[:50]}...")

    # Initialize response variables
    response_type = "text"
    text_content = ""
    vendors: list[VendorCardData] | None = None
    comparison: ComparisonData | None = None
    progress: SearchProgressData | None = None
    evidence: list[EvidenceItem] | None = None
    actions: list[ChatAction] = []
    run_id = payload.run_id
    request_id = None

    # Merge context from payload
    context = payload.context or {}

    # Check if we have an existing run
    if payload.run_id:
        run = db.query(SearchRun).filter(SearchRun.id == payload.run_id).first()
        if run:
            request_id = run.request_id
            if run.status in ["QUEUED", "RUNNING"]:
                response_type = "progress"
                progress = get_run_progress(db, payload.run_id)
                text_content = f"Pencarian sedang berjalan ({run.progress_pct or 0}% selesai). Tahap: {run.current_step or 'processing'}..."

                return ProcurementChatResponse(
                    message_id=message_id,
                    conversation_id=conversation_id,
                    response_type=response_type,
                    text_content=text_content,
                    progress=progress,
                    run_id=run_id,
                    request_id=request_id,
                    timestamp=datetime.utcnow(),
                )

    # Analyze user intent with LLM
    intent_data = await analyze_user_intent(provider, payload.message, context)
    logger.info(f"Intent analysis: {intent_data}")

    intent = intent_data.get("intent", "other")
    category = intent_data.get("category") or context.get("category")
    # Merge keywords: use new keywords if available, otherwise use context keywords
    new_keywords = intent_data.get("keywords", [])
    context_keywords = context.get("keywords", []) if context else []
    keywords = new_keywords if new_keywords else context_keywords
    # If category exists but no keywords, use category as keyword
    if not keywords and category:
        keywords = [category]
    budget = intent_data.get("budget") or context.get("budget")
    location = intent_data.get("location") or context.get("location")
    requirements = intent_data.get("requirements", []) or context.get("requirements", [])
    needs_clarification = intent_data.get("needs_clarification", False)
    clarification_question = intent_data.get("clarification_question")

    # Update context for response
    updated_context = {
        "category": category,
        "keywords": keywords,
        "budget": budget,
        "location": location,
        "requirements": requirements,
    }

    # Handle different intents
    if intent == "greeting":
        text_content = (
            "Halo! 👋 Saya adalah AI assistant untuk pencarian vendor.\n\n"
            "Saya bisa membantu Anda:\n"
            "- **Mencari** vendor untuk berbagai kategori\n"
            "- **Membandingkan** vendor side-by-side\n"
            "- **Menganalisis** pricing dan fitur\n\n"
            "Silakan ceritakan, vendor apa yang Anda cari?"
        )
        actions = [
            ChatAction(
                type="START_SEARCH",
                label="Mulai Pencarian Baru",
                icon="search",
                variant="primary",
            ),
        ]

    elif intent == "search" or (intent == "other" and keywords):
        # Search for vendors
        if run_id:
            # Search from existing run
            vendors = get_top_vendors(db, run_id, limit=6, filters={"location": location})
        else:
            # Search from all vendors in database
            vendors = search_vendors_by_keywords(db, keywords, location, limit=6)

        if vendors:
            # Check if we should trigger additional research
            avg_score = None
            scores = [v.overall_score for v in vendors if v.overall_score]
            if scores:
                avg_score = sum(scores) / len(scores)

            should_research = should_trigger_deep_research(
                db_vendor_count=len(vendors),
                avg_score=avg_score,
                threshold_count=3,
                threshold_score=50.0,
            )

            response_type = "vendors"
            text_content = await generate_vendor_summary(provider, vendors, category, location)
            actions = [
                ChatAction(
                    type="COMPARE_VENDORS",
                    label="Bandingkan Top 3",
                    icon="git-compare",
                    variant="primary",
                    payload={"vendor_ids": [v.id for v in vendors[:3]]},
                ),
                ChatAction(
                    type="ADD_TO_SHORTLIST",
                    label="Tambah ke Shortlist",
                    icon="bookmark-plus",
                    variant="secondary",
                ),
            ]

            # Add option to search web for more vendors if results are limited
            if should_research:
                text_content += (
                    f"\n\n💡 *Hasil terbatas ({len(vendors)} vendor). "
                    "Klik 'Cari Lebih Banyak' untuk mencari dari web.*"
                )
                actions.append(
                    ChatAction(
                        type="START_DEEP_RESEARCH",
                        label="Cari Lebih Banyak di Web",
                        icon="globe",
                        variant="primary",
                        payload={
                            "category": category,
                            "keywords": keywords,
                            "location": location,
                        },
                    )
                )
        elif keywords:
            # No vendors found in database - automatically trigger DeepResearch
            search_desc = category or ", ".join(keywords[:3])
            loc_desc = f" di **{location}**" if location else ""

            # Calculate budget_max from budget string if available
            budget_max = None
            if budget:
                try:
                    # Extract numeric value from budget string (e.g., "500 juta" -> 500000000)
                    import re
                    budget_clean = budget.lower().replace(".", "").replace(",", "")
                    if "juta" in budget_clean:
                        match = re.search(r"(\d+)", budget_clean)
                        if match:
                            budget_max = int(match.group(1)) * 1_000_000
                    elif "milyar" in budget_clean or "miliar" in budget_clean:
                        match = re.search(r"(\d+)", budget_clean)
                        if match:
                            budget_max = int(match.group(1)) * 1_000_000_000
                    else:
                        match = re.search(r"(\d+)", budget_clean)
                        if match:
                            budget_max = int(match.group(1))
                except (ValueError, AttributeError):
                    pass

            # Automatically start DeepResearch
            try:
                research_result = await start_chat_research(
                    db=db,
                    user_id=user_id,
                    category=category or keywords[0],
                    keywords=keywords,
                    location=location,
                    budget_max=budget_max,
                )

                response_type = "deep_research"
                run_id = research_result.run_id
                request_id = research_result.request_id

                text_content = (
                    f"Tidak ditemukan vendor untuk **{search_desc}**{loc_desc} di database.\n\n"
                    f"🔍 **Memulai pencarian web otomatis...**\n\n"
                    f"Saya akan mencari vendor dari berbagai sumber web dan menampilkan hasilnya secara real-time."
                )

                # Add progress data
                progress = SearchProgressData(
                    steps=[
                        SearchProgressStep(id="init", label="Inisialisasi", status="completed"),
                        SearchProgressStep(id="search", label="Mencari di web", status="active"),
                        SearchProgressStep(id="extract", label="Mengekstrak vendor", status="pending"),
                        SearchProgressStep(id="score", label="Menilai vendor", status="pending"),
                    ],
                    current_step="search",
                    progress_pct=10,
                    vendors_found=0,
                )

                actions = [
                    ChatAction(
                        type="CANCEL_RESEARCH",
                        label="Batalkan Pencarian",
                        icon="x",
                        variant="outline",
                        payload={"run_id": run_id},
                    ),
                ]

            except Exception as e:
                logger.error(f"Failed to start DeepResearch: {e}")
                # Fallback to old behavior if DeepResearch fails
                text_content = (
                    f"Maaf, saya tidak menemukan vendor untuk **{search_desc}**{loc_desc} di database kami saat ini.\n\n"
                    "Untuk menemukan vendor yang sesuai, Anda bisa:\n"
                    "- **Buat Request Pencarian** baru untuk menjalankan pencarian web secara lengkap\n"
                    "- Gunakan kata kunci yang lebih umum\n"
                    "- Hubungi tim procurement untuk bantuan manual"
                )
                actions = [
                    ChatAction(
                        type="CREATE_REQUEST",
                        label="Buat Request Pencarian Web",
                        icon="search",
                        variant="primary",
                    ),
                ]
        elif needs_clarification and clarification_question:
            response_type = "gathering_info"
            text_content = f"Saya mengerti Anda mencari **{category or 'vendor'}**.\n\n{clarification_question}"
            actions = [
                ChatAction(
                    type="CREATE_REQUEST",
                    label="Buat Request Baru",
                    icon="plus",
                    variant="outline",
                ),
            ]
        else:
            text_content = (
                f"Maaf, saya tidak menemukan vendor untuk **{category or keywords[0] if keywords else 'kriteria Anda'}**.\n\n"
                "Coba:\n"
                "- Gunakan kata kunci yang berbeda\n"
                "- Perluas kriteria pencarian\n"
                "- Buat request pencarian baru untuk hasil yang lebih lengkap"
            )
            actions = [
                ChatAction(
                    type="CREATE_REQUEST",
                    label="Buat Request Pencarian",
                    icon="search",
                    variant="primary",
                ),
            ]

    elif intent == "compare":
        if payload.vendor_ids and len(payload.vendor_ids) >= 2:
            response_type = "comparison"
            comparison = build_comparison_data(db, payload.vendor_ids, run_id)
            text_content = f"Berikut perbandingan **{len(payload.vendor_ids)} vendor**:"
            actions = [
                ChatAction(
                    type="EXPORT_CSV",
                    label="Export CSV",
                    icon="download",
                    variant="outline",
                ),
            ]
        elif run_id:
            top = get_top_vendors(db, run_id, limit=3)
            if top:
                response_type = "comparison"
                comparison = build_comparison_data(db, [v.id for v in top], run_id)
                text_content = "Berikut perbandingan **top 3 vendor**:"
            else:
                text_content = "Tidak ada vendor untuk dibandingkan. Coba lakukan pencarian terlebih dahulu."
        else:
            text_content = "Silakan pilih vendor yang ingin dibandingkan atau lakukan pencarian terlebih dahulu."

    elif intent == "question":
        # Answer question using LLM
        prompt = f"""Kamu adalah procurement AI assistant. Jawab pertanyaan user dengan singkat dan membantu.

Pertanyaan: {payload.message}

Konteks:
- Kategori: {category or 'Belum ditentukan'}
- Budget: {budget or 'Belum ditentukan'}
- Lokasi: {location or 'Belum ditentukan'}

Jawab dalam bahasa Indonesia, maksimal 100 kata."""

        try:
            response = await provider.complete_text(prompt)
            text_content = response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            logger.error(f"LLM error: {e}")
            text_content = "Maaf, saya mengalami kendala. Silakan coba lagi."

    else:
        # Handle other/fallback - try to be helpful
        if category or keywords:
            # User mentioned something, try to search
            search_keywords = keywords if keywords else [category] if category else []
            if search_keywords:
                vendors = search_vendors_by_keywords(db, search_keywords, location, limit=6)
                if vendors:
                    response_type = "vendors"
                    text_content = await generate_vendor_summary(provider, vendors, category, location)
                    actions = [
                        ChatAction(
                            type="COMPARE_VENDORS",
                            label="Bandingkan",
                            icon="git-compare",
                            variant="primary",
                            payload={"vendor_ids": [v.id for v in vendors[:3]]},
                        ),
                    ]
                else:
                    text_content = f"Saya tidak menemukan vendor untuk **{category or search_keywords[0]}**. Mau coba kata kunci lain?"
        else:
            text_content = (
                "Saya siap membantu mencari vendor untuk Anda!\n\n"
                "Beritahu saya:\n"
                "- **Apa** yang Anda cari? (contoh: solar panel, CRM, cloud hosting)\n"
                "- **Budget** yang tersedia?\n"
                "- **Lokasi** yang diinginkan?\n"
            )
            actions = [
                ChatAction(
                    type="START_SEARCH",
                    label="Mulai Pencarian",
                    icon="search",
                    variant="primary",
                ),
            ]

    # Generate enhanced card data
    insights: list[InsightData] = []
    quick_stats: list[StatData] = []
    categories: list[CategoryData] = []
    pricing_overview: list[PricingData] = []
    filter_chips: list[FilterChip] = []

    if response_type == "vendors" and vendors:
        insights = generate_insights(db, run_id, vendors)
        quick_stats = generate_quick_stats(db, run_id, vendors)
        categories = generate_category_breakdown(db, run_id, vendors)
        pricing_overview = generate_pricing_overview(db, vendors)
        filter_chips = generate_filter_chips(keywords, location)
    elif response_type == "comparison" and comparison:
        insights = generate_insights(db, run_id, comparison.vendors)
        quick_stats = generate_quick_stats(db, run_id, comparison.vendors)
        pricing_overview = generate_pricing_overview(db, comparison.vendors)

    # Generate suggested queries
    suggested_queries = generate_suggested_queries(
        response_type,
        keywords,
        bool(vendors)
    )

    # Build context to return for next message
    response_context = ConversationContext(
        category=category,
        keywords=keywords,
        budget=budget,
        location=location,
        requirements=requirements,
    )

    return ProcurementChatResponse(
        message_id=message_id,
        conversation_id=conversation_id,
        response_type=response_type,
        text_content=text_content,
        vendors=vendors,
        comparison=comparison,
        progress=progress,
        evidence=evidence,
        filter_chips=filter_chips,
        suggested_queries=suggested_queries,
        actions=actions,
        insights=insights,
        quick_stats=quick_stats,
        categories=categories,
        pricing_overview=pricing_overview,
        context=response_context,
        run_id=run_id,
        request_id=request_id,
        timestamp=datetime.utcnow(),
    )

