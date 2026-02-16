# DEPENDENCIES & RISKS MATRIX
**Purpose:** Help Product Lead / Tech Lead manage 14-week execution  
**Audience:** Tech Lead, Product Lead, Executive

---

## CRITICAL PATH ANALYSIS

### The Critical Path (Determines Overall Timeline)

```
Phase 0 (4d) → Phase 1 (2w) → Phase 2 (2w) → Phase 3 (2w) 
→ Phase 4 (2w) → Phase 5 (1.5w) → Phase 6 (1.5w) → Phase 7 (2w)

TOTAL: 18 weeks (if sequential)
ACTUAL: 14 weeks (with parallelization)

KEY INSIGHT: Phases 2+ can run in parallel IF:
  - Phase 1 API is stable (no breaking changes)
  - Database schema finalized (Phase 0)
  - Frontend architecture defined (Phase 1 design)
```

### Parallelization Opportunities

```
WEEK 2-3 (Phase 1 running):
  - Phase 1 Frontend (FE1) + Backend (BE1) working together
  - Phase 2 planning: BE2 designs inventory API
  - Phase 3 planning: Design invoicing schema
  - Phase 4 planning: Data warehouse design
  
WEEK 4-5 (Phase 1 complete, Phase 2 running):
  - Phase 2 Frontend (FE1) + Backend (BE2) running
  - Phase 3 can START: BE1 + FE2 (invoice UI)
  - Phase 4 planning: Analytics dashboard mockups
  
WEEK 6-7 (Phases 2-3 running):
  - Phase 3 running: Invoicing features
  - Phase 4 can START: BE1 building analytics endpoints
  - Phase 5 planning: ML model research
  
RESULT: 2 weeks saved through parallelization!
```

---

## DEPENDENCY MATRIX

### Hard Dependencies (Must Complete Before)

```
PHASE 1 depends on:
  ✓ Phase 0 Gate Approval (PostgreSQL, URLs, stability)
  ✓ Database schema: sales, sale_items, inventory tables defined
  ✓ Authentication: JWT working (from Phase 0)
  ✓ Backend API scaffold ready

PHASE 2 depends on:
  ✓ Phase 1 Database schema (inventory table exists)
  ✓ Phase 1 POS complete (sales integration working)
  ✓ Backend API: POST /sales endpoint stable
  
PHASE 3 depends on:
  ✓ Phase 2 Inventory API (GET /inventory/{id} for invoice items)
  ✓ Phase 1 Sales data (POS sales as invoice source)
  ✓ Database: sales.invoice_id column added

PHASE 4 depends on:
  ✓ Phase 1-3 Data (sales, inventory, invoices complete)
  ✓ Database: Data warehouse schema (star schema)
  ✓ Analytics queries designed

PHASE 5 depends on:
  ✓ Phase 4 Data (6 months historical sales data minimum)
  ✓ Feature engineering (product attributes, seasonality)
  ✓ ML infrastructure (Python, scikit-learn, models)

PHASE 6 depends on:
  ✓ Phase 5 Complete (stable features for translation)
  ✓ UI finalized (no more layout changes in Phase 6)
  ✓ Translation team onboarded

PHASE 7 depends on:
  ✓ Phases 1-6 Complete (all features working)
  ✓ Mobile backend API stable
  ✓ App architecture decisions made (React Native chosen)
```

### Soft Dependencies (Better If Complete, But Can Work Around)

```
Phase 2 is BETTER with:
  - Phase 1 testing complete (can learn from their test patterns)
  - Frontend framework decided (FE1 patterns established)
  
Phase 3 is BETTER with:
  - Phase 2 pagination working (invoices need pagination too)
  - Third-party payment APIs selected (Razorpay, etc.)
  
Phase 4 is BETTER with:
  - Analytics database optimizations done (materialized views)
  - Business metrics defined (KPIs that matter to retailers)
  
Phase 5 is BETTER with:
  - Phase 4 dashboards live (can validate forecast accuracy visually)
  - Feedback from Phase 1-4 rollout (understand pain points)
```

---

