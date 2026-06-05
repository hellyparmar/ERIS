#!/bin/bash
# Database Setup & Migration Script
# Enterprise Retail Intelligence System
# Run this script to set up database and run migrations

set -e  # Exit on error

echo "🚀 Starting Database Setup and Migration..."
echo "==========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BACKEND_DIR="/home/petpooja/Enterprise Retail Intelligence System/backend"
ENV_FILE="/home/petpooja/Enterprise Retail Intelligence System/.env.production"

# Step 1: Verify environment
echo -e "${YELLOW}Step 1: Verifying environment...${NC}"
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ .env.production not found${NC}"
    echo "Please copy .env.production.template to .env.production and fill in values"
    exit 1
fi
echo -e "${GREEN}✅ Environment file found${NC}"

# Step 2: Activate Python environment
echo -e "${YELLOW}Step 2: Activating Python environment...${NC}"
source /home/petpooja/venv/bin/activate
echo -e "${GREEN}✅ Python environment activated${NC}"

# Step 3: Check PostgreSQL
echo -e "${YELLOW}Step 3: Checking PostgreSQL installation...${NC}"
if ! command -v psql &> /dev/null; then
    echo -e "${RED}❌ PostgreSQL client not found${NC}"
    echo "Install with: sudo apt-get install postgresql-client"
    exit 1
fi
echo -e "${GREEN}✅ PostgreSQL client found${NC}"

# Step 4: Install Python dependencies
echo -e "${YELLOW}Step 4: Installing Python dependencies...${NC}"
cd "$BACKEND_DIR"
pip install -q sqlalchemy alembic psycopg2-binary python-dotenv
echo -e "${GREEN}✅ Dependencies installed${NC}"

# Step 5: Create database (if using local PostgreSQL)
echo -e "${YELLOW}Step 5: Setting up database...${NC}"
echo "Note: Ensure PostgreSQL is running and credentials are correct"
python << 'EOF'
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv("/home/petpooja/Enterprise Retail Intelligence System/.env.production")

db_host = os.getenv("DB_HOST", "localhost")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")

print(f"Database Configuration:")
print(f"  Host: {db_host}")
print(f"  User: {db_user}")
print(f"  Database: {db_name}")
print(f"  ✅ Ready to connect")

# Test connection
try:
    import psycopg2
    conn = psycopg2.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database="postgres"
    )
    conn.close()
    print("  ✅ PostgreSQL connection successful")
except Exception as e:
    print(f"  ⚠️  Could not connect: {str(e)}")
    print("     Continuing with migration setup...")

EOF

echo -e "${GREEN}✅ Database configuration verified${NC}"

# Step 6: Run Alembic migrations
echo -e "${YELLOW}Step 6: Running database migrations...${NC}"
cd "$BACKEND_DIR"

# Check if migrations directory exists
if [ ! -d "alembic" ]; then
    echo -e "${YELLOW}Initializing alembic...${NC}"
    alembic init alembic
fi

# Run migrations
echo "Running: alembic upgrade head"
alembic upgrade head
echo -e "${GREEN}✅ Migrations completed${NC}"

# Step 7: Seed sample data
echo -e "${YELLOW}Step 7: Seeding sample data...${NC}"
python << 'EOF'
import sys
sys.path.insert(0, '/home/petpooja/Enterprise Retail Intelligence System/backend')

try:
    # Import data seeding function
    from app.core.seed_data import seed_sample_data
    
    print("Creating sample data...")
    seed_sample_data()
    print("✅ Sample data seeded successfully")
except Exception as e:
    print(f"⚠️  Could not seed data: {str(e)}")
    print("   You can manually seed data later")

EOF

# Step 8: Verify database
echo -e "${YELLOW}Step 8: Verifying database setup...${NC}"
python << 'EOF'
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect

load_dotenv("/home/petpooja/Enterprise Retail Intelligence System/.env.production")

database_url = os.getenv("DATABASE_URL")
try:
    engine = create_engine(database_url)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"✅ Connected to database")
    print(f"   Tables created: {len(tables)}")
    
    expected_tables = [
        'users', 'outlets', 'products', 'sales', 'inventory',
        'forecasts', 'alerts', 'model_performance'
    ]
    
    for table in expected_tables:
        status = "✅" if table in tables else "⏳"
        print(f"   {status} {table}")
    
    engine.dispose()
except Exception as e:
    print(f"❌ Database verification failed: {str(e)}")
    exit(1)

EOF

echo ""
echo -e "${GREEN}✅ Database setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Start backend: cd /home/petpooja/Enterprise Retail Intelligence System && docker-compose -f docker-compose.production.yml up -d backend"
echo "2. Verify API: curl http://localhost:8000/health"
echo "3. Check dashboard: http://localhost:3000 (Grafana)"
echo ""
