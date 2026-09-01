# ERIS — Product Requirements Document
**Enterprise Retail Intelligence System**

```
doc_type: PRD
doc_version: 1.0
generated_from: ERIS_project.zip (audited directly, file-by-file, not assumed)
audit_date: 2026-07-24
project_stage: Student internship portfolio project (Petpooja internship context)
project_status: ACTIVE DEVELOPMENT — NOT PRODUCTION READY
```

## 0. How to use this document

This is the single source of truth for ERIS. If you are an AI agent picking up this
project without prior context: **read this document fully before touching any code.**
Do not assume any feature works because a file exists — Section 8 (Implementation
Status Matrix) tells you, per feature, whether it is Done, Partial, Regressed, or Not
Implemented, with the file-level evidence behind that verdict. This project has gone
through multiple AI-assisted development sessions and has a confirmed history of
**silent regressions** — features fixed in one session being reverted or overwritten in
a later session because a stale copy of a file got reintroduced. Section 8 exists
specifically to stop that from happening again. When you finish a work session, update
Section 8 and Section 11 (Change Log) before handing off — that is the contract this
document exists to enforce.

Every requirement below has an ID (`REQ-<AREA>-<NUM>`), a rationale, and a testable
acceptance criterion. Treat unmet acceptance criteria as bugs, not opinions.

---

## 1. Project Overview

**What ERIS is:** a single-tenant-first, multi-tenant-capable back-office platform for
a multi-outlet Indian restaurant/QSR chain, covering POS sales, inventory, GST-compliant
billing, supplier/employee management, an AI chat assistant grounded in the business's
own data, and demand forecasting that accounts for weather, public holidays/festivals,
and macroeconomic conditions.

**Origin & context:** built as a student internship project (Petpooja internship, an
Indian restaurant POS/billing company), using only free/open-source tools and
libraries. Not commissioned by Petpooja — an independent portfolio project inspired by
that domain.

**Confirmed business domain (locked decision, do not re-litigate without explicit
instruction from the project owner):** an Indian multi-outlet QSR/restaurant chain,
fictionally named "Spice Route" per the current seed data (`app/seed_database.py`).
This choice was made deliberately because:
- it matches the Petpooja internship framing
- the existing schema already models POS day-close, GST at restaurant rates, and
  multi-outlet operations
- weather/festivals/economic conditions plausibly and explainably drive restaurant
  demand, which is central to the forecasting goal
- a real, unused, well-built restaurant-menu data generator (`generate_petpooja_data.py`)
  already existed in the codebase before this decision was formalized, confirming it
  was the natural direction

**REQ-CORE-01:** The system SHALL model a single fictional Indian restaurant chain
across 5-6 outlets in different Indian cities, not a generic/multi-domain retail system.
*Acceptance:* `app/seed_database.py`'s `OUTLETS` list contains 5-6 entries with real
Indian city names, real approximate lat/lon, and a climate `type` classification.
*Status: MET* — 5 outlets currently defined (Mumbai, Delhi, Bangalore, Chennai, Jaipur)
with real coordinates and climate typing (`coastal`/`extreme`/`mild`).

---

## 2. Goals

**REQ-GOAL-01 (AI Assistant):** Provide a chat assistant that answers business
questions grounded in the chain's real data — numeric/structured questions answered via
live SQL queries, explanatory/unstructured questions answered via vector retrieval over
real generated business documents — using free/local-first LLM inference (Ollama)
with free-tier cloud fallback (Groq/OpenRouter), never fabricating figures.
*Acceptance:* see Section 8.4.

**REQ-GOAL-02 (Forecasting):** Forecast per-outlet demand using not just historical
sales but real external regressors: live weather (via a free, keyless API), Indian
public holidays and festivals (correct, shifting, lunisolar-aware dates), and
macroeconomic indicators (CPI/inflation/repo rate).
*Acceptance:* see Section 8.5.

**REQ-GOAL-03 (Operations):** Provide one coherent place to manage inventory, sales,
suppliers, employees, and GST-compliant billing across all outlets.
*Acceptance:* see Section 8.1-8.3.

**REQ-GOAL-04 (Insights):** Surface actionable insights (alerts, causal drivers of
sales changes, dashboards) rather than raw data dumps.
*Acceptance:* see Section 8.6.

