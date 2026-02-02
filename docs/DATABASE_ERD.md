# R-DIOS v6.0 Database Schema - Entity Relationship Diagram

## Overview

This document describes the database architecture for the R-DIOS thesis project.

**Total Tables**: 15 core + 3 external factor tables  
**Partitioning**: Quarterly on `sales` table (2022-2024)  
**Materialized Views**: 3 (daily revenue, product performance, customer RFM)

---

## Entity Relationship Diagram (Mermaid)

```mermaid
erDiagram
    %% Core Entities
    users ||--o{ sales : "creates"
    users ||--o{ customers : "manages"
    
    customers ||--o{ sales : "makes"
    customers ||--o{ credit_accounts : "has"
    customers ||--o{ payments : "makes"
    
    suppliers ||--o{ products : "supplies"
    suppliers ||--o{ purchase_orders : "receives"
    
    product_categories ||--o{ products : "contains"
    product_categories ||--o| product_categories : "parent_of"
    
    products ||--o{ sale_items : "sold_in"
    products ||--o{ stock_movements : "tracks"
    products ||--o{ purchase_order_items : "ordered_in"
    
    sales ||--o{ sale_items : "contains"
    sales ||--o{ payments : "receives"
    sales ||--o| credit_accounts : "creates"
    
    purchase_orders ||--o{ purchase_order_items : "contains"
    
    %% External Factors (for Causal Analysis)
    weather_data ||--o{ sales : "affects"
    holidays ||--o{ sales : "affects"
    economic_indicators ||--o{ sales : "affects"

    %% Entity Definitions
    users {
        bigint id PK
        varchar username UK
        varchar email UK
        varchar password_hash
        varchar role
        boolean is_active
        timestamp last_login
    }
    
    customers {
        bigint id PK
        bigint user_id FK
        varchar name
        varchar phone
        decimal credit_limit
        decimal outstanding_amount
        date last_purchase_date
        int purchase_count
        decimal total_spent
        varchar rfm_segment
    }
    
    suppliers {
        bigint id PK
        varchar name
        varchar gst_number
        int avg_lead_time_days
        decimal quality_rating
        decimal outstanding_payable
    }
    
    product_categories {
        int id PK
        varchar name
        int parent_id FK
        varchar hsn_code
        decimal default_gst_rate
        int dead_stock_days
    }
    
    products {
        bigint id PK
        int category_id FK
        bigint supplier_id FK
        varchar sku UK
        varchar name
        decimal cost_price
        decimal selling_price
        varchar hsn_code
        decimal gst_rate
        int stock_level
        int reorder_point
        char abc_classification
    }
    
    sales {
        bigint id PK
        timestamp sale_date PK
        bigint customer_id FK
        varchar invoice_number UK
        decimal total_amount
        varchar payment_status
        varchar channel
        decimal weather_temperature
        boolean is_holiday
    }
    
    sale_items {
        bigint id PK
        bigint sale_id FK
        bigint product_id FK
        int quantity
        decimal unit_price
        decimal gst_rate
        decimal line_total
    }
    
    payments {
        bigint id PK
        bigint sale_id FK
        bigint customer_id FK
        decimal amount
        varchar payment_method
        timestamp payment_date
    }
    
    credit_accounts {
        bigint id PK
        bigint customer_id FK
        bigint sale_id FK
        decimal amount
        decimal amount_paid
        date due_date
        varchar status
    }
    
    purchase_orders {
        bigint id PK
        bigint supplier_id FK
        varchar po_number UK
        date order_date
        decimal total_amount
        varchar status
        boolean is_auto_generated
    }
    
    stock_movements {
        bigint id PK
        bigint product_id FK
        varchar movement_type
        int quantity
        int stock_before
        int stock_after
    }
    
    weather_data {
        int id PK
        varchar city
        date date
        decimal temperature_avg
        decimal precipitation_mm
        varchar condition
    }
    
    holidays {
        int id PK
        date date
        varchar name
        varchar type
        boolean is_major
        decimal expected_impact_percent
    }
    
    economic_indicators {
        int id PK
        date date UK
        decimal cpi_inflation
        decimal fuel_price_petrol
        decimal usd_inr_rate
    }
```

---

## Table Descriptions

### Core Business Tables

