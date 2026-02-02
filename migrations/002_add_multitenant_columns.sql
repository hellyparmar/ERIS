-- ============================================================
-- R-DIOS Multi-Tenant Migration
-- Phase 1B: Add organization_id and store_id to Existing Tables
-- ============================================================

-- This migration adds multi-tenant columns to all existing tables
-- Run AFTER creating organizations and stores tables

BEGIN;

-- ============================================================
-- 1. ALTER USERS TABLE
-- ============================================================

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id);

-- Add assigned_stores (array of store IDs user can access)
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS assigned_stores UUID[] DEFAULT '{}';

-- Create index
CREATE INDEX IF NOT EXISTS idx_users_org ON users(organization_id);

COMMENT ON COLUMN users.organization_id IS 'Organization this user belongs to';
COMMENT ON COLUMN users.assigned_stores IS 'Stores this user has access to';


-- ============================================================
-- 2. ALTER PRODUCTS TABLE
-- ============================================================

ALTER TABLE products 
ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id);

CREATE INDEX IF NOT EXISTS idx_products_org ON products(organization_id);
CREATE INDEX IF NOT EXISTS idx_products_org_sku ON products(organization_id, sku);

COMMENT ON COLUMN products.organization_id IS 'Product belongs to this organization';


-- ============================================================
-- 3. ALTER CUSTOMERS TABLE
-- ============================================================

ALTER TABLE customers 
ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id);

CREATE INDEX IF NOT EXISTS idx_customers_org ON customers(organization_id);
CREATE INDEX IF NOT EXISTS idx_customers_org_phone ON customers(organization_id, phone);

COMMENT ON COLUMN customers.organization_id IS 'Customer belongs to this organization';


-- ============================================================
-- 4. ALTER SUPPLIERS TABLE
-- ============================================================

ALTER TABLE suppliers 
ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id);

CREATE INDEX IF NOT EXISTS idx_suppliers_org ON suppliers(organization_id);

COMMENT ON COLUMN suppliers.organization_id IS 'Supplier belongs to this organization';


-- ============================================================
-- 5. ALTER CATEGORIES TABLE
-- ============================================================

ALTER TABLE categories 
ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id);

CREATE INDEX IF NOT EXISTS idx_categories_org ON categories(organization_id);

COMMENT ON COLUMN categories.organization_id IS 'Category belongs to this organization';


-- ============================================================
--6. ALTER INVOICES TABLE
-- ============================================================

ALTER TABLE invoices 
ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id),
ADD COLUMN IF NOT EXISTS store_id UUID REFERENCES stores(id);

CREATE INDEX IF NOT EXISTS idx_invoices_org ON invoices(organization_id);
CREATE INDEX IF NOT EXISTS idx_invoices_store ON invoices(store_id);
CREATE INDEX IF NOT EXISTS idx_invoices_org_date ON invoices(organization_id, invoice_date DESC);

COMMENT ON COLUMN invoices.organization_id IS 'Invoice belongs to this organization';
COMMENT ON COLUMN invoices.store_id IS 'Invoice created at this store';


-- ============================================================
-- 7. ALTER PAYMENTS TABLE
-- ============================================================

ALTER TABLE payments 
ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id),
ADD COLUMN IF NOT EXISTS store_id UUID REFERENCES stores(id);

CREATE INDEX IF NOT EXISTS idx_payments_org ON payments(organization_id);
CREATE INDEX IF NOT EXISTS idx_payments_store ON payments(store_id);

COMMENT ON COLUMN payments.organization_id IS 'Payment belongs to this organization';
COMMENT ON COLUMN payments.store_id IS 'Payment received at this store';


-- ============================================================
-- 8. ALTER INVENTORY TABLE
-- ============================================================

ALTER TABLE inventory 
ADD COLUMN IF NOT EXISTS store_id UUID REFERENCES stores(id);

