# PHASE 0: CRITICAL BLOCKERS EXECUTION PACK
**Timeline:** Feb 17-20, 2026 (4 days)  
**Status:** 🟢 READY FOR IMMEDIATE START  
**Last Updated:** Feb 14, 2026

---

## PHASE 0 OVERVIEW

| Aspect | Details |
|--------|---------|
| **Duration** | 4 business days (Feb 17-20) |
| **Team Size** | 10 people (distributed roles) |
| **Total Effort** | 50 hours |
| **Critical Blockers** | 3 (SQLite, URLs, Pagination) |
| **Gate Deadline** | Feb 20, 5 PM IST |
| **Go-Live After Gate** | Feb 21 (Production) |
| **Phase 1 Start** | Feb 24 (if Phase 0 approved) |

---

## THE 3 CRITICAL BLOCKERS

### BLOCKER #1: SQLite Bottleneck ⚠️
**Problem:** 26K products causes OOM errors, slow queries >2s  
**Impact:** System crashes under load, unacceptable latency  
**Solution:** Migrate to PostgreSQL with proper indexing  
**Owner:** DevOps Lead + Backend Lead  
**Effort:** 20 hours  
**Target Completion:** Feb 18, 12 PM

**What needs to happen:**
1. Spin up PostgreSQL (AWS RDS or Docker)
2. Export data from SQLite (424K+ records)
3. Create schema in PostgreSQL with indexes
4. Migrate data (with validation)
5. Update connection strings in API
6. Test all 37 endpoints
7. Load testing: 100 concurrent users

**Success Criteria:**
- ✅ PostgreSQL online and responding
- ✅ All 424K+ records migrated
- ✅ Data integrity: 100% (no missing rows)
- ✅ Query latency <200ms for inventory list
- ✅ Load test: 100 users, <200ms, 0% error

---

### BLOCKER #2: Hardcoded URLs 🔗
**Problem:** Base URLs hardcoded in code (`localhost:8000`, API keys in files)  
**Impact:** Cannot switch environments, security risk, config drift  
**Solution:** Implement environment variables (.env, Docker secrets)  
**Owner:** Backend Lead + Frontend Lead  
**Effort:** 15 hours  
**Target Completion:** Feb 18, 6 PM

**What needs to happen:**
1. Create `.env.example` with all required variables
2. Update all API calls to use env variables
3. Backend: Update `main.py` config loading
4. Frontend: Update `vite.config.ts` and API client
5. Remove hardcoded values from git
6. Document env setup for team
7. Test in 3 environments (dev, staging, prod)

**Environment Variables Needed:**
```
# API
API_BASE_URL=http://localhost:8000
API_PORT=8000

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/enterprise_retail
DATABASE_POOL_SIZE=10

# Frontend
FRONTEND_URL=http://localhost:5173
VITE_API_BASE_URL=http://localhost:8000

# Auth
JWT_SECRET=your-secret-key-here
JWT_EXPIRY=3600

# Third-party APIs
RAZORPAY_KEY=xxx
RAZORPAY_SECRET=xxx
OPENROUTER_API_KEY=xxx

# Environment
ENVIRONMENT=development
DEBUG=true
```

**Success Criteria:**
- ✅ All hardcoded URLs removed (grep returns 0)
- ✅ .env.example complete with 15+ variables
- ✅ Backend loads from .env
- ✅ Frontend loads from .env
- ✅ Tests pass in dev/staging/prod configs

---

### BLOCKER #3: Pagination Crash 📄
**Problem:** Inventory pagination crashes with 26K products, no limit/offset handling  
**Impact:** Users can't browse products, inventory page unusable  
**Solution:** Implement proper pagination (50/100/250 per page)  
**Owner:** Backend Lead + Frontend Lead  
**Effort:** 15 hours  
**Target Completion:** Feb 19, 12 PM

**What needs to happen:**

**Backend Changes:**
1. Update `GET /api/v1/inventory/list` endpoint:
   - Add query params: `limit` (50/100/250), `offset` (0+), `sort`, `filter`
   - Implement SQL pagination: `LIMIT ? OFFSET ?`
   - Add response metadata: `total_count`, `page`, `pages`
   - Return 50 items by default
   
