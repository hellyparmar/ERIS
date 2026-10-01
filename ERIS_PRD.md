# ERIS Product Requirements and Implementation Plan

Version: 2.0
Status: portfolio hardening in progress
Scope owner: single organization, 5–7 outlets
Last reconciled with code: 2026-10-01

## 1. Product objective

ERIS demonstrates an end-to-end data-science product rather than disconnected dashboards. It must let a small retail organization capture or import operational data, maintain inventory and billing records, inspect analytics, ask grounded business questions, and generate measurable demand forecasts.

Portfolio priorities are:

1. AI answers grounded in the user's authorized ERIS data.
2. Forecasts produced by real models with honest holdout metrics.
3. Complete data flows from write action to database to analytics/UI.
4. A free/open-source-first architecture that one developer can understand and deploy.
5. No fabricated metrics, mock production actions, hardcoded secrets, or unnecessary infrastructure.

## 2. Users and authorization

| Role | Scope | Allowed actions |
|---|---|---|
| Admin | All outlets in the organization | All reads/writes, user registration, product creation, imports, exports, forecasts |
| Manager | Assigned outlets | Operational reads/writes, sales, inventory adjustments, customers, invoices, forecasts |
| Viewer | Assigned outlets | Read-only dashboards, analytics, records, forecasts, alerts, and AI questions |

All non-admin data access must be limited to assigned outlets. Cross-outlet IDs must produce 403 or an empty scoped result, never leaked rows.

## 3. Required functional areas

### 3.1 Authentication and settings

- Email/username login, short-lived access token, refresh token, logout, and current-user endpoint.
- Admin-only user registration with strong-password validation.
- Profile update and password change persisted to the database.
- Rate limiting on login endpoints.
- Access tokens must not be accepted as refresh tokens.

### 3.2 Organization and outlets

- Exactly one active organization for the portfolio release.
- Five deterministic demo outlets; architecture permits seven without code changes.
- Outlet list/detail/create/update/delete with organization and role scoping.
- Synthetic, structurally valid GSTIN generation for the demo organization.

### 3.3 Sales data acquisition

- Manual sale entry with product/customer/outlet/payment selection.
- CSV sales import with row validation and useful error reporting.
- Downloadable CSV source/template guidance.
- Deterministic synthetic generator for one year of portfolio data.
- Every accepted sale must persist line items, decrement the correct outlet inventory, update customer aggregates where applicable, and record stock movement.

POS/Odoo integration is deferred. It adds credential, mapping, retry, and vendor-support complexity without improving the current portfolio demonstration. It should be added only after a real data-source requirement exists.

### 3.4 Inventory and catalog

- One product catalog shared by the organization.
- One inventory balance per `(outlet_id, product_id)`; no second global stock field.
- Admin product/category creation and opening balance.
- Admin/manager stock adjustment with before/after movement history and notes.
- Low-stock and out-of-stock status based on product reorder level.
- Inventory CSV import and XLSX export.

### 3.5 Customers, suppliers, and outlets

- Paginated search/list/detail/create/update/delete flows.
- Organization isolation and soft deletion where modeled.
- Supplier payment terms and outstanding payable only when backed by stored fields.
- No invented credit scores, loyalty tiers, or recommendations.

### 3.6 GST invoicing

- Create invoice from actual outlet/customer/product data.
- Server-calculated taxable value, discount, CGST/SGST/IGST, and total.
- Persist line items and invoice status.
- Pay/cancel actions and downloadable PDF.
- GSTR-1 period summary and validation.
- Demo GSTIN values must be synthetic and labeled as such.

### 3.7 Analytics and reporting

- Summary KPIs, revenue trend, category mix, top products, and outlet comparison derived from sales tables.
- Sales, inventory, invoices, and customers export through real endpoints.
- Empty states must say that no data exists; they must not insert sample numbers.

### 3.8 Alerts

- Generate and persist missing low-stock/stockout alerts.
- List/filter alerts by outlet, severity, category, and acknowledgement state.
- Admin/manager acknowledgement with actor and timestamp.
- Scheduled generation may run in-process; a broker is not required for this deployment size.

### 3.9 Grounded AI assistant

- Match business questions only to reviewed read-only SQL templates.
- Parameterize outlet scopes; never interpolate user text into SQL.
- Return verified rows even when no LLM is available.
- Prefer local Ollama; optionally use Groq then OpenRouter for natural-language wording.
- Persist chat sessions per user and prevent cross-user history access.
- Clearly label the answering provider.
- Unsupported questions must not fabricate an answer.

Initial supported intents: top products, period revenue, daily trend, top customers, low/dead stock, month comparison, underperforming outlets, supplier payables, AOV trend, and latest forecast.

### 3.10 Forecasting

- Use completed sales joined to sale items and aggregate daily demand.
- Require at least 60 days of history.
- Evaluate Prophet and XGBoost on held-out recent data, retrain on full history, combine by inverse-error weighting, and persist all predictions/metrics.
- Support 7-, 14-, and 30-day horizons with optional product filter.
- Display point forecast, interval, component predictions, and MAPE/RMSE/MAE.
- Run through bounded in-process background jobs; job status is private to its creator.
- Provide inventory-depletion and anomaly endpoints only from real data.

