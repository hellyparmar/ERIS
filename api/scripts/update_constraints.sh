#!/usr/bin/env bash
# Re-resolve the newest allowed versions of api/requirements*.txt in a clean virtual environment, run the
# test suite, and only then rewrite constraints.txt (the exact versions CI, Docker and Render install).
#   cd api && scripts/update_constraints.sh            (needs Python 3.11 on PATH as python3.11)
set -euo pipefail
cd "$(dirname "$0")/.."
venv="$(mktemp -d)/venv"
python3.11 -m venv "$venv"
"$venv/bin/pip" install -q --upgrade pip
"$venv/bin/pip" install -q -r requirements-dev.txt
"$venv/bin/ruff" check app tests
"$venv/bin/pytest" -q
{
  echo "# Exact versions the test suite passed with (Python 3.11, Linux). Installs use them as constraints:"
  echo "#   pip install -r requirements.txt -c constraints.txt"
  echo "# Regenerate after changing requirements: scripts/update_constraints.sh"
  "$venv/bin/pip" freeze --exclude-editable | grep -viE "^(pip|setuptools|wheel)=="
} > constraints.txt
echo "constraints.txt updated - review the diff and commit it"
