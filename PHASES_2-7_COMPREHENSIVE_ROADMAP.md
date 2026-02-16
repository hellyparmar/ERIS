# PHASES 2-7 COMPREHENSIVE ROADMAP
**Duration:** 14 weeks (70 business days)  
**From:** 4.4/10 Readiness → 8.5/10 Production-Ready  
**Value Delivered:** ₹2M+ annual revenue protection + 100% retailer satisfaction  
**Team:** 8 people (Backend 2, Frontend 2, DevOps 1, QA 2, Product 1)

---

## EXECUTIVE SUMMARY

After Phase 0 (4 days) completes, R-DIOS enters a 14-week acceleration phase to transform from "works locally" to "production system used by 1000+ retailers."

**Current State (End of Phase 0):**
- ✅ PostgreSQL operational
- ✅ All hardcoded URLs removed
- ✅ Crash patches applied
- ✅ Readiness: 5.2/10

**Target State (End of Phase 7):**
- ✅ Production hardened system
- ✅ Multi-language (Hindi + English)
- ✅ Mobile app (iOS + Android)
- ✅ AI-powered forecasting
- ✅ Readiness: 8.5/10
- ✅ 1000+ concurrent users supported

---

## PHASE OVERVIEW

| Phase | Name | Duration | Owner | Value | Readiness |
|-------|------|----------|-------|-------|-----------|
| 0 | **Critical Blockers** | 4 days | Tech Lead | PostgreSQL, URLs, crashes | 4.4→5.2 |
| 1 | **POS System** | 2 weeks | Frontend Lead | Cashier sales workflow | 5.2→6.0 |
| 2 | **Inventory** | 2 weeks | Backend Lead | Real-time stock, alerts | 6.0→6.5 |
| 3 | **Invoicing** | 2 weeks | Backend Lead | GST, compliance, PDF | 6.5→7.0 |
| 4 | **Analytics** | 2 weeks | Backend Lead | Real-time dashboards, reports | 7.0→7.3 |
| 5 | **Forecasting** | 1.5 weeks | Backend Lead | Demand prediction, ML | 7.3→7.6 |
| 6 | **Localization** | 1.5 weeks | Frontend Lead | Hindi UI, regional settings | 7.6→8.0 |
| 7 | **Mobile App** | 2 weeks | Frontend Lead | iOS + Android (React Native) | 8.0→8.5 |

**Total:** 14 weeks (70 days)

---

## DETAILED PHASE BREAKDOWN

---

# PHASE 1: POS SYSTEM (2 weeks)
**Blocked On:** Phase 0 Gate Approval  
**Owner:** Frontend Lead + Backend Lead

## What Gets Built
- Complete POS page (barcode scan, manual search, cart, payment)
- Backend sale endpoints (create sale, payment processing)
- Receipt printing (58mm/80mm thermal printer, ESC/POS)
- WhatsApp receipt delivery (via Twilio/WATI)
- Offline transaction queue (IndexedDB)
- Integration tests

## Success Metrics
- Cashier completes 50+ transactions/day
- <2 seconds per operation
- Zero transaction loss (99.99% uptime)
- 95% customer satisfaction on checkout speed

## Daily Breakdown (see PHASE_1_POS_SPECIFICATION.md)
- Week 1: Design + API (Mon-Fri)
- Week 2: Receipts + WhatsApp + offline (Mon-Fri)

## Readiness Impact
- 5.2/10 → 6.0/10 (cashier workflow complete)

---

# PHASE 2: INVENTORY MANAGEMENT (2 weeks)
**Blocked On:** Phase 1 Complete  
**Owner:** Backend Lead + Frontend Lead

## What Gets Built
- Paginated inventory list (26K+ products)
- Real-time low-stock alerts (<500ms)
- Expiry date tracking + warnings
- Smart auto-reorder with supplier integration
- Stock adjustment history (audit trail)
- Multi-location inventory view

## Success Metrics
- 100% inventory accuracy
- Prevent stockouts (₹50K+ daily revenue protected)
- 6 hours/week manual work saved
- 5-10% margin improvement (reduced waste)

## Daily Breakdown (see PHASE_2_INVENTORY_SPECIFICATION.md)
- Week 1: Database schema + pagination + alerts (Mon-Fri)
- Week 2: Frontend UI + testing + go-live (Mon-Fri)

## Readiness Impact
- 6.0/10 → 6.5/10 (inventory management complete)

---

