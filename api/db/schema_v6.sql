-- R-DIOS v6.0 Comprehensive Database Schema
-- Master's Thesis - Retail Decision Intelligence Operating System
-- PostgreSQL 15+ with partitioning, materialized views, and strategic indexes

-- ============================================================
-- PART 1: CORE TABLES (Users, Authentication, Base Data)
-- ============================================================

-- 1. Users (Authentication)
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('admin', 'manager', 'cashier', 'user')),
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role) WHERE is_active = TRUE;

-- 2. Customers (B2C)
CREATE TABLE IF NOT EXISTS customers (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    name VARCHAR(200) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20),
    whatsapp VARCHAR(20),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    pincode VARCHAR(10),
    
    -- Credit/Khata Management
    credit_limit DECIMAL(15,2) DEFAULT 0,
    outstanding_amount DECIMAL(15,2) DEFAULT 0,
    credit_score INTEGER DEFAULT 100 CHECK (credit_score BETWEEN 0 AND 100),
    
    -- RFM Analytics (pre-calculated for performance)
    last_purchase_date DATE,
    purchase_count INTEGER DEFAULT 0,
    total_spent DECIMAL(15,2) DEFAULT 0,
    rfm_segment VARCHAR(50),
    
    -- Dates & Metadata
    date_of_birth DATE,
    anniversary_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_customers_phone ON customers(phone) WHERE phone IS NOT NULL;
CREATE INDEX idx_customers_rfm ON customers(last_purchase_date, purchase_count, total_spent);
CREATE INDEX idx_customers_segment ON customers(rfm_segment) WHERE rfm_segment IS NOT NULL;
CREATE INDEX idx_customers_credit ON customers(outstanding_amount) WHERE outstanding_amount > 0;

