# PHASE 0 — TECHNICAL IMPLEMENTATION GUIDE
**Status:** Ready for Development Team  
**Timeline:** 4 Days (Mon-Thu Week 1)  
**Objective:** Fix 3 critical blockers, pass gate criteria, unblock Phase 1

---

## OVERVIEW

Phase 0 consists of 5 major tasks with detailed subtasks. This document provides the technical specifications, code templates, and execution steps for each task.

### Critical Path
```
Day 1 (Mon):   Tasks 1.1-1.2 + 2.1-2.2 (parallel)
Day 2 (Tue):   Tasks 1.3-1.4 + 2.3-2.4 + 3.1-3.4 (parallel)
Day 3 (Wed):   Tasks 1.5-1.6 (PostgreSQL setup + endpoint tests)
Day 4 (Thu):   Tasks 4 + 5 (Load testing + documentation)
```

**Total Effort:** ~4 person-days  
**Team Size:** 2 backend + 1 frontend + 1 devops + 1 QA (minimum)

---

## TASK 1: SQLite → PostgreSQL Migration

**Owner:** Backend Lead + DevOps  
**Timeline:** 2-3 days  
**Blocker:** YES 🔴

### 1.1 AUDIT CURRENT SQLite SETUP

#### 1.1.1 Inventory Current State

**Location:** `api/db/models.py`

**Steps:**
```bash
# Check database file size
ls -lh api/database/petpooja_retail_db.sqlite3

# List all tables
sqlite3 api/database/petpooja_retail_db.sqlite3 ".tables"

# Get record counts
sqlite3 api/database/petpooja_retail_db.sqlite3 "SELECT name, COUNT(*) FROM sqlite_master WHERE type='table' GROUP BY name;"

# Check schema
sqlite3 api/database/petpooja_retail_db.sqlite3 ".schema"
```

**Expected Output:**
```
Current Database State:
├── Size: ~55MB
├── Tables: 10 (users, customers, products, sales, sale_items, inventory, invoices, suppliers, alerts, employees)
├── Total Records: 424,737
└── Schema: [dump schema here]
```

**Audit Checklist:**
```python
# Run this Python script to audit models:

import inspect
from api.db.models import *

MODELS = [User, Customer, Product, Sale, SaleItem, Inventory, Invoice, Supplier, Alert, Employee]

for model in MODELS:
    print(f"\n=== {model.__name__} ===")
    
    # Check for SQLite-specific issues
    for column_name, column in inspect.getmembers(model):
        if isinstance(column, Column):
            # Check AUTOINCREMENT (SQLite-specific)
            if hasattr(column, 'autoincrement'):
                print(f"  ⚠️  {column_name}: has autoincrement={column.autoincrement}")
            
            # Check for Boolean columns
            if str(column.type) == 'BOOLEAN':
                print(f"  ✅ {column_name}: BOOLEAN type OK")
            elif str(column.type) in ('INTEGER', 'INT'):
                print(f"  ⚠️  {column_name}: Using INTEGER for boolean? Check.")
            
            # Check for created_at/updated_at defaults
            if 'created_at' in column_name or 'updated_at' in column_name:
                if column.server_default is None and column.default is None:
                    print(f"  ⚠️  {column_name}: No default timestamp!")
```

**Output File:** `docs/CURRENT_DATABASE_STATE.md`

---

#### 1.1.2 Identify SQLite-Specific Issues

**Common Issues to Check:**

```python
# Issue 1: AUTOINCREMENT vs SERIAL
# WRONG (SQLite):
id = Column(Integer, primary_key=True, autoincrement=True)

# RIGHT (PostgreSQL-compatible):
id = Column(Integer, primary_key=True, autoincrement=True)  # Still works; SQLAlchemy handles it

# Issue 2: Boolean columns stored as INTEGER
# WRONG:
is_active = Column(Integer, default=1)  # SQLite stores boolean as 0/1

# RIGHT:
is_active = Column(Boolean, default=True)

# Issue 3: Missing server defaults on timestamps
# WRONG:
created_at = Column(DateTime, default=datetime.utcnow)  # Python-side default

# RIGHT:
created_at = Column(DateTime, server_default=func.now())  # Database-side default

# Issue 4: TEXT vs VARCHAR
# OK in SQLite, but VARCHAR more specific:
description = Column(Text)  # Can be VARCHAR(500) in PostgreSQL
```

