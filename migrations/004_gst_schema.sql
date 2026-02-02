-- ============================================================
-- R-DIOS GST Compliance Migration
-- Week 3: GST Schema (CGST/SGST/IGST)
-- ============================================================

-- This migration adds comprehensive GST fields to products and invoices
-- Compliant with Indian GST Act 2017

BEGIN;

-- ============================================================
-- 1. UPDATE PRODUCTS TABLE - GST FIELDS
-- ============================================================

-- Add GST-related columns to products
ALTER TABLE products 
ADD COLUMN IF NOT EXISTS hsn_code VARCHAR(20),
ADD COLUMN IF NOT EXISTS sac_code VARCHAR(20),
ADD COLUMN IF NOT EXISTS tax_type VARCHAR(20) DEFAULT 'GST',
ADD COLUMN IF NOT EXISTS cgst_rate DECIMAL(5,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS sgst_rate DECIMAL(5,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS igst_rate DECIMAL(5,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS cess_rate DECIMAL(5,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS is_taxable BOOLEAN DEFAULT true,
ADD COLUMN IF NOT EXISTS tax_exemption_reason VARCHAR(255);

-- Add pricing fields
ALTER TABLE products
ADD COLUMN IF NOT EXISTS mrp DECIMAL(12,2),
ADD COLUMN IF NOT EXISTS wholesale_price DECIMAL(12,2);

-- Add constraints
ALTER TABLE products
ADD CONSTRAINT valid_tax_type CHECK (tax_type IN ('GST', 'EXEMPT', 'NIL_RATED', 'NON_GST'));

ALTER TABLE products
ADD CONSTRAINT valid_gst_rates CHECK (
    (cgst_rate >= 0 AND cgst_rate <= 50) AND
    (sgst_rate >= 0 AND sgst_rate <= 50) AND
    (igst_rate >= 0 AND igst_rate <= 50) AND
    (cess_rate >= 0 AND cess_rate <= 50)
);

-- HSN/SAC validation (either HSN or SAC, not both)
ALTER TABLE products
ADD CONSTRAINT hsn_or_sac CHECK (
    (hsn_code IS NOT NULL AND sac_code IS NULL) OR
    (hsn_code IS NULL AND sac_code IS NOT NULL) OR
    (hsn_code IS NULL AND sac_code IS NULL)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_products_hsn ON products(hsn_code) WHERE hsn_code IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_products_sac ON products(sac_code) WHERE sac_code IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_products_gst_rate ON products(cgst_rate, sgst_rate, igst_rate);

COMMENT ON COLUMN products.hsn_code IS 'Harmonized System of Nomenclature (for goods)';
COMMENT ON COLUMN products.sac_code IS 'Services Accounting Code (for services)';
COMMENT ON COLUMN products.cgst_rate IS 'Central GST rate (%)';
COMMENT ON COLUMN products.sgst_rate IS 'State GST rate (%)';
COMMENT ON COLUMN products.igst_rate IS 'Integrated GST rate (%) - for inter-state';
COMMENT ON COLUMN products.cess_rate IS 'Cess rate (%) - additional tax';


-- ============================================================
-- 2. UPDATE INVOICES TABLE - GST DETAILS
-- ============================================================

-- Add GST calculation fields
ALTER TABLE invoices
ADD COLUMN IF NOT EXISTS is_interstate BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS place_of_supply VARCHAR(50),
ADD COLUMN IF NOT EXISTS reverse_charge BOOLEAN DEFAULT false,

-- Tax amounts
ADD COLUMN IF NOT EXISTS taxable_amount DECIMAL(14,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS cgst_amount DECIMAL(12,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS sgst_amount DECIMAL(12,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS igst_amount DECIMAL(12,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS cess_amount DECIMAL(12,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS total_tax DECIMAL(12,2) DEFAULT 0,

-- Discount
ADD COLUMN IF NOT EXISTS discount_amount DECIMAL(12,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS discount_type VARCHAR(20),

-- Round off
ADD COLUMN IF NOT EXISTS round_off DECIMAL(6,2) DEFAULT 0,

-- E-Invoice fields (for compliance)
ADD COLUMN IF NOT EXISTS irn VARCHAR(64),
ADD COLUMN IF NOT EXISTS ack_number VARCHAR(50),
ADD COLUMN IF NOT EXISTS ack_date TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS signed_invoice JSONB,
ADD COLUMN IF NOT EXISTS signed_qr_code TEXT,
ADD COLUMN IF NOT EXISTS e_invoice_status VARCHAR(20) DEFAULT 'not_generated',

-- E-Way Bill fields
ADD COLUMN IF NOT EXISTS eway_bill_number VARCHAR(20),
ADD COLUMN IF NOT EXISTS eway_bill_date TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS eway_bill_valid_until TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS transport_mode VARCHAR(20),
ADD COLUMN IF NOT EXISTS vehicle_number VARCHAR(20),
ADD COLUMN IF NOT EXISTS transporter_id VARCHAR(15),
ADD COLUMN IF NOT EXISTS distance_km INT;

-- Add constraints
ALTER TABLE invoices
ADD CONSTRAINT valid_e_invoice_status CHECK (
    e_invoice_status IN ('not_generated', 'pending', 'generated', 'cancelled', 'failed')
);

ALTER TABLE invoices
ADD CONSTRAINT valid_transport_mode CHECK (
    transport_mode IS NULL OR 
    transport_mode IN ('road', 'rail', 'air', 'ship')
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_invoices_irn ON invoices(irn) WHERE irn IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_invoices_eway ON invoices(eway_bill_number) WHERE eway_bill_number IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_invoices_place_supply ON invoices(place_of_supply);
CREATE INDEX IF NOT EXISTS idx_invoices_e_status ON invoices(e_invoice_status);

COMMENT ON COLUMN invoices.is_interstate IS 'True if invoice is inter-state (IGST applies)';
COMMENT ON COLUMN invoices.place_of_supply IS 'State code where supply is delivered';
COMMENT ON COLUMN invoices.reverse_charge IS 'True if reverse charge mechanism applies';
COMMENT ON COLUMN invoices.irn IS 'Invoice Reference Number from GST portal';
COMMENT ON COLUMN invoices.signed_qr_code IS 'Signed QR code for E-Invoice verification';


-- ============================================================
-- 3. UPDATE INVOICE_ITEMS TABLE - LINE ITEM GST
-- ============================================================

-- Add GST breakdown per line item
ALTER TABLE invoice_items
ADD COLUMN IF NOT EXISTS hsn_code VARCHAR(20),
ADD COLUMN IF NOT EXISTS unit VARCHAR(50) DEFAULT 'PCS',
ADD COLUMN IF NOT EXISTS unit_price DECIMAL(12,2) NOT NULL DEFAULT 0,
ADD COLUMN IF NOT EXISTS discount_percentage DECIMAL(5,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS discount_amount DECIMAL(12,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS taxable_amount DECIMAL(12,2) NOT NULL DEFAULT 0,

-- Tax rates per item
ADD COLUMN IF NOT EXISTS cgst_rate DECIMAL(5,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS cgst_amount DECIMAL(10,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS sgst_rate DECIMAL(5,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS sgst_amount DECIMAL(10,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS igst_rate DECIMAL(5,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS igst_amount DECIMAL(10,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS cess_rate DECIMAL(5,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS cess_amount DECIMAL(10,2) DEFAULT 0,

ADD COLUMN IF NOT EXISTS total_amount DECIMAL(12,2) NOT NULL DEFAULT 0;

-- Create index for HSN summary reports
CREATE INDEX IF NOT EXISTS idx_invoice_items_hsn ON invoice_items(hsn_code);

COMMENT ON COLUMN invoice_items.taxable_amount IS 'Amount before tax (after discount)';
COMMENT ON COLUMN invoice_items.total_amount IS 'Final amount including all taxes';


-- ============================================================
-- 4. GST RATE MASTER TABLE (Reference Data)
-- ============================================================

CREATE TABLE IF NOT EXISTS gst_rates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hsn_code VARCHAR(20) NOT NULL,
    description TEXT,
    gst_rate DECIMAL(5,2) NOT NULL,
    cess_rate DECIMAL(5,2) DEFAULT 0,
    effective_from DATE NOT NULL,
    effective_until DATE,
    category VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(hsn_code, effective_from)
);

CREATE INDEX idx_gst_rates_hsn ON gst_rates(hsn_code);
CREATE INDEX idx_gst_rates_active ON gst_rates(is_active, effective_from) WHERE is_active = true;

COMMENT ON TABLE gst_rates IS 'Master data for GST rates by HSN code';


-- ============================================================
-- 5. SEED COMMON GST RATES
-- ============================================================

INSERT INTO gst_rates (hsn_code, description, gst_rate, cess_rate, effective_from, category) VALUES
-- 0% GST
('9963', 'Educational Services', 0, 0, '2017-07-01', 'Services'),
('9992', 'Healthcare Services', 0, 0, '2017-07-01', 'Services'),

-- 5% GST
('1001', 'Rice', 5, 0, '2017-07-01', 'Food Grains'),
('0401', 'Milk and Cream', 5, 0, '2017-07-01', 'Dairy'),
('1701', 'Sugar', 5, 0, '2017-07-01', 'Food'),

-- 12% GST
('1701', 'Processed Food', 12, 0, '2017-07-01', 'Processed Food'),
('3004', 'Medicines', 12, 0, '2017-07-01', 'Pharma'),

-- 18% GST
('3003', 'Medical Equipment', 18, 0, '2017-07-01', 'Medical'),
('6402', 'Footwear', 18, 0, '2017-07-01', 'Apparel'),
('8517', 'Telecom Equipment', 18, 0, '2017-07-01', 'Electronics'),

-- 28% GST
('8703', 'Motor Vehicles', 28, 0, '2017-07-01', 'Automobiles'),
('2203', 'Beer', 28, 0, '2017-07-01', 'Beverages'),
('8471', 'Computers', 18, 0, '2017-07-01', 'IT'),

-- 28% + Cess
('2402', 'Cigarettes', 28, 5, '2017-07-01', 'Tobacco'),
('8703', 'Luxury Cars', 28, 15, '2017-07-01', 'Automobiles')

ON CONFLICT (hsn_code, effective_from) DO NOTHING;


-- ============================================================
-- 6. STATE CODES TABLE (For Place of Supply)
-- ============================================================

CREATE TABLE IF NOT EXISTS indian_states (
    state_code VARCHAR(2) PRIMARY KEY,
    state_name VARCHAR(100) NOT NULL UNIQUE,
    is_union_territory BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert all Indian states
INSERT INTO indian_states (state_code, state_name, is_union_territory) VALUES
('01', 'Jammu and Kashmir', true),
('02', 'Himachal Pradesh', false),
('03', 'Punjab', false),
('04', 'Chandigarh', true),
('05', 'Uttarakhand', false),
('06', 'Haryana', false),
('07', 'Delhi', true),
('08', 'Rajasthan', false),
('09', 'Uttar Pradesh', false),
('10', 'Bihar', false),
('11', 'Sikkim', false),
('12', 'Arunachal Pradesh', false),
('13', 'Nagaland', false),
('14', 'Manipur', false),
('15', 'Mizoram', false),
('16', 'Tripura', false),
('17', 'Meghalaya', false),
('18', 'Assam', false),
('19', 'West Bengal', false),
('20', 'Jharkhand', false),
('21', 'Odisha', false),
('22', 'Chhattisgarh', false),
('23', 'Madhya Pradesh', false),
('24', 'Gujarat', false),
('26', 'Dadra and Nagar Haveli and Daman and Diu', true),
('27', 'Maharashtra', false),
('28', 'Andhra Pradesh (Before Division)', false),
('29', 'Karnataka', false),
('30', 'Goa', false),
('31', 'Lakshadweep', true),
('32', 'Kerala', false),
('33', 'Tamil Nadu', false),
('34', 'Puducherry', true),
('35', 'Andaman and Nicobar Islands', true),
('36', 'Telangana', false),
('37', 'Andhra Pradesh (New)', false),
('38', 'Ladakh', true)
ON CONFLICT (state_code) DO NOTHING;


-- ============================================================
-- 7. VERIFICATION
-- ============================================================

-- Check products table
SELECT 
    COUNT(*) as total_products,
    COUNT(hsn_code) as products_with_hsn,
    COUNT(DISTINCT cgst_rate) as unique_gst_rates
FROM products;

-- Check invoices table
SELECT 
    COUNT(*) as total_invoices,
    COUNT(irn) as invoices_with_einvoice,
    COUNT(eway_bill_number) as invoices_with_eway
FROM invoices;

-- Check GST rates
SELECT 
    COUNT(*) as total_gst_rates,
    COUNT(DISTINCT gst_rate) as unique_rates
FROM gst_rates;

COMMIT;

-- Success message
SELECT 'GST Schema migration completed successfully!' AS status;
