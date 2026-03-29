# gap-analysis.md — Product Gaps & Recommended Additions

> Generated: 2025-12-31
> Updated: 2026-01-01 (Bug Sweep V)

---

## Gaps Addressed (Bug Sweep V) — AI Configuration

| Gap | Status | Implementation |
|-----|--------|----------------|
| Admin AI model selection | ✅ Done | GET/PUT /admin/settings/ai-config |
| Procurement LLM config | ✅ Done | llm.procurement.provider/model |
| Copilot LLM config | ✅ Done | llm.copilot.provider/model |
| Web search provider selection | ✅ Done | web_search.provider (SERPER/TAVILY/GEMINI_GROUNDING) |
| No silent fallback | ✅ Done | Actionable error if misconfigured |

---

## Gaps Addressed (Bug Sweep IV)

| Gap | Status | Implementation |
|-----|--------|----------------|
| Search Strategy UI Toggle | ✅ Backend done | TAVILY added, pipeline reads setting |
| Request cancellation | ✅ Backend done | POST /runs/{id}/cancel endpoint |
| Status display bug | ✅ Fixed | Dashboard uses run status |

---

## 1) Product Snapshot (What Exists Today)

### Key Features (Verified in Code)

| Category | Features |
|----------|----------|
| **Authentication** | JWT login/refresh, RBAC (admin/member), session management |
| **Procurement Requests** | Create/edit/delete, draft & submit workflow |
| **Vendor Discovery Pipeline** | 7-step automated search (expand→search→fetch→extract→dedup→score→logo) |
| **Vendor Data** | Profile, evidence tracking, source URLs, logo assets, fit/trust scores |
| **Shortlists** | CRUD, add/remove vendors, drag reorder, notes, side-by-side compare |
| **Reports** | HTML generation, full-page view, download, delete |
| **Copilot AI** | Ask questions, generate insights, execute actions (create shortlist) |
| **Admin** | API key management (encrypted), model picker, audit logs, app settings |
| **UI Polish** | Command palette, skeletons, empty states, landing page |

### Key User Roles and Permissions

| Role | Permissions |
|------|-------------|
| **Member** | Own requests, runs, vendors, shortlists, reports, copilot |
| **Admin** | All member permissions + API keys + audit logs + settings |

### Integrations Currently Supported

| Integration | Purpose | Status |
|-------------|---------|--------|
| OpenAI | LLM for extraction/chat | ✅ Implemented |
| Google Gemini | LLM fallback | ✅ Implemented |
| Serper.dev | Web search | ✅ Implemented |
| Clearbit | Logo fetching | ✅ Implemented (fallback to favicon) |

---

## 2) Missing or Incomplete Product Features

### 2.1 Procurement Workflow Completeness

| Gap | Current State | Why It Matters | Definition of Done |
|-----|---------------|----------------|-------------------|
| **Request templates** | Every request starts from scratch | Repetitive for similar searches | User can save/load request templates |
| **Request duplication** | No clone functionality | Can't iterate on similar searches | "Duplicate" button creates copy |
| **Request archiving** | Only delete available | Historical data lost | Archive status with filter |
| **Approval workflow** | No multi-user approval | Enterprise teams need sign-off | Submit for approval → approver reviews |
| **Request tagging/categories** | Basic category field only | Hard to organize many requests | Tag system with filtering |

### 2.2 Search Quality Controls

| Gap | Current State | Why It Matters | Definition of Done |
|-----|---------------|----------------|-------------------|
| **Search re-run** | Cannot re-run completed search | New vendors appear over time | "Re-run" button starts fresh pipeline |
| **Incremental search** | Full pipeline each time | Inefficient, loses previous results | Append new results, flag duplicates |
| **Search tuning** | Fixed expand prompts | Results quality varies | User can adjust search depth/breadth |
| **Search strategy UI** | Backend endpoint exists, no UI | Gemini Grounding as alternative | Admin toggle for Serper vs Gemini |
| **Manual URL addition** | Only automated discovery | Known vendor missing from search | "Add vendor by URL" feature |

### 2.3 Vendor Data Quality & Enrichment

| Gap | Current State | Why It Matters | Definition of Done |
|-----|---------------|----------------|-------------------|
| **Vendor editing** | Read-only vendor data | Extraction errors need correction | Inline editing with audit trail |
| **Data refresh** | Snapshot at search time | Vendor info becomes stale | "Refresh" button re-fetches |
| **Enrichment sources** | Only web search | Missing structured data | LinkedIn, Crunchbase integrations |
| **Vendor deduplication UI** | Automatic merge only | User should review merges | Merge suggestion queue |
| **Confidence thresholds** | All confidence levels shown | Low-confidence data mixed in | Filter by confidence, flag uncertain |