2. Database optimization:
   - Add composite index: `(product_id, status, stock_level)`
   - Add index on `created_at` for sorting
   - Query plan analysis with EXPLAIN

3. Response structure:
```json
{
  "status": "success",
  "data": [
    {"id": 1, "name": "Product 1", "stock": 100},
    ...
  ],
  "pagination": {
    "total_count": 26400,
    "page": 1,
    "pages": 528,
    "limit": 50,
    "offset": 0
  }
}
```

**Frontend Changes:**
1. Update inventory table component:
   - Add pagination controls (first, prev, next, last)
   - Add page input field
   - Add items-per-page dropdown (50/100/250)
   - Show "Page 1 of 528"

2. State management:
   - Track `currentPage`, `pageSize`, `totalCount`
   - Handle URL params: `?page=1&limit=50`

3. User experience:
   - Show loading spinner during page load
   - Preserve filter state while paginating
   - Quick jump to page number

**Testing:**
1. Unit tests:
   - Pagination with 26K items
   - First page, middle page, last page
   - Invalid page numbers (0, -1, 999999)
   - Different page sizes (50, 100, 250)

2. Integration tests:
   - Load entire dataset paginated
   - Filter + paginate combined
   - Sort + paginate combined
   - Performance: all 528 pages load <2s each

3. Performance:
   - Latency <200ms per page
   - Memory: constant (not growing with dataset)
   - Query time: <50ms from database

**Success Criteria:**
- ✅ Inventory pagination loads all 26K products
- ✅ No crash with any page number
- ✅ Response time <200ms per page
- ✅ All edge cases handled
- ✅ UI shows proper page numbers and controls
- ✅ 100% test pass rate

---

## PHASE 0 TASK BREAKDOWN (10 Tasks)

### Task Group 1: PostgreSQL Migration (4 tasks)

#### TASK 1.1: Set Up PostgreSQL Infrastructure
**Owner:** DevOps Lead  
**Duration:** 4 hours  
**Deadline:** Feb 17, 6 PM  
**Prerequisites:** None  
**Deliverables:**
- [ ] PostgreSQL server running (local Docker or AWS RDS)
- [ ] Database `enterprise_retail` created
- [ ] Connection tested from API
- [ ] Documentation: Connection string, credentials, port

**Steps:**
1. Provision PostgreSQL (AWS RDS: db.t3.micro, 20GB storage, or Docker)
2. Create database: `CREATE DATABASE enterprise_retail;`
3. Test connection: `psql -h localhost -U postgres -d enterprise_retail`
4. Document connection string
5. Set up automated backups

**Success Criteria:**
- ✅ PostgreSQL responding to queries
- ✅ Connection pool working
- ✅ Backup automated

---

#### TASK 1.2: Create PostgreSQL Schema
**Owner:** Backend Lead  
**Duration:** 4 hours  
**Deadline:** Feb 18, 12 PM  
**Prerequisites:** Task 1.1 complete  
**Deliverables:**
- [ ] All 16 tables created in PostgreSQL
- [ ] Indexes created (composites, FKs)
- [ ] Schema validation passed
- [ ] Migration script documented

**Steps:**
1. Export schema from SQLite: `sqlite3 petpooja_retail_db.sqlite3 .schema > schema.sql`
2. Convert SQLite dialect to PostgreSQL
3. Add proper indexes:
   - `inventory (product_id, status, stock_level)`
   - `sales (created_at, customer_id)`
   - `invoices (invoice_date, customer_id)`
4. Create foreign keys
5. Apply permissions and roles

**SQL Changes Example:**
```sql
-- Before (SQLite)
CREATE TABLE inventory (
  id INTEGER PRIMARY KEY,
  product_id TEXT,
  stock_level INTEGER
);

-- After (PostgreSQL)
CREATE TABLE inventory (
  id SERIAL PRIMARY KEY,
  product_id VARCHAR(255) NOT NULL,
  stock_level INTEGER NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_inventory_product_status 
ON inventory(product_id, status, stock_level);
```

**Success Criteria:**
- ✅ All 16 tables exist in PostgreSQL
- ✅ Schema matches SQLite structure
- ✅ Indexes created
- ✅ Foreign keys enforced

---

