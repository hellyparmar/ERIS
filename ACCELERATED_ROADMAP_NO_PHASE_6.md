# ACCELERATED ROADMAP: PHASES 0-7 (NO PHASE 6 LOCALIZATION)
**Status:** Updated Feb 14, 2026  
**Change:** Removed Phase 6 (Hindi Localization) → 2 weeks saved, ₹4L budget saved  
**New Go-Live:** April 25, 2026 (Friday) ← 2 weeks earlier than original May 9  

---

## EXECUTIVE SUMMARY

| Metric | Original | Updated | Change |
|--------|----------|---------|--------|
| **Timeline** | 18 weeks | 16.5 weeks | -1.5 weeks ✅ |
| **Go-Live Date** | May 9 | April 25 | -2 weeks ✅ |
| **Budget** | ₹36L | ₹32L | -₹4L ✅ |
| **Phases** | 0-7 (8 phases) | 0-5, 7 (7 phases) | Phase 6 removed |
| **Readiness** | 4.4/10 → 8.5/10 | Same | 8.5/10 target |
| **Revenue** | ₹6M annual | Same | ₹6M target |
| **Launch Scale** | 1000+ retailers | Same | 1000+ target |

**KEY BENEFIT:** Go live 2 weeks earlier with same end state (8.5/10 readiness).  
**RATIONALE:** Hindi localization (Phase 6) can be added in Phase 8 or later. MVP focuses on core features first.

---

## PHASES AT A GLANCE

```
PHASE 0 (Feb 17-20):     CRITICAL BLOCKERS (4 days)
  → SQLite→PostgreSQL, fix URLs, crash patches
  → Go-live date: Feb 20 ✅
  
PHASE 1 (Feb 24-Mar 6):  POS SYSTEM (2 weeks)
  → Barcode scanning, cart, payment, receipt, WhatsApp
  → Readiness: 5.2/10
  
PHASE 2 (Mar 10-20):     INVENTORY (2 weeks)
  → Pagination, real-time alerts, expiry, auto-reorder
  → Readiness: 6.5/10
  
PHASE 3 (Mar 24-Apr 3):  INVOICING (2 weeks)
  → GST calculation, PDF generation, bills, compliance
  → Readiness: 7.0/10
  
PHASE 4 (Apr 7-18):      ANALYTICS (2 weeks)
  → Dashboards, 100+ reports, real-time insights
  → Readiness: 7.5/10
  
PHASE 5 (Apr 21-May 2):  FORECASTING (1.5 weeks)
  → ML models (ARIMA, Prophet), demand prediction
  → Readiness: 8.0/10
  
PHASE 6: ⏭️  SKIPPED (Hindi Localization removed from MVP)
  → Can be added in Phase 8 or later if needed
  
PHASE 7 (May 5-16):      MOBILE APP (2 weeks)
  → iOS + Android React Native apps
  → Readiness: 8.5/10
  
🎯 GO-LIVE (Apr 25):     PRODUCTION DEPLOYMENT
```

---

## DETAILED PHASE BREAKDOWN

### PHASE 0: CRITICAL BLOCKERS (Feb 17-20, 4 days)
**Owner:** Tech Lead, Backend Lead, Frontend Lead, DevOps, QA  
**Status:** NOT STARTED  
**Effort:** 50 total hours (distributed)

Fixes 3 production blockers:
1. **SQLite Bottleneck** → Migrate to SQL
2. **Hardcoded URLs** → Use environment variables
3. **Pagination Crash** → Implement proper pagination

**Deliverables:**
- PostgreSQL database running in production
- All 37 endpoints passing tests
- No hardcoded URLs remaining
- Load test: 100 concurrent users, <200ms, 0% error
- Readiness: 4.4/10 → 5.2/10

**Gate Approval Criteria (10 items):**
- [ ] PostgreSQL operational
- [ ] 37/37 endpoints passing
- [ ] Load test successful (100 users, <200ms)
- [ ] No hardcoded URLs
- [ ] Crashes fixed
- [ ] Documentation complete
- [ ] Rollback plan tested
- [ ] Team trained
- [ ] All signatures collected
- [ ] Readiness: 5.2/10 confirmed

---

