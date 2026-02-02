-- ============================================================
-- R-DIOS Multi-Tenant Migration
-- Phase 1A: Organizations & Stores Schema
-- ============================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- 1. ORGANIZATIONS TABLE
-- ============================================================

CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Basic Information
    name VARCHAR(255) NOT NULL,
    legal_name VARCHAR(255),
    gstin VARCHAR(15) UNIQUE,
    pan VARCHAR(10),
    
    -- Address (JSON structure)
    address JSONB DEFAULT '{}'::jsonb,
    
    -- Contact
    contact_email VARCHAR(255),
    contact_phone VARCHAR(20),
    
    -- Subscription & Billing
    subscription_plan VARCHAR(50) DEFAULT 'free',
    subscription_status VARCHAR(20) DEFAULT 'trial',
    trial_ends_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '30 days',
    subscription_started_at TIMESTAMPTZ,
    subscription_ends_at TIMESTAMPTZ,
    
    -- Payment
    billing_address JSONB DEFAULT '{}'::jsonb,
    upi_vpa VARCHAR(100),
    
    -- Settings (extensible)
    settings JSONB DEFAULT '{
        "currency": "INR",
        "timezone": "Asia/Kolkata",
        "date_format": "DD/MM/YYYY",
        "fiscal_year_start": "04-01"
    }'::jsonb,
    
    -- Logo
    logo_url VARCHAR(500),
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    
    -- Deleted (soft delete)
    deleted_at TIMESTAMPTZ,
    
    CONSTRAINT valid_gstin CHECK (gstin IS NULL OR LENGTH(gstin) = 15),
    CONSTRAINT valid_pan CHECK (pan IS NULL OR LENGTH(pan) = 10)
);

-- Indexes for organizations
CREATE INDEX idx_organizations_gstin ON organizations(gstin) WHERE gstin IS NOT NULL;
CREATE INDEX idx_organizations_active ON organizations(is_active) WHERE is_active = true;
CREATE INDEX idx_organizations_plan ON organizations(subscription_plan);
CREATE INDEX idx_organizations_created ON organizations(created_at DESC);

-- Comments
COMMENT ON TABLE organizations IS 'Multi-tenant organizations (companies)';
COMMENT ON COLUMN organizations.gstin IS 'GST Identification Number (India)';
COMMENT ON COLUMN organizations.pan IS 'Permanent Account Number (India)';


-- ============================================================
-- 2. STORES TABLE
-- ============================================================

CREATE TABLE IF NOT EXISTS stores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Basic Information
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50),
    
    -- Address (JSON structure)
    address JSONB DEFAULT '{
        "line1": "",
        "line2": "",
        "city": "",
        "state": "",
        "state_code": "",
        "pincode": "",
        "country": "India"
    }'::jsonb,
    
    -- Store Type
    store_type VARCHAR(50) DEFAULT 'retail',
    
    -- Contact
    manager_name VARCHAR(255),
    contact_phone VARCHAR(20),
    contact_email VARCHAR(255),
    
    -- Operating Hours
    operating_hours JSONB DEFAULT '{
        "monday": {"open": "09:00", "close": "21:00"},
        "tuesday": {"open": "09:00", "close": "21:00"},
        "wednesday": {"open": "09:00", "close": "21:00"},
        "thursday": {"open": "09:00", "close": "21:00"},
        "friday": {"open": "09:00", "close": "21:00"},
        "saturday": {"open": "09:00", "close": "21:00"},
        "sunday": {"open": "10:00", "close": "20:00"}
    }'::jsonb,
    
    -- Settings (extensible)
    settings JSONB DEFAULT'{}'::jsonb,
    
    -- Metadata
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Deleted (soft delete)
    deleted_at TIMESTAMPTZ,
    
    UNIQUE(organization_id, code),
    CONSTRAINT valid_store_type CHECK (store_type IN ('retail', 'warehouse', 'franchise', 'online'))
);

-- Indexes for stores
CREATE INDEX idx_stores_org ON stores(organization_id);
CREATE INDEX idx_stores_active ON stores(organization_id, is_active) WHERE is_active = true;
CREATE INDEX idx_stores_type ON stores(store_type);
CREATE INDEX idx_stores_code ON stores(organization_id, code);

-- Comments
COMMENT ON TABLE stores IS 'Stores/locations within organizations';
COMMENT ON COLUMN stores.store_type IS 'retail, warehouse, franchise, or online';


-- ============================================================
-- 3. FUNCTIONS & TRIGGERS
-- ============================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for organizations
CREATE TRIGGER update_organizations_updated_at 
BEFORE UPDATE ON organizations
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Trigger for stores
CREATE TRIGGER update_stores_updated_at 
BEFORE UPDATE ON stores
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();


-- ============================================================
-- 4. SEED DATA (Demo Organization)
-- ============================================================

-- Insert demo organization (for data migration)
INSERT INTO organizations (
    id,
    name,
    legal_name,
    gstin,
    pan,
    contact_email,
    subscription_plan,
    subscription_status,
    address,
    settings
) VALUES (
    '00000000-0000-0000-0000-000000000001',
    'Demo Retail Store',
    'Demo Retail Store Pvt Ltd',
    '29ABCDE1234F1Z5',
    'ABCDE1234F',
    'demo@rdios.in',
    'enterprise',
    'active',
    '{"line1": "123 MG Road", "city": "Bangalore", "state": "Karnataka", "state_code": "29", "pincode": "560001", "country": "India"}'::jsonb,
    '{"currency": "INR", "timezone": "Asia/Kolkata"}'::jsonb
) ON CONFLICT (id) DO NOTHING;

-- Insert demo store
INSERT INTO stores (
    id,
    organization_id,
    name,
    code,
    store_type,
    address,
    manager_name,
    contact_phone
) VALUES (
    '00000000-0000-0000-0000-000000000002',
    '00000000-0000-0000-0000-000000000001',
    'Main Store',
    'MAIN',
    'retail',
    '{"line1": "123 MG Road", "city": "Bangalore", "state": "Karnataka", "state_code": "29", "pincode": "560001", "country": "India"}'::jsonb,
    'Store Manager',
    '+91-9876543210'
) ON CONFLICT (id) DO NOTHING;


-- ============================================================
-- 5. VERIFICATION QUERIES
-- ============================================================

-- Verify organizations table
SELECT 
    id,
    name,
    gstin,
    subscription_plan,
    created_at
FROM organizations
ORDER BY created_at DESC;

-- Verify stores table
SELECT 
    s.id,
    s.name,
    s.code,
    s.store_type,
    o.name as organization_name
FROM stores s
JOIN organizations o ON s.organization_id = o.id
ORDER BY s.created_at DESC;

-- Check constraints
SELECT 
    conname AS constraint_name,
    contype AS constraint_type,
    conrelid::regclass AS table_name
FROM pg_constraint
WHERE conrelid IN ('organizations'::regclass, 'stores'::regclass)
ORDER BY table_name, constraint_name;
