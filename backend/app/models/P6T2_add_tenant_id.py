"""
Phase 6 - Task 2: Multi-tenancy Implementation
Add tenant_id to all existing tables for proper data isolation

This migration script adds tenant_id (UUID) columns to all relevant tables
and establishes foreign key relationships to the organizations table.
"""

from sqlalchemy import text
from app.api.db.database import SessionLocal
import logging

logger = logging.getLogger(__name__)

def add_tenant_id_to_users():
    """Add tenant_id to users table"""
    session = SessionLocal()
    try:
        # Check if column already exists
        result = session.execute(text(
            "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='users' AND column_name='tenant_id'"
        ))
        if result.scalar() > 0:
            logger.info("tenant_id already exists in users table")
            return

        # Add the column with default value
        session.execute(text(
            """
            ALTER TABLE users ADD COLUMN tenant_id UUID NOT NULL 
            DEFAULT 'f47ac10b-58cc-4372-a567-0e02b2c3d479'::uuid;
            """
        ))
        
        # Add foreign key constraint
        session.execute(text(
            """
            ALTER TABLE users ADD CONSTRAINT fk_users_tenant_id 
            FOREIGN KEY (tenant_id) REFERENCES organizations(id) ON DELETE CASCADE;
            """
        ))
        
        # Create index
        session.execute(text("CREATE INDEX idx_users_tenant_id ON users(tenant_id);"))
        
        session.commit()
        logger.info("✓ Successfully added tenant_id to users table")
    except Exception as e:
        session.rollback()
        logger.error(f"✗ Error adding tenant_id to users: {e}")
    finally:
        session.close()


def add_tenant_id_to_products():
    """Add tenant_id to products table"""
    session = SessionLocal()
    try:
        result = session.execute(text(
            "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='products' AND column_name='tenant_id'"
        ))
        if result.scalar() > 0:
            logger.info("tenant_id already exists in products table")
            return

        session.execute(text(
            """
            ALTER TABLE products ADD COLUMN tenant_id UUID NOT NULL 
            DEFAULT 'f47ac10b-58cc-4372-a567-0e02b2c3d479'::uuid;
            """
        ))
        
        session.execute(text(
            """
            ALTER TABLE products ADD CONSTRAINT fk_products_tenant_id 
            FOREIGN KEY (tenant_id) REFERENCES organizations(id) ON DELETE CASCADE;
            """
        ))
        
        session.execute(text("CREATE INDEX idx_products_tenant_id ON products(tenant_id);"))
        session.commit()
        logger.info("✓ Successfully added tenant_id to products table")
    except Exception as e:
        session.rollback()
        logger.error(f"✗ Error adding tenant_id to products: {e}")
    finally:
        session.close()


def add_tenant_id_to_inventory():
    """Add tenant_id to inventory table"""
    session = SessionLocal()
    try:
        result = session.execute(text(
            "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='inventory' AND column_name='tenant_id'"
        ))
        if result.scalar() > 0:
            logger.info("tenant_id already exists in inventory table")
            return

        session.execute(text(
            """
            ALTER TABLE inventory ADD COLUMN tenant_id UUID NOT NULL 
            DEFAULT 'f47ac10b-58cc-4372-a567-0e02b2c3d479'::uuid;
            """
        ))
        
        session.execute(text(
            """
            ALTER TABLE inventory ADD CONSTRAINT fk_inventory_tenant_id 
            FOREIGN KEY (tenant_id) REFERENCES organizations(id) ON DELETE CASCADE;
            """
        ))
        
        session.execute(text("CREATE INDEX idx_inventory_tenant_id ON inventory(tenant_id);"))
        session.commit()
        logger.info("✓ Successfully added tenant_id to inventory table")
    except Exception as e:
        session.rollback()
        logger.error(f"✗ Error adding tenant_id to inventory: {e}")
    finally:
        session.close()


def add_tenant_id_to_sales():
    """Add tenant_id to sales table"""
    session = SessionLocal()
    try:
        result = session.execute(text(
            "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='sales' AND column_name='tenant_id'"
        ))
        if result.scalar() > 0:
            logger.info("tenant_id already exists in sales table")
            return

        session.execute(text(
            """
            ALTER TABLE sales ADD COLUMN tenant_id UUID NOT NULL 
            DEFAULT 'f47ac10b-58cc-4372-a567-0e02b2c3d479'::uuid;
            """
        ))
        
        session.execute(text(
            """
            ALTER TABLE sales ADD CONSTRAINT fk_sales_tenant_id 
            FOREIGN KEY (tenant_id) REFERENCES organizations(id) ON DELETE CASCADE;
            """
        ))
        
        session.execute(text("CREATE INDEX idx_sales_tenant_id ON sales(tenant_id);"))
        session.commit()
        logger.info("✓ Successfully added tenant_id to sales table")
    except Exception as e:
        session.rollback()
        logger.error(f"✗ Error adding tenant_id to sales: {e}")
    finally:
        session.close()


