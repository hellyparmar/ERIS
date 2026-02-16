# GITHUB PROJECT SETUP & TASK MANAGEMENT GUIDE
**Purpose:** Organize 18-week execution in GitHub Projects  
**Audience:** Tech Lead, Engineering Team  
**Duration:** 30 minutes to set up, 2 minutes per day to maintain

---

## OVERVIEW

GitHub Projects will track all 100+ tasks across 18 weeks (Phase 0-7). This guide shows exactly how to set it up for maximum team visibility and coordination.

---

## STEP 1: CREATE GITHUB PROJECT

### 1.1 Create Project Board
```
GitHub Repository: hellyparmar/R-DIOS
Go to: Projects (tab) → New Project
Name: "R-DIOS v3.0 - 18 Week Implementation"
Description: "4 days Phase 0 + 14 weeks Phases 1-7 → 8.5/10 production ready"
Template: Table (better for detailed task tracking than Kanban)
Visibility: Public (or Private if preferred)
```

### 1.2 Create Views
```
Create 5 Views in the project:

1. "Overview" (default table view - ALL TASKS)
   Columns: Title, Status, Assignee, Phase, Due Date, Priority
   Sort by: Due Date (ascending)
   Filter: None (show all)
   
2. "By Phase" (grouped view)
   Group by: Phase
   Show: 0, 1, 2, 3, 4, 5, 6, 7
   This lets Tech Lead see Phase progress at a glance
   
3. "By Person" (grouped view)
   Group by: Assignee
   Show: Each team member
   This lets each person see their tasks
   
4. "Blockers" (filtered view)
   Filter: Status = "Blocked"
   This highlights impediments
   
5. "This Week" (filtered view)
   Filter: Due Date = This Week
   This shows urgent tasks
```

---

## STEP 2: DEFINE TASK FIELDS

### 2.1 Status Field
```
Options (Kanban-style):
  🔴 Not Started (backlog, waiting to start)
  🟡 In Progress (actively being worked)
  🟢 Review (waiting for code review)
  ✅ Done (complete + tested)
  🚫 Blocked (waiting on external dependency)

Default: Not Started
```

### 2.2 Phase Field
```
Options:
  0 - Critical Blockers
  1 - POS System
  2 - Inventory
  3 - Invoicing
  4 - Analytics
  5 - Forecasting
  6 - Localization
  7 - Mobile App

Default: 0
```

### 2.3 Assignee Field
```
Select: Team member
Options:
  - Tech Lead
  - Backend Lead
  - Backend Engineer 2 (optional)
  - Frontend Lead
  - Frontend Engineer 2 (optional)
  - DevOps Engineer
  - QA Lead
  - QA Engineer 2 (optional)
```

### 2.4 Priority Field
```
Options (high to low):
  🔴 Critical (blocks other tasks, production issue)
  🟠 High (important, should do soon)
  🟡 Medium (normal priority)
  🔵 Low (nice to have, can defer)

Default: Medium
```

### 2.5 Effort Field
```
Options (estimated hours):
  < 1 hour
  1-2 hours
  2-4 hours
  4-8 hours
  8-16 hours
  16+ hours

Default: 2-4 hours
```

### 2.6 Story Points (Optional)
```
Options: 1, 2, 3, 5, 8, 13, 21
Use: Fibonacci scale for estimation
Default: 3
```

### 2.7 Documentation Link (Optional)
```
Type: URL
Example: "https://github.com/hellyparmar/R-DIOS/blob/main/PHASE_0_TECHNICAL_GUIDE.md#task-11"
Use: Links task to specification document
```

---

## STEP 3: CREATE PHASE 0 TASKS (Example - Complete)

### Create Issue for Each Task (Use Template Below)

**PHASE 0: CRITICAL BLOCKERS (4 days)**

