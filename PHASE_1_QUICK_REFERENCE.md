# Phase 1 Quick Reference Guide

## 🚀 Getting Started

### Start the Application
```bash
# Backend
cd /home/petpooja/Enterprise\ Retail\ Intelligence\ System
uvicorn api.main:app --reload

# Frontend
npm run dev

# Redis (in another terminal)
redis-server
```

### Check API Health
```bash
curl http://localhost:8000/health
# Response: {"status": "healthy", "version": "3.0.0"}
```

---

## 👥 Authentication

### Manager Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "manager", "password": "password"}'

# Response:
# {
#   "success": true,
#   "data": {
#     "access_token": "eyJ0eXAi...",
#     "refresh_token": "eyJ0eXAi...",
#     "expires_in": 3600,
#     "role": "manager"
#   }
# }
```

### Cashier Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/pos-login \
  -H "Content-Type: application/json" \
  -d '{"employee_id": 1, "pin": "1234"}'

# Response: 
# {
#   "success": true,
#   "data": {
#     "pos_token": "eyJ0eXAi...",
#     "expires_in": 28800,
#     "role": "cashier"
#   }
# }
```

---

## 💰 Manager Override

### Request Discount Approval (₹500+)
```bash
curl -X POST http://localhost:8000/api/v1/pos/override/request-discount \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <pos_token>" \
  -d '{
    "sale_id": 123,
    "discount_amount": 600,
    "discount_reason": "Customer loyalty",
    "manager_id": 1,
    "manager_pin": "1234"
  }'
```

### Request Refund Approval (₹1000+)
```bash
curl -X POST http://localhost:8000/api/v1/pos/override/request-refund \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <pos_token>" \
  -d '{
    "sale_id": 123,
    "refund_amount": 1200,
    "reason": "Defective item",
    "manager_id": 1,
    "manager_pin": "1234"
  }'
```

---

## 📊 Day Close Operations

### Open Register
```bash
curl -X POST http://localhost:8000/api/v1/pos/day/open \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "opening_float": 5000,
    "notes": "Start of day"
  }'
```

### Check Day Status
```bash
curl -X GET http://localhost:8000/api/v1/pos/day/status \
  -H "Authorization: Bearer <access_token>"

# Response:
# {
#   "success": true,
#   "data": {
#     "status": "open",
#     "date": "2026-02-17",
#     "opening_float": 5000,
#     "opened_at": "2026-02-17T10:00:00",
#     "closed_at": null,
#     "closing_float": null,
#     "variance": null,
#     "reconciliation_status": null
#   }
# }
```

### Close Register
```bash
curl -X POST http://localhost:8000/api/v1/pos/day/close \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{
    "physical_cash_count": 12500,
    "cheques_count": 0,
    "notes": "End of day reconciliation"
  }'

# Response:
# {
#   "success": true,
#   "data": {
#     "day_close_id": 1,
#     "date": "2026-02-17",
#     "opening_float": 5000,
#     "closing_float": 12500,
#     "expected_cash": 12300,
#     "physical_cash": 12500,
#     "variance": 200,
#     "variance_percent": 1.63,
#     "reconciliation_status": "small_variance",
#     "sales_summary": {
#       "transaction_count": 45,
#       "total_sales": 7300,
#       "cash_sales": 7300,
#       "upi_sales": 0,
#       "card_sales": 0,
#       "khata_sales": 0
#     }
#   }
# }
```

---

## 🌐 Offline Queue (Frontend)

### Import Service
```typescript
import { offlineQueueService } from '@/services/offlineQueueService';
```

### Queue a Transaction
```typescript
const transactionId = await offlineQueueService.queueTransaction({
  timestamp: Date.now(),
  type: 'sale',
  items: [
    {
      product_id: 1,
      product_name: 'Paneer Tikka',
      quantity: 2,
      unit_price: 300,
      total_price: 600,
      gst_amount: 90
    }
  ],
  total_amount: 690,
  payment_method: 'cash',
  customer_id: 123
});
```

