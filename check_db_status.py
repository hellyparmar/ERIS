#!/usr/bin/env python3
"""Quick diagnostic script to check database status"""
import sys
import os
sys.path.insert(0, '.')

# Check 1: Database type
print("=" * 60)
print("CHECK 1: Database Configuration")
print("=" * 60)
try:
    from api.db import engine
    print(f"✓ DB Type: {engine.dialect.name}")
    print(f"✓ DB URL: {str(engine.url).replace('%40', '@')}")
except Exception as e:
    print(f"✗ Error loading database: {e}")
    sys.exit(1)

# Check 2: Connection test
print("\n" + "=" * 60)
print("CHECK 2: Connection Test")
print("=" * 60)
try:
    from sqlalchemy import text
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))
        version = result.fetchone()[0]
        print(f"✓ Connection successful")
        print(f"✓ PostgreSQL version: {version[:50]}...")
except Exception as e:
    print(f"✗ Connection failed: {e}")
    sys.exit(1)

# Check 3: Tables in PostgreSQL
print("\n" + "=" * 60)
print("CHECK 3: PostgreSQL Tables")
print("=" * 60)
try:
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"✓ Total tables: {len(tables)}")
    if tables:
        print(f"✓ Sample tables: {', '.join(sorted(tables)[:10])}")
    else:
        print("⚠ WARNING: No tables found in PostgreSQL!")
except Exception as e:
    print(f"✗ Error inspecting tables: {e}")

# Check 4: SQLite file status
print("\n" + "=" * 60)
print("CHECK 4: SQLite File Status")
print("=" * 60)
sqlite_path = "api/rdios_dev.db"
if os.path.exists(sqlite_path):
    size_mb = os.path.getsize(sqlite_path) / (1024 * 1024)
    print(f"⚠ SQLite file exists: {sqlite_path}")
    print(f"⚠ Size: {size_mb:.2f} MB")
    print(f"⚠ This file should be removed or archived")
else:
    print(f"✓ No SQLite file found")

# Check 5: Hardcoded localhost references
print("\n" + "=" * 60)
print("CHECK 5: Hardcoded localhost in frontend")
print("=" * 60)
print("Run: grep -r 'localhost:8000' src/ --include='*.js' --include='*.jsx' -l")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("Database is configured for PostgreSQL ✓")
print("Next steps: Check if tables exist, remove SQLite, fix hardcoded URLs")
