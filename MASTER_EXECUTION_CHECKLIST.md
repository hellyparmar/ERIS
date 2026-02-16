# R-DIOS v3.0 — MASTER EXECUTION CHECKLIST
**Date:** 14 February 2026  
**Status:** Ready for Execution  
**Responsibility:** R-DIOS Development Team

---

## 📚 DOCUMENT ROADMAP

**Your implementation sequence:**

1. **START HERE:** [AUDIT_SUMMARY_AND_NEXT_STEPS.md](AUDIT_SUMMARY_AND_NEXT_STEPS.md) — 10 min read
2. **IMPLEMENTATION:** [PHASE_0_TECHNICAL_GUIDE.md](PHASE_0_TECHNICAL_GUIDE.md) — Task-by-task breakdown
3. **NEXT PHASE:** [PHASE_1_POS_SPECIFICATION.md](PHASE_1_POS_SPECIFICATION.md) — POS design docs
4. **TRACKING:** This document — Execution checklist

---

## PHASE 0 EXECUTION CHECKLIST

### Pre-Execution (Before Starting)

```
SETUP (Day 0):
[ ] All team members have access to repository
[ ] PostgreSQL 15 installed locally (or Docker ready)
[ ] Development environment working (npm/python/pip)
[ ] Communication channel set up (Slack, Teams, etc.)
[ ] Daily standup scheduled (15 min, 4:00 PM daily)
[ ] Task tracking board created (Jira/GitHub Projects)

KICKOFF MEETING (30 min):
[ ] Tech Lead reviews Phase 0 overview
[ ] Backend Lead owns Task 1 (PostgreSQL)
[ ] Frontend Lead owns Task 2 (URL removal)
[ ] DevOps Engineer owns Task 1.5 (Docker setup)
[ ] QA Lead owns Task 4 (Testing)
[ ] Timeline confirmed (4 days, Mon-Thu)
[ ] Dependencies and blockers identified
```

---

### DAY 1 — MONDAY (Audit & Setup)

#### Task 1.1: SQLite Audit
```
OWNER: Backend Lead
EFFORT: 2 hours
DUE: 11:00 AM

[ ] Run database audit script
[ ] Document all 10 tables (names, row counts)
[ ] Identify SQLite-specific issues:
    [ ] AUTOINCREMENT usage
    [ ] Boolean column storage
    [ ] Timestamp default handling
    [ ] TEXT vs VARCHAR usage
[ ] Create CURRENT_DATABASE_STATE.md
[ ] Review with Tech Lead (15 min)
[ ] ✅ SIGNOFF: Backend Lead
```

**Deliverable:** `docs/CURRENT_DATABASE_STATE.md`

---

#### Task 1.2: Database Connection Update
```
OWNER: Backend Lead + DevOps
EFFORT: 2 hours
DUE: 1:30 PM

[ ] Open api/db/database.py
[ ] Add environment variable support (DATABASE_URL)
[ ] Add PostgreSQL + SQLite fallback logic
[ ] Add connection pooling config
[ ] Test connection with both databases:
    [ ] SQLite connection works
    [ ] PostgreSQL connection string parsing works
[ ] Add logging for database type
[ ] Update requirements.txt (add psycopg2-binary)
[ ] Commit changes with message "feat: add PostgreSQL support to database layer"
[ ] ✅ SIGNOFF: Backend Lead
```

**Deliverable:** Updated `api/db/database.py`, `requirements.txt`

---

#### Task 2.1: Frontend URL Audit
```
OWNER: Frontend Lead
EFFORT: 1 hour
DUE: 10:30 AM

[ ] Run grep command: grep -r "http://localhost:8000" src/
[ ] Count total instances (expect 15-25)
[ ] Create HARDCODED_URLS_INVENTORY.md listing all files
[ ] Estimate effort to replace (expect ~1-2 hours)
[ ] ✅ SIGNOFF: Frontend Lead
```

**Deliverable:** `docs/HARDCODED_URLS_INVENTORY.md`

---

#### Task 2.2: Environment Files Setup
```
OWNER: Frontend Lead
EFFORT: 1.5 hours
DUE: 12:00 PM

[ ] Create .env file with VITE_API_URL=http://localhost:8000
[ ] Create .env.staging with staging API URL
[ ] Create .env.production with production API URL
[ ] Create .env.example (commit to git)
[ ] Update .gitignore to exclude .env files
[ ] Test that Vite loads env variables: import.meta.env.VITE_API_URL
[ ] ✅ SIGNOFF: Frontend Lead
```

