# Phase 0 Pre-Execution Environment Setup Guide

**Version:** 1.0  
**Date:** February 14-16, 2026  
**Audience:** DevOps Lead, Tech Leads  
**Purpose:** Verify all systems ready before Monday kickoff

---

## 🎯 Objectives

By end of Friday Feb 16, ALL systems must be:
- ✅ Provisioned and tested
- ✅ Credentials configured
- ✅ Backup procedures verified
- ✅ Team access granted
- ✅ Communication channels active

---

## 📋 Pre-Execution Checklist

### DevOps Setup (Friday by 2 PM)

#### PostgreSQL Infrastructure
```bash
# Option A: AWS RDS Setup
- [ ] Create RDS PostgreSQL instance (13.7+)
  - Instance size: db.t3.medium (minimum)
  - Storage: 100GB SSD (minimum)
  - Multi-AZ: YES (production ready)
  - Backup retention: 7 days
  - Parameter group: postgres13
  
- [ ] Security group configured
  - Inbound: Port 5432 from dev team IPs
  - Outbound: All allowed
  
- [ ] Database created
  - Name: enterprise_retail
  - Owner: postgres user
  - Encoding: UTF8
  - Collation: en_US.UTF-8
  
- [ ] Connection tested
  - Host: [your-rds-endpoint]
  - Port: 5432
  - Database: enterprise_retail
  - User: postgres
  - Password: [saved in .env]

# Option B: Docker Local Setup
- [ ] Docker installed (v20+)
- [ ] Docker Compose installed (v2+)
- [ ] PostgreSQL container running
  docker run --name postgres-enterprise \
    -e POSTGRES_DB=enterprise_retail \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_PASSWORD=[password] \
    -p 5432:5432 \
    -d postgres:13-alpine

- [ ] Database initialized
  psql -h localhost -U postgres -d enterprise_retail \
       -c "SELECT version();"
```

**Estimated Time:** 20-30 minutes  
**Success Indicator:** Can connect via psql

#### Environment File (.env)
```bash
# Copy to PHASE_0_IMPLEMENTATION/scripts/.env
- [ ] DATABASE_URL configured
  postgresql://postgres:password@localhost:5432/enterprise_retail

- [ ] TEST_DATABASE_URL configured
  postgresql://postgres:password@localhost:5432/enterprise_retail_test

- [ ] Backend settings
  - ENVIRONMENT=development
  - LOG_LEVEL=DEBUG
  - API_PORT=8000
  - CORS_ORIGINS=http://localhost:3000,http://localhost:5173

- [ ] Migration settings
  - BATCH_SIZE=1000
  - SKIP_VALIDATION=false
  - ROLLBACK_ENABLED=true

- [ ] Saved securely
  - Never commit to git
  - Shared via LastPass or 1Password
  - Backup in secure location
```

**Estimated Time:** 5 minutes  
**Success Indicator:** All variables defined

#### Backup & Rollback Verification
```bash
- [ ] SQLite backup taken
  cp petpooja_retail_db.sqlite3 \
     petpooja_retail_db.sqlite3.backup.$(date +%Y%m%d)

- [ ] Backup verified readable
  sqlite3 petpooja_retail_db.sqlite3.backup.20260214 \
         "SELECT COUNT(*) FROM inventory_items;"

- [ ] Rollback script tested
  bash PHASE_0_IMPLEMENTATION/scripts/rollback.sh --dry-run

- [ ] Recovery procedure documented
  - Database snapshots: AWS or local backup
  - Data restore time: < 15 minutes
  - Verified procedure: In writing
```

**Estimated Time:** 10 minutes  
**Success Indicator:** Can restore from backup

---

### Backend Setup (Friday by 3 PM)

