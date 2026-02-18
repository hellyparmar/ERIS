# Performance Benchmark Report
## Enterprise Retail Intelligence System v3.0

**Date:** February 18, 2026  
**Environment:** Production Staging  
**Status:** Template (Run `python3 scripts/benchmark_performance.py` when server is active)

---

## How to Run Benchmarks

### Prerequisites
```bash
# Ensure backend is running
docker-compose -f docker-compose.prod.yml up -d backend redis postgres

# Wait for services to be healthy (10-15 seconds)
sleep 15

# Check services
docker-compose ps
```

### Execute Benchmark Suite
```bash
# Install dependencies
pip install aiohttp

# Run benchmarks (generates benchmark_results.json)
cd /home/petpooja/Enterprise\ Retail\ Intelligence\ System
python3 scripts/benchmark_performance.py

# View results
cat benchmark_results.json | python -m json.tool
```

---

## Expected Benchmark Results

### Performance Targets

| Endpoint | Target Avg | Target P95 | Target P99 | Min Throughput |
|----------|-----------|-----------|-----------|----------------|
| Manager Login | < 100ms | < 300ms | < 500ms | 10 req/s |
| Cashier Login | < 100ms | < 300ms | < 500ms | 10 req/s |
| Get Override Config | < 50ms | < 150ms | < 300ms | 20 req/s |
| Get Day Status | < 100ms | < 300ms | < 500ms | 10 req/s |
| List Inventory | < 150ms | < 400ms | < 800ms | 8 req/s |
| List Products | < 150ms | < 400ms | < 800ms | 8 req/s |
| Health Check | < 10ms | < 20ms | < 50ms | 100+ req/s |

### Success Criteria
- ✅ Overall Success Rate: > 99%
- ✅ No response time anomalies > 2000ms
- ✅ P95 latency < 500ms for most endpoints
- ✅ Throughput > 8 req/s for all endpoints

---

## Benchmark Metrics Explained

### Response Time Percentiles
- **Avg:** Average response time across all requests
- **Median (Med):** 50th percentile - half faster, half slower
- **P95:** 95% of requests complete within this time
- **P99:** 99% of requests complete within this time
- **Max:** Worst-case response time

### Example Output
```json
{
  "benchmark_name": "Manager Login",
  "endpoint": "POST /api/v1/auth/manager/login",
  "iterations": 100,
  "results": {
    "min_time_ms": 45.2,
    "avg_time_ms": 87.5,
    "median_time_ms": 82.1,
    "p95_time_ms": 145.3,
    "p99_time_ms": 198.7,
    "max_time_ms": 342.1,
    "throughput": 11.4,
    "success_rate": 99.0
  }
}
```

---

## Performance Analysis

### What Each Metric Tells Us

**Response Time (ms):**
- Normal: 50-200ms (acceptable for most retail operations)
- Slow: 200-500ms (noticeable, but acceptable)
- Critical: > 500ms (poor user experience)

**Throughput (req/s):**
- Indicates how many simultaneous cashiers the system can handle
- Target: 50+ concurrent transactions per second
- Formula: iterations / total_time

**Success Rate (%):**
- Should always be 99%+ in production
- Lower rates indicate stability issues
- Investigate any failures immediately

---

## Load Test Scenarios

### Scenario 1: Normal Operations (8 Concurrent Cashiers)
```
Duration: 5 minutes
Concurrent Users: 8
Expected: 
- Avg Response Time: < 150ms
- Success Rate: > 99.5%
- Throughput: > 30 req/s
```

### Scenario 2: Peak Hours (20 Concurrent Cashiers)
```
Duration: 10 minutes
Concurrent Users: 20
Expected:
- Avg Response Time: < 300ms
- Success Rate: > 99%
- Throughput: > 50 req/s
```

### Scenario 3: Stress Test (50 Concurrent Users)
```
Duration: 5 minutes
Concurrent Users: 50
Expected:
- System should remain responsive
- Graceful degradation (not crashes)
- Success Rate: > 95% (acceptable for stress)
```

---

## Optimization Recommendations

### If Benchmarks Show Slow Response Times

**For Login Endpoints (> 200ms):**
```python
# Add Redis caching for manager profiles
redis.setex('manager:profile:{id}', 300, profile_json)

# Reduce JWT signing overhead
# Use RS256 instead of HS256 (but keep HS for now for speed)

# Add connection pooling optimization
# psql: max_connections = 100
# redis: maxmemory = 512mb
```

