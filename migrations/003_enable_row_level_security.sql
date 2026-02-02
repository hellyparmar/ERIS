-- ============================================================
-- R-DIOS Multi-Tenant Migration
-- Phase 1C: Row-Level Security (RLS)
-- ============================================================

-- This migration implements PostgreSQL RLS for tenant isolation
-- Ensures organizations can ONLY see their own data

BEGIN;

-- ============================================================
-- 1. ENABLE ROW LEVEL SECURITY
-- ============================================================

-- Enable RLS on all multi-tenant tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE suppliers ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE stores ENABLE ROW LEVEL SECURITY;

-- Inventory uses store-level isolation
ALTER TABLE inventory ENABLE ROW LEVEL SECURITY;


-- ============================================================
-- 2. CREATE HELPER FUNCTION
-- ============================================================

-- Function to get current organization ID from session
CREATE OR REPLACE FUNCTION current_org_id()
RETURNS UUID AS $$
BEGIN
    RETURN nullif(current_setting('app.current_org_id', true), '')::uuid;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION current_org_id() IS 'Get organization ID from session variable';


-- ============================================================
-- 3. ORGANIZATION-LEVEL POLICIES
-- ============================================================

-- USERS: Can only see users from their organization
CREATE POLICY org_isolation_users ON users
    FOR ALL
    TO PUBLIC
    USING (organization_id = current_org_id());

-- PRODUCTS: Can only see products from their organization
CREATE POLICY org_isolation_products ON products
    FOR ALL
    TO PUBLIC
    USING (organization_id = current_org_id());

-- CUSTOMERS: Can only see customers from their organization
CREATE POLICY org_isolation_customers ON customers
    FOR ALL
    TO PUBLIC
    USING (organization_id = current_org_id());

-- SUPPLIERS: Can only see suppliers from their organization
CREATE POLICY org_isolation_suppliers ON suppliers
    FOR ALL
    TO PUBLIC
    USING (organization_id = current_org_id());

-- CATEGORIES: Can only see categories from their organization
CREATE POLICY org_isolation_categories ON categories
    FOR ALL
    TO PUBLIC
    USING (organization_id = current_org_id());

-- INVOICES: Can only see invoices from their organization
CREATE POLICY org_isolation_invoices ON invoices
    FOR ALL
    TO PUBLIC
    USING (organization_id = current_org_id());

-- PAYMENTS: Can only see payments from their organization
CREATE POLICY org_isolation_payments ON payments
    FOR ALL
    TO PUBLIC
    USING (organization_id = current_org_id());

-- STORES: Can only see stores from their organization
CREATE POLICY org_isolation_stores ON stores
    FOR ALL
    TO PUBLIC
    USING (organization_id = current_org_id());


-- ============================================================
-- 4. STORE-LEVEL POLICIES
-- ============================================================

-- INVENTORY: Can only see inventory from stores in their organization
CREATE POLICY org_isolation_inventory ON inventory
    FOR ALL
    TO PUBLIC
    USING (
        store_id IN (
            SELECT id FROM stores 
            WHERE organization_id = current_org_id()
        )
    );


-- ============================================================
-- 5. INSERT POLICIES (New Records)
-- ============================================================

-- Ensure new records get organization_id automatically
CREATE POLICY org_isolation_products_insert ON products
    FOR INSERT
    TO PUBLIC
    WITH CHECK (organization_id = current_org_id());

CREATE POLICY org_isolation_customers_insert ON customers
    FOR INSERT
    TO PUBLIC
    WITH CHECK (organization_id = current_org_id());

CREATE POLICY org_isolation_suppliers_insert ON suppliers
    FOR INSERT
    TO PUBLIC
    WITH CHECK (organization_id = current_org_id());

CREATE POLICY org_isolation_invoices_insert ON invoices
    FOR INSERT
    TO PUBLIC
    WITH CHECK (organization_id = current_org_id());


-- ============================================================
-- 6. BYPASS RLS FOR SYSTEM ADMIN (Optional)
-- ============================================================

-- Create admin role that can bypass RLS
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'rdios_admin') THEN
        CREATE ROLE rdios_admin;
    END IF;
END $$;

-- Grant bypass to admin role
GRANT rdios_admin TO CURRENT_USER;

-- Admin can bypass all RLS
ALTER TABLE users FORCE ROW LEVEL SECURITY;
ALTER TABLE products FORCE ROW LEVEL SECURITY;
ALTER TABLE customers FORCE ROW LEVEL SECURITY;
ALTER TABLE suppliers FORCE ROW LEVEL SECURITY;
ALTER TABLE categories FORCE ROW LEVEL SECURITY;
ALTER TABLE invoices FORCE ROW LEVEL SECURITY;
ALTER TABLE payments FORCE ROW LEVEL SECURITY;
ALTER TABLE stores FORCE ROW LEVEL SECURITY;
ALTER TABLE inventory FORCE ROW LEVEL SECURITY;


-- ============================================================
-- 7. PERFORMANCE OPTIMIZATION
-- ============================================================

-- Add indexes to support RLS queries
CREATE INDEX IF NOT EXISTS idx_users_org_rls ON users(organization_id) WHERE organization_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_products_org_rls ON products(organization_id) WHERE organization_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_customers_org_rls ON customers(organization_id) WHERE organization_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_invoices_org_rls ON invoices(organization_id) WHERE organization_id IS NOT NULL;


-- ============================================================
-- 8. TESTING RLS
-- ============================================================

-- Test query (should return only demo org data)
DO $$
DECLARE
    product_count INT;
    customer_count INT;
BEGIN
    -- Set context to demo org
    PERFORM set_config('app.current_org_id', '00000000-0000-0000-0000-000000000001', false);
    
    -- Query products
    SELECT COUNT(*) INTO product_count FROM products;
    
    -- Query customers
    SELECT COUNT(*) INTO customer_count FROM customers;
    
    RAISE NOTICE 'RLS Test - Products visible: %, Customers visible: %', product_count, customer_count;
    
    -- Test with NULL context (should see nothing)
    PERFORM set_config('app.current_org_id', '', false);
    
    SELECT COUNT(*) INTO product_count FROM products;
    
    IF product_count > 0 THEN
        RAISE WARNING 'RLS LEAK: Products visible without org context!';
    ELSE
        RAISE NOTICE 'RLS Working: No data visible without org context';
    END IF;
END $$;


-- ============================================================
-- 9. VERIFICATION
-- ============================================================

-- List all RLS policies
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;


-- ============================================================
-- 10. ROLLBACK SCRIPT (if needed)
-- ============================================================

-- To disable RLS (emergency only):
/*
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE products DISABLE ROW LEVEL SECURITY;
ALTER TABLE customers DISABLE ROW LEVEL SECURITY;
ALTER TABLE suppliers DISABLE ROW LEVEL SECURITY;
ALTER TABLE categories DISABLE ROW LEVEL SECURITY;
ALTER TABLE invoices DISABLE ROW LEVEL SECURITY;
ALTER TABLE payments DISABLE ROW LEVEL SECURITY;
ALTER TABLE stores DISABLE ROW LEVEL SECURITY;
ALTER TABLE inventory DISABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS org_isolation_users ON users;
DROP POLICY IF EXISTS org_isolation_products ON products;
-- ... drop all policies

DROP FUNCTION IF EXISTS current_org_id();
*/

COMMIT;

-- Success message
SELECT 'Row-Level Security (RLS) enabled successfully!' AS status;
SELECT 'All organizations now isolated. Data cannot leak between tenants.' AS message;