#### Python Environment
```bash
# Workspace: /home/petpooja/Enterprise Retail Intelligence System

- [ ] Python 3.11+ installed
  python --version  # Should be 3.11+

- [ ] Virtual environment created
  python -m venv venv
  source venv/bin/activate

- [ ] Requirements installed
  pip install -r requirements.txt
  # Key packages: fastapi, sqlalchemy, psycopg2-binary, pytest

- [ ] Dependencies verified
  pip list | grep -E "fastapi|sqlalchemy|psycopg2"
  
  Expected output:
  fastapi          0.104.1
  sqlalchemy       2.0.23
  psycopg2-binary  2.9.9
  pytest           7.4.3
```

**Estimated Time:** 10 minutes  
**Success Indicator:** All packages installed

#### Backend Configuration
```bash
- [ ] Backend .env file created
  cat > backend/.env << EOF
  DATABASE_URL=postgresql://user:pass@localhost:5432/enterprise_retail
  ENVIRONMENT=development
  LOG_LEVEL=DEBUG
  API_PORT=8000
  CORS_ORIGINS=http://localhost:3000,http://localhost:5173
  JWT_SECRET_KEY=[generate-new-key]
  EOF

- [ ] Database connection tested
  python -c "
  import sys
  sys.path.insert(0, 'backend')
  from config import settings
  from database import engine
  with engine.connect() as conn:
      result = conn.execute('SELECT 1')
      print('✅ Database connection successful')
  "

- [ ] Backend startup verified
  cd backend
  uvicorn main:app --reload --host 0.0.0.0 --port 8000
  # Should start on http://localhost:8000
  # Hit Ctrl+C to stop
```

**Estimated Time:** 10 minutes  
**Success Indicator:** Backend starts and connects to DB

---

### Frontend Setup (Friday by 4 PM)

#### Node.js Environment
```bash
- [ ] Node.js 18+ installed
  node --version  # Should be 18+
  npm --version   # Should be 9+

- [ ] Project dependencies installed
  cd frontend
  npm install
  # Should take 2-3 minutes

- [ ] Build verified
  npm run build
  # Should complete with 0 errors
```

**Estimated Time:** 5 minutes  
**Success Indicator:** npm install completes

#### Frontend Configuration
```bash
- [ ] .env.local file created
  cat > frontend/.env.local << EOF
  VITE_API_URL=http://localhost:8000
  VITE_LOG_LEVEL=debug
  VITE_ENVIRONMENT=development
  EOF

- [ ] Frontend startup verified
  npm run dev
  # Should start on http://localhost:5173
  # Hit Ctrl+C to stop

- [ ] API connectivity tested
  curl http://localhost:8000/api/health
  # Should return: {"status": "healthy"}
```

**Estimated Time:** 5 minutes  
**Success Indicator:** Frontend dev server starts

---

### Git & Repository (Friday by 5 PM)

#### Repository Status
```bash
- [ ] All changes committed
  git status
  # Should show: "On branch main, nothing to commit, working tree clean"

- [ ] Latest code pulled
  git pull origin main
  # Should show: "Already up to date"

- [ ] Branches updated
  git fetch --all
  git branch -a
```

**Estimated Time:** 2 minutes  
**Success Indicator:** No uncommitted changes

#### GitHub Setup
```bash
- [ ] GitHub milestones created
  # Run commands from .github/PHASE_0_SETUP.md
  gh milestone create "Phase 0: Database & Config" \
    --description "Database migration, pagination, testing"

- [ ] GitHub labels created
  gh label create "phase-0-database" -c FF0000
  gh label create "phase-0-pagination" -c 00FF00
  # (Run all 8 labels from setup guide)

- [ ] GitHub project board created
  gh project create --title "Phase 0: Database Migration" \
    --description "Database setup and data migration tracking"

- [ ] Issues imported to GitHub
  # Run from: PHASE_0_IMPLEMENTATION/github_issues/
  for file in ISSUE_*.md; do
    gh issue create --title "$(head -1 $file)" \
      --body "$(cat $file)" --label phase-0
  done

- [ ] Issues assigned to team members
  gh issue edit 1 --assignee [DevOps-Lead-GitHub-Handle]
  gh issue edit 2 --assignee [Backend-Lead-GitHub-Handle]
  # (Assign all 12 issues)
```

