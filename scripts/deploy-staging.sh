#!/bin/bash
# ==============================================================================
# R-DIOS Staging Deployment Script
# Executed by GitHub Actions on the staging host to pull and restart containers.
# Usage: ./deploy-staging.sh <tag-version>
# ==============================================================================

set -e

VERSION=${1:-latest}
PROJECT_DIR="/opt/rdios-staging"
REGISTRY="ghcr.io/petpooja/rdios"

echo "[$(date)] Starting staging deployment for version: $VERSION"

cd "$PROJECT_DIR" || exit 1

# Pull the latest image
echo "[$(date)] Pulling new images from GHCR..."
docker-compose --env-file .env.staging pull

# Export TAG to be picked up by docker-compose.yml if dynamically tagged
export IMAGE_TAG="$VERSION"

# Restart services with new images
echo "[$(date)] Removing old containers and recreating..."
docker-compose --env-file .env.staging up -d --remove-orphans

# Wait for containers to boot
echo "[$(date)] Waiting for services to initialize..."
sleep 15

# Run database migrations
echo "[$(date)] Executing alembic database migrations..."
docker-compose --env-file .env.staging exec -T api alembic upgrade head

# Print status
echo "[$(date)] Staging deployment complete. Verifying running containers..."
docker-compose ps

echo "[$(date)] Deployment $VERSION applied successfully."
