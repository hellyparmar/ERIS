# R-DIOS Database Schema & Test Data Dictionary

## Overview

Complete documentation of all tables, fields, and test data structure for the R-DIOS system.

---

## Table: users

**Purpose**: Store staff accounts (cashiers, managers, admins)

| Column | Type | Constraint | Test Data |
|--------|------|-----------|-----------|
| id | TEXT | PRIMARY KEY | `user_a1b2c3d4` |
| username | TEXT | UNIQUE NOT NULL | `cashier_0`, `manager_0`, `admin_0` |
| email | TEXT | UNIQUE | `cashier0@petpooja.com` |
| password_hash | TEXT | - | SHA-256 hashed |
| pin | TEXT | - | `3000`, `2000`, `1000` |
| role | TEXT | CHECK(cashier\|manager\|admin) | `cashier`, `manager`, `admin` |
| name | TEXT | NOT NULL | Random first + last name |
| phone | TEXT | - | `9XXXXXXXXX` format |
| address | TEXT | - | City addresses |
| created_at | TEXT | DEFAULT CURRENT_TIMESTAMP | ISO 8601 datetime |
| updated_at | TEXT | - | ISO 8601 datetime |
| is_active | BOOLEAN | DEFAULT 1 | 1 (true) |
| last_login | TEXT | - | Recent ISO datetime |

**Sample Record**:
```json
{
  "id": "user_a1b2c3d4",
  "username": "cashier_0",
  "email": "cashier0@petpooja.com",
  "password_hash": "8d969eef6ecad3c29a3a873fba8a4b1d3...",
  "pin": "3000",
  "role": "cashier",
  "name": "Raj Kumar",
  "phone": "9876543210",
  "created_at": "2024-01-15T10:30:00",
  "is_active": true
}
```

**Test Data Summary**:
- Total: 20 users
- Admins: 4 (pins 1000-1003)
- Managers: 6 (pins 2000-2005)
- Cashiers: 10 (pins 3000-3009)

---

## Table: products

**Purpose**: Store product catalog with pricing and stock levels

| Column | Type | Constraint | Test Data |
|--------|------|-----------|-----------|
| id | TEXT | PRIMARY KEY | `prod_x1y2z3a4` |
| sku | TEXT | UNIQUE NOT NULL | `FRP0000` (category + index) |
| name | TEXT | NOT NULL | Product names from categories |
| description | TEXT | - | Product details |
| category | TEXT | NOT NULL | 10 product categories |
| price | REAL | NOT NULL | ₹20-₹400 range |
| cost | REAL | - | 50% of price typically |
| tax_rate | REAL | DEFAULT 0.05 | 5% or 0% for fresh produce |
| stock | INTEGER | DEFAULT 0 | 50-500 units |
| min_stock | INTEGER | DEFAULT 10 | 10-30 units |
| reorder_level | INTEGER | DEFAULT 20 | 30-50 units |
| supplier | TEXT | - | `Local` or `Import` |
| barcode | TEXT | - | Product barcode |
| image_url | TEXT | - | Product image URL |
| last_restocked | TEXT | - | ISO datetime |
| created_at | TEXT | DEFAULT CURRENT_TIMESTAMP | 30-180 days ago |
| updated_at | TEXT | - | Recent datetime |
| is_active | BOOLEAN | DEFAULT 1 | 1 (true) |

**Sample Record**:
```json
{
  "id": "prod_x1y2z3a4",
  "sku": "FRP0001",
  "name": "Tomato",
  "category": "Fresh Produce",
  "price": 30.0,
  "cost": 15.0,
  "tax_rate": 0.0,
  "stock": 240,
  "min_stock": 10,
  "reorder_level": 20,
  "supplier": "Local",
  "created_at": "2023-11-30T09:00:00"
}
```

**Test Data Summary**:
- Total: 200+ products
- Categories: 10 (Produce, Dairy, Meat, Beverages, etc.)
- Price Range: ₹20-₹400
- Stock Range: 50-500 units
- Tax Rate: 0% (Fresh), 5% (Others)

---

## Table: customers

**Purpose**: Store customer information and purchase history

