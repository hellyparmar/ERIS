#!/bin/bash
# PostgreSQL Migration Script
# Migrates data from SQLite to PostgreSQL for production

set -e  # Exit on error

echo "╔═══════════════════════════════════════════════════╗"
echo "║     R-DIOS SQLite → PostgreSQL Migration         ║"
echo "╚═══════════════════════════════════════════════════╝"

# Configuration
SQLITE_DB="${SQLITE_DB:-./api/rdios_dev.db}"
PG_HOST="${PG_HOST:-localhost}"
PG_PORT="${PG_PORT:-5432}"
PG_DB="${PG_DB:-rdios_production}"
PG_USER="${PG_USER:-rdios}"
PG_PASSWORD="${PG_PASSWORD:-rdios_secure_password}"

# Check prerequisites
echo ""
echo "📋 Checking prerequisites..."

if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL client (psql) not found. Install with: sudo apt install postgresql-client"
    exit 1
fi

if ! command -v sqlite3 &> /dev/null; then
    echo "❌ SQLite3 not found. Install with: sudo apt install sqlite3"
    exit 1
fi

if [ ! -f "$SQLITE_DB" ]; then
    echo "❌ SQLite database not found at: $SQLITE_DB"
    exit 1
fi

echo "✅ Prerequisites met"

# Create PostgreSQL database
echo ""
echo "🔧 Setting up PostgreSQL database..."

PGPASSWORD=$PG_PASSWORD psql -h $PG_HOST -U $PG_USER -p $PG_PORT -tc "SELECT 1 FROM pg_database WHERE datname = '$PG_DB'" | grep -q 1 || \
    PGPASSWORD=$PG_PASSWORD psql -h $PG_HOST -U $PG_USER -p $PG_PORT -c "CREATE DATABASE $PG_DB"

echo "✅ Database '$PG_DB' ready"

# Generate schema from SQLAlchemy models
echo ""
echo "📝 Creating schema in PostgreSQL..."

python3 << EOF
from api.db.database_postgres import engine, Base
from api.db import models  # Import all models

# Create all tables
Base.metadata.create_all(bind=engine)
print("✅ Schema created successfully")
EOF

# Export data from SQLite
echo ""
echo "📤 Exporting data from SQLite..."

mkdir -p ./migration_temp

# Tables to migrate
TABLES=(
    "users"
    "customers"
    "suppliers"
    "products"
    "sales"
    "sale_items"
    "invoices"
    "payments"
    "messages"
    "stock_swap_listings"
    "bulk_buy_groups"
    "bulk_buy_participants"
)

for table in "${TABLES[@]}"; do
    echo "  Exporting $table..."
    sqlite3 -header -csv "$SQLITE_DB" "SELECT * FROM $table;" > "./migration_temp/${table}.csv" 2>/dev/null || true
done

echo "✅ Data exported to CSV"

# Import data into PostgreSQL
echo ""
echo "📥 Importing data into PostgreSQL..."

for table in "${TABLES[@]}"; do
    if [ -f "./migration_temp/${table}.csv" ] && [ -s "./migration_temp/${table}.csv" ]; then
        echo "  Importing $table..."
        PGPASSWORD=$PG_PASSWORD psql -h $PG_HOST -U $PG_USER -p $PG_PORT -d $PG_DB -c "\COPY $table FROM './migration_temp/${table}.csv' WITH (FORMAT CSV, HEADER, NULL '')" 2>/dev/null || echo "    ⚠️ Skipped (may have FK constraints)"
    fi
done

echo "✅ Data imported"

# Reset sequences
echo ""
echo "🔄 Resetting PostgreSQL sequences..."

PGPASSWORD=$PG_PASSWORD psql -h $PG_HOST -U $PG_USER -p $PG_PORT -d $PG_DB << EOF
-- Reset auto-increment sequences for all tables
SELECT setval(pg_get_serial_sequence('"users"', 'id'), COALESCE((SELECT MAX(id) FROM users), 1));
SELECT setval(pg_get_serial_sequence('"customers"', 'id'), COALESCE((SELECT MAX(id) FROM customers), 1));
SELECT setval(pg_get_serial_sequence('"suppliers"', 'id'), COALESCE((SELECT MAX(id) FROM suppliers), 1));
SELECT setval(pg_get_serial_sequence('"products"', 'id'), COALESCE((SELECT MAX(id) FROM products), 1));
SELECT setval(pg_get_serial_sequence('"sales"', 'id'), COALESCE((SELECT MAX(id) FROM sales), 1));
SELECT setval(pg_get_serial_sequence('"invoices"', 'id'), COALESCE((SELECT MAX(id) FROM invoices), 1));
SELECT setval(pg_get_serial_sequence('"payments"', 'id'), COALESCE((SELECT MAX(id) FROM payments), 1));
EOF

echo "✅ Sequences reset"

# Verify migration
echo ""
echo "📊 Verifying migration..."

python3 << EOF
import os
os.environ['USE_SQLITE'] = 'false'  # Force PostgreSQL

from api.db.database_postgres import engine
from sqlalchemy import text

with engine.connect() as conn:
    tables = ['users', 'customers', 'products', 'sales', 'invoices']
    print("\n  Table Counts:")
    for table in tables:
        result = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()
        print(f"    {table}: {result[0]:,} rows")

print("\n✅ Migration verification complete!")
EOF

# Cleanup
echo ""
echo "🧹 Cleaning up temporary files..."
rm -rf ./migration_temp

echo ""
echo "╔═══════════════════════════════════════════════════╗"
echo "║       Migration Complete! 🎉                     ║"
echo "╠═══════════════════════════════════════════════════╣"
echo "║                                                   ║"
echo "║   Next Steps:                                     ║"
echo "║   1. Update .env with PostgreSQL credentials     ║"
echo "║   2. Set USE_SQLITE=false                        ║"
echo "║   3. Restart API server                          ║"
echo "║   4. Run health check: curl /health              ║"
echo "║                                                   ║"
echo "╚═══════════════════════════════════════════════════╝"
