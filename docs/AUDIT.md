# Scope audit

This document compares the agreed product scope (*retail intelligence and decision-support platform for one
organization with five configurable outlets*) with what is implemented. For each item it says where to find
the work and how it is verified. Deviations from the recommended stack are listed with their reasons.

Verification shorthand:

- **T**: pytest API tests (`api/tests`, 117 tests, SQLite and PostgreSQL).
- **E**: Playwright end-to-end tests (`e2e/`).
- **Ev**: evaluation scripts and reports.

## Organisation and access

| Requirement | Status | Where | Verified |
|---|---|---|---|
| One organisation, `organization_id` kept for modelling | Done | `models.Organization`, `Outlet.organization_id` | T |
| 5 outlets by default, configurable up to 7 | Done | `SEED_OUTLETS`, `MAX_OUTLETS = 7`, API returns 400 beyond 7, UI disables "Add outlet" | T `test_outlet_cap` |
| No multi-tenant RLS; outlet access enforced in the application | Done | `security.scoped_outlet_ids`, `ensure_outlet_access` on every outlet-scoped endpoint, assistant and reports | T, E |
| Roles admin / manager / viewer | Done, plus **staff** (billing only) | `models.ROLES`, `require_admin/manager/writer` | T `test_viewer_*`, E `viewer is read-only` |
| Managers with several outlets | Done | `user_outlets` table, outlet switcher | T, E `area manager…` |
| Login, refresh and session handling | Done: access + rotating refresh tokens, `token_version` revocation, sign out everywhere, lockout after 5 failures | `security.py`, `routers/auth.py`, `web/src/lib/api.js` | T `test_refresh_rotates…`, E `expired access token…` |

## Core features

| Feature | Status | Where |
|---|---|---|
| Dashboard | Done: KPIs vs previous period, trend, 14-day forecast, outlets, categories, alerts | Dashboard page |
| Outlet management | Done: CRUD, GST state, deactivate instead of delete when history exists | Outlets page |
| Sales history and manual entry | Done: filters, bill drawer, stock check, void with stock restore | Sales page |
| CSV sales import | Done (see below) | Data import page |
| Products and inventory | Done: catalogue (HSN, GST), stock per outlet, adjustments, transfers, movement history | Products and Inventory pages |
| Customer analytics | Done: RFM segments, repeat rate, top customers, at-risk list | Customers and Analytics pages |
| Forecasting | Done (see below) | Forecasts page |
| AI assistant | Done (see below) | AI Assistant page |
| Analytics and model comparison | Done | Analytics and Model comparison pages |
| Causal-driver analysis | Done: exact traffic/basket decomposition plus estimated drivers (rainfall labelled as association) | Anomalies & drivers page, `services/drivers.py` |
| Anomaly alerts | Done: robust z-score detector feeds the alerts bell, the Anomalies page and the assistant | `services/anomalies.py`, `services/alerts.py` |
| Reports and CSV/Excel export | Done: 9 reports, preview, CSV and formatted XLSX with an "About this report" sheet | Reports page, `services/reports.py` |
| Settings | Done: organisation (GSTIN, state, time zone, currency), users and roles, profile, system and dataset info, demo reset, clear transactions | Settings page |
| Demo GST invoices | Done (see below) | Invoices page |
| Supporting: suppliers, receiving, stock movements, low-stock recommendations | Done: suppliers, POs with partial receiving, movement log, reorder suggestions → POs, 14-day stockout risk | Suppliers and Inventory pages |
| Audit log for imports, sales and inventory changes | Done: automatic before-flush hook for every business record, one summary entry per import or bulk reset | Audit log page, T `test_audit_log_records_changes` |

**Removed or out of scope (as recommended):** multi-tenant RLS, multiple organisations, Odoo, Zoho, n8n and POS
connectors, communication hub, email and SMS, HR, PWA, IRN and e-invoice, GSTR filing, ERP accounting, API-key
management, and a separate multi-store page. None of these exist in the code.