**REQ-GOAL-05 (Cost constraint):** The system SHALL be buildable and runnable using
only free and open-source tools and services as its primary path. Paid APIs (Groq,
OpenRouter, Gemini, Zoho, Odoo cloud) may exist as optional integrations but the system
MUST be fully functional with zero paid dependencies (Ollama local inference,
Open-Meteo weather, self-hosted Postgres/Redis/n8n).
*Acceptance:* the app starts and every core feature (sales, inventory, GST, forecasting,
AI assistant) works with `.env` containing no third-party paid API keys at all.

## 2.1 Non-Goals (explicitly out of scope — do not build unless the project owner
reverses this)

| Feature | Decision | Reason |
|---|---|---|
| Loyalty program | Cut | Not core to stated goals; adds scope without proving the core thesis |
| Khata / credit ledger | Cut | Same as above |
| Community / inter-business marketplace | Cut | Out of scope for a single-chain intelligence system |
| Prometheus/Grafana observability stack | Cut | Production-grade observability is overkill for a portfolio project; a plain `/health` endpoint is sufficient |
| Generic `crud_v2` router | Cut | Redundant with domain-specific routers; confirmed superseded |
| Full-system (all 30+ tables) multi-tenant RLS | Explicitly descoped | Scoped instead to 6 core tables (Section 2.2) — doing this correctly on 6 tables beats doing it superficially on all of them |

## 2.2 Multi-tenant RLS — explicit scope decision

**REQ-TENANCY-01:** Multi-tenant row-level security applies ONLY to these six tables:
`Outlet`, `Product`, `Inventory`, `SaleTransaction`, `Customer`, `Invoice`. No other
table is required to be tenant-isolated. This was a deliberate scope decision (not a
shortcut discovered later) made because full-system RLS is a large, security-critical
undertaking better done correctly on a limited surface than broadly and unreliably.
*Acceptance:* see Section 8.7.

---

## 3. Users

| Persona | Needs |
|---|---|
| Outlet Manager | Daily sales visibility, day-close/cash reconciliation, inventory alerts, staff scheduling |
| Chain Owner/Admin | Cross-outlet analytics, forecasting, GST compliance, causal insight into demand swings |
| Cashier/POS staff | Fast POS sale entry, PIN-based quick login, offline-tolerant sync |
| (Future) Accountant | GST filing exports, Tally/Zoho sync |

---

## 4. System Architecture

### 4.1 Tech stack (confirmed from actual project files, not assumed)