**For List Endpoints (> 300ms):**
```python
# Implement query result caching
# Max 500 items per page prevents O(n²) lookups

# Add database indexing
# CREATE INDEX idx_sales_date ON sales(sale_date);
# CREATE INDEX idx_inventory_sku ON inventory(sku);

# Enable Redis pagination cache
```

**For Inventory/Products (> 400ms):**
```python
# Cache aggregated results
# Pre-calculate common queries (daily totals, by category, etc)

# Reduce database round-trips
# Use SELECT * efficiently, avoid N+1 queries

# Add pagination limits
# Never fetch > 500 rows without pagination
```

---

## Continuous Performance Monitoring

### Daily Benchmarks
```bash
#!/bin/bash
# /usr/local/bin/daily-benchmark.sh

cd /home/petpooja/Enterprise\ Retail\ Intelligence\ System

# Run benchmarks
python3 scripts/benchmark_performance.py

# Archive results
cp benchmark_results.json \
  /var/log/rdios/benchmark_$(date +%Y%m%d_%H%M%S).json

# Alert if thresholds exceeded
python3 << 'EOF'
import json
with open('benchmark_results.json') as f:
    results = json.load(f)
    for test in results['tests']:
        if test['results']['avg_time_ms'] > 200:
            print(f"ALERT: {test['name']} is slow: {test['results']['avg_time_ms']}ms")
        if test['results']['success_rate'] < 99:
            print(f"ALERT: {test['name']} has failures: {test['results']['success_rate']}%")
EOF
```

### Schedule
```bash
# Run daily at 2 AM
0 2 * * * /usr/local/bin/daily-benchmark.sh

# Edit crontab
sudo crontab -e
```

---

## Troubleshooting Slow Performance

### Step 1: Check System Resources
```bash
# CPU usage
top -b -n 1 | head -20

# Memory usage
free -h

# Disk I/O
iostat -x 1

# Network
netstat -an | grep ESTABLISHED | wc -l
```

### Step 2: Check Database
```bash
# Slow query log
sudo tail -100 /var/log/postgresql/postgresql.log | grep slow

# Active connections
psql -U rdios_user -d enterprise_retail_db -c \
  "SELECT pid, usename, state, query FROM pg_stat_activity"

# Connection pool usage
psql -U rdios_user -d enterprise_retail_db -c \
  "SELECT sum(numbackends) FROM pg_stat_database"
```

### Step 3: Check Redis
```bash
# Memory usage
redis-cli INFO memory

# Slow operations
redis-cli --latency

# Keys by type
redis-cli --scan --pattern '*' | wc -l
```

### Step 4: Check Application Logs
```bash
# Real-time logs
docker-compose logs -f backend

# Search for errors
docker-compose logs backend | grep -i error | tail -20

# Search for slow operations
docker-compose logs backend | grep '>100ms' | tail -20
```

---

## Success Benchmarking Report Template

```
BENCHMARK RUN: [DATE]
STATUS: ✅ PASSED / ⚠️ WARNING / ❌ FAILED

METRICS SUMMARY:
├─ Overall Success Rate: XX.X% (Target: > 99%)
├─ Average Response Time: XXms (Target: < 150ms)
├─ P95 Latency: XXms (Target: < 400ms)
└─ Throughput: XX req/s (Target: > 50 req/s)

ENDPOINT RESULTS:
├─ Manager Login: [PASS/WARN/FAIL]
├─ Cashier Login: [PASS/WARN/FAIL]
├─ Override Config: [PASS/WARN/FAIL]
├─ Day Status: [PASS/WARN/FAIL]
├─ Inventory List: [PASS/WARN/FAIL]
├─ Products List: [PASS/WARN/FAIL]
└─ Health Check: [PASS/WARN/FAIL]

ISSUES FOUND:
[List any performance issues]

RECOMMENDATIONS:
[List optimization suggestions]

SIGNED BY: [DevOps Lead]
DATE: [Date of run]
```

---

## Next Steps

1. **Start server:** `docker-compose -f docker-compose.prod.yml up -d`
2. **Wait 15 seconds** for services to be healthy
3. **Run benchmarks:** `python3 scripts/benchmark_performance.py`
4. **Review results:** `cat benchmark_results.json`
5. **Optimize:** Apply recommendations from results
6. **Document:** Attach JSON output to deployment checklist
