# Open items

Things that are known, unresolved, or waiting on the owner. Each has a reason and a suggested next step.

## Waiting on the owner

### H1. Verify the hosts (open: needs the owner to allow the hosts, then a run)
- **Blocked from the build environment.** The sandbox's network policy refuses `eris-tvro.onrender.com` and the Vercel site (HTTP 403). To allow them: in the session's cloud environment settings, Network access → Allowed domains, add both hosts (keep package managers ticked). Docs: https://code.claude.com/docs/en/cloud-environments#network-access
- **Then the check runs from anywhere:** `python3 scripts/verify_deployment.py https://eris-tvro.onrender.com --web https://<your-site>.vercel.app` (signs in with the public demo account; prints PASS/FAIL per check).
- **Also confirm on the hosts:** Render `ENVIRONMENT=production` and `REFRESH_COOKIE_SAMESITE=none`; `CORS_ORIGINS` set to the Vercel address only; Vercel `VITE_API_URL` starts with `https://`.
- **Evidence from the build environment:** the same script passed 24 of 25 checks against a local HTTPS production-mode server (self-signed certificate trusted with `--ca`). The one failure, the platform's plain-HTTP redirect, needs the live host.
- **Check made 2026-10-27 (live hosts):** `eris-retail.vercel.app` is reachable (HTTP 200) but serves an **older build**: the security headers from `vercel.json` are absent and an inline script is still in the page. Production is built from `main`, which does not yet contain the hardening (PR #33 is open). `eris-tvro.onrender.com` is still unreachable (HTTP 000). The branch's Vercel preview returned 403 from this environment, so it could not be checked either.
- **To complete H1:** (1) allow `eris-tvro.onrender.com` in the environment's network settings; (2) decide whether to merge PR #33 to `main`. Merging deploys the hardened web app to Vercel and, because Render auto-deploys `main`, the API to Render too. That needs the owner's approval; it was not done.

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

## Discrepancies to fix

### O6. Forecast evaluation scope: 25 series vs 20
- **Issue:** The README and `08` quote the 25-series study. The Model comparison screenshot shows 20 series, from the in-app `store_evaluation` run.
- **Impact:** Both are correct for their scope, but a reader can see two different numbers and think one is wrong.
- **Next step:** Label each figure with its scope, or make the in-app run use the same 25 series.

### O7. Test counts across documents
- **Checked:** `pytest --collect-only` gives 120, which matches `AUDIT.md` and the README. Older commit messages quote 117 and 110, which were correct at their dates.
- **Next step:** When the count changes, update the README, AUDIT.md and `10-testing.md` in the same change.

### O8. The E2E count (resolved)
- **Checked:** 14 end-to-end tests in `e2e/tests`, which matches the README. The commit fc09565 message quoted 13 at that time. Nothing to change.

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