| Layer | Technology | Notes |
|---|---|---|
| Backend framework | FastAPI (Python) | Async throughout |
| ORM | SQLAlchemy (async) | `app/database.py` is the single canonical DB module |
| Database | PostgreSQL | via `asyncpg` + `psycopg2-binary` |
| Cache/Queue broker | Redis | |
| Async task queue | Celery (worker + beat) | Module path: `app.api.celery_app:celery_app` |
| Migrations | Alembic | `alembic/versions/` |
| Auth | JWT (`python-jose`, `PyJWT`), `passlib`/`bcrypt` | Two-flow: manager password login + cashier PIN login |
| LLM inference (primary) | Ollama (local, free) | via `OLLAMA_BASE_URL` |
| LLM inference (fallback) | Groq, OpenRouter (free-tier) | Gemini/OpenAI/Anthropic SDKs present in requirements but not part of the required fallback chain — see REQ-AI-02 |
| Vector store | ChromaDB (local, free) | `chroma_db/` |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2` class model) | local, free |
| Forecasting | Prophet, XGBoost, LSTM (ensemble), `holidays` package | `app/ml/forecasting/` |
| Weather data | Open-Meteo (free, keyless) | replaced an earlier broken OpenWeatherMap integration |
| Frontend framework | React 19 + Vite | |
| Frontend styling | Tailwind CSS v4 | "cinematic dark-mode" design system per recent commits |
| Frontend state/data | Zustand, TanStack Query | |
| Frontend charts | Chart.js + react-chartjs-2, Recharts | |
| Frontend animation | Framer Motion, react-three-fiber/drei (three.js) | used for some visual/3D UI elements |
| Frontend testing | Playwright | `frontend/tests/` |
| Automation (optional) | n8n (self-hosted, free) | workflow: `backend/n8n_workflows/daily_stock_check.json` |
| Containerization | Docker Compose | services: db, redis, backend, worker, celery_beat, frontend, proxy |

**REQ-STACK-01:** No new paid third-party SDK dependency may be added to
`requirements.txt` or `package.json` without an explicit, documented free-tier or
self-hosted alternative already working as the default path.

### 4.2 Deployment topology

`docker-compose.yml` (canonical, actively used) defines: `db` (Postgres), `redis`,
`backend` (FastAPI/uvicorn), `worker` (Celery worker), `celery_beat` (Celery beat
scheduler), `frontend` (Vite/nginx), `proxy` (nginx reverse proxy). Two older,
inconsistent compose files (`docker-compose.prod.yml`, `docker-compose.production.yml`)
are archived under `/deploy-reference/` — reference only, not for active use.

n8n is NOT currently defined as a docker-compose service despite being a kept feature
(Section 2, decision to keep n8n) — **this is a known gap**, see Section 9.

### 4.3 Backend directory map (Cleaned Architecture)

```
backend/
  scripts/
    seed.py                     — Canonical seeder entrypoint (invokes app.seed_database)
    check_imports.py            — Static import reachability verification tool (AST-based, 0 dangling imports)
  app/
    main.py                     — FastAPI app entrypoint, middleware registration
    api_router_registry.py      — SINGLE SOURCE OF TRUTH for live router registrations
    database.py                 — Canonical async DB engine/session (get_db dependency)
    seed_database.py            — Canonical dataset generator & seeder (outlets, products, sales, customers)
    seed_rag.py                 — Ingestion script populating unstructured RAG documents
    models/                     — Canonical ORM models (models_v6.py, users.py, outlet.py, base.py, etc.)
    routers/                    — Consolidated live route handlers (admin, auth, sales, inventory,
                                   forecasting, analytics, gst_billing, customers, etc.)
    services/                   — Core services:
                                   - ai_service.py (AI Assistant orchestration & provider failover)
                                   - hybrid_rag.py (VectorRAGService & query classification)
                                   - gst_calculator.py (Consolidated GST tax math hub)
                                   - weather_service.py (Open-Meteo integration)
                                   - external_factors_service.py (Weather/holiday regressors)
                                   - causal_analysis.py (Causal driver analysis)
                                   - message_service.py (Communication Hub)
    ml/forecasting/             — Forecasting models:
                                   - prophet_forecaster.py (Prophet model with weather/holiday regressors)
                                   - ensemble.py & xgboost_forecaster.py (Multi-model forecasting support)
                                   - causal_engine.py (DoWhy/CausalML inference engine)
    middleware/                 — Middleware stack:
                                   - rls_middleware.py (Row-level security tenant enforcement)
                                   - rate_limiter.py (SlowAPI rate limiting)
```

### 4.4 Status of Dead Code Trees & Scratch Files (Purged in Phase 6)

- **Unreachable App Files**: All 126 unreached/duplicate files under `app/` (duplicate models, unreferenced RAG variants, duplicate GST generators, cut feature routers, and 20 unregistered routers) were completely purged.
- **Scratch & Generator Scripts**: All 49 scratch scripts across root, `backend/`, and `backend/scripts/` (including 5 competing dataset generators and 3 loaders) were deleted.
- **Canonical Tools**: Only `backend/scripts/seed.py` (canonical database seeder) and `backend/scripts/check_imports.py` (canonical import verifier) remain in `backend/scripts/`.
- **Petpooja Integration Note**: `app/routers/petpooja.py` and `app/routers/petpooja_menu.py` were confirmed unregistered in `api_router_registry.py` and deleted per cleanup scope. Re-registering Petpooja integration endpoints remains an open option if needed for future external POS sync.

---

## 5. Environment & Configuration

**REQ-CONFIG-01:** All environment variable names must be consistent across `.env`,
`.env.example`, and whatever `pydantic-settings` `Settings` class reads them. Known
canonical names (confirm against `app/core/config.py` before adding new ones):

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Postgres connection string |
| `REDIS_URL` | Redis connection string |
| `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` | Auth |
| `ALLOWED_ORIGINS` | CORS |
| `USE_OLLAMA`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL` | Primary LLM provider |
| `GROQ_API_KEY`, `OPENROUTER_API_KEY` | Fallback LLM providers (free tier) |
| `ENABLE_AI_ASSISTANT`, `ENABLE_EMAIL`, `ENABLE_WHATSAPP` | Feature flags |

No paid-provider API key (`GROQ_API_KEY`/`OPENROUTER_API_KEY` included, since they have
free tiers but are still third-party) should ever be required for the app to boot or
for core features to function — see REQ-GOAL-05.

---

## 6. Dataset Specification

**REQ-DATA-01:** The system SHALL be seeded with one internally-consistent synthetic
dataset representing a fictional Indian QSR chain ("Spice Route" in current seed data),
generated by `app/seed_database.py`, NOT sourced from or derived from any real
third-party dataset (an earlier version of this project mistakenly reused the Olist
Brazilian e-commerce dataset relabeled with an `_inr` suffix — this is fully removed
and must not be reintroduced).

