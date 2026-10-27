# Hardening, dead code and pipelines under load

**Recorded:** 2026-10-27. **Scope:** dead code, old links, open ports, security headers and connectivity, and the request pipelines under heavy traffic.

## Dead code

Removed, each after a repository-wide reference check:
- `api/app/services/gst.py`: `STATE_CODE_BY_NAME` (never read).
- `api/app/db.py`: `create_tables()` (no callers; tests use the metadata directly, and migrations run through Alembic).
- `api/app/models.py`: the constants `ROLES`, `SALE_SOURCES`, `ITEM_KINDS`, `SALE_STATUSES`, `PO_STATUSES` and `MOVEMENT_REASONS` (defined, never used). The web app has its own role list in `Help.jsx`.
- `api/app/services/sales.py`: the `extra` field of `SaleInput` (never read). The now-unused `field` import went with it.

Reviewed and kept (false positives from `vulture`, 132 hits at 60% confidence):
- FastAPI route handlers (`@router.get/post/...`) and exception handlers, which the framework calls.
- Pydantic validators (`@field_validator`, `@model_validator`).
- The audit hooks in `services/audit.py`, registered with `@event.listens_for`.
- Model columns (`contact_person`, `payment_terms`, `dataset_id`, ...), which are database fields even when the API does not return them.

The web app: no unused source files; `main.jsx` is the entry point.

## Old redirects and links

- No broken relative links in the README or `docs/`.
- No hard-coded links to the old hosts (`r-dios`). The GitHub homepage was updated by the owner.
- The web app sends unknown paths to `/` (`App.jsx` catch-all). There are no legacy routes to redirect.
- `localhost` appears only in development instructions and defaults.

## Open ports and exposure

| Surface | Before | Now |
|---|---|---|
| Compose: API | published on all interfaces (`8000:8000`) | published on `127.0.0.1` only |
| Compose: database | not published | not published (unchanged) |
| Compose: Ollama | not published | not published (unchanged) |
| Compose: JWT secret | placeholder default | required (`${JWT_SECRET_KEY:?...}`) |
| Compose: database password | fixed `eris:eris` | required (`${POSTGRES_PASSWORD:?...}`) |
| Container | listens on 8000 inside | unchanged; reached only through the platform proxy (Render) |
| Web (Vercel) | no security headers | CSP, HSTS, `nosniff`, `X-Frame-Options: DENY`, referrer and permissions policies |

## Security and connectivity

- **Security headers on every API response:** `nosniff`, `X-Frame-Options: DENY`, a strict referrer policy, a permissions policy, COOP, and a CSP (`default-src 'none'` for JSON). HTML from the app gets the app policy, which allows no inline scripts. `/docs` gets its own policy for Swagger UI.
- **Inline script removed:** the theme script moved from `web/index.html` to `web/public/theme-init.js`, so the policy can block every inline script.
- **HTTPS:** in production, a request that reached the server as plain HTTP through a proxy is redirected (308) to HTTPS. HSTS is sent in production. The health check is exempt, because it runs inside the container over HTTP.
- **Real client addresses:** the container runs uvicorn with `--proxy-headers`. Without it, every request would look like it came from the platform proxy, and one rate-limit bucket would throttle all users together. `FORWARDED_ALLOW_IPS` defaults to `*`, which is safe only while the container is reachable through the platform proxy alone. Set it to the proxy's range where the platform publishes one.
- **Database over TLS:** in production, a PostgreSQL URL without an explicit `sslmode` gets `sslmode=require`. An explicit mode is kept as written.
- **Production JWT secret:** the application refuses to start in production with the development or a short secret (this was already the case, confirmed by reading `main.py`).
- **Login brute force:** the existing per-account lockout (5 failures in 15 minutes) stays. It is now backed by a per-address rate limit.
- **Request size:** bodies over `MAX_BODY_MB` (20 MB) get 413 before they are read. Imports are capped at 15 MB inside the importer.

## Pipelines under heavy traffic

| Pipeline | Failure it could cause | Protection now | Measured (25 concurrent users, 60 s, one 4-CPU host) |
|---|---|---|---|
| Database connections | Requests wait for a connection, then fail with 500 after 30 s | Pool sized to the 40-thread request pool; 10 s pool timeout; saturation answers 503 `Retry-After: 2` | Before: 15 connections, 15 pool timeouts, 500 errors. After: 0 errors |
| Forecast fits | A burst of fits takes the CPU from other pages | `FORECAST_WORKERS` slots; busy answers 503 (existing) | Forecast p50 0.05–0.6 s |
| Exports (CSV, Excel) | Whole files built in memory; a burst slows every page | `EXPORT_WORKERS` (2) gate; a request waiting more than `EXPORT_WAIT_SECONDS` (10 s) gets 503 | Before: 25 client timeouts and 500s. After: 67 served, 72 answered 503 busy, no failures |
| Dashboard and cached pages | Concurrent cache misses each recompute the same answer | Single flight: one computation, the rest reuse it | Dashboard p50 13 s → 0.07 s |
| Sign-in | Credential guessing from one address | Per-address limit `RATE_LIMIT_LOGIN_PER_MINUTE` (60) plus the per-account lockout | Default limits: 429 with `Retry-After` |
| Heavy endpoints (forecast, assistant, imports, exports) | One client takes the server | Per-address limit `RATE_LIMIT_HEAVY_PER_MINUTE` (120) | Default limits: 429 once the budget is spent; ordinary pages unaffected |
| Every API call | Abuse of the whole API | Per-address limit `RATE_LIMIT_API_PER_MINUTE` (1200) | — |
| Assistant | Slow answers under load | Answers cached by meaning and data version (existing); the message is limited to 500 characters | p95 0.7 s at high limits |

