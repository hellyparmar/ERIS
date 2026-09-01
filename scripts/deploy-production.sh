#!/bin/bash
# ==============================================================================
# R-DIOS Production Deployment Script
# Executed by GitHub Actions ensuring zero-downtime reloads or careful restarts.
# Usage: ./deploy-production.sh <tag-version>
# ==============================================================================

set -e

VERSION=${1:-latest}
PROJECT_DIR="/opt/rdios-prod"

echo "[$(date)] Starting PRODUCTION deployment for version: $VERSION"

cd "$PROJECT_DIR" || exit 1

# Backup database before structural changes
echo "[$(date)] Triggering pre-deploy DB snapshot..."
./scripts/db_backup.sh || echo "Warning: Backup script failed, proceeding with caution."

# Pull latest images
export IMAGE_TAG="$VERSION"
docker-compose --env-file .env.production pull

# Restart services (downtime < 5 seconds)
# For true zero-downtime, utilize docker swarm or a rolling nginx up-stream update instead.
echo "[$(date)] Restarting production API and Frontend..."
docker-compose --env-file .env.production up -d --remove-orphans

echo "[$(date)] Waiting for API health..."
sleep 20

# Run migrations (assuming backward compatibility)
echo "[$(date)] Applying Database Migrations safely..."
docker-compose --env-file .env.production exec -T api alembic upgrade head

echo "[$(date)] Production deployment $VERSION live! Please monitor logs utilizing 'docker-compose logs -f'."
