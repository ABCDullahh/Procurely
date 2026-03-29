"""Refine search step - targeted follow-up research for identified gaps."""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.services.pipeline.steps.gap_analysis import GapAnalysisResult
from app.services.providers.base import ScrapedPage, SearchResult

logger = logging.getLogger(__name__)

# Maximum research iterations to prevent infinite loops
MAX_ITERATIONS = 3

# Delay between searches to avoid rate limiting
SEARCH_DELAY_SECONDS = 0.5


@dataclass
class RefineSearchResult:
    """Result from refined search iteration."""

    iteration: int
    queries_executed: list[str]
    search_results: list[SearchResult]
    scraped_pages: list[ScrapedPage]
    new_evidence: list[dict]  # New evidence extracted
    execution_time_ms: int
    errors: list[str]

    def to_dict(self) -> dict:
        return {
            "iteration": self.iteration,
            "queries_executed": self.queries_executed,
            "search_results_count": len(self.search_results),
            "scraped_pages_count": len(self.scraped_pages),
            "new_evidence_count": len(self.new_evidence),
            "execution_time_ms": self.execution_time_ms,
            "errors": self.errors,
        }


async def refine_search(
    db: Session,
    run_id: int,
    gap_result: GapAnalysisResult,
    iteration: int,
    search_providers: list[str],
    scrape_providers: list[str],
    max_queries: int = 10,
    max_results_per_query: int = 5,
) -> RefineSearchResult:
    """
    Execute targeted search for specific information gaps.

    This implements the "ACT" phase of DeepResearch iteration:
    1. Takes follow-up queries from gap analysis
    2. Executes parallel searches using selected providers
    3. Scrapes resulting pages
    4. Returns new content for extraction

    Args:
        db: Database session
        run_id: SearchRun ID for tracking
        gap_result: Results from gap analysis step
        iteration: Current iteration number (1-based)
        search_providers: Search provider names to use
        scrape_providers: Scrape provider names to use
        max_queries: Maximum queries to execute
        max_results_per_query: Max results per query

    Returns:
        RefineSearchResult with new scraped content
    """
    from app.services.pipeline.parallel_executor import ParallelExecutor

    start_time = datetime.now(timezone.utc)
    errors: list[str] = []

    # Check iteration limit
    if iteration > MAX_ITERATIONS:
        logger.info(f"Max iterations ({MAX_ITERATIONS}) reached, stopping refinement")
        return RefineSearchResult(
            iteration=iteration,
            queries_executed=[],
            search_results=[],
            scraped_pages=[],
            new_evidence=[],
            execution_time_ms=0,
            errors=["Max iterations reached"],
        )

    # Get follow-up queries from gap analysis
    queries = gap_result.follow_up_queries[:max_queries]

    if not queries:
        logger.info("No follow-up queries to execute")
        return RefineSearchResult(
            iteration=iteration,
            queries_executed=[],
            search_results=[],
            scraped_pages=[],
            new_evidence=[],
            execution_time_ms=0,
            errors=[],
        )

    logger.info(
        f"Refine search iteration {iteration}: executing {len(queries)} queries"
    )

    # Initialize parallel executor
    executor = ParallelExecutor(db, run_id)

    try:
        # Execute parallel search - returns list[ProviderResult]
        provider_results = await executor.execute_search(
            queries=queries,
            search_providers=search_providers,
            results_per_query=max_results_per_query,
        )

        # Collect unique URLs from all provider results
        urls = []
        seen_urls = set()
        search_results = []  # Collect all SearchResult objects
        for pr in provider_results:
            if pr.status.value == "COMPLETED":
                for item in pr.data:  # pr.data is list of dicts
                    url = item.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        urls.append(url)
                        # Convert to SearchResult
                        search_results.append(SearchResult(
                            url=url,
                            title=item.get("title", ""),
                            snippet=item.get("snippet", ""),
                            position=item.get("position", 0),
                            source_provider=item.get("source_provider", "unknown"),
                        ))

        logger.info(f"Found {len(urls)} unique URLs from search results")

        # Execute parallel scrape - returns list[ProviderResult]
        if urls:
            scrape_provider_results = await executor.execute_scrape(
                urls=urls[:30],  # Limit to 30 URLs per iteration
                scrape_providers=scrape_providers,
            )

            # Extract ScrapedPage objects from provider results
            scraped_pages = []
            for pr in scrape_provider_results:
                if pr.status.value == "COMPLETED":
                    for page_data in pr.data:
                        page = ScrapedPage.from_dict(page_data)
                        scraped_pages.append(page)
        else:
            scraped_pages = []

        # Filter successful pages
        successful_pages = [p for p in scraped_pages if p.status == "SUCCESS"]

        logger.info(
            f"Scraped {len(successful_pages)}/{len(scraped_pages)} pages successfully"
        )

        # Calculate execution time
        end_time = datetime.now(timezone.utc)
        execution_time_ms = int((end_time - start_time).total_seconds() * 1000)

        return RefineSearchResult(
            iteration=iteration,
            queries_executed=queries,
            search_results=search_results,
            scraped_pages=successful_pages,
            new_evidence=[],  # Will be filled by extraction step
            execution_time_ms=execution_time_ms,
            errors=errors,
        )

    except Exception as e:
        logger.error(f"Refine search failed: {e}")
        errors.append(str(e))

        end_time = datetime.now(timezone.utc)
        execution_time_ms = int((end_time - start_time).total_seconds() * 1000)

        return RefineSearchResult(
            iteration=iteration,
            queries_executed=queries,
            search_results=[],
            scraped_pages=[],
            new_evidence=[],
            execution_time_ms=execution_time_ms,
            errors=errors,
        )


