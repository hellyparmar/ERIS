# ERIS — Retail Intelligence System

ERIS is a portfolio-ready retail operations and data-science application for one organization with multiple outlets. It combines sales, inventory, customer, supplier, GST, and reporting workflows with a grounded AI assistant and an ensemble demand forecast.

The application is intentionally small enough to run without Docker, Redis, Celery, a vector database, or paid services. Local development uses SQLite; production uses PostgreSQL.

## What works

- JWT authentication with `admin`, `manager`, and read-only `viewer` roles
- Outlet-scoped access for managers and viewers
- Manual sales entry, CSV sales import, and deterministic synthetic demo data
- Outlet inventory, product creation, stock adjustment, and movement history
- Customer, supplier, and outlet management
- GST invoices, invoice PDF generation, payment/cancellation, and GSTR-1 summaries
- Database-backed dashboard and analytics
- Sales, inventory, customer, and invoice exports
- Low-stock alert generation and acknowledgement
- AI assistant with safe SQL templates, outlet scoping, and optional Ollama/Groq/OpenRouter wording
- Prophet + XGBoost ensemble forecasting with persisted results and measured holdout metrics
- Native Render API deployment and Vercel frontend deployment

## Architecture

```text
React + Vite (Vercel)
        |
        | HTTPS / JSON
        v
FastAPI + SQLAlchemy (Render)
        |
        +-- PostgreSQL in production / SQLite locally
        +-- in-process forecast jobs
        +-- optional Ollama, Groq, or OpenRouter
```

Docker was removed because it added a database, proxy, queue, and worker stack that this single-organization portfolio deployment does not need. Forecasts run in a bounded in-process job registry and durable results are stored in the database.

## Local setup

Requirements: Python 3.12, Node.js 24, and npm. Ollama is optional.

1. Copy `.env.example` to `.env`.
2. Replace every required `CHANGE_ME` value. For local SQLite, use `sqlite+aiosqlite:///./eris_dev.sqlite3` for `DATABASE_URL`. Generate a unique JWT secret of at least 32 random bytes. Choose your own demo password for `ERIS_SEED_PASSWORD`.
3. Install and initialize the backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m alembic upgrade head
python scripts/seed.py
python -m uvicorn app.main:app --reload
```

4. In another terminal, start the frontend:

```powershell
npm ci
npm run dev
```

The seed creates clearly synthetic `admin`, `manager`, and `viewer` users. They all use the password you supplied through `ERIS_SEED_PASSWORD`. The manager and viewer are restricted to outlet 1.

API documentation is available at `http://127.0.0.1:8000/docs`; the frontend runs at `http://127.0.0.1:5173`.

## Verification

```powershell
python -m ruff check backend
python backend/scripts/check_imports.py
python backend/scripts/ci_architecture_check.py
cd backend; python -m pytest -q; cd ..
npm run lint
npm run build
npm audit --omit=dev --audit-level=high
```

Secret scanning in CI runs both Gitleaks and:

```bash
git ls-files -z | xargs -0 detect-secrets-hook --baseline .secrets.baseline
```

See [ERIS_PRD.md](ERIS_PRD.md) for product scope and the phased implementation plan, and [SECURITY_CLOSURE.md](SECURITY_CLOSURE.md) for credential handling and historical-alert actions.

## Deployment

- Backend: create the Render service from `render.yaml`, attach a PostgreSQL `DATABASE_URL`, set `ALLOWED_ORIGINS` to the frontend URL, and optionally set an AI provider key.
- Frontend: import the repository into Vercel and set `VITE_API_URL` to the Render API origin.
- Run the seed manually once only if the portfolio deployment should contain synthetic demo data. Never seed a real operational database.

All runtime credentials belong in the deployment provider's environment settings, never in Git.

## Data

The included generator creates synthetic data only. No real business, customer, payment, or GST credentials are required or bundled.
