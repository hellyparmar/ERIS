# Docker Compose Validation & Deployment Guide
## Enterprise Retail Intelligence System v3.0

**Date:** February 18, 2026  
**Docker Version Required:** 20.10+  
**Docker Compose Version Required:** 2.0+

---

## Pre-Deployment Verification

### Step 1: Check Docker Installation
```bash
# Verify Docker is installed and running
docker --version
# Expected: Docker version 20.10 or higher

# Verify Docker daemon is running
docker ps
# Expected: Shows CONTAINER ID, IMAGE, etc (no errors)

# Verify Docker Compose
docker-compose --version
# Expected: Docker Compose version 2.0 or higher
```

### Step 2: Verify File Structure
```bash
cd /home/petpooja/Enterprise\ Retail\ Intelligence\ System

# Check required files exist
ls -la docker-compose.prod.yml          # ✅ Must exist
ls -la Dockerfile.backend               # ✅ Must exist
ls -la Dockerfile.frontend              # ✅ Must exist
ls -la .env                              # ✅ Must exist (copy from .env.example)

# Check directories
ls -d api/                               # ✅ Must exist
ls -d src/                               # ✅ Must exist
ls -d scripts/                           # ✅ Must exist
```

### Step 3: Create .env File
```bash
# Copy template
cp .env.example .env

# Edit with production values
nano .env

# Critical variables to update:
#   JWT_SECRET_KEY         (generate new)
#   POS_JWT_SECRET_KEY     (generate new)
#   DATABASE_PASSWORD      (change from default)
#   MSG91_API_KEY          (add WhatsApp API key)
#   ENVIRONMENT            (set to production)
```

---

## Docker Compose Configuration Validation

### Service Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Nginx Reverse Proxy                      │
│                  (Port 80/443)                              │
└─────────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────┬─────────────────────┐
        ↓                     ↓                     ↓
   ┌─────────┐          ┌─────────┐        ┌──────────┐
   │ Backend │          │Frontend │        │  Celery  │
   │(8000)   │          │(5173)   │        │ Worker   │
   └────┬────┘          └────┬────┘        └────┬─────┘
        │                    │                   │
        └────────┬───────────┘───────────────────┘
                 ↓
        ┌────────────────────┐
        │  rdios_network     │  (Bridge Network)
        │ (Internal Docker)  │
        └────────────────────┘
         │                  │
         ↓                  ↓
    ┌────────┐        ┌─────────┐
    │PostgreSQL        │  Redis  │
    │(5433)   │        │(6379)   │
    └────────┘        └─────────┘
```

### Volume Mapping
```
postgres_data   → /var/lib/postgresql/data     (Persistent DB)
redis_data      → /data                         (Persistent cache)
./api           → /app/api                      (Live code)
./src           → /app/src                      (Live frontend)
./logs          → /app/logs                     (Application logs)
```

### Network Configuration
```
Service        Container Name      Port Mapping    Health Check
─────────────────────────────────────────────────────────────────
PostgreSQL     rdios_postgres      5433:5432      pg_isready
Redis          rdios_redis         6379:6379      redis-cli ping
Backend        rdios_backend       8000:8000      /health endpoint
Frontend       rdios_frontend      5173:5173      (no check)
Celery         rdios_celery_worker (none)         (restart only)
Nginx          rdios_nginx         80:80, 443:443 (no check)
```

---

## Deployment Steps

### Step 1: Pre-flight Checks
```bash
# Navigate to project
cd /home/petpooja/Enterprise\ Retail\ Intelligence\ System

# Validate compose file
docker-compose -f docker-compose.prod.yml config
# Expected: Returns entire config without errors

# Check for syntax errors
docker-compose -f docker-compose.prod.yml config > /dev/null
# Expected: No output = success
```

### Step 2: Build Docker Images
```bash
# Build backend image
docker-compose -f docker-compose.prod.yml build backend
# Expected: Shows build progress, ends with "Successfully built..."

# Build frontend image
docker-compose -f docker-compose.prod.yml build frontend
# Expected: npm build completes successfully

# Build celery worker
docker-compose -f docker-compose.prod.yml build celery_worker
# Expected: Uses same backend image

# List built images
docker images | grep rdios
# Expected: Shows rdios_backend, rdios_frontend images
```

### Step 3: Start Services
```bash
# Start all services in background
docker-compose -f docker-compose.prod.yml up -d

# Expected output:
# Creating rdios_postgres ... done
# Creating rdios_redis ... done
# Creating rdios_backend ... done
# Creating rdios_frontend ... done
# Creating rdios_celery_worker ... done
# Creating rdios_nginx ... done
```

### Step 4: Verify Services Started
```bash
# Check status
docker-compose -f docker-compose.prod.yml ps