async def merge_iteration_results(
    existing_vendors: list[dict],
    new_pages: list[ScrapedPage],
    new_evidence: list[dict],
) -> list[dict]:
    """
    Merge results from refinement iteration into existing vendor data.

    Updates vendor records with:
    - New evidence from additional sources
    - Updated field values with higher confidence
    - New source URLs

    Args:
        existing_vendors: Current vendor data
        new_pages: Newly scraped pages
        new_evidence: Evidence extracted from new pages

    Returns:
        Updated vendor list
    """
    # Build vendor lookup
    vendors_by_name = {v.get("name", "").lower(): v for v in existing_vendors}

    for evidence in new_evidence:
        vendor_name = evidence.get("vendor_name", "").lower()
        field_name = evidence.get("field")
        new_value = evidence.get("value")
        new_confidence = evidence.get("confidence", 0.5)

        if vendor_name in vendors_by_name and field_name and new_value:
            vendor = vendors_by_name[vendor_name]

            # Get existing evidence
            existing_evidence = vendor.get("evidence", [])
            existing_value = vendor.get(field_name)

            # Find existing evidence for this field
            field_evidence = [
                e for e in existing_evidence
                if e.get("field") == field_name
            ]

            if field_evidence:
                best_existing_confidence = max(
                    e.get("confidence", 0) for e in field_evidence
                )

                # Only update if new evidence is more confident
                if new_confidence > best_existing_confidence:
                    vendor[field_name] = new_value
                    existing_evidence.append(evidence)
            else:
                # No existing evidence, add new
                vendor[field_name] = new_value
                existing_evidence.append(evidence)

            vendor["evidence"] = existing_evidence

            # Add source if present
            source_url = evidence.get("source_url")
            if source_url:
                sources = vendor.get("sources", [])
                if source_url not in sources:
                    sources.append(source_url)
                vendor["sources"] = sources

    return existing_vendors


