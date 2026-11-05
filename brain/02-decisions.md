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

## D19. Commits and pull requests carry no attribution trailers
- **What:** Commits and pull requests carry no `Co-Authored-By` or `Claude-Session` lines and no "Generated with" footer. No model name appears in commit messages, PR text or repository files.
- **Why:** The owner asked that the project not show that Claude helped build it, in GitHub or anywhere else people see the project. A session rule also forbids model names in repository artifacts.
- **Alternatives:** Keep the neutral trailer (rejected by the owner). Rewrite the older history on `main` to remove the trailers (not done: it would change every commit SHA on the public `main`, and the owner did not ask for it; 79 older commits still carry trailers).
- **Consequence:** Only commits from 2026-11-03 onward are clean, plus the six commits rewritten on the branch that day. `CLAUDE.md` states the new rule.
- **Source:** recorded (owner's request, 2026-11-03; `CLAUDE.md`). Supersedes the earlier version of this decision.

---

## D20. Protect the request pipelines before they fail, and answer "busy" rather than error
- **What:** A pool sized to the thread pool, with a 10-second wait and a 503 when it is saturated. Export and forecast gates answer 503 when full. Identical cache misses share one computation. Per-address rate limits on the API, sign-in and heavy endpoints. Security headers, HTTPS redirect in production, request size ceiling, and TLS to PostgreSQL in production.
- **Why:** Under 25 concurrent users, the database pool timed out (15 connections against 40 threads) and exports returned 500 after 30 s. A 503 with `Retry-After` is recoverable; a 500 after a long wait is not. Single flight stops a burst from doing the same work many times.
- **Alternatives:** Stream the export files (rejected for now: the database session has to outlive the response, which needs care). Shared rate-limit store (deferred: one worker).
- **Consequence:** Heavy endpoints answer 429 after their budget per address. Shared networks need the limits raised; the settings are in `brain/13`.
- **Source:** recorded (`brain/13-hardening-and-pipelines.md`; load test figures above).



---

## D21. Both session tokens in HTTP-only cookies; no token readable by the page
- **What:** Browsers receive the access token (`eris_access`, path `/api`) and the refresh token (`eris_refresh`, path `/api/auth`) as HTTP-only cookies, and neither token appears in a response body. They send `X-ERIS-Client: web`; changing requests authenticated by cookie, and refresh or logout with the cookie, are refused without it. API clients use the `Authorization` header and keep both tokens in the body.
- **Why:** The owner asked that tokens not be stored where page scripts can read them. `localStorage` is readable by any script that runs on the page.
- **Alternatives:** Keep `localStorage` (rejected: readable by script). Put both tokens in cookies (rejected: the access token is then sent with every request, including to other sites).
- **Consequence:** Cross-site cookies must be allowed (`SameSite=none`, Secure). Cookies blocked by the browser end the session on reload.
- **Source:** recorded (`brain/13`; code in `api/app/security.py`, `api/app/routers/auth.py` and `web/src/lib/api.js`).

## D22. CI runs on a fixed Ubuntu image
- **What:** Every CI job runs on `ubuntu-24.04`, not `ubuntu-latest`.
- **Why:** `ubuntu-latest` moved to Ubuntu 26.04. The pinned Playwright 1.56.1 cannot install Chromium there, so the `e2e` job failed on every run after the move (run 41688702034, commit 6f17eac). The other jobs passed on the same commit, so the break was in the runner image, not the code.
- **Alternatives:** Upgrade Playwright to 1.64.1 (Dependabot #37): a version change with its own risk, kept for a separate change. Pin only `e2e`: leaves jobs on different images.
- **Consequence:** The image must be moved on purpose before GitHub retires 24.04, with the Playwright version checked at the same time.
- **Source:** recorded (CI log; `.github/workflows/ci.yml`).

## D23. The runtime stays on Python 3.11; Dependabot holds the newer versions
- **What:** The API runs and is tested on Python 3.11 (CI jobs, `Dockerfile` base `python:3.11-slim`). `.github/dependabot.yml` ignores `numpy` 2.5 and later, and Docker `python` 3.12 and later. Moving the runtime is a separate change, made on purpose, with the full suite re-run.
- **Why:** numpy 2.5 publishes no wheel for Python 3.11, so Dependabot's pip group (#42) cannot install. The Docker base bump to 3.15 (#35) would move the runtime without the suite having run on it.
- **Alternatives:** Move to Python 3.12+ now (a runtime change with its own risk; the suite and the Render image must be re-verified). Let Dependabot keep proposing the bumps (they fail CI each month).
- **Consequence:** Existing PRs #42 and #35 stay open until closed; the rules stop new ones of the same kind. The owner can overrule this decision by removing the rules.
- **Source:** recorded (owner has not answered the question; this is the default chosen in the session, to be confirmed).

## D24. The hosted API is kept warm by a scheduled ping
- **What:** `.github/workflows/keep-warm.yml` requests the public health endpoint every 10 minutes. A failed ping fails the run.
- **Why:** The hosted free instance sleeps when idle. In the live light-load test one request hit a 60 s timeout; a warm request takes 0.3 to 0.5 s. The cold start is the likely cause (not proven: the server log is not available).
- **Alternatives:** A paid always-on plan (costs money; owner chose the free option). Leaving it (accepts slow first requests after idle periods).
- **Consequence:** One free instance running all month uses about 744 of the 750 free instance hours, so no second free service can run on the same account without exceeding them. Schedules can run late; the ping is a target, not a guarantee.
- **Source:** recorded (owner's answer, 2026-11-04).

## D25. The sales export escapes its text cells explicitly; no caching, no background job
- **What:** `csv_response` takes `escape=True` by default (every cell is checked, as before). The sales export escapes its text cells (invoice number, outlet, SKU, payment, channel, phone, customer name) itself and passes `escape=False`, so the numeric cells are not checked. Output is byte-identical. Exports are not cached, and no background export job is added. The export gate (two workers, 10 s wait, then 503 with Retry-After) stays.
- **Why:** A two-month export is 76k lines and 7.4 MB, about 1.0 s of in-process work. The 11 s median under 40 concurrent exports is queueing for two export slots on a CPU-limited host. Skipping the check on the numeric cells gives about 7 to 8 %. The earlier estimate of 15 to 25 % came from a variant that also skipped escaping on most text cells, which is unsafe and was not used.
- **Alternatives:** Cache the export (rejected: a 7 MB body per user and parameter set would grow the cache without a bound, and the cache stores JSON only). A background export job (a new endpoint and UI, moderate effort; not chosen). More CPU and export slots (costs money).
- **Consequence:** Under heavy export load callers still get a fast 503 and retry. The escaping is now explicit in the sales export and tested (`test_sales_export_neutralises_formulas_in_text_cells_only`).
- **Source:** recorded (owner's answers, 2026-11-04; measured in `brain/13`).

## D26. Admission control: at most 8 requests are answered at once; a wait of 5 s, then 503
- **What:** `HardeningMiddleware` answers at most `MAX_INFLIGHT_REQUESTS` (8; 0 disables) requests at once. A request that cannot get a slot within `INFLIGHT_WAIT_SECONDS` (5) gets `503` with `Retry-After: 2`. Health checks skip the queue.
- **Why:** The live heavy test (20 concurrent workers, 280 requests, 2026-11-04) answered 219 with 200 and 27 with 503, but **34 requests hit the 60 s client timeout**, including 27 of 40 forecasts. The server returned no 5xx: requests queued in silence past every client timeout. The per-endpoint gates do not bound the total queue. D20 already says to answer "busy" rather than wait.
- **Alternatives:** Only lower the endpoint gates (rejected: the queue is shared by all endpoints). A cap of 24 with immediate refusal (rejected: 20 workers would still all be admitted and would still hang on this host). A paid always-on host (the owner chose the free option).
- **Consequence:** With more than 8 requests in progress, the excess wait up to 5 s and are then refused. The values 8 and 5 are a first estimate for a 0.1-CPU host: they are not measured on the hosted instance yet and must be re-measured after deploy (open item G8).
- **Source:** recorded (live and local load tests, 2026-11-04; `brain/13`).

## D27. /api/health reports the commit that is serving
- **What:** `/api/health` returns `build`: the first 12 characters of `RENDER_GIT_COMMIT` (set by Render for each deploy), or `unknown` where it is not set.
- **Why:** Earlier checks could not confirm which build served the hosted API (open items G8 and the deploy-status question). One request now shows the commit.
- **Alternatives:** Put the SHA into the image at build time (needs a build argument and a Dockerfile change; the platform already provides the value). Expose nothing (rejected: the owner needs to verify deploys).
- **Consequence:** The commit SHA is public. The repository is already public, so no secret is exposed. The value is read only; health remains unauthenticated and unchanged otherwise.
- **Source:** recorded (owner's request, 2026-11-04; `api/app/main.py`).

## D28. "Sales incl. GST" is the name of the headline sales figure; the basis does not change
- **What:** Every visible label that said "Revenue" for the sum of bill totals now says "Sales incl. GST" (web pages, report headers, assistant tables, charts and KPIs). Margin and food cost stay on sales **excl. GST** and say so ("food cost 21.1% of sales excl. GST", "78.9% margin on sales excl. GST"). The compact money units are written out: "lakh" and "crore" (the single letter L is also litres elsewhere in the app). The forecast card says the total is for 14 days and that the % compares the next 7 days with the last 7. API field names (`revenue`) are unchanged.
- **Why:** The dashboard headline summed `Sale.total`, which includes 5% GST (₹4.50 L of ₹94.56 L on the hosted demo), while gross profit, margin and food cost were computed on sales without GST. Both were labelled "revenue" or "sales", so the figures looked inconsistent. Checked on the live payload: outlets, categories, payments and the daily trend each sum to the headline exactly (100.00%), so one basis applies throughout and one label is accurate everywhere.
- **Alternatives:** Make revenue exclude GST (every figure about 5% lower; the owner chose not to). Keep the labels and add a footnote (easy to miss).
- **Consequence:** Sentences the assistant narrates ("Revenue is down ...") and the example questions users can type keep the word "revenue" and still parse. A future page that shows a GST-exclusive figure must label it so.
- **Source:** recorded (owner's decision, 2026-11-04; code in `api/app/services/analytics.py`, web pages).

## D29. Uncached forecasts pass an admission gate before any data is loaded
- **What:** `forecast_series` now answers a cached result first, with no gate. An uncached request takes an admission slot (`FORECAST_WORKERS` + `FORECAST_QUEUE` = 1 fitting + 3 preparing) within `FORECAST_ADMIT_WAIT_SECONDS` (5 s); otherwise it is refused with the existing "Forecasts are busy" 503 and `Retry-After: 5`. The fit slot and its 20 s wait are unchanged.
- **Why:** On the hosted instance (0.1 CPU), 16 concurrent uncached forecasts gave 8 refused by the global limit after about 6 s, but of the 8 admitted, 6 were refused only after about 61 s and one connection was cut at 60 s. The series load and feature preparation run before the fit slot, so several of them slow each other down and the slot wait starts late (`brain/13`).
- **Alternatives:** Take the fit slot before loading (rejected: it would also serialise the cheap reuse path and make warm-cache requests wait behind a 30 s fit). A lower global cap (tried: 4 is worse than 8). Only shorten `FORECAST_WAIT_SECONDS` (rejected: the delay is mostly before the slot).
- **Consequence:** At most 4 uncached forecasts are in progress. Cached and reused answers are unaffected. The numbers 3 and 5 s are a first estimate: to be measured on the hosted instance after deploy (G8).
- **Source:** recorded (live measurements 2026-11-04; `api/app/services/forecasting.py`, `api/tests/test_isolation.py`).

## D30. Hosted forecast settings: FORECAST_QUEUE=1, FORECAST_WAIT_SECONDS=10
- **What:** On the Render service, as environment variables: `FORECAST_QUEUE=1` (one fitting plus one preparing) and `FORECAST_WAIT_SECONDS=10` (down from 3 and 20). The code defaults are unchanged.
- **Why:** Measured live (`brain/13`): the 16-forecast burst takes 40 s instead of 49 s, 14 of 16 settle within about 13 s, and the 20-worker test answers 187 of 280 instead of 178, still with no timeouts.
- **Alternatives:** The code defaults (3 and 20). A lower global cap (4 was worse than 8, D26).
- **Consequence:** More uncached forecasts are refused early under load (with a retry hint); cached ones are never affected. If the service is rebuilt from `render.yaml`, these two variables must be set again (or added to `render.yaml`).
- **Source:** recorded (owner set the variables; measured 2026-11-05).