# PHASE 3: INVOICING & GST COMPLIANCE (2 weeks)
**Blocked On:** Phase 2 Complete  
**Owner:** Backend Lead + QA Lead

## What Gets Built
- Invoice creation workflow (auto GST calculation)
- Multiple payment methods (Cash, Card, UPI, Check)
- PDF generation (branded invoices)
- Email delivery (with PDF attachment)
- GST compliance reports (B2B invoices, GSTR-1 export)
- Bill management (vendor bills, GST input credits)
- POS to Invoice conversion (single/bulk)
- Reconciliation (invoice vs delivery)

## Success Metrics
- 1000+ invoices/day processable
- <5 second PDF generation
- 100% GST compliance
- Zero revenue leakage (all sales invoiced)
- Tally/Quickbooks sync ready

## Database Changes
- Add invoice_id to sales (link POS → Invoice)
- Add payment_methods table
- Add gst_returns table (GSTR-1, GSTR-2)

## Endpoints Added (11)
```
POST   /api/v1/invoices/create
GET    /api/v1/invoices
GET    /api/v1/invoices/{id}
PUT    /api/v1/invoices/{id}
POST   /api/v1/invoices/{id}/payment
POST   /api/v1/invoices/{id}/get-pdf
POST   /api/v1/invoices/{id}/send-email
GET    /api/v1/invoices/analytics/summary
GET    /api/v1/invoices/analytics/monthly
GET    /api/v1/bills/reconciliation/{period}
POST   /api/v1/pos/sales-to-invoice
```

## Readiness Impact
- 6.5/10 → 7.0/10 (compliance + revenue tracking complete)

---

# PHASE 4: ANALYTICS & BUSINESS INTELLIGENCE (2 weeks)
**Blocked On:** Phase 3 Complete  
**Owner:** Backend Lead + Frontend Lead

## What Gets Built
- Real-time dashboard (KPIs, charts, alerts)
- Sales analytics (hourly/daily/weekly/monthly trends)
- Customer analytics (segmentation, RFM, LTV)
- Product analytics (top products, sell-through rate)
- Vendor analytics (payment history, quality)
- Employee analytics (cashier performance, adherence)
- Custom reports builder
- Data export (Excel, PDF, CSV)

## Success Metrics
- Dashboard loads <1 second
- Real-time data (updated every 60 seconds)
- 100+ different reports available
- User can create custom reports in <2 minutes

## Endpoints Added (6)
```
GET    /api/v1/analytics/sales
GET    /api/v1/analytics/customers
GET    /api/v1/analytics/products
GET    /api/v1/analytics/vendors
GET    /api/v1/analytics/employees
GET    /api/v1/reports/custom
```

## Database Optimization
- Add materialized views for fast reporting
- Implement data warehouse schema (star schema)
- Archive old transactions (>1 year) for performance

## Readiness Impact
- 7.0/10 → 7.3/10 (decision-making insights complete)

---

# PHASE 5: DEMAND FORECASTING & OPTIMIZATION (1.5 weeks)
**Blocked On:** Phase 4 Complete  
**Owner:** Backend Lead + Data Scientist

## What Gets Built
- Demand forecasting (ARIMA, Prophet, ML models)
- Seasonality detection (holidays, festivals, weather)
- Stock optimization (safety stock, reorder point)
- Price elasticity analysis
- Promotion ROI tracking
- Demand alerts (unusual patterns)

## Success Metrics
- Forecast accuracy >85% (MAPE <15%)
- Reduce overstock by 20%
- Reduce stockouts by 30%
- Stock carrying cost reduced by 15%

## Endpoints Added (4)
```
GET    /api/forecasting/forecast/{product_id}
GET    /api/forecasting/seasonality/{product_id}
GET    /api/forecasting/optimization-recommendations
POST   /api/forecasting/train-model
```

## Tech Stack
- Python: scikit-learn, statsmodels, Prophet
- Background jobs: Celery
- Model storage: MLflow
- Feature store: Redis

## Readiness Impact
- 7.3/10 → 7.6/10 (predictive intelligence complete)

---

# PHASE 6: LOCALIZATION & REGIONAL SUPPORT (1.5 weeks)
**Blocked On:** Phase 5 Complete  
**Owner:** Frontend Lead + Backend Lead

