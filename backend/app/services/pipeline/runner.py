"""Pipeline runner - orchestrates the vendor search pipeline."""

import json
import logging
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy.orm import Session

from app.models.procurement_request import ProcurementRequest, RequestStatus
from app.models.search_run import SearchRun
from app.models.vendor import Vendor
from app.models.vendor_asset import VendorAsset
from app.models.vendor_evidence import VendorFieldEvidence
from app.models.vendor_metrics import VendorMetrics
from app.models.vendor_source import VendorSource
from app.services.errors import ConfigMissingError, ProviderError
from app.services.keys import get_active_api_key
from app.services.llm.gemini import GeminiProvider
from app.services.llm.openai import OpenAIProvider
from app.services.pipeline.parallel_executor import ParallelExecutor
from app.services.pipeline.steps.dedup import deduplicate_vendors
from app.services.pipeline.steps.expand import expand_queries, expand_queries_with_tracking
from app.services.pipeline.steps.expand_indonesia import expand_with_indonesia_focus
from app.services.pipeline.steps.extract import (
    extract_vendors_from_pages,
    extract_vendors_with_tracking,
)
from app.services.pipeline.steps.fetch import fetch_pages
from app.services.pipeline.steps.gap_analysis import analyze_gaps
from app.services.pipeline.steps.logo import fetch_logos
from app.services.pipeline.steps.quality_assessment import (
    assess_research_quality,
)
from app.services.pipeline.steps.refine_search import (
    refine_search,
    should_continue_iteration,
)
from app.services.pipeline.steps.score import score_vendors
from app.services.pipeline.steps.search import dedupe_urls, search_web
from app.services.pipeline.steps.shopping_search import search_shopping_prices
from app.services.providers.base import ScrapedPage
from app.services.search.serper import SerperProvider
from app.services.category_classifier import (
    is_product_category,
    requires_shopping_search,
    CategoryType,
)

logger = logging.getLogger(__name__)


class PipelineStep(str, Enum):
    """Pipeline steps for progress tracking."""

    INIT = "INIT"
    EXPAND = "EXPAND"
    EXPAND_INDONESIA = "EXPAND_INDONESIA"
    SEARCH = "SEARCH"
    PARALLEL_SEARCH = "PARALLEL_SEARCH"
    FETCH = "FETCH"
    PARALLEL_SCRAPE = "PARALLEL_SCRAPE"
    EXTRACT = "EXTRACT"
    GAP_ANALYSIS = "GAP_ANALYSIS"
    REFINE_SEARCH = "REFINE_SEARCH"
    SHOPPING_SEARCH = "SHOPPING_SEARCH"
    QUALITY_ASSESS = "QUALITY_ASSESS"
    DEDUP = "DEDUP"
    SCORE = "SCORE"
    LOGO = "LOGO"
    SAVE = "SAVE"
    DONE = "DONE"


STEP_PROGRESS = {
    PipelineStep.INIT: 0,
    PipelineStep.EXPAND: 8,
    PipelineStep.EXPAND_INDONESIA: 12,
    PipelineStep.SEARCH: 20,
    PipelineStep.PARALLEL_SEARCH: 20,
    PipelineStep.FETCH: 35,
    PipelineStep.PARALLEL_SCRAPE: 35,
    PipelineStep.EXTRACT: 50,
    PipelineStep.GAP_ANALYSIS: 55,
    PipelineStep.REFINE_SEARCH: 60,
    PipelineStep.SHOPPING_SEARCH: 65,
    PipelineStep.QUALITY_ASSESS: 70,
    PipelineStep.DEDUP: 75,
    PipelineStep.SCORE: 82,
    PipelineStep.LOGO: 90,
    PipelineStep.SAVE: 95,
    PipelineStep.DONE: 100,
}

# String to progress mapping for when step is a string
STEP_PROGRESS_STR = {s.value: p for s, p in STEP_PROGRESS.items()}


def normalize_step(step: PipelineStep | str) -> str:
    """Normalize step to string value, handles both Enum and string."""
    if hasattr(step, "value"):
        return step.value
    return str(step)


def get_step_progress(step: PipelineStep | str) -> int:
    """Get progress percentage for a step, handles both Enum and string."""
    if isinstance(step, PipelineStep):
        return STEP_PROGRESS.get(step, 50)
    return STEP_PROGRESS_STR.get(str(step), 50)


