# Decisions

Each decision gives: **what** was chosen, **why**, **alternatives**, **consequences**, and **source**.
*Source* is one of: *recorded* (in a commit, doc or code comment), or *reconstructed* (inferred from the code and docs; the original reasoning was not written down).

---

## D1. Rebuild the backend and web app rather than extend the earlier product
- **What:** On 2026-10-01 the legacy backend, frontend and tooling were removed (782df68) and ERIS was built from scratch (951a0e7, 49e3dda).
- **Why:** The product brief is one organisation with several outlets, with forecasting, analytics and an assistant. The earlier product was a phased POS and billing system built around a different domain. Rebuilding gave one consistent data model instead of two.
- **Alternatives:** Extend the old code in place. Not chosen.
- **Consequences:** The earlier history is only in git. Nothing from Era 0 or Era 1 is reachable from the working tree.
- **Source:** recorded in the commit subjects; the reason is *reconstructed*.

## D2. SQLAlchemy and Alembic, SQLite by default, PostgreSQL supported
- **What:** The same code runs on SQLite (zero setup, the demo and tests) and on PostgreSQL (production-like). Migrations are Alembic, currently up to `0004` (restaurant model).
- **Why:** SQLite means a demo runs with no install. PostgreSQL is what a real deployment would use, and some bugs only show there.
- **Evidence:** The rainfall driver returned NaN on PostgreSQL because rows were unordered (fixed in 9653f22). Tests run on both (`api-postgres` job).
- **Consequence:** No database-specific SQL. Assistant cache keys are capped at 64 characters because of a `varchar(64)` column on PostgreSQL.
- **Source:** recorded (commit 9653f22; AUDIT.md).

## D3. No multi-tenant row-level security; access enforced in the application
- **What:** One organisation (`organization_id` kept for modelling). Outlet access is checked in code (`security.scoped_outlet_ids`, `ensure_outlet_access`) on every outlet-scoped endpoint, including the assistant and reports.
- **Why:** The brief is one organisation. Row-level security adds a lot of machinery for a case that does not exist.
- **Alternatives:** Database RLS per tenant. Not chosen, listed as out of scope in AUDIT.md.
- **Consequence:** Every new endpoint must call the scope check. Tests (`test_viewer_*`, the area-manager test) guard this.
- **Source:** recorded (AUDIT.md).

## D4. Roles: admin, manager, viewer, plus staff
- **What:** Admin and manager can change data; viewer is read-only; staff can only bill. Managers may cover several outlets through `user_outlets`.
- **Why:** The brief asked for these roles. Staff was added so a counter user can bill without seeing the rest of the business.
- **Source:** recorded (AUDIT.md). The staff reason is *reconstructed*.

## D5. Access tokens plus rotating refresh tokens, revocation and lockout
- **What:** Short-lived access tokens and refresh tokens that rotate on each use. A `token_version` on the user revokes all sessions ("sign out everywhere"). Five failed logins lock the account.
- **Why:** Standard protection against stolen tokens and password guessing.
- **Consequence:** Covered by rotation and revocation tests (`test_refresh_rotates…`, and the revocation tests).
- **Source:** recorded (AUDIT.md, commit 7a84135).

## D6. Forecasting picks a model per series by back-test, and keeps a naive baseline
- **What:** Five candidates: seasonal naive, Holt-Winters, XGBoost (lags, calendar, promotions, weather), Prophet (seasonality, Indian festival calendar, regressors), and an ensemble. The "auto" choice is the best model on two 28-day back-test folds.
- **Why:** No single model wins everywhere. Keeping the seasonal-naive baseline means every claim of accuracy is measured against something simple. If a fancy model cannot beat naive, the app should say so.
- **Alternatives:** Always use one model (rejected: it lost on some series types). Only deep-learning models (rejected: slow on a small server, and little data per series).
- **Result:** 14.1% WAPE for auto vs 15.9% for seasonal naive across 25 series (about 11% lower error). See `08`.
- **Source:** recorded (commit 82259a4, FORECAST_EVALUATION.md).

