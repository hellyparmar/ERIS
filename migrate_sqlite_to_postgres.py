"""
Migrate data from SQLite to PostgreSQL
This script transfers all data from rdios_dev.db to the PostgreSQL database
"""
import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import logging
import sys

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

SQLITE_PATH = "rdios_dev.db"
PG_DSN = "host=localhost port=5433 dbname=enterprise_retail user=postgres password=EnterpriseRetail@2026"

# Tables in dependency order (foreign keys)
TABLE_ORDER = [
    "users",
    "organizations",
    "stores",
    "customers",
    "suppliers",
    "products",
    "inventory",
    "sales",
    "sale_items",
    "invoices",
    "invoice_payments",
    "payments",
    "purchase_orders",
    "purchase_order_items",
    "alerts",
    "customer_credits",
    "referrals",
    "messages",
    "community_listings",
    "bulk_buy_groups",
    "bulk_buy_participants",
    "sync_logs"
]

def table_exists_in_sqlite(conn, table_name):
    """Check if table exists in SQLite"""
    cur = conn.cursor()
    cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    return cur.fetchone() is not None

def convert_row_types(table, row, cols):
    """Convert SQLite types to PostgreSQL types"""
    converted = list(row)
    
    # Boolean conversions (SQLite stores as 0/1, PostgreSQL needs true/false)
    boolean_fields = {
        'organizations': ['is_active'],
        'stores': ['is_active'],
        'products': ['is_dead_stock', 'is_active'],
        'inventory': ['is_active'],
        'customers': ['is_active'],
        'sales': ['is_completed']
    }
    
    if table in boolean_fields:
        for field in boolean_fields[table]:
            if field in cols:
                idx = cols.index(field)
                if converted[idx] is not None:
                    converted[idx] = bool(converted[idx])
    
    return tuple(converted)

def migrate():
    """Migrate all data from SQLite to PostgreSQL"""
    try:
        # Connect to databases
        logger.info("Connecting to SQLite database...")
        sqlite_conn = sqlite3.connect(SQLITE_PATH)
        sqlite_conn.row_factory = sqlite3.Row
        
        logger.info("Connecting to PostgreSQL database...")
        pg_conn = psycopg2.connect(PG_DSN)
        pg_cur = pg_conn.cursor()
        
        total_rows = 0
        migrated_tables = 0
        
        # Skip tables with schema mismatches that need manual fixing
        skip_tables = {
            'customers',  # enum mismatch for message_channel
            'sale_items',  # column mismatch (total_price vs line_total)
        }
        
        logger.info(f"\nStarting migration of {len(TABLE_ORDER)} tables...\n")
        
        for table in TABLE_ORDER:
            try:
                # Skip problematic tables
                if table in skip_tables:
                    logger.info(f"⊘ {table}: skipped (schema mismatch - needs manual fix)")
                    continue
                
                # Check if table exists in SQLite
                if not table_exists_in_sqlite(sqlite_conn, table):
                    logger.info(f"⊘ {table}: not found in SQLite, skipping")
                    continue
                
                # Get data from SQLite
                cur = sqlite_conn.cursor()
                cur.execute(f"SELECT * FROM {table}")
                rows = cur.fetchall()
                
                if not rows:
                    logger.info(f"○ {table}: empty")
                    continue
                
                # Get column names
                cols = [d[0] for d in cur.description]
                
                # Convert types and insert into PostgreSQL
                converted_rows = [convert_row_types(table, r, cols) for r in rows]
                query = f"INSERT INTO {table} ({','.join(cols)}) VALUES %s ON CONFLICT DO NOTHING"
                execute_values(pg_cur, query, converted_rows, page_size=1000)
                pg_conn.commit()
                
                logger.info(f"✓ {table}: {len(rows):,} rows migrated")
                total_rows += len(rows)
                migrated_tables += 1
                
            except Exception as e:
                pg_conn.rollback()
                logger.error(f"✗ {table}: {e}")
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Migration complete!")
        logger.info(f"Tables migrated: {migrated_tables}/{len(TABLE_ORDER)}")
        logger.info(f"Total rows: {total_rows:,}")
        logger.info(f"{'='*60}\n")
        
        # Close connections
        sqlite_conn.close()
        pg_conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