class PipelineRunner:
    """Orchestrates the vendor search pipeline."""

    def __init__(self, db: Session, run_id: int):
        """
        Initialize pipeline runner.

        Args:
            db: Database session
            run_id: SearchRun ID to execute
        """
        self.db = db
        self.run_id = run_id
        self.run: SearchRun | None = None
        self.request: ProcurementRequest | None = None
        # Pipeline logging and token tracking
        self._pipeline_logs: list[dict] = []
        self._token_usage: dict[str, dict] = {}

    def _add_log(
        self,
        step: str,
        level: str,
        message: str,
        data: dict | None = None,
    ) -> None:
        """Add a log entry to the pipeline logs."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "step": step,
            "level": level,  # "info", "warning", "error", "debug"
            "message": message,
        }
        if data:
            entry["data"] = data
        self._pipeline_logs.append(entry)

        # Also log to standard logger
        log_fn = getattr(logger, level, logger.info)
        log_fn(f"[{step}] {message}")

    def _add_token_usage(
        self,
        step: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        model: str = "",
    ) -> None:
        """Track token usage for a step."""
        if step not in self._token_usage:
            self._token_usage[step] = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "calls": 0,
                "model": model,
            }
        self._token_usage[step]["prompt_tokens"] += prompt_tokens
        self._token_usage[step]["completion_tokens"] += completion_tokens
        self._token_usage[step]["total_tokens"] += total_tokens
        self._token_usage[step]["calls"] += 1
        if model:
            self._token_usage[step]["model"] = model

    def _save_logs_and_tokens(self) -> None:
        """Save accumulated logs and token usage to the run."""
        if not self.run:
            return
        try:
            self.run.pipeline_logs = json.dumps(self._pipeline_logs)
            self.run.token_usage = json.dumps(self._token_usage)
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to save logs/tokens: {e}")

    def _is_cancelled(self) -> bool:
        """Check if run has been cancelled by user.
        
        Re-fetches run from DB to get latest status.
        Returns True if run should stop.
        """
        if not self.run:
            return False

        # Refresh run from DB to check for cancellation
        self.db.refresh(self.run)
        if self.run.status == "CANCELLED":
            logger.info(f"Run {self.run_id} was cancelled, stopping pipeline")
            return True
        return False

    def _update_run(
        self,
        step: PipelineStep | str,
        status: str | None = None,
        error: str | None = None,
        vendors_found: int | None = None,
        sources_searched: int | None = None,
    ) -> None:
        """Update run status in database. Handles both Enum and string step values."""
        if not self.run:
            return

        try:
            self.run.current_step = normalize_step(step)
            self.run.progress_pct = get_step_progress(step)

            if status:
                self.run.status = status
            if error:
                # Truncate error to avoid DB overflow
                self.run.error_message = error[:1000] if len(error) > 1000 else error
            if vendors_found is not None:
                self.run.vendors_found = vendors_found
            if sources_searched is not None:
                self.run.sources_searched = sources_searched

            is_done = (
                (isinstance(step, PipelineStep) and step == PipelineStep.DONE)
                or (isinstance(step, str) and step == "DONE")
            )
            if is_done or error:
                self.run.completed_at = datetime.now(timezone.utc)

            # Also update request status when run completes or fails
            if self.request:
                if status == "COMPLETED":
                    self.request.status = RequestStatus.COMPLETED.value
                elif status == "FAILED" or error:
                    self.request.status = RequestStatus.FAILED.value
                elif status == "RUNNING":
                    self.request.status = RequestStatus.RUNNING.value

            # Always save logs and tokens
            if self._pipeline_logs:
                self.run.pipeline_logs = json.dumps(self._pipeline_logs)
            if self._token_usage:
                self.run.token_usage = json.dumps(self._token_usage)

            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to update run status: {e}")
            # Try to at least commit what we have
            try:
                self.db.rollback()
            except Exception:
                pass

    async def run_pipeline(self) -> None:
        """
        Execute the full pipeline.

        Steps:
        1. Expand queries from request
        2. Search web for each query (single or multi-provider)
        3. Fetch page content (single or multi-provider)
        4. Extract vendor info via LLM
        5. Deduplicate vendors
        6. Score vendors
        7. Fetch logos
        8. Save to database
        """
        # Load run and request
        self.run = self.db.query(SearchRun).filter(SearchRun.id == self.run_id).first()
        if not self.run:
            logger.error(f"Run {self.run_id} not found")
            return

        self.request = (
            self.db.query(ProcurementRequest)
            .filter(ProcurementRequest.id == self.run.request_id)
            .first()
        )
        if not self.request:
            self._update_run(PipelineStep.INIT, status="FAILED", error="Request not found")
            return

        # Mark as running
        self.run.status = "RUNNING"
        self.run.started_at = datetime.now(timezone.utc)
        self._update_run(PipelineStep.INIT)

        try:
            # Parse selected providers from request
            selected_providers = self._parse_selected_providers()
            use_multi_provider = bool(selected_providers)

            # Get LLM provider (always needed)
            llm = await self._get_llm_provider()

            # Step 1: Expand queries
            self._update_run(PipelineStep.EXPAND)
            self._add_log("EXPAND", "info", "Starting query expansion")
            keywords = json.loads(self.request.keywords) if self.request.keywords else []
            must_have = (
                json.loads(self.request.must_have_criteria)
                if self.request.must_have_criteria
                else []
            )
            nice_to_have = (
                json.loads(self.request.nice_to_have_criteria)
                if self.request.nice_to_have_criteria
                else []
            )

            expand_result = await expand_queries_with_tracking(
                llm=llm,
                title=self.request.title,
                description=self.request.description or "",
                category=self.request.category or "general",
                keywords=keywords,
                must_have=must_have,
                nice_to_have=nice_to_have,
                num_queries=5,
            )
            queries = expand_result.queries

            # Track token usage from expansion
            self._add_token_usage(
                "EXPAND",
                expand_result.prompt_tokens,
                expand_result.completion_tokens,
                expand_result.total_tokens,
                expand_result.model,
            )
            self._add_log("EXPAND", "info",
                f"Generated {len(queries)} queries, {expand_result.total_tokens} tokens",
                {"queries": queries, "tokens": expand_result.total_tokens})

            # Check for cancellation
            if self._is_cancelled():
                return

            # Step 2 & 3: Search and Fetch (multi-provider or legacy)
            if use_multi_provider:
                pages = await self._execute_multi_provider_collection(
                    queries, selected_providers
                )
            else:
                pages = await self._execute_legacy_collection(queries)

            # Check for cancellation
            if self._is_cancelled():
                return

            # Step 4: Extract vendors
            self._update_run(PipelineStep.EXTRACT)
            self._add_log("EXTRACT", "info", f"Starting extraction from {len(pages)} pages")
            extraction_result = await extract_vendors_with_tracking(
                llm=llm,
                pages=pages,
                category=self.request.category or "general",
                requirements=must_have + nice_to_have,
                log_callback=self._add_log,
            )
            extracted = extraction_result.vendors

            # Track token usage from extraction
            self._add_token_usage(
                "EXTRACT",
                extraction_result.token_usage.prompt_tokens,
                extraction_result.token_usage.completion_tokens,
                extraction_result.token_usage.total_tokens,
                extraction_result.token_usage.model,
            )
            self._add_log("EXTRACT", "info",
                f"Extraction complete: {len(extracted)} vendors, "
                f"{extraction_result.token_usage.total_tokens} tokens used",
                {"vendors": len(extracted), "tokens": extraction_result.token_usage.total_tokens})

            # Step 5: Deduplicate
            self._update_run(PipelineStep.DEDUP)
            deduped = deduplicate_vendors(extracted)

            # Step 6: Score
            self._update_run(PipelineStep.SCORE)
            scored = score_vendors(deduped, must_have, nice_to_have)

            # Step 7: Fetch logos
            self._update_run(PipelineStep.LOGO)
            self._add_log("LOGO", "info", f"Fetching logos for {len(scored)} vendors")
            logos = await fetch_logos(scored)
            self._add_log("LOGO", "info",
                f"Logo fetch complete: {sum(1 for l in logos if l.logo_url)}/{len(logos)} found")

            # Step 8: Save to database
            self._update_run(PipelineStep.SAVE)
            await self._save_results(scored, pages, logos)

            # Done
            self._update_run(
                PipelineStep.DONE,
                status="COMPLETED",
                vendors_found=len(scored),
            )

            # Close LLM provider
            await llm.close()

            logger.info(f"Pipeline completed for run {self.run_id}: {len(scored)} vendors found")

        except ConfigMissingError as e:
            self._update_run(
                PipelineStep.INIT,
                status="FAILED",
                error=f"Missing API key: {e.provider}",
            )
            logger.error(f"Pipeline failed: {e}")
        except ProviderError as e:
            self._update_run(
                self.run.current_step if self.run else PipelineStep.INIT,
                status="FAILED",
                error=f"Provider error: {e.message}",
            )
            logger.error(f"Pipeline failed: {e}")
        except Exception as e:
            self._update_run(
                self.run.current_step if self.run else PipelineStep.INIT,
                status="FAILED",
                error=str(e)[:500],
            )
            logger.exception(f"Pipeline failed unexpectedly: {e}")

    def _parse_selected_providers(self) -> dict[str, list[str]] | None:
        """
        Parse selected providers from request.

        Returns:
            Dict with 'search' and 'scrape' provider lists, or None if not set.
        """
        if not self.request or not self.request.selected_providers:
            return None

        try:
            providers = json.loads(self.request.selected_providers)
            if not providers or not isinstance(providers, list):
                return None

            # Categorize providers
            from app.services.providers.registry import (
                _scrape_providers,
                _search_providers,
            )

            search = [p for p in providers if p in _search_providers]
            scrape = [p for p in providers if p in _scrape_providers]

            if not search and not scrape:
                return None

            return {"search": search, "scrape": scrape}

        except (json.JSONDecodeError, TypeError):
            logger.warning(f"Invalid selected_providers JSON: {self.request.selected_providers}")
            return None

    async def _get_llm_provider(self):
        """Get LLM provider based on AI config settings."""
        from app.models.app_settings import AppSettings
        from app.services.keys import get_active_api_key_with_model

        def get_setting(key: str, default: str = "") -> str:
            setting = self.db.query(AppSettings).filter(
                AppSettings.key == key
            ).first()
            return setting.value if setting else default

        # Get configured LLM provider and model for procurement
        llm_provider = get_setting("llm.procurement.provider", "OPENAI")
        llm_model = get_setting("llm.procurement.model", "")

        logger.info(f"Pipeline using LLM: provider={llm_provider} model={llm_model}")

        # Create LLM provider based on config (NO silent fallback)
        if llm_provider == "OPENAI":
            try:
                openai_key, default_model = get_active_api_key_with_model(
                    self.db, "OPENAI"
                )
                model_to_use = llm_model or default_model or "gpt-4o"
                return OpenAIProvider(openai_key, default_model=model_to_use)
            except ConfigMissingError:
                raise ConfigMissingError(
                    "OPENAI API key not configured. "
                    "Go to Admin → API Keys to add OPENAI key, "
                    "or change AI Config to use GEMINI."
                )
        elif llm_provider == "GEMINI":
            try:
                gemini_key, default_model = get_active_api_key_with_model(
                    self.db, "GEMINI"
                )
                model_to_use = llm_model or default_model or "gemini-1.5-pro"
                return GeminiProvider(gemini_key, default_model=model_to_use)
            except ConfigMissingError:
                raise ConfigMissingError(
                    "GEMINI API key not configured. "
                    "Go to Admin → API Keys to add GEMINI key, "
                    "or change AI Config to use OPENAI."
                )
        else:
            raise ConfigMissingError(
                f"Unknown LLM provider '{llm_provider}'. "
                "Go to Admin → AI Configuration to select OPENAI or GEMINI."
            )

    async def _execute_multi_provider_collection(
        self,
        queries: list[str],
        selected_providers: dict[str, list[str]],
    ) -> list[ScrapedPage]:
        """
        Execute parallel data collection with multiple providers.

        Args:
            queries: List of search queries
            selected_providers: Dict with 'search' and 'scrape' provider lists

        Returns:
            List of ScrapedPage from all providers (no dedup)
        """
        search_providers = selected_providers.get("search", [])
        scrape_providers = selected_providers.get("scrape", [])

        # If no search providers selected, use default from settings
        if not search_providers:
            search_providers = ["SERPER", "TAVILY"]

        # If no scrape providers selected, use default (FIRECRAWL first for quality)
        if not scrape_providers:
            scrape_providers = ["FIRECRAWL", "JINA_READER"]

        logger.info(
            f"Multi-provider collection: search={search_providers}, scrape={scrape_providers}"
        )

        # Create parallel executor
        executor = ParallelExecutor(
            db=self.db,
            run_id=self.run_id,
            on_progress=lambda step, pct: self._update_run(step),
        )

        # Execute full pipeline
        result = await executor.execute_full_pipeline(
            queries=queries,
            search_providers=search_providers,
            scrape_providers=scrape_providers,
            results_per_query=10,
            max_concurrent_scrape=5,
        )

        # Update sources searched
        self._update_run(
            PipelineStep.PARALLEL_SCRAPE,
            sources_searched=result.total_urls,
        )

        logger.info(
            f"Multi-provider collection complete: "
            f"{result.total_urls} URLs, {result.total_pages_scraped} pages scraped"
        )

        return result.scraped_pages

    async def _execute_legacy_collection(self, queries: list[str]) -> list[ScrapedPage]:
        """
        Execute legacy single-provider collection (for backwards compatibility).

        Args:
            queries: List of search queries

        Returns:
            List of ScrapedPage (converted from legacy format)
        """
        from app.models.app_settings import AppSettings
        from app.services.search.tavily import TavilyProvider

        def get_setting(key: str, default: str = "") -> str:
            setting = self.db.query(AppSettings).filter(
                AppSettings.key == key
            ).first()
            return setting.value if setting else default

        # Get search strategy from settings
        search_strategy = get_setting("web_search.provider", "SERPER")
        if not search_strategy:
            search_strategy = get_setting("search_strategy", "SERPER")

        logger.info(f"Legacy collection using search strategy: {search_strategy}")

        # Create search provider
        if search_strategy == "TAVILY":
            try:
                search_key = get_active_api_key(self.db, "TAVILY")
                search_provider = TavilyProvider(search_key)
            except ConfigMissingError:
                raise ConfigMissingError(
                    "TAVILY API key not configured. "
                    "Go to Admin → API Keys to add TAVILY key."
                )
        else:
            try:
                search_key = get_active_api_key(self.db, "SEARCH_PROVIDER")
                search_provider = SerperProvider(search_key)
            except ConfigMissingError:
                raise ConfigMissingError(
                    "SEARCH_PROVIDER API key not configured. "
                    "Go to Admin → API Keys to add Serper key."
                )

        # Step 2: Search web
        self._update_run(PipelineStep.SEARCH)
        search_results = await search_web(
            search_provider=search_provider,
            queries=queries,
            results_per_query=10,
        )
        urls = dedupe_urls(search_results)
        self._update_run(
            PipelineStep.SEARCH,
            sources_searched=len(urls),
        )

        # Step 3: Fetch pages
        self._update_run(PipelineStep.FETCH)
        legacy_pages = await fetch_pages(urls, max_concurrent=5)

        # Close search provider
        await search_provider.close()

        # Convert legacy pages to ScrapedPage format

        pages: list[ScrapedPage] = []
        for page in legacy_pages:
            pages.append(
                ScrapedPage(
                    url=page.url,
                    title=page.title,
                    content=page.content,
                    content_format="text",
                    content_hash=page.content_hash,
                    status=page.status,
                    error=page.error,
                    source_provider="HTTPX",
                    fetched_at=page.fetched_at,
                    metadata={},
                )
            )

        return pages

    async def _expand_with_indonesia_focus(
        self,
        llm,
        keywords: list[str],
        must_have: list[str],
        nice_to_have: list[str],
        location: str | None = None,
        region_bias: bool = True,
    ) -> list[str]:
        """
        Expand queries with Indonesia focus.

        This is the enhanced expansion step for DeepResearch.
        """
        self._update_run(PipelineStep.EXPAND_INDONESIA)

        queries = await expand_with_indonesia_focus(
            llm=llm,
            title=self.request.title,
            description=self.request.description or "",
            category=self.request.category or "general",
            keywords=keywords,
            must_have=must_have,
            nice_to_have=nice_to_have,
            location=location,
            region_bias=region_bias,
            num_base_queries=5,
            num_indonesia_queries=5,
        )

        logger.info(f"Generated {len(queries)} Indonesia-focused queries")
        return queries

    async def _execute_gap_analysis_loop(
        self,
        llm,
        extracted_vendors: list,
        search_providers: list[str],
        scrape_providers: list[str],
        pages: list[ScrapedPage],
        max_iterations: int = 3,
        gap_threshold: float = 0.6,
    ) -> tuple[list, list[ScrapedPage], int]:
        """
        Execute the DeepResearch gap analysis and refinement loop.

        Returns:
            Tuple of (updated_vendors, all_pages, iterations_completed)
        """
        vendors = extracted_vendors
        all_pages = list(pages)
        iterations_completed = 0
        previous_completeness = None

        for iteration in range(1, max_iterations + 1):
            logger.info(f"Gap analysis iteration {iteration}/{max_iterations}")

            # Check for cancellation
            if self._is_cancelled():
                break

            # Phase 1: Analyze gaps
            self._update_run(PipelineStep.GAP_ANALYSIS)

            # Convert vendors to dicts for gap analysis
            vendor_dicts = []
            for v in vendors:
                if hasattr(v, 'vendor'):
                    # ScoredVendor - extract the inner ExtractedVendor and convert
                    inner = v.vendor
                    vd = dict(inner.data) if hasattr(inner, 'data') else {}
                    vd['name'] = inner.name if hasattr(inner, 'name') else v.vendor.name
                    vd['evidence'] = inner.evidence if hasattr(inner, 'evidence') else []
                    vd['source_url'] = inner.source_url if hasattr(inner, 'source_url') else None
                    vendor_dicts.append(vd)
                elif hasattr(v, 'data') and hasattr(v, 'name'):
                    # ExtractedVendor - convert to dict
                    vd = dict(v.data)
                    vd['name'] = v.name
                    vd['evidence'] = v.evidence if hasattr(v, 'evidence') else []
                    vd['source_url'] = v.source_url if hasattr(v, 'source_url') else None
                    vendor_dicts.append(vd)
                elif isinstance(v, dict):
                    vendor_dicts.append(v)

            gap_result = await analyze_gaps(
                vendors=vendor_dicts,
                llm=llm,
                gap_threshold=gap_threshold,
            )

            logger.info(
                f"Gap analysis: completeness={gap_result.overall_completeness:.1f}%, "
                f"needs_iteration={gap_result.needs_iteration}"
            )

            # Check if we should continue
            if not should_continue_iteration(
                gap_result=gap_result,
                iteration=iteration,
                previous_completeness=previous_completeness,
            ):
                logger.info("Stopping iteration loop - convergence reached")
                break

            # Phase 2: Execute refined search
            self._update_run(PipelineStep.REFINE_SEARCH)
            refine_result = await refine_search(
                db=self.db,
                run_id=self.run_id,
                gap_result=gap_result,
                iteration=iteration,
                search_providers=search_providers,
                scrape_providers=scrape_providers,
            )

            if refine_result.scraped_pages:
                all_pages.extend(refine_result.scraped_pages)

                # Phase 3: Extract from new pages
                self._update_run(PipelineStep.EXTRACT)
                self._add_log("EXTRACT", "info", f"Refine iteration {iteration}: extracting from {len(refine_result.scraped_pages)} new pages")
                refine_extraction = await extract_vendors_with_tracking(
                    llm=llm,
                    pages=refine_result.scraped_pages,
                    category=self.request.category or "general",
                    requirements=[],
                    log_callback=self._add_log,
                )
                new_extracted = refine_extraction.vendors

                # Track token usage
                self._add_token_usage(
                    "EXTRACT",
                    refine_extraction.token_usage.prompt_tokens,
                    refine_extraction.token_usage.completion_tokens,
                    refine_extraction.token_usage.total_tokens,
                    refine_extraction.token_usage.model,
                )

                # Merge new vendors
                def get_vendor_name(v) -> str:
                    """Extract vendor name from various object types."""
                    if hasattr(v, 'vendor') and hasattr(v.vendor, 'name'):
                        return v.vendor.name.lower()
                    elif hasattr(v, 'name'):  # ExtractedVendor
                        return v.name.lower()
                    elif isinstance(v, dict):
                        return v.get('name', '').lower()
                    return ''

                existing_names = {get_vendor_name(v) for v in vendors}
                for new_vendor in new_extracted:
                    name = get_vendor_name(new_vendor)
                    if name and name not in existing_names:
                        vendors.append(new_vendor)
                        existing_names.add(name)

            iterations_completed = iteration
            previous_completeness = gap_result.overall_completeness

        return vendors, all_pages, iterations_completed

    async def _execute_shopping_search(
        self,
        vendors: list,
        category: str | None,
    ) -> dict:
        """
        Execute Google Shopping search for vendor pricing.

        This performs two types of searches:
        1. Category-based search: Search for the product category to get market prices
        2. Vendor-specific search: Search for each vendor's products

        Returns:
            Dict with vendor pricing data and category pricing
        """
        self._update_run(PipelineStep.SHOPPING_SEARCH)

        vendor_names = []
        for v in vendors[:10]:  # Limit to top 10 vendors
            if hasattr(v, 'vendor') and hasattr(v.vendor, 'name'):
                vendor_names.append(v.vendor.name)
            elif hasattr(v, 'name'):  # ExtractedVendor
                vendor_names.append(v.name)
            elif isinstance(v, dict):
                vendor_names.append(v.get('name', ''))

        # Get category keywords from request
        keywords = []
        if self.request.keywords:
            try:
                keywords = json.loads(self.request.keywords)[:5]
            except json.JSONDecodeError:
                pass

        # Add category and title as keywords if not already included
        if category and category not in keywords:
            keywords.insert(0, category)
        if self.request.title and self.request.title not in keywords:
            keywords.insert(0, self.request.title)

        # Limit to top 5 keywords
        keywords = keywords[:5]

        if not keywords:
            logger.warning("No keywords for shopping search")
            return {}

        try:
            # First, do a category-based search (without vendor names) to get market prices
            from app.services.pipeline.steps.shopping_search import get_category_price_benchmark

            category_benchmark = await get_category_price_benchmark(
                db=self.db,
                category=category or self.request.title,
                sample_keywords=keywords[:3],
            )

            logger.info(
                f"Category benchmark: {category_benchmark.get('category')} - "
                f"avg: {category_benchmark.get('price_avg')}, "
                f"sample size: {category_benchmark.get('sample_size')}"
            )

            # Then do vendor-specific searches if we have vendors
            shopping_result = None
            if vendor_names:
                shopping_result = await search_shopping_prices(
                    db=self.db,
                    vendor_names=vendor_names,
                    product_keywords=keywords,
                    category=category,
                )
                logger.info(
                    f"Vendor shopping search: {shopping_result.total_products} products, "
                    f"market avg: {shopping_result.market_avg}"
                )

            # Combine results
            result = {
                "category_benchmark": category_benchmark,
                "vendor_pricing": shopping_result.to_dict().get("vendor_pricing", {}) if shopping_result else {},
                "category_pricing": shopping_result.to_dict().get("category_pricing", {}) if shopping_result else {},
                "market_avg": shopping_result.market_avg if shopping_result else category_benchmark.get("price_avg"),
                "total_products": (shopping_result.total_products if shopping_result else 0) + category_benchmark.get("sample_size", 0),
                "search_queries": keywords,
            }

            return result

        except Exception as e:
            logger.warning(f"Shopping search failed: {e}")
            import traceback
            traceback.print_exc()
            return {}

    async def _assess_research_quality(
        self,
        vendors: list,
        pages: list[ScrapedPage],
        iterations: int,
    ) -> dict:
        """
        Assess research quality across all vendors.

        Returns:
            Quality assessment dict
        """
        self._update_run(PipelineStep.QUALITY_ASSESS)

        vendor_dicts = []
        for v in vendors:
            if hasattr(v, 'vendor'):
                # ScoredVendor wrapper
                vd = v.vendor.to_dict() if hasattr(v.vendor, 'to_dict') else dict(v.vendor.data)
                vd['name'] = v.vendor.name
                vendor_dicts.append(vd)
            elif hasattr(v, 'data') and hasattr(v, 'name'):
                # ExtractedVendor object
                vd = dict(v.data)
                vd['name'] = v.name
                vd['evidence'] = v.evidence if hasattr(v, 'evidence') else []
                vendor_dicts.append(vd)
            elif isinstance(v, dict):
                vendor_dicts.append(v)

        all_sources = [{"url": p.url, "fetched_at": p.fetched_at.isoformat()} for p in pages]

        quality_report = assess_research_quality(
            vendors=vendor_dicts,
            all_sources=all_sources,
            research_iterations=iterations,
        )

        logger.info(
            f"Quality assessment: overall={quality_report.overall_quality:.1f}%, "
            f"grade={quality_report.overall_grade}"
        )

        return quality_report.to_dict()

    async def run_deep_research_pipeline(self) -> None:
        """
        Execute the DeepResearch-enhanced pipeline.

        This is an enhanced version of run_pipeline that includes:
        - Indonesia-focused query expansion
        - Iterative gap analysis and refinement
        - Google Shopping integration
        - Quality assessment

        Steps:
        1. Expand queries with Indonesia focus
        2. Search web (multi-provider)
        3. Fetch page content (multi-provider)
        4. Extract vendor info via LLM
        5. Gap analysis loop (iterate 1-3 times)
        6. Shopping search for pricing
        7. Quality assessment
        8. Deduplicate vendors
        9. Enhanced scoring
        10. Fetch logos
        11. Save to database
        """
        # Load run and request
        self.run = self.db.query(SearchRun).filter(SearchRun.id == self.run_id).first()
        if not self.run:
            logger.error(f"Run {self.run_id} not found")
            return

        self.request = (
            self.db.query(ProcurementRequest)
            .filter(ProcurementRequest.id == self.run.request_id)
            .first()
        )
        if not self.request:
            self._update_run(PipelineStep.INIT, status="FAILED", error="Request not found")
            return

        # Mark as running
        self.run.status = "RUNNING"
        self.run.started_at = datetime.now(timezone.utc)
        self._update_run(PipelineStep.INIT)

        try:
            # Parse selected providers
            selected_providers = self._parse_selected_providers()
            search_providers = selected_providers.get("search", ["SERPER"]) if selected_providers else ["SERPER"]
            scrape_providers = selected_providers.get("scrape", ["JINA_READER"]) if selected_providers else ["JINA_READER"]

            # Get LLM provider
            llm = await self._get_llm_provider()

            # Parse request data
            keywords = json.loads(self.request.keywords) if self.request.keywords else []
            must_have = (
                json.loads(self.request.must_have_criteria)
                if self.request.must_have_criteria
                else []
            )
            nice_to_have = (
                json.loads(self.request.nice_to_have_criteria)
                if self.request.nice_to_have_criteria
                else []
            )

            # Get research config (defaults to Indonesia focus)
            research_config = {}
            if hasattr(self.request, 'research_config') and self.request.research_config:
                try:
                    research_config = json.loads(self.request.research_config)
                except (json.JSONDecodeError, TypeError):
                    research_config = {}

            max_iterations = research_config.get("max_iterations", 2)
            gap_threshold = research_config.get("gap_threshold", 0.6)
            include_shopping = research_config.get("include_shopping", True)
            region_bias = research_config.get("region_bias", True)
            location = research_config.get("location", "Indonesia")

            # Step 1: Expand queries with Indonesia focus
            queries = await self._expand_with_indonesia_focus(
                llm=llm,
                keywords=keywords,
                must_have=must_have,
                nice_to_have=nice_to_have,
                location=location,
                region_bias=region_bias,
            )

            if self._is_cancelled():
                return

            # Step 2 & 3: Multi-provider search and scrape
            pages = await self._execute_multi_provider_collection(
                queries, {"search": search_providers, "scrape": scrape_providers}
            )

            if self._is_cancelled():
                return

            # Step 4: Initial extraction
            self._update_run(PipelineStep.EXTRACT)
            self._add_log("EXTRACT", "info", f"DeepResearch: starting extraction from {len(pages)} pages")
            extraction_result = await extract_vendors_with_tracking(
                llm=llm,
                pages=pages,
                category=self.request.category or "general",
                requirements=must_have + nice_to_have,
                log_callback=self._add_log,
            )
            extracted = extraction_result.vendors

            # Track token usage
            self._add_token_usage(
                "EXTRACT",
                extraction_result.token_usage.prompt_tokens,
                extraction_result.token_usage.completion_tokens,
                extraction_result.token_usage.total_tokens,
                extraction_result.token_usage.model,
            )
            self._add_log("EXTRACT", "info",
                f"Initial extraction: {len(extracted)} vendors, {extraction_result.token_usage.total_tokens} tokens",
                {"vendors": len(extracted), "tokens": extraction_result.token_usage.total_tokens})

            # Step 5: Gap analysis loop
            if max_iterations > 1 and len(extracted) > 0:
                extracted, pages, iterations = await self._execute_gap_analysis_loop(
                    llm=llm,
                    extracted_vendors=extracted,
                    search_providers=search_providers,
                    scrape_providers=scrape_providers,
                    pages=pages,
                    max_iterations=max_iterations,
                    gap_threshold=gap_threshold,
                )
            else:
                iterations = 1

            if self._is_cancelled():
                return

            # Step 6: Shopping search - MANDATORY for product categories
            shopping_data = {}
            is_product = is_product_category(
                self.request.category,
                self.request.title,
                self.request.keywords,
            )
            requires_shopping, reason = requires_shopping_search(
                self.request.category,
                self.request.title,
                self.request.keywords,
            )

            if (include_shopping or requires_shopping) and len(extracted) > 0:
                logger.info(
                    f"Shopping search: is_product={is_product}, "
                    f"reason={reason}"
                )
                shopping_data = await self._execute_shopping_search(
                    vendors=extracted,
                    category=self.request.category,
                )

                # Log warning if product category but no pricing found
                if is_product and not shopping_data.get("vendor_pricing"):
                    logger.warning(
                        f"PRODUCT SEARCH WITHOUT MARKETPLACE PRICING: "
                        f"'{self.request.title}' (category: {self.request.category}). "
                        f"SerpAPI key may not be configured. "
                        f"Falling back to LLM-extracted pricing."
                    )

            # Step 7: Quality assessment
            quality_data = await self._assess_research_quality(
                vendors=extracted,
                pages=pages,
                iterations=iterations,
            )

            # Step 8: Deduplicate
            self._update_run(PipelineStep.DEDUP)
            deduped = deduplicate_vendors(extracted)

            # Step 9: Enhanced scoring
            self._update_run(PipelineStep.SCORE)
            scored = score_vendors(deduped, must_have, nice_to_have)

            # Step 10: Fetch logos
            self._update_run(PipelineStep.LOGO)
            logos = await fetch_logos(scored)

            # Step 11: Save to database with DeepResearch quality data
            self._update_run(PipelineStep.SAVE)
            await self._save_results(
                scored=scored,
                pages=pages,
                logos=logos,
                quality_data=quality_data,
                shopping_data=shopping_data,
                research_iterations=iterations,
            )

            # Store research metadata in run
            if self.run:
                self.run.research_iterations = iterations
                self.run.quality_assessment = json.dumps(quality_data)
                if shopping_data:
                    self.run.shopping_data = json.dumps(shopping_data)
                self.db.commit()

            # Done
            self._update_run(
                PipelineStep.DONE,
                status="COMPLETED",
                vendors_found=len(scored),
            )

            await llm.close()

            logger.info(
                f"DeepResearch pipeline completed for run {self.run_id}: "
                f"{len(scored)} vendors found, {iterations} iterations"
            )

        except ConfigMissingError as e:
            self._update_run(
                PipelineStep.INIT,
                status="FAILED",
                error=f"Missing API key: {e.provider}",
            )
            logger.error(f"Pipeline failed: {e}")
        except ProviderError as e:
            self._update_run(
                self.run.current_step if self.run else PipelineStep.INIT,
                status="FAILED",
                error=f"Provider error: {e.message}",
            )
            logger.error(f"Pipeline failed: {e}")
        except Exception as e:
            self._update_run(
                self.run.current_step if self.run else PipelineStep.INIT,
                status="FAILED",
                error=str(e)[:500],
            )
            logger.exception(f"Pipeline failed unexpectedly: {e}")

    async def _get_providers(self):
        """Get LLM and search providers based on AI config settings (legacy)."""
        from app.models.app_settings import AppSettings
        from app.services.keys import get_active_api_key_with_model
        from app.services.search.tavily import TavilyProvider

        def get_setting(key: str, default: str = "") -> str:
            setting = self.db.query(AppSettings).filter(
                AppSettings.key == key
            ).first()
            return setting.value if setting else default

        # Get configured LLM provider and model for procurement
        llm_provider = get_setting("llm.procurement.provider", "OPENAI")
        llm_model = get_setting("llm.procurement.model", "")

        logger.info(f"Pipeline using LLM: provider={llm_provider} model={llm_model}")

        # Create LLM provider based on config (NO silent fallback)
        if llm_provider == "OPENAI":
            try:
                openai_key, default_model = get_active_api_key_with_model(
                    self.db, "OPENAI"
                )
                # Use configured model or fallback to key's default
                model_to_use = llm_model or default_model or "gpt-4o"
                llm = OpenAIProvider(openai_key, default_model=model_to_use)
            except ConfigMissingError:
                raise ConfigMissingError(
                    "OPENAI API key not configured. "
                    "Go to Admin → API Keys to add OPENAI key, "
                    "or change AI Config to use GEMINI."
                )
        elif llm_provider == "GEMINI":
            try:
                gemini_key, default_model = get_active_api_key_with_model(
                    self.db, "GEMINI"
                )
                model_to_use = llm_model or default_model or "gemini-1.5-pro"
                llm = GeminiProvider(gemini_key, default_model=model_to_use)
            except ConfigMissingError:
                raise ConfigMissingError(
                    "GEMINI API key not configured. "
                    "Go to Admin → API Keys to add GEMINI key, "
                    "or change AI Config to use OPENAI."
                )
        else:
            raise ConfigMissingError(
                f"Unknown LLM provider '{llm_provider}'. "
                "Go to Admin → AI Configuration to select OPENAI or GEMINI."
            )

        # Get search strategy from new settings key
        search_strategy = get_setting("web_search.provider", "SERPER")
        # Fallback to legacy key
        if not search_strategy or search_strategy == "":
            search_strategy = get_setting("search_strategy", "SERPER")

        logger.info(f"Pipeline using search strategy: {search_strategy}")

        # Create appropriate search provider
        if search_strategy == "TAVILY":
            try:
                search_key = get_active_api_key(self.db, "TAVILY")
                search_provider = TavilyProvider(search_key)
            except ConfigMissingError:
                raise ConfigMissingError(
                    "TAVILY API key not configured. "
                    "Go to Admin → API Keys to add TAVILY key, "
                    "or change AI Config to use SERPER."
                )
        elif search_strategy == "GEMINI_GROUNDING":
            # Gemini grounding uses Serper as fallback for now
            logger.info("GEMINI_GROUNDING: using Serper as implementation")
            try:
                search_key = get_active_api_key(self.db, "SEARCH_PROVIDER")
                search_provider = SerperProvider(search_key)
            except ConfigMissingError:
                raise ConfigMissingError(
                    "SEARCH_PROVIDER API key not configured. "
                    "Go to Admin → API Keys to add Serper key."
                )
        else:
            # Default to Serper
            try:
                search_key = get_active_api_key(self.db, "SEARCH_PROVIDER")
                search_provider = SerperProvider(search_key)
            except ConfigMissingError:
                raise ConfigMissingError(
                    "SEARCH_PROVIDER API key not configured. "
                    "Go to Admin → API Keys to add Serper key."
                )

        return llm, search_provider

    async def _save_results(
        self,
        scored,
        pages,
        logos,
        quality_data: dict | None = None,
        shopping_data: dict | None = None,
        research_iterations: int = 1,
    ) -> None:
        """Save pipeline results to database.

        Args:
            scored: List of ScoredVendor objects
            pages: List of ScrapedPage objects
            logos: List of logo results
            quality_data: Quality assessment data from DeepResearch (optional)
            shopping_data: Shopping/pricing data from DeepResearch (optional)
            research_iterations: Number of research iterations completed
        """
        # Create page lookup
        page_map = {p.url: p for p in pages}
        logo_map = {logo_item.vendor_name: logo_item for logo_item in logos}

        # Extract per-vendor quality metrics if available
        vendor_quality = {}
        if quality_data and "vendor_reports" in quality_data:
            # vendor_reports is a dict with vendor names as keys
            for vendor_name, vr in quality_data.get("vendor_reports", {}).items():
                vendor_quality[vendor_name.lower()] = vr

        # Extract per-vendor pricing data if available
        vendor_pricing = {}
        if shopping_data and "vendor_pricing" in shopping_data:
            # vendor_pricing is a dict, not a list
            for vendor_name, vp in shopping_data.get("vendor_pricing", {}).items():
                vendor_pricing[vendor_name.lower()] = vp

        # Calculate source diversity
        unique_domains = set()
        for p in pages:
            try:
                from urllib.parse import urlparse
                domain = urlparse(p.url).netloc
                unique_domains.add(domain)
            except Exception:
                pass
        source_diversity = len(unique_domains)

        for scored_vendor in scored:
            vendor_data = scored_vendor.vendor

            # Helper to get value from vendor.data or evidence as fallback
            def get_field(field_name: str) -> str | None:
                """Get field value from vendor data or evidence."""
                # First try vendor.data
                value = vendor_data.data.get(field_name)
                if value:
                    return value
                # Fallback to evidence
                for ev in vendor_data.evidence:
                    if ev.get("field") == field_name:
                        return ev.get("value")
                return None

            # Create vendor with all extracted fields
            vendor = Vendor(
                name=vendor_data.name,
                website=get_field("website"),
                description=get_field("description"),
                location=get_field("location"),
                country=get_field("country"),
                industry=get_field("industry"),
                email=get_field("email"),
                phone=get_field("phone"),
                pricing_model=get_field("pricing_model"),
                pricing_details=get_field("pricing_details"),
                employee_count=get_field("employee_count"),
                security_compliance=get_field("security_compliance"),
                deployment=get_field("deployment"),
                integrations=get_field("integrations"),
            )
            self.db.add(vendor)
            self.db.flush()  # Get vendor ID

            # Create source
            page = page_map.get(vendor_data.source_url)
            source = VendorSource(
                vendor_id=vendor.id,
                search_run_id=self.run_id,
                source_url=vendor_data.source_url,
                source_type="WEBSITE",
                page_title=vendor_data.source_title or (page.title if page else None),
                raw_content=(page.content[:10000] if page else None),
                content_hash=(page.content_hash if page else None),
                fetch_status="SUCCESS" if page and page.status == "SUCCESS" else "FAILED",
                fetched_at=page.fetched_at if page else datetime.now(timezone.utc),
            )
            self.db.add(source)
            self.db.flush()

            # Create evidence records
            for ev in vendor_data.evidence:
                evidence = VendorFieldEvidence(
                    vendor_id=vendor.id,
                    source_id=source.id,
                    field_name=ev.get("field", "unknown"),
                    field_value=str(ev.get("value", ""))[:1000],
                    evidence_url=vendor_data.source_url,
                    evidence_snippet=str(ev.get("snippet", ""))[:2000],
                    confidence=0.8,  # Default confidence
                    extraction_method="LLM",
                )
                self.db.add(evidence)

            # Get vendor-specific quality data
            vendor_name_lower = vendor_data.name.lower()
            vq = vendor_quality.get(vendor_name_lower, {})
            vp = vendor_pricing.get(vendor_name_lower, {})

            # Save shopping data to vendor if available
            if vp:
                vendor.shopping_data = json.dumps(vp)
                vendor.price_range_min = vp.get("price_min")
                vendor.price_range_max = vp.get("price_max")
                vendor.price_last_updated = datetime.now(timezone.utc)
            else:
                # Fallback to LLM-extracted price range if no shopping data
                llm_price_min = vendor_data.data.get("price_range_min")
                llm_price_max = vendor_data.data.get("price_range_max")
                if llm_price_min:
                    try:
                        vendor.price_range_min = float(llm_price_min)
                    except (ValueError, TypeError):
                        pass
                if llm_price_max:
                    try:
                        vendor.price_range_max = float(llm_price_max)
                    except (ValueError, TypeError):
                        pass
                if vendor.price_range_min or vendor.price_range_max:
                    vendor.price_last_updated = datetime.now(timezone.utc)

            # Calculate quality score (from quality assessment or derived)
            quality_score = vq.get("overall_quality", 0.0)
            completeness_pct = vq.get("completeness_score", 0.0)
            confidence_pct = vq.get("confidence_score", 0.0)

            # Calculate price score (from shopping data or default)
            price_score = 50.0  # Default neutral
            price_competitiveness = None
            if vp:
                price_competitiveness = vp.get("competitiveness")
                if price_competitiveness is not None:
                    # Map competitiveness to score: below_market=80, market=50, above_market=30
                    if price_competitiveness < 0.9:
                        price_score = 80.0
                    elif price_competitiveness > 1.1:
                        price_score = 30.0
                    else:
                        price_score = 50.0

            # Calculate enhanced overall score if quality data available
            if quality_data:
                # Use enhanced formula: 35% fit + 25% trust + 25% quality + 15% price
                enhanced_overall = (
                    scored_vendor.fit_score * 0.35 +
                    scored_vendor.trust_score * 0.25 +
                    quality_score * 0.25 +
                    price_score * 0.15
                )
            else:
                enhanced_overall = scored_vendor.overall_score

            # Create metrics with all fields
            metrics = VendorMetrics(
                vendor_id=vendor.id,
                search_run_id=self.run_id,
                fit_score=scored_vendor.fit_score,
                trust_score=scored_vendor.trust_score,
                overall_score=round(enhanced_overall, 1),
                must_have_matched=scored_vendor.must_have_matched,
                must_have_total=scored_vendor.must_have_total,
                nice_to_have_matched=scored_vendor.nice_to_have_matched,
                nice_to_have_total=scored_vendor.nice_to_have_total,
                source_count=1,
                evidence_count=len(vendor_data.evidence),
                # DeepResearch quality fields
                quality_score=round(quality_score, 1),
                price_score=round(price_score, 1),
                completeness_pct=round(completeness_pct, 1),
                confidence_pct=round(confidence_pct, 1),
                source_diversity=source_diversity,
                research_depth=research_iterations,
                price_competitiveness=price_competitiveness,
            )
            self.db.add(metrics)

            # Create logo asset if found
            logo = logo_map.get(vendor_data.name)
            if logo and logo.logo_url:
                asset = VendorAsset(
                    vendor_id=vendor.id,
                    asset_type="LOGO",
                    asset_url=logo.logo_url,
                    source_url=logo.source_url,
                    priority=logo.priority,
                )
                self.db.add(asset)

        self.db.commit()