#### Task 1.1: SQLite Audit
```
Title: "Task 1.1: Audit current SQLite database"
Description: 
  Understand current database state before migration
  
  Deliverable: CURRENT_DATABASE_STATE.md with:
  - All 10 table names + row counts
  - AUTOINCREMENT usage inventory
  - Boolean column storage approach
  - Timestamp default handling
  - TEXT vs VARCHAR usage
  
  See: PHASE_0_TECHNICAL_GUIDE.md § Task 1.1

Phase: 0
Assignee: Backend Lead
Priority: 🔴 Critical (blocks 1.2)
Effort: 2-4 hours
Due Date: 2026-02-17 (Monday noon)
Status: Not Started
Documentation Link: PHASE_0_TECHNICAL_GUIDE.md#task-11

Acceptance Criteria:
  [ ] Database audit script run
  [ ] All 10 tables documented
  [ ] Row counts verified
  [ ] SQLite-specific issues identified
  [ ] CURRENT_DATABASE_STATE.md created
  [ ] Tech Lead reviewed (15 min)
```

#### Task 1.2: Database Connection Update
```
Title: "Task 1.2: Update database.py for PostgreSQL + SQLite fallback"
Description:
  Modify api/db/database.py to support:
  - Environment variable DATABASE_URL
  - PostgreSQL connection pooling
  - Fallback to SQLite if PostgreSQL unavailable
  - Connection logging
  
  See: PHASE_0_TECHNICAL_GUIDE.md § Task 1.2

Phase: 0
Assignee: Backend Lead
Priority: 🔴 Critical
Effort: 2-4 hours
Due Date: 2026-02-17 (Monday 1:30 PM)
Status: Not Started
Depends On: Task 1.1
Documentation Link: PHASE_0_TECHNICAL_GUIDE.md#task-12

Acceptance Criteria:
  [ ] DATABASE_URL env var supported
  [ ] PostgreSQL connection works
  [ ] SQLite fallback works
  [ ] requirements.txt updated (psycopg2-binary)
  [ ] Logging shows db type
  [ ] Code committed to git
```

#### Task 2.1: Frontend URL Audit
```
Title: "Task 2.1: Audit all hardcoded localhost:8000 URLs"
Description:
  Inventory all frontend files with hardcoded API URLs
  
  Run: grep -r "http://localhost:8000" src/
  
  Deliverable: HARDCODED_URLS_INVENTORY.md with:
  - File name
  - Line number
  - Current URL
  - Service file name
  
  See: PHASE_0_TECHNICAL_GUIDE.md § Task 2.1

Phase: 0
Assignee: Frontend Lead
Priority: 🔴 Critical
Effort: 1-2 hours
Due Date: 2026-02-17 (Monday 10:30 AM)
Status: Not Started
Documentation Link: PHASE_0_TECHNICAL_GUIDE.md#task-21

Acceptance Criteria:
  [ ] grep command run
  [ ] All instances found (expect 15-25)
  [ ] Inventory spreadsheet created
  [ ] Effort estimate confirmed (1-2 hours to fix)
```

#### Task 2.2-2.4: .env Files + URL Replacement
```
Title: "Task 2.2-2.4: Create .env files and replace hardcoded URLs"
Description:
  1. Create .env, .env.staging, .env.production, .env.example
  2. Create src/config.js with getApiUrl() helper
  3. Update all service files to use config
  4. Test builds for all 3 environments
  
  See: PHASE_0_TECHNICAL_GUIDE.md § Tasks 2.2-2.4

Phase: 0
Assignee: Frontend Lead
Priority: 🔴 Critical
Effort: 4-8 hours
Due Date: 2026-02-18 (Tuesday 3:30 PM)
Status: Not Started
Depends On: Task 2.1
Documentation Link: PHASE_0_TECHNICAL_GUIDE.md#task-22

Acceptance Criteria:
  [ ] .env files created
  [ ] config.js created
  [ ] All service files updated
  [ ] grep -r "localhost" returns 0 results
  [ ] Dev build works (localhost)
  [ ] Staging build works (staging URL)
  [ ] Prod build works (prod URL)
```

