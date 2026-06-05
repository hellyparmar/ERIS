"""Direct seeding using environment-based connection"""
import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal
import random
import uuid
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# PostgreSQL connection
import psycopg2
from psycopg2 import sql

def get_connection():
    """Get database connection"""
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/r_dios_db")
    # Parse URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "").replace("postgresql+asyncpg://", "")
    
    parts = db_url.split("@")
    if len(parts) == 2:
        auth, host_db = parts
        user, password = auth.split(":")
        host, port, db = host_db.replace(":", "/").split("/")
        port = port or "5432"
    else:
        # Simple format
        return psycopg2.connect("dbname=r_dios_db user=postgres host=localhost")
    
    return psycopg2.connect(
        dbname=db, user=user, password=password,
        host=host, port=int(port)
    )

def seed_sales(conn, count=10000):
    """Seed sales table with synthetic data"""
    cur = conn.cursor()
    
    try:
        # Check existing
        cur.execute("SELECT COUNT(*) FROM sales")
        existing = cur.fetchone()[0]
        logger.info(f"Existing sales records: {existing}")
        
        if existing > 0:
            logger.info("⚠️  Database already has sales records")
            return existing
        
        # Get base IDs
        cur.execute("SELECT id FROM organizations LIMIT 1")
        org_id = cur.fetchone()[0]
        
        cur.execute("SELECT id FROM stores LIMIT 10")
        store_ids = [row[0] for row in cur.fetchall()]
        
        cur.execute("SELECT id FROM customers LIMIT 500")
        customer_ids = [row[0] for row in cur.fetchall()]
        
        cur.execute("SELECT id FROM users LIMIT 50")
        user_ids = [row[0] for row in cur.fetchall()]
        
        logger.info(f"Found: {len(store_ids)} stores, {len(customer_ids)} customers, {len(user_ids)} users")
        
        # Insert sales
        logger.info(f"Seeding {count} sales records...")
        
        start_date = datetime.utcnow() - timedelta(days=550)
        records = []
        
        for i in range(count):
            sale_date = start_date + timedelta(seconds=i * (550*86400//count))
            
            record = (
                str(uuid.uuid4()),  # id
                f"TXN-{i+1:08d}",    # transaction_id
                str(org_id),  # organization_id
                str(random.choice(store_ids)),  # store_id
                str(random.choice(customer_ids)) if random.random() > 0.3 else None,  # customer_id
                str(random.choice(user_ids)),  # cashier_id
                Decimal(str(random.uniform(100, 5000))).quantize(Decimal("0.01")),  # subtotal
                Decimal(str(random.uniform(0, 500))).quantize(Decimal("0.01")),  # discount
                Decimal(str(random.uniform(50, 800))).quantize(Decimal("0.01")),  # tax_amount
                Decimal(str(random.uniform(500, 6000))).quantize(Decimal("0.01")),  # total_amount
                Decimal(str(random.uniform(500, 6000))).quantize(Decimal("0.01")),  # amount_paid
                Decimal("0.00"),  # change_due
                random.choice(["cash", "card", "upi", "wallet"]),  # payment_method
                "paid",  # payment_status
                random.choice(["pos", "online", "manual"]),  # channel
                sale_date,  # transaction_date
                sale_date  # created_at
            )
            records.append(record)
            
            if (i+1) % 5000 == 0:
                logger.info(f"  {i+1}/{count} records prepared")
        
        # Batch insert
        values_template = ",".join(["%s"] * len(records[0]))
        placeholders = ",".join([f"({values_template})"] * len(records))
        
        columns = ["id", "transaction_id", "organization_id", "store_id", "customer_id", "cashier_id",
                  "subtotal", "discount", "tax_amount", "total_amount", "amount_paid", "change_due",
                  "payment_method", "payment_status", "channel", "transaction_date", "created_at"]
        
        insert_sql = f"INSERT INTO sales ({','.join(columns)}) VALUES {placeholders}"
        flat_records = [item for record in records for item in record]
        
        cur.execute(insert_sql, flat_records)
        conn.commit()
        
        cur.execute("SELECT COUNT(*) FROM sales")
        final_count = cur.fetchone()[0]
        logger.info(f"✓ Seeding complete! Total records: {final_count}")
        
        return final_count
    
    except Exception as e:
        logger.error(f"✗ Seeding failed: {e}")
        conn.rollback()
        return -1
    finally:
        cur.close()

if __name__ == "__main__":
    conn = get_connection()
    final_count = seed_sales(conn, count=100000)
    conn.close()
    
    logger.info("=" * 50)
    logger.info(f"Seeding Summary: {final_count} sales records")