**Action Items:**
- [ ] Run audit script above
- [ ] Document all SQLite-specific patterns found
- [ ] Create migration fix list

---

### 1.2 UPDATE DATABASE CONNECTION LAYER

**Location:** `api/db/database.py`

#### 1.2.1 Current Connection Code

```python
# CURRENT (SQLite only):
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./petpooja_retail_db.sqlite3"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_size=20,
    max_overflow=40,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

#### 1.2.2 Updated Connection Code (PostgreSQL + SQLite fallback)

**Replace with:**

```python
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Determine database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./petpooja_retail_db.sqlite3"  # Fallback for local dev only
)

# Log which database is being used
DB_TYPE = "PostgreSQL" if "postgresql" in DATABASE_URL else "SQLite"
print(f"[INFO] Using {DB_TYPE} database")
print(f"[INFO] DATABASE_URL: {DATABASE_URL.split('@')[0] if '@' in DATABASE_URL else DATABASE_URL[:50]}...")

# Configuration differs by database type
if "postgresql" in DATABASE_URL:
    # PostgreSQL configuration
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        pool_size=20,           # Connection pool size
        max_overflow=40,        # Max overflow connections
        pool_pre_ping=True,     # Verify connections before use
        connect_args={
            "connect_timeout": 10,
            "application_name": "rdios_app"
        }
    )
else:
    # SQLite configuration (local dev only)
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        pool_size=5,
        max_overflow=10,
    )

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