## INTEGRATION POINTS (Where Phases Connect)

### Database Integration Points

```
PHASE 1 → 2:
  sales table (Phase 1) → inventory deduction (Phase 2)
  Dependency: sales.product_id + sales.quantity must exist
  
PHASE 2 → 3:
  inventory table (Phase 2) + sales table (Phase 1) → invoice items (Phase 3)
  Dependency: Products have prices, inventory has location_id
  
PHASE 3 → 4:
  invoices table (Phase 3) → analytics aggregations (Phase 4)
  Dependency: invoice_id linked to sales
  
PHASE 1-4 → 5:
  Historical data (Phases 1-4) → ML training data (Phase 5)
  Dependency: 6 months of clean data available
  
ALL → 6:
  UI strings from all phases (1-5) → Translation strings (Phase 6)
  Dependency: No more UI text changes after Phase 5
```

### API Integration Points

```
POS API (Phase 1) ← Used by:
  - Inventory (Phase 2) - deducts stock from sales
  - Invoicing (Phase 3) - converts sales to invoices
  - Analytics (Phase 4) - aggregates sales metrics
  - Forecasting (Phase 5) - trains on sales history
  - Mobile (Phase 7) - displays sales history
  
Inventory API (Phase 2) ← Used by:
  - POS (Phase 1) - checks stock availability
  - Invoicing (Phase 3) - validates inventory for invoice
  - Analytics (Phase 4) - inventory turnover metrics
  - Mobile (Phase 7) - shows stock levels
  
Invoicing API (Phase 3) ← Used by:
  - Analytics (Phase 4) - invoice metrics, GST tracking
  - Mobile (Phase 7) - view invoices
  
Analytics API (Phase 4) ← Used by:
  - Dashboard (all phases)
  - Mobile (Phase 7) - view reports
  - Forecasting (Phase 5) - input for ML models
```

---

## RISK REGISTER

### 🔴 CRITICAL RISKS (Impact: CATASTROPHIC, Probability: MEDIUM)

#### Risk 1.1: Phase 0 Gate Rejection
```
Description: PostgreSQL migration fails, readiness stays <5.0
Probability: MEDIUM (30%) if Phase 0 not executed properly
Impact: CATASTROPHIC - entire roadmap delayed 4+ weeks
Timeline Impact: +4 weeks delay = miss go-live by 1 month

Mitigation:
  [ ] Phase 0 requires 5 approvers (all must sign off)
  [ ] Pre-phase-0 checklist (prerequisites verified)
  [ ] PostgreSQL tested locally BEFORE Phase 0 starts
  [ ] Rollback procedure tested
  
Contingency:
  IF gate fails:
    → Stay on SQLite longer (not ideal)
    → OR migrate to PostgreSQL with extended Phase 0
    → OR reduce Phase 1 scope, push features to Phase 2
```

#### Risk 1.2: Data Loss During Phase 0 Migration
```
Description: SQLite → PostgreSQL migration loses transaction data
Probability: LOW (10%) if migration procedure followed
Impact: CATASTROPHIC - 6 months of data lost, reputation damage
Timeline Impact: +3 weeks (to recover from backup + re-test)

Mitigation:
  [ ] Backup SQLite before ANY migration step
  [ ] Test migration on non-production copy FIRST
  [ ] Verify row counts match (SELECT COUNT(*) for each table)
  [ ] Spot-check data (sample 100 rows for accuracy)
  [ ] Keep SQLite backup for 2+ weeks
  
Contingency:
  IF migration fails:
    → Restore from backup
    → Investigate root cause
    → Create detailed migration manual
    → Retry with 2nd engineer verifying each step
```

