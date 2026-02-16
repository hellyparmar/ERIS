#!/bin/bash
# Archive SQLite database before removal
# R-DIOS Phase 0 - Task 1

set -e

SQLITE_FILE="api/rdios_dev.db"
BACKUP_DIR="api/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/rdios_dev.db.backup.${TIMESTAMP}"

echo "============================================================"
echo "SQLite Database Archival Script"
echo "============================================================"

# Check if SQLite file exists
if [ ! -f "$SQLITE_FILE" ]; then
    echo "✓ SQLite file does not exist. Nothing to archive."
    exit 0
fi

# Get file size
SIZE=$(du -h "$SQLITE_FILE" | cut -f1)
echo "Found SQLite file: $SQLITE_FILE ($SIZE)"

# Create backup directory
echo "Creating backup directory..."
mkdir -p "$BACKUP_DIR"

# Archive the file
echo "Archiving to: $BACKUP_FILE"
cp "$SQLITE_FILE" "$BACKUP_FILE"

# Verify backup
if [ -f "$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "✓ Backup created successfully ($BACKUP_SIZE)"
    
    # Remove original
    echo "Removing original SQLite file..."
    rm "$SQLITE_FILE"
    
    if [ ! -f "$SQLITE_FILE" ]; then
        echo "✓ Original SQLite file removed"
        echo ""
        echo "============================================================"
        echo "SUMMARY"
        echo "============================================================"
        echo "✓ SQLite archived to: $BACKUP_FILE"
        echo "✓ Original file removed"
        echo "✓ App now uses PostgreSQL exclusively"
    else
        echo "✗ Failed to remove original file"
        exit 1
    fi
else
    echo "✗ Backup failed"
    exit 1
fi