### PHASE 1: POS SYSTEM (Feb 24-Mar 6, 2 weeks)
**Owner:** Backend Lead, Frontend Lead  
**Status:** NOT STARTED  
**Effort:** 80 total hours

Complete POS system for barcode scanning & checkout.

**Features:**
- Barcode/QR code scanning
- Product search (name, SKU)
- Shopping cart management
- Discount/tax application
- Payment processing (Razorpay)
- Receipt printing (thermal 58mm/80mm)
- Receipt delivery via WhatsApp
- Offline transaction queue

**API Endpoints:**
- POST /api/v1/sales/create
- GET /api/v1/sales/{id}
- POST /api/v1/sales/{id}/payment
- POST /api/v1/sales/{id}/print-receipt
- POST /api/v1/sales/{id}/send-whatsapp

**Frontend Components:**
- POS page (Vite + React)
- Barcode scanner integration
- Cart UI
- Payment selection
- Receipt preview

**Tests:**
- Unit tests (50+ test cases)
- Integration tests (end-to-end workflow)
- Load test (50 concurrent POS users)
- Thermal printer compatibility

**Success Criteria:**
- ✅ Barcode scanning works
- ✅ Cart & payment functional
- ✅ Receipt printing <2 sec
- ✅ WhatsApp delivery confirmed
- ✅ 100% test pass rate
- ✅ Readiness: 6.0/10

---

### PHASE 2: INVENTORY (Mar 10-20, 2 weeks)
**Owner:** Backend Lead, Frontend Lead  
**Status:** NOT STARTED  
**Effort:** 80 total hours

Real-time inventory management with pagination & alerts.

**Features:**
- Inventory dashboard (26.4K+ products)
- Pagination (50/100/250 items per page)
- Real-time low-stock alerts (<500ms)
- Product expiry tracking
- Stock adjustments with audit trail
- Auto-reorder workflow
- Inventory analytics

**Database Changes:**
- `alerts` table (alert_type, severity, metadata)
- `stock_adjustments` table (audit trail)
- New columns: `expiry_date`, `min_stock`, `max_stock`, `reorder_quantity`

**API Endpoints:**
- GET /api/v1/inventory/list (paginated)
- GET /api/v1/inventory/alerts
- POST /api/v1/inventory/adjust
- POST /api/v1/inventory/auto-reorder

**Frontend Components:**
- Inventory table (paginated)
- Real-time alerts modal
- Search/filter/sort UI
- Stock adjustment form
- Analytics charts

**Tests:**
- Pagination tests (1st page, last page, invalid)
- Alert latency tests (<500ms)
- Load test (10K products)

**Success Criteria:**
- ✅ 26K+ products paginated
- ✅ <500ms alert latency
- ✅ Auto-reorder working
- ✅ 100% test pass
- ✅ Readiness: 6.5/10

---

### PHASE 3: INVOICING (Mar 24-Apr 3, 2 weeks)
**Owner:** Backend Lead, Frontend Lead  
**Status:** NOT STARTED  
**Effort:** 90 total hours

Professional invoicing with GST compliance.

**Features:**
- Invoice creation form
- Customer selection/creation
- Multi-item line editor
- Tax calculation (GST)
- PDF generation
- Email delivery
- Invoice archiving
- Bill tracking
- GST reconciliation

**Database Changes:**
- `invoices` table (customer, date, items, taxes, total)
- `invoice_items` table (product, qty, price, tax)
- `bills` table (vendor, date, items, GST input)

**API Endpoints:**
- POST /api/v1/invoices/create
- GET /api/v1/invoices
- GET /api/v1/invoices/{id}
- POST /api/v1/invoices/{id}/get-pdf
- POST /api/v1/invoices/{id}/send-email
- POST /api/v1/bills/create
- POST /api/v1/bills/{id}/claim-gst

**Frontend Components:**
- Invoice creation form
- Invoice list with search
- PDF preview
- GST tracking dashboard

**Tests:**
- GST calculation accuracy
- PDF generation
- Email delivery
- Bill tracking

**Success Criteria:**
- ✅ Invoices created with GST
- ✅ PDF generation <1 sec
- ✅ Email delivery confirmed
- ✅ Bills tracked
- ✅ 100% test pass
- ✅ Readiness: 7.0/10

---

### PHASE 4: ANALYTICS (Apr 7-18, 2 weeks)
**Owner:** Backend Lead, Frontend Lead  
**Status:** NOT STARTED  
**Effort:** 90 total hours