**Deliverable:** `.env`, `.env.staging`, `.env.production`, `.env.example`

---

#### Task 3.1: Pagination Fixes (Parallel)
```
OWNER: Backend Lead
EFFORT: 1.5 hours
DUE: 4:00 PM

[ ] Identify all endpoints with LIMIT hardcoding
[ ] Fix inventory/list endpoint:
    [ ] Add page + per_page query parameters
    [ ] Remove LIMIT 5000 band-aid
    [ ] Return pagination metadata (total, pages)
[ ] Fix alerts/list endpoint similarly
[ ] Test locally with pagination
[ ] ✅ SIGNOFF: Backend Lead
```

**Deliverable:** Updated endpoint handlers with pagination

---

### EOD DAY 1 CHECKLIST
```
✅ Database audit complete
✅ Database connection layer updated
✅ .env files created
✅ Pagination fixes started
✅ Frontend URL inventory documented

🎯 Status: ON TRACK
⏱️ Next: URL replacement + Migration creation
```

---

### DAY 2 — TUESDAY (Migration & Replacement)

#### Task 1.3: Alembic Migration
```
OWNER: Backend Lead
EFFORT: 1.5 hours
DUE: 10:30 AM

[ ] Check if Alembic initialized (if not, alembic init alembic)
[ ] Update alembic/env.py to use DATABASE_URL env var
[ ] Run: alembic revision --autogenerate -m "SQLite to PostgreSQL migration"
[ ] Review generated migration file for correctness
[ ] Check for:
    [ ] All 10 tables created
    [ ] Foreign keys defined
    [ ] Indexes created
    [ ] No SQLite-specific syntax
[ ] Test migration on fresh PostgreSQL locally:
    [ ] Create fresh PostgreSQL database
    [ ] Run: alembic upgrade head
    [ ] Verify schema matches
[ ] ✅ SIGNOFF: Backend Lead
```

**Deliverable:** `alembic/versions/[timestamp]_sqlite_to_postgresql.py`

---

#### Task 1.4: Data Migration Script
```
OWNER: Backend Lead
EFFORT: 2 hours
DUE: 12:00 PM

[ ] Create scripts/migrate_sqlite_to_postgres.py
[ ] Implement connection logic:
    [ ] SQLite connection
    [ ] PostgreSQL connection
    [ ] Error handling + logging
[ ] Implement table-by-table migration:
    [ ] Respect foreign key order
    [ ] Handle large batches (1000K+ records)
    [ ] Progress reporting
[ ] Implement verification:
    [ ] Row count checks
    [ ] Data sampling validation
[ ] Test migration locally:
    [ ] Backup current SQLite database
    [ ] Run migration script
    [ ] Verify row counts match
    [ ] Spot-check data integrity
[ ] Document rollback procedure
[ ] ✅ SIGNOFF: Backend Lead
```

**Deliverable:** `scripts/migrate_sqlite_to_postgres.py`

---

#### Task 2.3: Replace Hardcoded URLs
```
OWNER: Frontend Lead
EFFORT: 2 hours
DUE: 3:30 PM

[ ] Create src/config.js with getApiUrl() helper
[ ] Update each service file in src/services/:
    [ ] inventory.js
    [ ] dashboard.js
    [ ] invoices.js
    [ ] pos.js
    [ ] ... (all service files)
[ ] Replace pattern:
    FROM: fetch('http://localhost:8000/api/...')
    TO: fetch(getApiUrl('/api/...'))
[ ] Test imports work correctly
[ ] Verify no hardcoded URLs remain:
    grep -r "localhost:8000" src/
[ ] ✅ SIGNOFF: Frontend Lead
```

**Deliverable:** Updated all service files + `src/config.js`

---

#### Task 2.4: Build Environment Testing
```
OWNER: Frontend Lead
EFFORT: 1 hour
DUE: 4:30 PM

[ ] Build for localhost:
    VITE_API_URL=http://localhost:8000 npm run build
[ ] Build for staging:
    VITE_API_URL=https://staging-api.r-dios.com npm run build
[ ] Build for production:
    VITE_API_URL=https://api.r-dios.com npm run build
[ ] Verify no localhost URLs in dist/:
    grep -r "localhost" dist/
[ ] Document build process in README
[ ] ✅ SIGNOFF: Frontend Lead
```