#### TASK 1.3: Migrate Data from SQLite to PostgreSQL
**Owner:** Backend Lead + DevOps Lead  
**Duration:** 6 hours  
**Deadline:** Feb 18, 6 PM  
**Prerequisites:** Tasks 1.1, 1.2 complete  
**Deliverables:**
- [ ] All 424K+ records migrated
- [ ] Data validation: 100% match
- [ ] Migration script created (reusable)
- [ ] Rollback plan documented

**Steps:**
1. Create migration script (Python/SQL):
   - Read from SQLite table by table
   - Transform data (convert types)
   - Insert into PostgreSQL with batch processing
   - Log progress every 10K records

2. Data validation:
   - Count check: SQLite rows == PostgreSQL rows
   - Sample checks: Compare 100 random rows
   - Checksum validation (hash comparison)
   - NULL checks (expected NULLs match)

3. Performance optimization:
   - Batch inserts: 1000 rows at a time
   - Disable triggers during migration
   - Use COPY command for bulk data

**Migration Script Outline:**
```python
import sqlite3
import psycopg2

# Read from SQLite
sqlite_conn = sqlite3.connect('petpooja_retail_db.sqlite3')
sqlite_cursor = sqlite_conn.cursor()

# Write to PostgreSQL
pg_conn = psycopg2.connect("dbname=enterprise_retail user=postgres")
pg_cursor = pg_conn.cursor()

tables = ['users', 'inventory', 'sales', 'invoices', 'bills', ...]

for table in tables:
    print(f"Migrating {table}...")
    sqlite_cursor.execute(f"SELECT * FROM {table}")
    rows = sqlite_cursor.fetchall()
    
    # Batch insert
    for i in range(0, len(rows), 1000):
        batch = rows[i:i+1000]
        insert_sql = f"INSERT INTO {table} VALUES (%s, %s, ...)"
        pg_cursor.executemany(insert_sql, batch)
        pg_conn.commit()
        print(f"  {i+len(batch)}/{len(rows)}")

# Validation
sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
sqlite_count = sqlite_cursor.fetchone()[0]

pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
pg_count = pg_cursor.fetchone()[0]

assert sqlite_count == pg_count, f"Count mismatch: {sqlite_count} != {pg_count}"
print(f"✅ Migration complete: {pg_count} records")
```

**Success Criteria:**
- ✅ All 424K+ records in PostgreSQL
- ✅ Count validation: 100% match
- ✅ Sample data checks pass
- ✅ No data corruption
- ✅ Migration script documented

---

#### TASK 1.4: Update API Connection & Test All 37 Endpoints
**Owner:** Backend Lead  
**Duration:** 6 hours  
**Deadline:** Feb 19, 12 PM  
**Prerequisites:** Tasks 1.1, 1.2, 1.3 complete  
**Deliverables:**
- [ ] API connected to PostgreSQL
- [ ] All 37 endpoints tested
- [ ] Load test: 100 users, <200ms, 0% error
- [ ] Latency metrics documented

**Changes in Code:**
```python
# Before (SQLite)
DATABASE_URL = "sqlite:///./petpooja_retail_db.sqlite3"

# After (PostgreSQL)
DATABASE_URL = os.getenv("DATABASE_URL", 
    "postgresql://user:pass@localhost:5432/enterprise_retail")

# Connection pooling for PostgreSQL
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600
)
```

**Testing:**
1. Unit test each endpoint:
   - GET endpoints return data
   - POST endpoints create records
   - PUT endpoints update records
   - DELETE endpoints remove records

2. Integration test:
   - Endpoint → API → PostgreSQL flow
   - Check data consistency

3. Load test:
   - 100 concurrent users
   - Sustained for 2 minutes
   - Measure: latency, throughput, errors

**Load Test Script:**
```bash
# Using Apache Bench
ab -n 10000 -c 100 http://localhost:8000/api/v1/inventory/list

# Result format
Requests per second: 500
Time per request: 200ms
Failed requests: 0
```

**Success Criteria:**
- ✅ API connected to PostgreSQL (0 errors)
- ✅ All 37 endpoints working
- ✅ Load test: 100 users, <200ms avg, 0% error
- ✅ Response times logged

---

### Task Group 2: Environment Variables (2 tasks)

