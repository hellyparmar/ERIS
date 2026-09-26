# Security & Credentials Policy

## Strict No-Hardcoded-Credentials Rule
1. **Never write real or real-looking credentials**:
   - Under no circumstances should real passwords, API keys, JWT secrets, database connection strings, or high-entropy tokens be written into source code, test files, seed scripts, fixtures, mock data, or example configurations.
2. **Use obviously-fake placeholder values**:
   - For tests, always use explicitly labeled mock tokens, such as `MOCK_API_KEY_FOR_TESTS`, `INVALID_KEY_FOR_TESTS`, `test-admin-pw`, `testpass`.
   - For example configurations (`.env.example`), always use `CHANGE_ME` or `CHANGE_ME_OR_LEAVE_BLANK`.
3. **Environment variable lookups**:
   - Always read credentials and secrets dynamically via `os.getenv` / `process.env` / settings objects.
   - For production code, never provide real-looking default fallbacks. Raise a clear startup error (e.g. `RuntimeError`) if a required configuration is missing.
4. **Pre-commit & CI Compliance**:
   - All commits must pass Gitleaks and detect-secrets scans before pushing.
