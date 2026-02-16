#!/bin/bash
# PostgreSQL Setup Script for R-DIOS
# This script starts PostgreSQL, creates the database, and sets up the user

set -e

echo "=== PostgreSQL Setup for R-DIOS ==="
echo ""

# Step 1: Start PostgreSQL
echo "Step 1: Starting PostgreSQL service..."
sudo service postgresql start
sleep 2

# Step 2: Check PostgreSQL status
echo "Step 2: Checking PostgreSQL status..."
sudo service postgresql status | head -5

# Step 3: Check which port PostgreSQL is running on
echo ""
echo "Step 3: Checking PostgreSQL port..."
sudo netstat -plnt | grep postgres || echo "Could not determine port"

# Step 4: Create database and user
echo ""
echo "Step 4: Creating database 'enterprise_retail'..."
sudo -u postgres psql -c "DROP DATABASE IF EXISTS enterprise_retail;" 2>/dev/null || true
sudo -u postgres psql -c "CREATE DATABASE enterprise_retail;"
echo "✅ Database created"

# Step 5: Set password for postgres user
echo ""
echo "Step 5: Setting password for postgres user..."
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'EnterpriseRetail@2026';"
echo "✅ Password set"

# Step 6: Test connection
echo ""
echo "Step 6: Testing connection..."
PGPASSWORD='EnterpriseRetail@2026' psql -h localhost -U postgres -d enterprise_retail -c "SELECT 'Connection successful!' as status;"

echo ""
echo "✅ PostgreSQL setup complete!"
echo "Database: enterprise_retail"
echo "User: postgres"
echo "Password: EnterpriseRetail@2026"
