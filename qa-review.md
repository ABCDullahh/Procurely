# QA Audit Report - DeepResearch Implementation

**Date**: January 11, 2026
**Auditor**: Senior QA Engineer + Technical Auditor
**Status**: CRITICAL ISSUES FOUND

---

## Executive Summary

The DeepResearch-like vendor discovery system has been **partially implemented** (approximately 65-70% complete). While the core backend infrastructure exists, several **critical integration issues** prevent the system from functioning as intended.

### Overall Assessment: FAIL - Critical bugs must be fixed before deployment.

---

## Plan Execution Audit

| Plan Item | Status | Details |
|-----------|--------|---------|
| Bug Fix: Provider Enable/Disable Race Condition | DONE | `api_keys.py:200-214` disables providers on key delete |
| Bug Fix: Tavily API Key Validation | DONE | `providers.py:259-266` validates key before enable |
| Indonesia Query Expansion | DONE | `expand_indonesia.py` fully implemented |
| Gap Analysis Step | DONE | `gap_analysis.py` fully implemented |
| Refine Search Step | DONE | `refine_search.py` fully implemented |
| Shopping Search Step | DONE | `shopping_search.py` fully implemented |
| Quality Assessment Step | DONE | `quality_assessment.py` fully implemented |
| SerpAPI Shopping Provider | DONE | `serpapi_shopping.py` fully implemented |
| Database Migration | DONE | `011_deepresearch_fields.py` creates all columns |
| Model: ProcurementRequest | DONE | locale, country_code, region_bias, research_config |
| Model: SearchRun | DONE | research_iterations, gap_analysis, etc. |
| Model: VendorMetrics | DONE | quality_score, price_score, etc. |
| Model: Vendor | NOT DONE | Missing shopping_data, price_range_* fields |
| Pipeline Runner: DeepResearch method | DONE | `run_deep_research_pipeline()` implemented |
| Pipeline Integration | CRITICAL | `run_deep_research_pipeline()` NEVER CALLED |
| Enhanced Scoring Integration | NOT DONE | Old scoring formula still used |
| VendorMetrics Saving | CRITICAL | New fields not saved to database |
| API: Research Config Endpoints | NOT DONE | Endpoints not created |
| Schema: research.py | NOT DONE | File not created |
| Frontend: NewRequestPage | PARTIAL | Missing locale, region_bias, research_config |
| Frontend: VendorQuickView | NOT DONE | No quality indicators |
| Frontend: VendorProfilePage | NOT DONE | No research depth display |
| Frontend: Admin ApiKeys | PARTIAL | No SerpAPI/research config UI |

---

## Critical Bugs (MUST FIX)

### BUG-001: DeepResearch Pipeline Never Called [CRITICAL]

**Severity**: P0 - BLOCKER
**File**: `backend/app/api/v1/requests.py:32`

**Problem**: The API calls `runner.run_pipeline()` instead of `runner.run_deep_research_pipeline()`. All DeepResearch features are dead code.

**Evidence**:
```python
# Line 32 in requests.py
asyncio.run(runner.run_pipeline())  # Uses OLD pipeline!
```

**Impact**:
- Gap analysis NEVER runs
- Iterative research NEVER runs
- Shopping search NEVER runs
- Quality assessment NEVER runs
- Indonesia focus NEVER applied
- The entire DeepResearch implementation is useless

---

### BUG-002: VendorMetrics New Fields Not Saved [CRITICAL]

**Severity**: P0 - BLOCKER
**File**: `backend/app/services/pipeline/runner.py:1114-1127`

**Problem**: When saving vendors, the new DeepResearch metrics fields are NOT populated.

**Missing Fields**:
- quality_score
- price_score
- completeness_pct
- confidence_pct
- source_diversity
- research_depth
- price_competitiveness

---

### BUG-003: Vendor Model Missing Shopping Fields [HIGH]

**Severity**: P1 - HIGH
**File**: `backend/app/models/vendor.py`

**Missing Fields**:
- shopping_data (JSON)
- price_range_min (Float)
- price_range_max (Float)
- price_last_updated (DateTime)

---

### BUG-004: Enhanced Scoring Not Integrated [HIGH]

**Severity**: P1 - HIGH
**File**: `backend/app/services/pipeline/steps/score.py:126`

**Problem**: Still uses old formula (60% fit + 40% trust). Should use:
- fit_score * 0.35
- trust_score * 0.25
- quality_score * 0.25
- price_score * 0.15

---

## Medium Bugs

### BUG-005: Frontend Missing Indonesia Focus Controls [MEDIUM]

**File**: `frontend/src/pages/NewRequestPage.tsx`

**Missing**:
- Locale dropdown (default: id_ID)
- Country code field
- Region bias toggle
- Max iterations slider
- Gap threshold slider
- Include shopping checkbox

---

### BUG-006: Frontend Missing Quality Indicators [MEDIUM]

**Files**: `VendorQuickView.tsx`, `VendorProfilePage.tsx`

**Missing**:
- Quality score badge (A-F grade)
- Research depth indicator
- Completeness % bar
- Source diversity count
- Pricing data panel

---

## Fix Priority Order

1. **BUG-001**: Make run_deep_research_pipeline() actually called
2. **BUG-002**: Save new VendorMetrics fields to database
3. **BUG-004**: Integrate enhanced scoring formula
4. **BUG-003**: Add Vendor model shopping fields + migration
5. **BUG-005**: Add frontend Indonesia/research controls
6. **BUG-006**: Add frontend quality indicators

---

## Comparison with Gemini/OpenAI DeepResearch

| Feature | Gemini/OpenAI | Procurely (Current) |
|---------|---------------|---------------------|
| Iterative research loops | Yes | Code exists, NEVER RUNS |
| Gap analysis | Yes | Code exists, NEVER RUNS |
| Quality assessment | Yes | Code exists, NEVER RUNS |
| Source diversity | Yes | Code exists, NEVER RUNS |
| Progress visibility | Yes | Works |
| Shopping/Pricing | No | Code exists, NEVER RUNS |

**Verdict**: Procurely has the architecture to match or exceed Gemini/OpenAI, but **none of it runs** due to BUG-001.