#### TASK 2.1: Backend Environment Configuration
**Owner:** Backend Lead  
**Duration:** 5 hours  
**Deadline:** Feb 18, 6 PM  
**Prerequisites:** None  
**Deliverables:**
- [ ] `.env.example` created with 15+ variables
- [ ] `main.py` updated to load from .env
- [ ] All hardcoded URLs removed
- [ ] Documentation complete

**Steps:**
1. Create `.env.example`:
   ```
   # Database
   DATABASE_URL=postgresql://user:pass@localhost:5432/enterprise_retail
   
   # API
   API_BASE_URL=http://localhost:8000
   API_PORT=8000
   
   # Auth
   JWT_SECRET=your-secret-key-generate-with-secrets.token_urlsafe()
   JWT_EXPIRY=3600
   
   # Third-party
   RAZORPAY_KEY=xyz
   OPENROUTER_API_KEY=xyz
   
   # Environment
   ENVIRONMENT=development
   ```

2. Update `main.py`:
   ```python
   from dotenv import load_dotenv
   import os
   
   load_dotenv()
   
   DATABASE_URL = os.getenv("DATABASE_URL")
   API_PORT = int(os.getenv("API_PORT", 8000))
   JWT_SECRET = os.getenv("JWT_SECRET")
   ```

3. Search & replace hardcoded values:
   ```bash
   grep -r "localhost:8000" . --include="*.py"
   grep -r "postgresql://" . --include="*.py"
   ```

4. Test:
   ```bash
   python main.py
   # Verify: Connected to PostgreSQL via ENV variable
   ```

**Success Criteria:**
- ✅ No hardcoded URLs in code (grep returns 0)
- ✅ .env.example complete
- ✅ API loads from .env correctly
- ✅ All 37 endpoints work with env config

---

#### TASK 2.2: Frontend Environment Configuration
**Owner:** Frontend Lead  
**Duration:** 5 hours  
**Deadline:** Feb 18, 6 PM  
**Prerequisites:** None  
**Deliverables:**
- [ ] `.env.example` created for frontend
- [ ] `vite.config.ts` updated
- [ ] API client uses env variables
- [ ] Hardcoded URLs removed

**Steps:**
1. Create `.env.example`:
   ```
   VITE_API_BASE_URL=http://localhost:8000
   VITE_APP_ENV=development
   ```

2. Update `vite.config.ts`:
   ```typescript
   import { defineConfig, loadEnv } from 'vite'
   
   export default defineConfig(({ command, mode }) => {
     const env = loadEnv(mode, process.cwd())
     return {
       define: {
         __API_BASE_URL__: JSON.stringify(env.VITE_API_BASE_URL)
       }
     }
   })
   ```

3. Update API client:
   ```typescript
   // Before
   const apiBase = "http://localhost:8000"
   
   // After
   const apiBase = import.meta.env.VITE_API_BASE_URL
   ```

4. Test in dev:
   ```bash
   npm run dev
   # Verify: Network tab shows requests to env URL
   ```

**Success Criteria:**
- ✅ No hardcoded URLs in React code
- ✅ .env file loaded by Vite
- ✅ API calls use env URL
- ✅ Tests pass

---

### Task Group 3: Pagination (3 tasks)

#### TASK 3.1: Backend Pagination Implementation
**Owner:** Backend Lead  
**Duration:** 6 hours  
**Deadline:** Feb 19, 12 PM  
**Prerequisites:** Task 1.4 complete  
**Deliverables:**
- [ ] GET `/api/v1/inventory/list` updated with pagination
- [ ] SQL pagination queries working
- [ ] Response includes pagination metadata
- [ ] Tests passing

**Implementation:**
```python
# In main.py or inventory router

@app.get("/api/v1/inventory/list")
async def list_inventory(
    limit: int = Query(50, ge=1, le=250),
    offset: int = Query(0, ge=0),
    sort_by: str = "product_id",
    filter_status: str = None
):
    """
    Paginate inventory with limit/offset
    - limit: 50-250 items per page (default 50)
    - offset: skip N items (0-indexed)
    - sort_by: product_id, stock_level, created_at
    - filter_status: active, inactive, discontinued
    """
    
    # Build query
    query = db.query(Inventory)
    
    # Apply filter
    if filter_status:
        query = query.filter(Inventory.status == filter_status)
    
    # Count total
    total_count = query.count()
    pages = (total_count + limit - 1) // limit  # Ceiling division
    
    # Paginate
    items = query.order_by(getattr(Inventory, sort_by))\
                  .limit(limit)\
                  .offset(offset)\
                  .all()
    
    return {
        "status": "success",
        "data": items,
        "pagination": {
            "total_count": total_count,
            "page": (offset // limit) + 1,
            "pages": pages,
            "limit": limit,
            "offset": offset
        }
    }
```