# Expected output:
# NAME                     STATUS                  PORTS
# rdios_postgres          Up 2 minutes (healthy)  0.0.0.0:5433->5432/tcp
# rdios_redis             Up 2 minutes (healthy)  0.0.0.0:6379->6379/tcp
# rdios_backend           Up 1 minute (healthy)   0.0.0.0:8000->8000/tcp
# rdios_frontend          Up 1 minute             0.0.0.0:5173->5173/tcp
# rdios_celery_worker     Up 1 minute             
# rdios_nginx             Up 1 minute             0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
```

### Step 5: Health Checks
```bash
# Check backend health
curl http://localhost:8000/health
# Expected: {"status": "healthy", "timestamp": "..."}

# Check database connection
curl http://localhost:8000/api/v1/health/db
# Expected: {"database": "connected"}

# Check Redis connection
curl http://localhost:8000/api/v1/health/redis
# Expected: {"redis": "connected"}

# Check API docs
curl http://localhost:8000/docs
# Expected: HTML response (Swagger UI)
```

---

## Post-Deployment Verification

### Functional Tests
```bash
# 1. Manager Login
curl -X POST http://localhost:8000/api/v1/auth/manager/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@example.com","password":"admin123"}'
# Expected: {"access_token": "...", "token_type": "bearer"}

# 2. List Products
curl http://localhost:8000/api/v1/products \
  -H "Authorization: Bearer YOUR_TOKEN"
# Expected: {"items": [...], "total": 123, "page": 1}

# 3. Create Transaction (POS)
curl -X POST http://localhost:8000/api/v1/transactions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer POS_TOKEN" \
  -d '{"items":[{"sku":"ITEM1","qty":2}],"payment_method":"cash"}'
# Expected: {"transaction_id": "...", "total": 1234.50}

# 4. Health Check
curl http://localhost:8000/health
# Expected: {"status": "healthy"}
```

### Performance Checks
```bash
# Response time for /health endpoint
time curl http://localhost:8000/health
# Expected: real 0m0.1s (100ms or less)

# Check database query time
time curl http://localhost:8000/api/v1/products?page=1
# Expected: real 0m0.2s (200ms or less)

# Check concurrent requests
ab -n 100 -c 10 http://localhost:8000/health
# Expected: Requests per second: >50
```

### Data Persistence Check
```bash
# Add test data
curl -X POST http://localhost:8000/api/v1/products \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{"name":"Test","sku":"TEST123","price":99.99}'

# Restart backend (data should persist)
docker-compose -f docker-compose.prod.yml restart backend

# Sleep 10 seconds for restart
sleep 10

# Verify data still exists
curl http://localhost:8000/api/v1/products \
  -H "Authorization: Bearer TOKEN"
# Expected: Test product still in list
```

---

## Monitoring & Logs

### View Logs
```bash
# Backend logs (real-time)
docker-compose -f docker-compose.prod.yml logs -f backend

# Last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100 backend

# Logs from specific time
docker-compose -f docker-compose.prod.yml logs --since 10m backend

# All services logs
docker-compose -f docker-compose.prod.yml logs -f

# Celery worker logs
docker-compose -f docker-compose.prod.yml logs -f celery_worker
```

### Service Resource Usage
```bash
# Real-time stats
docker stats

# Specific service
docker stats rdios_backend

# Output:
# CONTAINER   CPU %   MEM USAGE / LIMIT    NET I/O
# rdios_backend  2.1%   287MiB / 2GiB       102MB / 45MB
```

### Database Statistics
```bash
# Connect to database
docker-compose exec postgres psql -U rdios_user -d enterprise_retail_db

# List tables
\dt

# Table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
FROM pg_tables 
WHERE schemaname != 'pg_catalog' 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

# Exit
\q
```

### Redis Status
```bash
# Check Redis
docker-compose exec redis redis-cli INFO

# Memory usage
docker-compose exec redis redis-cli INFO memory

# Key count
docker-compose exec redis redis-cli DBSIZE

# Monitor commands
docker-compose exec redis redis-cli MONITOR
```

---

## Common Issues & Solutions

### Issue 1: Services Fail to Start

**Symptoms:** `ERROR: Service 'backend' failed to build`

**Solution:**
```bash
# Check Docker daemon
sudo systemctl status docker

# Rebuild without cache
docker-compose -f docker-compose.prod.yml build --no-cache backend

# Check disk space
df -h /var/lib/docker

# Clear unused images
docker system prune -a

# Rebuild
docker-compose -f docker-compose.prod.yml build
```

### Issue 2: Database Connection Fails

**Symptoms:** `SQLALCHEMY_ERROR: Could not connect to database`

**Solution:**
```bash
# Check PostgreSQL is running
docker-compose ps postgres
# Should show "Up X seconds (healthy)"

# Check logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres

# Wait for health check
sleep 15

# Verify connection
docker-compose exec postgres psql -U rdios_user -d enterprise_retail_db -c "SELECT 1"
```

### Issue 3: Port Already in Use

**Symptoms:** `ERROR: driver failed programming external connectivity on endpoint`

**Solution:**
```bash
# Find service using port 8000
sudo lsof -i :8000
# Or
netstat -tulpn | grep 8000