Comprehensive analytics & reporting.

**Features:**
- Sales dashboard (revenue, orders, avg transaction)
- Product analytics (top sellers, revenue by product)
- Customer analytics (top customers, segments)
- Time-based reports (daily, weekly, monthly, yearly)
- Custom date range reports
- Export to CSV/Excel
- Real-time metrics

**Database Queries:**
- Sales by day/week/month
- Top 100 products by revenue
- Top 100 customers by spend
- Customer lifetime value (CLV)

**API Endpoints:**
- GET /api/v1/analytics/sales
- GET /api/v1/analytics/products
- GET /api/v1/analytics/customers
- GET /api/v1/analytics/reports
- POST /api/v1/analytics/export

**Frontend Components:**
- Dashboard with KPI cards
- Sales trend chart
- Top products table
- Customer segmentation chart
- Export button

**Tests:**
- Report accuracy tests
- Performance tests (1000 rows)
- Export format tests

**Success Criteria:**
- ✅ Dashboards load <1 sec
- ✅ 100+ reports available
- ✅ Export working
- ✅ Real-time updates
- ✅ 100% test pass
- ✅ Readiness: 7.5/10

---

### PHASE 5: FORECASTING (Apr 21-May 2, 1.5 weeks)
**Owner:** Backend Lead  
**Status:** NOT STARTED  
**Effort:** 60 total hours

ML-powered demand forecasting.

**Features:**
- ARIMA forecasting model
- Prophet forecasting model
- Forecast by product
- Forecast by location
- Confidence intervals (80%, 95%)
- Model accuracy metrics (>85% target)
- Forecast visualization
- Reorder suggestion

**ML Models:**
- ARIMA(1,1,1) baseline
- Facebook Prophet for seasonality
- Ensemble (weighted average)
- Test data: Last 6 months sales history

**API Endpoints:**
- GET /api/v1/forecasting/forecast/:product_id
- GET /api/v1/forecasting/forecast/:product_id/:location_id
- POST /api/v1/forecasting/train-model
- GET /api/v1/forecasting/accuracy

**Frontend Components:**
- Forecast chart (historical + predicted)
- Confidence interval visualization
- Model metrics display
- Reorder recommendation

**Tests:**
- Model accuracy (>85%)
- Forecast vs actual comparison
- Performance (<2 sec response)

**Success Criteria:**
- ✅ Model accuracy >85%
- ✅ Forecasts generated <2 sec
- ✅ Confidence intervals calculated
- ✅ Reorder working
- ✅ 100% test pass
- ✅ Readiness: 8.0/10

---

### PHASE 6: ⏭️ SKIPPED - HINDI LOCALIZATION

**Originally Planned:** 1.5 weeks (Weeks 11-12.5)

**Why Removed:**
1. MVP focus on core features, not localization
2. Saves 2 weeks → go-live April 25 instead of May 9
3. Saves ₹4L budget
4. Can be added in Phase 8 (future)

**What Would Have Been Included:**
- Hindi UI translation (all pages)
- Regional languages (Tamil, Telugu, Kannada, Malayalam, Marathi)
- Localized number/date formatting
- Language switcher
- i18n framework setup

**Phase 8 Plan:**
If needed post-launch, Hindi + regional languages can be added with similar effort.

---

### PHASE 7: MOBILE APP (May 5-16, 2 weeks)
**Owner:** Frontend Lead  
**Status:** NOT STARTED  
**Effort:** 100 total hours

Native iOS & Android apps using React Native.

**Features:**
- Cross-platform React Native codebase
- POS system (barcode, cart, payment)
- Inventory check (real-time)
- Invoice viewer (PDF download)
- Sales analytics dashboard
- Account settings
- Offline mode (sync on reconnect)
- Push notifications

**Platforms:**
- iOS 14+ (TestFlight → App Store)
- Android 10+ (Internal → Play Store)

**App Store Setup:**
- iOS: Xcode, signing, App Store Connect
- Android: Gradle, Play Store Console

**Testing:**
- Device testing (iPhone 12+, Galaxy S21+)
- Offline sync validation
- Performance (<2 sec load)
- Compliance review

