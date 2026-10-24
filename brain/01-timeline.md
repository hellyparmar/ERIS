# Timeline

All non-merge commits on this branch, oldest first, grouped by era. Dates are commit dates. "PR #n" marks a merge
commit on the GitHub pull request of that number.

Three eras are visible in the history:

- **Era 0 (Feb–Mar 2026): an earlier product.** Phased POS, billing and compliance work. Removed in full on
  2026-10-01. Its history is kept, its code is not in the working tree.
- **Era 1 (June 2026): a UI pass on that earlier product.** Superseded by the rebuild.
- **Era 2 (2026-10-01 onward): ERIS.** The current product, a restaurant intelligence system.

---

## Era 0: earlier product, Feb–Mar 2026 (removed)

| Date | Commit | What it did |
|---|---|---|
| 02-17 | b86cc36 | Phase 0 foundation: PostgreSQL verified, indexes added, packages installed, localhost fixed |
| 02-17 | b6ef1e7, 1a7855e | Two-flow JWT login: manager password (1 h session) and cashier PIN (8 h), with role permissions |
| 02-17 | 1c88bcd | Pagination helpers and a Redis cache utility |
| 02-17 | cffd941 | Enabled the two-flow auth endpoints in the app router |
| 02-17 | 5ad876c | Phase 1B: manager override system and day open/close workflow |
| 02-17 | d0e7f69 | Phase 1B: offline queue and WhatsApp integration |
| 02-17 | 6c790ea, 1c382fb, 35f68af | Phase 1 documentation, developer quick reference and index |
| 02-18 | b808301, 9b14741, 35c874e | Production-readiness infrastructure and documentation |
| 02-18 | 1434422 | Phase 2 core services: GST, invoicing, credit management |
| 02-18 | 58b225c, bfee4d4, f13cdac | Phase 2 REST routers, PDF invoice generation, unit tests |
| 02-18 | 1171978 → d925345 | Phase 2 Session 3: database integration, credit and GST routers, auth middleware, integration tests, status documents |
| 02-18 | 629f0f0, a0d0848, c44edc2 | Test-execution fixes: imports, foreign keys, fixtures, host middleware |
| 02-18 | 5dff3bc | Invoice router accepts JSON bodies with Pydantic models (work in progress) |
| 02-25 | 18e7012 | Remaining Phase 1 tasks |
| 02-25 | 537410b | Phase 3: billing and compliance |
| 02-25 | 67ba17f, 8d40deb | SQL column fixes, GSTIN column compatibility |
| 02-26 | 0ce8c3e | POS login fix: bypass an ORM mapper conflict |
| 03-25 | 3e614eb | Initial commit after a security audit and cleanup |
| 03-26 | 6b0dbc8 | JWT secret rotated; unneeded files removed |

## Era 1: June 2026 UI pass (superseded)

| Date | Commit | What it did |
|---|---|---|
| 06-05 | 1c513fb | Removed obsolete legacy tests; renamed the load-test file |
| 06-11 | 446683b, 9d529e7, c971483 | Premium component system, Storybook configuration, dark-mode foundation on Tailwind v4 |
| 06-11 | fdd317a | Removed duplicate page titles |
| 06-12 | a20b013 | First README |

## Era 2: ERIS (2026-10-01 onward)

### The rebuild

