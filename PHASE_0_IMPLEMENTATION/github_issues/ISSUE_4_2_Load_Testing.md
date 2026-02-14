# Task 4.2: Load Testing & Performance Validation
**Owner:** QA Lead  
**Duration:** 4 hours  
**Deadline:** Feb 19, 6:00 PM IST  
**Priority:** 🟡 HIGH (Go/No-Go gate requirement)  
**Phase:** Phase 0 - Critical Blockers  
**Depends On:** #1.4 API Testing

---

## Description

Execute load testing to verify system handles 100 concurrent users with < 200ms response time (p95). Validate database and API performance before production deployment.

## Acceptance Criteria

- [ ] Load test: 100 concurrent users
- [ ] Target response time: < 200ms (p95)
- [ ] Error rate: < 0.1%
- [ ] Database connections stable
- [ ] Memory usage < 500MB
- [ ] CPU usage < 80%
- [ ] No crashes or timeouts
- [ ] Report generated with metrics

## Load Test Scenarios

### Scenario 1: Inventory Browsing (30% of traffic)
```
GET /api/v1/inventory/list?limit=50&offset=X
- 30 concurrent users
- Varying page numbers (1-528)
- Duration: 10 minutes
- Target: < 200ms
```

### Scenario 2: Sales Operations (40% of traffic)
```
GET /api/v1/sales/list
POST /api/v1/sales
- 40 concurrent users
- Create + read operations
- Duration: 10 minutes
- Target: < 300ms average
```

### Scenario 3: Reporting Queries (30% of traffic)
```
GET /api/v1/sales/reports/daily?start_date=...&end_date=...
- 30 concurrent users
- Complex date-range queries
- Duration: 10 minutes
- Target: < 500ms
```

## Load Testing Tools

### Apache Bench (Simple)
```bash
# Single URL test
ab -n 10000 -c 100 http://localhost:8000/api/v1/inventory/list

# Expected output:
# Concurrency Level:      100
# Time taken for tests:    10.234 seconds
# Complete requests:       10000
# Failed requests:         0
# Requests per second:     977 [#/sec]
# Time per request:        102.34 [ms] (mean)
# Time per request:        1.02 [ms] (mean, across all concurrent requests)
```

### Locust (Advanced - Recommended)
```bash
pip install locust
```

Create `locustfile.py`:
```python
from locust import HttpUser, task, between
import random

class InventoryUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def browse_inventory(self):
        """30% of traffic - browse pages"""
        page = random.randint(1, 528)
        offset = (page - 1) * 50
        self.client.get(f"/api/v1/inventory/list?limit=50&offset={offset}")
    
    @task(4)
    def sales_operations(self):
        """40% of traffic - sales"""
        self.client.get("/api/v1/sales/list")
        self.client.post("/api/v1/sales", json={
            "customer_id": random.randint(1, 1000),
            "items": [{"product_id": random.randint(1, 26420), "quantity": 1}]
        })
    
    @task(3)
    def run_reports(self):
        """30% of traffic - reports"""
        self.client.get("/api/v1/sales/reports/daily?days_back=30")

# Run with: locust -f locustfile.py --host=http://localhost:8000
```

### JMeter (Enterprise)
```bash
# Create test plan with 100 thread groups
# Each thread: 10000 requests
# Ramp-up: 60 seconds
# Duration: 10 minutes
```

## Performance Targets

| Metric | Target | Threshold |
|--------|--------|-----------|
| Average Response | < 150ms | < 200ms |
| p95 Response | < 200ms | < 300ms |
| p99 Response | < 300ms | < 500ms |
| Error Rate | < 0.01% | < 0.1% |
| Throughput | > 500 req/s | > 300 req/s |
| Memory | < 300MB | < 500MB |
| CPU | < 60% | < 80% |

## Load Test Execution

### Step 1: Baseline Test (5 minutes)
```bash
# Single user to establish baseline
ab -n 1000 -c 1 http://localhost:8000/api/v1/inventory/list
```

### Step 2: Ramp-up Test (5 minutes)
```bash
# Gradually increase load: 10 → 50 → 100 users
# Monitor for issues
```

### Step 3: Sustained Load Test (10 minutes)
```bash
# Maintain 100 concurrent users
# Measure steady-state performance
```

### Step 4: Spike Test (5 minutes)
```bash
# Jump to 200 concurrent users suddenly
# Verify system recovers gracefully
```

### Step 5: Stress Test (Until failure)
```bash
# Increase load until system fails
# Find breaking point for documentation
```

## Monitoring During Load Test

### System Metrics
```bash
# Monitor in separate terminal
watch -n 1 'top -bn1 | head -20'
ps aux | grep python  # Process memory/CPU
docker stats            # Container metrics (if using Docker)
```

### Database Metrics
```sql
-- Monitor active connections
SELECT count(*) FROM pg_stat_activity;

-- Monitor query performance
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

### Application Logs
```bash
tail -f /var/log/enterprise_retail.log | grep "ERROR|WARNING|duration"
```

## Load Test Report

```
LOAD TEST RESULTS
═════════════════════════════════════════

Test Date: Feb 19, 2024
Duration: 10 minutes
Concurrent Users: 100
Total Requests: 10,000

RESPONSE TIMES
──────────────────────────────────────────
Minimum:        45ms
Maximum:        850ms
Average:        142ms
Median:         130ms
p95:            195ms ✅ (Target: < 200ms)
p99:            280ms ✅ (Target: < 300ms)

THROUGHPUT
──────────────────────────────────────────
Requests/sec:   987 req/s ✅ (Target: > 500)
Data throughput: 5.2 MB/s

ERRORS & FAILURES
──────────────────────────────────────────
Total Errors:   2
Failed Requests: 0.02% ✅ (Target: < 0.1%)
Timeouts:       0

RESOURCE USAGE
──────────────────────────────────────────
Peak Memory:    287 MB ✅ (Target: < 500 MB)
Avg CPU:        52% ✅ (Target: < 80%)
Database Conn:  45/50 available

STATUS: ✅ PASS - Ready for production
═════════════════════════════════════════
```

## Troubleshooting Performance Issues

If p95 > 200ms:
1. Check database indexes
2. Check for N+1 queries
3. Add caching layer
4. Scale horizontally (add more workers)

If error rate > 0.1%:
1. Check error logs
2. Increase connection pool
3. Add retry logic
4. Scale backend

If memory usage > 500MB:
1. Profile memory usage
2. Reduce batch sizes
3. Implement pagination in queries
4. Add garbage collection

## Related Issues
- #1.4 API Testing
- #4.1 Testing - Unit & Integration

## Files to Generate
- [ ] `load_test_results.html` - HTML report
- [ ] `load_test_metrics.json` - Raw metrics
- [ ] `locustfile.py` - Locust load test script

## Definition of Done
✅ 100 concurrent users sustained for 10 minutes  
✅ p95 response < 200ms  
✅ Error rate < 0.1%  
✅ Memory usage < 500MB  
✅ CPU < 80%  
✅ Load test report generated  
✅ Ready for gate approval
