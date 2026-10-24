# Credential exposure in repository history

**Found:** 2026-10-24, by a full scan of the working tree and of every commit on every branch.
**Status:** Open. The exposed database credential has not been rotated yet (pending the owner's Supabase check). Rotation needs the owner, because it happens in the hosting provider's dashboard.
**Severity:** High. The repository is public (`hellyparmar/ERIS`, checked through the GitHub API), so anything committed is readable by anyone.

Values are deliberately not written here. Commits and file types are enough to find them.

## What was exposed

| # | Commit | Date | What | Still in the working tree? | Severity |
|---|---|---|---|---|---|
| 1 | `18e7012` | 2026-02-25 | A PostgreSQL connection string with a real-looking password for a hosted database, in several backend and docs files of the earlier product | No | **High** |
| 2 | `b86cc36` | 2026-02-17 | `.env.supabase` with the project URL and a public (anon) key for a hosted Supabase project | No | **Medium** |
| 3 | `b808301`, `3e614eb`, `1c382fb`, `b86cc36` | Feb–Mar 2026 | Local and test database placeholders: `postgres:postgres`, `rdios_secure_password_*`, `eris:eris`, `test_password`, `user:pass` | No | Low |
| 4 | `6b0dbc8` | 2026-03-26 | Commit titled "Rotated JWT secret". The diff does not show the secret, so the rotated value cannot be identified from history | No | Medium (see below) |
| 5 | `e988fd2`, `514787f` | Oct 2026 | `JWT_SECRET_KEY=ci-only…` in CI, and the development default in the code | Yes (CI and dev only) | Informational |

### Notes on each

- **#1 (high).** The password is a real value, not a placeholder. Treat it as compromised. The host also belongs
  to a hosted project, so the owner must check whether that project still exists and holds data.
- **#2 (medium).** An anon key is designed to be public inside a browser app, but it still identifies the project.
  If the project is still used, rotate its keys. If it is not, delete the project.
- **#3 (low).** Local and test values. Confirm none of them is the password of a deployed database.
- **#4 (medium).** Any JWT signing secret that existed before 2026-03-26 must be treated as compromised.
  The current deployment does not use it: `render.yaml` sets `JWT_SECRET_KEY` with `generateValue: true`, so Render
  generates a random value.
- **#5 (informational).** `api/app/main.py` contains a development JWT default. It is documented as a development
  value, and the API logs a warning when it is in use. It is not a production secret, but anyone could forge tokens
  on a deployment that runs with it.

## Checked and found clean

- **Current tree.** No credentials found. Patterns checked: AWS access keys, PEM private keys, GitHub tokens,
  GitHub fine-grained tokens, Slack tokens, Google API keys, Stripe live keys, Render keys, JWT-shaped tokens, and
  database URLs with embedded passwords.
- **Env files.** `.env`, `.env.production` and `api/.env` are ignored by git. The only tracked env file is
  `api/.env.example`, which holds placeholders.
- **Demo logins.** `admin@eris.demo` and the other demo accounts are public on purpose. They are listed in the
  README and they open demo data only.
- **Configuration.** Secrets are read from environment variables. None is hard-coded in the application.
- **Scanned history.** All commits on all branches were searched with the patterns above. The matches are the ones listed in the table.

## What CI does and does not cover

- The CI job named GitGuardian runs on pull requests and passed on this branch. The history findings above came from a
  separate full-history scan, so a passing pull-request check does not mean old commits are clean.

## Owner actions (required)

1. **Rotate the database password** of the hosted project behind commit `18e7012`, or delete the project if nothing uses it. Check the project's activity logs for any access from unknown sources.
2. **Rotate the Supabase keys** from commit `b86cc36` if that project is still used. Otherwise delete it.
3. **Check Render.** In the `eris` service, confirm `JWT_SECRET_KEY` is the generated value and not the development default. Confirm `DEMO_SHIFT_DATES=false` (see `11`, O4).
4. **Turn on secret scanning and push protection** in the repository settings, so a secret cannot be pushed again. *(Verified 2026-10-24 through the GitHub API: secret scanning enabled, push protection enabled. Still unknown: whether any alerts are open. The alerts endpoint is blocked through this environment's proxy, so the owner should check the Security tab.)*
5. **Decide on history removal.** Rewriting history (for example with `git filter-repo`, followed by a force-push of every branch) removes the values from the repository, but not from forks, caches or copies already taken. It also breaks the shared branch history. Do it only after rotation, and only with the owner's explicit approval. Rotation is the fix that matters; a rewrite on its own does not make a leaked password safe.

## Progress log

- **2026-10-24:** Repo settings checked through the GitHub API: secret scanning and push protection are enabled.
- **2026-10-24:** Browser-based checks of GitHub, Render and Supabase were requested. The browser tools were not available in this session, so they were not done. Render's `JWT_SECRET_KEY` and `DEMO_SHIFT_DATES`, and the Supabase project's status and keys, are still unverified.

- **2026-10-24 (Render, checked by the owner):** `JWT_SECRET_KEY` is the generated value, not the development default. Good.
- **2026-10-24 (Render, open):** `DEMO_SHIFT_DATES` is not listed in the dashboard. The code default is `True`, so the service shifts the demo data on each start. Set it to `false` in the `eris` service's Environment tab. `render.yaml` says `false`, so the dashboard should match.
- **2026-10-24 (Render, mismatch):** the dashboard has `SEED_DEMO_DATA=false`, but `render.yaml` has `"true"`. Harmless while the baked database has users. Either change the dashboard to match the file, or update the file, so they agree.

- **2026-10-24 (owner report):** Render's `JWT_SECRET_KEY` is the generated value, not the development default. `DEMO_SHIFT_DATES` is **not visible** in the Render service even though `render.yaml` sets it to `false`. The app's own default is `true`, so the hosted demo will shift dates on each start until the variable is added. Action: add `DEMO_SHIFT_DATES=false` to the `eris` service and redeploy.
- **2026-10-24 (owner report):** GitHub secret scanning shows **no open alerts**. This does not make the exposed password safe. The alert may never have fired, or may have been closed, and the password is still readable in public history until it is rotated.
- **2026-10-24:** The exposed Supabase project is the one whose reference starts with `rmqawn` (from the URL in `b86cc36:.env.supabase`). The current app has no Supabase references, so the project can be deleted or rotated without changing the app. **Pending:** the owner has not yet confirmed whether the project is in use, or whether its database password was reset or the project deleted.

- **2026-10-24 (owner report):** Render `DEMO_SHIFT_DATES=false` added and redeployed (owner report; not verified from this environment, which could not reach the hosted API).
- **2026-10-24 (owner screenshot):** the Supabase project shown is a different project from the exposed one. Its address starts with `bsunxz`, it is in Mumbai, and it is still starting up. The exposed project (reference starting `rmqawn`) was **not** in that view. **Pending:** find `rmqawn` in the project list and delete, pause, or rotate it.

- **2026-10-24 (history check):** the project reference `rmqawn` appears only in commits from the earlier product (`b86cc36`, `18e7012`, `1c513fb`, February–June 2026). No commit of the rebuilt ERIS (from 2026-10-01) adds or removes it, and the current tree does not contain it. The project is therefore not used by the current code. Whether anything else outside this repository uses it can only be checked in Supabase (the project's logs and any connected apps).

## What was done in the repository

- Confirmed the current tree is clean (above).
- Did not rewrite history, rotate anything, or change any hosted setting. Those actions need the owner.

## How to verify when the owner says it is done

- The hosted database rejects the old password.
- Render's `JWT_SECRET_KEY` is not the development default.
- Repository settings show secret scanning and push protection as enabled.
- Re-run the history scan (the patterns above) and record the result in `01-timeline.md`.