**Deliverable:** Verified build process for all environments

---

#### Task 3.2-3.4: Remaining Crash Fixes
```
OWNER: Backend Lead
EFFORT: 2 hours
DUE: 4:00 PM

[ ] Memory leak fixes:
    [ ] Optimize queries (select only needed columns)
    [ ] Implement connection pooling
    [ ] Test memory usage under load
[ ] Error handling:
    [ ] Add try/except to all write operations
    [ ] Implement db.rollback() on errors
    [ ] Ensure no raw exceptions to frontend
[ ] CORS verification:
    [ ] Test CORS headers present
    [ ] Test from different origins
[ ] ✅ SIGNOFF: Backend Lead
```

**Deliverable:** Updated router files with improved error handling

---

### EOD DAY 2 CHECKLIST
```
✅ Alembic migration created + tested
✅ Data migration script created + tested
✅ All hardcoded URLs replaced
✅ Build tests pass for all environments
✅ Crash fixes applied

🎯 Status: ON TRACK
⏱️ Next: Docker setup + Endpoint testing
```

---

### DAY 3 — WEDNESDAY (Database Migration & Testing)

#### Task 1.5: PostgreSQL in docker-compose.yml
```
OWNER: DevOps Engineer
EFFORT: 1 hour
DUE: 10:00 AM

[ ] Add PostgreSQL 15 service to docker-compose.yml
[ ] Configure:
    [ ] Image: postgres:15-alpine
    [ ] Ports: 5432
    [ ] Environment variables
    [ ] Volume for persistence
    [ ] Healthcheck
[ ] Add backend service environment:
    [ ] DATABASE_URL pointing to postgres service
[ ] Test docker-compose setup:
    docker-compose build
    docker-compose up -d postgres
    [ ] Verify PostgreSQL running: docker ps
    [ ] Verify connection: psql -U rdios -d rdios_db
[ ] ✅ SIGNOFF: DevOps Engineer
```

**Deliverable:** Updated `docker-compose.yml`

---

#### Task 1.6: Data Migration Execution
```
OWNER: Backend Lead + DevOps
EFFORT: 2 hours
DUE: 12:00 PM

[ ] Backup current SQLite database:
    cp api/database/petpooja_retail_db.sqlite3 api/database/petpooja_retail_db.sqlite3.backup
[ ] Start PostgreSQL:
    docker-compose up -d postgres
    [ ] Wait for healthcheck to pass (10-15 sec)
[ ] Run Alembic migration:
    export DATABASE_URL=postgresql://rdios:rdios@localhost:5432/rdios_db
    alembic upgrade head
    [ ] Verify all migrations applied successfully
[ ] Run data migration script:
    export DATABASE_URL=postgresql://rdios:rdios@localhost:5432/rdios_db
    python scripts/migrate_sqlite_to_postgres.py
    [ ] Verify row counts match
    [ ] Check data integrity spot-checks
[ ] ✅ SIGNOFF: Backend Lead + DevOps
```

**Deliverable:** Data successfully migrated to PostgreSQL

---

#### Task 4: Comprehensive Testing
```
OWNER: QA Lead + Team
EFFORT: 3 hours
DUE: 4:30 PM

UNIT TESTS:
[ ] Run: pytest tests/ -v
[ ] Verify: 100% pass rate (37+ tests)
[ ] Coverage: ≥80%

INTEGRATION TESTS:
[ ] Test POS transaction end-to-end
[ ] Test inventory deduction after sale
[ ] Test invoice creation
[ ] Test dashboard data fetch
[ ] Test authentication workflows

LOAD TESTING:
[ ] Install apache2-utils: apt-get install apache2-utils
[ ] Run load test: ab -n 1000 -c 100 http://localhost:8000/api/v1/inventory/list
[ ] Verify:
    [ ] Average response time: <200ms
    [ ] Error rate: 0%
    [ ] Requests per second: >100

PERFORMANCE BASELINE:
[ ] Document all response times
[ ] Compare with pre-migration baseline
[ ] Create PERFORMANCE_BASELINE.md

[ ] ✅ SIGNOFF: QA Lead
```