## What Gets Built
- Hindi UI (all pages translated)
- Regional language support (6 languages: Hi, Ta, Te, Kn, Mr, Gu)
- Locale-specific number formatting (₹ symbol, 1,00,000 format)
- Date/time locale formatting
- Regional payment methods (UPI, Google Pay, PhonePe)
- Indian phone number validation
- GST rate tables by state
- Regional holiday calendars
- RTL support (future: Arabic, Urdu)

## Success Metrics
- 90%+ UI coverage in Hindi
- All error messages translated
- User can switch language in 1 click
- <100ms language switching

## Frontend Changes
- i18n framework (react-i18next)
- Translation files (JSON) for 6 languages
- Locale provider context
- 500+ translation strings

## Readiness Impact
- 7.6/10 → 8.0/10 (usability for Indian retailers complete)

---

# PHASE 7: MOBILE APP (iOS + Android) (2 weeks)
**Blocked On:** Phase 6 Complete  
**Owner:** Frontend Lead (React Native)

## What Gets Built
- iOS app (via React Native)
- Android app (via React Native)
- Offline-first architecture (sync when online)
- Biometric login (fingerprint/face)
- Home screen widgets (quick stats)
- Deep linking (share product/invoice links)
- Push notifications
- App Store + Google Play distribution

## Features in Mobile App
- View dashboard (read-only on mobile)
- Check inventory (quick scan, search)
- Manage customers (WhatsApp contact)
- Accept payments (QR code, camera)
- View sales (last 30 days)
- Print receipts (via Bluetooth printer)
- Settings (profile, app preferences)

## Success Metrics
- 4.5+ star rating on both stores
- 50K+ downloads in first 3 months
- <50MB app size
- 99.9% uptime
- <1 second app startup

## Tech Stack
- React Native (Expo)
- Firebase (push notifications)
- Redux (state management)
- SQLite (offline storage)

## Readiness Impact
- 8.0/10 → 8.5/10 (mobile-first retailer support complete)

---

## CROSS-PHASE DEPENDENCIES

```
Phase 0 (4d)
    ↓
Phase 1 (2w) ← POS system foundation
    ↓
Phase 2 (2w) ← Inventory ties to sales
    ↓
Phase 3 (2w) ← Invoicing ties to sales + inventory
    ↓
Phase 4 (2w) ← Analytics aggregates all data
    ↓
Phase 5 (1.5w) ← Forecasting uses historical data
    ↓
Phase 6 (1.5w) ← Localization across all phases
    ↓
Phase 7 (2w) ← Mobile app mirrors Phase 1-6 features
```

**Critical Path:** Phase 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7

---

## TEAM ASSIGNMENT & CAPACITY

### Backend Team (2 engineers)
**Capacity:** 80 hours/week = 4 weeks/engineer

| Phase | Tasks | Hours | Owner | Timeline |
|-------|-------|-------|-------|----------|
| 1 | Sales endpoints, payment | 40 | BE1 | Week 2 |
| 2 | Inventory API, alerts | 40 | BE2 | Week 4-5 |
| 3 | Invoicing, GST, PDF | 60 | BE1+BE2 | Week 6-7 |
| 4 | Analytics, reporting | 50 | BE1 | Week 8-9 |
| 5 | Forecasting, ML models | 50 | BE2 | Week 10-11 |
| 6 | Localization backend | 30 | BE1 | Week 12 |
| 7 | Mobile API support | 20 | BE2 | Week 13-14 |

### Frontend Team (2 engineers)
**Capacity:** 80 hours/week = 4 weeks/engineer

| Phase | Tasks | Hours | Owner | Timeline |
|-------|-------|-------|-------|----------|
| 1 | POS page, payment UI | 50 | FE1 | Week 2-3 |
| 2 | Inventory dashboard | 40 | FE1 | Week 4-5 |
| 3 | Invoice UI | 30 | FE2 | Week 6-7 |
| 4 | Analytics dashboards | 50 | FE2 | Week 8-9 |
| 5 | Forecasting UI | 20 | FE1 | Week 10-11 |
| 6 | i18n, localization | 50 | FE1+FE2 | Week 12 |
| 7 | Mobile app (React Native) | 80 | FE1 | Week 13-14 |

### QA Team (2 engineers)
**Capacity:** 80 hours/week

| Phase | Tasks | Hours | Owner | Timeline |
|-------|-------|-------|-------|----------|
| 1 | POS testing, integration | 40 | QA1 | Week 2-3 |
| 2 | Inventory testing | 30 | QA2 | Week 4-5 |
| 3 | GST compliance testing | 50 | QA1 | Week 6-7 |
| 4 | Analytics accuracy | 40 | QA2 | Week 8-9 |
| 5 | Forecast accuracy | 30 | QA1 | Week 10-11 |
| 6 | Localization testing (all languages) | 40 | QA1+QA2 | Week 12 |
| 7 | Mobile app testing (iOS + Android) | 60 | QA1+QA2 | Week 13-14 |