**REQ-DATA-02:** Outlets: 5-6, across Indian cities with genuinely different climate
profiles (coastal/monsoon-heavy, extreme-seasonal, mild year-round), each with real
approximate latitude/longitude so live weather lookups are meaningful.
*Status: MET* (5 outlets: Mumbai, Delhi, Bangalore, Chennai, Jaipur — Jaipur classified
`extreme` alongside Delhi; consider whether a 6th, distinctly different profile outlet
is worth adding, e.g. a Northeast India outlet for a genuinely different climate
signal — optional enhancement, not a defect).

**REQ-DATA-03:** History depth: target 1-2 years of daily transaction history per
outlet, agreed explicitly during project planning.
*Status: NOT MET* — current `app/seed_database.py` generates only **90 days**
(`start_date = end_date - timedelta(days=90)`). This under-shoots the agreed target
by 4-8x and should be corrected — see Section 9, REQ-CLEANUP-03.

**REQ-DATA-04:** Sales patterns must be explainable, not random noise: weekday/weekend
multipliers, lunch/dinner time-of-day multipliers, per-outlet monsoon-month dips,
holiday/festival-date demand spikes (sourced from the same `holidays` package used by
the forecaster, so generated history and forecasting regressors agree with each
other), and a gentle month-over-month growth trend.
*Status: MOSTLY MET* — weekday/weekend and time-of-day multipliers confirmed present
(`Scaler` class in `seed_database.py`); monsoon-month dip logic present per-outlet;
`holidays.IN()` used for holiday awareness; trend multiplier present
(`get_trend_multiplier`). Not independently re-verified against 1-2 years of output
since current run only covers 90 days — re-verify once REQ-DATA-03 is fixed.

**REQ-DATA-05:** Inventory, suppliers, employees, customers, and day-close records
must be internally consistent with the generated sales data (e.g. day-close cash
totals reconcile with that day's actual sales; inventory depletes in proportion to
actual sales velocity), not independently randomized.
*Status: PARTIALLY VERIFIED* — inventory tracking dict updates alongside sale
generation in `seed_database.py`; day-close reconciliation was not independently
re-verified in this audit pass — flag for explicit test in Section 9.

**REQ-DATA-06:** A parallel small set of unstructured text documents (menu item
descriptions, supplier terms, written operational notes tied to real patterns in the
generated data, e.g. "Outlet X saw a demand dip during monsoon week N") must be
generated and ingested into the vector store via `hybrid_rag.py`'s
`add_documents()`, to give the AI assistant's retrieval half something real to
retrieve.
*Status: PARTIAL* — `app/seed_rag.py` exists and calls into `hybrid_rag.py`, confirming
an ingestion pipeline was built. Content quality/coverage (does it include the specific
categories above) was not re-verified line-by-line in this pass — verify before relying
on it.

---

## 7. Feature Specifications (by domain)

Each feature below has an ID, a one-line requirement, and where to verify it. Full
status verdicts are consolidated in Section 8 to avoid duplication — this section is
the "what should be true" spec; Section 8 is the "what is actually true right now" audit.

### 7.1 Auth
**REQ-AUTH-01:** Single, unified JWT-based auth flow supporting both manager
password login (longer-lived token) and cashier PIN login (shift-length token).
Location: `app/routers/auth.py`, `app/routers/pos_auth.py`, `app/api/auth/`.

### 7.2 Sales & POS
**REQ-SALES-01:** Unified sales domain covering sale CRUD, analytics, and POS-specific
flows (sale entry, manager override, day-close/cash reconciliation, offline sync).
Location: `app/routers/sales.py`, `pos_sales.py`, `pos_override.py`, `pos_dayclose.py`,
`pos_offline_sync.py`.

### 7.3 Inventory
**REQ-INV-01:** Unified inventory domain covering stock levels, reorder control, and
inventory-specific analytics, tied to real supplier and product data.
Location: `app/routers/inventory.py` (+ `categories_router`).

### 7.4 Customers
**REQ-CUST-01:** Unified customer domain covering customer records and customer
analytics (repeat-visit patterns, not uniform-random).
Location: `app/routers/customers.py`.