**Deliverable:** `PERFORMANCE_BASELINE.md`, test results

---

### EOD DAY 3 CHECKLIST
```
✅ PostgreSQL deployed in docker-compose
✅ Data migration completed
✅ All 37 endpoints tested (100% pass)
✅ Load test passed (100 concurrent users, 0% error)
✅ Performance baseline documented

🎯 Status: ON TRACK
⏱️ Next: Documentation + Gate approval
```

---

### DAY 4 — THURSDAY (Documentation & Gate)

#### Task 5: Documentation
```
OWNER: Tech Lead
EFFORT: 2 hours
DUE: 2:00 PM

[ ] Create PHASE_0_COMPLETION_REPORT.md:
    [ ] Summary of changes
    [ ] Files modified (list all)
    [ ] Test results (paste pytest output)
    [ ] Load test results
    [ ] Performance improvements
[ ] Update RDIOS_AGENT_PROMPT.md
[ ] Update main README.md:
    [ ] PostgreSQL setup instructions
    [ ] Environment variables reference
    [ ] Build for different environments
[ ] Create PHASE_0_ROLLBACK_PLAN.md:
    [ ] Rollback procedure if critical issues found
    [ ] Data restore from SQLite backup
    [ ] Timeline for rollback
[ ] ✅ SIGNOFF: Tech Lead
```

**Deliverable:** Complete documentation package

---

#### Gate Approval (2:00 PM - 4:00 PM)
```
GATE CRITERIA VERIFICATION:

[ ] PostgreSQL replaces SQLite
[ ] All 37 API endpoints pass tests (100%)
[ ] Load test: 100 concurrent users, <200ms avg, 0% error
[ ] VITE_API_URL environment variable works everywhere
[ ] No localhost hardcodes remain in codebase
[ ] Memory/crashes fixed
[ ] No exception traces to UI
[ ] CORS + JWT + rate-limiting verified
[ ] Documentation updated
[ ] Rollback plan documented

APPROVALS REQUIRED:
[ ] Tech Lead ........................... _______________  ___________
[ ] Backend Lead ........................ _______________  ___________
[ ] Frontend Lead ....................... _______________  ___________
[ ] DevOps Engineer ..................... _______________  ___________
[ ] QA Lead ............................ _______________  ___________

GATE STATUS: ______ APPROVED / ______ REJECTED

If REJECTED:
[ ] Document issues found
[ ] Create action items for fixes
[ ] Schedule re-approval after fixes
[ ] Blockers: ___________________________________________________________________
```

---

### EOD DAY 4 CHECKLIST & SIGN-OFF
```
✅ Documentation complete
✅ Gate criteria verified (all 10 items)
✅ Team approvals received
✅ PHASE 0 COMPLETE ✨

🎉 READY FOR PHASE 1 (POS SYSTEM)
📅 Next Milestone: Phase 1 Kickoff (Monday, Week 2)
```

---

## RISK MANAGEMENT

### Potential Blockers & Mitigation

```
RISK 1: Data Loss During Migration
├─ Impact: HIGH (catastrophic if data lost)
├─ Probability: LOW (if procedure followed)
└─ Mitigation:
    [ ] Backup SQLite before migration
    [ ] Verify row counts before/after
    [ ] Sample data validation (spot-checks)
    [ ] Keep rollback backup for 1 week

RISK 2: PostgreSQL Connection Issues
├─ Impact: MEDIUM (blocks all development)
├─ Probability: MEDIUM (new setup)
└─ Mitigation:
    [ ] Test PostgreSQL locally first
    [ ] DBA review connection string
    [ ] Have alternative setup ready
    [ ] Document connection troubleshooting

RISK 3: API Endpoint Regression
├─ Impact: HIGH (breaks existing functionality)
├─ Probability: LOW (with proper testing)
└─ Mitigation:
    [ ] Run full test suite
    [ ] Load test with baseline comparison
    [ ] Have SQLite fallback available
    [ ] Rollback plan ready

RISK 4: Build Process Breaks
├─ Impact: MEDIUM (can't deploy)
├─ Probability: MEDIUM (env var issues)
└─ Mitigation:
    [ ] Test builds with all env configs
    [ ] CI/CD pipeline verification
    [ ] Document build commands
```

---

## COMMUNICATION PLAN