### DevOps (1 engineer)
- Week 1-4: Database performance tuning, monitoring setup
- Week 5-7: Docker deployment automation
- Week 8-14: Infrastructure scaling (prepare for 1000+ users)

### Product Lead (1 person)
- Weekly stakeholder updates
- Feature priority decisions
- User feedback collection
- Go-live planning

---

## WEEKLY MILESTONE SCHEDULE

```
WEEK 1:  Phase 0 (Mon-Thu) + Phase 1 planning (Fri)
WEEK 2:  Phase 1 Design + API (BE1, FE1)
WEEK 3:  Phase 1 Receipts + Testing (BE1, FE1, QA1)
WEEK 4:  Phase 2 Inventory (BE2, FE1) — PARALLEL
WEEK 5:  Phase 2 Testing + Phase 3 planning (BE2, FE1, QA2)
WEEK 6:  Phase 3 Invoicing + GST (BE1+BE2, FE2)
WEEK 7:  Phase 3 Testing + Phase 4 planning (BE1+BE2, FE2, QA1)
WEEK 8:  Phase 4 Analytics (BE1, FE2)
WEEK 9:  Phase 4 Testing + Phase 5 planning (BE1, FE2, QA1+QA2)
WEEK 10: Phase 5 Forecasting (BE2 + Data Scientist)
WEEK 11: Phase 5 Testing + Phase 6 planning (BE2, QA1)
WEEK 12: Phase 6 Localization (FE1+FE2, BE1)
WEEK 13: Phase 7 Mobile App (FE1, QA1+QA2)
WEEK 14: Phase 7 Testing + Production Hardening (FE1, QA1+QA2)
```

---

## CRITICAL SUCCESS FACTORS

### 1. Phase 0 Gate Approval (Make or Break)
```
IF Phase 0 gate NOT approved:
  → Entire roadmap delayed
  → Risk: Run out of budget/time
  
GATE CRITERIA (must all pass):
  [ ] PostgreSQL operational
  [ ] All 37 endpoints pass tests (100%)
  [ ] Load test: 100 concurrent users, <200ms
  [ ] No hardcoded URLs
  [ ] Zero data loss
  [ ] Documentation complete
```

### 2. Scope Discipline (Don't Add Features)
```
WHAT'S IN SCOPE (14 weeks, above):
  ✅ Phases 1-7 as described
  ✅ Bug fixes for Phase 1-7 features
  
WHAT'S OUT OF SCOPE (defer to Phase 8):
  ❌ B2B Marketplace (complex, 4+ weeks)
  ❌ Causal Analysis (research, not revenue)
  ❌ Advanced ML/AI (overkill for Phase 1)
  ❌ Offline POS (complex, Phase 7 mobile covers)
  ❌ WhatsApp Business API (API, not product)
```

### 3. Architecture Decisions Made Upfront
```
DATABASE: PostgreSQL 15 (Phase 0)
CACHE: Redis for real-time data (Phase 4)
SEARCH: Elasticsearch for product search (Phase 2, optional)
JOBS: Celery for background tasks (Phase 5+)
MESSAGING: RabbitMQ/Redis for async (Phase 1+)
MONITORING: Prometheus + Grafana (Phase 1)
LOGGING: ELK stack or Datadog (Phase 1)
MOBILE: React Native (Phase 7)
```

### 4. Data Quality During Migration
```
Phase 0 data migration (SQLite → PostgreSQL):
  [ ] Backup SQLite before migration
  [ ] Verify row counts match
  [ ] Spot-check data (sample 100 records)
  [ ] Test all 37 endpoints after migration
  
If migration fails:
  → Rollback to SQLite
  → Fix issues
  → Retry migration
```

### 5. Testing at Every Phase
```
Phase 1: Unit tests (50+), Integration tests (20+), Load test
Phase 2: Database tests (20+), API tests (15+), Frontend tests (30+)
Phase 3: GST compliance tests (30+), PDF tests (10+), Email tests
Phase 4: Analytics accuracy tests (25+), Chart tests (15+)
Phase 5: Forecast accuracy tests (20+), ML model tests (15+)
Phase 6: i18n tests (50+), RTL tests (10+)
Phase 7: Mobile tests (iOS 30+, Android 30+), E2E tests (20+)

Target: >80% code coverage, >95% functional coverage
```