#### Task 3.1-3.4: Crash Patches
```
Title: "Task 3.1-3.4: Apply crash patches (pagination, memory, errors, CORS)"
Description:
  Fix 4 crash issues:
  1. Pagination: Remove LIMIT 5000 band-aid
  2. Memory: Optimize queries, implement connection pooling
  3. Error handling: Add try/except, rollback on errors
  4. CORS: Verify headers, test from different origins
  
  See: PHASE_0_TECHNICAL_GUIDE.md § Tasks 3.1-3.4

Phase: 0
Assignee: Backend Lead
Priority: 🔴 Critical
Effort: 2-4 hours
Due Date: 2026-02-19 (Wednesday 4:00 PM)
Status: Not Started
Documentation Link: PHASE_0_TECHNICAL_GUIDE.md#task-31

Acceptance Criteria:
  [ ] Pagination tested with 10K products
  [ ] Memory usage stable
  [ ] All write operations have error handling
  [ ] CORS headers verified
```

#### Task 4: Load Testing
```
Title: "Task 4: Comprehensive load testing (unit + integration + load)"
Description:
  Run full test suite:
  - Unit tests: 100% pass rate
  - Integration tests: All workflows
  - Load test: 100 concurrent users, <200ms, 0% error
  
  See: PHASE_0_TECHNICAL_GUIDE.md § Task 4

Phase: 0
Assignee: QA Lead
Priority: 🔴 Critical
Effort: 3-4 hours
Due Date: 2026-02-20 (Thursday 4:30 PM)
Status: Not Started
Depends On: Tasks 1.x, 2.x, 3.x
Documentation Link: PHASE_0_TECHNICAL_GUIDE.md#task-4

Acceptance Criteria:
  [ ] pytest result: 100% pass
  [ ] Load test: 100 users, <200ms avg
  [ ] Load test: 0% error rate
  [ ] PERFORMANCE_BASELINE.md created
```

#### Task 5: Documentation
```
Title: "Task 5: Complete Phase 0 documentation"
Description:
  Create:
  - PHASE_0_COMPLETION_REPORT.md
  - Update README.md (PostgreSQL setup)
  - PHASE_0_ROLLBACK_PLAN.md
  
  See: PHASE_0_TECHNICAL_GUIDE.md § Task 5

Phase: 0
Assignee: Tech Lead
Priority: 🟠 High
Effort: 2 hours
Due Date: 2026-02-20 (Thursday 2:00 PM)
Status: Not Started
Depends On: Tasks 1-4
Documentation Link: PHASE_0_TECHNICAL_GUIDE.md#task-5

Acceptance Criteria:
  [ ] Completion report written
  [ ] README updated
  [ ] Rollback plan documented
```

#### GATE: Phase 0 Approval
```
Title: "GATE: Phase 0 Gate Approval"
Description:
  Verify all 10 gate criteria pass:
  [ ] PostgreSQL operational
  [ ] All 37 endpoints pass (100%)
  [ ] Load test: 100 users, <200ms, 0% error
  [ ] No hardcoded URLs
  [ ] Memory/crashes fixed
  [ ] Documentation complete
  [ ] Rollback plan ready
  [ ] Team trained
  [ ] Phase 1 spec reviewed
  [ ] Timeline confirmed
  
  Get signatures:
  [ ] Tech Lead ___________
  [ ] Backend Lead ___________
  [ ] Frontend Lead ___________
  [ ] DevOps ___________
  [ ] QA Lead ___________

Phase: 0
Assignee: Tech Lead
Priority: 🔴 Critical
Effort: 1 hour
Due Date: 2026-02-20 (Thursday 2:00 PM)
Status: Not Started
Depends On: Task 5

DECISION:
  [ ] APPROVED → Start Phase 1 Monday
  [ ] REJECTED → Fix blockers, re-test, re-gate
```

---

## STEP 4: CREATE PHASE 1 TASKS

Use similar template for Phase 1 tasks. Example:

#### Task 1: Design POS Page
```
Title: "Phase 1 Task 1: Design POS page (mockup + spec)"
Description: See PHASE_1_POS_SPECIFICATION.md § Frontend Design
Phase: 1
Assignee: Frontend Lead
Priority: 🔴 Critical
Effort: 4-8 hours
Due Date: 2026-02-24 (Monday - Week 2)
Status: Not Started
Depends On: GATE Phase 0
Documentation Link: PHASE_1_POS_SPECIFICATION.md
Acceptance Criteria:
  [ ] POS page mockup created (Figma/Adobe XD)
  [ ] Components documented (product search, cart, payment)
  [ ] Reviewed with Backend Lead
```

