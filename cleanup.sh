#!/bin/bash
echo "🧹 Starting safe cleanup..."

# Delete log files
find . -maxdepth 1 -name "*.log" -type f -delete
echo "✓ Deleted log files"

# Delete old databases
find . -maxdepth 1 -name "*.db" -type f -delete
find . -maxdepth 1 -name "*.sqlite3" -type f -delete
echo "✓ Deleted old databases"

# Delete backup folders
rm -rf framer_motion_backup_*
rm -rf alembic_backup
echo "✓ Deleted backup folders"

# Delete Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null
rm -f .coverage
echo "✓ Deleted Python cache"

# Archive documentation
mkdir -p docs/archive
mv PHASE_*.md docs/archive/ 2>/dev/null
mv *_COMPLETE.md docs/archive/ 2>/dev/null
mv *_SUMMARY.md docs/archive/ 2>/dev/null
echo "✓ Archived documentation"

echo "✅ Cleanup complete!"
du -sh .
