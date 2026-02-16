"""
Supabase Database Setup Script
Creates all 22 tables in Supabase using SQLAlchemy models
Run this after configuring Supabase credentials in backend/.env
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv('backend/.env')

# Verify Supabase credentials
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_ANON_KEY must be set in backend/.env")
    sys.exit(1)

print(f"🌐 Connecting to Supabase: {SUPABASE_URL}")

# Get database password from user
db_password = input("Enter your Supabase database password: ").strip()

if not db_password:
    print("❌ Error: Database password is required")
    sys.exit(1)

# Extract project ref from URL
project_ref = SUPABASE_URL.replace('https://', '').replace('.supabase.co', '')

# Build Supabase PostgreSQL connection string
DATABASE_URL = f"postgresql://postgres:{db_password}@db.{project_ref}.supabase.co:5432/postgres"

print(f"📊 Database URL: postgresql://postgres:***@db.{project_ref}.supabase.co:5432/postgres")

# Update environment variable
os.environ['DATABASE_URL'] = DATABASE_URL

# Import SQLAlchemy models
from api.db.models import Base
from sqlalchemy import create_engine, text

# Create engine with Supabase connection
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=5,
    max_overflow=10
)

print("\n🔧 Creating tables in Supabase...")

try:
    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.scalar()
        print(f"✅ Connected to PostgreSQL: {version[:50]}...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Verify tables created
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """))
        tables = [row[0] for row in result]
    
    print(f"\n✅ Successfully created {len(tables)} tables in Supabase:")
    for table in tables:
        print(f"   - {table}")
    
    # Update backend/.env with DATABASE_URL
    env_path = 'backend/.env'
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    # Replace DATABASE_URL line
    with open(env_path, 'w') as f:
        for line in lines:
            if line.startswith('DATABASE_URL='):
                f.write(f'DATABASE_URL={DATABASE_URL}\n')
            else:
                f.write(line)
    
    print(f"\n✅ Updated {env_path} with Supabase DATABASE_URL")
    print("\n🎉 Supabase database setup complete!")
    print("\nNext steps:")
    print("1. Test POS transaction: python3 test_pos_transaction.py")
    print("2. Start backend: cd backend && uvicorn api.main:app --reload")
    print("3. Start frontend: npm run dev")

except Exception as e:
    print(f"\n❌ Error creating tables: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
