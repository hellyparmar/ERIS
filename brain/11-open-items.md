# Open items

Things that are known, unresolved, or waiting on the owner. Each has a reason and a suggested next step.

## Waiting on the owner

### H1. Verify the hosts (resolved 2026-11-03)
- **Blocked from the build environment.** The sandbox's network policy refuses `eris-tvro.onrender.com` and the Vercel site (HTTP 403). To allow them: in the session's cloud environment settings, Network access → Allowed domains, add both hosts (keep package managers ticked). Docs: https://code.claude.com/docs/en/cloud-environments#network-access
- **Then the check runs from anywhere:** `python3 scripts/verify_deployment.py https://eris-tvro.onrender.com --web https://<your-site>.vercel.app` (signs in with the public demo account; prints PASS/FAIL per check).
- **Also confirm on the hosts:** Render `ENVIRONMENT=production` and `REFRESH_COOKIE_SAMESITE=none`; `CORS_ORIGINS` set to the Vercel address only; Vercel `VITE_API_URL` starts with `https://`.
- **Evidence from the build environment:** the same script passed 24 of 25 checks against a local HTTPS production-mode server (self-signed certificate trusted with `--ca`). The one failure, the platform's plain-HTTP redirect, needs the live host.
- **Check made 2026-10-27 (live hosts):** `eris-retail.vercel.app` is reachable (HTTP 200) but serves an **older build**: the security headers from `vercel.json` are absent and an inline script is still in the page. Production is built from `main`, which does not yet contain the hardening (PR #33 is open). `eris-tvro.onrender.com` is still unreachable (HTTP 000). The branch's Vercel preview returned 403 from this environment, so it could not be checked either.
- **Resolved 2026-11-03:** both hosts are reachable from the build environment; PR #33 and PR #43 are merged to `main`; `REFRESH_COOKIE_SAMESITE=none` is live on Render. `verify_deployment.py` passes 24 of 24 against the live API and the Vercel site (`brain/13`, "Live check findings"). Cross-site cookies (H2) are the reason the `none` setting is needed.

### H2. Cross-site cookies (decision for the owner)
- Browsers that block third-party cookies end the session on reload when the web app (Vercel) and the API (Render) are on different sites. Option: make them the same site (a custom domain for both, or Vercel rewrites `/api/*` to Render). That also lets `SameSite=lax` apply. Trade-off: behind a rewrite, every request reaches the API from Vercel's address, so per-address limits depend on forwarded headers being trusted; that needs checking on the live host. Not changed here.

### S1. Rotate the credentials exposed in public history (open, high)
- **Issue:** A real database password (commit `18e7012`) and a Supabase project's keys (commit `b86cc36`) are in a public repository's history. Full detail and the owner actions are in `12-security-incident.md`.
- **Next step:** The owner rotates or deletes the hosted project, checks Render's `JWT_SECRET_KEY`, and enables secret scanning. History is not to be rewritten without the owner's approval.

### O1. Commit attribution lines (decided)
- **Decision (D19):** Future commits use the neutral trailer `Co-Authored-By: Claude <noreply@anthropic.com>` and the `Claude-Session:` line. No model names in commits, PR text or repo files. Earlier commits keep their existing trailers; history is not rewritten.
- **Status:** Applied from commit `9118970` onward and written into `CLAUDE.md`.
- **Open:** The owner may still choose a different trailer; if so, change `CLAUDE.md` and D19 together.

### O2. Standing rule in every session (resolved)
- **Decision:** A `CLAUDE.md` at the repository root points to `brain/README.md` and states the rule, so each session reads it first.

### O3. Commit the brain folder (resolved)
- **Done:** Committed and pushed to `claude/loving-wright-326xam` as `9118970`. No pull request opened.

### O4. Set `DEMO_SHIFT_DATES=false` on the hosted API (resolved)
- **Done:** The owner confirmed it is set on the hosted API. `render.yaml` also sets it, so a fresh blueprint deploy keeps it. Without it the hosted assistant becomes slow again (D10, 06).
- **Keep in mind:** Re-check this after any change to the Render service, or if the service is recreated by hand.

### O5. Fraunces was added and then removed (resolved: Geist)
- **Decision:** Geist is the final typeface. Fraunces is no longer in the code: no import, no font package, no CSS reference. The styles define one family, Geist, with Geist Mono for figures (`web/src/styles.css`, `main.jsx`).
- **Why this is recorded:** The screenshots, the README and the shipped app all use Geist. Reintroducing a serif would be a new decision, not a restoration.

### G7. Sales export is the slow path under concurrent load (decided 2026-11-04: D25; adopted: explicit escaping, about 7 to 8 % faster)
- **Measured:** 40 concurrent workers: p50 11.4 s, p95 12.8 s, and 70 of 100 export requests answered 503 (`brain/13`, "Load check").
- **Investigated 2026-11-03 (`brain/13`):** one export is about 0.3 s of work; the wait is queueing for two export slots on a CPU-limited host. The leaner writer saves 15 to 25 %; not adopted (small gain, touches the escaping path). Owner decision needed: more CPU or export slots for the hosted instance, or an export that runs as a background job and is downloaded when ready.

## Discrepancies to fix

### O6. Forecast evaluation scope: 25 series vs 20
- **Issue:** The README and `08` quote the 25-series study. The Model comparison screenshot shows 20 series, from the in-app `store_evaluation` run.
- **Impact:** Both are correct for their scope, but a reader can see two different numbers and think one is wrong.
- **Next step:** Label each figure with its scope, or make the in-app run use the same 25 series.

### O7. Test counts across documents
- **Checked:** `pytest --collect-only` gives 120, which matches `AUDIT.md` and the README. Older commit messages quote 117 and 110, which were correct at their dates.
- **Next step:** When the count changes, update the README, AUDIT.md and `10-testing.md` in the same change.

### O8. The E2E count (resolved)
- **Checked 2026-11-03:** 15 end-to-end tests in `e2e/tests`; all pass locally with Playwright 1.56.1. Earlier notes said 14, and the commit fc09565 message said 13 at that time. The count is not quoted elsewhere in the brain.

### O9. Some reasons are reconstructed
- **Issue:** Decisions D1, D4, D5, D15 and parts of D6 have reasons that were not written at the time. `02-decisions.md` marks them *reconstructed*.
- **Next step:** When the owner gives a reason, record it and mark the source as *recorded*.

## Known gaps in the product

### G1. Filtered lists still take about a second on the smallest host (06).
### G2. First assistant answer for a new question takes a few seconds (06, 07).
### G3. Assistant phrasing from the optional LLM is not evaluated the way the templates are (07).
### G4. Forecasts for new dishes and new outlets are weak until history builds up (08).
### G5. Rainfall is an association, not a proven cause (08). Keep the label.
### G6. Anomaly precision is 0.64. About a third of flagged outlet-days are not injected anomalies (08).

## Cleanup candidates
- `api/data/eris.db` (about 145 MB) is a local demo database. Check whether it is ignored by git before any commit (it is not in the commit list).
- `.ruff_cache/` is local tooling output. Confirm it is ignored.
- Era 0 and Era 1 code is only in git history. Nothing else refers to it.

### I1. Obsolete planning issues (closed 2026-11-03)
- Twelve open issues (#1–#12, "1 1 PostgreSQL Setup" to "5 2 Deployment Checklist") were the planning tasks of the earlier product, created 15 February 2026. That product was retired and removed from the repository in October 2026, so the issues were closed as not planned, each with a note saying so. No open issues remain.

### I2. Dependabot PRs that need a decision (default chosen 2026-11-03, D23; owner to confirm)
- **Issue:** Dependabot PRs [#42](https://github.com/hellyparmar/ERIS/pull/42) (pip group, 48 updates) and [#35](https://github.com/hellyparmar/ERIS/pull/35) (Docker base `python:3.11-slim` → `3.15-slim`) fail or change the runtime. #42 moves the constraint to `numpy==2.5.4`, which has no wheel for Python 3.11, so the `api` job cannot install. The CI and the Docker image run Python 3.11. The other Dependabot PRs ([#36](https://github.com/hellyparmar/ERIS/pull/36)–[#41](https://github.com/hellyparmar/ERIS/pull/41), [#37](https://github.com/hellyparmar/ERIS/pull/37) Playwright 1.64.1 and the GitHub Actions major bumps, [#17](https://github.com/hellyparmar/ERIS/pull/17) Node 26) run on bases from before the 2026-11-03 fixes and need a rebase before they are judged.
- **Default applied (D23):** Python stays on 3.11; `dependabot.yml` ignores numpy 2.5+ and Python 3.12+. Open PRs #42 and #35 still need closing.
- **Next step (owner):** Confirm D23, or choose a runtime: stay on Python 3.11 and pin numpy to 2.4.x (close #42's numpy bump), or move the runtime to 3.12+ with the full suite re-run. Then rebase the rest. Nothing was merged or pushed to these branches.

### I3. Refresh hosted demo: resolved 2026-11-03 (the hook secret works)
- **Issue:** The scheduled workflow `refresh-demo.yml` calls the Render deploy hook from the secret `RENDER_DEPLOY_HOOK_URL`. It has failed with exit code 22 since 12 October, which points to an old hook URL.
- **Resolved:** the scheduled run of 2026-11-02 (run 4) logged "Rebuild requested." The secret was replaced after the failure of 2026-10-25 (run 3). The job runs on `ubuntu-24.04` since D22's follow-up.
- **Earlier steps (kept for reference):** In Render, open the `eris` service and copy the current Deploy Hook URL into the GitHub secret `RENDER_DEPLOY_HOOK_URL` (or delete the secret if the demo is refreshed by the Render auto-deploy instead). Then run the workflow once from the Actions tab.

### I4. Dependabot PRs #42 and #35 closed (2026-11-04)
- Closed without a comment: a closing comment would need the attribution footer the environment adds, which conflicts with the owner's request. The reason is in D23 and this entry.
- Reopen only if the runtime moves (D23 holds the rules in `.github/dependabot.yml`).

### I5. Claude trailers on 79 older commits of main (decided 2026-11-04: leave history)
- New commits and PRs are clean from now on (CLAUDE.md, D19). Older history is not rewritten, since that changes every commit SHA on the public default branch and needs a force-push.

### I6. Hosted instance hours (watch)
- The keep-warm ping (D24) runs one free instance all month. If another free service is added to the account, the total exceeds the free hours. Check the Render usage page after adding any service.
