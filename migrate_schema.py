#!/usr/bin/env python3
"""
Migrate SQLite schema to match API expectations
Add missing columns to sales table for analytics queries
"""

import sqlite3
from datetime import datetime

def migrate_schema():
    """Add missing columns to match API expectations"""
    
    conn = sqlite3.connect('api/rdios_dev.db')
    cursor = conn.cursor()
    
    print("🔄 Migrating schema to match API expectations...\n")
    
    # Get current columns
    cursor.execute("PRAGMA table_info(sales)")
    existing_cols = {row[1] for row in cursor.fetchall()}
    
    # Add missing columns to sales table
    missing_cols = {
        'gst_amount': 'REAL',
        'discount_amount': 'REAL',
        'payment_status': 'TEXT',
        'is_holiday': 'BOOLEAN',
        'sale_date': 'DATE',  # Alias for transaction_date
    }
    
    for col, dtype in missing_cols.items():
        if col not in existing_cols:
            try:
                if col == 'sale_date':
                    # Populate from transaction_date
                    cursor.execute(f"ALTER TABLE sales ADD COLUMN {col} {dtype}")
                    cursor.execute("UPDATE sales SET sale_date = DATE(transaction_date)")
                    print(f"  ✅ Added column: {col} ({dtype})")
                elif col == 'gst_amount':
                    # Calculate from tax (assuming tax is GST in India)
                    cursor.execute(f"ALTER TABLE sales ADD COLUMN {col} {dtype} DEFAULT 0")
                    cursor.execute("UPDATE sales SET gst_amount = COALESCE(tax, 0)")
                    print(f"  ✅ Added column: {col} ({dtype}) - populated from tax")
                elif col == 'discount_amount':
                    # Map from discount column
                    cursor.execute(f"ALTER TABLE sales ADD COLUMN {col} {dtype} DEFAULT 0")
                    cursor.execute("UPDATE sales SET discount_amount = COALESCE(discount, 0)")
                    print(f"  ✅ Added column: {col} ({dtype}) - populated from discount")
                elif col == 'payment_status':
                    # Default to 'paid'
                    cursor.execute(f"ALTER TABLE sales ADD COLUMN {col} {dtype} DEFAULT 'paid'")
                    print(f"  ✅ Added column: {col} ({dtype}) - default 'paid'")
                elif col == 'is_holiday':
                    # Default to false
                    cursor.execute(f"ALTER TABLE sales ADD COLUMN {col} {dtype} DEFAULT 0")
                    print(f"  ✅ Added column: {col} ({dtype}) - default false")
            except sqlite3.OperationalError as e:
                if "already exists" in str(e):
                    print(f"  ℹ️  Column already exists: {col}")
                else:
                    print(f"  ❌ Error adding column {col}: {e}")
    
    # Check sale_items table
    print("\n🔍 Checking sale_items table...")
    cursor.execute("PRAGMA table_info(sale_items)")
    sale_items_cols = {row[1] for row in cursor.fetchall()}
    
    missing_si_cols = {
        'gst_rate': 'REAL',
    }
    
    for col, dtype in missing_si_cols.items():
        if col not in sale_items_cols:
            try:
                cursor.execute(f"ALTER TABLE sale_items ADD COLUMN {col} {dtype} DEFAULT 0.05")
                print(f"  ✅ Added column to sale_items: {col} ({dtype})")
            except sqlite3.OperationalError as e:
                if "already exists" in str(e):
                    print(f"  ℹ️  Column already exists: {col}")
    
    # Commit changes
    conn.commit()
    
    # Verify
    print("\n✅ Verifying changes...")
    cursor.execute("PRAGMA table_info(sales)")
    cols = [row[1] for row in cursor.fetchall()]
    print(f"   Sales table now has {len(cols)} columns:")
    for col in sorted(cols):
        print(f"     - {col}")
    
    print("\n✅ Schema migration complete!")
    
    conn.close()

if __name__ == "__main__":
    migrate_schema()