CREATE INDEX IF NOT EXISTS idx_inventory_store ON inventory(store_id);
CREATE INDEX IF NOT EXISTS idx_inventory_store_product ON inventory(store_id, product_id);

COMMENT ON COLUMN inventory.store_id IS 'Inventory at this store location';


-- ============================================================
-- 9. DATA MIGRATION
-- ============================================================

-- Set demo organization and store IDs
DO $$
DECLARE
    demo_org_id UUID := '00000000-0000-0000-0000-000000000001';
    demo_store_id UUID := '00000000-0000-0000-0000-000000000002';
BEGIN
    -- Migrate users
    UPDATE users 
    SET organization_id = demo_org_id,
        assigned_stores = ARRAY[demo_store_id]
    WHERE organization_id IS NULL;
    
    -- Migrate products
    UPDATE products 
    SET organization_id = demo_org_id
    WHERE organization_id IS NULL;
    
    -- Migrate customers
    UPDATE customers 
    SET organization_id = demo_org_id
    WHERE organization_id IS NULL;
    
    -- Migrate suppliers
    UPDATE suppliers 
    SET organization_id = demo_org_id
    WHERE organization_id IS NULL;
    
    -- Migrate categories
    UPDATE categories 
    SET organization_id = demo_org_id
    WHERE organization_id IS NULL;
    
    -- Migrate invoices
    UPDATE invoices 
    SET organization_id = demo_org_id,
        store_id = demo_store_id
    WHERE organization_id IS NULL;
    
    -- Migrate payments
    UPDATE payments 
    SET organization_id = demo_org_id,
        store_id = demo_store_id
    WHERE organization_id IS NULL;
    
    -- Migrate inventory
    UPDATE inventory 
    SET store_id = demo_store_id
    WHERE store_id IS NULL;
    
    RAISE NOTICE 'Data migration completed successfully';
END $$;


-- ============================================================
-- 10. ENFORCE NOT NULL CONSTRAINTS
-- ============================================================

-- After data migration, make columns NOT NULL
ALTER TABLE users ALTER COLUMN organization_id SET NOT NULL;
ALTER TABLE products ALTER COLUMN organization_id SET NOT NULL;
ALTER TABLE customers ALTER COLUMN organization_id SET NOT NULL;
ALTER TABLE suppliers ALTER COLUMN organization_id SET NOT NULL;
ALTER TABLE categories ALTER COLUMN organization_id SET NOT NULL;
ALTER TABLE invoices ALTER COLUMN organization_id SET NOT NULL;
ALTER TABLE invoices ALTER COLUMN store_id SET NOT NULL;
ALTER TABLE payments ALTER COLUMN organization_id SET NOT NULL;
ALTER TABLE inventory ALTER COLUMN store_id SET NOT NULL;


-- ============================================================
-- 11. VERIFICATION
-- ============================================================

DO $$
DECLARE
    org_count INT;
    users_migrated INT;
    products_migrated INT;
    invoices_migrated INT;
BEGIN
    -- Count organizations
    SELECT COUNT(*) INTO org_count FROM organizations;
    
    -- Count migrated data
    SELECT COUNT(*) INTO users_migrated FROM users WHERE organization_id IS NOT NULL;
    SELECT COUNT(*) INTO products_migrated FROM products WHERE organization_id IS NOT NULL;
    SELECT COUNT(*) INTO invoices_migrated FROM invoices WHERE organization_id IS NOT NULL AND store_id IS NOT NULL;
    
    RAISE NOTICE 'Organizations: %', org_count;
    RAISE NOTICE 'Users migrated: %', users_migrated;
    RAISE NOTICE 'Products migrated: %', products_migrated;
    RAISE NOTICE 'Invoices migrated: %', invoices_migrated;
    
    IF org_count = 0 THEN
        RAISE EXCEPTION 'No organizations found! Run 001_create_organizations_stores.sql first';
    END IF;
END $$;

COMMIT;

-- Success message
SELECT 'Multi-tenant migration completed successfully!' AS status;
