#!/usr/bin/env python3
"""
PostgreSQL Migration Script
Migrates data from SQLite to PostgreSQL

Usage:
    python migrate_sqlite_to_postgresql.py

Requirements:
    - PostgreSQL running and accessible
    - SQLite database (petpooja_retail_db.sqlite3)
    - Python packages: psycopg2, sqlite3, pandas
"""

import sqlite3
import psycopg2
import pandas as pd
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Database connections
SQLITE_DB = "petpooja_retail_db.sqlite3"
PG_CONNECTION_STRING = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/enterprise_retail"
)

class MigrationManager:
    def __init__(self):
        self.sqlite_conn = None
        self.pg_conn = None
        self.migration_log = []
        self.batch_size = 1000
        self.tables = [
            'users', 'products', 'categories', 'locations',
            'inventory', 'customers', 'sales', 'sales_items',
            'invoices', 'invoice_items', 'bills', 'bill_items',
            'alerts', 'forecasts', 'reports', 'settings'
        ]
    
    def connect_sqlite(self):
        """Connect to SQLite database"""
        try:
            self.sqlite_conn = sqlite3.connect(SQLITE_DB)
            self.sqlite_conn.row_factory = sqlite3.Row
            logger.info(f"✅ Connected to SQLite: {SQLITE_DB}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to SQLite: {e}")
            return False
    
    def connect_postgresql(self):
        """Connect to PostgreSQL database"""
        try:
            self.pg_conn = psycopg2.connect(PG_CONNECTION_STRING)
            logger.info("✅ Connected to PostgreSQL")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to PostgreSQL: {e}")
            return False
    
    def backup_postgresql(self):
        """Create backup of PostgreSQL before migration"""
        try:
            os.system(f"pg_dump {PG_CONNECTION_STRING} > backup_pg_$(date +%Y%m%d_%H%M%S).sql")
            logger.info("✅ PostgreSQL backup created")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to backup PostgreSQL: {e}")
            return False
    
    def disable_constraints(self):
        """Disable foreign key constraints during migration"""
        try:
            cursor = self.pg_conn.cursor()
            for table in self.tables:
                cursor.execute(f"ALTER TABLE {table} DISABLE TRIGGER ALL")
            self.pg_conn.commit()
            logger.info("✅ Foreign key constraints disabled")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to disable constraints: {e}")
            return False
    
    def enable_constraints(self):
        """Re-enable foreign key constraints after migration"""
        try:
            cursor = self.pg_conn.cursor()
            for table in self.tables:
                cursor.execute(f"ALTER TABLE {table} ENABLE TRIGGER ALL")
            self.pg_conn.commit()
            logger.info("✅ Foreign key constraints enabled")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to enable constraints: {e}")
            return False
    
    def migrate_table(self, table_name):
        """Migrate single table from SQLite to PostgreSQL"""
        try:
            # Get data from SQLite
            sqlite_cursor = self.sqlite_conn.cursor()
            sqlite_cursor.execute(f"SELECT * FROM {table_name}")
            rows = sqlite_cursor.fetchall()
            
            if not rows:
                logger.info(f"  ⚠️  {table_name}: No data to migrate")
                return 0
            
            # Get column names
            columns = [description[0] for description in sqlite_cursor.description]
            
            # Prepare data for PostgreSQL
            values_list = [tuple(row) for row in rows]
            
            # Insert in batches
            pg_cursor = self.pg_conn.cursor()
            total_inserted = 0
            
            for i in range(0, len(values_list), self.batch_size):
                batch = values_list[i:i + self.batch_size]
                
                placeholders = ','.join(
                    [f"({','.join(['%s']*len(columns))})" for _ in batch]
                )
                query = f"""
                    INSERT INTO {table_name} ({','.join(columns)})
                    VALUES {placeholders}
                    ON CONFLICT DO NOTHING
                """
                
                flat_batch = [item for sublist in batch for item in sublist]
                pg_cursor.execute(query, flat_batch)
                
                total_inserted += len(batch)
                
                if (i // self.batch_size + 1) % 10 == 0:
                    logger.info(f"  ⏳ {table_name}: Inserted {total_inserted} rows...")
            
            self.pg_conn.commit()
            logger.info(f"  ✅ {table_name}: {total_inserted} rows migrated")
            
            return total_inserted
        
        except Exception as e:
            logger.error(f"  ❌ {table_name}: Migration failed - {e}")
            self.pg_conn.rollback()
            return 0
    
    def validate_migration(self):
        """Validate migration by comparing row counts"""
        logger.info("\n📊 VALIDATING MIGRATION")
        logger.info("=" * 50)
        
        sqlite_cursor = self.sqlite_conn.cursor()
        pg_cursor = self.pg_conn.cursor()
        
        all_match = True
        total_sqlite = 0
        total_pg = 0
        
        for table in self.tables:
            try:
                sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                sqlite_count = sqlite_cursor.fetchone()[0]
                
                pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                pg_count = pg_cursor.fetchone()[0]
                
                match = "✅" if sqlite_count == pg_count else "❌"
                print(f"{match} {table:20} SQLite: {sqlite_count:10,} | PostgreSQL: {pg_count:10,}")
                
                if sqlite_count != pg_count:
                    all_match = False
                
                total_sqlite += sqlite_count
                total_pg += pg_count
            
            except Exception as e:
                logger.error(f"  ❌ {table}: Validation failed - {e}")
                all_match = False
        
        logger.info("=" * 50)
        print(f"{'✅' if total_sqlite == total_pg else '❌'} TOTAL: SQLite: {total_sqlite:,} | PostgreSQL: {total_pg:,}")
        logger.info("=" * 50)
        
        return all_match
    
    def execute_migration(self):
        """Execute complete migration"""
        logger.info("🚀 STARTING MIGRATION")
        logger.info("=" * 50)
        
        # Step 1: Connect
        logger.info("\n📡 STEP 1: Connecting to databases...")
        if not self.connect_sqlite():
            return False
        if not self.connect_postgresql():
            return False
        
        # Step 2: Backup
        logger.info("\n💾 STEP 2: Creating backups...")
        self.backup_postgresql()
        
        # Step 3: Disable constraints
        logger.info("\n🔒 STEP 3: Disabling constraints...")
        self.disable_constraints()
        
        # Step 4: Migrate
        logger.info("\n📋 STEP 4: Migrating tables...")
        total_migrated = 0
        for table in self.tables:
            rows = self.migrate_table(table)
            total_migrated += rows
        
        # Step 5: Enable constraints
        logger.info("\n🔓 STEP 5: Enabling constraints...")
        self.enable_constraints()
        
        # Step 6: Validate
        logger.info("\n✔️ STEP 6: Validating migration...")
        validation_passed = self.validate_migration()
        
        # Final status
        logger.info("\n" + "=" * 50)
        if validation_passed:
            logger.info("✅ MIGRATION SUCCESSFUL!")
            logger.info(f"   Total records migrated: {total_migrated:,}")
            logger.info("=" * 50)
            return True
        else:
            logger.error("❌ MIGRATION FAILED - Count mismatch!")
            logger.error("   Please review errors above")
            logger.error("=" * 50)
            return False
    
    def cleanup(self):
        """Close database connections"""
        if self.sqlite_conn:
            self.sqlite_conn.close()
        if self.pg_conn:
            self.pg_conn.close()


def main():
    manager = MigrationManager()
    
    try:
        success = manager.execute_migration()
        sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        logger.warning("\n⚠️ Migration interrupted by user")
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
    
    finally:
        manager.cleanup()


if __name__ == "__main__":
    main()