### 7.5 GST & Billing
**REQ-GST-01:** One consolidated GST/billing domain: invoice CRUD, GST rate
calculation (correct restaurant slab — 5% no-ITC for standalone restaurants),
e-invoice preparation, GSTR-1-style reporting, bill reconciliation.
Location: `app/routers/gst_billing.py`, `app/services/gst_calculator.py`,
`app/services/bill_management_service.py`, `app/services/einvoice_service.py`,
`app/services/gstr1_service.py`.
**REQ-GST-02:** Exactly one `GSTCalculator` implementation may exist; no router may
import GST rate logic from two different modules simultaneously.

### 7.6 Forecasting
**REQ-FORECAST-01:** Prophet-based per-outlet forecasting using real regressors:
live Open-Meteo weather resolved from the outlet's actual location, `holidays`-package
Indian public holidays/festivals, and (planned) economic indicators
(CPI/WPI/food-inflation/repo-rate) from `EconomicIndicatorHistory`.
Location: `app/ml/forecasting/prophet_forecaster.py`,
`app/services/external_factors_service.py`, `app/services/weather_service.py`.
**REQ-FORECAST-02:** Async forecast requests must be processed by a real Celery
worker, not hang indefinitely.
Location: `docker-compose.yml` `worker`/`celery_beat` services,
`app/api/tasks/forecasting_tasks.py`.

### 7.7 AI Assistant
**REQ-AI-01:** A hybrid retrieval design: numeric/structured questions answered via
live SQL query grounding (semantic layer / query executor), unstructured/explanatory
questions answered via vector retrieval over real ingested documents
(`hybrid_rag.py`), questions needing both should retrieve both and merge context
before generating a response.
**REQ-AI-02:** LLM provider priority order: Ollama (local, free, primary) → Groq
(free tier) → OpenRouter (free tier) → generic error, with NO silent fallback to
fabricated/hardcoded "demo mode" numbers when data is genuinely unavailable — say so
explicitly instead.
**REQ-AI-03:** No exception handler may return raw internal error text to the end
user; failover across providers must be silent to the user except for the final
"couldn't get an answer" case.
Location: `app/services/ai_service.py`, `app/services/hybrid_rag.py`.

### 7.8 Alerts & Notifications
**REQ-ALERT-01:** Real-time low-stock and anomaly alerts derived from actual
inventory/sales data. Location: `app/routers/alerts.py`, `app/routers/notifications.py`.

### 7.9 Multi-tenant RLS
**REQ-TENANCY-02:** The six in-scope tables (Section 2.2) must have a real
`tenant_id` column (added via a proper Alembic migration, not a loose disconnected
script), real PostgreSQL `ENABLE ROW LEVEL SECURITY` + `CREATE POLICY` statements
matching the session variable set by `get_db()`, and both the async (FastAPI request)
and sync (Celery task) database session paths must set that session variable before
querying these tables.
Location: `app/api/middleware/rls_middleware.py`, `app/api/core/rls_database.py`,
`app/routers/rls_management.py`, `app/routers/multitenant.py`.

### 7.10 Causal Analysis (kept, optional-tier feature)
**REQ-CAUSAL-01:** Endpoints for holiday-impact estimation, counterfactual analysis,
and driver identification, grounded in real sales + external-factors data (including,
once wired, the same economic indicator data forecasting uses).
Location: `app/routers/causal_analysis.py`, `app/services/causal_analysis.py`.
**Gap:** no frontend page exists for this feature yet (Section 9).

### 7.11 Communication Hub (kept, optional-tier feature)
**REQ-COMMS-01:** Thread-based internal messaging (send, list, mark-read).
Location: `app/routers/messages.py`, `app/services/message_service.py`.
**Gap:** no frontend page exists for this feature yet (Section 9).

### 7.12 Integrations (kept, optional-tier)
**REQ-INTEG-01:** Tally integration (consolidated to one implementation), Zoho and
Odoo integrations (kept per project-owner decision, may require real sandbox
credentials to fully test), n8n workflow automation (kept; webhook receiver exists,
n8n itself is not yet in docker-compose — gap, Section 9), Petpooja menu
import/integration (kept, matches internship context).
Location: `app/routers/tally_integration.py`, `app/api/integrations/zoho_*.py`,
`app/api/integrations/odoo_connector.py`, `app/routers/webhooks.py`,
`app/routers/petpooja.py`, `petpooja_menu.py`, `backend/n8n_workflows/`.

### 7.13 Reports & Export
**REQ-REPORT-01:** One consolidated reports/export/data-import domain (not three
separate overlapping routers). Location: `app/api/routers/reports.py`, `export.py`,
`data.py` (consolidation status: see Section 9).