### Get Queue Statistics
```typescript
const stats = await offlineQueueService.getQueueStats();
console.log(stats);
// {pending: 5, failed: 0, total: 5}
```

### Manual Sync
```typescript
const result = await offlineQueueService.manualSync();
console.log(result);
// {
//   success: true,
//   synced: [...],
//   failed: [],
//   errors: []
// }
```

---

## ⚙️ Configuration

### Environment Variables
```bash
# Authentication
JWT_SECRET_KEY=your_secret_key_here
POS_JWT_SECRET_KEY=your_pos_secret_key_here

# Database
DATABASE_URL=postgresql://user:password@localhost:5433/enterprise_retail_db

# Redis
REDIS_URL=redis://localhost:6379/0

# WhatsApp (MSG91)
MSG91_API_KEY=your_msg91_api_key
MSG91_SENDER_ID=R-DIOS

# Frontend
VITE_API_URL=http://localhost:8000

# Logging
LOG_LEVEL=INFO
```

---

## 🔍 Monitoring

### Check Circuit Breaker Status
```python
from api.services.whatsapp_service import get_circuit_status

status = get_circuit_status()
print(status)
# {
#   "operational": true,
#   "failures": 0,
#   "circuit_open": false,
#   "circuit_break_time": null
# }
```

### View API Routes
```bash
curl http://localhost:8000/openapi.json | jq '.paths | keys'
```

### Check Database Connection
```python
from api.db import engine
from sqlalchemy import inspect

inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"Database tables: {len(tables)}")
print(tables)
```

---

## 🐛 Debugging

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Offline Queue (IndexedDB)
```javascript
// In browser console
db = await new Promise((r) => {
  let req = indexedDB.open('rdios_offline', 1);
  req.onsuccess = () => r(req.result);
});

store = db.transaction(['transactions']).objectStore('transactions');
store.getAll().onsuccess = e => console.log(e.target.result);
```

### Test WhatsApp API
```python
from api.services.whatsapp_service import send_via_msg91

result = send_via_msg91(
    phone="+919876543210",
    message="Test message"
)
print(result)
```

---

## 📊 Common Queries

### Get Today's Sales
```sql
SELECT SUM(total_amount) as total, COUNT(*) as count
FROM sales
WHERE DATE(created_at) = CURRENT_DATE
AND status = 'completed';
```

### Get Override History
```sql
SELECT * FROM manager_overrides
WHERE DATE(created_at) = CURRENT_DATE
ORDER BY created_at DESC;
```

### Get Audit Log
```sql
SELECT * FROM audit_logs
WHERE DATE(created_at) = CURRENT_DATE
AND action LIKE '%override%'
ORDER BY created_at DESC;
```

---

## 🚨 Troubleshooting

### WhatsApp Not Sending
1. Check circuit breaker: `get_circuit_status()`
2. Verify MSG91_API_KEY is set
3. Check phone number format (must be 91XXXXXXXXXX)
4. Check logs for MSG91 API errors

### Offline Queue Not Syncing
1. Verify network connectivity
2. Check auth token validity
3. Check IndexedDB in browser DevTools
4. Manual sync: `offlineQueueService.manualSync()`

### Token Expired
- Manager: Re-login (1h expiry)
- Cashier: Use pos-login for new token (8h expiry)
- Use refresh endpoint for new access token

### Database Connection Issues
1. Verify PostgreSQL is running: `psql -U postgres`
2. Check DATABASE_URL in .env
3. Check connection pool settings in api/db/__init__.py

---

## 📚 API Documentation

Full API documentation available at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

---

## 🔗 Related Documentation

- [Phase 1 Completion Report](PHASE_1_COMPLETION_REPORT.md)
- [CLAUDE.md - Implementation Requirements](CLAUDE.md)
- [Database Integration Guide](DATABASE_INTEGRATION_COMPLETE_INDEX.md)
- [Auth Implementation Guide](AUTH_IMPLEMENTATION_GUIDE.md)

---

**Last Updated:** February 17, 2026  
**Phase:** 1 Complete  
**Status:** Ready for Production Testing ✅