| Column | Type | Constraint | Test Data |
|--------|------|-----------|-----------|
| id | TEXT | PRIMARY KEY | `cust_p1q2r3s4` |
| name | TEXT | NOT NULL | Random first + last name |
| phone | TEXT | UNIQUE | `9XXXXXXXXX` format |
| email | TEXT | - | `customer{i}@email.com` |
| address | TEXT | - | Street address |
| city | TEXT | - | Major Indian cities |
| state | TEXT | - | State name |
| country | TEXT | - | "India" |
| postal_code | TEXT | - | Postal code |
| customer_type | TEXT | - | Regular, Premium, Occasional |
| date_of_birth | TEXT | - | ISO date |
| registration_date | TEXT | DEFAULT CURRENT_TIMESTAMP | 1-365 days ago |
| last_purchase | TEXT | - | 0-30 days ago |
| total_purchases | INTEGER | DEFAULT 0 | 1-100 |
| total_spent | REAL | DEFAULT 0.0 | ₹500-₹500,000 |
| average_order_value | REAL | DEFAULT 0.0 | Calculated |
| rfm_segment | TEXT | - | RFM segment name |
| loyalty_points | INTEGER | DEFAULT 0 | Accumulated points |
| is_active | BOOLEAN | DEFAULT 1 | 1 (true) |

**Sample Record**:
```json
{
  "id": "cust_p1q2r3s4",
  "name": "Priya Sharma",
  "phone": "9876543210",
  "email": "customer123@email.com",
  "city": "Mumbai",
  "customer_type": "Premium",
  "registration_date": "2023-06-15T10:30:00",
  "last_purchase": "2024-01-10T14:20:00",
  "total_purchases": 45,
  "total_spent": 45000.50,
  "average_order_value": 1000.01,
  "rfm_segment": "Loyal Customers"
}
```

**Test Data Summary**:
- Total: 500 customers
- Regular: 300 (60%)
- Premium: 100 (20%)
- Occasional: 100 (20%)
- Purchase Range: 1-100
- Spent Range: ₹500-₹500,000
- Cities: 10 major Indian cities

---

## Table: transactions

**Purpose**: Store POS transaction records

| Column | Type | Constraint | Test Data |
|--------|------|-----------|-----------|
| id | TEXT | PRIMARY KEY | `txn_t1u2v3w4` |
| timestamp | TEXT | DEFAULT CURRENT_TIMESTAMP | Last 90 days |
| cashier_id | TEXT | NOT NULL FOREIGN KEY | Reference to users |
| cashier_name | TEXT | - | Cashier name |
| customer_id | TEXT | FOREIGN KEY | Optional, 70% populated |
| customer_name | TEXT | - | Customer name |
| item_count | INTEGER | DEFAULT 0 | 1-10 items |
| subtotal | REAL | DEFAULT 0.0 | Sum of items |
| discount | REAL | DEFAULT 0.0 | 0-15% of subtotal |
| tax | REAL | DEFAULT 0.0 | 5% on taxable items |
| total | REAL | DEFAULT 0.0 | subtotal - discount + tax |
| payment_method | TEXT | CHECK(...) | Cash, Card, UPI, Digital Wallet |
| reference_number | TEXT | - | `REFYYYYMMDDxxxxxx` |
| receipt_url | TEXT | - | Receipt file path |
| status | TEXT | DEFAULT 'completed' | completed, pending, cancelled |
| notes | TEXT | - | Transaction notes |
| is_synced | BOOLEAN | DEFAULT 0 | Sync status |

**Sample Record**:
```json
{
  "id": "txn_t1u2v3w4",
  "timestamp": "2024-01-10T14:30:45",
  "cashier_id": "user_a1b2c3d4",
  "cashier_name": "Raj Kumar",
  "customer_id": "cust_p1q2r3s4",
  "customer_name": "Priya Sharma",
  "item_count": 5,
  "subtotal": 2500.0,
  "discount": 250.0,
  "tax": 112.50,
  "total": 2362.50,
  "payment_method": "Card",
  "reference_number": "REF20240110000123",
  "status": "completed"
}
```

**Test Data Summary**:
- Total: 2,000 transactions
- Span: Last 90 days
- Items per txn: 1-10
- Payment Methods: Cash (35%), Card (40%), UPI (20%), Digital (5%)
- Discounts: 15% of transactions
- Status: 95% completed, 3% pending, 2% cancelled

---

## Table: transaction_items

**Purpose**: Store individual items within each transaction

