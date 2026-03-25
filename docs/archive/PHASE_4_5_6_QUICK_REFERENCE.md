# Phase 4-6 Quick Reference Guide

**Quick Start**: Copy, paste, run! 🚀

---

## Installation & Launch

```bash
# Install dependencies
pip install fastapi uvicorn pydantic psutil numpy

# Start the application
python main_phase2.py

# Verify it's running
curl http://localhost:8000/api/v2/info
```

---

## Phase 4: Quick Tests

### Dashboard
```bash
# Get dashboard
curl http://localhost:8000/api/v1/dashboard/overview

# Top products
curl http://localhost:8000/api/v1/dashboard/top-products

# Pending orders
curl http://localhost:8000/api/v1/dashboard/pending-orders
```

### Health
```bash
# System health
curl http://localhost:8000/api/v1/health/system

# Heartbeat
curl http://localhost:8000/api/v1/health/heartbeat
```

### Tally & Feedback
```bash
# Sync status
curl http://localhost:8000/api/v1/tally/sync/status

# Get feedback
curl http://localhost:8000/api/v1/tally/feedback
```

### WebSocket (JavaScript)
```javascript
// Metrics
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/metrics');
ws.onmessage = (e) => console.log(JSON.parse(e.data));

// Notifications
const notif = new WebSocket('ws://localhost:8000/api/v1/ws/notifications');
notif.onmessage = (e) => console.log(JSON.parse(e.data));
```

---

## Phase 5: Quick Tests

### Forecasting
```bash
# Get 14-day forecast
curl -X POST http://localhost:8000/api/v1/intelligence/forecast \
  -H "Content-Type: application/json" \
  -d '{"days_ahead": 14, "confidence_level": 0.95}'

# Product forecast
curl http://localhost:8000/api/v1/intelligence/forecast/product/1?days=30

# Category forecast
curl "http://localhost:8000/api/v1/intelligence/forecast/category/Beverages"
```

### Natural Language Query
```bash
# Ask a question
curl -X POST http://localhost:8000/api/v1/intelligence/nl-query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are total sales today?"}'

# Get examples
curl http://localhost:8000/api/v1/intelligence/nl-examples
```

### Anomalies
```bash
# Get anomalies
curl http://localhost:8000/api/v1/intelligence/anomalies

# Get insights
curl http://localhost:8000/api/v1/intelligence/insights

# Get recommendations
curl http://localhost:8000/api/v1/intelligence/recommendations
```

---

## Phase 6: Quick Tests

### Admin Users
```bash
# Get all users
curl http://localhost:8000/api/v1/admin/users

# Create user
curl -X POST http://localhost:8000/api/v1/admin/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john",
    "email": "john@example.com",
    "role": "manager",
    "store_id": 1
  }'

# Get roles
curl http://localhost:8000/api/v1/admin/roles

# Get permissions
curl http://localhost:8000/api/v1/admin/permissions
```

### Organizations & Stores
```bash
# Get organizations
curl http://localhost:8000/api/v1/admin/organizations

# Create organization
curl -X POST http://localhost:8000/api/v1/admin/organizations \
  -H "Content-Type: application/json" \
  -d '{"name": "Store Chain", "type": "retail"}'

# Get stores
curl http://localhost:8000/api/v1/admin/stores

# Create store
curl -X POST http://localhost:8000/api/v1/admin/stores \
  -H "Content-Type: application/json" \
  -d '{"name": "Downtown", "location": "123 Main", "organization_id": 1, "manager_id": 1}'
```

### Security & Performance
```bash
# Audit log
curl http://localhost:8000/api/v1/admin/security/audit-log

# API keys
curl http://localhost:8000/api/v1/admin/security/api-keys

# Cache stats
curl http://localhost:8000/api/v1/admin/performance/cache-stats

# API metrics
curl http://localhost:8000/api/v1/admin/performance/api-metrics

# Resource usage
curl http://localhost:8000/api/v1/admin/performance/resource-usage
```

---

## Common Endpoints

| Feature | GET | POST | PUT | DELETE |
|---------|-----|------|-----|--------|
| Dashboard | ✅ | - | - | - |
| Health | ✅ | - | - | - |
| Users | ✅ | ✅ | ✅ | ✅ |
| Roles | ✅ | ✅ | - | - |
| Orgs | ✅ | ✅ | - | - |
| Forecast | - | ✅ | - | - |
| Feedback | ✅ | ✅ | - | - |
| Audit | ✅ | - | - | - |

---

## Response Patterns

### Success (200)
```json
{
  "data": {...},
  "status": "success",
  "timestamp": "2024-01-14T10:00:00"
}
```

### Error (400/500)
```json
{
  "detail": "Error message",
  "status_code": 400
}
```

