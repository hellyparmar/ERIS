# Task 1.2: PostgreSQL Schema Creation
**Owner:** Backend Lead  
**Duration:** 4 hours  
**Deadline:** Feb 18, 12:00 PM IST  
**Priority:** 🔴 CRITICAL (Blocks data migration)  
**Phase:** Phase 0 - Critical Blockers  
**Depends On:** #1.1 PostgreSQL Infrastructure

---

## Description

Create PostgreSQL database schema with all 16 tables, indexes, and constraints. Migrate from SQLite schema format to PostgreSQL-optimized format.

## Acceptance Criteria

- [ ] All 16 tables created in PostgreSQL
- [ ] All columns match SQLite schema (with type conversion)
- [ ] Primary keys configured
- [ ] Foreign keys configured
- [ ] Composite indexes created for performance
- [ ] Schema validation: 100% match with SQLite
- [ ] Migration script created & documented
- [ ] Rollback script tested

## Schema Tables (16 total)

```sql
-- Core tables
CREATE TABLE users (...)
CREATE TABLE products (...)
CREATE TABLE inventory (...)
CREATE TABLE categories (...)
CREATE TABLE locations (...)

-- Sales & transactions
CREATE TABLE sales (...)
CREATE TABLE sales_items (...)
CREATE TABLE customers (...)

-- Invoicing (Phase 2B)
CREATE TABLE invoices (...)
CREATE TABLE invoice_items (...)
CREATE TABLE bills (...)
CREATE TABLE bill_items (...)

-- Analytics
CREATE TABLE alerts (...)
CREATE TABLE forecasts (...)
CREATE TABLE reports (...)

-- Configuration
CREATE TABLE settings (...)
```

## Implementation

### Step 1: Export SQLite Schema
```bash
sqlite3 petpooja_retail_db.sqlite3 .schema > sqlite_schema.sql
```

### Step 2: Convert to PostgreSQL
**Key conversions:**
- `INTEGER PRIMARY KEY` → `SERIAL PRIMARY KEY` or `BIGSERIAL PRIMARY KEY`
- `TEXT` → `VARCHAR(255)` or `TEXT`
- `AUTOINCREMENT` → `SERIAL` or `BIGSERIAL`
- `DATETIME` → `TIMESTAMP`
- `BOOLEAN` → `BOOLEAN`

### Step 3: Create Indexes for Performance
```sql
-- Composite indexes for common queries
CREATE INDEX idx_inventory_product_status 
ON inventory(product_id, status, stock_level);

CREATE INDEX idx_sales_customer_date 
ON sales(customer_id, created_at DESC);

CREATE INDEX idx_invoices_customer_date 
ON invoices(customer_id, invoice_date DESC);

-- Sorting indexes
CREATE INDEX idx_created_at 
ON inventory(created_at DESC);

CREATE INDEX idx_sales_created 
ON sales(created_at DESC);
```

### Step 4: Create Foreign Keys
```sql
ALTER TABLE sales 
ADD CONSTRAINT fk_sales_customer 
FOREIGN KEY (customer_id) 
REFERENCES customers(id);
```

### Step 5: Validate Schema
```python
# Python validation script
import sqlite3
import psycopg2

# Get SQLite table list
sqlite_conn = sqlite3.connect('petpooja_retail_db.sqlite3')
sqlite_cursor = sqlite_conn.cursor()
sqlite_cursor.execute("""
SELECT name FROM sqlite_master 
WHERE type='table' ORDER BY name
""")
sqlite_tables = [row[0] for row in sqlite_cursor.fetchall()]

# Get PostgreSQL table list
pg_conn = psycopg2.connect("dbname=enterprise_retail user=postgres")
pg_cursor = pg_conn.cursor()
pg_cursor.execute("""
SELECT table_name FROM information_schema.tables 
WHERE table_schema='public' ORDER BY table_name
""")
pg_tables = [row[0] for row in pg_cursor.fetchall()]

# Validate
assert set(sqlite_tables) == set(pg_tables), "Table mismatch!"
print(f"✅ Schema valid: {len(pg_tables)} tables")
```

## Related Issues
- #1.1 PostgreSQL Infrastructure
- #1.3 Data Migration
- #1.4 API Testing

## Files to Create
- [ ] `scripts/01_create_schema.sql` - Main schema creation
- [ ] `scripts/02_create_indexes.sql` - Performance indexes
- [ ] `scripts/03_validate_schema.py` - Validation script

## Definition of Done
✅ All 16 tables exist in PostgreSQL  
✅ Schema matches SQLite 100% (type-converted)  
✅ Indexes created for performance  
✅ Foreign keys configured  
✅ Validation script passes