## D7. Forecasts run off the request path, with limited slots
- **What:** Model fits take one of `FORECAST_WORKERS` slots. A request that cannot get one within `FORECAST_WAIT_SECONDS` gets a fast 503 with `Retry-After`. The dashboard answers without its forecast, and the assistant says forecasts are busy.
- **Why:** On a 0.1-CPU host, a few model fits can freeze every other request. A fast "busy, try again" is better than a hung page.
- **Alternatives (reconstructed):** Queue every fit (long waits on a small host). Precompute everything at build time only (good for the demo, but a real organisation's new data still needs live fits).
- **Source:** recorded (commit 514787f); the alternatives are reconstructed.

## D8. The assistant never writes SQL and never invents numbers
- **What:** Each question is matched to a validated intent template. The engine runs fixed queries and fills numbers from them. Every answer shows its data source, filters, timing, model version and caveats (provenance). Definition and how-to questions are answered from the project docs by retrieval. An optional local LLM (Ollama) can phrase answers, but the numbers still come from the queries.
- **Why:** The product promise is that every number traces back to data. Generated SQL is hard to audit and can return wrong numbers silently.
- **Alternatives:** Text-to-SQL with an LLM (rejected: not auditable). Pure LLM answers (rejected: ungrounded).
- **Source:** recorded (README, commit e282d5e). See `07`.

## D9. A deterministic synthetic dataset with labelled anomalies
- **What:** Seed 42. Two years of bills for a fictional five-outlet restaurant chain, with 26 labelled anomalies and 5 injected bill errors.
- **Why:** Results must be reproducible, and detection can only be scored against known answers. Labels make precision and recall measurable.
- **Consequence:** Numbers are fake by design. The UI, README and invoices say so. Invoices are watermarked "DEMO - NOT FOR TAX FILING".
- **Source:** recorded (DATASET.md, MODEL_CARD.md). See `05`.

## D10. Demo data is prepared at build time, and never shifted at start
- **What:** The Docker build bakes the database and warms caches. The hosted service sets `DEMO_SHIFT_DATES=false`.
- **Why:** Shifting dates on every start rewrote every dated row, held a write lock for minutes, and invalidated every cached answer. This was the main cause of slow replies on the hosted demo (2c920a2).
- **Consequence:** If the hosted service was not created from `render.yaml`, `DEMO_SHIFT_DATES=false` must be set by hand. See `11`.
- **Source:** recorded (commit 2c920a2, render.yaml).

## D11. Caches keyed by content, not by time
- **What:** Assistant answers are cached under the SHA-256 of the context JSON (64 hex characters). Lists for bills, stock and products use a response cache. Caches are invalidated when the data version changes.
- **Why:** A time-based cache returns stale numbers after an import. A content key is correct by construction, because a different question or different data gives a different key.
- **Source:** recorded (commits 2c920a2, 5a44a72, 90c91d2). See `06`.

## D12. Pipelines are isolated: CI, demo build, forecasting, imports
- **What:** CI uses a read-only token, checkout without persisted credentials, and actions pinned to commit hashes. The demo-data build is its own Docker stage with no network. The running image cannot write its own code, runs with 512 MB, no Linux capabilities, and `no-new-privileges`. PostgreSQL imports take an advisory lock.
- **Why:** Limits the damage a bad dependency, a compromised action or a bad import can do.
- **Source:** recorded (commit 514787f). See `09`.

## D13. Stock is drawn down by recipe
- **What:** Every sale of a dish reduces the ingredients its recipe uses, per outlet. Voiding a bill puts back exactly what was drawn. An ingredient cannot be sold as if it were a menu item. Reorder suggestions, run-out risk and lost-sales estimates use ingredient use, not dish sales.
- **Why:** For a restaurant, stock is ingredients, not dishes. Dish-level stock is wrong for a kitchen: one chicken goes into many dishes.
- **Alternatives:** Count dishes as stock (rejected: wrong for a kitchen). Manual stock only (rejected: no link to sales).
- **Source:** recorded (commit 90c91d2).

## D14. Pivot from a supermarket to a restaurant chain
- **What:** The supermarket catalogue (8be81c2) was replaced by Saffron Table, a five-outlet restaurant chain (90c91d2). The data model gained `products.kind` (menu or ingredient), a `recipes` table, `sales.covers`, and channels (dine-in, takeaway, delivery).
- **Why:** The owner asked directly for "a restaurant chain of 4–5 outlets", replacing the old dataset, with features changed to match.
- **Source:** recorded (the user's request, commit 90c91d2).

## D15. Typography: serif tried, then removed
- **What:** On 10-06 page titles were set in Fraunces (4b2ad6f). On 10-07 the serif was removed and headings returned to Geist with tighter sizes (8be81c2).
- **Why (recorded in 8be81c2):** the decluttering pass wanted one consistent typeface. The reason for the reversal is only partly recorded.
- **Final:** Geist is the typeface shipped. Fraunces is not in the code. Confirmed by the owner (`11`, O5).
- **Consequence:** Do not reintroduce Fraunces without reading this entry.
- **Source:** recorded for the change; the reason for reversing it is *reconstructed*.

## D16. Chart colours validated for colour-blind separation and contrast
- **What:** An 8-colour warm set, checked for colour-blind separation and contrast in light and dark themes, and on the dark forecast card.
- **Why:** Charts must read for everyone, including colour-blind readers.
- **Source:** recorded (commit fc09565).

## D17. Dependency upgrades are fixed, not just bumped
- **What:** The Dependabot web-group bump (Vite 8, ESLint 10, react-hooks 7) was merged with code changes: `manualChunks` as a function (Vite 8 requires it), and state set inside effects moved to refs or render-time adjustments (react-hooks 7).
- **Why:** A bump alone broke the build.
- **Source:** recorded (commit f4fddc7).

## D18. Evaluation numbers are regenerated and documented, not hand-edited
- **What:** `FORECAST_EVALUATION.md`, `ASSISTANT_EVALUATION.md`, screenshots and the dataset figures are produced by scripts and committed with the change that made them.
- **Why:** Hand-typed numbers drift from the code. Generated ones can be checked.
- **Source:** recorded (commits 8be81c2, 884fec9).

---

## D19. Commit trailers name no model
- **What:** Commits end with `Co-Authored-By: Claude <noreply@anthropic.com>` and `Claude-Session: <session URL>`. No model name appears in commit messages, PR text or repository files.
- **Why:** A session rule forbids model names in repository artifacts. Earlier commits named a model in their trailer, which conflicted with that rule.
- **Alternatives:** Keep the model trailer (conflicts with the rule). Rewrite earlier history (rejected: it would break the shared branch and the merged PRs).
- **Consequence:** Earlier commits keep their trailers. Only new commits follow this convention. `CLAUDE.md` states it.
- **Source:** recorded (`CLAUDE.md`, commit `9118970`).

---

## D20. Protect the request pipelines before they fail, and answer "busy" rather than error
- **What:** A pool sized to the thread pool, with a 10-second wait and a 503 when it is saturated. Export and forecast gates answer 503 when full. Identical cache misses share one computation. Per-address rate limits on the API, sign-in and heavy endpoints. Security headers, HTTPS redirect in production, request size ceiling, and TLS to PostgreSQL in production.
- **Why:** Under 25 concurrent users, the database pool timed out (15 connections against 40 threads) and exports returned 500 after 30 s. A 503 with `Retry-After` is recoverable; a 500 after a long wait is not. Single flight stops a burst from doing the same work many times.
- **Alternatives:** Stream the export files (rejected for now: the database session has to outlive the response, which needs care). Shared rate-limit store (deferred: one worker).
- **Consequence:** Heavy endpoints answer 429 after their budget per address. Shared networks need the limits raised; the settings are in `brain/13`.
- **Source:** recorded (`brain/13-hardening-and-pipelines.md`; load test figures above).



---

## D21. Refresh token only in an HTTP-only cookie; access token only in memory
- **What:** Browsers receive the refresh token as an HTTP-only cookie scoped to `/api/auth`. They send `X-ERIS-Client: web`, which refresh and logout require when the cookie is present. The access token lives in a variable. A reload restores the session. API clients keep the refresh token in the body.
- **Why:** The owner asked that tokens not be stored where page scripts can read them. `localStorage` is readable by any script that runs on the page.
- **Alternatives:** Keep `localStorage` (rejected: readable by script). Put both tokens in cookies (rejected: the access token is then sent with every request, including to other sites).
- **Consequence:** Cross-site cookies must be allowed (`SameSite=none`, Secure). Cookies blocked by the browser end the session on reload.
- **Source:** recorded (`brain/13`; code in `api/app/routers/auth.py` and `web/src/lib/api.js`).