**Estimated Time:** 10 minutes  
**Success Indicator:** 12 issues visible in GitHub

---

### Team Communication (Friday by 6 PM)

#### Slack Setup
```bash
- [ ] #phase-0-execution channel created
  /create #phase-0-execution

- [ ] Channel description set
  "Phase 0 database migration & pagination (Feb 17-20)"

- [ ] Team members invited
  10 team members + executives + stakeholders

- [ ] Pinned messages created
  1. PHASE_0_EXECUTION_READY.md (link)
  2. Daily standup time: 5:00 PM IST
  3. Escalation contacts (with phone numbers)
  4. Contingency procedures

- [ ] Notification preferences set
  - Mentions: Push notifications
  - Channel updates: Normal
  - Time zone: IST
```

**Estimated Time:** 5 minutes  
**Success Indicator:** Team can access and see messages

#### Email Communications
```bash
- [ ] Kickoff meeting invite sent
  - When: Monday Feb 17, 9:00 AM - 10:00 AM IST
  - Where: [Zoom/Teams link]
  - Agenda: 15-min brief + task assignment
  - Calendar link: [Include]

- [ ] Pre-kickoff email sent to team
  Subject: "Phase 0 Kickoff Monday 9 AM - Please Review Materials"
  Content:
  1. Welcome to Phase 0 execution
  2. Link to PHASE_0_EXECUTION_READY.md
  3. Your assigned task from GitHub
  4. Pre-kickoff checklist for your role
  5. Q&A process (Slack #phase-0-execution)
  6. Contingency contact info
```

**Estimated Time:** 5 minutes  
**Success Indicator:** Team receives communications

---

## 🧪 Verification Tests

Run these tests Friday by 5 PM to confirm readiness:

### Database Connectivity Test
```bash
#!/bin/bash
# Test file: scripts/test_connectivity.sh

echo "🧪 Testing Database Connectivity..."

# Test PostgreSQL connection
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT VERSION();" > /dev/null 2>&1
if [ $? -eq 0 ]; then
  echo "✅ PostgreSQL connection successful"
else
  echo "❌ PostgreSQL connection failed"
  exit 1
fi

# Test table creation ability
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "CREATE TABLE test_table (id SERIAL PRIMARY KEY); DROP TABLE test_table;" > /dev/null 2>&1
if [ $? -eq 0 ]; then
  echo "✅ Table creation/deletion works"
else
  echo "❌ Table operations failed"
  exit 1
fi

echo "✅ All connectivity tests passed"
```

**Run:** `bash scripts/test_connectivity.sh`  
**Expected:** All checks pass with ✅

### Application Startup Test
```bash
#!/bin/bash
# Test file: scripts/test_startup.sh

echo "🧪 Testing Application Startup..."

# Start backend (background)
cd backend
uvicorn main:app --reload --port 8000 > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
sleep 2

# Test backend health
curl -s http://localhost:8000/api/health | grep -q "healthy"
if [ $? -eq 0 ]; then
  echo "✅ Backend health check passed"
else
  echo "❌ Backend health check failed"
  kill $BACKEND_PID
  exit 1
fi

# Start frontend (background)
cd ../frontend
npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
sleep 3

# Test frontend startup
curl -s http://localhost:5173 | grep -q "<!DOCTYPE"
if [ $? -eq 0 ]; then
  echo "✅ Frontend startup successful"
else
  echo "❌ Frontend startup failed"
  kill $BACKEND_PID $FRONTEND_PID
  exit 1
fi

# Cleanup
kill $BACKEND_PID $FRONTEND_PID
echo "✅ All startup tests passed"
```

**Run:** `bash scripts/test_startup.sh`  
**Expected:** Both tests pass with ✅