| Table | Purpose | Key Features |
|-------|---------|--------------|
| `users` | Authentication & authorization | Role-based access (admin/manager/cashier/user) |
| `customers` | B2C customer management | Credit/Khata, RFM analytics pre-calculated |
| `suppliers` | B2B vendor management | Performance tracking, lead time |
| `product_categories` | Hierarchical categorization | HSN codes, GST rates, dead stock threshold |
| `products` | Product catalog | Variants (JSONB), ABC classification, stock tracking |

### Transactional Tables

| Table | Purpose | Key Features |
|-------|---------|--------------|
| `sales` | Sales transactions | **Quarterly partitioned**, causal factors embedded |
| `sale_items` | Line items | Product-sale relationship |
| `payments` | Payment records | Split payment support (JSONB) |
| `credit_accounts` | Khata ledger | Aging, reminders, status tracking |

### Procurement Tables

| Table | Purpose | Key Features |
|-------|---------|--------------|
| `purchase_orders` | Supplier orders | Auto-generation tracking |
| `purchase_order_items` | PO line items | Quantity ordered vs received |
| `stock_movements` | Inventory audit trail | Full movement history |

### External Factor Tables (Causal Analysis)

| Table | Purpose | Key Features |
|-------|---------|--------------|
| `weather_data` | Weather by city/date | Temperature, precipitation, condition |
| `holidays` | Indian holiday calendar | Major event flag, expected impact % |
| `economic_indicators` | Macro-economic data | CPI, fuel prices, exchange rates |

---

## Partitioning Strategy

### Sales Table Partitioning

```
sales (Parent)
├── sales_2022_q1 (Jan-Mar 2022)
├── sales_2022_q2 (Apr-Jun 2022)
├── sales_2022_q3 (Jul-Sep 2022)
├── sales_2022_q4 (Oct-Dec 2022)
├── sales_2023_q1 (Jan-Mar 2023)
├── sales_2023_q2 (Apr-Jun 2023)
├── sales_2023_q3 (Jul-Sep 2023)
├── sales_2023_q4 (Oct-Dec 2023)
├── sales_2024_q1 (Jan-Mar 2024)
├── sales_2024_q2 (Apr-Jun 2024)
├── sales_2024_q3 (Jul-Sep 2024)
├── sales_2024_q4 (Oct-Dec 2024)
└── sales_future (2025+)
```

**Benefits for Thesis:**
- Demonstrates partition pruning in EXPLAIN ANALYZE
- Benchmarkable: partitioned vs non-partitioned queries
- Real-world applicable for enterprise-scale retail

---

## Materialized Views

### 1. `mv_daily_revenue`
Pre-aggregated daily revenue by channel.
- **Refresh**: Nightly (or on-demand)
- **Use Case**: Dashboard, time-series analysis

### 2. `mv_product_performance`
Product-level metrics (margin, units sold, days since sale).
- **Refresh**: Weekly
- **Use Case**: ABC analysis, dead stock identification

### 3. `mv_customer_rfm`
Pre-calculated RFM scores and segments.
- **Refresh**: Weekly
- **Use Case**: Customer segmentation, campaign triggers

---

## Indexes Strategy

| Category | Index | Purpose |
|----------|-------|---------|
| **Lookup** | `idx_products_sku` | Fast SKU search |
| **Lookup** | `idx_customers_phone` | Fast customer lookup |
| **Time-Series** | `idx_sales_date` | Partition pruning |
| **Analytics** | `idx_customers_rfm` | RFM queries |
| **Causal** | `idx_sales_causal` | Weather/holiday analysis |
| **JSONB** | `idx_products_variants (GIN)` | Variant queries |

---

## Causal Analysis Fields

The schema embeds fields specifically for causal inference:

```sql
-- In sales table
weather_temperature DECIMAL(5,2)  -- From weather_data join
weather_condition VARCHAR(50)     -- sunny/cloudy/rainy/stormy
is_holiday BOOLEAN                -- From holidays join
holiday_name VARCHAR(100)         -- Which holiday
promotion_code VARCHAR(50)        -- Which promotion
channel VARCHAR(50)               -- offline/online/whatsapp
```

These enable queries like:
```sql
-- Causal analysis: Sales by weather condition
SELECT 
    weather_condition,
    is_holiday,
    AVG(total_amount) as avg_sale,
    COUNT(*) as order_count
FROM sales
GROUP BY weather_condition, is_holiday;
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 6.0.0 | 2026-01-20 | Initial thesis schema with partitioning, materialized views, causal analysis support |