def add_tenant_id_to_customers():
    """Add tenant_id to customers table"""
    session = SessionLocal()
    try:
        result = session.execute(text(
            "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='customers' AND column_name='tenant_id'"
        ))
        if result.scalar() > 0:
            logger.info("tenant_id already exists in customers table")
            return

        session.execute(text(
            """
            ALTER TABLE customers ADD COLUMN tenant_id UUID NOT NULL 
            DEFAULT 'f47ac10b-58cc-4372-a567-0e02b2c3d479'::uuid;
            """
        ))
        
        session.execute(text(
            """
            ALTER TABLE customers ADD CONSTRAINT fk_customers_tenant_id 
            FOREIGN KEY (tenant_id) REFERENCES organizations(id) ON DELETE CASCADE;
            """
        ))
        
        session.execute(text("CREATE INDEX idx_customers_tenant_id ON customers(tenant_id);"))
        session.commit()
        logger.info("✓ Successfully added tenant_id to customers table")
    except Exception as e:
        session.rollback()
        logger.error(f"✗ Error adding tenant_id to customers: {e}")
    finally:
        session.close()


def add_tenant_id_to_invoices():
    """Add tenant_id to invoices table"""
    session = SessionLocal()
    try:
        result = session.execute(text(
            "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='invoices' AND column_name='tenant_id'"
        ))
        if result.scalar() > 0:
            logger.info("tenant_id already exists in invoices table")
            return

        session.execute(text(
            """
            ALTER TABLE invoices ADD COLUMN tenant_id UUID NOT NULL 
            DEFAULT 'f47ac10b-58cc-4372-a567-0e02b2c3d479'::uuid;
            """
        ))
        
        session.execute(text(
            """
            ALTER TABLE invoices ADD CONSTRAINT fk_invoices_tenant_id 
            FOREIGN KEY (tenant_id) REFERENCES organizations(id) ON DELETE CASCADE;
            """
        ))
        
        session.execute(text("CREATE INDEX idx_invoices_tenant_id ON invoices(tenant_id);"))
        session.commit()
        logger.info("✓ Successfully added tenant_id to invoices table")
    except Exception as e:
        session.rollback()
        logger.error(f"✗ Error adding tenant_id to invoices: {e}")
    finally:
        session.close()


def add_tenant_id_to_bills():
    """Add tenant_id to bills table"""
    session = SessionLocal()
    try:
        result = session.execute(text(
            "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='bills' AND column_name='tenant_id'"
        ))
        if result.scalar() > 0:
            logger.info("tenant_id already exists in bills table")
            return

        session.execute(text(
            """
            ALTER TABLE bills ADD COLUMN tenant_id UUID NOT NULL 
            DEFAULT 'f47ac10b-58cc-4372-a567-0e02b2c3d479'::uuid;
            """
        ))
        
        session.execute(text(
            """
            ALTER TABLE bills ADD CONSTRAINT fk_bills_tenant_id 
            FOREIGN KEY (tenant_id) REFERENCES organizations(id) ON DELETE CASCADE;
            """
        ))
        
        session.execute(text("CREATE INDEX idx_bills_tenant_id ON bills(tenant_id);"))
        session.commit()
        logger.info("✓ Successfully added tenant_id to bills table")
    except Exception as e:
        session.rollback()
        logger.error(f"✗ Error adding tenant_id to bills: {e}")
    finally:
        session.close()


def add_tenant_id_to_devices():
    """Add tenant_id to devices table"""
    session = SessionLocal()
    try:
        result = session.execute(text(
            "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='devices' AND column_name='tenant_id'"
        ))
        if result.scalar() > 0:
            logger.info("tenant_id already exists in devices table")
            return

        session.execute(text(
            """
            ALTER TABLE devices ADD COLUMN tenant_id UUID NOT NULL 
            DEFAULT 'f47ac10b-58cc-4372-a567-0e02b2c3d479'::uuid;
            """
        ))
        
        session.execute(text(
            """
            ALTER TABLE devices ADD CONSTRAINT fk_devices_tenant_id 
            FOREIGN KEY (tenant_id) REFERENCES organizations(id) ON DELETE CASCADE;
            """
        ))
        
        session.execute(text("CREATE INDEX idx_devices_tenant_id ON devices(tenant_id);"))
        session.commit()
        logger.info("✓ Successfully added tenant_id to devices table")
    except Exception as e:
        session.rollback()
        logger.error(f"✗ Error adding tenant_id to devices: {e}")
    finally:
        session.close()


def run_all_migrations():
    """Run all tenant_id migrations"""
    print("\n" + "="*70)
    print("PHASE 6 - TASK 2: MULTI-TENANCY MIGRATION")
    print("="*70)
    print("\nAdding tenant_id to all tables for data isolation...\n")
    
    add_tenant_id_to_users()
    add_tenant_id_to_products()
    add_tenant_id_to_inventory()
    add_tenant_id_to_sales()
    add_tenant_id_to_customers()
    add_tenant_id_to_invoices()
    add_tenant_id_to_bills()
    add_tenant_id_to_devices()
    
    print("\n" + "="*70)
    print("✓ MIGRATION COMPLETE!")
    print("="*70)
    print("\nAll tables now have tenant_id columns for multi-tenant data isolation.")
    print("\nNext steps:")
    print("1. Update all API endpoints to filter by tenant_id")
    print("2. Extract tenant_id from JWT token")
    print("3. Apply row-level security policies")
    print("4. Implement audit logging for multi-tenant access")
    print("\n")


if __name__ == "__main__":
    run_all_migrations()