#### Risk 1.3: Performance Collapses at Scale
```
Description: System works with 10 users but crashes at 100+ concurrent
Probability: MEDIUM (25%) - common in retail systems
Impact: CATASTROPHIC - can't support 1000+ retailers
Timeline Impact: +6 weeks to redesign, retest, redeploy

Examples:
  - Inventory pagination returns 26K items (no pagination limit)
  - Dashboard queries full 12-month dataset on every load
  - Real-time alerts trigger for every user simultaneously
  
Mitigation:
  [ ] Load testing at EVERY phase (not just Phase 0)
  [ ] Phase 1: Test 500+ transactions/day
  [ ] Phase 2: Test 10K products, pagination
  [ ] Phase 3: Test 1000+ invoices
  [ ] Phase 4: Test 100+ concurrent dashboard users
  [ ] Database indexing reviewed before each phase
  [ ] Caching strategy (Redis) implemented early (Phase 1)
  
Contingency:
  IF performance degraded:
    → Identify bottleneck (database, API, frontend)
    → Optimize or redesign (may take 2+ weeks)
    → Delay go-live 2-4 weeks
```

---

### 🟠 HIGH RISKS (Impact: SEVERE, Probability: MEDIUM-HIGH)

#### Risk 2.1: Scope Creep (Feature Bloat)
```
Description: "Just one more feature" extends timeline by weeks
Probability: HIGH (50%) - common in startups
Impact: SEVERE - miss go-live, team burnout

Examples:
  - "Can we add WhatsApp ordering?" (Phase 8, not Phase 1)
  - "Retailer wants custom reports" (Phase 4+, not Phase 3)
  - "We need iOS app NOW" (Phase 7, not Phase 1)
  
Mitigation:
  [ ] Feature freeze after Phase 0 approved
  [ ] Backlog discipline: No feature changes without Product Lead + Tech Lead sign-off
  [ ] Weekly scope review (is this Phase 1? Phase 2? or Phase 8?)
  [ ] Features added to roadmap only if scheduled phase not yet started
  [ ] If feature request comes mid-phase, automatically goes to Phase 8+
  
Contingency:
  IF scope creep detected:
    → Document feature + timeline impact
    → Schedule for Phase 8 or next release
    → Communicate delay to stakeholder
```

#### Risk 2.2: Key Person Dependency (Bus Factor = 1)
```
Description: If Backend Lead quits during Phase 3-5, invoicing system stalls
Probability: MEDIUM (20% per person per quarter)
Impact: SEVERE - 2+ week delay, knowledge loss

Mitigation:
  [ ] Knowledge sharing: Code reviews, pair programming, documentation
  [ ] On-the-job training: Each phase, 2nd engineer shadows primary
  [ ] Documentation: Architecture, API specs, database schema documented
  [ ] Code quality: Tests cover critical paths (not just features)
  
Contingency:
  IF key person leaves:
    → Secondary engineer takes over (with support from Tech Lead)
    → 1-week knowledge transfer + onboarding
    → Pair programming for 1-2 weeks minimum
    → Delay estimate: +1-2 weeks, but manageable with good docs
```

#### Risk 2.3: Third-Party API Failures
```
Description: Razorpay API down, WhatsApp API broken, Twilio outage
Probability: MEDIUM (15%) - APIs have occasional outages
Impact: SEVERE - payments don't process, receipts don't send

Examples:
  - Razorpay: 4-hour outage (happened Jan 2024)
  - WhatsApp: API rate limiting (500 msg/day limit)
  - Twilio: Regional SMS failures
  
Mitigation:
  [ ] Phase 1: Fallback payment methods (Cash, Check, Split payment)
  [ ] Phase 1: Graceful error handling when API down
  [ ] Phase 1: Retry logic with exponential backoff
  [ ] Phase 3: Email receipts if WhatsApp fails
  [ ] Phase 3: Queue receipts when API down, send when recovered
  [ ] Monitoring: Alert when API response time >2 seconds
  
Contingency:
  IF API down:
    → Trigger fallback immediately
    → Queue messages for retry when API recovers
    → Notify user of delay
    → Manual sending option (admin portal)
    → Post-mortem: Switch to backup API provider for next release
```

