-- Migration: Create integration_tokens table for OAuth storage
-- Purpose: Store encrypted OAuth tokens for third-party integrations (Zoho, Odoo, etc.)

BEGIN;

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create integration_tokens table
CREATE TABLE IF NOT EXISTS integration_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL,
    integration_type VARCHAR(50) NOT NULL,
    
    -- Encrypted tokens
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_type VARCHAR(50) DEFAULT 'Bearer',
    
    -- Token metadata
    expires_at TIMESTAMP NOT NULL,
    scopes TEXT,
    additional_data TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_org_integration UNIQUE (organization_id, integration_type)
);

-- Create indexes
CREATE INDEX idx_integration_tokens_org_id ON integration_tokens(organization_id);
CREATE INDEX idx_integration_tokens_type ON integration_tokens(integration_type);
CREATE INDEX idx_integration_tokens_expires ON integration_tokens(expires_at);

-- Add foreign key to organizations table
ALTER TABLE integration_tokens
ADD CONSTRAINT fk_integration_tokens_organization
FOREIGN KEY (organization_id) REFERENCES organizations(id)
ON DELETE CASCADE;

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_integration_tokens_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_integration_tokens_updated_at
BEFORE UPDATE ON integration_tokens
FOR EACH ROW
EXECUTE FUNCTION update_integration_tokens_updated_at();

-- Verification
DO $$
BEGIN
    ASSERT (SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'integration_tokens') = 1,
        'integration_tokens table was not created';
    
    ASSERT (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'integration_tokens') >= 10,
        'integration_tokens table does not have all required columns';
    
    RAISE NOTICE 'Migration 005: integration_tokens table created successfully';
END $$;

COMMIT;