def get_db():
    """Dependency for FastAPI routes to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Environment Variables to Set:**

```bash
# .env (local development - use SQLite)
DATABASE_URL=sqlite:///./petpooja_retail_db.sqlite3

# .env.staging (staging - use PostgreSQL)
DATABASE_URL=postgresql://rdios_user:${POSTGRES_PASSWORD}@postgres-staging:5432/rdios_db

# .env.production (production - use PostgreSQL)
DATABASE_URL=postgresql://rdios_user:${POSTGRES_PASSWORD}@postgres-prod:5432/rdios_db
```

**Verification:**
```python
# Test connection after update
from api.db.database import engine, SessionLocal

# Test 1: Can we create engine?
print(f"Engine created: {engine}")

# Test 2: Can we connect?
try:
    with engine.connect() as conn:
        result = conn.execute("SELECT 1")
        print(f"✅ Database connection successful")
except Exception as e:
    print(f"❌ Database connection failed: {e}")

# Test 3: Can we create session?
try:
    db = SessionLocal()
    db.close()
    print(f"✅ Session creation successful")
except Exception as e:
    print(f"❌ Session creation failed: {e}")
```

**Checklist:**
- [ ] Updated `api/db/database.py` with new connection logic
- [ ] Added environment variable support
- [ ] Tested connection locally (SQLite)
- [ ] Tested connection string parsing
- [ ] Added logging for database type

---

### 1.3 CREATE ALEMBIC MIGRATION

**Location:** `alembic/`

#### 1.3.1 Initialize Alembic (if not exists)

```bash
# If Alembic not yet set up:
cd api
alembic init alembic

# This creates:
# alembic/
# ├── env.py           (migration environment config)
# ├── script.py.mako   (migration template)
# └── versions/        (migration scripts)
```

#### 1.3.2 Configure alembic/env.py for Auto-Migration

```python
# alembic/env.py - UPDATE THIS SECTION:

from api.db.database import engine
from api.db.models import Base

# ... existing code ...

def run_migrations_online() -> None:
    """Run migrations in 'online' mode"""
    
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = os.getenv(
        "DATABASE_URL",
        "sqlite:///./petpooja_retail_db.sqlite3"
    )
    
    connectable = engine
    
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=Base.metadata,
            render_as_batch=True,  # Important for compatibility
        )
        
        with context.begin_transaction():
            context.run_migrations()
```

#### 1.3.3 Create Auto-Migration Script

```bash
# Generate migration from current models
cd api
alembic revision --autogenerate -m "SQLite to PostgreSQL migration"

# This creates: alembic/versions/abc123_sqlite_to_postgresql.py
```

**Generated Migration Should Include:**
- Create all tables with PostgreSQL-specific syntax
- Add foreign keys
- Add indexes
- Add constraints

**Verify Generated Migration:**

```python
# alembic/versions/abc123_sqlite_to_postgresql.py should have:

def upgrade():
    """Upgrade to PostgreSQL"""
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    # ... more tables ...

def downgrade():
    """Downgrade (rollback)"""
    op.drop_table('users')
    # ... more tables ...
```

**Checklist:**
- [ ] Alembic initialized
- [ ] Migration generated
- [ ] Migration reviewed (no errors)
- [ ] Downgrade function included

---

### 1.4 CREATE DATA MIGRATION SCRIPT

**Location:** `scripts/migrate_sqlite_to_postgres.py`

#### 1.4.1 SQLite → PostgreSQL Data Migration Script

```python
#!/usr/bin/env python
"""
Migrate data from SQLite to PostgreSQL
Usage: python scripts/migrate_sqlite_to_postgres.py
"""

import os
import sqlite3
import sys
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Source (SQLite)
SQLITE_URL = "sqlite:///./petpooja_retail_db.sqlite3"
sqlite_engine = create_engine(SQLITE_URL)

# Target (PostgreSQL)
POSTGRES_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/rdios_db")
postgres_engine = create_engine(POSTGRES_URL)

# Table order (respect foreign keys)
TABLES_IN_ORDER = [
    'users',
    'employees', 
    'customers',
    'products',
    'inventory',
    'sales',
    'sale_items',
    'invoices',
    'suppliers',
    'alerts'
]

def get_row_count(engine, table_name):
    """Get total rows in a table"""
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        return result.scalar()

def migrate_table(table_name):
    """Migrate single table from SQLite to PostgreSQL"""
    
    print(f"\n📋 Migrating {table_name}...", end=" ")
    
    try:
        # Read from SQLite
        with sqlite_engine.connect() as sqlite_conn:
            result = sqlite_conn.execute(text(f"SELECT * FROM {table_name}"))
            rows = result.fetchall()
            columns = result.keys()
        
        if not rows:
            print(f"✅ (0 rows)")
            return True
        
        # Write to PostgreSQL
        with postgres_engine.connect() as pg_conn:
            # Build INSERT statement
            cols_str = ", ".join(columns)
            vals_str = ", ".join([f"${i+1}" for i in range(len(columns))])
            insert_sql = f"INSERT INTO {table_name} ({cols_str}) VALUES ({vals_str})"
            
            # Insert in batches
            batch_size = 1000
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i+batch_size]
                for row in batch:
                    pg_conn.execute(text(insert_sql), row)
                pg_conn.commit()
            
            pg_conn.commit()
        
        migrated_count = len(rows)
        print(f"✅ ({migrated_count} rows)")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def verify_migration():
    """Verify data integrity after migration"""
    
    print(f"\n🔍 Verifying migration...")
    
    all_ok = True
    for table_name in TABLES_IN_ORDER:
        sqlite_count = get_row_count(sqlite_engine, table_name)
        postgres_count = get_row_count(postgres_engine, table_name)
        
        if sqlite_count == postgres_count:
            print(f"  ✅ {table_name}: {sqlite_count} rows match")
        else:
            print(f"  ❌ {table_name}: SQLite={sqlite_count}, PostgreSQL={postgres_count} MISMATCH")
            all_ok = False
    
    return all_ok

def main():
    """Main migration process"""
    
    print("=" * 60)
    print("SQLite → PostgreSQL Data Migration")
    print("=" * 60)
    
    print(f"\nSource: {SQLITE_URL}")
    print(f"Target: {POSTGRES_URL.split('@')[0]}...{POSTGRES_URL.split('@')[1] if '@' in POSTGRES_URL else ''}")
    
    # Step 1: Verify connections
    print(f"\n🔗 Testing connections...")
    try:
        with sqlite_engine.connect() as conn:
            print(f"  ✅ SQLite connection OK")
    except Exception as e:
        print(f"  ❌ SQLite connection FAILED: {e}")
        sys.exit(1)
    
    try:
        with postgres_engine.connect() as conn:
            print(f"  ✅ PostgreSQL connection OK")
    except Exception as e:
        print(f"  ❌ PostgreSQL connection FAILED: {e}")
        sys.exit(1)
    
    # Step 2: Migrate tables
    print(f"\n📊 Migrating data...")
    failed_tables = []
    
    for table_name in TABLES_IN_ORDER:
        if not migrate_table(table_name):
            failed_tables.append(table_name)
    
    # Step 3: Verify
    if not verify_migration():
        print(f"\n❌ Verification FAILED - check data integrity!")
        sys.exit(1)
    
    print(f"\n" + "=" * 60)
    if failed_tables:
        print(f"❌ Migration INCOMPLETE - failed tables: {failed_tables}")
        sys.exit(1)
    else:
        print(f"✅ Migration COMPLETE - all data transferred!")
        print(f"=" * 60)

if __name__ == "__main__":
    main()
```

**Usage:**
```bash
# Set target database first
export DATABASE_URL="postgresql://user:pass@localhost:5432/rdios_db"

# Run migration
python scripts/migrate_sqlite_to_postgres.py
```

**Expected Output:**
```
============================================================
SQLite → PostgreSQL Data Migration
============================================================

Source: sqlite:///./petpooja_retail_db.sqlite3
Target: postgresql://user:...@localhost/rdios_db

🔗 Testing connections...
  ✅ SQLite connection OK
  ✅ PostgreSQL connection OK

📊 Migrating data...
📋 Migrating users... ✅ (15 rows)
📋 Migrating employees... ✅ (8 rows)
📋 Migrating customers... ✅ (5200 rows)
📋 Migrating products... ✅ (26400 rows)
...

🔍 Verifying migration...
  ✅ users: 15 rows match
  ✅ employees: 8 rows match
  ✅ customers: 5200 rows match
  ...

============================================================
✅ Migration COMPLETE - all data transferred!
============================================================
```

**Checklist:**
- [ ] Migration script created
- [ ] Tested with dummy data locally
- [ ] Handles large batch transfers (1000K+ records)
- [ ] Verification step included
- [ ] Rollback notes documented

---

### 1.5 UPDATE docker-compose.yml

**Location:** `docker-compose.yml`

#### 1.5.1 Add PostgreSQL Service

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: rdios-postgres
    environment:
      POSTGRES_USER: rdios
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-rdios_dev_pass}
      POSTGRES_DB: rdios_db
      POSTGRES_INITDB_ARGS: "-c timezone=UTC"
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/01-init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U rdios -d rdios_db"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - rdios-network

  # Backend API (FastAPI)
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    container_name: rdios-backend
    environment:
      DATABASE_URL: postgresql://rdios:${POSTGRES_PASSWORD:-rdios_dev_pass}@postgres:5432/rdios_db
      API_HOST: 0.0.0.0
      API_PORT: 8000
      LOG_LEVEL: info
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./api:/app/api
    networks:
      - rdios-network

  # Frontend (React)
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    container_name: rdios-frontend
    environment:
      VITE_API_URL: http://localhost:8000
    ports:
      - "5173:5173"
    depends_on:
      - backend
    networks:
      - rdios-network

volumes:
  postgres_data:

networks:
  rdios-network:
    driver: bridge
```

#### 1.5.2 Startup Script

```bash
#!/bin/bash
# scripts/start-dev.sh

echo "🚀 Starting R-DIOS Development Environment..."

# Set environment variables
export POSTGRES_PASSWORD=rdios_dev_pass
export DATABASE_URL=postgresql://rdios:rdios_dev_pass@localhost:5432/rdios_db

echo "📦 Building containers..."
docker-compose build

echo "🔧 Starting services..."
docker-compose up -d

echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5

echo "🗄️  Applying database migrations..."
docker-compose exec backend alembic upgrade head

echo "✅ Development environment ready!"
echo ""
echo "Services:"
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:5173"
echo "  Postgres: localhost:5432"
echo ""
echo "View logs: docker-compose logs -f"
```

**Checklist:**
- [ ] Added PostgreSQL service to docker-compose.yml
- [ ] Set environment variables correctly
- [ ] Added healthcheck for database
- [ ] Updated backend to use DATABASE_URL env var
- [ ] Tested docker-compose up locally
- [ ] Updated startup scripts

---

### 1.6 TEST ALL 37 API ENDPOINTS

**Location:** `tests/`

#### 1.6.1 Run Full Test Suite

```bash
# Run all tests
pytest tests/ -v --tb=short

# Run with coverage
pytest tests/ --cov=api --cov-report=html

# Run specific test file
pytest tests/test_inventory.py -v

# Run specific test
pytest tests/test_inventory.py::test_list_inventory -v
```

#### 1.6.2 Expected Test Results

```
tests/test_auth.py::test_login PASSED
tests/test_auth.py::test_jwt_validation PASSED
tests/test_dashboard.py::test_realtime_dashboard PASSED
tests/test_inventory.py::test_list_inventory PASSED
tests/test_inventory.py::test_create_product PASSED
tests/test_invoicing.py::test_create_invoice PASSED
tests/test_invoicing.py::test_invoice_pdf PASSED
tests/test_pos.py::test_pos_transaction PASSED
tests/test_alerts.py::test_list_alerts PASSED
...

======================== 37 passed in 45.23s ========================
```

#### 1.6.3 Performance Baseline

```bash
# Measure response times post-migration
# Create a performance test

import time
import requests

API_URL = "http://localhost:8000"
ENDPOINTS = [
    ("GET", "/api/v1/inventory/list"),
    ("GET", "/api/v1/dashboard/realtime"),
    ("GET", "/api/v1/invoices"),
    # ... add all critical endpoints
]

results = {}
for method, endpoint in ENDPOINTS:
    start = time.time()
    response = requests.request(method, f"{API_URL}{endpoint}")
    elapsed = (time.time() - start) * 1000  # Convert to ms
    
    results[endpoint] = {
        "status": response.status_code,
        "time_ms": elapsed
    }
    print(f"{endpoint}: {elapsed:.2f}ms")

# Compare with baseline:
# Before: avg 104ms
# After: should be similar or better with PostgreSQL
```

**Checklist:**
- [ ] All 37 endpoints pass tests (100%)
- [ ] Response times match or improve baseline
- [ ] No SQLite-specific query failures
- [ ] Performance report generated
- [ ] Results documented

---

## TASK 2: REMOVE LOCALHOST HARDCODES

**Owner:** Frontend Lead  
**Timeline:** 1 day

### 2.1 AUDIT FRONTEND SERVICE FILES

**Command:**
```bash
grep -r "http://localhost:8000" src/
```

**Expected Output:**
```
src/services/inventory.js:const API_URL = "http://localhost:8000";
src/services/dashboard.js:const API_URL = "http://localhost:8000";
src/services/invoices.js:const API_URL = "http://localhost:8000";
... (10+ more files)
```

**Create Inventory:**
```markdown
# Hardcoded URLs Inventory

| File | Instances | Status |
|------|-----------|--------|
| src/services/inventory.js | 3 | ❌ TO FIX |
| src/services/dashboard.js | 2 | ❌ TO FIX |
| src/services/invoices.js | 1 | ❌ TO FIX |
...
| TOTAL | 20+ | - |
```

---

### 2.2 CREATE ENV FILE STRUCTURE

**Create `.env.example`:**
```
# Local Development
VITE_API_URL=http://localhost:8000
VITE_LOG_LEVEL=debug
```

**Create `.env`:**
```
# Local Development - DO NOT COMMIT
VITE_API_URL=http://localhost:8000
VITE_LOG_LEVEL=debug
```

**Create `.env.production`:**
```
# Production
VITE_API_URL=https://api.r-dios.com
VITE_LOG_LEVEL=error
```

**Create `.env.staging`:**
```
# Staging
VITE_API_URL=https://staging-api.r-dios.com
VITE_LOG_LEVEL=info
```

---

### 2.3 CREATE CENTRALIZED CONFIG

**Create `src/config.js`:**

```javascript
/**
 * Centralized configuration for frontend
 * All environment-dependent values go here
 */

export const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const LOG_LEVEL = import.meta.env.VITE_LOG_LEVEL || 'debug';

// Validate configuration
if (!API_BASE) {
  console.error('❌ VITE_API_URL not set. Using default http://localhost:8000');
}

console.log(`[CONFIG] API_BASE: ${API_BASE}`);
console.log(`[CONFIG] LOG_LEVEL: ${LOG_LEVEL}`);

export const getApiUrl = (endpoint) => `${API_BASE}${endpoint}`;
```

**Update All Service Files:**

```javascript
// BEFORE (WRONG):
// src/services/inventory.js
const API_URL = "http://localhost:8000";

export const fetchInventory = async (page = 1) => {
  const response = await fetch(`${API_URL}/api/v1/inventory/list?page=${page}`);
  return response.json();
};

// AFTER (CORRECT):
// src/services/inventory.js
import { getApiUrl } from '../config';

export const fetchInventory = async (page = 1) => {
  const response = await fetch(getApiUrl(`/api/v1/inventory/list?page=${page}`));
  return response.json();
};
```

**Template for All Services:**

```javascript
// src/services/[feature].js

import { getApiUrl } from '../config';

const API_ENDPOINTS = {
  LIST: '/api/v1/[feature]/list',
  CREATE: '/api/v1/[feature]/create',
  UPDATE: '/api/v1/[feature]/:id',
  DELETE: '/api/v1/[feature]/:id',
};

export const fetchList = async (page = 1, perPage = 50) => {
  const response = await fetch(
    getApiUrl(`${API_ENDPOINTS.LIST}?page=${page}&per_page=${perPage}`)
  );
  if (!response.ok) throw new Error(`Failed to fetch list`);
  return response.json();
};

export const createItem = async (data) => {
  const response = await fetch(getApiUrl(API_ENDPOINTS.CREATE), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error(`Failed to create item`);
  return response.json();
};
```

---

### 2.4 TEST IN DIFFERENT ENVIRONMENTS

**Build & Test Script:**

```bash
#!/bin/bash
# scripts/test-build-environments.sh

echo "Testing builds with different API URLs..."

# Test 1: Local development
echo "🔨 Building for localhost..."
VITE_API_URL=http://localhost:8000 npm run build
if [ $? -eq 0 ]; then echo "✅ Localhost build OK"; else echo "❌ Localhost build FAILED"; fi

# Test 2: Staging
echo "🔨 Building for staging..."
VITE_API_URL=https://staging-api.r-dios.com npm run build
if [ $? -eq 0 ]; then echo "✅ Staging build OK"; else echo "❌ Staging build FAILED"; fi

# Test 3: Production
echo "🔨 Building for production..."
VITE_API_URL=https://api.r-dios.com npm run build
if [ $? -eq 0 ]; then echo "✅ Production build OK"; else echo "❌ Production build FAILED"; fi

# Test 4: Verify embedded URLs in build
echo "🔍 Verifying no localhost URLs in build..."
if grep -r "localhost:8000" dist/; then
  echo "❌ Found localhost URLs in build!"
  exit 1
else
  echo "✅ No localhost URLs found"
fi
```

**Checklist:**
- [ ] Created `src/config.js`
- [ ] Updated all service files
- [ ] Created `.env` files
- [ ] Build tests pass with all environments
- [ ] No hardcoded URLs remain

---

## TASK 3: CRASH PATCHES & STABILITY FIXES

**Owner:** Backend Lead  
**Timeline:** 1 day

### 3.1 PAGINATION FIXES

**Fix LIMIT 5000 Band-Aid:**

```python
# BEFORE (WRONG):
# api/routers/inventory.py
@router.get("/list")
async def list_inventory(db: Session = Depends(get_db)):
    # Band-aid: just LIMIT 5000 to avoid crash
    products = db.query(Product).limit(5000).all()
    return products

# AFTER (CORRECT):
# api/routers/inventory.py
from typing import Optional
from pydantic import BaseModel

class PaginationParams(BaseModel):
    page: int = 1
    per_page: int = 50
    max_per_page: int = 200

@router.get("/list")
async def list_inventory(
    page: int = 1,
    per_page: int = 50,
    db: Session = Depends(get_db)
):
    """List inventory with pagination"""
    # Validate pagination params
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 50
    if per_page > 200:
        per_page = 200  # Max to prevent abuse
    
    # Calculate offset
    offset = (page - 1) * per_page
    
    # Get total count
    total = db.query(Product).count()
    
    # Get paginated results
    items = db.query(Product).offset(offset).limit(per_page).all()
    
    # Return paginated response
    return {
        "success": True,
        "data": items,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page
        }
    }
```

---

### 3.2 MEMORY LEAK FIXES

**Optimize Queries (Select Only Needed Columns):**

```python
# BEFORE (LOADS EVERYTHING):
# api/routers/inventory.py
products = db.query(Product).all()  # Loads 50+ columns per product

# AFTER (SELECT ONLY NEEDED):
from sqlalchemy import select

products = db.query(
    Product.id,
    Product.name,
    Product.price,
    Product.stock_qty,
    Product.last_updated
).all()  # Only 5 columns per product
```

**Connection Pooling Configuration:**

```python
# api/db/database.py
from sqlalchemy.pool import QueuePool

if "postgresql" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=20,           # Keep 20 connections open
        max_overflow=40,        # Allow up to 40 overflow connections
        pool_pre_ping=True,     # Verify connection before use
        pool_recycle=3600,      # Recycle connections after 1 hour
    )
```

---

### 3.3 ERROR HANDLING FIXES

**Add Try/Except to ALL Write Operations:**

```python
# BEFORE:
@router.post("/products")
async def create_product(data: ProductCreate, db: Session = Depends(get_db)):
    product = Product(**data.dict())
    db.add(product)
    db.commit()  # ❌ No error handling
    return product

# AFTER:
import logging
logger = logging.getLogger(__name__)

@router.post("/products")
async def create_product(data: ProductCreate, db: Session = Depends(get_db)):
    try:
        product = Product(**data.dict())
        db.add(product)
        db.commit()
        db.refresh(product)
        logger.info(f"Created product: {product.id}")
        return {
            "success": True,
            "data": product,
            "message": "Product created successfully"
        }
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Product already exists or invalid data"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to create product. Please try again."
        )
```

---

### 3.4 CORS & SECURITY FIXES

**Verify CORS Configuration:**

```python
# api/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# .env
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

---

## TASK 4: COMPREHENSIVE TESTING

**Owner:** QA Lead  
**Timeline:** 1 day

### 4.1 UNIT TESTS

```bash
pytest tests/ -v --tb=short
```

**Expected:** 100% pass rate

---

### 4.2 INTEGRATION TESTS

```python
# tests/test_integration_e2e.py

def test_pos_transaction_end_to_end(client):
    """Test complete POS workflow: add items → create sale → verify inventory"""
    
    # Step 1: Get inventory before
    resp = client.get("/api/v1/inventory/list?page=1&per_page=10")
    assert resp.status_code == 200
    initial_qty = resp.json()["data"][0]["stock_qty"]
    
    # Step 2: Create sale
    sale_data = {
        "items": [{"product_id": 1, "qty": 5, "price": 100}]
    }
    resp = client.post("/api/v1/sales", json=sale_data)
    assert resp.status_code == 201
    sale_id = resp.json()["data"]["id"]
    
    # Step 3: Verify inventory updated
    resp = client.get("/api/v1/inventory/list?page=1&per_page=10")
    updated_qty = resp.json()["data"][0]["stock_qty"]
    assert updated_qty == initial_qty - 5
    
    print("✅ POS transaction E2E test passed")
```

---

### 4.3 LOAD TESTING

```bash
# Using Apache Bench
ab -n 1000 -c 100 http://localhost:8000/api/v1/inventory/list

# Expected output:
# Requests per second:   500.00 [#/sec]
# Time per request:      200.00 [ms]
# Transfer rate:         5000.00 [Kbytes/sec]
```

---

### 4.4 SECURITY TESTS

```python
# Test JWT authentication
def test_jwt_invalid_token(client):
    resp = client.get(
        "/api/v1/inventory/list",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert resp.status_code == 401
```

---

## GATE CRITERIA CHECKLIST

```
MUST PASS (all 10):
[ ] PostgreSQL successfully replaces SQLite
    └─ All data transferred correctly
[ ] All 37 API endpoints pass tests (100%)
    └─ pytest results show 37/37 passed
[ ] Load test: 100 concurrent users, <200ms avg, 0% error
    └─ Load test results documented
[ ] VITE_API_URL env variable works everywhere
    └─ Builds work with all 3 environments
[ ] No localhost hardcodes remain in codebase
    └─ grep -r "localhost:8000" returns nothing
[ ] Memory/crashes fixed
    └─ No OOM errors under sustained load
[ ] No exception traces to UI
    └─ All errors return user-friendly messages
[ ] CORS + JWT + rate-limiting verified
    └─ Manual testing confirms all 3 work
[ ] Documentation updated
    └─ README, DEPLOYMENT.md updated
[ ] Rollback plan documented
    └─ PHASE_0_ROLLBACK_PLAN.md created
```

---

## DAILY EXECUTION TIMELINE

```
📅 DAY 1 (MONDAY)
─────────────────────────────────────────────────────
09:00 - 10:00   Task 1.1 (Audit SQLite)             [Backend Lead]
09:00 - 10:30   Task 2.1 (Audit URLs)               [Frontend Lead]
10:00 - 11:30   Task 1.2 (Update DB connection)     [Backend Lead + DevOps]
10:30 - 12:00   Task 2.2 (Create .env files)        [Frontend Lead]
12:00 - 13:00   🍴 LUNCH
13:00 - 14:00   Task 1.2 continued                  [Backend Lead]
13:00 - 14:30   Task 2.3 (Create config.js)         [Frontend Lead]
14:00 - 15:00   Task 3.1 (Pagination fixes)         [Backend Lead]
14:30 - 16:00   Task 2.4 (Test builds)              [Frontend Lead]
16:00 - 17:00   Daily standup + issues              [Everyone]

✅ EOD: DB connection updated, .env ready, URLs centralized

─────────────────────────────────────────────────────
📅 DAY 2 (TUESDAY)
─────────────────────────────────────────────────────
09:00 - 10:30   Task 1.3 (Alembic migration)        [Backend Lead]
09:00 - 10:00   Deploy PostgreSQL locally           [DevOps]
10:00 - 11:30   Task 1.4 (Data migration script)    [Backend Lead]
10:30 - 12:00   Test script + verification          [QA]
12:00 - 13:00   🍴 LUNCH
13:00 - 14:00   Task 1.4 continued                  [Backend Lead]
13:00 - 14:30   Task 3.2-3.4 (Crash fixes)          [Backend Lead]
14:00 - 15:00   Task 1.5 (docker-compose update)    [DevOps]
14:30 - 16:00   Test all URL replacements           [Frontend Lead]
16:00 - 17:00   Daily standup + issues              [Everyone]

✅ EOD: Migration scripts ready, all URLs replaced, crash patches applied

─────────────────────────────────────────────────────
📅 DAY 3 (WEDNESDAY)
─────────────────────────────────────────────────────
09:00 - 10:00   Local PostgreSQL setup              [DevOps]
09:00 - 11:00   Task 1.5-1.6 (Migrate data)         [Backend Lead]
10:00 - 11:00   Run alembic migrations              [Backend Lead]
11:00 - 12:00   Verify data integrity               [QA]
12:00 - 13:00   🍴 LUNCH
13:00 - 14:30   Task 4.1-4.2 (Unit + integration)   [QA]
14:30 - 15:30   Task 4.3 (Load testing)             [QA]
15:30 - 16:30   Performance baseline report         [QA]
16:30 - 17:00   Daily standup + issues              [Everyone]

✅ EOD: All endpoints tested, load test passed, 37/37 ✅

─────────────────────────────────────────────────────
📅 DAY 4 (THURSDAY)
─────────────────────────────────────────────────────
09:00 - 10:00   Task 4.4 (Security tests)           [QA]
09:00 - 10:30   Task 5 (Documentation)              [Tech Lead]
10:00 - 11:00   CORS + JWT + rate-limiting tests    [Backend Lead]
10:30 - 12:00   Create PHASE_0_COMPLETION_REPORT    [Tech Lead]
12:00 - 13:00   🍴 LUNCH
13:00 - 14:00   Final verification checks           [Everyone]
14:00 - 15:00   Rollback plan documentation         [DevOps]
15:00 - 16:00   Team review + gate approval         [All Leads]
16:00 - 17:00   Phase 0 gate sign-off               [Tech Lead]

✅ EOD: GATE APPROVED - Ready for Phase 1!
```

---

## SUCCESS METRICS

**Phase 0 = SUCCESS when:**

```
✅ PostgreSQL deployed and tested
✅ All 37 endpoints passing
✅ Load test: 100 concurrent users OK
✅ 0 hardcoded URLs remaining
✅ 0 crashes under load
✅ All documentation updated
✅ Team sign-off complete
```

**Phase 0 = FAILURE if:**

```
❌ Any endpoint still failing
❌ Load test shows >10% error rate
❌ Hardcoded URLs still exist
❌ Migration incomplete or data loss
❌ Crashes during testing
```

---

*Phase 0 Technical Implementation Guide  
Ready for Development Team  
Proceed to execution when gate approval received*