**Database Index:**
```sql
CREATE INDEX idx_inventory_product_status 
ON inventory(product_id, status, stock_level);
```

**Success Criteria:**
- ✅ Endpoint returns paginated results
- ✅ Metadata includes total_count, pages, current page
- ✅ <200ms response time
- ✅ Tests passing (all edge cases)

---

#### TASK 3.2: Frontend Pagination UI
**Owner:** Frontend Lead  
**Duration:** 6 hours  
**Deadline:** Feb 19, 6 PM  
**Prerequisites:** Task 3.1 complete  
**Deliverables:**
- [ ] Inventory page shows pagination controls
- [ ] Page navigation working (first/prev/next/last)
- [ ] Items-per-page selector working (50/100/250)
- [ ] URL params updated (`?page=1&limit=50`)

**React Component:**
```typescript
// InventoryTable.tsx
import { useState, useEffect } from 'react'

const InventoryTable = () => {
  const [items, setItems] = useState([])
  const [pagination, setPagination] = useState({
    total_count: 0,
    page: 1,
    pages: 0,
    limit: 50
  })
  const [loading, setLoading] = useState(false)

  const loadPage = async (page: number, limit: number) => {
    setLoading(true)
    const offset = (page - 1) * limit
    
    const response = await fetch(
      `/api/v1/inventory/list?limit=${limit}&offset=${offset}`
    )
    const data = await response.json()
    
    setItems(data.data)
    setPagination(data.pagination)
    setLoading(false)
  }

  useEffect(() => {
    loadPage(pagination.page, pagination.limit)
  }, [])

  return (
    <div>
      {/* Table */}
      <table>
        <thead>...</thead>
        <tbody>
          {items.map(item => (
            <tr key={item.id}>...</tr>
          ))}
        </tbody>
      </table>

      {/* Pagination Controls */}
      <div className="pagination">
        <button 
          onClick={() => loadPage(1, pagination.limit)}
          disabled={pagination.page === 1}
        >
          First
        </button>
        
        <button 
          onClick={() => loadPage(pagination.page - 1, pagination.limit)}
          disabled={pagination.page === 1}
        >
          Previous
        </button>
        
        <span>
          Page {pagination.page} of {pagination.pages}
        </span>
        
        <input 
          type="number" 
          value={pagination.page}
          min="1"
          max={pagination.pages}
          onChange={(e) => loadPage(parseInt(e.target.value), pagination.limit)}
          placeholder="Go to page"
        />
        
        <button 
          onClick={() => loadPage(pagination.page + 1, pagination.limit)}
          disabled={pagination.page === pagination.pages}
        >
          Next
        </button>
        
        <button 
          onClick={() => loadPage(pagination.pages, pagination.limit)}
          disabled={pagination.page === pagination.pages}
        >
          Last
        </button>

        {/* Items per page */}
        <select 
          value={pagination.limit}
          onChange={(e) => loadPage(1, parseInt(e.target.value))}
        >
          <option value="50">50 per page</option>
          <option value="100">100 per page</option>
          <option value="250">250 per page</option>
        </select>

        <span>
          Showing {pagination.total_count.toLocaleString()} total items
        </span>
      </div>
    </div>
  )
}

export default InventoryTable
```

**Success Criteria:**
- ✅ Pagination controls visible and working
- ✅ All page navigation buttons functional
- ✅ Items-per-page selector working
- ✅ URL params updating
- ✅ Page loads correctly

---

#### TASK 3.3: Pagination Testing & Performance Validation
**Owner:** QA Lead  
**Duration:** 6 hours  
**Deadline:** Feb 20, 12 PM  
**Prerequisites:** Tasks 3.1, 3.2 complete  
**Deliverables:**
- [ ] 50+ test cases passing
- [ ] Load test results documented
- [ ] Performance acceptable (<200ms)
- [ ] Bug report (if any)

