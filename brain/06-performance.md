# Performance

## The problem
The hosted demo runs on a 0.1-CPU server. Early on:
- Sales and Inventory pages took **minutes** to show data (the user reported this).
- AI assistant replies took **minutes** (the user asked why).
- Default list pages took **3–7 s**.

## Causes found
1. **Date shifting at every start.** An old baked demo was shifted forward on each start. That rewrote every dated row (minutes of CPU, and a held write lock) and invalidated all pre-computed answers. **Fix:** `DEMO_SHIFT_DATES=false` (set in `render.yaml`) skips it. Commit 2c920a2.
2. **Assistant answers recomputed from raw bill lines on every message.** **Fix:** answers are cached by what the question means, the asker and the data version. Suggested questions are stored at build time. Commit 2c920a2.
3. **Lists computed on every request.** **Fix:** a response cache for bills, stock and products, and their default views are prepared at build time (`WARM_URLS`, `WARM_URLS_UNPINNED`). Commit 5a44a72 and 90c91d2.
4. **Missing index on sale time.** **Fix:** `ix_sales_sold_at`, added in migration 0004.
5. **Heavy lookup lists.** The dish and product pickers loaded full records. **Fix:** pickers use a light list (`fields=basic`). Commit 90c91d2.
6. **Forecasts computed inside requests.** **Fix:** forecast fits run in bounded slots and are prepared at build time (D7).

## Design choices behind the fixes
- **Content-keyed caches (D11).** A cache keyed by time returns stale numbers after an import. Keying by the content of the question and the data version is correct by construction.
- **Build-time warming.** The demo is an artefact. Work that depends only on the baked data is done once, in the build, not on each visit.
- **Fast refusal over slow waiting.** When forecasts are busy, the API returns 503 with `Retry-After` in well under a second, rather than holding a request thread (D7).

## Measurements

| What | Before | After | Measured |
|---|---|---|---|
| Default lists (bills, stock, menu) | 3–7 s | 0.1–0.4 s | 0.1-CPU host, 90c91d2 |
| Filtered lists | — | about 1 s | same |
| Suggested assistant questions | 20–55 s | 0.4 s | 2c920a2 |
| Other assistant questions | — | 4–6 s first time, then 0.4 s | 2c920a2 |

Measurements are from the commit messages. They were not re-run for this note.

## Known remaining costs
- Filtered lists still take about a second on the smallest host.
- The first assistant answer for a new question takes a few seconds, because it is not cached yet.
- Forecasts for a new scope are computed on demand and can wait for a slot.