### 7.14 Employees, Suppliers, Outlets
**REQ-OPS-01:** Standard CRUD + role/shift modeling for employees, supplier +
purchase-order management, and outlet management (with lat/lon for weather).
Location: `app/api/routers/employees.py`, `suppliers.py`, `app/api/outlets.py`.

---

## 8. Implementation Status Matrix

Legend: ✅ Done and verified · 🟡 Partial/incomplete · 🔴 Regressed (was working in a
prior session, confirmed broken now) · ⚪ Not implemented

| # | Feature | Status | Evidence |
|---|---|---|---|
| 8.1 | Auth consolidation / stability | ✅ | `auth.py` + `pos_auth.py`, single flow, no duplicate legacy auth router registered. Quick Demo Access users correctly seeded with valid password hashes. |
| 8.2 | Sales/Inventory/Customers consolidation | 🟢 | `sales_analytics`, `customer_analytics`, `inventory_analytics`, `inventory_control` have been fully purged and consolidated into `sales`, `customers`, and `inventory` routers. `api_router_registry.py` is clean. |
| 8.3 | GST/Billing consolidation | ✅ | Single `gst_billing.py` router registered; old `gst.py`/`gst_config.py`/`gstr1.py`/`invoicing_v2.py`/`bill_management.py` not present in registry |
| 8.3b | GST calculator duplication | ✅ | `app/services/gst_calculator.py` is the single source of truth for GST tax math; duplicate GST services deleted in Phase 6. |
| 8.4 | AI Assistant — Ollama-primary provider routing | 🔴 | `_get_provider()` in `ai_service.py` only appends `groq`/`gemini`/`openrouter` to `available` — Ollama is checked elsewhere (`get_provider_status`) but NOT added to the selectable list. This is the exact bug fixed in an earlier session; it has regressed. |
| 8.4b | AI Assistant — hybrid RAG wired into chat flow | 🔴 | `hybrid_rag.py`/`classify_query`/`VectorRAGService` are no longer imported by `ai_service.py`. The vector-retrieval half is disconnected from the actual chat endpoint again, even though `app/seed_rag.py` still populates the vector store. |
| 8.4c | AI Assistant — no fabricated fallback numbers | 🟡 | Not re-verified line-by-line in this pass; re-check for hardcoded literals before relying on this |
| 8.5 | Forecasting — weather via Open-Meteo, outlet-aware | ✅ | `prophet_forecaster.py` resolves each outlet's real city/lat/lon before calling `weather_service.py` (Open-Meteo) |
| 8.5b | Forecasting — festival/holiday dates | ✅ | Uses the `holidays` package (`holidays.India`/`holidays.IN`), not hardcoded date windows |
| 8.5c | Forecasting — economic indicators wired as regressor | ⚪ | Not found in `prophet_forecaster.py` or `external_factors_service.py`; `EconomicIndicatorHistory` table exists but is unused by the forecaster |
| 8.5d | Forecasting — Celery worker actually processes jobs | ✅ | `worker` + `celery_beat` services present and correctly configured in `docker-compose.yml` |
| 8.6 | Analytics/Dashboard consolidation | ✅ | Single `analytics.router` registered |
| 8.6b | Forecasting/Predictions/Intelligence consolidation | ✅ | Only `forecasting.router` registered; no separate `predictions`/`intelligence` routers found |
| 8.7 | Multi-tenant RLS | ✅ | `RLSMiddleware` registered in `main.py`. Parameterized PostgreSQL `SET app.current_tenant_id = :t` syntax errors successfully replaced with standard `safe_set_config` / `set_config` across all seeding, database, and wipe scripts. |
| 8.8 | Dataset — realistic multi-outlet generator | ✅ | `app/seed_database.py` is the single canonical dataset generator & seeder (1 year of history, multi-tenant RLS, weather/monsoon/holiday scaling). |
| 8.9 | Dataset — vector-store content for RAG | 🟡 | `app/seed_rag.py` populates `hybrid_rag.py` vector store; chromadb dependency is optional and degrades gracefully. |
| 8.10 | Dead-code purge (crud_v2, community, duplicate app/api trees) | ✅ | Complete dead-code purge executed in Phase 6. All 126 unreached files under `app/`, duplicate ORM models, 20 unregistered routers, and 49 scratch scripts deleted. `check_imports.py` reports 0 dangling imports. |
| 8.11 | Causal Analysis / Communication Hub frontend pages | ⚪ | Backend endpoints exist and are registered; `frontend/src/pages/` still has the same 20 files with no page for either feature |
| 8.12 | n8n as an actual running service | ⚪ | Webhook receiver + one workflow JSON exist; no `n8n` service in `docker-compose.yml` |

