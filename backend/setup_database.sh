#!/bin/bash
# setup_database.sh - Initialize production-ready database
# Enterprise Retail Intelligence System (ERIS)

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🗄️  Enterprise Retail Intelligence System - Database Setup"
echo "=========================================================="
echo ""

# 1. Check environment
echo "📋 Checking environment..."
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
    echo "   Please update .env with your database credentials."
fi

# 2. Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

# 3. Run Alembic migrations
echo ""
echo "🔄 Running Alembic migrations..."
alembic upgrade head

# 4. Initialize database (creates tables if not already created)
echo ""
echo "🏗️  Initializing database tables..."
python -c "from app.models.database import init_db; init_db(); print('✓ Database tables initialized')"

# 5. Health check
echo ""
echo "🏥 Running database health check..."
python -c "from app.models.database import healthcheck_db; health = healthcheck_db(); print('✓ Database is healthy' if health else '✗ Database health check failed')"

echo ""
echo "✅ Database setup complete!"
echo ""
echo "Next steps:"
echo "  1. Seed initial roles and permissions: python scripts/seed_rbac.py"
echo "  2. Create an admin user: python scripts/create_admin.py"
echo "  3. Start the API server: python -m uvicorn app.main:app --reload"
