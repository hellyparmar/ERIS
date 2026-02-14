# Task 1.3: SQLite to PostgreSQL Data Migration
**Owner:** Backend Lead  
**Duration:** 6 hours  
**Deadline:** Feb 18, 6:00 PM IST  
**Priority:** 🔴 CRITICAL (Blocks API testing)  
**Phase:** Phase 0 - Critical Blockers  
**Depends On:** #1.2 PostgreSQL Schema

---

## Description

Migrate 424,737 records from SQLite database to PostgreSQL. This is the core data migration that unblocks all API functionality testing.

## Acceptance Criteria

- [ ] All 424,737 records migrated without errors
- [ ] Data integrity: 100% (checksums match)
- [ ] No null values introduced
- [ ] Relationships preserved (foreign keys valid)
- [ ] Migration time: < 10 minutes
- [ ] Rollback tested and working
- [ ] Migration script documented
- [ ] Data validation report generated

## Key Statistics

**Source (SQLite):**
- Total records: 424,737
- Database size: ~180 MB
- Tables: 16
- Relationships: 8 foreign keys

**Target (PostgreSQL):**
- Expected records: 424,737 (exact match)
- Expected size: ~200 MB (with indexes)
- Indexes: 12 composite indexes

## Migration Strategy

### Phase 1: Preparation (30 minutes)
```python
import sqlite3
import psycopg2
from datetime import datetime

# Step 1: Create backup
print("[1/5] Creating backup...")
os.system("cp petpooja_retail_db.sqlite3 backup_$(date +%Y%m%d_%H%M%S).sqlite3")

# Step 2: Get record counts
sqlite_conn = sqlite3.connect('petpooja_retail_db.sqlite3')
sqlite_cursor = sqlite_conn.cursor()
sqlite_cursor.execute("SELECT COUNT(*) FROM products")
product_count = sqlite_cursor.fetchone()[0]
print(f"✅ Products in SQLite: {product_count}")
```

### Phase 2: Data Export (5 minutes)
```python
# Export to CSV for validation
print("[2/5] Exporting to CSV...")

tables = ['products', 'inventory', 'sales', 'customers', 'invoices']
for table in tables:
    query = f"SELECT * FROM {table}"
    df = pd.read_sql_query(query, sqlite_conn)
    df.to_csv(f"export_{table}.csv", index=False)
    print(f"✅ Exported {table}: {len(df)} rows")
```

### Phase 3: Data Import (3 minutes)
```python
print("[3/5] Importing to PostgreSQL...")

pg_conn = psycopg2.connect("dbname=enterprise_retail user=postgres")
pg_cursor = pg_conn.cursor()

# Disable constraints during import
pg_cursor.execute("ALTER TABLE sales DISABLE TRIGGER ALL")
pg_cursor.execute("ALTER TABLE invoices DISABLE TRIGGER ALL")

# Batch import
batch_size = 1000
for table_name, df in [(t, pd.read_csv(f"export_{t}.csv")) for t in tables]:
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size]
        # Insert batch
        print(f"✅ Imported {table_name}: {i+batch_size}/{len(df)}")

# Re-enable constraints
pg_cursor.execute("ALTER TABLE sales ENABLE TRIGGER ALL")
pg_conn.commit()
```

### Phase 4: Validation (10 minutes)
```python
print("[4/5] Validating data...")

validation_queries = {
    'products': "SELECT COUNT(*) FROM products",
    'inventory': "SELECT COUNT(*) FROM inventory",
    'sales': "SELECT COUNT(*) FROM sales",
    'customers': "SELECT COUNT(*) FROM customers"
}

for table, query in validation_queries.items():
    sqlite_cursor.execute(query)
    sqlite_count = sqlite_cursor.fetchone()[0]
    
    pg_cursor.execute(query)
    pg_count = pg_cursor.fetchone()[0]
    
    status = "✅" if sqlite_count == pg_count else "❌"
    print(f"{status} {table}: SQLite={sqlite_count}, PostgreSQL={pg_count}")
```

### Phase 5: Rollback Plan (If needed)
```sql
-- Restore from backup if errors occur
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
-- Re-run schema creation script
psql enterprise_retail < schema.sql
```

## Expected Timeline

| Step | Duration | Status |
|------|----------|--------|
| 1. Backup & Validation | 5 min | ⏳ |
| 2. Schema Creation | 10 min | ⏳ |
| 3. Data Export | 5 min | ⏳ |
| 4. Data Import | 3 min | ⏳ |
| 5. Validation & Indexes | 10 min | ⏳ |
| **TOTAL** | **~33 min** | ⏳ |

## Related Issues
- #1.2 PostgreSQL Schema
- #1.4 API Testing with New Database
- #2.1 Environment Configuration

## Files to Create
- [ ] `scripts/migrate_sqlite_to_postgresql.py` - Main migration script
- [ ] `scripts/validate_migration.py` - Data validation
- [ ] `scripts/rollback_migration.sql` - Rollback script

## Definition of Done
✅ 424,737 records in PostgreSQL  
✅ Data integrity: 100% (validation script passes)  
✅ Foreign key constraints valid  
✅ Rollback tested successfully  
✅ Migration time < 10 minutes  
✅ Team briefed on migration results