### 2.4 Collaboration & Decision-Making

| Gap | Current State | Why It Matters | Definition of Done |
|-----|---------------|----------------|-------------------|
| **Shared shortlists** | Single-user ownership | Teams collaborate on decisions | Share shortlist with view/edit permissions |
| **Comments on vendors** | Only notes in shortlist | Unstructured, not searchable | Threaded comments with @mentions |
| **Scoring weightings** | Fixed algorithm | Different priorities per search | Configurable criteria weights |
| **Voting/ranking** | No team input mechanism | Decisions are opaque | Upvote/downvote on shortlist items |
| **Decision status** | No final outcome tracking | Can't report on results | "Selected", "Rejected", "Pending" status |

### 2.5 Reporting & Export

| Gap | Current State | Why It Matters | Definition of Done |
|-----|---------------|----------------|-------------------|
| **PDF export** | HTML only | PDF more portable | Download as PDF |
| **Report templates** | Single format | Different stakeholders need views | Template selection |
| **Scheduled reports** | Manual generation only | Recurring updates needed | Email schedule configuration |
| **Comparison export** | CSV from compare matrix | Limited format | Include metrics, notes, scores |
| **Shortlist export** | No export | Need offline sharing | Export shortlist as CSV/PDF |

### 2.6 Copilot Capabilities

| Gap | Current State | Why It Matters | Definition of Done |
|-----|---------------|----------------|-------------------|
| **Prompt safety** | No input filtering | Prompt injection possible | Input validation/sanitization |
| **Source grounding** | Citations shown but not verified | Users may not trust AI | Highlight extractable from source |
| **Action confirmation** | Some actions immediate | Destructive actions risky | Confirmation step for changes |
| **Conversation memory** | Per-run localStorage | No cross-session learning | Backend persistence option |
| **Custom actions** | Fixed action set | Users want workflow flexibility | Plugin/action configuration |

### 2.7 Admin & Governance

| Gap | Current State | Why It Matters | Definition of Done |
|-----|---------------|----------------|-------------------|
| **User management** | No UI for user CRUD | Admins can't add users | Admin panel for users |
| **Role customization** | admin/member only | Finer permissions needed | Custom roles with permissions |
| **Feature flags** | None | Can't disable features | Admin toggle for features |
| **Usage quotas** | No limits | Cost control for LLM usage | Quota per user/organization |
| **Multi-tenancy** | Single tenant | SaaS deployment | Organization isolation |

### 2.8 Observability

| Gap | Current State | Why It Matters | Definition of Done |
|-----|---------------|----------------|-------------------|
| **Structured logging** | Print statements | Hard to aggregate/search | JSON structured logs |
| **Metrics collection** | None | Can't measure performance | Prometheus/StatsD integration |
| **Tracing** | None | Hard to debug distributed calls | OpenTelemetry traces |
| **Error tracking** | Logs only | No alerting on errors | Sentry/Rollbar integration |
| **Pipeline metrics** | progress_pct only | No step-level timing | Step duration, success rate tracking |

### 2.9 Reliability & Resilience

| Gap | Current State | Why It Matters | Definition of Done |
|-----|---------------|----------------|-------------------|
| **Retry logic** | None in API client | Transient failures not recovered | Exponential backoff retry |
| **Circuit breaker** | None | Provider outage cascades | Circuit breaker pattern |
| **Background job recovery** | Run stuck if worker dies | Lost work, stuck status | Job persistence + restart |
| **Graceful degradation** | Full failure on provider error | No partial results | Return what succeeded |
| **Health check depth** | `/health` returns OK | Doesn't check DB/providers | Deep health checks |

### 2.10 UX Polish

| Gap | Current State | Why It Matters | Definition of Done |
|-----|---------------|----------------|-------------------|
| **Dark mode** | Not implemented | User preference | Theme toggle + persistence |
| **Keyboard shortcuts** | Command palette only | Power users want shortcuts | k → shortcuts reference |
| **Mobile responsive** | Partial | Users on tablet/phone | Full responsive UX |
| **Accessibility (a11y)** | Basic | Compliance, usability | WCAG 2.1 AA compliance |
| **Onboarding tour** | None | New users confused | Guided product tour |
| **Bulk operations** | One-at-a-time | Slow for many items | Bulk select + action |

---

## 3) "Must-Have" vs "Nice-to-Have" Roadmap

### Must-Have (Next 1–2 Iterations)

