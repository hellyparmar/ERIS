# Security, CI, Docker and hosting

## Access control (D3, D4, D5)
- Roles: admin, manager, viewer, staff. Staff can only bill.
- Outlet scope on every outlet-scoped endpoint, including the assistant and reports.
- Access tokens are short-lived. Refresh tokens rotate, and the tests `test_refresh_rotates…` and the revocation tests check it. `token_version` on the user revokes every session. (The exact replay handling for a reused refresh token was not re-read for this note.)
- Five failed logins lock the account.
- Dev JWT secret: the API logs a warning if the development secret is in use. Set `JWT_SECRET_KEY` for any shared deployment.

## Import and input safety
- CSV only (or TXT, TSV). Excel files and binary content rejected with guidance.
- 15 MB and 50,000 rows maximum.
- **CSV injection:** cells beginning with `=`, `+`, `-` or `@` are neutralised on export (ebc267a).
- **UTF-16** files are accepted (ebc267a), so Windows exports work.
- **NaN and huge quantities** are rejected per row (ebc267a).
- **Dates before an outlet opened** are rejected per row (ebc267a).
- Imports are atomic.

## Concurrency (f534063, e258523)
- Numbering (invoices, POs) is unique under concurrent writes.
- PostgreSQL imports take an advisory lock, so two uploads of the same file do not clash.
- Route guards in the web app stop a viewer from reaching write screens.

## Audit trail
- Automatic before-flush hook on every business record.
- One summary entry per import and per bulk reset.
- Audit log page is read-only.

## CI (514787f, edfd346)
- **Read-only** workflow token.
- Checkout without persisted credentials.
- Third-party actions **pinned to commit hashes**, not version tags.
- The refresh workflow gets **no token** at all.
- The image used in CI signs in with the demo login it publishes, not a password stored in the workflow.
- Jobs: `api` (SQLite), `api-postgres`, `web`, `e2e`, `docker`. GitGuardian scans for secrets.

## Docker (514787f)
- Demo data is prepared in its **own build stage with no network access**.
- The final image receives only the data directory, owned by a non-root user.
- At run time: 512 MB memory limit, no Linux capabilities, `no-new-privileges`, and the code directory is not writable by the process.
- `BAKE_DEMO=1` triggers the bake (`Dockerfile`, line 29).

## Hosting
- **API:** Render, service `eris` (ceec816). `render.yaml` sets `DEMO_SHIFT_DATES=false` (D10).
- **Web:** Vercel (`vercel.json`). Preview deployments on each PR branch.
- **Live demo:** eris-retail.vercel.app, with the API on eris-tvro.onrender.com.
- The free API server sleeps when idle, so the first visit can take up to a minute.

## Things to check after a deploy
- `DEMO_SHIFT_DATES=false` is set in the Render service. If the service was not created from `render.yaml`, it must be set by hand (`11`).
- `JWT_SECRET_KEY` is set to a real secret for any shared deployment.
- The demo is on the expected data version (check the Settings page dataset info).

## Earlier security work (Era 0, for context)
- 2026-03-25 and 03-26: post-audit cleanup and JWT secret rotation in the earlier product (3e614eb, 6b0dbc8). That code was removed in the rebuild.
