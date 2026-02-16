# R-DIOS v3.0 — PHASE 0 ACTION PLAN
**Start Date:** 14 February 2026  
**Target Completion:** End of Week 0  
**Gate:** All Phase 0 tasks MUST complete before production deployment

---

## OVERVIEW

Phase 0 is a prerequisite gate. The system is **NOT production-ready** until all tasks below are complete. These are not enhancements — they are **blocking defects**.

```
🔴 BLOCKER #1: SQLite cannot handle concurrent writes (fatal for production)
🔴 BLOCKER #2: API_BASE hardcoded as localhost (breaks in production)
🔴 BLOCKER #3: Crash fixes not applied (unstable under load)
```

---

## TASK BREAKDOWN

### TASK 1: SQLite → PostgreSQL Migration

**Owner:** Backend Lead  
**Timeline:** 2-3 days  
**Blocker:** YES 🔴

#### Subtasks:

##### 1.1 Audit Current SQLite Setup
- [ ] List all tables in `api/db/models.py`
- [ ] Verify all models for SQLite-specific issues:
  - [ ] AUTOINCREMENT → SERIAL/IDENTITY
  - [ ] Boolean columns using correct type
  - [ ] created_at/updated_at have server defaults
  - [ ] No TEXT where VARCHAR appropriate
- [ ] Document current database size + record counts per table

**File:** `api/db/models.py`

##### 1.2 Update Database Connection Layer
- [ ] Update `api/db/database.py`:
  ```python
  # USE THIS PATTERN:
  DATABASE_URL = os.getenv(
      "DATABASE_URL",
      "sqlite:///./petpooja_retail_db.sqlite3"  # Fallback for local dev only
  )
  
  # For PostgreSQL production:
  # DATABASE_URL = "postgresql://user:pass@postgres:5432/rdios_db"
  ```
- [ ] Add `psycopg2-binary` to `requirements.txt`
- [ ] Test connection string parsing for both SQLite and PostgreSQL

**File:** `api/db/database.py`, `requirements.txt`

##### 1.3 Create Alembic Migration
- [ ] Run: `alembic revision --autogenerate -m "migrate sqlite to postgresql"`
- [ ] Review generated migration file for correctness
- [ ] Test migration on fresh PostgreSQL instance
- [ ] Document rollback procedure

**File:** `alembic/versions/*.py`

##### 1.4 Create Data Migration Script
- [ ] Write script to read from SQLite (current)
- [ ] Write to PostgreSQL (target)
- [ ] Verify data integrity (row counts, checksums, sample rows)
- [ ] Document any data transformations needed

**Files:** `scripts/migrate_sqlite_to_postgres.py`

##### 1.5 Update docker-compose.yml
- [ ] Add PostgreSQL 15 service:
  ```yaml
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: rdios
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: rdios_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
  ```
- [ ] Add environment variables section for DATABASE_URL
- [ ] Test docker-compose up with PostgreSQL

**File:** `docker-compose.yml`

##### 1.6 Test All 37 API Endpoints
- [ ] Run full pytest suite against PostgreSQL
- [ ] Verify response times (should match or improve vs SQLite)
- [ ] Check for any SQLite-specific query failures
- [ ] Document any performance differences

**Files:** `tests/test_*.py`

---

### TASK 2: Remove Hardcoded localhost API URLs

**Owner:** Frontend Lead  
**Timeline:** 1 day  
**Blocker:** YES 🔴

#### Subtasks:

##### 2.1 Audit Frontend Service Files
- [ ] Search for all instances of `http://localhost:8000` in `src/services/`
- [ ] Create inventory of files to change
- [ ] Document all API calls found

**Command:**
```bash
grep -r "http://localhost:8000" src/
```

##### 2.2 Update .env Template
- [ ] Create `.env.example` with:
  ```
  VITE_API_URL=http://localhost:8000
  ```
- [ ] Create `.env.production` with:
  ```
  VITE_API_URL=https://api.r-dios.com
  ```
- [ ] Document in README how to configure for different environments

**Files:** `.env.example`, `.env.production`, `README.md`

##### 2.3 Replace All Hardcoded URLs
- [ ] Pattern for EVERY service file:
  ```javascript
  // BEFORE (WRONG):
  const response = await fetch('http://localhost:8000/api/v1/inventory');
  
  // AFTER (CORRECT):
  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const response = await fetch(`${API_BASE}/api/v1/inventory`);
  ```
- [ ] Create reusable `src/config.js`:
  ```javascript
  export const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  ```
- [ ] Update all service files to import from config.js

**Files:** All `src/services/*.js`

