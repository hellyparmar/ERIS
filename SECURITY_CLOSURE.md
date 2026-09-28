# Security Closure & Credential Inventory

This document tracks every credential, token, and secret that has ever been present or referenced across the ERIS codebase and repository history.

> **Status Notice**: All credentials in active code (`HEAD`) have been removed and replaced with dynamic reads from environment variables. Any required secret missing or set to a placeholder (`CHANGE_ME`) at runtime causes an immediate fail-fast termination (`RuntimeError`).

---

## 1. Credential Checklist & Rotation Status

| # | Credential / Secret | Where It Lived in Repo History | Rotated (Y/N) | Env Var Name Now Used | Purpose / Usage Context |
|---|---------------------|--------------------------------|---------------|-----------------------|-------------------------|
| 1 | **Database Password** | `backend/app/services/query_executor.py`, `backend/app/database.py` (commits `492088a`, `fb38a65`, `4017deb`) | [ ] | `DATABASE_URL`, `POSTGRES_PASSWORD` | PostgreSQL production database connection string and password. |
| 2 | **JWT Secret Key** | Hardcoded defaults (`"your-super-secret-key..."`, `"dev_secret"`, `"your-secret-key"`) in `backend/app/core/security.py`, `backend/app/core/config.py`, `backend/app/models/tenant_context.py` | [ ] | `JWT_SECRET_KEY` (alias `JWT_SECRET`) | HS256 HMAC signing key for user authentication tokens. |
| 3 | **Encryption / Fernet Key** | Fallback key generation / dummy strings in `backend/app/api/utils/encryption.py`, `backend/app/api/integrations/zoho_auth.py` | [ ] | `ENCRYPTION_KEY` | Symmetric 32-byte Fernet key for encrypting sensitive tenant/integration tokens at rest. |
| 4 | **n8n / Webhook Secret** | `docker-compose.yml`, `backend/n8n_workflows/daily_stock_check.json`, `backend/app/routers/webhooks.py` (`rdios-n8n-secret`) | [ ] | `N8N_WEBHOOK_SECRET` / `WEBHOOK_SECRET` | Header secret token (`X-Webhook-Secret`) authenticating incoming automated trigger requests. |
| 5 | **Groq API Key** | `backend/app/services/ai_service.py`, `backend/app/routers/forecasting.py`, `.env.example` | [ ] | `GROQ_API_KEY` | Fast LLM inference endpoint (Llama / Mixtral models). |
| 6 | **Gemini API Key** | `backend/app/services/ai_service.py`, `research/notebooks/ai_assistant_evaluation.ipynb`, `.env.example` | [ ] | `GEMINI_API_KEY` | Google Gemini AI assistant and natural language SQL query generation. |
| 7 | **OpenRouter API Key** | `backend/app/services/ai_service.py`, `.env.example` | [ ] | `OPENROUTER_API_KEY` | Multi-model fallback gateway for retail intelligence queries. |
| 8 | **OpenAI API Key** | `backend/app/services/ai_service.py`, `backend/app/core/config.py`, `.env.example` | [ ] | `OPENAI_API_KEY` | OpenAI GPT model fallback for conversational retail analysis. |
| 9 | **Anthropic API Key** | `backend/app/core/config.py`, `.env.example` | [ ] | `ANTHROPIC_API_KEY` | Claude API integration for analytics reasoning. |
| 10 | **Zoho OAuth Client Secret & Refresh Token** | `backend/app/api/integrations/zoho_client.py`, `backend/app/api/integrations/zoho_auth.py` | [ ] | `ZOHO_CLIENT_SECRET`, `ZOHO_REFRESH_TOKEN` | OAuth2 credentials for syncing Zoho Inventory and Books. |
| 11 | **MSG91 / WhatsApp API Key** | `backend/app/services/message_service.py`, `backend/app/services/whatsapp.py`, `.env.example` | [ ] | `MSG91_API_KEY`, `WHATSAPP_API_TOKEN` | SMS / WhatsApp transactional alerts and customer notification dispatch. |
| 12 | **OpenWeather API Key** | `backend/app/services/weather_service.py`, `.env.example` | [ ] | `OPENWEATHER_API_KEY` | External factor demand forecasting weather enrichment. |

---

## 2. History Scrubbing (`git filter-repo`) Reference Commands

> **DO NOT RUN AUTOMATICALLY.** Run these only after coordinating rotation of credentials and establishing team backup.

### A. Prepare Replacements File
Create a `filter-replacements.txt` file listing all exposed strings mapped to redactions:
```text
<OLD_DB_PASSWORD>==>REDACTED_ROTATE_THIS_PASSWORD
<OLD_SECRET_KEY>==>REDACTED_ROTATE_THIS_KEY
```

### B. Run `git filter-repo`
```bash
# 1. Ensure working directory is clean
git status

# 2. Rewrite history across all branches and tags
git filter-repo --replace-text filter-replacements.txt --force

# 3. Clean up filter-repo backup references
rm -rf .git/filter-repo
```

### C. Verify History Cleanliness
```bash
# Verify the string no longer appears anywhere in commit history
git log --all -S "<OLD_PASSWORD>" --oneline

# Run full gitleaks history check
gitleaks detect --log-opts="--all" --config .gitleaks.toml
```

### D. Force Push Instructions
```bash
# Re-add remote origin (git-filter-repo clears remotes for safety)
git remote add origin https://github.com/hellyparmar/ERIS.git

# Force-push the rewritten history to all branches and tags
git push origin --force --all
git push origin --force --tags
```

### E. Team Re-Clone Instructions
Every contributor and deployment server must re-clone to avoid re-introducing old commits:
```bash
# Archive or remove old local clone
mv eris_project eris_project_backup

# Fresh clone from remote
git clone https://github.com/hellyparmar/ERIS.git
cd ERIS
```

---

## 3. Runtime Fail-Fast Enforcement

The application verifies critical configuration at boot before starting any server workers:
- **`DATABASE_URL`**: Verified non-empty, valid connection schema, and refuses `CHANGE_ME` / placeholder values.
- **`JWT_SECRET_KEY` / `JWT_SECRET`**: Verified non-empty and refuses placeholder values.
- **`ENCRYPTION_KEY`**: Verified non-empty, 32-byte Fernet key, and refuses placeholder values.

If any of these conditions are violated, ERIS immediately terminates with an explicit `RuntimeError`.