# Kill process
kill -9 <PID>

# Or change port in docker-compose
# Edit: services.backend.ports: ["8001:8000"]

# Restart
docker-compose up -d
```

### Issue 4: Redis Connection Issues

**Symptoms:** `Error: ECONNREFUSED 127.0.0.1:6379`

**Solution:**
```bash
# Check Redis container
docker-compose ps redis
# Should show "Up X seconds (healthy)"

# Restart Redis
docker-compose restart redis

# Clear Redis data if needed
docker volume rm enterprise_retail_system_redis_data

# Rebuild
docker-compose up -d redis
```

### Issue 5: Frontend Can't Reach Backend

**Symptoms:** Browser shows CORS error or "Cannot reach API"

**Solution:**
```bash
# Check CORS configuration in backend
grep -i cors .env

# Verify backend is accessible
curl http://localhost:8000/health

# Check frontend environment
docker-compose logs frontend | grep VITE_API_URL

# Frontend config should have
# VITE_API_URL: http://localhost:8000  (for development)
# VITE_API_URL: http://backend:8000    (inside Docker)
```

---

## Scaling & Performance Tuning

### Increase Celery Workers
```bash
# Edit docker-compose.prod.yml
# Change celery_worker command to:
command: celery -A api.tasks.celery_app worker -l info --concurrency=8

# Restart
docker-compose restart celery_worker
```

### Increase Database Connections
```bash
# Edit docker-compose.prod.yml postgres environment:
# Add: POSTGRES_INITDB_ARGS: "-c max_connections=200"

# Restart (WARNING: loses data)
docker volume rm enterprise_retail_system_postgres_data
docker-compose restart postgres
```

### Increase Redis Memory
```bash
# Edit docker-compose.prod.yml redis command:
command: redis-server --appendonly yes --maxmemory 1gb

# Restart
docker-compose restart redis
```

### Enable Redis Persistence
```bash
# Already enabled: --appendonly yes
# Verify:
docker-compose exec redis redis-cli CONFIG GET appendonly
# Expected: 1 (yes)
```

---

## Shutdown & Cleanup

### Stop Services
```bash
# Stop but keep volumes
docker-compose -f docker-compose.prod.yml stop

# Stop and remove containers
docker-compose -f docker-compose.prod.yml down

# Stop and remove everything (including volumes)
docker-compose -f docker-compose.prod.yml down -v
```

### Clean Up
```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove unused networks
docker network prune

# Deep clean (WARNING: removes everything)
docker system prune -a --volumes
```

### Backup Data
```bash
# Before cleanup, backup database
docker-compose exec postgres pg_dump -U rdios_user enterprise_retail_db | \
  gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Before cleanup, backup Redis
docker-compose exec redis redis-cli BGSAVE
docker cp rdios_redis:/data/dump.rdb ./dump_$(date +%Y%m%d_%H%M%S).rdb
```

---

## Docker Production Best Practices

### 1. Use Environment Variables
```bash
# ✅ Good - Use .env file
docker-compose -f docker-compose.prod.yml up -d

# ❌ Bad - Hardcoded in compose
# database_url=localhost:5432  (visible in git)
```

### 2. Never Run as Root
```bash
# ✅ Compose file already uses non-root user
# See: Dockerfile.backend -> USER appuser

# Verify
docker-compose exec backend id
# Expected: uid=1000(appuser) gid=1000(appuser)
```

### 3. Use Health Checks
```bash
# ✅ Already configured for each service
# Backend checks /health endpoint
# Database checks pg_isready
# Redis checks redis-cli ping
```

### 4. Set Resource Limits
```yaml
# Edit docker-compose.prod.yml to add:
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### 5. Enable Logging
```bash
# Already configured - check logs
docker-compose logs backend | head -20

# For production, use log drivers
# Add to backend service in docker-compose.prod.yml:
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

---

## Kubernetes Migration (Optional)

For running on Kubernetes instead of Docker Compose:

```bash
# Generate Kubernetes manifests from docker-compose
kompose convert -f docker-compose.prod.yml -o k8s/

# Deploy to Kubernetes
kubectl apply -f k8s/

# Check deployment
kubectl get pods
kubectl get services
```

See [KUBERNETES_DEPLOYMENT.md](KUBERNETES_DEPLOYMENT.md) for detailed instructions.

---

## Summary Checklist

- ✅ Docker version 20.10+ installed
- ✅ Docker Compose 2.0+ installed
- ✅ `.env` file created with secrets
- ✅ Docker images built successfully
- ✅ All 6 services running and healthy
- ✅ Health checks passing
- ✅ API responding correctly
- ✅ Database connected
- ✅ Redis connected
- ✅ Frontend accessible
- ✅ Logs being written
- ✅ No critical errors in logs

**Status:** ✅ Ready for Production Deployment