| Priority | Feature | Reason |
|----------|---------|--------|
| P0 | **E2E tests (Playwright)** | Prevent regressions, enable CI |
| P0 | **Background job recovery** | Stuck runs currently unrecoverable |
| P0 | **Windows asyncio fix** | Users on Windows experience hangs |
| P1 | **Search re-run** | Core user need: iterate on results |
| P1 | **User management UI** | Admins can't onboard users |
| P1 | **Error tracking (Sentry)** | Production visibility |
| P1 | **Retry logic in API client** | Resilience for transient errors |

### Should-Have (Next 1–2 Months)

| Priority | Feature | Reason |
|----------|---------|--------|
| P2 | **Dark mode** | Common user request |
| P2 | **Search strategy UI toggle** | Backend exists, needs UI |
| P2 | **Vendor editing** | Data correction common need |
| P2 | **Shared shortlists** | Team collaboration |
| P2 | **PDF export** | Business stakeholder preference |
| P2 | **Request templates** | Efficiency for repeat searches |

### Nice-to-Have (Later)

| Priority | Feature | Reason |
|----------|---------|--------|
| P3 | Approval workflows | Enterprise feature |
| P3 | Multi-tenancy | SaaS deployment |
| P3 | Custom roles | Enterprise RBAC |
| P3 | LinkedIn/Crunchbase enrichment | Enhanced data quality |
| P3 | Scheduled reports | Automation |
| P3 | Onboarding tour | New user experience |

---

## 4) Recommended System-Level Improvements (Non-Feature)

### 4.1 Testing Strategy Improvements

| Improvement | Current State | Recommendation | Acceptance Criteria |
|-------------|---------------|----------------|---------------------|
| Pipeline unit tests | None | Add tests for each step | Each step has ≥3 tests |
| Integration tests | Auth only | Add request→run flow | Submit→complete tested |
| E2E tests | None | Add Playwright suite | Critical journeys covered |
| Mutation testing | None | Optional: eval test quality | Mutation score ≥80% |

### 4.2 Error Handling Standardization

| Improvement | Current State | Recommendation | Acceptance Criteria |
|-------------|---------------|----------------|---------------------|
| Error response format | Varies | Standard `{error, code, detail}` | All endpoints use format |
| Error logging | Inconsistent | Structured log with context | Errors include request ID |
| Client error handling | Per-component | Centralized error handler | Single source of truth |
| User-friendly messages | Technical sometimes | Map codes to friendly text | All errors readable |

### 4.3 Performance Improvements

| Improvement | Current State | Recommendation | Acceptance Criteria |
|-------------|---------------|----------------|---------------------|
| Query optimization | Unknown | Add query logging, analyze | No N+1 queries |
| Response compression | Likely default | Verify gzip enabled | Responses compressed |
| Bundle splitting | React.lazy used | Analyze bundle size | No chunk >200KB |
| Database indexing | Some indexes | Audit query patterns | Key queries use indexes |

### 4.4 Security Hardening

| Improvement | Current State | Recommendation | Acceptance Criteria |
|-------------|---------------|----------------|---------------------|
| Rate limiting | None verified | Add per-IP limits | Login ≤5/min, API ≤100/min |
| Token rotation | Fixed refresh | Consider rotation policy | Refresh token single-use |
| Input validation | Pydantic | Audit for edge cases | All inputs validated |
| Dependency audit | Unknown | Add `npm audit`, `pip-audit` | No high vulnerabilities |

---

## 5) Open Questions & Unknowns

### Cannot Verify from Code

| Question | Why Unknown | Evidence Needed |
|----------|-------------|-----------------|
| Actual LLM response quality | No runtime access | Manual testing with real providers |
| Production database size | Using SQLite in dev | Production metrics |
| Real-world pipeline reliability | Mocked in tests | Production error rates |
| Frontend performance on large datasets | No load testing | Performance profiling |
| Actual token usage/cost | No metering in code | Provider dashboards |

### Architectural Decisions Unclear

| Question | Evidence in Code | Clarification Needed |
|----------|------------------|---------------------|
| Why no WebSocket for real-time? | Polling used everywhere | Intentional or to-be-implemented? |
| PostgreSQL production readiness | SQLite mentioned in README | Production DB recommendation? |
| Multi-worker deployment | Single process assumed | Celery/RQ for background jobs? |
| Secret management | .env files | Vault/KMS for production? |
| Backup/recovery strategy | Not in code | Database backup plan? |

### Product Decisions Needed

| Question | Current Behavior | Decision Point |
|----------|------------------|----------------|
| Max vendors per run? | Unlimited | Should there be a cap for performance? |
| Chat history retention? | localStorage (forever) | Should messages expire? |
| Report HTML size limit? | Unlimited | Could impact performance at scale |
| API key per-user vs shared? | User-owned | Should org-level keys exist? |
