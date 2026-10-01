# ERIS — Enterprise Retail Intelligence System

ERIS is an open-source retail management and analytics platform for a business that runs **several outlets**.
It puts sales, inventory, purchasing, customers, **demand forecasting** and a **plain-English AI assistant**
in one place, so a non-technical owner or store manager can run every outlet from one screen.

![Dashboard](docs/images/dashboard.png)

It ships with a realistic demo company, **Urban Harvest Foods** (a food & beverage retail chain with
6 outlets in Mumbai, Pune, Bengaluru and Ahmedabad, ~18 months of history, ~200k bills), generated on first start.

## Features

| Area | What you can do |
|---|---|
| **Dashboard** | Revenue, bills, average bill, gross profit vs previous period · trend vs last period · 14-day forecast · outlet ranking · category mix · live alerts |
| **AI Assistant** | Ask *"What should I reorder?"*, *"Compare September with August"*, *"Forecast milk demand for 2 weeks"*, *"Which customers are at risk?"*, *"How can I increase sales?"* — answers with numbers, charts and tables from live data. Follow-up questions (*"what about Pune?"*), voice input, works offline; optionally uses a free local LLM (Ollama) |
| **Sales** | Bill list with filters, manual billing (stock checked & reduced, customer linked by phone, discounts, GST-inclusive pricing), void with stock restore, CSV export |
| **Inventory** | Stock per outlet with days of cover, stock-take / damage adjustments, transfers between outlets, full movement audit log, **demand-driven reorder suggestions → purchase orders in one click** |
| **Products** | Catalogue with prices, GST, margins, suppliers, categories; product detail with stock by outlet, sales trend and *frequently bought with* |
| **Suppliers & POs** | Supplier directory with lead times and on-time rate, purchase orders, partial receiving |
| **Customers** | Loyalty & business customers, purchase history, RFM segment (Champions, At Risk, …) |
| **Forecasts** | Total / outlet / category / product forecasts (7–90 days) with 80% range, model leaderboard, back-test overlay, festival calendar, stock-out date and order quantity |
| **Analytics** | Trends, weekday × hour heatmap, payment & channel mix, bill-size distribution, ABC analysis, market-basket analysis, outlet comparison, RFM segmentation |
| **Data import** | CSV import for sales, products, customers, suppliers and stock counts — templates, dry-run check with row-level errors, all-or-nothing commit |
| **Roles** | Admin (all outlets, settings, users) · Manager (own outlet, stock, purchasing, voids) · Staff (billing, stock lookup) |

## Screenshots

| AI assistant | Forecasts |
|---|---|
| ![Assistant](docs/images/assistant.png) | ![Forecasts](docs/images/forecasts.png) |
| **Analytics** | **Reorder suggestions** |
| ![Analytics](docs/images/analytics.png) | ![Reorder](docs/images/reorder.png) |

<img src="docs/images/mobile-dark.png" alt="Mobile, dark mode" width="260">

## Data science highlights

- **Forecasting with model selection** — Seasonal-naive baseline, Holt-Winters (statsmodels), recursive gradient
  boosting on lag + calendar + festival features (scikit-learn) and Prophet with an Indian festival calendar.
  Every series is back-tested on the latest 4 weeks; the lowest-WAPE model (or an ensemble of the best two) is used,
  and the 80% interval comes from that model's real back-test errors.
- **Inventory optimisation** — reorder point = demand × lead time + safety stock (1.65σ√L ≈ 95% service level),
  order-up-to = lead time + review period, pending POs counted as incoming stock.
- **Market-basket analysis** — support, confidence and lift for product pairs.
- **RFM customer segmentation** and **ABC product classification**.
- **Synthetic data generator** with a structural demand model: weekday and yearly seasonality, Indian festivals
  (Diwali, Holi, Ganesh Chaturthi, …), monsoon footfall dip, outlet growth/decline, a new outlet ramping up,
  loyalty customers with churn, product affinities, UPI adoption trend and price inflation.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the design, data model and methodology.

## Tech stack (all free & open source)

- **Backend:** Python 3.11, FastAPI, SQLAlchemy 2, SQLite (default) or PostgreSQL, pandas, scikit-learn,
  statsmodels, Prophet, JWT + bcrypt
- **Frontend:** React 19, Vite, React Router, TanStack Query, Recharts, Lucide icons (plain CSS, light/dark theme, mobile-friendly)
- **Optional AI:** [Ollama](https://ollama.com) running a local model such as `llama3.2:3b`
- **Tooling:** pytest, ruff, ESLint, GitHub Actions, Docker

## Quick start

### Option 1 — local (Python 3.11+ and Node 20+)

```bash
# 1. API (generates the demo data on first start, ~1 minute)
cd api
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 2. Web app (second terminal)
cd web
npm install
npm run dev                                             # http://localhost:5173
```

### Option 2 — one process

```bash
cd web && npm install && npm run build      # creates web/dist
cd ../api && uvicorn app.main:app --port 8000
# open http://localhost:8000 - the API also serves the built web app
```

### Option 3 — Docker

```bash
docker compose up --build                       # http://localhost:8000
docker compose --profile ai up --build          # + local LLM; then: docker compose exec ollama ollama pull llama3.2:3b
```

### Demo logins

| Role | Email | Password |
|---|---|---|
| Owner / admin | `admin@eris.demo` | `Admin@123` |
| Outlet manager (Andheri West) | `priya.and@eris.demo` | `Manager@123` |
| Staff (Andheri West) | `staff.andheri@eris.demo` | `Staff@123` |

## Using your own data

1. Sign in as admin → **Settings → System & data → Clear transactions** (keeps outlets, products, suppliers, users),
   or edit the demo outlets/products directly.
2. **Data import** → download a template → fill it in Excel/Google Sheets → *Check file* → *Import*.
3. Or record sales manually from **Sales → New sale**.

Regenerate the demo at any time from Settings, or from the command line: `cd api && python -m app.seed`.

## Configuration

Everything has a sensible default; see [`api/.env.example`](api/.env.example). Most useful settings:

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///api/data/eris.db` | e.g. `postgresql+psycopg2://eris:eris@localhost:5432/eris` |
| `JWT_SECRET_KEY` | dev value | **Change for any shared deployment** |
| `SEED_DEMO_DATA` / `SEED_DAYS` | `true` / `540` | Generate demo data on an empty database |
| `OLLAMA_URL` / `OLLAMA_MODEL` | `http://localhost:11434` / `llama3.2:3b` | Optional local LLM for the assistant |

## Development

```bash
cd api && pip install -r requirements-dev.txt && ruff check app tests && pytest -q   # 23 API tests
cd web && npm run lint && npm run build
```

API documentation is available at `http://localhost:8000/docs` (OpenAPI / Swagger).

## Project structure

```
api/                 FastAPI backend
  app/models.py      data model (organization, outlets, products, stock, sales, POs, customers, users)
  app/routers/       REST endpoints
  app/services/      analytics, forecasting, inventory, sales, CSV import, alerts, AI assistant
  app/seed/          demo data generator
  tests/             end-to-end API tests
web/                 React frontend (pages/, components/, lib/)
docs/                architecture & methodology
```

## About

Built as a data-science internship project (Jan 2025 – Apr 2026) and extended into a fully working portfolio project.
