"""
Create PostgreSQL Tables for R-DIOS
This script creates all tables in the PostgreSQL database using SQLAlchemy models
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.db import engine, Base
from api.db.models import *
# Note: invoicing_models has duplicate table definitions, skip for now


def create_tables():
    """Create all tables in the database"""
    try:
        print("Creating tables in PostgreSQL...")
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully!")
        
        # List created tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"\nCreated {len(tables)} tables:")
        for table in sorted(tables):
            print(f"  - {table}")
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_tables()