---

## RESOURCE REQUIREMENTS

### Team Size
- Backend: 2 engineers
- Frontend: 2 engineers
- QA: 2 engineers
- DevOps: 1 engineer
- Product Lead: 1 person
- **Total: 8 people**

### Infrastructure
- PostgreSQL 15 server (production-grade)
- Redis cluster (caching + sessions)
- RabbitMQ (async jobs)
- Docker registry (container images)
- Monitoring stack (Prometheus, Grafana, Datadog)
- S3 / Cloud storage (for PDFs, exports)
- CI/CD (GitHub Actions, GitLab CI, or Jenkins)

### Third-Party Services
- **Payments:** Razorpay (UPI, Card, NetBanking)
- **SMS/WhatsApp:** WATI, Twilio, AWS SNS
- **Email:** SendGrid, AWS SES
- **Monitoring:** Datadog, New Relic, Sentry
- **Analytics:** Mixpanel, Amplitude

### Training & Onboarding
- Week 1: Team onboarding (Phase 0 walkthrough)
- Week 2: Phase 1 kickoff (design review, API review)
- Weekly: Architecture reviews, sprint planning

---

## BUDGET ESTIMATE

| Category | Cost | Duration |
|----------|------|----------|
| **Team (8 people)** | ₹24L | 14 weeks |
| **Infrastructure** | ₹3L | 14 weeks |
| **Third-party APIs** | ₹2L | 14 weeks |
| **Tools & Services** | ₹1L | 14 weeks |
| **Contingency (20%)** | ₹6L | |
| **TOTAL** | **₹36L** | **14 weeks** |

**ROI:** ₹2M annual revenue protected + 100+ retailer customers @ ₹5K/month = ₹6M annual recurring revenue

---

## GO-LIVE CHECKLIST

### Pre-Go-Live (Week 13)
- [ ] All phases complete and tested
- [ ] Load test: 1000+ concurrent users
- [ ] Data migration (Phase 1-7) verified
- [ ] Production database backed up
- [ ] Monitoring alerts configured
- [ ] Disaster recovery plan tested
- [ ] Support team trained
- [ ] Documentation complete

### Go-Live (Week 14)
- [ ] Phase 1: POS system live (beta with 10 stores)
- [ ] Phase 1-3: Full features live (all 100 stores)
- [ ] Phase 4-7: Advanced features available
- [ ] 24/7 support team active
- [ ] Post-go-live monitoring (24 hours)
- [ ] Performance metrics baseline

### Post-Go-Live
- Week 1: Daily standups, bug fixes, hotfixes
- Week 2-4: Weekly releases (bug fixes + optimizations)
- Week 5+: Monthly releases, feature enhancements

---

## SUCCESS METRICS (END OF PHASE 7)

### Business Metrics
- ✅ 1000+ retailers on platform
- ✅ ₹2M+ annual revenue protected
- ✅ 98%+ system uptime
- ✅ <2 second average response time
- ✅ 4.5+ star rating (app stores)
- ✅ <5% monthly churn

### Technical Metrics
- ✅ 8.5/10 production readiness
- ✅ 1000+ concurrent users supported
- ✅ >80% code coverage
- ✅ <100ms p95 latency
- ✅ Zero security vulnerabilities
- ✅ Automatic scaling (up to 5000 users)

### User Satisfaction Metrics
- ✅ 90%+ users report "very easy to use"
- ✅ 95%+ tasks completed <5 minutes
- ✅ <2% daily active bugs reported
- ✅ 98% customer support resolved <24 hours

---

## RISK MITIGATION

### Critical Risks

**Risk 1: Team turnover**
- Impact: HIGH (lose institutional knowledge)
- Mitigation: Documentation, knowledge sharing, mentoring

**Risk 2: Scope creep**
- Impact: HIGH (miss go-live deadline)
- Mitigation: Strict feature gate, backlog discipline, weekly reviews

**Risk 3: Performance degradation**
- Impact: HIGH (system slows with data)
- Mitigation: Database tuning, caching, load testing at each phase

**Risk 4: Data loss during migration**
- Impact: CRITICAL (lose all history)
- Mitigation: Backup before migration, verify data integrity

**Risk 5: Third-party API failures**
- Impact: MEDIUM (payment processing fails)
- Mitigation: Fallback payment methods, API rate limiting, retry logic