-- 3. Suppliers (B2B)
CREATE TABLE IF NOT EXISTS suppliers (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    contact_person VARCHAR(200),
    email VARCHAR(255),
    phone VARCHAR(20),
    gst_number VARCHAR(20),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    pincode VARCHAR(10),
    
    -- Performance Metrics
    avg_lead_time_days INTEGER DEFAULT 7,
    quality_rating DECIMAL(3,2) DEFAULT 5.0 CHECK (quality_rating BETWEEN 0 AND 5),
    on_time_delivery_rate DECIMAL(5,2) DEFAULT 100,
    
    -- Financial
    payment_terms_days INTEGER DEFAULT 30,
    outstanding_payable DECIMAL(15,2) DEFAULT 0,
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_suppliers_gst ON suppliers(gst_number) WHERE gst_number IS NOT NULL;

-- 4. Product Categories
CREATE TABLE IF NOT EXISTS product_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    parent_id INTEGER REFERENCES product_categories(id),
    hsn_code VARCHAR(20),
    default_gst_rate DECIMAL(5,2) DEFAULT 18.00,
    avg_margin DECIMAL(5,2) DEFAULT 25.00,
    dead_stock_days INTEGER DEFAULT 180,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Products
CREATE TABLE IF NOT EXISTS products (
    id BIGSERIAL PRIMARY KEY,
    category_id INTEGER REFERENCES product_categories(id),
    supplier_id BIGINT REFERENCES suppliers(id),
    
    -- Identification
    sku VARCHAR(50) UNIQUE,
    barcode VARCHAR(50),
    name VARCHAR(300) NOT NULL,
    description TEXT,
    
    -- Pricing
    cost_price DECIMAL(15,2) NOT NULL,
    selling_price DECIMAL(15,2) NOT NULL,
    mrp DECIMAL(15,2),
    
    -- Tax
    hsn_code VARCHAR(20) NOT NULL,
    gst_rate DECIMAL(5,2) NOT NULL DEFAULT 18.00,
    
    -- Inventory
    stock_level INTEGER DEFAULT 0,
    reorder_point INTEGER DEFAULT 10,
    min_order_quantity INTEGER DEFAULT 1,
    max_stock_level INTEGER DEFAULT 1000,
    
    -- Variants (JSONB for flexibility)
    has_variants BOOLEAN DEFAULT FALSE,
    variants JSONB, -- [{"size": "S", "color": "Red", "stock": 10, "sku": "ABC-S-R"}]
    
    -- Analytics
    last_sale_date DATE,
    last_restock_date DATE,
    total_units_sold INTEGER DEFAULT 0,
    abc_classification CHAR(1) CHECK (abc_classification IN ('A', 'B', 'C')),
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_products_sku ON products(sku) WHERE sku IS NOT NULL;
CREATE INDEX idx_products_barcode ON products(barcode) WHERE barcode IS NOT NULL;
CREATE INDEX idx_products_stock ON products(stock_level, reorder_point);
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_supplier ON products(supplier_id);
CREATE INDEX idx_products_abc ON products(abc_classification) WHERE abc_classification IS NOT NULL;
CREATE INDEX idx_products_dead_stock ON products(last_sale_date) WHERE last_sale_date IS NOT NULL;
CREATE INDEX idx_products_variants ON products USING GIN (variants) WHERE has_variants = TRUE;

-- ============================================================
-- PART 2: TRANSACTIONAL TABLES (Sales, Invoices, Payments)
-- ============================================================

-- 6. Sales (Partitioned by Quarter for thesis demonstration)
CREATE TABLE IF NOT EXISTS sales (
    id BIGSERIAL,
    customer_id BIGINT REFERENCES customers(id) ON DELETE SET NULL,
    user_id BIGINT REFERENCES users(id),
    
    -- Transaction Details
    invoice_number VARCHAR(50) UNIQUE,
    sale_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Amounts
    subtotal DECIMAL(15,2) NOT NULL,
    gst_amount DECIMAL(15,2) DEFAULT 0,
    discount_amount DECIMAL(15,2) DEFAULT 0,
    total_amount DECIMAL(15,2) NOT NULL,
    
    -- Payment
    payment_method VARCHAR(50) CHECK (payment_method IN ('cash', 'upi', 'card', 'credit', 'mixed')),
    payment_status VARCHAR(50) DEFAULT 'pending' CHECK (payment_status IN ('pending', 'partial', 'paid', 'overdue')),
    amount_paid DECIMAL(15,2) DEFAULT 0,
    amount_due DECIMAL(15,2) DEFAULT 0,
    
    -- Split Payment Support (JSONB)
    split_payment JSONB, -- {"cash": 500, "upi": 300, "card": 200}
    
    -- Context for Causal Analysis
    channel VARCHAR(50) DEFAULT 'offline' CHECK (channel IN ('offline', 'online', 'whatsapp')),
    promotion_code VARCHAR(50),
    weather_temperature DECIMAL(5,2),
    weather_condition VARCHAR(50),
    is_holiday BOOLEAN DEFAULT FALSE,
    holiday_name VARCHAR(100),
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    PRIMARY KEY (id, sale_date)
) PARTITION BY RANGE (sale_date);

-- Create quarterly partitions for 2022-2024 (thesis data range)
CREATE TABLE sales_2022_q1 PARTITION OF sales FOR VALUES FROM ('2022-01-01') TO ('2022-04-01');
CREATE TABLE sales_2022_q2 PARTITION OF sales FOR VALUES FROM ('2022-04-01') TO ('2022-07-01');
CREATE TABLE sales_2022_q3 PARTITION OF sales FOR VALUES FROM ('2022-07-01') TO ('2022-10-01');
CREATE TABLE sales_2022_q4 PARTITION OF sales FOR VALUES FROM ('2022-10-01') TO ('2023-01-01');
CREATE TABLE sales_2023_q1 PARTITION OF sales FOR VALUES FROM ('2023-01-01') TO ('2023-04-01');
CREATE TABLE sales_2023_q2 PARTITION OF sales FOR VALUES FROM ('2023-04-01') TO ('2023-07-01');
CREATE TABLE sales_2023_q3 PARTITION OF sales FOR VALUES FROM ('2023-07-01') TO ('2023-10-01');
CREATE TABLE sales_2023_q4 PARTITION OF sales FOR VALUES FROM ('2023-10-01') TO ('2024-01-01');
CREATE TABLE sales_2024_q1 PARTITION OF sales FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');
CREATE TABLE sales_2024_q2 PARTITION OF sales FOR VALUES FROM ('2024-04-01') TO ('2024-07-01');
CREATE TABLE sales_2024_q3 PARTITION OF sales FOR VALUES FROM ('2024-07-01') TO ('2024-10-01');
CREATE TABLE sales_2024_q4 PARTITION OF sales FOR VALUES FROM ('2024-10-01') TO ('2025-01-01');
CREATE TABLE sales_future PARTITION OF sales FOR VALUES FROM ('2025-01-01') TO ('2030-01-01');

-- Indexes on partitioned table
CREATE INDEX idx_sales_date ON sales(sale_date);
CREATE INDEX idx_sales_customer ON sales(customer_id, sale_date);
CREATE INDEX idx_sales_payment_status ON sales(payment_status) WHERE payment_status != 'paid';
CREATE INDEX idx_sales_channel ON sales(channel, sale_date);
CREATE INDEX idx_sales_causal ON sales(sale_date, weather_temperature, is_holiday);

-- 7. Sale Items
CREATE TABLE IF NOT EXISTS sale_items (
    id BIGSERIAL PRIMARY KEY,
    sale_id BIGINT NOT NULL,
    sale_date TIMESTAMPTZ NOT NULL, -- Needed for partition reference
    product_id BIGINT REFERENCES products(id) ON DELETE RESTRICT,
    
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(15,2) NOT NULL,
    discount_percent DECIMAL(5,2) DEFAULT 0,
    discount_amount DECIMAL(15,2) DEFAULT 0,
    gst_rate DECIMAL(5,2) NOT NULL,
    gst_amount DECIMAL(15,2) NOT NULL,
    line_total DECIMAL(15,2) NOT NULL,
    
    -- Variant info (if applicable)
    variant_sku VARCHAR(50),
    variant_details JSONB,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    FOREIGN KEY (sale_id, sale_date) REFERENCES sales(id, sale_date) ON DELETE CASCADE
);

CREATE INDEX idx_sale_items_sale ON sale_items(sale_id);
CREATE INDEX idx_sale_items_product ON sale_items(product_id, sale_date);

-- 8. Payments
CREATE TABLE IF NOT EXISTS payments (
    id BIGSERIAL PRIMARY KEY,
    sale_id BIGINT,
    sale_date TIMESTAMPTZ,
    customer_id BIGINT REFERENCES customers(id),
    
    payment_date TIMESTAMPTZ DEFAULT NOW(),
    amount DECIMAL(15,2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    reference_number VARCHAR(100),
    
    -- Split payment tracking
    split_payment JSONB,
    
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    FOREIGN KEY (sale_id, sale_date) REFERENCES sales(id, sale_date) ON DELETE SET NULL
);

CREATE INDEX idx_payments_customer ON payments(customer_id, payment_date);
CREATE INDEX idx_payments_sale ON payments(sale_id);

-- 9. Credit Accounts (Khata)
CREATE TABLE IF NOT EXISTS credit_accounts (
    id BIGSERIAL PRIMARY KEY,
    customer_id BIGINT REFERENCES customers(id) ON DELETE RESTRICT,
    sale_id BIGINT,
    sale_date TIMESTAMPTZ,
    
    amount DECIMAL(15,2) NOT NULL,
    amount_paid DECIMAL(15,2) DEFAULT 0,
    due_date DATE NOT NULL,
    
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'partial', 'paid', 'overdue', 'written_off')),
    
    last_payment_date DATE,
    reminder_count INTEGER DEFAULT 0,
    last_reminder_date DATE,
    
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    closed_date TIMESTAMPTZ,
    
    FOREIGN KEY (sale_id, sale_date) REFERENCES sales(id, sale_date) ON DELETE SET NULL
);

CREATE INDEX idx_credit_customer ON credit_accounts(customer_id, status);
CREATE INDEX idx_credit_overdue ON credit_accounts(due_date, status) WHERE status IN ('pending', 'partial');

-- ============================================================
-- PART 3: INVENTORY & PROCUREMENT
-- ============================================================

-- 10. Purchase Orders
CREATE TABLE IF NOT EXISTS purchase_orders (
    id BIGSERIAL PRIMARY KEY,
    supplier_id BIGINT REFERENCES suppliers(id) ON DELETE RESTRICT,
    user_id BIGINT REFERENCES users(id),
    
    po_number VARCHAR(50) UNIQUE NOT NULL,
    order_date DATE NOT NULL DEFAULT CURRENT_DATE,
    expected_delivery_date DATE,
    actual_delivery_date DATE,
    
    subtotal DECIMAL(15,2) NOT NULL,
    gst_amount DECIMAL(15,2) DEFAULT 0,
    total_amount DECIMAL(15,2) NOT NULL,
    
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'sent', 'confirmed', 'shipped', 'delivered', 'cancelled')),
    
    -- Auto-reorder tracking
    is_auto_generated BOOLEAN DEFAULT FALSE,
    trigger_reason VARCHAR(100), -- 'low_stock', 'scheduled', 'manual'
    
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_po_supplier ON purchase_orders(supplier_id, order_date);
CREATE INDEX idx_po_status ON purchase_orders(status) WHERE status NOT IN ('delivered', 'cancelled');