## Synthetic dataset

All requirements are met: deterministic generation, 5 outlets with different profiles, 61 products in 9
categories, 2 years of bill lines, customers, suppliers, inventory movements and POs, promotions, price
changes, weekday, monthly and annual seasonality, Indian festivals, weather, outlet-specific growth,
substitutions and stockouts, and 26 labelled anomalies.

- **Provenance.** `dataset_info` records the source, generator version, seed, timestamp and period, and every
  synthetic sale references it through `sales.dataset_id`.
- **Configuration.** The seed defaults to 42 and the end date is configurable (`SEED_END_DATE`, `--end-date`).
  The generator only produces information that would be known at forecast time: planned promotions and
  climatological weather. See [DATASET.md](DATASET.md).
- **Invalid-row samples.** These are produced as downloadable sample files with deliberate mistakes rather than
  stored in the database, so they can't pollute analytics.

## CSV import (all 10 items)

| # | Requirement | Implementation |
|---|---|---|
| 1 | Template | `GET /api/imports/templates/{kind}`, plus valid sample files built from real outlets and products |
| 2 | Size and type validation | 15 MB / 50,000 rows; CSV, TXT or TSV only; Excel files and binary content rejected with guidance |
| 3 | Column-mapping preview | `POST /imports/{kind}/inspect` suggests a mapping (POS aliases such as Bill No, Store, Item Code, Qty); editable in the UI with the first 5 rows shown |
| 4 | Date, amount, product, outlet and quantity validation | Per row, with original values quoted in messages |
| 5 | Duplicate detection | Within the file (same invoice for different outlets or dates, duplicate SKUs or phones) and against the database (existing invoice numbers: skipped with a warning or rejected) |
| 6 | Dry run | Default mode; nothing is written |
| 7 | Summary | Rows, bills, created, updated, errors, skipped duplicates, preview |
| 8 | Error report | `GET /imports/history/{id}/errors.csv` |
| 9 | Atomic import | Single transaction; any error means nothing is saved |
| 10 | History and audit | `import_jobs` table and page, `sales.import_id`, one audit entry per commit |

Verified by T (`test_imports.py`) and E (`import with column mapping…`).

## Forecasting

| Requirement | Status |
|---|---|
| Seasonal naive, exponential smoothing, Prophet, XGBoost, optional ensemble | Done. **LSTM is not implemented.** The scope makes it optional, and the evaluation shows that even XGBoost does not beat Prophet on this data. |
| Outlet, product and category; horizons 7, 14 and 30 | Done; total revenue too; outlet filter for product and category series |
| Features: lags, rolling level, calendar (DOW, month, quarter, weekend), festivals, promotions, price, weather, stockouts | Done (`services/features.py`). The rolling mean is used as the scale ("level") for the lags. Outlet and category are handled by fitting one model per series rather than as features. |
| Rolling CV with MAE, RMSE, WAPE, sMAPE, interval coverage, training and inference time | Done (`app/evaluation.py`, two back-test folds per forecast in production) |
| Persist each run with data range, features, parameters, metrics, selected model, version and timestamp | Done (`forecast_runs`, `forecast_results`); scoped by outlet |
| Model Comparison page explaining the selection | Done |
| Honest errors, no fabricated predictions | Done. Failures are persisted and shown; there are no random fallbacks in the UI. |
| Stock-depletion forecasts and confidence intervals | Done (stock plan, 14-day stockout risk, 80% interval with measured coverage) |

Results are in [FORECAST_EVALUATION.md](FORECAST_EVALUATION.md) and [MODEL_CARD.md](MODEL_CARD.md).

## AI assistant

