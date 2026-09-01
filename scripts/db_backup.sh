#!/bin/bash
# ==============================================================================
# R-DIOS Database Backup Script
# Automatically creates daily PostgreSQL backups via pg_dump and enforces
# a 30-day retention policy for old backups to save disk space.
#
# Recommended Cron:
# 0 2 * * * /path/to/R-DIOS/scripts/db_backup.sh >> /var/log/rdios_backup.log 2>&1
# ==============================================================================

# Load Environment Variables from local .env
source "$(dirname "$0")/../.env"

# Configuration
BACKUP_DIR="$(dirname "$0")/../backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RETENTION_DAYS=30

# Handle Supabase / external URL
# Export connection strings for pg_dump
export PGURL="$DATABASE_URL"
DB_NAME="petpooja_retail"
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_backup_${TIMESTAMP}.sql.gz"

echo "[$(date)] Starting R-DIOS database backup..."

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Run pg_dump
if pg_dump "$PGURL" | gzip > "$BACKUP_FILE"; then
    echo "[$(date)] Backup completed successfully: $BACKUP_FILE"
else
    echo "[$(date)] ERROR: Backup failed!"
    exit 1
fi

# Apply 30-day retention policy
echo "[$(date)] Pruning backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "${DB_NAME}_backup_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete

echo "[$(date)] Backup process finished successfully."