def should_continue_iteration(
    gap_result: GapAnalysisResult,
    iteration: int,
    improvement_threshold: float = 5.0,
    previous_completeness: float | None = None,
) -> bool:
    """
    Determine if another research iteration should be performed.

    Considers:
    - Maximum iteration limit
    - Whether gaps still exist
    - Whether previous iteration improved completeness

    Args:
        gap_result: Current gap analysis result
        iteration: Current iteration number
        improvement_threshold: Minimum % improvement required
        previous_completeness: Completeness from previous iteration

    Returns:
        True if another iteration should run
    """
    # Check iteration limit
    if iteration >= MAX_ITERATIONS:
        logger.info("Max iterations reached")
        return False

    # Check if gaps remain
    if not gap_result.needs_iteration:
        logger.info("No critical gaps remaining")
        return False

    # Check improvement from previous iteration
    if previous_completeness is not None:
        improvement = gap_result.overall_completeness - previous_completeness
        if improvement < improvement_threshold:
            logger.info(
                f"Improvement ({improvement:.1f}%) below threshold ({improvement_threshold}%)"
            )
            return False

    # Check if we have queries to execute
    if not gap_result.follow_up_queries:
        logger.info("No follow-up queries available")
        return False

    return True


async def execute_deep_research_loop(
    db: Session,
    run_id: int,
    initial_vendors: list[dict],
    llm: Any,  # LLMProvider
    search_providers: list[str],
    scrape_providers: list[str],
    max_iterations: int = 3,
    gap_threshold: float = 0.6,
) -> dict:
    """
    Execute the complete DeepResearch iterative loop.

    This is the main orchestrator for multi-step research:
    1. Analyze gaps in current data
    2. If gaps exist, execute targeted search
    3. Extract new evidence from results
    4. Merge into vendor data
    5. Repeat until complete or max iterations

    Args:
        db: Database session
        run_id: SearchRun ID for tracking
        initial_vendors: Starting vendor data
        llm: LLM provider for extraction
        search_providers: Search providers to use
        scrape_providers: Scrape providers to use
        max_iterations: Maximum iterations
        gap_threshold: Completeness threshold

    Returns:
        Dict with final vendors and iteration history
    """
    from app.services.pipeline.steps.extract import extract_vendors_from_pages
    from app.services.pipeline.steps.gap_analysis import analyze_gaps

    vendors = initial_vendors
    iteration_history = []
    previous_completeness = None

    for iteration in range(1, max_iterations + 1):
        logger.info(f"DeepResearch iteration {iteration}/{max_iterations}")

        # Phase 1: Analyze gaps
        gap_result = await analyze_gaps(
            vendors=vendors,
            llm=llm,
            gap_threshold=gap_threshold,
        )

        # Check if we should continue
        if not should_continue_iteration(
            gap_result=gap_result,
            iteration=iteration,
            previous_completeness=previous_completeness,
        ):
            logger.info("Stopping iteration loop")
            break

        # Phase 2: Execute refined search
        refine_result = await refine_search(
            db=db,
            run_id=run_id,
            gap_result=gap_result,
            iteration=iteration,
            search_providers=search_providers,
            scrape_providers=scrape_providers,
        )

        # Phase 3: Extract new evidence
        if refine_result.scraped_pages:
            new_vendors, new_evidence = await extract_vendors_from_pages(
                llm=llm,
                pages=refine_result.scraped_pages,
                existing_vendors=[v.get("name") for v in vendors],
            )
            refine_result.new_evidence = new_evidence

            # Phase 4: Merge results
            vendors = await merge_iteration_results(
                existing_vendors=vendors,
                new_pages=refine_result.scraped_pages,
                new_evidence=new_evidence,
            )

        # Record iteration
        iteration_history.append({
            "iteration": iteration,
            "completeness_before": previous_completeness,
            "completeness_after": gap_result.overall_completeness,
            "queries": len(refine_result.queries_executed),
            "pages_scraped": len(refine_result.scraped_pages),
            "new_evidence": len(refine_result.new_evidence),
        })

        previous_completeness = gap_result.overall_completeness

    return {
        "vendors": vendors,
        "iterations_completed": len(iteration_history),
        "final_completeness": gap_result.overall_completeness if gap_result else None,
        "iteration_history": iteration_history,
    }
