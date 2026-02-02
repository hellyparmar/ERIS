-- ============================================================
-- Odoo ERP Integration Schema
-- Stores connection details and sync status for Odoo
-- ============================================================

CREATE TABLE IF NOT EXISTS odoo_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Connection Credentials
    url VARCHAR(500) NOT NULL,
    db_name VARCHAR(255) NOT NULL,
    username VARCHAR(255) NOT NULL,
    api_key VARCHAR(500) NOT NULL, -- Encrypted at application level or stored securely
    
    -- Sync Settings
    sync_products BOOLEAN DEFAULT true,
    sync_customers BOOLEAN DEFAULT true,
    sync_invoices BOOLEAN DEFAULT false, -- Push to Odoo
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    last_sync_at TIMESTAMPTZ,
    last_sync_status VARCHAR(50), -- 'success', 'failed', 'partial'
    last_error_message TEXT,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(organization_id) -- One Odoo config per organization
);

-- Index for fast lookups
CREATE INDEX idx_odoo_configs_org ON odoo_configs(organization_id);

-- Trigger for updating timestamp
CREATE TRIGGER update_odoo_configs_updated_at 
BEFORE UPDATE ON odoo_configs
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE odoo_configs IS 'Configuration and credentials for Odoo ERP integration';
COMMENT ON COLUMN odoo_configs.api_key IS 'API Key or Password (should be stored encrypted)';
