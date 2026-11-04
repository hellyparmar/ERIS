# Timeline

All non-merge commits on this branch, oldest first, grouped by era. Dates are commit dates. "PR #n" marks a merge
commit on the GitHub pull request of that number.

Three eras are visible in the history:

- **Era 0 (Feb–Mar 2026): an earlier product.** Phased POS, billing and compliance work. Removed in full on
  2026-10-01. Its history is kept, its code is not in the working tree.
- **Era 1 (June 2026): a UI pass on that earlier product.** Superseded by the rebuild.
- **Era 2 (2026-10-01 onward): ERIS.** The current product, the Enterprise Retail Intelligence System, demonstrated on a restaurant chain.

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

### 2026-11-03: CI failure in two import tests fixed (date of the sample row)

**What changed**
- `api/tests/test_isolation.py`, `_sample_row`: the sample sale is dated yesterday in the business time zone (`clock.today() - 1 day`), not the latest seeded sale date.

**Why this approach**
- CI runs 165 (`db77a14`) and 166 (`748e59c`) failed `api` and `api-postgres` in two tests of `test_isolation.py`. Run 164 (`efb828d`) had passed on the same code.
- Reproduced locally in the full suite, not in the single file. The importer's error for the sample row: "Sale date/time cannot be in the future" (`created` = 0).
- Cause: the sample date was the latest seeded sale date. The conftest seeds that data ending on `date.today()` in the runner's UTC clock, while the app's business clock is Asia/Kolkata. Near midnight in India the seeded data can reach the business "today", and the row is then refused as future.
- Fix: yesterday on the business clock is always in the past and after the outlets opened, and the importer's own sample generator uses the same rule.

**Alternatives considered**
- Retry the tests: rejected; the failure is deterministic near midnight IST, not random.
- Change the seed to use the business clock: a larger change to test setup; left for later.

**Trade-offs and risks**
- The test now depends on the business clock, as the importer does. If the organization's time zone changes, the test follows it.

**Decision record**
- No new decision. Topic file: `brain/10-testing.md`.

**Verification (as run)**
- Full API suite locally: `pytest -q` → 152 passed (before the fix: 150 passed, 2 failed in the same two tests).
- `ruff check app tests`: passed.
- CI on the fix: pending at the time of writing (see the next entry).

### 2026-11-04: Admission control for the hosted instance (D26); live heavy-load result

**Request (as given):** the stop-hook goal: the pipelines must not break under heavy traffic on the deployed system; measure it.

**What changed**
- `api/app/hardening.py`: `HardeningMiddleware` admits at most `MAX_INFLIGHT_REQUESTS` requests at once; a request waiting more than `INFLIGHT_WAIT_SECONDS` gets 503 with `Retry-After: 2`. Health checks skip the queue.
- `api/app/config.py`: `MAX_INFLIGHT_REQUESTS = 8`, `INFLIGHT_WAIT_SECONDS = 5.0`.
- `api/tests/test_admission.py`: 3 tests.
- `brain/02` (D26), `brain/10`, `brain/11` (G8), `brain/13`.

**Why this approach**
- The live heavy test (20 workers, 280 requests) gave 34 client timeouts with no server error: the server held requests past any client's patience. Bounding the total in progress and refusing with a retry hint is the D20 design.

**Alternatives considered:** see D26.

**Trade-offs and risks**
- Under heavy load, some requests now get 503 instead of an answer. The values 8 and 5 are a first estimate and are not measured on the hosted host yet.

**Decision record:** D26 in `02-decisions.md`. Source: recorded (live and local load tests).

**Verification (as run)**
- `pytest -q` (API): 156 passed, including the 3 new tests. `ruff check app tests`: passed.
- Local server, defaults, 20 workers × 200 requests: 200 × 200.
- Live, before the change, 20 workers × 280 requests: 219 × 200, 27 × 503, 34 timeouts, no 5xx.
- Not yet run on the hosted instance (needs the merge).