| Date | Commit | What it did and why |
|---|---|---|
| 10-01 | a8f5319, c1299f5 | Repaired the old frontend so its production build passed, before it was replaced |
| 10-01 | 951a0e7 | **Rebuilt the backend**: demo data, forecasting and the AI assistant |
| 10-01 | 49e3dda | **New web app**, docs, Docker and CI |
| 10-01 | 782df68 | **Removed the legacy backend, frontend and tooling** |
| 10-01 | 3ba1979 | PostgreSQL support verified; forecast evaluation study; security hardening |
| 10-01 | 616f0cc | Business clock uses the organisation's time zone; Ollama client tested |
| 10-02 | 7a84135 | Schema v3 with Alembic migrations, generator v3, roles, refresh tokens, audit log |
| 10-02 | 82259a4 | Forecasting v3: XGBoost with exogenous features, persisted runs, anomaly detection, revenue drivers |
| 10-02 | 9a3f340 | Importer v2, reports with CSV and Excel export, demo GST invoices, audit-log API |
| 10-02 | e282d5e | Assistant v3: new intents, provenance on every answer, documentation retrieval |
| 10-02 | 7153c3d | API tests: refresh rotation and revocation, area managers, multi-outlet users, outlet cap, viewer limits |
| 10-02 | 9f4dd00 | Web: model comparison, anomalies and drivers, reports, invoices, audit log, import column mapping, provenance |
| 10-02 | 884fec9 | Playwright end-to-end suite in CI; assistant grounding evaluation; refreshed forecast evaluation |
| 10-02 | 9653f22 | Fixed a rainfall-driver NaN on PostgreSQL (rows were unordered); Postgres tests start from an empty schema |
| 10-02 | 42c0275 | Notebook: XGBoost and exogenous features, rain effect, anomaly detection against labels |
| 10-02 | aa76cc0 | Docs: README, dataset, model card, scope audit, portfolio summary, architecture diagrams, screenshots |
| 10-02 | 4bbe5e4 | Login lists all demo roles and says the data is synthetic |
| 10-02 | f96e137 | Fixes from a full API and assistant sweep |
| 10-02 | e258523 | Concurrency, first-run setup, generator edge cases, empty-data answers |
| 10-02 | ebc267a | Import and export fixes: UTF-16 files, NaN and huge quantities, dates before an outlet opened, CSV injection |
| 10-02 | f534063 | Concurrency gaps from full verification; like-for-like comparisons; route guards |
| 10-02 | 63d38ea | Numbering made airtight; calibrated forecast band; lean demo generation; hosted demo |
| 10-02 | e988fd2 | CI and Vercel fixes; dependencies pinned to tested versions; XGBoost without scikit-learn |
| 10-03 | be50e29 | Demo sign-in shortcuts come from the API, not from the web app |
| 10-04 | ceec816 | Render service renamed to `eris` |
| 10-04 | 5a44a72 | Hosted demo ready on start; redesigned UI; reusable forecasts; cached analytics |
| 10-04 | 26e56fe | Page answers prepared as single-outlet users request them |
| 10-04 | e0ca0bb | README screenshots on the prepared demo |
| 10-04 | edfd346 | CI signs in to the built image with the demo login it publishes, not a password in the workflow |
| 10-05 | 514787f | **Isolated each pipeline**: CI, demo-data build, forecasting and CSV imports |
| 10-05 | fc09565 | **UI redesign**: warm framed workspace, new dashboard, outlets page, assistant |
| 10-06 | a7e8978 | README links the live demo |
| 10-06 | 4b2ad6f | Every page opens at its top; titles set in Fraunces (a serif) |
| 10-06 | d558b53 | Test accepts a one-day like-for-like baseline for "this week" |
| 10-07 | 8be81c2 | Supermarket catalogue; demo-account dropdown; declutter pages; **removed the serif, back to Geist** |
| 10-08 | f4fddc7 | Web toolchain: Vite 8, ESLint 10, react-hooks 7, lucide 1 (Dependabot group, PR #30) |
| 10-15 | 2c920a2 | Assistant replies fast on the hosted demo: stopped per-start date shifting; cached answers |
| 10-15 | 90c91d2 | **Restaurant chain**: Saffron Table dataset, recipes, covers, channels, stock drawn by recipe, fast Sales, Kitchen stock and Menu pages (PR #31) |
| 10-17 | a595a26 | Screenshots regenerated; Sales and Analytics shots added; axis labels trimmed; Analytics heading reworded (PR #32) |
| 10-17 | 8615f2e | Merge of PR #32 into `main` |

### Pull-request merges in Era 2

#13, #22, #23, #24, #25, #27, #28, #29, #30, #31, #32 (see `git log --merges` for the full list).

### Work outside commits

- **2026-10-23/24:** this `brain` folder created. Not yet committed.
- A model-comparison evaluation was stored in the local demo database used for screenshots. That database is not part of the repository.