#### Task 2: Implement POS API
```
Title: "Phase 1 Task 2: Implement POST /api/v1/sales/create"
Description: See PHASE_1_POS_SPECIFICATION.md § Backend API
Phase: 1
Assignee: Backend Lead
Priority: 🔴 Critical
Effort: 4-8 hours
Due Date: 2026-02-24 (Monday - Week 2)
Status: Not Started
Depends On: GATE Phase 0
Documentation Link: PHASE_1_POS_SPECIFICATION.md
Acceptance Criteria:
  [ ] Endpoint accepts barcode scan
  [ ] Inventory deducted
  [ ] Transaction logged
  [ ] <2 second response time
  [ ] Tests pass (100%)
```

---

## STEP 5: AUTOMATED WORKFLOWS (Optional)

### 5.1 Stale Issue Detection
```
GitHub Actions: Auto-close issues not updated in 2 weeks
This ensures active task tracking (prevents abandoned tasks)
```

### 5.2 Milestone-Based Progress
```
Create Milestones:
  - Phase 0 (Due: 2026-02-20)
  - Phase 1 (Due: 2026-03-06)
  - Phase 2 (Due: 2026-03-20)
  - ... Phase 3-7
  - Production Go-Live (Due: 2026-05-09)

Link each task to its Milestone
GitHub automatically shows progress (X/Y tasks complete)
```

### 5.3 Automated Status Updates
```
GitHub Actions can auto-update issues on commits:
  If PR contains "Fixes #123", auto-close #123
  If commit mentions "In progress #456", auto-update status
```

---

## STEP 6: DAILY USAGE WORKFLOW

### Tech Lead (Daily)
```
9:00 AM:  Open GitHub Project → "This Week" view
          Check for blocked tasks (red flags)
          If any blocked: escalate immediately
          
4:00 PM:  Check "Overview" sorted by Phase
          Verify progress matches schedule
          Update any task statuses as needed
```

### Individual Engineer (Daily)
```
Start of day:
  1. Open GitHub Project → "By Person" view
  2. Filter by your name
  3. See your tasks (sorted by Due Date)
  4. Move "In Progress" task from "Not Started" to "In Progress"
  
During day:
  1. Work on task
  2. If stuck: Change status to "Blocked", add comment explaining blocker
  
End of day:
  1. Update task status (In Progress, Review, or Done)
  2. Add comment summarizing progress
```

### During Standup (4:00 PM)
```
Use GitHub Project "Overview" to reference:
  1. "What did you complete today?" (point to "Done" items)
  2. "What are you working on tomorrow?" (point to "In Progress" items)
  3. "Any blockers?" (point to "Blocked" items)
```

---

## STEP 7: GITHUB PROJECT SETTINGS

### 7.1 Access Control
```
Team: hellyparmar/R-DIOS-dev (create if not exists)
Members:
  - Tech Lead (Admin)
  - Backend Lead (Write)
  - Frontend Lead (Write)
  - DevOps (Write)
  - QA Lead (Write)
  - All Engineers (Write)
  - Product Lead (Read)

Public vs Private:
  Recommendation: Public (so investors can see progress)
  But keep detailed technical notes in private issues if needed
```

### 7.2 Templates
```
Create Issue Templates in .github/ISSUE_TEMPLATE/:

1. task-template.md (for Phase tasks)
2. bug-report.md (for production bugs)
3. feature-request.md (for future features)

This ensures consistent issue format
```

### 7.3 Branch Protection Rules
```
Main branch: Require 1 code review before merge
This ensures quality (no direct commits to main)

PR template: Require:
  [ ] Related issue #___
  [ ] Tests pass
  [ ] Documentation updated
```

---

## STEP 8: REPORTING (For Stakeholders)