| Column | Type | Constraint | Test Data |
|--------|------|-----------|-----------|
| id | TEXT | PRIMARY KEY | `item_{transaction_id}_{product_id}` |
| transaction_id | TEXT | NOT NULL FOREIGN KEY | Reference to transactions |
| product_id | TEXT | NOT NULL FOREIGN KEY | Reference to products |
| product_name | TEXT | - | Product name |
| quantity | INTEGER | NOT NULL | 1-5 units |
| unit_price | REAL | NOT NULL | Product selling price |
| line_total | REAL | NOT NULL | quantity * unit_price |
| discount | REAL | DEFAULT 0.0 | Per-item discount |
| tax | REAL | DEFAULT 0.0 | Per-item tax |

**Sample Record**:
```json
{
  "id": "item_txn_t1u2v3w4_prod_x1y2z3a4",
  "transaction_id": "txn_t1u2v3w4",
  "product_id": "prod_x1y2z3a4",
  "product_name": "Tomato",
  "quantity": 3,
  "unit_price": 30.0,
  "line_total": 90.0
}
```

**Test Data Summary**:
- Total: 8,000+ items (avg 4 per transaction)
- Quantity per item: 1-5 units
- Coverage: All 200+ products represented

---

## Table: stock_history

**Purpose**: Track inventory changes over time

| Column | Type | Constraint | Test Data |
|--------|------|-----------|-----------|
| id | TEXT | PRIMARY KEY | `stk_hist_{uuid}` |
| product_id | TEXT | NOT NULL FOREIGN KEY | Reference to products |
| old_quantity | INTEGER | - | Previous stock level |
| new_quantity | INTEGER | - | Current stock level |
| change_quantity | INTEGER | - | Difference |
| operation | TEXT | CHECK(...) | add, remove, adjust, sale |
| reason | TEXT | - | Reason for change |
| reference | TEXT | - | Related transaction/order |
| timestamp | TEXT | DEFAULT CURRENT_TIMESTAMP | When change occurred |
| user_id | TEXT | FOREIGN KEY | Who made the change |

**Sample Record**:
```json
{
  "id": "stk_hist_abc123",
  "product_id": "prod_x1y2z3a4",
  "old_quantity": 245,
  "new_quantity": 240,
  "change_quantity": -5,
  "operation": "sale",
  "reason": "Sold via transaction",
  "reference": "txn_t1u2v3w4",
  "timestamp": "2024-01-10T14:30:45",
  "user_id": "user_a1b2c3d4"
}
```

---

## Table: inventory_alerts

**Purpose**: Store inventory-related alerts

| Column | Type | Constraint | Test Data |
|--------|------|-----------|-----------|
| id | TEXT | PRIMARY KEY | `alert_{uuid}` |
| product_id | TEXT | NOT NULL FOREIGN KEY | Reference to products |
| alert_type | TEXT | CHECK(...) | low_stock, expiring, excess_stock |
| severity | TEXT | DEFAULT 'medium' | low, medium, high |
| message | TEXT | - | Alert description |
| is_resolved | BOOLEAN | DEFAULT 0 | 0 (unresolved) |
| created_at | TEXT | DEFAULT CURRENT_TIMESTAMP | When alert created |
| resolved_at | TEXT | - | When resolved |

**Sample Record**:
```json
{
  "id": "alert_xyz789",
  "product_id": "prod_x1y2z3a4",
  "alert_type": "low_stock",
  "severity": "high",
  "message": "Tomato stock is 15 units, below minimum 20",
  "is_resolved": 0,
  "created_at": "2024-01-10T15:00:00"
}
```

**Test Data Summary**:
- Total: 20-30 active alerts
- Types: Low stock (80%), Expiring (15%), Excess (5%)
- Severity: Low, Medium, High distribution

---

## Table: analytics_daily

**Purpose**: Store aggregated daily sales metrics