Load test: a mixed script (dashboard, sales list, stock list, menu list, forecast, assistant, sales export) run against a server on the demo database. Default limits, with all 25 users behind one address: normal pages p50 0.14–0.16 s; no 5xx other than the deliberate 503s; no tracebacks. The script is kept outside the repository, in the session scratch folder.

## Settings added

| Setting | Default | Meaning |
|---|---|---|
| `RATE_LIMIT_ENABLED` | `true` | Turn all request limits off (the test suite does this) |
| `RATE_LIMIT_API_PER_MINUTE` | 1200 | Per address, every `/api` call |
| `RATE_LIMIT_LOGIN_PER_MINUTE` | 60 | Per address, sign-in attempts |
| `RATE_LIMIT_HEAVY_PER_MINUTE` | 120 | Per address, forecasts, assistant, imports, exports |
| `MAX_BODY_MB` | 20 | Request body ceiling |
| `EXPORT_WORKERS` | 2 | Exports running at once |
| `EXPORT_WAIT_SECONDS` | 10 | How long an export waits for a slot |
| `FORWARDED_ALLOW_IPS` | `*` | Proxy addresses whose forwarded headers are trusted (Dockerfile) |

## Browser sessions and the model server (updated 2026-10-27)

- **No token the page can read.** Sign-in and refresh set two HTTP-only cookies: `eris_access` (path `/api`, lifetime of the access token) and `eris_refresh` (path `/api/auth`, lifetime of the refresh token). Both are `Secure` in production and `SameSite=none` on Render, where the web app is cross-site. The browser sends them; page scripts cannot read them. Neither token appears in any response body for a browser.
- **Forged changes refused.** The web app sends `X-ERIS-Client: web`. A request authenticated by the access cookie that changes data (anything but GET, HEAD or OPTIONS) is refused with 403 without that header, and so is a refresh or logout that carries the refresh cookie without it. A third-party page cannot add the header without a CORS preflight the API refuses for other origins.
- **Session restore.** `web/src/lib/api.js` remembers only whether a session exists. A reload checks it through the refresh cookie. Old `localStorage` tokens are removed on start.
- **API clients unchanged.** A request with an `Authorization` header is authenticated by it, and its login response keeps both tokens in the body (scripts, the CI smoke test).
- **Model server.** In production, every connection to the model server must be `https://`. Plain HTTP is refused even on the same machine, so production has no unencrypted model traffic. The assistant then uses its built-in engine. Development keeps plain `localhost` for a local model.

## Limits of this design (residual risks)

- **Per process:** the rate limits and the single-flight lock live in one process. The container runs one worker, so this holds. With several workers or several instances, move these counters to a shared store (for example Redis).
- **Trusted forwarded headers:** `FORWARDED_ALLOW_IPS=*` trusts any sender. It is safe only behind the platform proxy. Set the proxy's range where the platform publishes one.
- **Access token in memory:** a script running on the page could still use it while the page is open. The refresh token is not reachable from script.
- **Third-party cookies:** browsers that block cross-site cookies (some privacy settings, private windows) will not restore the session after a reload; the user signs in again. Serving the web app and the API from one site (a custom domain for both) removes this.
- **Verify on the hosts:** not verifiable from the build environment. See `11`, H1.
- **SQLite is one writer:** writes queue on a single lock. Under heavy writing, PostgreSQL is the right choice (see `render.yaml` comments).
- **CORS defaults:** the default allowed origins include `localhost`. Production should set `CORS_ORIGINS` to the web app's address only.
- **Verify on the hosts (H1):** the Render service needs `ENVIRONMENT=production` (set in `render.yaml`), and the Vercel build needs `VITE_API_URL` to be an `https://` address. Neither can be checked from the repository.

## How to verify the deployed system

`python3 scripts/verify_deployment.py https://<api host> --web https://<web host>` runs the connectivity and security checks against a live deployment (see `brain/11`, H1). Add `--local --ca <file>` for a test server.

## How to verify

```bash
cd api && ruff check app tests && pytest -q          # 137 tests, incl. tests/test_hardening.py, test_capacity.py, test_transport.py
cd web && npx eslint src && npm run build
cd e2e && npx playwright test                          # 14 tests; the login limit is raised for this server only
```