Poor model accuracy is a result to improve, not a number to hide. Evaluation must state dataset, split, horizon, and metric limitations.

## 4. Technical architecture

| Layer | Choice |
|---|---|
| Web | React 19, Vite, TanStack Query, Recharts/Chart.js |
| API | FastAPI, Pydantic, SlowAPI |
| Persistence | SQLAlchemy 2, Alembic, PostgreSQL production, SQLite development/tests |
| Forecasting | pandas, NumPy, Prophet, XGBoost, scikit-learn, holidays |
| AI | reviewed SQL semantic layer; optional Ollama/Groq/OpenRouter over HTTP |
| Scheduling | APScheduler in the web process |
| Deployment | Render API, Vercel static frontend |
| CI/security | pytest, Ruff, ESLint, Vite build, npm audit, Gitleaks, detect-secrets |

Docker, Celery, Redis/Valkey, ChromaDB, n8n, Nginx, LSTM/Torch, multi-tenant RLS, and vendor integrations are excluded. They solve scale or integration problems this release does not have.

## 5. Data and schema rules

- IDs and foreign keys must use compatible types.
- Organization and outlet scope columns must be present on operational records that require them.
- Financial values use decimal database types; serialization may convert to numbers at the API boundary.
- The migration directory has one portfolio baseline. Prototype databases are recreated rather than upgraded through deleted experimental migrations.
- The generator uses fixed seed 42 by default, synthetic `.example`/`.test` identities, and an operator-supplied password.

## 6. Security and privacy requirements

- No runtime secret may have a default value.
- `.env.example` contains placeholders only.
- Production startup rejects missing/placeholder database and JWT configuration.
- Error responses must not expose stack traces or provider response bodies in production.
- Mutation endpoints require admin/manager as specified.
- Secret scanners must pass on every push and pull request.
- Historical GitGuardian findings require provider-side rotation and dashboard resolution; code changes alone do not close them.

## 7. Deployment acceptance criteria

- Alembic upgrades an empty PostgreSQL database to one head.
- API health endpoint responds successfully.
- Vercel frontend reaches the configured Render API without CORS errors.
- Login, one manual sale, one CSV import, one stock adjustment, one invoice/PDF, one alert acknowledgement, one AI query, and one forecast complete in the deployed environment.
- No required feature depends on a process not declared in deployment configuration.
- Restarting the API may clear transient job status, but persisted forecasts and business records remain.

## 8. Current implementation status

### Phase 1 — architecture, security, and core-flow repair: implemented

- Removed Docker/Compose, Nginx, Redis/Valkey, Celery, n8n, abandoned integrations, duplicated models/services, fake pages/actions, and stale browser tests.
- Consolidated authentication, roles, outlet isolation, models, migration baseline, example configuration, and CI.
- Repaired sales/manual/CSV inventory effects, customer aggregates, product creation, stock history, invoices, exports, analytics, alerts, settings, AI grounding, and ensemble forecasting.
- Added deterministic five-outlet seed and portfolio-critical API tests.
- Replaced historical screenshots/notebooks that contradicted current code with reproducible validation.

### Phase 2 — release verification and deployment: current

1. Keep backend tests, Ruff/import/architecture checks, frontend lint/build, package audit, and both secret scanners green.
2. Validate the runtime-generated OpenAPI schema against frontend calls.
3. Deploy PostgreSQL + Render API + Vercel frontend with environment-only secrets.
4. Perform the deployment acceptance journey in section 7 and capture new screenshots from that build.
5. Add a short demo video and architecture/forecast evaluation notes to the portfolio.

### Phase 3 — data-science quality upgrades: next

1. Add rolling-origin backtesting by outlet/product and a naive seasonal baseline.
2. Report WAPE/MASE alongside MAPE so low-volume products are evaluated fairly.
3. Track forecast runs rather than overwriting the latest model row, then chart accuracy drift.
4. Add feature-importance/explainability for XGBoost and holiday/event contribution notes.
5. Create an automated AI evaluation set covering intent matching, outlet isolation, no-data responses, and unsupported questions.
6. Add data-quality monitoring for missing dates, negative values, duplicate sales, and inventory reconciliation.

### Phase 4 — optional expansion, only after evidence of need

- A single real POS/Odoo connector with documented field mapping, idempotency, retry, and sync audit.
- Durable external job queue only if forecasts exceed web-host limits or concurrent usage requires it.
- Additional organizations only with a complete tenancy threat model and isolation tests.

## 9. Explicit non-goals

- Production ERP replacement, payment processing, payroll, messaging/WhatsApp, marketplace, loyalty program, causal inference, or autonomous purchasing.
- Claims of “real-time” behavior where the implementation polls or schedules periodically.
- AI-generated SQL, autonomous mutations, or forecasts presented as guarantees.
- Paid APIs as a requirement for the demo.

## 10. Definition of done for the portfolio release

The release is done when all CI/security gates pass, the fresh database and seed work, the deployment acceptance journey succeeds, current screenshots match the deployed product, and the README/PRD accurately describe only the code that exists. Historical service credentials must be rotated or proven invalid separately.