### 2026-11-04: PR #46 merged; keep-warm verified; sales export adopted with explicit escaping

**Request (as given):** "approve PR 46 and merge it"; "adopt the leaner export writer (15–25% faster, identical output)".

**What changed**
- `api/app/routers/common.py`: `csv_response(..., escape=True)`; `escape=False` skips the per-cell check.
- `api/app/routers/sales.py`: the sales export escapes its text cells itself and passes `escape=False`.
- `api/tests/test_api.py`: `test_sales_export_neutralises_formulas_in_text_cells_only`.
- `brain/02` (D25 rewritten), `brain/10`, `brain/11` (G7), `brain/13`.

**Why this approach**
- The owner asked for the leaner writer. The version used for the earlier estimate skipped escaping on most text cells; the adopted version escapes every text cell, so the formula protection is unchanged.
- Measured speed-up is about 7 to 8 %, not 15 to 25 %. Stated as measured.

**Alternatives considered**
- Keep the unsafe variant for the 15 to 25 %: rejected (formula injection through customer names).

**Trade-offs and risks**
- The escaping for the sales export is now in the endpoint, not in the shared helper. A future export that forgets to escape would be unprotected. The test covers the sales export only.

**Decision record**
- D25 rewritten in `02`. Source: recorded (owner's answer; measured).

**Verification (as run)**
- Baseline and after, same database, same endpoint and window: `cmp` identical (7,426,974 bytes, 76,369 lines).
- Timing: before 1.031 s best / 1.064 s median; after 0.962 s / 0.981 s.
- `pytest -q` (API): 153 passed (152 before, plus the new test). `ruff check app tests`: passed.
- PR #46: approval refused by GitHub (the author cannot approve their own PR); the merge then succeeded (`55132f8`).
- Keep-warm: manual run on `main` returned `200` in 34.4 s (cold instance).

### 2026-11-04: Keep-warm ping for the hosted API; Dependabot #42 and #35 closed; decisions on export and history

**Request (as given):** The owner's answers to four open questions: export under load (keep as is), keep the hosted instance warm (scheduled ping), close Dependabot #42 and #35, leave the history on main as it is.

**What changed**
- `.github/workflows/keep-warm.yml`: new; pings `https://eris-tvro.onrender.com/api/health` every 10 minutes; `permissions: {}`.
- Dependabot PRs #42 and #35: closed (no comment).
- `brain/02-decisions.md`: D24 (keep-warm), D25 (export stays).
- `brain/11-open-items.md`: G7 decided; I4 (PRs closed), I5 (history left), I6 (free hours to watch).

**Why this approach**
- The one slow live request (60 s) was most likely a cold start, so a ping is the cheapest fix that keeps the free plan.
- Export: the measured work is 0.3 s; the wait is queueing. Adding code would not change the picture (D25).

**Alternatives considered**
- Paid always-on plan: costs money; not chosen.
- Closing Dependabot PRs with a comment: a comment would carry the attribution footer the environment adds, which conflicts with the owner's request; closed without comment.

**Trade-offs and risks**
- One free instance running all month uses about 744 of 750 free hours (D24).
- Scheduled runs can be late; the ping is best-effort.

**Decision record**
- D24 and D25 in `02-decisions.md`. Source: recorded (owner's answers).

**Verification (as run)**
- `yaml.safe_load` on `keep-warm.yml`: parses; one job (`ping`), schedule `*/10 * * * *`.
- Dependabot #42 and #35: state `closed` returned by the GitHub API.
- Keep-warm workflow run: see the follow-up entry once it has run.

### 2026-11-03: Live light-load check, port reachability, and the export investigation

**What changed:** `brain/13` (new section), `brain/11` (G7 updated). No application code changed.

**Verification (as run)**
- Live API, 5 workers, 70 requests: 68 × 200, 1 × 503, 1 client timeout at 60 s; no 5xx from the server. Warm requests 0.3 to 0.5 s.
- TCP on the public hostname: 80 and 443 open; 22, 5432, 6379, 8000, 8080 closed or filtered.
- Export profile in-process: about 0.3 s per 30-day export; leaner writer 15 to 25 % faster with byte-identical output; the join-free lookup variant no faster. Not adopted.

**Outcome:** the export is not made materially faster by code on this host; the decision is capacity or a background export (open item G7).

### 2026-11-03: Load check of the request pipelines; live build status

**Request (as given):** Stop-hook goal: "pipeline doesn't break during heavy traffic", and whether the merged build is live.

**What changed**
- `scripts/load_check.py`: new, stdlib-only load check over the heavy endpoints; exits non-zero on a server error.
- `brain/13-hardening-and-pipelines.md`: "Load check (2026-11-03)" with the measured results.
- `brain/11-open-items.md`: G7, the sales export under concurrency.

**Why this approach**
- The goal asked for the pipelines to hold under heavy traffic; the earlier notes had no measurement of that. This run measures it on a local server with the demo data.
- Live build status: `/api/health` reports only the app version, not the commit. Since `af1acc2` no application code changed (`git diff --stat af1acc2 f97b319 -- api/app web/src` is empty); PR #44 changed CI, tests, docs and the verification script. So the live check (24 of 24) still describes the running application code.

**Alternatives considered**
- Load-test the hosted free instance: not done; it is a shared resource, and a test there would be unannounced load on production.

**Trade-offs and risks**
- One machine, one shape of load. Not a capacity figure for the hosted host.

**Decision record**
- No new decision.

**Verification (as run)**
- Local server, 40 workers × 700 requests: 630 × 200, 70 × 503; zero 500s or exceptions; server log without errors.
- Forecast cap: 429 from request 18 of 150, `Retry-After: 4`.
- `ruff check scripts/load_check.py`: passed (the script is not in CI's lint scope).
- Live check: `verify_deployment.py` 24 of 24 (run earlier on this tree; the application code is unchanged since).

**Follow-ups**
- G7: the export is the slow path under load.
- Dependabot #42 and #35 still open (owner decision).
- Older `main` commits still carry Claude trailers (owner chose not to rewrite them).

### 2026-11-03: Attribution removed from new commits and the rule; six branch commits rewritten

**Request (as given):** "make sure nothing like co-authored with claude or claude's name in doing all these appear in github repo or anywhere where other ppl get to know this project". Choices given by the owner: rewrite only this branch's six unmerged commits; keep the mentions in the files.

**What changed**
- The six unmerged commits on this branch (`6f17eac` to `efb828d`, now `67a8328` to `db77a14`): the `Co-Authored-By: Claude` and `Claude-Session` lines were removed from their messages. No file content changed.
- `CLAUDE.md`, "Commits": the trailer rule now says no attribution trailers or footers.
- `brain/02-decisions.md`: D19 replaced with the new rule; the earlier version is noted as superseded.

**Why this approach**
- The six commits are not on `main`, so rewriting them changes nothing public that others have seen; the rewrite was done with `git filter-branch` on `origin/main..HEAD`, and the tree hash was checked before and after (identical: `62027ed`).
- The older 79 commits on `main` were not rewritten: that changes every SHA on the public default branch and needs the owner's explicit choice.

**Alternatives considered**
- Rewrite all 85 commits and force-push `main`: not chosen by the owner; blocked in practice by the `main` protection and it breaks links to commits.
- Keep the trailers and only stop adding them: rejected by the owner's request for the branch.

**Trade-offs and risks**
- `main` still shows the trailers on 79 older commits and in the four files that mention Claude (`CLAUDE.md`, brain notes). Anyone reading the history can still see them.
- The force-push replaced `efb828d`. A local backup branch `backup/pre-attribution-rewrite` keeps the old tip; it is local only.

**Decision record**
- D19 in `02-decisions.md` (superseded wording kept in the entry). Source: recorded (owner's request).

**Verification (as run)**
- `git rev-parse HEAD^{tree}` before and after the rewrite: `62027ed` both; `git log origin/main..HEAD --grep Claude -i`: 0 matches after the rewrite.
- Force-push with `--force-with-lease=claude/loving-wright-326xam:efb828d`: accepted.

**Follow-ups**
- Owner decision: whether to rewrite the 79 older commits on `main` (changes SHAs; needs a `main` branch change).
- CLAUDE.md still names Claude in its title and in the brain-folder rule's text; left as the owner asked.

### 2026-11-03: Refresh hosted demo verified; its runner pinned

**What changed**
- `.github/workflows/refresh-demo.yml`: `runs-on: ubuntu-latest` → `ubuntu-24.04`, as in D22.

**Why this approach**
- The open item "stale RENDER_DEPLOY_HOOK_URL" was wrong. The scheduled run of 2026-11-02 (run 4) logged "Rebuild requested.", so the secret works. Run 3 (2026-10-25) was the last failure.
- The job still ran on `ubuntu-26.04`; pinning it matches the other workflows.

**Verification (as run)**
- GitHub API: runs 3 (failure, 2026-10-25) and 4 (success, 2026-11-02) of the workflow; job log of run 4 read.
- `yaml.safe_load` on `refresh-demo.yml`: parses.

### 2026-11-03: Dependabot held to Python 3.11 (D23)

**Request (as given):** Stop-hook goal, pipeline items still open: the Dependabot PRs (#42, #35) blocked by the runtime decision.

**What changed**
- `.github/dependabot.yml`: pip ignores `numpy` `>=2.5`; docker ignores `python` `>=3.12`.

**Why this approach**
- The tested runtime is 3.11 (CI, Dockerfile). numpy 2.5 has no 3.11 wheel, so the pip group fails at install (PR #42, run log: "no matching distributions available").
- A rule keeps the next monthly run from proposing the same breaking bump, without touching the open PRs.

**Alternatives considered**
- Move to 3.12+ now: a runtime change that needs the full suite and Render re-verified; not done without the owner.

**Trade-offs and risks**
- Two open PRs (#42, #35) remain until closed. The rule is not a substitute for closing them.
- The owner has not answered the runtime question; D23 is the default and can be overruled.

**Decision record**
- D23 in `02-decisions.md`. Source: recorded as a default, pending owner confirmation.

**Verification (as run)**
- `yaml.safe_load` on `dependabot.yml`: parses; both ignore rules present.

**Follow-ups**
- Close #42 and #35 (owner or Claude on request) once the rule is confirmed.
- Refresh hosted demo secret: owner action (I3).

### 2026-11-03: CI e2e job fixed by pinning the runner; live check 24 of 24

**Request (as given):** Stop-hook goal: check dead code, old redirects, open ports, pipelines under heavy traffic, optimise the pipelines, encrypt and secure the connectivity to the backend, and verify on the deployed system. The unresolved items named were the live SameSite check, the failing CI run on 6f17eac, the red Dependabot PRs and the failing Refresh hosted demo job.

**What changed**
- `.github/workflows/ci.yml`: every job `runs-on: ubuntu-latest` → `ubuntu-24.04` (five jobs).

**Why this approach**
- CI run 159 on 6f17eac failed in the `e2e` job only. `npx playwright install --with-deps chromium` stopped with "Playwright does not support chromium on ubuntu26.04-x64": `ubuntu-latest` now resolves to Ubuntu 26.04, and the pinned `@playwright/test` 1.56.1 does not support it. The api, api-postgres, web and docker jobs passed on the same commit, so the break is in the runner image, not the code.
- Pinning to 24.04, which Playwright 1.56.1 supports, fixes it without a Playwright upgrade. A fixed image also stops a future runner change from breaking the pipeline without notice (D22).
- The live SameSite item is closed: the owner set `REFRESH_COOKIE_SAMESITE=none` on Render, and the live check now passes.

**Alternatives considered**
- Upgrade Playwright to 1.64.1 (Dependabot #37): a version change with its own risk. Kept for its own PR.
- Pin only the e2e job: leaves the jobs on different images. Rejected.

**Trade-offs and risks**
- The pin is a deliberate maintenance point: GitHub will retire 24.04, and the image must be moved on purpose, with the Playwright version checked. It would show as a red `e2e` job again.

**Decision record**
- New decision D22 in `02-decisions.md`. Source: recorded (CI log of run 41688702034).

**Verification (as run)**
- `yaml.safe_load` on `ci.yml`: parses; jobs `api`, `api-postgres`, `web`, `docker`, `e2e`.
- Local e2e: `npm run build` in `web`, then `npx playwright test` in `e2e` with Playwright 1.56.1 and the pre-installed Chromium, against the API on SQLite: **15 passed** (2.1 min). Earlier notes said 14; the suite has 15 tests.
- `ruff check app tests`: passed. `pytest -q` in `api`: **152 passed**.
- CI on `0a73cf6` (run 41692003425, https://github.com/hellyparmar/ERIS/actions/runs/41692003425): **all five jobs passed** on `ubuntu-24.04` (api, api-postgres, web, docker, e2e).
- Live: `python3 scripts/verify_deployment.py https://eris-tvro.onrender.com --web https://eris-retail.vercel.app`: **24 of 24 passed**, including `SameSite=None` on both session cookies, the HTTP-to-HTTPS 301 and the hardened Vercel build (CSP, no inline scripts).

**Follow-ups**
- Dependabot #42 (pip group) fails in the `api` job: it moves the constraint to `numpy==2.5.4`, which has no wheel for Python 3.11, the CI and Docker runtime. Needs a decision (stay on 2.4.6, or move the runtime). Open item I2.
- Dependabot #35 moves the Docker base to Python 3.15; the tested runtime is 3.11. Open item I2.
- Dependabot branches predate the fixes on `main`; rebase them before judging their results.
- Refresh hosted demo still fails (exit 22): `RENDER_DEPLOY_HOOK_URL` is stale. Owner action; open item I3.

### 2026-11-03: PR #43 merged; live check 23 of 25

- PR #43 merged to `main` (af1acc2). Render serves the new build (security headers present).
- Live check: 23 of 25 passed. The application-level redirect check is local-only (the platform proxy overrides the header). Open: the live cookies are `SameSite=lax`; `REFRESH_COOKIE_SAMESITE` must be set to `none` in Render's environment for the Vercel site's sign-in to work (owner action).

### 2026-11-03: cause of the failed Render deploy of 8213593, and the fix

- Render's log for the failed deploy (owner-provided): the app started ("Started server process", "Waiting for application startup", migrations), but Render's port scan timed out before "Application startup complete" and "Uvicorn running" appeared. The app answered health checks with 200 only after that. Uvicorn runs the application's start-up code before it opens the port, so the start-up work exceeded Render's port-scan window.
- Fix (branch, not yet on `main`): in production the start-up work (migrations and the demo-data check) runs in a background thread, so the port opens within about a second. Until it finishes, the health check returns 200 with status "starting" and API calls answer 503 with Retry-After. If start-up fails, the health check returns 503 so a broken deploy is not put into service. Development and tests keep the synchronous start.
- Verified: 152 API tests pass (4 new in `tests/test_startup.py`); lint passes; the production start with the Dockerfile's exact command on port 10000 answers in about 1 s with "starting", then "ok" once start-up finishes.
- Still to do: merge to `main` (deploys to production; needs the owner's approval), then a Render deploy and `scripts/verify_deployment.py`.

### 2026-11-03: Render deploy of 8213593 failed its health check

- The owner reports Render's deploy of `8213593` (PR #34) failed: "Timed out after waiting for internal health check ... eris-tvro.onrender.com:10000/api/health" (27 Oct, 11:58 PM). Earlier Render deploys (`8615f2e`) succeeded, and CI on `8213593` passed, including the Docker smoke test.
- Startup code reviewed (`api/app/main.py` `_bootstrap`): migrations run, then the app returns at once when the database already has users, so the health check should not wait on seeding. The health path is exempt from the HTTPS redirect.
- Root cause not yet identified: it needs Render's log for the failed deploy. The sandbox could not reproduce the container (its Python no longer has the app's packages).
- Next: owner shares the Render log lines from the failed deploy; fix it on a branch and deploy it; then run `scripts/verify_deployment.py`.

### 2026-10-27: PR #34 merged; CI green on main; Render still on the previous build

- Owner approved. PR #34 (fix to the container start command and the web lint error) merged to `main` as `8213593`.
- CI on `main` for `8213593`: all jobs passed (including `docker`, which had failed before).
- Vercel production serves the new build (CSP present).
- Render's `/api/health` still returns the previous build's response (no `x-content-type-options`, no HSTS from the app). No deployment status is reported to GitHub for Render, so the Render deploy state could not be read from here. The live check (`scripts/verify_deployment.py`) is still to run against Render. Owner action: check the `eris` service's Events in Render and trigger a manual deploy of the latest commit if none is running.

### 2026-10-27: PR #33 merged; CI on main failed; start command fixed

- PR #33 merged to `main` (357279e) at the owner's request. Vercel production now serves the hardened web build (CSP present).
- CI on the merge failed in two jobs. `web`: an empty `catch` in `web/public/theme-init.js`. `docker`: the container start command left `*` unquoted in `--forwarded-allow-ips ${FORWARDED_ALLOW_IPS:-*}`; the shell expanded it into the file names of the working directory, so uvicorn received wrong arguments and the container exited. The same build on Render failed, so Render kept the previous version.
- Fixed on the working branch: the wildcard is quoted, and the start command was tested to pass exactly the intended arguments; the empty `catch` now carries a comment. Lint and the web build pass locally. Not yet merged to `main` (a new merge deploys to production; awaiting the owner's approval).

### 2026-10-27: live check (partial)

- `eris-retail.vercel.app` reachable; serves an older build from `main` (no `vercel.json` security headers, inline script present). Hardening is not in production until PR #33 is merged.
- `eris-tvro.onrender.com` unreachable (HTTP 000). Branch preview returned 403.
- No merge made: merging deploys to production and needs the owner's approval.

### 2026-10-27: no session token readable by the page; deployment check script

- **Access token out of the page too:** `eris_access` (HTTP-only, path `/api`) joins the refresh cookie; the browser body carries no token. Changing cookie-authenticated requests need `X-ERIS-Client: web` (403 without it). Decision D21 updated.
- **Model server in production:** only `https://` is accepted (loopback no longer exempt), so production has no unencrypted model traffic.
- **Deployment check:** `scripts/verify_deployment.py` passed 24 of 25 against a local HTTPS production-mode server; the live hosts remain to be checked (H1, needs the owner to allow the hosts in the environment's network settings).
- **Tests:** API 148; e2e 15 (renewal after a 401; reload keeps the session; tokens HTTP-only).

### 2026-10-27: browser sessions and model-server transport

- **Refresh token out of the browser:** sign-in and refresh set it as an HTTP-only, Secure cookie (`SameSite=none` on Render). The access token is kept in memory. Old `localStorage` tokens are removed on start. Decision D21.
- **Forged cookie requests:** refresh and logout require `X-ERIS-Client: web` when the cookie is present.
- **Model server:** a plain-HTTP Ollama address outside this machine is refused in production.
- **Tests:** API 145 (new: browser cookie flow, Ollama transport); e2e 15 (renewal from the cookie after a 401; reload keeps the session and stores no token).
- **Not done:** host checks (H1), blocked from this environment. A verification script (`scripts/verify_deployment.py`) is in the repository for a run on the live hosts; against a local HTTPS production-mode server it passed 22 of 23 checks (the 23rd is the platform redirect that needs the live host).

### 2026-10-27: goal review (dead code, ports, security, pipelines)

- **Dead code removed:** `STATE_CODE_BY_NAME`, `create_tables()`, six unused constants in `models.py`, and the unused `extra` field of `SaleInput`. Other `vulture` hits reviewed as false positives (see `13`).
- **Links:** no broken relative links; no old host references in code or docs.
- **Ports and exposure:** compose publishes the API on `127.0.0.1` only; required secrets for the JWT and the database password; Postgres and Ollama stay unpublished.
- **Security:** headers on every response; CSP and HSTS; HTTPS redirect in production; TLS to PostgreSQL in production; inline theme script moved to a file; uvicorn trusts forwarded headers so limits see real addresses.
- **Pipelines:** database pool sized to the thread pool, with 503 when saturated (was 500 after 30 s); export gate; single flight for cached answers; per-address rate limits; body size ceiling. Load test (25 users): no 5xx except deliberate 503s, dashboard p50 13 s → 0.07 s. Recorded in `13`, decision D20.
- **Tests:** API 120 → 137 (new: hardening, capacity, transport); e2e 14 passed under the new policy; lint and build clean.
- **Found and fixed in the process:** the export wrap first removed the code after each handler (caught by the test suite; restored and redone).

### 2026-10-24 entry: name, verification, security review

- **Name:** the product is now called **Enterprise Retail Intelligence System** everywhere it appears: the README title, the sidebar brand, the page title, and the brain. The dataset stays one restaurant chain (Saffron Table) with five outlets by default.
- **Causal analysis and RAG:** kept. Checked in the code (`services/drivers.py`, `services/assistant/knowledge.py`, `docs/knowledge/`). Full API suite re-run: 120 passed; Ruff clean. Relevant tests: `test_revenue_drivers_add_up`, `test_how_to_questions_are_answered_from_the_docs`, `test_how_it_works_questions_use_documentation`.
- **Screenshots:** regenerated on the scratch demo so the sidebar shows the new name.
- **Credentials:** full scan of the tree and all history. Current tree clean. Two real exposures in history (commits `18e7012` and `b86cc36`), recorded in `12-security-incident.md`. Rotation is open and needs the owner.
- **Brain:** new file 12; open item S1 added.
- **2026-10-24 (Render, owner check):** `JWT_SECRET_KEY` is the generated value. `DEMO_SHIFT_DATES` is missing from the dashboard (open: set it to false). `SEED_DEMO_DATA` is false in the dashboard but true in `render.yaml` (mismatch recorded in `12`).
- **2026-10-24:** Render's last live deploy before this check was `788bf2b` (2026-10-06). A deploy of `8615f2e` (PR #32) was started by the owner after the `DEMO_SHIFT_DATES` change. Recorded in `09`.
- **2026-10-26:** `.gitignore` extended to cover credential files, SSH and cloud CLI state folders, and Terraform state. Tested with `git check-ignore`; `api/.env.example` stays tracked. Recorded in `09`.
- **2026-10-26:** The weekly `refresh-demo.yml` workflow has failed on every scheduled run since 2026-10-12 (exit code 22: the Render deploy hook is rejected). Cause and owner fix recorded in `09`. Not fixed from this repository, because the hook URL is a GitHub secret.
- **2026-10-24 (later):** GitHub settings confirmed through the API: secret scanning and push protection enabled. Browser checks of Render and Supabase were not possible in this session, so S1 stays open for those.

### Brain and repository rules

- **2026-10-24:** Open items closed: `DEMO_SHIFT_DATES=false` confirmed on the hosted API (O4); Geist confirmed as the final typeface and Fraunces confirmed absent from the code (O5, D15).
- **2026-10-24:** `brain/` committed as `9118970`. Trailer convention decided (D19). `CLAUDE.md` added at the repository root to point future sessions to `brain/README.md`.

### Work outside commits

- A model-comparison evaluation was stored in the local demo database used for screenshots. That database is not part of the repository.