### Daily Standup (4:00 PM - 4:15 PM)
```
Format:
1. What did you complete today? (2 min)
2. What are you working on tomorrow? (2 min)
3. Any blockers? (2 min)
4. Status summary (Quick → On Track / At Risk / Blocked)

Attendees: All 5 leads
Channel: Slack / Teams / In-person
```

### Daily Status Update (End of Day)
```
To: Tech Lead, Product Manager
Subject: Phase 0 Daily Status - [DATE]

✅ COMPLETED TODAY:
- Task 1.1: Database audit
- Task 2.1: URL inventory
- ...

⏳ IN PROGRESS:
- Task 1.2: Database connection update
- ...

🔴 BLOCKERS:
- None

📊 PROGRESS: [████░░░░░░] 40% (Days 1/4 complete)
```

### Weekly Status (Friday)
```
Executive Summary:
- Phase 0 Progress: [% complete]
- On Track: YES / NO
- Risks: [List any new risks]
- Next Week: [High-level plan]

Metrics:
- Tests passing: 37/37
- Load test: 100 users, <200ms
- Performance: Baseline established
```

---

## SUCCESS METRICS

### Phase 0 = SUCCESS when:

```
✅ TECHNICAL:
  [ ] PostgreSQL fully operational
  [ ] All 37 endpoints passing (100%)
  [ ] Load test: 100 concurrent, <200ms, 0% error
  [ ] No hardcoded localhost URLs
  [ ] Memory usage stable
  [ ] Zero data loss
  
✅ OPERATIONAL:
  [ ] Docker-compose works for everyone
  [ ] Rollback procedure tested
  [ ] Documentation complete
  [ ] Team trained on new setup
  
✅ MANAGEMENT:
  [ ] Gate approval signed off
  [ ] Phase 1 backlog ready
  [ ] No critical issues remaining
  [ ] Timeline met (4 days)
```

### Phase 0 = FAILURE if:

```
❌ Any of these are true:
  [ ] PostgreSQL fails to deploy
  [ ] <5 endpoints passing
  [ ] Load test shows >10% error rate
  [ ] Data loss during migration
  [ ] Hardcoded URLs still exist
  [ ] Build breaks for any environment
  [ ] Team unable to work with new setup
```

---

## TEAM ROLES & RESPONSIBILITIES

```
TECH LEAD (Overall Owner)
├─ Coordinates all tasks
├─ Runs daily standups
├─ Makes decision calls on blockers
├─ Gate approval authority
└─ Success = All 10 gate criteria met + team signed off

BACKEND LEAD (Tasks 1.1-1.6, 3.1-3.4)
├─ Database migration (primary owner)
├─ API endpoint testing
├─ Performance optimization
└─ Success = 37/37 endpoints passing

FRONTEND LEAD (Tasks 2.1-2.4)
├─ Remove hardcoded URLs
├─ Environment configuration
├─ Build testing (3 environments)
└─ Success = All builds pass, no localhost URLs

DEVOPS ENGINEER (Task 1.5)
├─ PostgreSQL setup
├─ Docker configuration
├─ Infrastructure testing
└─ Success = docker-compose works for all

QA LEAD (Task 4)
├─ Test planning + execution
├─ Load testing
├─ Baseline reporting
└─ Success = 100% pass rate + <200ms avg
```

---

## NEXT MILESTONE: PHASE 1 (POS SYSTEM)

```
🎯 GATE APPROVAL = Phase 0 Complete
📅 PHASE 1 KICKOFF = Monday, Week 2
🎬 PHASE 1 TIMELINE = 2 weeks (10 business days)

PHASE 1 DELIVERABLES:
├─ Complete POS page (frontend)
├─ Sale creation endpoint (backend)
├─ Payment processing (Razorpay/UPI)
├─ Thermal receipt printing (ESC/POS)
├─ WhatsApp receipt delivery
├─ Offline transaction queue
└─ Integration tests + go-live readiness

SUCCESS = Cashier can complete 50+ transactions/day
```

---

## PRINT/BOOKMARK THIS

**Keep this checklist visible during execution:**
- Print it out and post on team wall
- Share link in Slack pinned messages
- Check off items daily
- Use for standup reference

---

*Master Execution Checklist - Phase 0  
R-DIOS v3.0 Development Team  
14 February 2026*
