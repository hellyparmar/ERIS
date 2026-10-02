# ERIS: Enterprise Retail Intelligence System

ERIS is an open-source **retail intelligence and decision-support platform** for one organisation running
several outlets (five by default, up to seven). It brings together:

- day-to-day operations: sales, stock, purchasing, customers and demo GST invoices;
- **demand forecasting with model comparison**;
- a **grounded natural-language assistant**;
- **anomaly detection** and **revenue-driver analysis**.

Every number traces back to the data.

> **Synthetic-data project.** ERIS runs on a deterministic, documented synthetic dataset for a fictional
> chain, *Urban Harvest Foods*. It is a portfolio and learning project. It is **not** a production ERP, and it
> is **not** a GST-compliant invoicing system: the GSTINs are synthetic and every invoice is watermarked
> *DEMO - NOT FOR TAX FILING*.

![Dashboard](docs/images/dashboard.png)

## Highlights

| | |
|---|---|
| **Forecasting** | Seasonal naive, Holt-Winters, XGBoost, Prophet (Indian festival calendar plus promotion, price and weather regressors) and an ensemble. Each series is back-tested on two 28-day folds and every run is saved with its data range, features, parameters and metrics. In a rolling-origin study over 25 series the production pipeline scores **17.3% WAPE vs 20.2% for the seasonal-naive baseline** (about 14% lower error). |
| **AI assistant** | Answers questions such as *"Why was Outlet 3 revenue lower this week?"*, *"Which items may go out of stock in the next 14 days?"* and *"What forecast model performed best for beverages?"*. It maps each question to a validated intent template (no generated SQL), respects outlet permissions, and shows its data source, filters, timing, model version and caveats. Definition and how-to questions are answered from the project docs by retrieval. Optional local LLM through Ollama. **Grounding check: 27/27 intents and 19/19 answers match independent SQL.** |
| **Anomalies and drivers** | Robust z-score detection of unusual outlet-days and suspicious bill lines: **precision 0.79, recall 0.73** against the 26 anomalies injected into the data. A "why did revenue change?" analysis splits the change exactly into bills × average bill, then by outlet and category, and estimates the calendar, promotion, stockout and rainfall contributions. |
| **Data pipeline** | A deterministic generator (seed 42): 2 years of bill lines with seasonality, festivals, weather, promotions, price elasticity, substitutions and stockouts, plus full provenance. CSV import with column mapping, a dry run, duplicate handling, an error report, an atomic commit and import history. |
| **Engineering** | FastAPI with SQLAlchemy 2 and Alembic on SQLite or PostgreSQL; React 19. JWT access and refresh tokens, 4 roles with application-level outlet scoping, and an automatic audit log. 88 API tests on SQLite and PostgreSQL, 10 Playwright end-to-end tests, and CI. |

## Screenshots

| AI assistant (with provenance) | Forecasts |
|---|---|
| ![Assistant](docs/images/assistant.png) | ![Forecasts](docs/images/forecasts.png) |
| **Model comparison** | **Why did revenue change?** |
| ![Model comparison](docs/images/model-comparison.png) | ![Drivers](docs/images/drivers.png) |
| **Unusual days vs injected ground truth** | **CSV import with column mapping** |
| ![Anomalies](docs/images/anomalies.png) | ![Import](docs/images/import.png) |
| **Demo GST invoice** | **Reports & export** |
| ![Invoice](docs/images/invoice.png) | ![Reports](docs/images/reports.png) |

<img src="docs/images/mobile-dark.png" alt="Mobile, dark mode" width="260">

## Features

| Area | What you can do |
|---|---|
| Dashboard | KPIs vs the previous period, trend, 14-day forecast, outlet ranking, category mix and alerts (stock, overdue POs, unusual days, suspicious bills, festivals) |
| AI Assistant | Plain-English questions about sales, products, outlets, stock, customers, forecasts, anomalies and *why* numbers changed; follow-up questions, voice input, and a "Source & method" panel under every answer |
| Sales | Bill history with filters, manual billing (stock checked, GST-inclusive prices, customer by phone), voids with stock restore, a demo GST invoice for any bill, CSV export |
| Inventory | Stock per outlet with days of cover, adjustments, transfers, movement history, demand-based reorder suggestions → purchase orders, 14-day stockout risk |
| Products, Suppliers, Customers | Catalogue with HSN and GST; suppliers and POs with partial receiving; customers with GSTIN, RFM segment and history |
| Forecasts | Total, outlet, category or product forecasts; 7, 14 or 30 days; 80% band; model leaderboard (WAPE, sMAPE, MAE, RMSE, band coverage, bias); stock plan |
| Model comparison | Rolling-origin evaluation (start one from the page), WAPE per model, per series type and per series, and the history of every forecast run with full details |
| Anomalies & drivers | Driver decomposition for 7, 14 or 30 days or month to date; unusual days with evidence; suspicious bill lines; detector precision and recall |
| Analytics | Trends, weekday × hour heatmap, payment and channel mix, ABC, market basket (lift), outlets, RFM |
| Reports & export | 9 reports (daily sales, outlets, products ABC, categories, GST summary, inventory valuation, reorder, customer segments, unusual days) as CSV or formatted Excel |
| Data import | Sales, products, customers, suppliers and stock counts; templates and sample files (valid, and with mistakes), column mapping, dry run, error report CSV, history |
| Invoices | Demo GST invoices: CGST + SGST or IGST by place of supply, HSN, amount in words, PDF, history |
| Audit log | Who created, changed, voided or deleted what, with field-level changes (admin) |
| Settings | Organisation (GSTIN, state, time zone, currency), users with several outlets and 4 roles, profile, sign out everywhere, dataset info, demo reset, clear transactions |