**Submission Timeline:**
- Week 1: Complete development, internal testing
- Week 2: Submit to App Store/Play Store
- Week 3 (post-launch): App approval, public release

**Success Criteria:**
- ✅ iOS app on App Store
- ✅ Android app on Play Store
- ✅ 4.5+/5 star rating
- ✅ 10K+ downloads by week 15
- ✅ 100% test pass
- ✅ Readiness: 8.5/10

---

## TIMELINE GANTT CHART

```
Feb 2026:
  17-20: Phase 0 (4 days) ████
  24-28: Phase 1 Week 1   ████
  Mar 3-7: Phase 1 Week 2 ████ → GATE 1

Mar 2026:
  10-14: Phase 2 Week 1   ████
  17-21: Phase 2 Week 2   ████ → GATE 2
  24-28: Phase 3 Week 1   ████
  31-04: Phase 3 Week 2   ████ → GATE 3

Apr 2026:
  7-11: Phase 4 Week 1    ████
  14-18: Phase 4 Week 2   ████ → GATE 4
  21-25: Phase 5 (1.5w)   ████ → GATE 5
  25: 🎯 GO-LIVE (Deployment week, May 5-16: Phase 7 overlaps)

May 2026:
  5-9: Phase 7 Week 1     ████
  12-16: Phase 7 Week 2   ████ → GATE 6
  19-23: Production testing, fixes
  26: Post-launch monitoring

Total: 16.5 weeks (2 weeks saved!)
```

---

## BUDGET BREAKDOWN

**Total Budget:** ₹32L (16.5 weeks)

### Personnel (₹22L)
- Backend Lead (16.5 weeks @ ₹1L/week): ₹1.65L
- Backend Engineer #2 (16.5 weeks): ₹1.65L
- Frontend Lead (16.5 weeks): ₹1.65L
- Frontend Engineer #2 (16.5 weeks): ₹1.65L
- DevOps Engineer (16.5 weeks): ₹1.2L
- QA Lead (16.5 weeks): ₹1.2L
- QA Engineer #2 (16.5 weeks): ₹1.2L
- Product Lead (16.5 weeks): ₹1.2L
- **Subtotal:** ₹14.4L
- **Contingency (overruns):** ₹7.6L
- **Total Personnel:** ₹22L

### Infrastructure & Services (₹6L)
- AWS RDS PostgreSQL (16.5 weeks @ ₹85K/week): ₹1.4L
- AWS EC2 instances (16.5 weeks): ₹1.4L
- CloudFront CDN (16.5 weeks): ₹0.4L
- Monitoring (Datadog/New Relic): ₹0.9L
- Dev tools (GitHub Pro, Figma): ₹0.5L
- Testing tools (LoadRunner, ApacheBench): ₹0.5L
- **Total Infrastructure:** ₹6L

### Third-Party APIs (₹2L)
- Razorpay (payment processing): ₹0.7L
- SendGrid (email delivery): ₹0.4L
- WATI (WhatsApp integration): ₹0.6L
- Weather API (if used): ₹0.2L
- Twilio (SMS backup): ₹0.1L
- **Total APIs:** ₹2L

### Tools & Services (₹1L)
- Cloud storage backup: ₹0.3L
- Monitoring & logging: ₹0.4L
- Documentation tools: ₹0.3L
- **Total Tools:** ₹1L

### Contingency (₹1L)
- Unforeseen expenses, emergency hiring, scope changes: ₹1L

**GRAND TOTAL:** ₹32L

**Budget Savings vs Original:**
- Original: ₹36L (18 weeks)
- Updated: ₹32L (16.5 weeks)
- **Saved: ₹4L (11% reduction)**

---

## SUCCESS METRICS

### Phase 0 Success
- ✅ PostgreSQL operational (0 downtime)
- ✅ All 37 endpoints passing (100%)
- ✅ Load test: 100 users, <200ms, 0% error
- ✅ No hardcoded URLs (grep returns 0)
- ✅ Crashes fixed (pagination working with 26K products)
- ✅ Readiness: 5.2/10

### Phase 1 Success
- ✅ POS transactions: 50+ per day
- ✅ <2 second checkout
- ✅ Barcode scanning accuracy: 99%
- ✅ Receipt printing: 100% success
- ✅ WhatsApp delivery: 95%+ success
- ✅ Readiness: 6.0/10