### Migration Dry-Run Test
```bash
#!/bin/bash
# Test file: scripts/test_migration_dryrun.sh

echo "🧪 Testing Migration Dry-Run..."

# Run migration in dry-run mode
python PHASE_0_IMPLEMENTATION/scripts/migrate_sqlite_to_postgresql.py \
  --source petpooja_retail_db.sqlite3 \
  --destination $DATABASE_URL \
  --dry-run \
  --batch-size 1000

if [ $? -eq 0 ]; then
  echo "✅ Migration dry-run completed successfully"
  echo "✅ Check output for record counts and estimated time"
else
  echo "❌ Migration dry-run failed"
  exit 1
fi
```

**Run:** `bash scripts/test_migration_dryrun.sh`  
**Expected:** Dry-run completes with record counts

---

## 🚨 Pre-Execution Issues Resolution

### If PostgreSQL Connection Fails

**Problem:** `psql: could not connect to server`

**Solutions:**
1. Verify PostgreSQL is running
   ```bash
   sudo systemctl status postgresql  # Linux
   brew services list | grep postgres  # macOS
   ```

2. Check connection string
   ```bash
   # Should be: postgresql://user:password@host:port/database
   echo $DATABASE_URL
   ```

3. Verify firewall/security groups
   ```bash
   nc -zv localhost 5432  # Linux/macOS
   Test-NetConnection -ComputerName localhost -Port 5432  # Windows
   ```

4. Check RDS security group (AWS)
   - Inbound rule for 5432 from your IP
   - Outbound rule allowing all

### If Backend Won't Start

**Problem:** `Address already in use: ('0.0.0.0', 8000)`

**Solutions:**
1. Kill existing process
   ```bash
   lsof -ti:8000 | xargs kill -9
   ```

2. Change port in .env
   ```bash
   API_PORT=8001
   ```

3. Verify no firewalls blocking port
   ```bash
   sudo ufw allow 8000  # Linux
   ```

### If Frontend Build Fails

**Problem:** `npm ERR! code ERESOLVE`

**Solutions:**
1. Clear npm cache
   ```bash
   npm cache clean --force
   ```

2. Delete node_modules and reinstall
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

3. Use Node 18 LTS
   ```bash
   nvm use 18  # If using nvm
   ```

### If Migration Dry-Run Fails

**Problem:** `ModuleNotFoundError: No module named 'psycopg2'`

**Solutions:**
1. Install Python dependencies
   ```bash
   pip install -r requirements.txt
   ```

2. For macOS with M1/M2
   ```bash
   pip install psycopg2-binary
   ```

---

## 📱 Team Pre-Execution Duties

### DevOps Lead (Friday by 5 PM)
- [ ] PostgreSQL infrastructure ready (AWS/Docker)
- [ ] .env file configured and shared securely
- [ ] Backup/rollback procedures tested
- [ ] All connectivity tests passing
- [ ] GitHub setup commands executed
- [ ] Slack channel #phase-0-execution created
- [ ] Contingency contacts documented

### Backend Lead (Friday by 4 PM)
- [ ] Python environment set up (3.11+)
- [ ] Dependencies installed via pip
- [ ] Backend code tested for import errors
- [ ] Database connection verified from Python
- [ ] Backend startup test passed
- [ ] GitHub issues reviewed (8 backend issues)
- [ ] Tasks understood and time estimated

### Frontend Lead (Friday by 4 PM)
- [ ] Node.js 18+ installed
- [ ] npm dependencies installed
- [ ] Build process verified (npm run build succeeds)
- [ ] Frontend startup tested
- [ ] Backend API connectivity verified
- [ ] GitHub issues reviewed (2 frontend issues)
- [ ] Tasks understood and time estimated

### QA Lead (Friday by 3 PM)
- [ ] Test environment configured
- [ ] Apache Bench installed and tested
- [ ] pytest framework installed
- [ ] Test scripts reviewed and understood
- [ ] Load testing baseline established
- [ ] GitHub issues reviewed (4 QA issues)
- [ ] Testing strategy confirmed with team

### Product Lead (Friday by 2 PM)
- [ ] Phase 0 timeline confirmed
- [ ] Gate approval criteria reviewed (10 questions)
- [ ] Success metrics understood
- [ ] Escalation procedures documented
- [ ] Thursday 3 PM gate approval meeting scheduled
- [ ] Executive stakeholders briefed

