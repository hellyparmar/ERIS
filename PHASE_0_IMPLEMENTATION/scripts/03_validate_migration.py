#!/usr/bin/env python3
"""
Database Validation Script
Validates PostgreSQL migration by comparing with SQLite

Usage:
    python validate_migration.py
"""

import sqlite3
import psycopg2
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

SQLITE_DB = "petpooja_retail_db.sqlite3"
PG_CONNECTION_STRING = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/enterprise_retail"
)

def validate():
    """Validate migration completeness"""
    
    logger.info("\n🔍 DATABASE MIGRATION VALIDATION")
    logger.info("=" * 60)
    
    # Connect to databases
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    pg_conn = psycopg2.connect(PG_CONNECTION_STRING)
    
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    tables = [
        'users', 'products', 'categories', 'locations',
        'inventory', 'customers', 'sales', 'sales_items',
        'invoices', 'invoice_items', 'bills', 'bill_items',
        'alerts', 'forecasts', 'reports', 'settings'
    ]
    
    all_valid = True
    total_sqlite = 0
    total_pg = 0
    
    logger.info("\n📊 RECORD COUNTS")
    logger.info("-" * 60)
    
    for table in tables:
        sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
        sqlite_count = sqlite_cursor.fetchone()[0]
        
        pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
        pg_count = pg_cursor.fetchone()[0]
        
        match = sqlite_count == pg_count
        symbol = "✅" if match else "❌"
        
        logger.info(f"{symbol} {table:20} SQLite: {sqlite_count:8,} | PostgreSQL: {pg_count:8,}")
        
        if not match:
            all_valid = False
        
        total_sqlite += sqlite_count
        total_pg += pg_count
    
    logger.info("-" * 60)
    total_match = total_sqlite == total_pg
    symbol = "✅" if total_match else "❌"
    logger.info(f"{symbol} {'TOTAL':20} SQLite: {total_sqlite:8,} | PostgreSQL: {total_pg:8,}")
    
    # Validation results
    logger.info("\n" + "=" * 60)
    if all_valid and total_match:
        logger.info("✅ VALIDATION PASSED - Migration successful!")
        logger.info(f"   Total records: {total_pg:,}")
        logger.info("=" * 60)
        return 0
    else:
        logger.info("❌ VALIDATION FAILED - Mismatch detected!")
        logger.info("   Please review the differences above")
        logger.info("=" * 60)
        return 1
    
    sqlite_conn.close()
    pg_conn.close()

if __name__ == "__main__":
    exit(validate())