**Test Plan:**

1. **Unit Tests (10 tests):**
   - First page (offset=0, limit=50)
   - Middle page (page 10 of 528)
   - Last page
   - Invalid page (>528)
   - Invalid limit (>250)
   - Sort by different columns
   - Filter + paginate
   - Response structure validation

2. **Integration Tests (15 tests):**
   - End-to-end page load
   - Navigation flow: first → last → first
   - Pagination with different limits: 50, 100, 250
   - All 528 pages load successfully
   - Data consistency across pages (no duplicates)

3. **Performance Tests (10 tests):**
   - Page 1 load time <200ms
   - Page 528 load time <200ms
   - Concurrent requests (10 users, different pages)
   - Memory usage constant (not growing)

4. **UI Tests (15 tests):**
   - Buttons enable/disable correctly
   - Page input field validation
   - Items-per-page dropdown working
   - Error messages on invalid input

**Test Code Example:**
```python
import pytest
from fastapi.testclient import TestClient

def test_pagination_first_page():
    response = client.get("/api/v1/inventory/list?limit=50&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 50
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["total_count"] == 26400

def test_pagination_response_time():
    start = time.time()
    response = client.get("/api/v1/inventory/list?limit=50&offset=0")
    duration = (time.time() - start) * 1000  # ms
    assert duration < 200, f"Response took {duration}ms"

def test_pagination_all_pages():
    # Load all 528 pages, ensure no errors
    for page in range(1, 529):
        offset = (page - 1) * 50
        response = client.get(f"/api/v1/inventory/list?limit=50&offset={offset}")
        assert response.status_code == 200
```

**Load Test:**
```bash
# Apache Bench: 10K requests, 100 concurrent
ab -n 10000 -c 100 http://localhost:8000/api/v1/inventory/list

# Expected output:
# Requests per second: ~500
# Time per request: 200ms
# Failed requests: 0
```

**Success Criteria:**
- ✅ 50+ test cases passing
- ✅ No crashes on any page
- ✅ Response time consistently <200ms
- ✅ Load test: 100 concurrent, 0% error
- ✅ Bug list empty or resolved

---

## PHASE 0 TIMELINE

```
Monday, Feb 17:
  9:00 AM:  Kickoff meeting (all 10 team members)
  10:00 AM: Task 1.1 starts (PostgreSQL setup)
  12:00 PM: Daily standup #1
  4:00 PM:  Daily standup #2
  
Tuesday, Feb 18:
  9:00 AM:  Daily standup
  10:00 AM: Tasks 1.2, 2.1, 2.2 progress check
  12:00 PM: Task 1.1 complete ✅
  2:00 PM:  Task 1.2 complete ✅
  4:00 PM:  Task 1.3 starts (data migration)
  6:00 PM:  Tasks 2.1, 2.2 complete ✅

Wednesday, Feb 19:
  9:00 AM:  Daily standup
  10:00 AM: Task 1.3 complete ✅
  12:00 PM: Tasks 1.4, 3.1 complete ✅
  3:00 PM:  Task 3.2 in progress
  6:00 PM:  Task 3.2 complete ✅

Thursday, Feb 20:
  9:00 AM:  Daily standup
  10:00 AM: Task 3.3 testing starts
  12:00 PM: All tasks complete ✅
  2:00 PM:  Final review & QA sign-off
  3:00 PM:  Gate approval meeting (10 signatures required)
  5:00 PM:  ✅ GATE APPROVED (or re-plan if needed)
```

---

## GATE 1 APPROVAL CHECKLIST (Feb 20, 5 PM)

**10 Required Approvals:**

**Technical Requirements:**
- [ ] **1. PostgreSQL Migration** ✅
  - [ ] All 424K+ records migrated
  - [ ] Data integrity: 100%
  - [ ] Connection stable, 0 errors
  - [ ] Backups automated

- [ ] **2. No Hardcoded URLs** ✅
  - [ ] grep: 0 hardcoded "localhost:8000"
  - [ ] .env.example complete
  - [ ] All endpoints use env variables

