# Repository Guidelines & Agent Rules

## Security & Credentials Policy
- **Never write real or real-looking credentials** into test files, seed scripts, fixture files, or example configs.
- **Always use obviously-fake placeholder values**:
  - Test files: `MOCK_API_KEY_FOR_TESTS`, `test-admin-pw`, `testpass`, etc.
  - Configuration templates (`.env.example`): `CHANGE_ME` or `CHANGE_ME_OR_LEAVE_BLANK`.
- **Dynamic Reads**: Always retrieve secrets and keys from environment variables (`os.getenv(...)`).
- **Fail Fast**: When a critical secret is required at runtime, raise an explicit error (`RuntimeError`) rather than falling back to a dummy or default secret.