-- 11. Purchase Order Items
CREATE TABLE IF NOT EXISTS purchase_order_items (
    id BIGSERIAL PRIMARY KEY,
    purchase_order_id BIGINT REFERENCES purchase_orders(id) ON DELETE CASCADE,
    product_id BIGINT REFERENCES products(id) ON DELETE RESTRICT,
    
    quantity_ordered INTEGER NOT NULL,
    quantity_received INTEGER DEFAULT 0,
    unit_cost DECIMAL(15,2) NOT NULL,
    gst_rate DECIMAL(5,2) NOT NULL,
    line_total DECIMAL(15,2) NOT NULL,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 12. Stock Movements (Audit Trail)
CREATE TABLE IF NOT EXISTS stock_movements (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT REFERENCES products(id) ON DELETE CASCADE,
    
    movement_type VARCHAR(50) NOT NULL CHECK (movement_type IN ('sale', 'purchase', 'return', 'adjustment', 'transfer', 'shrinkage')),
    quantity INTEGER NOT NULL, -- Positive for in, negative for out
    
    reference_type VARCHAR(50), -- 'sale', 'purchase_order', 'adjustment'
    reference_id BIGINT,
    
    stock_before INTEGER NOT NULL,
    stock_after INTEGER NOT NULL,
    
    user_id BIGINT REFERENCES users(id),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_stock_movements_product ON stock_movements(product_id, created_at);
CREATE INDEX idx_stock_movements_type ON stock_movements(movement_type, created_at);

-- ============================================================
-- PART 4: EXTERNAL FACTORS (For Causal Analysis)
-- ============================================================

-- 13. Weather Data
CREATE TABLE IF NOT EXISTS weather_data (
    id SERIAL PRIMARY KEY,
    city VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    
    temperature_high DECIMAL(5,2),
    temperature_low DECIMAL(5,2),
    temperature_avg DECIMAL(5,2),
    precipitation_mm DECIMAL(7,2) DEFAULT 0,
    humidity_percent INTEGER,
    condition VARCHAR(50), -- 'sunny', 'cloudy', 'rainy', 'stormy'
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(city, date)
);

CREATE INDEX idx_weather_date ON weather_data(date, city);

-- 14. Holiday Calendar
CREATE TABLE IF NOT EXISTS holidays (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    name VARCHAR(200) NOT NULL,
    type VARCHAR(50) CHECK (type IN ('national', 'regional', 'religious', 'observance')),
    region VARCHAR(100), -- NULL for national holidays
    is_major BOOLEAN DEFAULT FALSE, -- Major shopping events (Diwali, Eid, Christmas)
    expected_impact_percent DECIMAL(5,2), -- Expected sales impact (25% = +25%)
    
    UNIQUE(date, name)
);

CREATE INDEX idx_holidays_date ON holidays(date);
CREATE INDEX idx_holidays_major ON holidays(date) WHERE is_major = TRUE;

-- 15. Economic Indicators
CREATE TABLE IF NOT EXISTS economic_indicators (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    
    -- Indian economic indicators
    cpi_inflation DECIMAL(5,2), -- Consumer Price Index
    wpi_inflation DECIMAL(5,2), -- Wholesale Price Index
    fuel_price_petrol DECIMAL(7,2),
    fuel_price_diesel DECIMAL(7,2),
    gold_price DECIMAL(10,2),
    usd_inr_rate DECIMAL(7,2),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_economic_date ON economic_indicators(date);

-- ============================================================
-- PART 5: MATERIALIZED VIEWS (Performance Optimization)
-- ============================================================

-- Daily Revenue Summary (Refresh nightly)
CREATE MATERIALIZED VIEW mv_daily_revenue AS
SELECT 
    DATE(sale_date) as date,
    channel,
    COUNT(*) as order_count,
    SUM(total_amount) as revenue,
    SUM(gst_amount) as gst_collected,
    SUM(discount_amount) as discounts_given,
    AVG(total_amount) as avg_order_value,
    COUNT(DISTINCT customer_id) as unique_customers
FROM sales
WHERE payment_status != 'cancelled'
GROUP BY DATE(sale_date), channel
ORDER BY date;

CREATE UNIQUE INDEX idx_mv_daily_revenue ON mv_daily_revenue(date, channel);

-- Product Performance (Refresh weekly)
CREATE MATERIALIZED VIEW mv_product_performance AS
SELECT 
    p.id as product_id,
    p.name as product_name,
    p.category_id,
    pc.name as category_name,
    p.stock_level,
    p.cost_price,
    p.selling_price,
    p.selling_price - p.cost_price as margin,
    (p.selling_price - p.cost_price) / NULLIF(p.cost_price, 0) * 100 as margin_percent,
    COALESCE(s.total_units_sold, 0) as units_sold_30d,
    COALESCE(s.total_revenue, 0) as revenue_30d,
    p.last_sale_date,
    CURRENT_DATE - p.last_sale_date as days_since_last_sale
FROM products p
JOIN product_categories pc ON p.category_id = pc.id
LEFT JOIN (
    SELECT 
        si.product_id,
        SUM(si.quantity) as total_units_sold,
        SUM(si.line_total) as total_revenue
    FROM sale_items si
    WHERE si.sale_date >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY si.product_id
) s ON p.id = s.product_id
WHERE p.is_active = TRUE;

CREATE UNIQUE INDEX idx_mv_product_perf ON mv_product_performance(product_id);

-- Customer RFM Scores (Refresh weekly)
CREATE MATERIALIZED VIEW mv_customer_rfm AS
SELECT 
    c.id as customer_id,
    c.name,
    c.last_purchase_date,
    c.purchase_count,
    c.total_spent,
    
    -- Recency Score (1-5, 5 = most recent)
    CASE 
        WHEN c.last_purchase_date >= CURRENT_DATE - INTERVAL '7 days' THEN 5
        WHEN c.last_purchase_date >= CURRENT_DATE - INTERVAL '30 days' THEN 4
        WHEN c.last_purchase_date >= CURRENT_DATE - INTERVAL '90 days' THEN 3
        WHEN c.last_purchase_date >= CURRENT_DATE - INTERVAL '180 days' THEN 2
        ELSE 1
    END as recency_score,
    
    -- Frequency Score (1-5, 5 = most frequent)
    CASE 
        WHEN c.purchase_count >= 20 THEN 5
        WHEN c.purchase_count >= 10 THEN 4
        WHEN c.purchase_count >= 5 THEN 3
        WHEN c.purchase_count >= 2 THEN 2
        ELSE 1
    END as frequency_score,
    
    -- Monetary Score (1-5, 5 = highest spend)
    CASE 
        WHEN c.total_spent >= 50000 THEN 5
        WHEN c.total_spent >= 20000 THEN 4
        WHEN c.total_spent >= 10000 THEN 3
        WHEN c.total_spent >= 5000 THEN 2
        ELSE 1
    END as monetary_score,
    
    -- Combined RFM Segment
    CONCAT(
        CASE 
            WHEN c.last_purchase_date >= CURRENT_DATE - INTERVAL '7 days' THEN 5
            WHEN c.last_purchase_date >= CURRENT_DATE - INTERVAL '30 days' THEN 4
            WHEN c.last_purchase_date >= CURRENT_DATE - INTERVAL '90 days' THEN 3
            WHEN c.last_purchase_date >= CURRENT_DATE - INTERVAL '180 days' THEN 2
            ELSE 1
        END,
        CASE 
            WHEN c.purchase_count >= 20 THEN 5
            WHEN c.purchase_count >= 10 THEN 4
            WHEN c.purchase_count >= 5 THEN 3
            WHEN c.purchase_count >= 2 THEN 2
            ELSE 1
        END,
        CASE 
            WHEN c.total_spent >= 50000 THEN 5
            WHEN c.total_spent >= 20000 THEN 4
            WHEN c.total_spent >= 10000 THEN 3
            WHEN c.total_spent >= 5000 THEN 2
            ELSE 1
        END
    ) as rfm_score,
    
    CASE 
        -- Champions: High R, F, M
        WHEN c.last_purchase_date >= CURRENT_DATE - INTERVAL '30 days' 
             AND c.purchase_count >= 10 AND c.total_spent >= 20000 THEN 'champions'
        -- Loyal: High F, M
        WHEN c.purchase_count >= 10 AND c.total_spent >= 10000 THEN 'loyal'
        -- Potential Loyalist: Recent, moderate F
        WHEN c.last_purchase_date >= CURRENT_DATE - INTERVAL '30 days' 
             AND c.purchase_count >= 3 THEN 'potential_loyalist'
        -- At Risk: Not recent, but was valuable
        WHEN c.last_purchase_date < CURRENT_DATE - INTERVAL '90 days' 
             AND c.total_spent >= 10000 THEN 'at_risk'
        -- Hibernating: Long time, low engagement
        WHEN c.last_purchase_date < CURRENT_DATE - INTERVAL '180 days' THEN 'hibernating'
        -- New: Recent first purchase
        WHEN c.purchase_count <= 1 THEN 'new'
        ELSE 'regular'
    END as segment
    
FROM customers c
WHERE c.purchase_count > 0;

CREATE UNIQUE INDEX idx_mv_customer_rfm ON mv_customer_rfm(customer_id);
CREATE INDEX idx_mv_customer_segment ON mv_customer_rfm(segment);

-- ============================================================
-- PART 6: FUNCTIONS & TRIGGERS
-- ============================================================

-- Function to update product stock after sale
CREATE OR REPLACE FUNCTION update_stock_on_sale()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE products
    SET 
        stock_level = stock_level - NEW.quantity,
        total_units_sold = total_units_sold + NEW.quantity,
        last_sale_date = CURRENT_DATE,
        updated_at = NOW()
    WHERE id = NEW.product_id;
    
    -- Record stock movement
    INSERT INTO stock_movements (product_id, movement_type, quantity, reference_type, reference_id, stock_before, stock_after, user_id)
    SELECT 
        NEW.product_id,
        'sale',
        -NEW.quantity,
        'sale',
        NEW.sale_id,
        stock_level + NEW.quantity,
        stock_level,
        (SELECT user_id FROM sales WHERE id = NEW.sale_id AND sale_date = NEW.sale_date)
    FROM products WHERE id = NEW.product_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_stock_on_sale
    AFTER INSERT ON sale_items
    FOR EACH ROW
    EXECUTE FUNCTION update_stock_on_sale();

-- Function to update customer metrics after sale
CREATE OR REPLACE FUNCTION update_customer_on_sale()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.customer_id IS NOT NULL THEN
        UPDATE customers
        SET 
            last_purchase_date = NEW.sale_date::DATE,
            purchase_count = purchase_count + 1,
            total_spent = total_spent + NEW.total_amount,
            updated_at = NOW()
        WHERE id = NEW.customer_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_customer_on_sale
    AFTER INSERT ON sales
    FOR EACH ROW
    EXECUTE FUNCTION update_customer_on_sale();

-- Function to refresh materialized views (call via cron)
CREATE OR REPLACE FUNCTION refresh_all_materialized_views()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_revenue;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_product_performance;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_customer_rfm;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- PART 7: SEED DATA FOR THESIS DEMONSTRATION
-- ============================================================

-- Product Categories (Indian GST rates)
INSERT INTO product_categories (name, hsn_code, default_gst_rate, avg_margin, dead_stock_days) VALUES
('Grocery & Essentials', '1905', 0.00, 15.00, 30),
('Food & Beverages', '2201', 5.00, 20.00, 60),
('Health & Personal Care', '3304', 12.00, 35.00, 180),
('Electronics', '8471', 18.00, 10.00, 365),
('Fashion & Apparel', '6109', 12.00, 45.00, 180),
('Home & Kitchen', '9403', 18.00, 30.00, 365),
('Sports & Leisure', '9506', 18.00, 35.00, 365),
('Books & Stationery', '4901', 0.00, 25.00, 365),
('Baby Products', '9503', 12.00, 30.00, 180),
('Jewelry & Accessories', '7113', 3.00, 50.00, 365)
ON CONFLICT DO NOTHING;

-- Indian Holidays (Major events for causal analysis)
INSERT INTO holidays (date, name, type, is_major, expected_impact_percent) VALUES
('2023-10-24', 'Diwali', 'religious', TRUE, 35.00),
('2023-11-01', 'Diwali (Bhai Dooj)', 'religious', TRUE, 20.00),
('2023-03-08', 'Holi', 'religious', TRUE, 25.00),
('2023-04-22', 'Eid-ul-Fitr', 'religious', TRUE, 30.00),
('2023-08-15', 'Independence Day', 'national', FALSE, 10.00),
('2023-10-02', 'Gandhi Jayanti', 'national', FALSE, 5.00),
('2023-12-25', 'Christmas', 'religious', TRUE, 25.00),
('2024-10-31', 'Diwali', 'religious', TRUE, 35.00),
('2024-03-25', 'Holi', 'religious', TRUE, 25.00),
('2024-04-10', 'Eid-ul-Fitr', 'religious', TRUE, 30.00)
ON CONFLICT DO NOTHING;

-- ============================================================
-- PART 8: ANALYSIS QUERY EXAMPLES (For Thesis)
-- ============================================================

-- Commented out for reference, not executed during schema creation

/*
-- Example: Partition pruning demonstration
EXPLAIN ANALYZE
SELECT * FROM sales
WHERE sale_date >= '2023-10-01' AND sale_date < '2023-11-01';

-- Example: RFM segment distribution
SELECT segment, COUNT(*), AVG(total_spent)
FROM mv_customer_rfm
GROUP BY segment
ORDER BY COUNT(*) DESC;

-- Example: Causal analysis prep - sales by weather
SELECT 
    DATE(sale_date) as date,
    w.temperature_avg,
    w.condition,
    h.name as holiday,
    COUNT(*) as orders,
    SUM(total_amount) as revenue
FROM sales s
LEFT JOIN weather_data w ON DATE(s.sale_date) = w.date AND w.city = 'Mumbai'
LEFT JOIN holidays h ON DATE(s.sale_date) = h.date
GROUP BY DATE(sale_date), w.temperature_avg, w.condition, h.name
ORDER BY date;
*/

-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version VARCHAR(20) PRIMARY KEY,
    applied_at TIMESTAMPTZ DEFAULT NOW(),
    description TEXT
);

INSERT INTO schema_version (version, description) VALUES
('6.0.0', 'Initial R-DIOS v6.0 thesis schema with partitioning, materialized views, and causal analysis support');
