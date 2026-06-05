#!/usr/bin/env python3
"""Verify data in database"""
import os
import sys
from sqlalchemy import create_engine, text

db_url = "postgresql+psycopg2://eris_admin:admin1234@127.0.0.1:5432/eris_production"

try:
    engine = create_engine(db_url)
    with engine.connect() as conn:
        # Check table counts
        tables = ['product', 'customer', 'sale', 'sale_item', 'invoice', '"user"']
        print("\n📊 DATABASE CONTENTS:")
        print("=" * 60)
        
        for table in tables:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"{table.ljust(15)}: {count:>10,} records")
        
        print("=" * 60 + "\n")
        
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