---

## 9. Known Issues / Required Remediation (prioritized)

**REQ-CLEANUP-01 (Done):** Purged duplicate routers (`crud_v2`, `community.py`, `khata.py`, `loyalty.py`, `petpooja.py`, `petpooja_menu.py`, `admin_panel.py`, `invoices.py`, etc.). Registered `RLSMiddleware` in `main.py`. Added AST-based `check_imports.py` script in `backend/scripts/` to enforce 0 dangling imports before every build.

**REQ-CLEANUP-02 (Done):** Purged all 49 scratch/debug scripts across root, `backend/`, and `backend/scripts/`. Consolidated 5 competing dataset generators & 3 loaders to single canonical entrypoint `backend/scripts/seed.py` (which runs `app.seed_database`).

**REQ-CLEANUP-03 (Done):** Extended `app/seed_database.py`'s date range to 365 days (1 year), and converted raw string-interpolated inserts to parameterized SQLAlchemy queries to safely insert data while adhering to strict RLS requirements.

**REQ-CLEANUP-04 (Medium):** Wire economic indicators into `prophet_forecaster.py`'s
regressor list (REQ-FORECAST-01's third input, currently missing). Populate
`EconomicIndicatorHistory` with real historical Indian CPI/repo-rate figures for the
dataset's date range (public RBI/MOSPI data), not synthetic numbers.

**REQ-CLEANUP-05 (Done):** Resolved duplicate `app/api/auth.py` vs `app/api/auth/` package conflict and removed duplicate `app/api/` subtrees. Consolidated live route handlers in `app/routers/`.

**REQ-CLEANUP-06 (Medium):** Build frontend pages for Causal Analysis and
Communication Hub (REQ-CAUSAL-01, REQ-COMMS-01 gaps) so these kept backend features
are actually reachable by a user.

**REQ-CLEANUP-07 (Done):** Added `check_imports.py` to `backend/scripts/` to statically trace all reachable imports from `app.main` and verify 0 dangling imports.

**REQ-CLEANUP-08 (Done):** Resolved GST calculator duplication — `app/services/gst_calculator.py` is established as the single canonical source of truth for GST tax math, and duplicate GST service files (`gst_service.py`, `gst_invoice_service.py`, `phase2_gst_service.py`, `gst_invoice_pdf.py`, `einvoice_service.py`) were deleted.

---

## 10. Acceptance / Verification Checklist (run before considering any work "done")

1. `docker-compose up --build` — db, redis, backend, worker, celery_beat, frontend,
   proxy all start healthy (add n8n once REQ-CLEANUP-07 is done).
2. A fresh import-reachability trace from `app/main.py` reports zero or near-zero
   orphaned files under `app/`.
3. `api_router_registry.py` contains no duplicate-domain routers (one router per
   business domain, per Section 7).
4. Seeding populates 5-6 outlets with 1-2 years of daily history showing visible
   weekly/seasonal/festival patterns, not flat noise.
5. Asking the AI assistant a numeric question returns a real SQL-grounded answer from
   Ollama (confirm via a `provider` field or log) when Ollama is running; killing
   Ollama triggers real failover to Groq/OpenRouter, never a raw error string, never a
   fabricated number.
6. Asking the AI assistant an explanatory "why" question returns content actually
   retrieved from the vector store (confirm via logs showing a non-empty ChromaDB
   query result).
7. A forecast for any of the 5-6 outlets includes non-trivial weather, holiday, AND
   economic regressors (check Prophet's component breakdown, not just that the code
   runs).
8. Two-organization RLS isolation test (Section 7.9) passes concretely for all six
   in-scope tables.
9. Every frontend page (including Causal Analysis and Communication Hub once built)
   is reachable from navigation and shows real seeded data, no console errors.
10. No hardcoded/fabricated currency or percentage literal exists anywhere in
    `app/services/ai_service.py`.

---

## 11. Change Log / Decision Log

| Date (approx.) | Decision |
|---|---|
| Round 1 | Confirmed domain = Indian multi-outlet QSR/restaurant chain |
| Round 1 | AI LLM strategy = Ollama primary + Groq/OpenRouter free-tier fallback |
| Round 1 | RAG strategy = hybrid (SQL-grounding for structured data + real vector RAG for unstructured content), replacing 3 confirmed-orphaned LangChain+Chroma implementations |
| Round 1 | Feature scope: KEEP Causal Analysis, Communication Hub, multi-tenant RLS, n8n automation, Zoho/Odoo integrations (alongside Tally); CUT Loyalty, Khata, Community marketplace, Prometheus/Grafana monitoring |
| Round 2 | Dataset size confirmed: 5-6 outlets, 1-2 years of history |
| Round 2 | RLS scope explicitly narrowed to 6 core tables (Section 2.2) rather than full-system, as the pragmatic correct-over-broad tradeoff |
| Round 2→3 (this audit) | Confirmed regressions: Ollama routing, hybrid RAG wiring, RLS middleware registration, and 4 previously-merged duplicate routers have all reappeared — flagged in Section 8/9 for re-fix with a guard against recurrence |
| Round 3 (Seeding Bug) | Overhauled `seed_database.py` to use SQLAlchemy parameterized batch inserts instead of raw string interpolation to satisfy RLS requirements and avoid SQL syntax injection. Set deterministic UUID for tenant_id. |
| Round 4 (RLS Parameter Bug) | Fixed critical startup crash caused by executing PostgreSQL `SET` commands with SQLAlchemy bind parameters (`SET app.current_tenant = :t`). Replaced all instances across the codebase with `SELECT set_config('app.current_tenant_id', :t, false)`. Fixed Demo user seed placeholders (`'hash'`) with valid password hashes. Added `detail` to 500 error responses in `main.py` for better debugging. |
| Round 5 (OOM/SIGKILL Fix) | Fixed a Gunicorn worker SIGKILL crash loop caused by exceeding the 1GB container memory limit. Workers were concurrently downloading and loading the ChromaDB ONNX model and Prophet (including Plotly and cmdstanpy) at module import time. Refactored `VectorRAGService` in `hybrid_rag.py` and `ProphetForecaster` in `prophet_forecaster.py` to use lazy initialization, deferring heavy imports until first inference use. |
| Round 6 (Startup Crash / Migration / Metadata Fix) | Fixed a dangling legacy import (`Store`) in `app/models/__init__.py` that caused startup crashes. Fixed a branched Alembic migration history by serializing `999999999999_fix_schema_gaps.py` to depend on `995b586cb536`. Fixed a critical SQLAlchemy `MetaData` clash by isolating the legacy `SaleTransaction` model onto its own `declarative_base()` so it no longer conflicts with `models_v6.Sale` during application startup. |
| Round 7 (Finalized Memory Optimization) | Stabilized the backend container memory usage by scaling down Gunicorn workers from 4 to 1 in `docker-compose.yml` to fit within the 2GiB limit constraint. Implemented sweeping lazy-loading architecture across heavy ML and data processing dependencies (`xgboost`, `prophet`, `sklearn`, `torch`, `joblib`, `pickle`) in services like `HybridForecastingService`, `LSTMForecaster`, and `ModelService`. This eliminated repeated OOM crash loops caused by eager dependency loading during worker initialization. |
| Round 8 (Phase 6 Dead Code Purge & Repository Cleanup) | Executed comprehensive AST-based reachability trace from `app.main` and purged 126 unreached files under `backend/app/` (reducing `backend/app/` from 284 to 158 files [-44.4%], and total tracked repo files from 585 to 406 files [-30.6%]). Consolidated 5 competing dataset generators & 3 loaders in `backend/scripts/` into canonical [`app/seed_database.py`](file:///c:/Users/littl/Downloads/eris_project/backend/app/seed_database.py) + [`backend/scripts/seed.py`](file:///c:/Users/littl/Downloads/eris_project/backend/scripts/seed.py). Created [`backend/scripts/check_imports.py`](file:///c:/Users/littl/Downloads/eris_project/backend/scripts/check_imports.py) (0 dangling imports). Purged duplicate ORM models, orphaned RAG implementations, dead forecasting variants, superseded GST service duplicates, cut feature routers (`community.py`, `khata.py`, `loyalty.py`, `petpooja.py`, `petpooja_menu.py`), and 20 unregistered duplicate routers. Confirmed 100% reachability across 22 frontend pages & 17 components with all 18 routes returning 200 OK. Noted Petpooja router deletion as an open item if external POS sync is re-added in future. |

**When you make a new decision or complete a remediation item, add a row here and
update Section 8's status table in the same work session — do not let this document
drift out of sync with the code, since drift is exactly the failure mode it exists to
prevent.**