#### Risk 2.4: Team Burnout (Crunch Mode)
```
Description: 2 backend engineers can't handle 14-week sprint
Probability: HIGH (40%) - common in agile retail projects
Impact: SEVERE - quality degrades, bugs spike, team leaves

Reasons:
  - 14 weeks of non-stop coding
  - No time for refactoring (technical debt builds)
  - Weekend/evening work for bugs/deployments
  - Pressure to hit go-live deadline
  
Mitigation:
  [ ] Hire 3rd backend engineer (or contractor) for Phases 4-5
  [ ] Phases are 2 weeks, not 1 week (reasonable pace)
  [ ] Code review time built into timeline (not rushed)
  [ ] Testing time allocated (not "test later")
  [ ] Friday afternoons off (team morale + planning)
  [ ] Post-launch: 2-week cooldown before Phase 8 starts
  
Contingency:
  IF team exhausted:
    → Extend timeline 2-3 weeks (Phase 8 features pushed)
    → Hire contractor for 3-4 weeks
    → Reduce Phase scope (defer Phase 7 mobile to next quarter)
```

---

### 🟡 MEDIUM RISKS (Impact: MODERATE, Probability: MEDIUM)

#### Risk 3.1: Architectural Decisions Revisited Mid-Project
```
Description: "Should we use Elasticsearch for search?" (Week 5, mid-Phase 2)
Probability: MEDIUM (30%)
Impact: MODERATE - 1-2 week delay, refactoring

Examples:
  - Switch from SQLite to PostgreSQL mid-Phase 0 (we're doing this anyway)
  - Add Redis caching in Phase 2 (should be Phase 0-1)
  - Change React to Vue in Phase 3 (nightmare scenario)
  
Mitigation:
  [ ] Architecture review BEFORE Phase 0 (done: COMPLETE_SYSTEM_ARCHITECTURE.md)
  [ ] Tech stack locked in: PostgreSQL, React, FastAPI, Redis
  [ ] Major decisions: Search (full-text SQL first, Elasticsearch if needed), Cache (Redis), Jobs (Celery)
  [ ] Weekly architecture review (ensure no mid-project changes)
  
Contingency:
  IF major architecture change needed:
    → Delay go-live 1-2 weeks
    → Add 3rd engineer to transition phase
```

#### Risk 3.2: Poor Test Coverage (Bugs in Production)
```
Description: "We ran out of time for testing" → 100+ bugs found in Week 1
Probability: MEDIUM (25%) - common in startups
Impact: MODERATE - reputation damage, 1-2 week hotfix sprints

Mitigation:
  [ ] Each phase allocates 20-25% time for testing
  [ ] Unit tests written DURING coding, not after
  [ ] Integration tests run nightly (CI/CD pipeline)
  [ ] Load tests before each phase goes to production
  [ ] Regression tests maintained (no features broken)
  [ ] QA team involved from Phase 1 (not added in Phase 6)
  
Contingency:
  IF bugs spike in production:
    → Pause new features (enter bug-fix mode)
    → Dedicate QA + 1 engineer to hotfixes
    → Delay Phase 7 / go-live by 2-4 weeks
    → Root cause: Insufficient testing in previous phase
```

#### Risk 3.3: Retailer Onboarding Too Slow
```
Description: Can only onboard 10 retailers/week (target: 50+/week)
Probability: MEDIUM (20%)
Impact: MODERATE - miss revenue targets

Reasons:
  - Onboarding workflow too complex
  - Staff training takes 2+ hours per retailer
  - System has bugs that require support tickets
  
Mitigation:
  [ ] Phase 1: Onboarding workflow simplified (< 15 minutes)
  [ ] Phase 1: Demo video + guided tour
  [ ] Phase 2+: Self-service (most issues self-resolved)
  [ ] Hire onboarding specialist (not just support)
  [ ] Track: Onboarding time, first-sale time, support tickets
  
Contingency:
  IF onboarding slow:
    → Analyze bottlenecks (UX issue? training? system bug?)
    → Fix most common issue first
    → Provide better documentation/training
```

---

### 🟢 LOW RISKS (Impact: MINOR, Probability: LOW)

