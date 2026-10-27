# Backend

Code is in `api/app/`. FastAPI, SQLAlchemy 2, Alembic. Entry point `main.py`. Configuration in `config.py`.

## Routers (`api/app/routers/`)

Route prefixes and module docstrings, as they are in the code today (`routers/*.py`, 11 routers included in `main.py`).

| Router | Prefix and tag | What it covers |
|---|---|---|
| `auth.py` | `/api`, "auth & users" | Login, refresh, sign-out, users |
| `catalog.py` | `/api`, "products" | Menu items and categories (filtered by kind), dish detail with recipe and portions, ingredient detail, recipe CRUD |
| `common.py` | — (helpers) | Small helpers shared by routers, such as CSV writing |
| `imports.py` | `/api/imports`, "data import" | Import types, templates, samples, inspect (column mapping), dry run, commit, history, error report |
| `insights.py` | `/api`, "insights" | Dashboard, analytics, forecasting, alerts and the AI assistant (module docstring) |
| `inventory.py` | `/api`, "inventory & purchasing" | Ingredient stock per outlet (the `_stocked` guard), counts, wastage, transfers, movements, reorder suggestions, purchase orders |
| `outlets.py` | `/api/outlets`, "outlets" | Outlet CRUD, cap of seven, deactivation |
| `partners.py` | `/api`, "suppliers & customers" | Suppliers and customers (the business's contacts) |
| `records.py` | `/api`, "reports, invoices & audit" | Reports and exports, demo GST invoices, audit log |
| `sales.py` | `/api/sales`, "sales" | Bill list and detail, new bill, void (restores stock), CSV export, covers |
| `settings.py` | `/api/settings`, "settings" | Organisation, users, roles, profile, dataset info, demo reset, clear transactions |

The line that builds these routers is `main.py` line 110 (`app.include_router(r.router)`).

## Services (`api/app/services/`)

### Sales and stock
- **`sales.py`**: `_ingredient_needs(product, qty)` works out what a dish takes from stock, using its recipe. A sale is rejected if an ingredient is sold as a dish. A void reverses the recorded sale movements, so stock returns exactly what was drawn.
  - *Why it is shaped this way:* the recipe is the only source of truth for ingredient use. Storing the draw-down as movements (not as a balance) makes voids and audits exact (D13).
- **`inventory.py`**: stock, counts, wastage, transfers, movement history.
- **`analytics.py`**:
  - `kpis(...)` returns revenue, gross profit, guests, spend per guest, average bill, and food cost % (`food_cost_pct`).
  - `usage_query` and `avg_daily_usage` compute ingredient use per day, per outlet. Reorder, run-out and lost-sales logic all use these, not dish sales.
  - `dish_revenue_by_ingredient` attributes revenue to ingredients, for the "where does food cost go" view.
  - `lost_sales_estimate` was rewritten: it estimates dishes not sold because an ingredient was out.
  - ABC analysis `not_sold` is restricted to menu items. Ingredients are not sold, so counting them as "not sold" was wrong.
- **`forecasting.py`**:
  - `_daily_usage` builds the ingredient usage series used by reorder and run-out risk.
  - `product_stock_plan` reports dish portions: `stock_basis` is `"portions"`, plus `limiting_ingredient` (the ingredient that runs out first). This is the answer to "how many portions can the kitchen still make?"

### Forecasting and insight engines
- **`features.py`**: calendar, lag, promotion, weather and festival features.
- **`holidays.py`**: Indian festivals (Diwali, Navratri, and others) and Valentine's Day.
- **`evaluation.py`** (in `api/app/`): the rolling-origin study (`08`).
- **`anomalies.py`**: robust z-score detection of unusual outlet-days and suspicious bill lines (`08`).
- **`drivers.py`**: exact decomposition of revenue change into bills and average bill, plus estimated drivers (`08`).
- **`alerts.py`**: builds the alerts list (ingredients out or low, overdue POs, unusual days, suspicious bills, festivals) that the bell and the dashboard show.

### Reports, invoices, imports
- **`reports.py`**: nine reports; CSV and XLSX export with an "About this report" sheet.
- **`gst.py`** and **`invoices.py`**: demo GST invoices. Intra-state (CGST+SGST) or inter-state (IGST) by place of supply. Watermarked "DEMO - NOT FOR TAX FILING". Numbering is gap-free and unique per outlet (commit 63d38ea, "airtight numbering").
- **`importer.py`**:
  - Column aliases for POS exports, and channel aliases (`CHANNEL_ALIASES`, so Swiggy and Zomato map to delivery).
  - Restaurant templates for menu and ingredients (with recipe lines), sales, and customers.
  - Handles UTF-16 files, NaN and huge quantities, dates before an outlet opened, and CSV-injection characters.
  - Atomic commit: one transaction, nothing saved on any error.
  - On PostgreSQL, an advisory lock makes duplicate uploads skip cleanly.

### Audit
- **`audit.py`**: a before-flush hook records every change to business records, plus one summary per import or bulk reset. Automatic, so new models are covered (Recipe is tracked).

### Caching and state
- **`response_cache.py`**: cache for list and page responses, invalidated on data change (`06`).
- **`state.py`**: process-wide state, including the forecast worker slots (D7).
- **`clock.py`**: the business clock in the organisation's time zone (616f0cc). Dates such as "today" and "last week" must be computed in the business's time zone, not the server's.
- **`security.py`**: password hashing, tokens, outlet scoping, role checks (`require_admin`, `require_manager`, `require_writer`).

### Assistant (`services/assistant/`)
- **`nlu.py`**: intent matching with weighted patterns, synonyms (restaurant wording), `_resolve_item_kind` (dish or ingredient), and longest-name matching for dishes.
- **`tools.py`** and **`insight_tools.py`**: the fixed query templates each intent runs. `_dish_portions` gives the portions answer. Guests and covers are summarised in sales answers.
- **`engine.py`**: runs the matched template, builds the answer and its provenance, caches it (`07`).
- **`knowledge.py`**: retrieval over `docs/knowledge/` for definition and how-to questions.
- **`llm.py`**: optional phrasing through a local model (Ollama). `LLM_ENABLED` defaults to **true** in `config.py`. When it is false, the client reports itself unavailable and the templates answer alone. Tests and the e2e server set it to false, so they never depend on a model.

### Seed and generator (`api/app/seed/`)
- **`catalog.py`**: Saffron Table: the organisation, five outlets with their taste profiles (`OUTLET_TASTE`), seven suppliers, 38 ingredients, 50 menu items with recipes, the course each item belongs to (`COURSE_OF`), and the rice side dishes (`RICE_SIDES`). See `05`.
- **`generator.py`**: `GENERATOR_VERSION = "4.0.0"`. Deterministic (seed 42). See `05`.
- **`bake.py`**: builds the demo at Docker build time. Steps: generate, demo activity (including wastage), prewarm forecasts, store the model-comparison evaluation (optional, `--no-evaluation`), warm response caches and assistant answers, compact the database. Warms `WARM_URLS` and `WARM_URLS_UNPINNED` (menu lists and the dish picker) and the assistant's suggested questions.
- **`refresh.py`**: keeps an untouched demo current. If the database holds only generated demo sales (nothing typed in by a user), every date is shifted forward by whole weeks, so weekday patterns stay intact. Real data is never modified. This is the opposite of the start-up shifting that caused the slowdown (`06`, D10); it is for a demo that is weeks old, not for every start.

### Evaluation scripts (`api/app/`)
- **`evaluation.py`**: forecast back-test study.
- **`assistant_eval.py`**: 31 cases. Checks that each question maps to the right intent and that each number matches an independent SQL query (`07`).

## Key rules that the code enforces
1. Every outlet-scoped endpoint calls the scope check (D3).
2. Every write needs a writer role (admin or manager; staff for billing only).
3. Ingredients are never sold as dishes.
4. Voids restore exactly what was drawn.
5. Imports are all-or-nothing.
6. Forecast fits are bounded by slots; a busy server answers with 503, never hangs.
7. Dates and "today" use the business time zone.