- [ ] **3. Pagination Working** ✅
  - [ ] All 26K products paginated
  - [ ] No crashes on any page
  - [ ] Response <200ms
  - [ ] UI navigation working

- [ ] **4. Load Testing** ✅
  - [ ] 100 concurrent users supported
  - [ ] Average response time: <200ms
  - [ ] Error rate: 0%
  - [ ] Sustained for 2+ minutes

- [ ] **5. All 37 Endpoints Operational** ✅
  - [ ] 37/37 endpoints responding
  - [ ] All methods working (GET/POST/PUT/DELETE)
  - [ ] Authentication enabled
  - [ ] CORS headers correct

**Quality Assurance:**
- [ ] **6. Unit Tests Passing** ✅
  - [ ] 50+ test cases passing
  - [ ] 100% pass rate
  - [ ] No critical failures

- [ ] **7. Integration Tests Passing** ✅
  - [ ] End-to-end workflows verified
  - [ ] Data flow verified
  - [ ] All integrations working

- [ ] **8. No Production Blockers** ✅
  - [ ] No known critical bugs
  - [ ] No security vulnerabilities
  - [ ] Documentation complete

**Team Readiness:**
- [ ] **9. Team Trained & Ready** ✅
  - [ ] All team members briefed on Phase 1
  - [ ] Documentation available
  - [ ] Tools and access configured

- [ ] **10. Readiness Score: 5.2/10** ✅
  - [ ] Baseline functionality verified
  - [ ] Ready for Phase 1 (POS system)
  - [ ] Phase 1 team ready to start Feb 24

---

## GATE APPROVAL SIGN-OFF

```
PHASE 0 GATE APPROVAL FORM
Date: Feb 20, 2026
Deadline: 5:00 PM IST

DECISION: [ ] APPROVE → Phase 1 Starts Feb 24
          [ ] CONDITIONAL APPROVE (requires _____)
          [ ] REJECT (reason: _____)

Required Signatures:

Tech Lead: ___________________  Date: _______
Backend Lead: ___________________  Date: _______
Frontend Lead: ___________________  Date: _______
DevOps Engineer: ___________________  Date: _______
QA Lead: ___________________  Date: _______

Witness Signatures:

Product Lead: ___________________  Date: _______
Engineering Manager: ___________________  Date: _______

Comments/Issues:
_________________________________________
_________________________________________

Next Phase: Phase 1 (POS System)
Start Date: Feb 24, 2026
Duration: 2 weeks
Gate Deadline: Mar 6, 2026
```

---

## EXECUTION TIPS

✅ **Communication**
- Daily standups: 12 PM & 4 PM IST
- Slack channel: #phase-0-blockers
- Escalate blockers immediately (no heroics)

✅ **Version Control**
- All code committed to `main` branch
- Feature branches for large changes
- Pull requests reviewed same-day

✅ **Testing**
- Run full test suite before committing
- Test in dev environment first
- Load test before production deployment

✅ **Documentation**
- Update README as you go
- Document all environment variables
- Create runbooks for migration steps

✅ **Contingency**
- PostgreSQL backup created before migration
- Rollback plan documented (revert to SQLite if needed)
- Reserve 2 hours on Feb 20 for final fixes

---

## PHASE 0 SUCCESS INDICATORS

| Indicator | Target | Status |
|-----------|--------|--------|
| PostgreSQL online | 1 Feb 18 | 🟡 In Progress |
| 424K records migrated | 100% | 🟡 In Progress |
| Hardcoded URLs removed | 0 remaining | 🟡 In Progress |
| Pagination implemented | 100% pages load | 🟡 In Progress |
| All 37 endpoints working | 37/37 | 🟡 In Progress |
| Load test: 100 users | <200ms | 🟡 In Progress |
| Tests passing | 100% pass rate | 🟡 In Progress |
| Team trained | 10/10 ready | 🟡 In Progress |
| Documentation complete | 100% | 🟡 In Progress |
| **Gate Approval** | **✅ APPROVED** | 🟡 Pending Feb 20 |

---

**PHASE 0: READY FOR EXECUTION**  
*Start Date: Monday, Feb 17, 2026*  
*Gate Review: Thursday, Feb 20, 2026 @ 5 PM IST*  
*Next Phase: Phase 1 (POS System) - Monday, Feb 24, 2026*
