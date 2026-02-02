#!/bin/bash
# ============================================================
# R-DIOS Multi-Tenant Migration Runner
# Consolidated script to apply all Phase 1 migrations
# ============================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}R-DIOS Multi-Tenant Migration${NC}"
echo -e "${GREEN}Phase 1: Organizations & Stores${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""

# Database configuration
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-rdios}"
DB_USER="${DB_USER:-postgres}"

echo -e "${YELLOW}Database Configuration:${NC}"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo ""

# Backup prompt
echo -e "${YELLOW}⚠️  WARNING: This will modify your database schema!${NC}"
echo -e "${YELLOW}⚠️  Please ensure you have a backup before proceeding.${NC}"
echo ""
read -p "Do you have a database backup? (yes/no): " backup_confirm

if [ "$backup_confirm" != "yes" ]; then
    echo -e "${RED}Migration aborted. Please backup your database first.${NC}"
    echo ""
    echo "To create a backup:"
    echo "  pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > backup_$(date +%Y%m%d_%H%M%S).sql"
    exit 1
fi

# Confirm migration
echo ""
read -p "Proceed with migration? (yes/no): " proceed

if [ "$proceed" != "yes" ]; then
    echo -e "${RED}Migration cancelled.${NC}"
    exit 0
fi

echo ""
echo -e "${GREEN}Starting migration...${NC}"
echo ""

# Step 1: Organizations & Stores
echo -e "${YELLOW}[1/3] Creating organizations and stores tables...${NC}"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f migrations/001_create_organizations_stores.sql

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Organizations and stores created${NC}"
else
    echo -e "${RED}✗ Failed to create organizations and stores${NC}"
    exit 1
fi

echo ""

# Step 2: Add multi-tenant columns
echo -e "${YELLOW}[2/3] Adding organization_id and store_id columns...${NC}"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f migrations/002_add_multitenant_columns.sql

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Multi-tenant columns added${NC}"
else
    echo -e "${RED}✗ Failed to add multi-tenant columns${NC}"
    exit 1
fi

echo ""

# Step 3: Enable RLS
echo -e "${YELLOW}[3/3] Enabling Row-Level Security (RLS)...${NC}"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f migrations/003_enable_row_level_security.sql

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Row-Level Security enabled${NC}"
else
    echo -e "${RED}✗ Failed to enable RLS${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}✓ Migration Complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""

# Verification
echo -e "${YELLOW}Verifying migration...${NC}"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
SELECT 
    'Organizations' as table_name,
    COUNT(*) as record_count
FROM organizations
UNION ALL
SELECT 
    'Stores' as table_name,
    COUNT(*) as record_count
FROM stores
UNION ALL
SELECT
    'RLS Policies' as table_name,
    COUNT(*) as record_count
FROM pg_policies
WHERE schemaname = 'public';
"

echo ""
echo -e "${GREEN}Next Steps:${NC}"
echo "1. Update environment variables with organization context"
echo "2. Test API endpoints: GET /api/v1/organizations/current"
echo "3. Test tenant isolation"
echo "4. Update frontend to include organization selector"
echo ""
echo -e "${GREEN}Documentation:${NC}"
echo "  Implementation Plan: multitenant_implementation_plan.md"
echo "  Gap Analysis: production_gap_analysis.md"
echo "  Roadmap: production_roadmap.md"
echo ""