### 8.1 Weekly Progress Report (Auto-Generate)
```
From GitHub Project, calculate:
  - Total tasks: 100+
  - Completed: X
  - In Progress: Y
  - Blocked: Z
  - On Track: YES/NO

Template for weekly email:
  "Phase 0: 8/10 tasks complete (80%)
   Phase 1: 2/20 tasks complete (10%, on track)
   Blockers: 1 (database performance - investigating)"
```

### 8.2 Burndown Chart (Manual)
```
Track weekly:
  - Week 1: Total tasks remaining (90)
  - Week 2: Total tasks remaining (75)
  - Week 3: Total tasks remaining (60)
  - ...
  
Create spreadsheet or chart showing:
  X-axis: Week number
  Y-axis: Tasks remaining
  Target line: Linear decrease (90 → 0 over 18 weeks)
```

### 8.3 Velocity Tracking
```
Calculate: Tasks completed per week
  Week 1: 8 tasks
  Week 2: 12 tasks
  Week 3: 10 tasks
  Average: 10 tasks/week
  
Estimate: At 10 tasks/week, Phase 0 completes in 1 week, Phase 1 in 2 weeks, etc.
Use: Adjust timeline if velocity drops
```

---

## QUICK START (30 Minutes to Set Up)

```
Step 1: Create GitHub Project (5 min)
  Go to hellyparmar/R-DIOS → Projects → New
  Name: "R-DIOS v3.0 - 18 Week Implementation"
  
Step 2: Create Fields (5 min)
  Add: Status, Phase, Assignee, Priority, Effort, Due Date
  
Step 3: Create Views (5 min)
  Add: Overview, By Phase, By Person, Blockers, This Week
  
Step 4: Add Phase 0 Tasks (10 min)
  Copy template above, create 10+ issues
  Assign to team members
  Set due dates
  
Step 5: Test Project (5 min)
  Open each view
  Verify visibility
  Share with team

TOTAL TIME: 30 minutes
```

---

## EXAMPLE: FULL PHASE 0 TIMELINE IN GITHUB

```
MONDAY (Feb 17):
  Task 1.1 (Database Audit) - Due 11:00 AM
  Task 2.1 (URL Audit) - Due 10:30 AM
  Task 1.2 (DB Connection) - Due 1:30 PM
  Task 2.2-2.4 (URL fixes) - Due end of day
  Daily standup: 4:00 PM
  Status: Report progress

TUESDAY (Feb 18):
  Task 1.3 (Alembic) - Due 10:30 AM
  Task 1.4 (Data Migration) - Due 12:00 PM
  Task 2.2-2.4 (URL fixes) - Continue if needed
  Daily standup: 4:00 PM

WEDNESDAY (Feb 19):
  Task 3.1-3.4 (Crash patches) - Due 4:00 PM
  Daily standup: 4:00 PM

THURSDAY (Feb 20):
  Task 4 (Load testing) - Due 4:30 PM
  Task 5 (Documentation) - Due 2:00 PM
  GATE REVIEW: 2:00 PM - 4:00 PM
  DECISION: Approved or Rejected

FRIDAY (Feb 21):
  If approved: Phase 1 planning + kickoff
  If rejected: Fix blockers + re-test + re-gate
  Daily standup: 4:00 PM
```

---

## SUCCESS CHECKLIST

```
Before your team starts:
  [ ] GitHub Project created
  [ ] 5 views set up (Overview, By Phase, By Person, Blockers, This Week)
  [ ] 7 custom fields added (Status, Phase, Assignee, Priority, Effort, Due Date, Docs Link)
  [ ] Phase 0 issues created (10+ tasks)
  [ ] Milestones created (Phase 0-7 + Go-Live)
  [ ] Team added with correct access levels
  [ ] Issue templates created (task, bug, feature)
  [ ] Branch protection rules enabled
  [ ] Tech Lead knows how to triage blockers
  [ ] Daily standup calendar set (4:00 PM)
  
After first week:
  [ ] Team comfortable with GitHub Project
  [ ] Daily updates happening
  [ ] No "forgotten" tasks
  [ ] Blockers identified and escalated
  [ ] Phase 0 gate criteria tracked
```

---

*GitHub Project Setup Guide - R-DIOS v3.0*  
*14 February 2026*