### Medium Risks

**Risk 6: Mobile app store rejection**
- Impact: MEDIUM (can't release iOS/Android)
- Mitigation: Early submission, compliance review, apple dev account setup

**Risk 7: Competitor feature launch**
- Impact: MEDIUM (lose market differentiation)
- Mitigation: Feature prioritization by business value, market research

**Risk 8: Customer data breach**
- Impact: CRITICAL (reputation damage)
- Mitigation: Security audits, penetration testing, encryption, compliance (ISO27001)

---

## DECISION GATES

### Gate 1: Phase 0 Complete (Week 1)
```
DECISION: Can we proceed to Phase 1?

CRITERIA:
  [ ] PostgreSQL operational
  [ ] All 37 endpoints pass
  [ ] Load test 100 concurrent users ✓
  [ ] No hardcoded URLs ✓
  [ ] Phase 1 specification reviewed ✓
  
APPROVAL REQUIRED FROM:
  [ ] Tech Lead
  [ ] Backend Lead
  [ ] Frontend Lead
  [ ] DevOps Engineer
  
IF NOT APPROVED: Fix blockers, re-test, retry gate
IF APPROVED: Start Phase 1 Monday morning (Week 2)
```

### Gate 2: Phase 1 Complete (Week 3)
```
DECISION: Is POS system production-ready?

CRITERIA:
  [ ] All user workflows tested (barcode, manual, discount, payment)
  [ ] Receipt printing works (thermal printer)
  [ ] WhatsApp delivery working
  [ ] Offline queue handling tested
  [ ] 100% test pass rate
  [ ] <2 seconds per operation
  [ ] Can handle 500+ transactions/day
  
IF NOT APPROVED: Extend Phase 1, fix issues, retry
IF APPROVED: Start Phase 2 (Inventory)
```

### Gate 3: Phases 2-5 Complete (Week 11)
```
DECISION: Can we launch Phase 6 (Localization)?

CRITERIA:
  [ ] POS + Inventory + Invoicing + Analytics verified
  [ ] No critical bugs in Phase 1-5
  [ ] Performance metrics acceptable
  [ ] Team ready for Phase 6 sprint
  [ ] Localization requirements finalized
  
IF NOT APPROVED: Fix Phase 1-5 issues before Phase 6
IF APPROVED: Start Phase 6 (i18n)
```

### Gate 4: Phase 7 Complete - Production Go-Live (Week 14)
```
DECISION: Is system ready for production?

CRITERIA:
  [ ] All 7 phases complete + tested
  [ ] Load test: 1000+ concurrent users ✓
  [ ] Disaster recovery tested
  [ ] Support team trained
  [ ] Marketing/sales materials ready
  [ ] Legal/compliance review done
  [ ] Mobile apps in app stores
  [ ] 24/7 support team ready
  
APPROVAL REQUIRED FROM:
  [ ] Tech Lead
  [ ] QA Lead
  [ ] DevOps Lead
  [ ] Product Lead
  [ ] CEO/Founder
  
IF APPROVED: GO-LIVE! 🎉
IF NOT APPROVED: Delay go-live, fix critical issues
```

---

## APPENDIX: PHASE COMPARISON

| Phase | Duration | Team | Features | Tests | Readiness |
|-------|----------|------|----------|-------|-----------|
| 0 | 4d | 5 | PostgreSQL, URLs, crashes | Unit + integration | 5.2 |
| 1 | 2w | 3 | POS, payment, receipt, WhatsApp | Integration + load | 6.0 |
| 2 | 2w | 2 | Inventory, alerts, expiry, reorder | API + frontend | 6.5 |
| 3 | 2w | 2 | Invoicing, GST, PDF, bills | Compliance + load | 7.0 |
| 4 | 2w | 2 | Analytics, reporting, dashboards | Accuracy + frontend | 7.3 |
| 5 | 1.5w | 1.5 | Forecasting, ML, optimization | Accuracy + unit | 7.6 |
| 6 | 1.5w | 2 | i18n, localization, regional | i18n + translation | 8.0 |
| 7 | 2w | 3 | Mobile app, iOS, Android, widgets | Mobile + E2E | 8.5 |

---

*14-Week Comprehensive Roadmap - R-DIOS v3.0  
From 4.4/10 to 8.5/10 Production Ready  
Start Date: Week 1 (after Phase 0)  
End Date: Week 14 (Production Go-Live)*