| Requirement | Status |
|---|---|
| The 7 example questions | All answered. Checked against independent SQL in [ASSISTANT_EVALUATION.md](ASSISTANT_EVALUATION.md): 27/27 intents and 19/19 grounding checks pass. |
| Safe architecture: intent, validated parameters, approved query templates, outlet and date filters, structured result | Done. No generated SQL anywhere. |
| LLM explanation based only on returned data | Ollama is used only to (a) classify unclear questions into the same validated schema, (b) word general advice from a fact summary, and (c) rephrase retrieved documentation, with instructions to use only the given facts or passages |
| Every answer shows data source, filters, execution time, metrics, model version and insufficient-data notes | Done (provenance block, shown under each answer) |
| Works without Ollama (structured mode) | Done. This is the default and is what all the tests and evaluations run on. |
| RAG over real project content only | Done: `docs/knowledge/*.md` plus generated dataset and outlet summaries. No invented policies or suppliers. |

## GST

Every item is done:

- A deterministic synthetic GSTIN, flagged `tax_id_is_demo` and shown with a Demo badge.
- A per-outlet GSTIN for each state.
- CGST and SGST within a state, IGST between states.
- HSN codes on products and invoices.
- A printable PDF with the **DEMO - NOT FOR TAX FILING** watermark.
- Invoice history.
- A GST summary report, labelled "for analysis only".

There is no IRN, filing, e-way bill or any claim of compliance.

## Phase 6 polish

| Item | Status |
|---|---|
| Playwright end-to-end tests | `e2e/`, 13 scenarios, CI job `e2e` |
| PostgreSQL integration tests | Full suite runs on PostgreSQL 16 (CI job `api-postgres`) |
| Docker Compose | `docker compose up` (SQLite); `--profile postgres` and `--profile ai` (Ollama) |
| One-command demo seed | Automatic on first start, or `python -m app.seed` |
| Screenshots and architecture diagram | `docs/images/`, Mermaid diagrams in [ARCHITECTURE.md](ARCHITECTURE.md) |
| README with setup, model design, dataset, metrics, limitations and credentials | [README.md](../README.md) |
| Notebook | `notebooks/forecast_evaluation.ipynb` (executed) |
| Model card and AI grounding evaluation | [MODEL_CARD.md](MODEL_CARD.md), [ASSISTANT_EVALUATION.md](ASSISTANT_EVALUATION.md) |
| Resume summary | [PORTFOLIO_SUMMARY.md](PORTFOLIO_SUMMARY.md) |

## Deliberate deviations from the recommended stack

| Recommended | Used | Why |
|---|---|---|
| Async SQLAlchemy | Sync SQLAlchemy 2 in FastAPI's thread pool | The analytics workloads are CPU-bound pandas and model code, so async I/O would not speed them up. Sync sessions keep transactions (atomic imports, audit hook) simple, and the codebase is consistent. |
| PostgreSQL as the primary database | SQLite by default, PostgreSQL fully supported and tested | Zero-setup demo for reviewers. One flag (`--profile postgres`) switches to PostgreSQL, which runs the same Alembic migration and test suite. |
| Valkey + Celery for background training | In-process background threads (demo generation, evaluation) with status endpoints; forecasts are cached by data version | A single container is enough for a one-organisation demo, and long jobs are rare. Celery and Valkey would add two services without changing the results. |
| Chroma / embeddings for RAG | TF-IDF retrieval in pure Python | The corpus is about 50 sections of project docs. TF-IDF is deterministic, needs no model download, and has no embedding-model licence to check. The quality is adequate (all documentation checks pass). |
| Plotly or Recharts | Recharts | As recommended. |

## Known limitations

- All accuracy figures come from synthetic data.
- XGBoost underperforms the baseline on aggregate series, and this is reported as such.
- The rule-based parser covers the documented question types. Other phrasings fall back to help text, or to
  Ollama when it is installed.
- Background jobs run in the API process, so they are lost if the process restarts, and the job is restarted
  manually.
- The Ollama runtime is MIT-licensed. The licence of the chosen model (for example Llama 3.2) must be checked
  separately before redistribution.