| Column | Type | Constraint | Test Data |
|--------|------|-----------|-----------|
| id | TEXT | PRIMARY KEY | `daily_{date}` |
| date | TEXT | UNIQUE NOT NULL | ISO date (YYYY-MM-DD) |
| transaction_count | INTEGER | DEFAULT 0 | Daily transactions |
| total_revenue | REAL | DEFAULT 0.0 | Daily sales |
| total_discount | REAL | DEFAULT 0.0 | Total discounts |
| total_tax | REAL | DEFAULT 0.0 | Total tax collected |
| average_transaction | REAL | DEFAULT 0.0 | Avg transaction value |
| items_sold | INTEGER | DEFAULT 0 | Total items sold |
| unique_customers | INTEGER | DEFAULT 0 | Unique customers |
| peak_hour | INTEGER | - | Hour with most sales |
| created_at | TEXT | DEFAULT CURRENT_TIMESTAMP | When calculated |

**Sample Record**:
```json
{
  "id": "daily_2024-01-10",
  "date": "2024-01-10",
  "transaction_count": 25,
  "total_revenue": 31250.75,
  "total_discount": 2100.50,
  "total_tax": 1406.26,
  "average_transaction": 1250.03,
  "items_sold": 120,
  "unique_customers": 18,
  "peak_hour": 14
}
```

---

## Table: category_performance

**Purpose**: Store aggregated category performance metrics

| Column | Type | Constraint | Test Data |
|--------|------|-----------|-----------|
| id | TEXT | PRIMARY KEY | `cat_{category}` |
| category | TEXT | UNIQUE NOT NULL | Product category |
| transaction_count | INTEGER | DEFAULT 0 | Transactions involving category |
| total_revenue | REAL | DEFAULT 0.0 | Revenue from category |
| items_sold | INTEGER | DEFAULT 0 | Items sold from category |
| average_price | REAL | DEFAULT 0.0 | Average price in category |
| last_updated | TEXT | DEFAULT CURRENT_TIMESTAMP | Last update time |

**Sample Record**:
```json
{
  "id": "cat_Fresh_Produce",
  "category": "Fresh Produce",
  "transaction_count": 350,
  "total_revenue": 125000.0,
  "items_sold": 2500,
  "average_price": 50.0
}
```

---

## Table: rfm_analysis

**Purpose**: Store RFM (Recency, Frequency, Monetary) customer segments

| Column | Type | Constraint | Test Data |
|--------|------|-----------|-----------|
| customer_id | TEXT | PRIMARY KEY FOREIGN KEY | Reference to customers |
| recency | INTEGER | - | Days since last purchase |
| frequency | INTEGER | - | Number of purchases |
| monetary | REAL | - | Total amount spent |
| r_score | INTEGER | - | Recency score (1-5) |
| f_score | INTEGER | - | Frequency score (1-5) |
| m_score | INTEGER | - | Monetary score (1-5) |
| rfm_score | INTEGER | - | Total score (3-15) |
| segment | TEXT | - | VIP, Loyal, Potential, At Risk, Lost |
| last_updated | TEXT | DEFAULT CURRENT_TIMESTAMP | When analyzed |

**Sample Record**:
```json
{
  "customer_id": "cust_p1q2r3s4",
  "recency": 5,
  "frequency": 45,
  "monetary": 45000.50,
  "r_score": 5,
  "f_score": 4,
  "m_score": 4,
  "rfm_score": 13,
  "segment": "Loyal Customers"
}
```

**RFM Segments**:
- **VIP Customers** (Score 12-15): Most valuable, frequent buyers
- **Loyal Customers** (Score 9-11): Regular, consistent buyers
- **Potential Customers** (Score 6-8): Some promise, need engagement
- **At Risk** (Score 3-5): Low engagement, may churn
- **Lost Customers** (Score 0-2): Inactive, unlikely to return

---

## Table: anomalies

**Purpose**: Store detected anomalies for investigation

| Column | Type | Constraint | Test Data |
|--------|------|-----------|-----------|
| id | TEXT | PRIMARY KEY | `anom_{uuid}` |
| type | TEXT | NOT NULL | Anomaly type |
| description | TEXT | - | Detailed description |
| timestamp | TEXT | DEFAULT CURRENT_TIMESTAMP | When detected |
| transaction_id | TEXT | FOREIGN KEY | Related transaction |
| severity | TEXT | DEFAULT 'low' | low, medium, high |
| value | REAL | - | Anomalous value |
| is_resolved | BOOLEAN | DEFAULT 0 | Resolution status |
| resolved_at | TEXT | - | When resolved |
| notes | TEXT | - | Investigation notes |

