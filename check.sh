#!/usr/bin/env bash
# Runs the same checks as CI (.github/workflows/ci.yml) before you push:  ./check.sh
# Set TEST_DATABASE_URL=postgresql+psycopg2://eris:eris@localhost:5432/eris_test to also test PostgreSQL,
# and E2E=1 to run the Playwright suite.
set -euo pipefail
cd "$(dirname "$0")"
echo "== API: lint and tests (SQLite)"
(cd api && ruff check app tests && TEST_DATABASE_URL= pytest -q)
if [[ "${TEST_DATABASE_URL:-}" == postgresql* ]]; then
  echo "== API: tests (PostgreSQL)"
  (cd api && pytest -q)
fi
echo "== Web: lint and build"
(cd web && npm ci --no-audit --no-fund && npm run lint && npm run build)
if [[ "${E2E:-}" == 1 ]]; then
  echo "== End-to-end (Playwright)"
  (cd e2e && npm ci --no-audit --no-fund && npm test)
fi
echo "All checks passed"
