#!/usr/bin/env python3
"""
PostgreSQL Table Verification Script
Verifies that all SQLAlchemy models have corresponding PostgreSQL tables.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import inspect
from api.db import engine, Base

# Import all models to register them with Base
from api.db import models, multitenant_models


def verify_tables():
    """Verify all models have corresponding tables in PostgreSQL."""
    print("=" * 80)
    print("PostgreSQL Table Verification")
    print("=" * 80)
    print()
    
    # Get inspector
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    
    print(f"📊 Found {len(existing_tables)} tables in PostgreSQL database:")
    for table in sorted(existing_tables):
        print(f"  • {table}")
    print()
    
    # Get all models from Base metadata
    model_tables = set()
    for table in Base.metadata.tables.values():
        model_tables.add(table.name)
    
    print(f"🔍 Found {len(model_tables)} SQLAlchemy model tables:")
    for table in sorted(model_tables):
        print(f"  • {table}")
    print()
    
    # Check for missing tables
    missing_in_db = model_tables - existing_tables
    extra_in_db = existing_tables - model_tables
    
    # Report results
    print("=" * 80)
    print("VERIFICATION RESULTS")
    print("=" * 80)
    print()
    
    if not missing_in_db and not extra_in_db:
        print("✅ Perfect match! All models have corresponding tables.")
        print()
        print(f"Total verified: {len(model_tables)} tables")
        return True
    
    if missing_in_db:
        print("❌ MISSING IN DATABASE:")
        print("   These models exist but tables are missing:")
        for table in sorted(missing_in_db):
            print(f"  • {table}")
        print()
    
    if extra_in_db:
        print("ℹ️  EXTRA IN DATABASE:")
        print("   These tables exist but have no corresponding models:")
        for table in sorted(extra_in_db):
            print(f"  • {table}")
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Model Tables: {len(model_tables)}")
    print(f"DB Tables: {len(existing_tables)}")
    print(f"Matching: {len(model_tables & existing_tables)}")
    print(f"Missing in DB: {len(missing_in_db)}")
    print(f"Extra in DB: {len(extra_in_db)}")
    print()
    
    if missing_in_db:
        print("💡 RECOMMENDATION:")
        print("Run database migrations to create missing tables:")
        print("  cd api && alembic revision --autogenerate -m 'Add missing tables'")
        print("  cd api && alembic upgrade head")
        print()
        return False
    
    return True


if __name__ == "__main__":
    try:
        success = verify_tables()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
