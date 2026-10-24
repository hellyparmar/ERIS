# Open items

Things that are known, unresolved, or waiting on the owner. Each has a reason and a suggested next step.

## Waiting on the owner

### O1. Commit attribution lines (decided)
- **Decision (D19):** Future commits use the neutral trailer `Co-Authored-By: Claude <noreply@anthropic.com>` and the `Claude-Session:` line. No model names in commits, PR text or repo files. Earlier commits keep their existing trailers; history is not rewritten.
- **Status:** Applied from commit `9118970` onward and written into `CLAUDE.md`.
- **Open:** The owner may still choose a different trailer; if so, change `CLAUDE.md` and D19 together.

### O2. Standing rule in every session (resolved)
- **Decision:** A `CLAUDE.md` at the repository root points to `brain/README.md` and states the rule, so each session reads it first.

### O3. Commit the brain folder (resolved)
- **Done:** Committed and pushed to `claude/loving-wright-326xam` as `9118970`. No pull request opened.

### O4. Set `DEMO_SHIFT_DATES=false` on the hosted API
- **Issue:** `render.yaml` sets it, but if the Render service was not created from the blueprint, the variable must be set by hand. Without it, the hosted assistant is slow again (D10, 06).
- **Next step:** Check the Render environment variables.

### O5. Fraunces was added and then removed
- **Issue:** The serif title font was added (4b2ad6f) and removed (8be81c2). Reason for the reversal is only partly recorded (D15).
- **Next step:** The owner confirms Geist is the intended final choice, or asks for the serif again.

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