### Phase 2 Success
- ✅ 26K+ products paginated
- ✅ Alert latency: <500ms
- ✅ Auto-reorder working
- ✅ Readiness: 6.5/10

### Phase 3 Success
- ✅ Invoices with GST: 100% accurate
- ✅ PDF generation: <1 sec
- ✅ Email delivery: 99% success
- ✅ Readiness: 7.0/10

### Phase 4 Success
- ✅ Dashboards: <1 sec load
- ✅ 100+ reports available
- ✅ Export functionality working
- ✅ Real-time updates
- ✅ Readiness: 7.5/10

### Phase 5 Success
- ✅ Model accuracy: >85%
- ✅ Forecasts: <2 sec
- ✅ Reorder suggestions: 90%+ accuracy
- ✅ Readiness: 8.0/10

### Phase 7 Success
- ✅ iOS app: App Store published
- ✅ Android app: Play Store published
- ✅ Rating: 4.5+/5 stars
- ✅ Downloads: 10K+ by week 15
- ✅ Readiness: 8.5/10

### Overall Success
- ✅ Go-live: April 25, 2026 (2 weeks earlier!)
- ✅ 1000+ retailers by day 90
- ✅ ₹6M annual revenue projection
- ✅ 99.9%+ system uptime
- ✅ Zero critical production incidents

---

## DECISION GATES

### GATE 1: Phase 0 (Feb 20)
**Approval Required:** 10 criteria
- [ ] Tech Lead ___________
- [ ] Backend Lead ___________
- [ ] Frontend Lead ___________
- [ ] DevOps ___________
- [ ] QA Lead ___________

**Decision:** APPROVE → Phase 1 starts Feb 24

### GATE 2: Phase 1 (Mar 6)
**Approval Required:** 10 criteria
- [ ] Tech Lead
- [ ] QA Lead
- [ ] Product Lead

**Decision:** APPROVE → Phase 2 starts Mar 10

### GATE 3: Phase 2 (Mar 20)
### GATE 4: Phase 3 (Apr 3)
### GATE 5: Phase 4 (Apr 18)
### GATE 6: Phase 5 (May 2)
### GATE 7: Phase 7 (May 16)
### GATE 8: Production Go-Live (Apr 25)

---

## KEY DIFFERENCES FROM ORIGINAL PLAN

| Aspect | Original | Updated | Impact |
|--------|----------|---------|--------|
| **Go-Live Date** | May 9 | April 25 | +2 weeks acceleration |
| **Total Duration** | 18 weeks | 16.5 weeks | -1.5 weeks |
| **Budget** | ₹36L | ₹32L | -₹4L savings |
| **Phase 6** | Hindi localization | SKIPPED | Removed from MVP |
| **Phases** | 0-7 (8 phases) | 0-5, 7 (7 phases) | Combined structure |
| **Personnel** | ₹24L | ₹22L | -₹2L |
| **Readiness Target** | 8.5/10 | 8.5/10 | Same endpoint |
| **Revenue Target** | ₹6M | ₹6M | Same revenue |

---

## NEXT STEPS

✅ **This Week (Feb 14):**
- [x] Create accelerated roadmap (DONE)
- [ ] CEO approves plan
- [ ] Notify team of timeline change

✅ **Next Week (Feb 17):**
- [ ] Phase 0 starts Monday 9 AM
- [ ] Set up GitHub project
- [ ] Daily standups (4:00 PM)
- [ ] Assign all 10 Phase 0 tasks

✅ **Feb 20 (Gate 1):**
- [ ] Phase 0 gate review
- [ ] Decision: APPROVE or REJECT
- [ ] If approved → Phase 1 kicks off Feb 24

✅ **Apr 25 (Go-Live!):**
- [ ] Production deployment
- [ ] DNS cutover
- [ ] Monitoring setup (24/7)

✅ **May 9+ (Post-Launch):**
- [ ] 30-day stabilization
- [ ] Onboard 100+ retailers
- [ ] Phase 8 planning (localization, features)

---

**ACCELERATED ROADMAP - READY FOR EXECUTION**  
*Updated: Feb 14, 2026*  
*Status: 🟢 APPROVED FOR IMMEDIATE START*  
*Next: Team reviews Monday morning, Phase 0 begins immediately*
