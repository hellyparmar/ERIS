#!/bin/bash
# ==============================================================================
# R-DIOS Rollback Script
# Rapidly reverts the production API and Frontend to the specific previous version.
# Usage: ./rollback.sh <previous-tag-version>
# Example: ./rollback.sh v1.0.1
# ==============================================================================

set -e

PREVIOUS_VERSION=$1
PROJECT_DIR="/opt/rdios-prod"

if [ -z "$PREVIOUS_VERSION" ]; then
    echo "ERROR: Previous version tag is required!"
    echo "Usage: ./rollback.sh <vX.Y.Z>"
    exit 1
fi

echo "[$(date)] Starting EMERGENCY ROLLBACK to version: $PREVIOUS_VERSION"

cd "$PROJECT_DIR" || exit 1

# Step 1: Revert database migrations if explicitly required
# (Note: This is risky in production. If the new version added columns, older code
# usually ignores them safely. Only downgrade alembic if the old code completely crashes.)
echo "[$(date)] Please manually downgrade PostgreSQL via alembic if schema is fully incompatible."
# docker-compose --env-file .env.production exec -T api alembic downgrade -1

# Step 2: Spin up the older images
export IMAGE_TAG="$PREVIOUS_VERSION"
echo "[$(date)] Pulling older reliable images ($PREVIOUS_VERSION)..."
docker-compose --env-file .env.production pull

echo "[$(date)] Restarting API and Frontend instances on $PREVIOUS_VERSION..."
docker-compose --env-file .env.production up -d --remove-orphans

echo "[$(date)] Waiting for API health recovery..."
sleep 15
docker-compose ps

echo "[$(date)] Rollback complete. Please run ./scripts/health-check.sh locally to verify."
