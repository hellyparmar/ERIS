# ERIS Security Status and Historical-Incident Checklist

## Current-tree status

The active application contains no committed runtime credentials. Critical configuration is read from environment variables, and startup fails when `DATABASE_URL` or `JWT_SECRET_KEY` is missing or still set to a placeholder. The demo-user password is also required explicitly through `ERIS_SEED_PASSWORD`.

Supported secret-bearing variables are limited to:

| Variable | Required | Purpose |
|---|---:|---|
| `DATABASE_URL` | Yes | SQLite locally or PostgreSQL in production |
| `JWT_SECRET_KEY` | Yes | JWT signing key; use at least 32 random bytes |
| `ERIS_SEED_PASSWORD` | Seed only | Password chosen by the operator for synthetic demo users |
| `GROQ_API_KEY` | No | Optional hosted AI fallback |
| `OPENROUTER_API_KEY` | No | Optional hosted AI fallback |

Ollama needs no API key. Removed integrations—including Gemini, OpenAI SDK, Zoho, Odoo, n8n, WhatsApp, Supabase, and weather enrichment—are not part of the runtime and their old variables must not be reintroduced.

## Why GitGuardian may still email

GitGuardian reports include historical commits, test-like values, and findings in other repositories. Cleaning the current branch cannot revoke a credential, erase an old Git object, or close an incident in the GitGuardian dashboard.

For each historical incident:

1. Identify the service and exact exposed value without posting it in an issue or commit.
2. If the value could ever have been valid, revoke/rotate it at the provider first.
3. Update the deployment environment with the replacement.
4. Mark the GitGuardian incident resolved only after verification. Use “false positive” only for an unmistakable non-secret test placeholder.
5. Treat findings shown for `helly-portfolio` or `vibe-vault` as separate repository work; ERIS changes cannot resolve them.

## Repository-history rewriting

History rewriting is intentionally not automated. It changes commit IDs and requires force-pushing every affected branch/tag and re-cloning all copies. Rotation is still required even after a rewrite because a copied secret cannot be made secret again.

If you decide to rewrite history, first create an offline backup, coordinate all repository users, use `git filter-repo` with exact known values, scan all refs, then force-push. Never place exposed values in a tracked replacements file.

## Automated controls

- `.github/workflows/secret-scan.yml` runs Gitleaks and `detect-secrets` on pushes and pull requests.
- `.secrets.baseline` records reviewed findings only; it is not a list of secrets to ignore casually.
- `.pre-commit-config.yaml` offers the same scanners locally.
- `.gitleaks.toml` allowlists only unmistakable test/config placeholders.
- `.env`, local databases, build output, and model artifacts are ignored.
- Test credentials follow `AGENTS.md` and use conspicuously fake values.

Local current-tree verification:

```bash
git ls-files -z | xargs -0 detect-secrets-hook --baseline .secrets.baseline
gitleaks detect --config .gitleaks.toml --no-banner
```

Gitleaks scans Git history in CI. A current-tree pass does not prove that historical provider keys were rotated; that remains an account-owner action.