---

## ✅ Sign-Off Checklist

**For Each Team Lead (Friday by 6 PM):**
```
Date: ________________  
Team Lead Name: ________________  
Role: ________________  

Pre-Execution Verification:
- [ ] My environment is fully configured
- [ ] All tests for my role are passing
- [ ] I understand my Phase 0 tasks
- [ ] I've reviewed my GitHub issues
- [ ] I'm confident in Monday execution
- [ ] I have contact info for escalations
- [ ] I'm aware of contingency plans

Signature: ____________________
```

**For DevOps Lead (Special Items):**
```
Database Infrastructure Status:
- [ ] PostgreSQL online and verified
- [ ] Backup procedures tested
- [ ] Rollback procedures ready
- [ ] Performance baseline established
- [ ] All team members have access

Estimated Migration Time: _____ minutes
Estimated Schema Creation Time: _____ minutes
Ready for Monday: [ ] YES [ ] NO
```

**For Product Lead (Final Approval):**
```
Phase 0 Readiness Assessment:
- [ ] All teams confirmed ready
- [ ] Infrastructure verified
- [ ] Contingencies in place
- [ ] Communication channels active
- [ ] Stakeholders informed

Final Go/No-Go for Monday Execution: [ ] GO [ ] NO-GO
Comments: _________________________________
```

---

## 🎯 Final Pre-Execution Meeting (Friday 5 PM)

**Duration:** 30 minutes  
**Attendees:** All 5 team leads + Product Manager  
**Agenda:**

1. **Database Status** (5 min)
   - DevOps reports infrastructure ready
   - Connectivity tests all passing
   - Backup/rollback procedures verified

2. **Team Readiness** (15 min)
   - Backend Lead: Environment, dependencies, tests ready
   - Frontend Lead: Environment, build, connectivity ready
   - QA Lead: Test environment, tools, procedures ready
   - Each lead confirms 3 items ready

3. **GitHub Setup** (5 min)
   - All milestones created
   - All labels created
   - All 12 issues assigned to team members
   - Project board operational

4. **Communication Verification** (3 min)
   - Slack channel active
   - Kickoff email sent
   - Escalation contacts confirmed

5. **Go/No-Go Decision** (2 min)
   - Product Lead makes final call
   - If GO: Team dismissed, ready for Monday
   - If NO-GO: Issues documented, rescheduling

---

## 📞 Emergency Contacts

**Setup Friday Evening (Keep This List Handy):**

| Role | Name | Phone | Email | Backup |
|------|------|-------|-------|--------|
| Product Lead | [Name] | [Phone] | [Email] | [Backup Name] |
| DevOps Lead | [Name] | [Phone] | [Email] | [Backup Name] |
| Backend Lead | [Name] | [Phone] | [Email] | [Backup Name] |
| Frontend Lead | [Name] | [Phone] | [Email] | [Backup Name] |
| QA Lead | [Name] | [Phone] | [Email] | [Backup Name] |

**Copy this template and fill in details Friday by 4 PM.**

---

## 🚀 Monday Morning Start (9:00 AM)

**If all pre-execution checks pass, you're ready:**

1. **9:00 AM:** Kickoff meeting starts
2. **9:15 AM:** Team assigned to GitHub issues
3. **9:30 AM:** Task execution begins
4. **5:00 PM:** First standup + daily update

**If any checks failed:**
- Issue documented with root cause
- Fix time estimated
- Rescheduling planned
- Stakeholders notified

---

## 📋 Summary

**By End of Friday Feb 16:**

✅ All systems provisioned  
✅ All connectivity verified  
✅ All teams confirmed ready  
✅ All communications active  
✅ All GitHub setup complete  
✅ All contingencies documented  
✅ Final GO decision made  

**Monday 9 AM: Phase 0 Execution Begins** 🚀

---

**Document:** Phase 0 Pre-Execution Environment Setup  
**Version:** 1.0  
**Status:** Ready to Execute  
**Last Updated:** February 14, 2026