**Roles.**

- **Admin:** everything.
- **Manager:** assigned outlets, stock, purchasing, imports and voids.
- **Staff:** billing and stock lookup.
- **Viewer:** read-only dashboards, analytics, forecasts, reports and the assistant.

## Quick start

### Docker (one command)

```bash
docker compose up --build                 # http://localhost:8000; demo data is generated on first start (~1 minute)
```

Other variants:

```bash
DATABASE_URL=postgresql+psycopg2://eris:eris@postgres:5432/eris docker compose --profile postgres up --build
docker compose --profile ai up --build    # adds Ollama; then: docker compose exec ollama ollama pull llama3.2:3b
```

### Local (Python 3.11+, Node 20+)

```bash
cd api && python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000          # creates the schema (Alembic) and the demo data on first start

cd web && npm install && npm run dev               # http://localhost:5173 (proxies /api to :8000)
```

To run everything as a single process, run `cd web && npm run build`; the API then serves the built app on
port 8000.

### Start with your own data

Set `SEED_DEMO_DATA=false`, `INITIAL_ADMIN_EMAIL` and `INITIAL_ADMIN_PASSWORD` before the first start (or run
`python -m app.manage create-admin --email owner@shop.in --name "Owner" --org "My Shop"` in `api/`). Sign in, add
your outlets, products and suppliers in the app, or load them with **Data import**. Forecasts need at least three weeks
with sales (more history gives better accuracy); until then the Forecasts page says so.

### Demo logins

| Role | Email | Password | Outlets |
|---|---|---|---|
| Owner / admin | `admin@eris.demo` | `Admin@123` | all |
| Outlet manager | `priya.and@eris.demo` | `Manager@123` | Andheri West |
| Area manager | `arjun.ind@eris.demo` | `Manager@123` | Indiranagar + Whitefield |
| Staff | `staff.andheri@eris.demo` | `Staff@123` | Andheri West |
| Analyst (viewer) | `analyst@eris.demo` | `Viewer@123` | all, read-only |

## Dataset

The demo dataset has:

- one organisation and 5 outlets (Mumbai, Pune, Bengaluru ×2, Ahmedabad), each with its own demand profile;
- 61 products in 9 categories, 8 suppliers and about 2,600 customers;
- **2 years of bill-level history** (about 216,000 bills and 789,000 lines);
- 53 promotions, 103 price changes, daily weather, 597 stockout events with substitutes and 26 labelled
  anomalies.

It is deterministic: the same seed and end date always produce the same data. Every synthetic bill references
a provenance record (generator version, seed, timestamp, period).

To regenerate it:

```bash
cd api && python -m app.seed --days 730 --outlets 5 --seed 42 [--end-date 2026-09-30]
```

Details are in [docs/DATASET.md](docs/DATASET.md). To use your own data, clear the transactions (Settings →
System & data), then import CSVs or enter sales manually. Real data is never date-shifted or overwritten.

## Model design and results

- **Forecasting.** The candidates and features are described in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#forecasting).
  The selection rule is: Prophet is the incumbent, and a challenger must cut back-test WAPE by more than 10% to
  replace it. The 80% interval comes from back-test errors.

  | Model | Mean WAPE (25 series × 3 origins) |
  |---|---:|
  | Seasonal naive (baseline) | 20.2% |
  | Holt-Winters | 19.6% |
  | XGBoost | 22.0% |
  | **Prophet** | **17.2%** |
  | ERIS auto-selection | 17.3% |

  The full report is in [docs/FORECAST_EVALUATION.md](docs/FORECAST_EVALUATION.md), with the model card in
  [docs/MODEL_CARD.md](docs/MODEL_CARD.md) and the notebook in
  [notebooks/forecast_evaluation.ipynb](notebooks/forecast_evaluation.ipynb).