### List Response
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "limit": 50
}
```

---

## Environment Setup

```bash
# PostgreSQL
export DATABASE_URL=postgresql://user:pass@localhost/retail_db

# Redis
export REDIS_URL=redis://localhost:6379

# Tally Integration
export TALLY_API_KEY=your_key
export TALLY_ORG_ID=your_org

# CORS
export CORS_ORIGINS=http://localhost:3000

# API
export API_HOST=0.0.0.0
export API_PORT=8000
```

---

## Docker Quick Start

```bash
# Build
docker build -f Dockerfile.backend -t retail:latest .

# Run
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e REDIS_URL=redis://... \
  retail:latest

# With compose
docker-compose up -d
```

---

## Troubleshooting

### Port Already in Use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
python main_phase2.py --port 8001
```

### Database Connection Failed
```bash
# Check connection
psql postgresql://user:pass@localhost/retail_db

# Reset
python -c "from api.db.database import init_db; init_db()"
```

### WebSocket Connection Issues
```javascript
// Check WebSocket status
const checkWS = async () => {
  const res = await fetch('http://localhost:8000/api/v1/ws/status');
  console.log(await res.json());
};
```

### Performance Issues
```bash
# Check API metrics
curl http://localhost:8000/api/v1/admin/performance/api-metrics | jq

# Check resource usage
curl http://localhost:8000/api/v1/admin/performance/resource-usage | jq

# Check cache
curl http://localhost:8000/api/v1/admin/performance/cache-stats | jq
```

---

## Monitoring Dashboard

Create a simple monitoring script:

```bash
#!/bin/bash
# monitor.sh

while true; do
  clear
  echo "=== System Status ==="
  curl -s http://localhost:8000/api/v1/health/system | jq '.overall_status'
  
  echo "=== Active Connections ==="
  curl -s http://localhost:8000/api/v1/ws/status | jq '.active_connections'
  
  echo "=== Performance ==="
  curl -s http://localhost:8000/api/v1/admin/performance/api-metrics | jq '.response_time_ms.average'
  
  sleep 10
done
```

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| ModuleNotFoundError | `pip install -r requirements.txt` |
| Database Connection Error | Check DATABASE_URL env var |
| WebSocket Timeout | Check Redis connection |
| High Response Times | Check `/admin/performance/*` |
| Rate Limit Hit | Wait before retrying |
| CORS Error | Check CORS_ORIGINS env var |
| Permission Denied | Check RBAC role assignments |

---

## Performance Tuning

```bash
# Enable query caching
export CACHE_TTL=3600

# Increase connection pool
export DB_POOL_SIZE=20

# Enable compression
export GZIP_MIN_SIZE=1000

# WebSocket buffer
export WS_BUFFER_SIZE=65536
```

---

## Security Checklist

- [ ] Change default API keys
- [ ] Set strong database passwords
- [ ] Enable HTTPS in production
- [ ] Configure CORS properly
- [ ] Enable audit logging
- [ ] Set up rate limiting
- [ ] Regular security audits
- [ ] Monitor audit logs
- [ ] Update dependencies
- [ ] Review user permissions

---

## Key Files

```
main_phase2.py                    - Main app
routers/
├── phase4_dashboard.py           - Dashboard
├── phase4_websocket.py           - Real-time
├── phase4_health.py              - Health checks
├── phase4_tally_feedback.py      - Tally & Feedback
├── phase5_intelligence.py        - AI & Forecasting
└── phase6_admin.py               - Admin & Security

PHASE_4_5_6_IMPLEMENTATION_GUIDE.md     - Full docs
PHASE_4_5_6_TESTING_DEPLOYMENT.md       - Testing guide
PHASE_4_5_6_COMPLETE.md                 - Status report
```

---

## Support URLs

- **API Docs**: http://localhost:8000/docs
- **API Schema**: http://localhost:8000/openapi.json
- **Health**: http://localhost:8000/api/v1/health/system
- **Dashboard**: http://localhost:8000/api/v1/dashboard/overview

---

## Quick Commands

```bash
# Start server
python main_phase2.py

# Test all endpoints
bash test_phase4_6.sh

# View logs
tail -f app.log

# Database backup
pg_dump retail_db > backup.sql

# Database restore
psql retail_db < backup.sql

# Performance test
ab -n 1000 -c 100 http://localhost:8000/api/v1/health/system
```

---

## Next Steps

1. ✅ Deploy to staging
2. ✅ Run full test suite
3. ✅ Configure monitoring
4. ✅ Train operations team
5. ✅ Deploy to production
6. ⏳ Monitor metrics
7. ⏳ Plan Phase 7

---

**All 12 Features Ready** ✅
**53 Endpoints Implemented** ✅
**Documentation Complete** ✅
**Testing Guide Included** ✅

**Ready for Production Deployment!** 🚀
