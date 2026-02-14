# Task 1.4: API Testing with PostgreSQL
**Owner:** QA Lead  
**Duration:** 6 hours  
**Deadline:** Feb 19, 9:00 AM IST  
**Priority:** 🔴 CRITICAL (Go/No-Go gate)  
**Phase:** Phase 0 - Critical Blockers  
**Depends On:** #1.3 Data Migration

---

## Description

Test 49 verified API endpoints against PostgreSQL database. Verify inventory loading, sales queries, and pagination work correctly with 424K+ records.

## Acceptance Criteria

- [ ] All 49 endpoints tested against PostgreSQL
- [ ] Load test: 100 concurrent users, < 200ms p95 response time
- [ ] Inventory endpoint: Loads all 26K products with pagination
- [ ] Pagination: All 528 pages load successfully
- [ ] Sales queries: < 500ms for date ranges
- [ ] Zero crashes on any endpoint
- [ ] Database connection stable over 1-hour load test
- [ ] Test report generated

## API Endpoints to Test

### Inventory Endpoints (Critical)
- [ ] `GET /api/v1/inventory/list` - List all products (pagination)
- [ ] `GET /api/v1/inventory/{id}` - Get single product
- [ ] `GET /api/v1/inventory/search?q=...` - Search products
- [ ] `GET /api/v1/inventory/category/{category}` - Filter by category
- [ ] `GET /api/v1/inventory/low-stock` - Low stock alerts

### Sales Endpoints
- [ ] `GET /api/v1/sales/list` - List sales (pagination)
- [ ] `POST /api/v1/sales` - Create sale
- [ ] `GET /api/v1/sales/{id}` - Get sale details
- [ ] `GET /api/v1/sales/reports/daily` - Daily sales report

### Customer Endpoints
- [ ] `GET /api/v1/customers/list` - List customers
- [ ] `POST /api/v1/customers` - Create customer
- [ ] `GET /api/v1/customers/{id}` - Get customer

...and 36 more endpoints

## Test Plan

### Step 1: Smoke Test (30 minutes)
```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

endpoints = [
    "GET /inventory/list",
    "GET /sales/list",
    "GET /customers/list",
    "POST /sales"
]

for method, endpoint in endpoints:
    if method == "GET":
        response = requests.get(f"{BASE_URL}{endpoint}")
    else:
        response = requests.post(f"{BASE_URL}{endpoint}", json={})
    
    status = "✅" if response.status_code < 400 else "❌"
    print(f"{status} {method} {endpoint}: {response.status_code}")
```

### Step 2: Pagination Test (1 hour)
```python
# Test all 528 pages of inventory
for page in range(1, 529):
    response = requests.get(
        f"{BASE_URL}/inventory/list?page={page}&limit=50"
    )
    assert response.status_code == 200
    assert len(response.json()['data']) > 0
    
    if page % 100 == 0:
        print(f"✅ Tested {page}/528 pages")
```

### Step 3: Load Test (1 hour)
```bash
# Apache Bench: 100 concurrent users
ab -n 10000 -c 100 http://localhost:8000/api/v1/inventory/list

# Expected results:
# Requests per second: 1000+
# Failed requests: 0
# Requests per second: 1000+
```

### Step 4: Database Stability Test (1 hour)
```python
# Run 10000 requests over 60 minutes
import time

start_time = time.time()
error_count = 0
success_count = 0

while time.time() - start_time < 3600:
    try:
        response = requests.get(f"{BASE_URL}/inventory/list")
        if response.status_code == 200:
            success_count += 1
    except Exception as e:
        error_count += 1
    
    time.sleep(0.36)  # ~10000 requests/hour

print(f"✅ Success: {success_count}")
print(f"❌ Errors: {error_count}")
print(f"Error rate: {error_count/success_count*100:.2f}%")
```

## Expected Results

| Metric | Target | Actual |
|--------|--------|--------|
| API response time (p95) | < 200ms | ??? |
| Concurrent users | 100+ | ??? |
| Throughput | 1000+ req/s | ??? |
| Error rate | < 0.1% | ??? |
| Database stability | 1+ hours | ??? |

## Related Issues
- #1.3 Data Migration
- #2.1 Environment Configuration
- #3.1 Pagination Implementation

## Test Files
- [ ] `test_scripts/test_49_endpoints.py` - Endpoint tests
- [ ] `test_scripts/test_pagination.py` - Pagination tests
- [ ] `test_scripts/load_test.sh` - Load testing commands
- [ ] `test_scripts/database_stability_test.py` - 1-hour stability test

## Definition of Done
✅ All 49 endpoints respond with status 200  
✅ Load test: 100 concurrent users, p95 < 200ms  
✅ Pagination: 528 pages load successfully  
✅ Zero crashes or database connection errors  
✅ Test report with metrics generated  
✅ Ready for Go/No-Go gate approval