- **Assistant.** Its design is in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#ai-assistant), and the
  grounding evaluation is in [docs/ASSISTANT_EVALUATION.md](docs/ASSISTANT_EVALUATION.md).
- **Scope audit.** [docs/AUDIT.md](docs/AUDIT.md) compares every agreed requirement with its implementation and
  lists the deliberate deviations.

## Limitations

- All accuracy figures come from **synthetic** data. They show how the models compare against a known demand
  process, not how they would perform for a real shop.
- XGBoost is weaker than the baseline on aggregate series in this data, which is reported as is. LSTM was left
  out because the scope made it optional and simpler models already win.
- The 80% prediction band is slightly narrow: it covers 75.5% of held-out days.
- The assistant's rule-based parser covers the documented question types. Other phrasings fall back to help
  text, or to the local LLM when Ollama is installed. Check the licence of whichever model you pull.
- Demo GST invoices are illustrations only: there is no IRN, e-way bill or GSTR filing.
- Background jobs (demo generation, evaluation) run inside the API process. That is fine for a single-tenant
  demo; a production deployment would use a task queue.

## Configuration

Every setting has a default; see [`api/.env.example`](api/.env.example).

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | SQLite in `api/data/eris.db` | e.g. `postgresql+psycopg2://eris:eris@localhost:5432/eris` |
| `JWT_SECRET_KEY` | development value | **Change this for any shared deployment** (the app warns at startup) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` / `REFRESH_TOKEN_EXPIRE_DAYS` | 60 / 14 | Session lifetime |
| `SEED_DEMO_DATA`, `SEED_DAYS`, `SEED_OUTLETS`, `SEED_RANDOM_STATE`, `SEED_END_DATE` | true, 730, 5, 42, yesterday | Demo data generation (at least 90 days, 1-7 outlets) |
| `INITIAL_ADMIN_EMAIL`, `INITIAL_ADMIN_PASSWORD` | not set | With `SEED_DEMO_DATA=false`: the first admin created on an empty database |
| `LLM_ENABLED`, `OLLAMA_URL`, `OLLAMA_MODEL` | true, `http://localhost:11434`, `llama3.2:3b` | Optional local LLM |

## Development and verification

```bash
cd api
pip install -r requirements-dev.txt
ruff check app tests && pytest -q                       # 88 tests
TEST_DATABASE_URL=postgresql+psycopg2://eris:eris@localhost:5432/eris_test pytest -q   # same suite on PostgreSQL
python -m app.evaluation                                # forecast evaluation   -> docs/FORECAST_EVALUATION.md
python -m app.assistant_eval                            # assistant grounding   -> docs/ASSISTANT_EVALUATION.md

cd web && npm run lint && npm run build
cd e2e && npm install && npx playwright install chromium && npm test   # starts its own API on a fresh database
```

The OpenAPI docs are at `http://localhost:8000/docs`. CI (`.github/workflows/ci.yml`) runs four jobs: the API
tests on SQLite, the API tests on PostgreSQL 16, web lint and build, and the Playwright e2e suite.

## Project structure

```
api/
  app/models.py            data model (26 tables)            migrations/   Alembic
  app/routers/             REST endpoints                    tests/        pytest suite
  app/services/            analytics, forecasting, features, anomalies, drivers, importer, reports,
                           invoices, gst, audit, alerts, assistant/ (nlu, tools, knowledge, llm, engine)
  app/seed/                synthetic data generator
  app/evaluation.py        rolling-origin forecast evaluation
  app/assistant_eval.py    assistant grounding evaluation
web/                       React app (pages/, components/, lib/)
e2e/                       Playwright end-to-end tests
notebooks/                 demand analysis and model comparison
docs/                      architecture, dataset, model card, evaluations, audit, knowledge base for the assistant
```

## Tech stack (all free and open source)

- **Backend:** Python 3.11, FastAPI, SQLAlchemy 2, Alembic, SQLite or PostgreSQL, pandas, NumPy, statsmodels,
  Prophet, XGBoost, openpyxl, reportlab, PyJWT, bcrypt.
- **Frontend:** React 19, Vite, React Router, TanStack Query, Recharts, Lucide.
- **Optional AI:** Ollama with a local model.
- **Quality:** pytest, Playwright, ruff, ESLint, GitHub Actions, Docker.

## About

ERIS began as a data-science internship project (Jan 2025 – Apr 2026) and was later rebuilt into a complete,
reproducible portfolio project. [docs/PORTFOLIO_SUMMARY.md](docs/PORTFOLIO_SUMMARY.md) gives a résumé-ready
summary.