#### Risk 4.1: Mobile App Store Rejection
```
Description: iOS rejected, Android delayed, go-live set back 2 weeks
Probability: LOW (5%) - if compliance done correctly
Impact: MINOR - Phase 7 delayed, but can do without mobile initially

Mitigation:
  [ ] Phase 7: Review Apple App Store guidelines early
  [ ] Phase 7: Beta testing with real users (TestFlight)
  [ ] Phase 7: Ensure privacy policy, data handling compliant
  
Contingency:
  IF rejected:
    → Fix issues, resubmit (2 weeks for review)
    → Launch Android first (less strict review)
    → Don't delay Phase 7, web app serves as fallback
```

#### Risk 4.2: Forecast Model Accuracy Poor
```
Description: Phase 5 forecasts only 60% accurate (target: 85%+)
Probability: LOW (15%) - if data quality good
Impact: MINOR - Phase 5 extended 1 week, but system still works

Mitigation:
  [ ] Phase 5: Data quality audits before model training
  [ ] Phase 5: Multiple models tested (ARIMA, Prophet, LSTM)
  [ ] Phase 5: Cross-validation (80% accuracy minimum before launch)
  
Contingency:
  IF models poor:
    → Extend Phase 5 by 1 week
    → Improve feature engineering
    → Add domain expertise (retailer feedback)
    → Switch to simpler model (moving average) as fallback
```

#### Risk 4.3: Competitor Launches Similar Product
```
Description: Competitor launches POS system with invoicing
Probability: LOW (10%) - but always possible
Impact: MINOR - lose first-mover advantage, but can compete

Mitigation:
  [ ] Go-live fast (14 weeks vs. competitor's 6+ months)
  [ ] Better UX (focus on retailer experience, not features)
  [ ] Localization (Hindi support in Phase 6)
  
Contingency:
  IF competitor launches:
    → Don't change roadmap (stay focused)
    → Highlight unique features (offline mode, WhatsApp, Hindi)
    → Accelerate onboarding (capture market share fast)
```

---

## RISK SCORING MATRIX

```
CRITICAL RISKS (Must prevent):
  - Phase 0 gate rejection (30% chance, catastrophic impact)
  - Data loss during migration (10% chance, catastrophic)
  - Performance collapse at scale (25% chance, catastrophic)
  
HIGH RISKS (Monitor closely):
  - Scope creep (50% chance, severe)
  - Key person departure (20% chance, severe)
  - Third-party API failures (15% chance, severe)
  - Team burnout (40% chance, severe)
  
MEDIUM RISKS (Plan for):
  - Architecture changes (30% chance, moderate)
  - Poor test coverage (25% chance, moderate)
  - Slow onboarding (20% chance, moderate)
  
LOW RISKS (Document, monitor):
  - Mobile app rejection (5% chance, minor)
  - Forecast accuracy issues (15% chance, minor)
  - Competitor launch (10% chance, minor)
```

---

## MONTHLY RISK REVIEW TEMPLATE

```
MONTH 1 (Weeks 1-4): Phase 0 + Phase 1
[ ] Phase 0 gate on track? (Critical Risk 1.1)
[ ] Data migration successful? (Critical Risk 1.2)
[ ] Load test 100 users passing? (Critical Risk 1.3)
[ ] Any scope creep detected? (High Risk 2.1)
[ ] Team morale good? (High Risk 2.4)
Update: _____________________

MONTH 2 (Weeks 5-8): Phases 2-3
[ ] Performance still good? (Critical Risk 1.3)
[ ] Third-party APIs reliable? (High Risk 2.3)
[ ] Key engineers still on team? (High Risk 2.2)
[ ] Test coverage >80%? (Medium Risk 3.2)
[ ] Onboarding workflow defined? (Medium Risk 3.3)
Update: _____________________

MONTH 3 (Weeks 9-14): Phases 4-7
[ ] Forecast model accuracy >80%? (Low Risk 4.2)
[ ] Mobile app review progressing? (Low Risk 4.1)
[ ] All systems integrated well? (Medium Risk 3.1)
[ ] Ready for production go-live? (All risks resolved)
Update: _____________________
```

---

*Dependencies & Risk Matrix - R-DIOS v3.0  
Updated: 14 February 2026*