**Sample Record**:
```json
{
  "id": "anom_0001",
  "type": "high_value_transaction",
  "description": "Transaction value ₹25000 is 3.2x average",
  "timestamp": "2024-01-05T16:45:00",
  "transaction_id": "txn_t1u2v3w4",
  "severity": "medium",
  "value": 25000.0,
  "is_resolved": 0
}
```

**Anomaly Types**:
- High-value transactions (3x+ average)
- Excessive discounts (20%+ off)
- Unusual patterns
- Stock anomalies
- Price inconsistencies

---

## Table: forecasts

**Purpose**: Store revenue and demand forecasts

| Column | Type | Constraint | Test Data |
|--------|------|-----------|-----------|
| id | TEXT | PRIMARY KEY | `fcst_{uuid}` |
| period | TEXT | - | Forecast period |
| forecast_type | TEXT | - | revenue, demand, stock |
| predicted_value | REAL | - | Forecasted value |
| confidence_score | REAL | - | Confidence 0-1 |
| start_date | TEXT | - | Period start |
| end_date | TEXT | - | Period end |
| created_at | TEXT | DEFAULT CURRENT_TIMESTAMP | When created |
| accuracy | REAL | - | Actual accuracy if realized |

**Sample Record**:
```json
{
  "id": "fcst_xyz001",
  "period": "2024-02-01 to 2024-02-07",
  "forecast_type": "revenue",
  "predicted_value": 225000.0,
  "confidence_score": 0.85,
  "start_date": "2024-02-01",
  "end_date": "2024-02-07",
  "created_at": "2024-01-15T10:00:00"
}
```

---

## Relationships Diagram

```
users (1) ─── (N) transactions
            └─ (N) stock_history

products (1) ─── (N) transaction_items
            ├─ (N) stock_history
            └─ (N) inventory_alerts

customers (1) ─── (N) transactions
           └─ (1) rfm_analysis

transactions (1) ─── (N) transaction_items
             └─ (N) anomalies
```

---

## Summary Statistics

| Entity | Count | Notes |
|--------|-------|-------|
| Users | 20 | 4 admin, 6 manager, 10 cashier |
| Products | 200+ | 10 categories, ₹20-₹400 range |
| Customers | 500 | 60% Regular, 20% Premium, 20% Occasional |
| Transactions | 2,000 | 90-day span, avg ₹1,250 |
| Transaction Items | 8,000+ | Avg 4 items per transaction |
| Total Revenue | ₹10-15L | Realistic retail volume |
| RFM Segments | 5 | VIP to Lost distribution |
| Inventory Alerts | 20-30 | Low stock focus |
| Anomalies | 50-100 | Various types and severities |

---

## Data Integrity Constraints

### Foreign Keys
- transactions.cashier_id → users.id
- transactions.customer_id → customers.id
- transaction_items.transaction_id → transactions.id
- transaction_items.product_id → products.id
- stock_history.product_id → products.id
- stock_history.user_id → users.id
- inventory_alerts.product_id → products.id
- rfm_analysis.customer_id → customers.id
- anomalies.transaction_id → transactions.id

### Unique Constraints
- users.username
- users.email
- products.sku
- customers.phone
- customers.email
- analytics_daily.date
- category_performance.category

### Check Constraints
- users.role IN ('cashier', 'manager', 'admin')
- products.tax_rate >= 0
- transactions.payment_method IN ('Cash', 'Card', 'UPI', 'Digital Wallet')
- transaction_items.quantity > 0
- stock_history.operation IN ('add', 'remove', 'adjust', 'sale')
- inventory_alerts.alert_type IN ('low_stock', 'expiring', 'excess_stock')

---

## Testing Guidelines

### Data Validation
- ✓ No NULL values in required fields
- ✓ All foreign key relationships valid
- ✓ Date ranges logical and consistent
- ✓ Amounts non-negative
- ✓ Quantities positive

### Realistic Distributions
- ✓ Payment methods distributed
- ✓ Customer types represented
- ✓ RFM segments populated
- ✓ Price range realistic
- ✓ Transaction amounts varied

### Feature Coverage
- ✓ POS transactions complete
- ✓ Inventory tracking enabled
- ✓ Customer analytics ready
- ✓ Anomalies for detection
- ✓ Analytics available

---

*Last Updated: 2024*
*Schema Version: 1.0*
*Test Data Version: 1.0*