##### 2.4 Test in Different Environments
- [ ] Build locally: `npm run build` (with VITE_API_URL=http://localhost:8000)
- [ ] Build for staging: `VITE_API_URL=https://staging-api.r-dios.com npm run build`
- [ ] Build for production: `VITE_API_URL=https://api.r-dios.com npm run build`
- [ ] Verify each build connects to correct API

---

### TASK 3: Apply Crash Patches & Stability Fixes

**Owner:** Backend + QA  
**Timeline:** 1 day  
**Blocker:** YES 🔴

#### Subtasks:

##### 3.1 Apply Pagination Fixes
- [ ] Inventory list endpoint: Add `page` + `per_page` params (default 50, max 200)
- [ ] Remove LIMIT 5000 band-aid (replace with proper pagination)
- [ ] Alerts list endpoint: Add cursor-based pagination
- [ ] Test with 100K+ records to ensure memory doesn't spike

**Files:** `api/routers/inventory.py`, `api/routers/alerts.py`, `api/services/*.py`

##### 3.2 Fix Memory Leaks
- [ ] Review all list endpoints for `SELECT *` → specify only needed columns
- [ ] Add connection pooling configuration
- [ ] Test memory usage under load (1000 concurrent connections)
- [ ] Document findings in performance report

**Files:** `api/db/database.py`, `api/routers/*.py`

##### 3.3 Apply Error Handling Fixes
- [ ] Add try/except with db.rollback() to ALL write operations
- [ ] Verify no raw exception stack traces leak to frontend
- [ ] Test with invalid inputs (missing fields, type mismatches)
- [ ] Verify all errors return user-friendly messages

**Files:** All `api/routers/*.py`, `api/services/*.py`

##### 3.4 Fix CORS Configuration
- [ ] Verify CORS headers correctly set in `main.py`
- [ ] Test cross-origin requests from frontend
- [ ] Ensure credentials passed correctly in requests

**File:** `api/main.py`

---

### TASK 4: Comprehensive Testing

**Owner:** QA Lead  
**Timeline:** 1 day  
**Blocker:** YES 🔴

#### Subtasks:

##### 4.1 Unit Tests
- [ ] Run pytest for all 37 endpoints: `pytest tests/ -v`
- [ ] Verify 100% pass rate
- [ ] Check coverage (target 80%+)

##### 4.2 Integration Tests
- [ ] Test end-to-end: frontend → API → PostgreSQL → response
- [ ] Test 5 critical workflows:
  1. POS transaction creation (end-to-end)
  2. Inventory update
  3. Invoice creation + PDF generation
  4. Customer lookup + Khata (credit) tracking
  5. Dashboard data fetch (real-time)

##### 4.3 Load Testing
- [ ] Simulate 100 concurrent users for 10 minutes
- [ ] Measure:
  - Average response time (target < 200ms)
  - P95 response time (target < 500ms)
  - Error rate (target 0%)
  - Database connection pool utilization
- [ ] Document results in performance report

##### 4.4 Security Testing
- [ ] Verify JWT auth on all protected endpoints
- [ ] Test invalid token rejection
- [ ] Verify rate limiting active

---

### TASK 5: Documentation

**Owner:** Tech Lead  
**Timeline:** 0.5 days  
**Blocker:** NO (but needed for handoff)

#### Subtasks:

##### 5.1 Create Phase 0 Completion Report
- [ ] Document all changes made
- [ ] List all files changed with reasons
- [ ] Include test results summary
- [ ] Include performance baseline metrics

**File:** `PHASE_0_COMPLETION_REPORT.md`

##### 5.2 Update Developer Documentation
- [ ] Update `RDIOS_AGENT_PROMPT.md` with Phase 0 completion status
- [ ] Update deployment guide with PostgreSQL instructions
- [ ] Document environment variables required

**Files:** `RDIOS_AGENT_PROMPT.md`, `DEPLOYMENT.md`

##### 5.3 Create Rollback Plan
- [ ] Document how to revert PostgreSQL if critical issues found
- [ ] Include data restore procedures

**File:** `PHASE_0_ROLLBACK_PLAN.md`

---

## GATE CRITERIA: Phase 0 Complete ✅

The system is ready to move to Phase 1 ONLY when ALL of the following are true:

```
✅ PostgreSQL successfully replaces SQLite
✅ All 37 API endpoints pass tests (100% pass rate)
✅ Localhost URLs removed from all frontend services
✅ VITE_API_URL environment variable works correctly
✅ Load test: 100 concurrent users, 0% error rate, <200ms avg response
✅ All crash/memory issues fixed
✅ No raw exception traces leak to frontend
✅ CORS headers working correctly
✅ JWT authentication verified
✅ Rate limiting active
✅ Comprehensive documentation updated
✅ Rollback plan documented
```

**Gate Approval Required From:** Tech Lead, QA Lead, DevOps Lead

---

## TIMELINE SUMMARY

```
DAY 1 (Mon):  Task 1.1-1.2 (SQLite audit + DB connection update)
DAY 1 (Mon):  Task 2.1-2.2 (Frontend audit + .env setup)
              
DAY 2 (Tue):  Task 1.3-1.4 (Alembic migration + data migration)
DAY 2 (Tue):  Task 2.3-2.4 (Replace all localhost URLs + test)
DAY 2 (Tue):  Task 3.1-3.4 (Apply crash patches)

DAY 3 (Wed):  Task 1.5-1.6 (PostgreSQL in docker-compose + endpoint tests)
DAY 3 (Wed):  Task 4 (Comprehensive testing)
DAY 3 (Wed):  Task 5 (Documentation)

DAY 4 (Thu):  GATE APPROVAL + Sign-off
```

**Total Effort:** ~4 person-days  
**Critical Path:** SQLite migration (longest task, 2-3 days)

---

## RISK MITIGATION

| RISK | MITIGATION |
|------|-----------|
| Data loss during migration | Create backup of SQLite before migration. Verify row counts before/after. Test on staging first. |
| PostgreSQL connection issues | Test locally with docker-compose first. Document connection string format. Have DBA review. |
| API response time regression | Run load tests before → after migration. Optimize queries if needed. Have performance baseline. |
| Frontend breaks with new env var | Test build process with all possible VITE_API_URL values. Verify localhost still works locally. |
| Rollback needed mid-production | Have rollback plan documented. Keep SQLite backup. Test rollback procedure before deploying. |

---

## SUCCESS METRICS

**Phase 0 Success = System Ready for Phase 1**

- [x] Zero production blockers remaining
- [x] System can handle 100+ concurrent users (PostgreSQL)
- [x] Environment-specific API URLs work correctly
- [x] All 37 endpoints tested and passing
- [x] Memory/crash issues fixed
- [x] Ready for POS Phase 1 development

---

*Gate Status: WAITING FOR PHASE 0 TASKS TO BEGIN*
