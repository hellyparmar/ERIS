# Phase 5 Setup Guide
## External Factors + Celery + Monitoring

**Created**: January 20, 2026  
**Time**: 12:30 AM  
**Status**: Foundation Ready - Full Implementation Over 2 Weeks

---

## 🎯 What's Been Set Up

### 1. Phase 5: External Factors (Foundation) ✅

**Database Models** (`api/db/external_factors_models.py`):
- `ExternalFactor` - Daily consolidated factors
- `EconomicIndicatorHistory` - RBI data (repo rate, inflation, gold, etc)
- `WeatherHistory` - Hourly weather readings
- `HolidayCalendar` - Indian festivals & national holidays

**Celery Tasks** (`api/tasks/external_factors.py`):
- `sync_daily_factors` - Runs 1 AM daily
- `sync_weather` - Runs every hour
- `backfill_historical` - For loading historical data

**Data Sources** (Placeholders - TO IMPLEMENT):
- RBI API for economic indicators
- OpenWeatherMap for weather
- Indian holiday calendar

### 2. Celery Workers (Configuration) ✅

**Config** (`api/celery_app.py`):
- Broker: Redis
- Scheduled tasks configured
- Auto-discovery enabled

**Task Modules**:
- `api/tasks/external_factors.py` - Weather, economy, holidays
- `api/tasks/invoices.py` - PDF generation, reminders
- `api/tasks/__init__.py` - Package init

**Scheduled Jobs**:
- Daily: External factors sync, overdue marking, payment reminders
- Hourly: Weather updates
- Weekly: Reports, cache cleanup

### 3. Monitoring Dashboard ✅

**Router** (`api/routers/monitoring.py`):
- `/monitoring/metrics/prometheus` - Prometheus format
- `/monitoring/dashboard/stats` - JSON stats
- `/monitoring/dashboard/trends` - Trend data

**Metrics Exposed**:
- Invoice counts (total, paid, overdue)
- Message counts (total, unread)
- Community listings
- WhatsApp costs & budget
- Cache hit rates

---

## 📦 Installation Requirements

### Update requirements.txt
```bash
# Add to requirements.txt
celery==5.3.4
redis==5.0.1
flower==2.0.1  # Celery monitoring UI
requests==2.31.0  # For API calls
holidays==0.35  # Indian holidays
```

### Install
```bash
pip install celery redis flower requests holidays
```

---

## 🚀 Running Celery

### 1. Start Redis (Required for Celery)
```bash
# Install Redis
sudo apt install redis-server

# Or use Docker
docker run -d -p 6379:6379 redis:7-alpine

# Verify
redis-cli ping  # Should return PONG
```

### 2. Start Celery Worker
```bash
cd /home/petpooja/Enterprise\ Retail\ Intelligence\ System

# Start worker
celery -A api.celery_app worker --loglevel=info

# With multiple workers (for production)
celery -A api.celery_app worker --loglevel=info --concurrency=4
```

### 3. Start Celery Beat (Scheduler)
```bash
# In a separate terminal
celery -A api.celery_app beat --loglevel=info
```

### 4. Start Flower (Monitoring UI - Optional)
```bash
# In another terminal
celery -A api.celery_app flower

# Access at http://localhost:5555
```

---

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Redis (Celery)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Redis (Cache)
REDIS_ENABLED=true
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=1  # Different DB than Celery

# External API Keys (TO GET)
OPENWEATHER_API_KEY=your_key_here  # Get from openweathermap.org
RBI_API_KEY=optional  # If RBI provides API

# Email (for fallback)
EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
FROM_EMAIL=noreply@rdios.com
FROM_NAME=R-DIOS
```

---

## 📊 Using the Monitoring Dashboard

### Prometheus Metrics
```bash
# Get metrics
curl http://localhost:8000/monitoring/metrics/prometheus

# Returns:
# rdios_invoices_total 150
# rdios_invoices_paid 100
# rdios_whatsapp_cost_today 245.50
# etc.
```

### Dashboard Stats (JSON)
```bash
curl http://localhost:8000/monitoring/dashboard/stats

# Returns comprehensive system stats
```

### Grafana Setup (Optional - Weekend)
```bash
# 1. Install Grafana
docker run -d -p 3000:3000 grafana/grafana

# 2. Add Prometheus datasource
# - Point to http://localhost:8000/monitoring/metrics/prometheus

# 3. Create dashboard with queries:
# - Graph: rdios_invoices_total
# - Graph: rdios_whatsapp_cost_today
# - Alert: rdios_invoices_overdue > 10
```

---

## ✅ Testing Celery Tasks

### Manual Task Execution
```python
# In Python shell
from api.celery_app import celery_app
from api.tasks.external_factors import sync_daily_factors, sync_weather
from api.tasks.invoices import mark_overdue_invoices, generate_pdf_async

# Run tasks immediately (async)
result = sync_weather.delay()
print(result.get(timeout=10))

# Run scheduled task manually
mark_overdue_invoices.delay()

# Generate PDF for invoice 1
generate_pdf_async.delay(invoice_id=1)
```

### Check Task Status 
```bash
# List all registered tasks
celery -A api.celery_app inspect registered

# Active tasks
celery -A api.celery_app inspect active

# Scheduled tasks (beat)
celery -A api.celery_app inspect scheduled
```

---

## 📋 Next Steps (Full Implementation - 2 Weeks)

### Week 1: External Factors
- [ ] Get OpenWeatherMap API key (free tier: 1000 calls/day)
- [ ] Implement RBI data scraping (no official API, use web scraping)
- [ ] Load Indian holidays library
- [ ] Run database migration to add external_factors tables
- [ ] Backfill historical data (past 2 years)
- [ ] Test daily sync job

### Week 2: Celery & Monitoring
- [ ] Migrate PDF generation to async (use celery task)
- [ ] Implement bulk reminder sending via Celery
- [ ] Setup Supervisor for Celery workers (production)
- [ ] Create Grafana dashboard
- [ ] Setup alerts (Slack/Email when issues occur)
- [ ] Load testing with async tasks

---

## 🎯 Quick Wins Available NOW

### 1. Test Monitoring Dashboard
```bash
# Check it works
curl http://localhost:8000/monitoring/dashboard/stats | jq

# See Prometheus metrics
curl http://localhost:8000/monitoring/metrics/prometheus
```

### 2. Manual Weather Sync (Mock Data)
```bash
# Run in Python
from api.tasks.external_factors import sync_weather
result = sync_weather()
print(result)
```

### 3. View Celery Registered Tasks
```bash
# After starting worker
celery -A api.celery_app inspect registered
```

---

## 📈 Expected Benefits

**External Factors**:
- Understand weather → sales correlation
- Track economic impact on retail
- Festival season forecasting

**Celery Workers**:
- Non-blocking API responses
- Scalable async processing
- Scheduled automation

**Monitoring**:
- Real-time system health
- Proactive issue detection
- Business KPI tracking

---

##🔥 What's Production-Ready

**NOW**:
- Database models defined ✅
- Celery configuration complete ✅
- Scheduled tasks configured ✅
- Monitoring endpoints live ✅

**NEEDS WORK** (2 weeks):
- External API integrations
- Historical data backfill
- Celery worker deployment (Supervisor)
- Grafana dashboard creation

---

**Status**: Foundation complete, ready for full implementation!  
**Time Investment**: 30 minutes setup tonight  
**Next Session**: Implement APIs & backfill data (2-3 hours)
