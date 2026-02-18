# PRODUCTION DEPLOYMENT & OPERATIONS GUIDE
## Enterprise Retail Intelligence System v3.0

**Last Updated:** February 18, 2026

---

## Quick Start Checklist

```bash
# 1. Clone and setup
git clone https://github.com/hellyparmar/R-DIOS.git
cd R-DIOS
cp .env.example .env

# 2. Edit environment
nano .env  # Set production values

# 3. Docker deployment
docker-compose -f docker-compose.prod.yml up -d

# 4. Verify
curl http://localhost:8000/health

# 5. Run tests
python3 scripts/benchmark_performance.py
python3 scripts/security_testing.py
```

---

## Performance Benchmarking

### Run Benchmark Suite

```bash
# Install dependencies
pip install aiohttp

# Run benchmarks
python3 scripts/benchmark_performance.py

# Results saved to: benchmark_results.json
```

**Expected Results:**
- Average response time: 50-200ms
- P95 response time: < 500ms
- P99 response time: < 1000ms
- Throughput: > 50 requests/second
- Success rate: > 99%

**Key Metrics to Monitor:**
```
Manager Login:           50-100ms
Cashier Login:           50-100ms
List Products:           100-200ms
Health Check:            10-20ms
```

---

## Security Testing

### Run Security Tests

```bash
# Install dependencies
pip install requests

# Run security tests
python3 scripts/security_testing.py

# Results saved to: security_test_results.json
```

**Security Checks:**
- ✅ HTTPS/SSL configuration
- ✅ Security headers (X-Content-Type-Options, X-Frame-Options, etc)
- ✅ CORS policy
- ✅ Authentication endpoints
- ✅ SQL injection protection
- ✅ Rate limiting
- ✅ Input validation

**Expected Results:**
- All critical tests PASS
- No CRITICAL severity issues
- < 5 HIGH severity warnings
- All security headers present

---

## Docker Deployment

### Production Setup with Docker

```bash
# 1. Pull/build images
docker-compose -f docker-compose.prod.yml pull
# or
docker-compose -f docker-compose.prod.yml build

# 2. Start services
docker-compose -f docker-compose.prod.yml up -d

# 3. Check status
docker-compose -f docker-compose.prod.yml ps

# 4. View logs
docker-compose -f docker-compose.prod.yml logs -f backend
```

### Service Management

```bash
# Stop all services
docker-compose -f docker-compose.prod.yml down

# Restart specific service
docker-compose -f docker-compose.prod.yml restart backend

# View service logs
docker-compose -f docker-compose.prod.yml logs -f celery_worker

# Resource usage
docker stats
```

### Production Configuration

**docker-compose.prod.yml includes:**
- PostgreSQL (port 5433)
- Redis (port 6379)
- FastAPI Backend (port 8000)
- React Frontend (port 5173)
- Celery Worker
- Nginx Reverse Proxy (port 80/443)

---

## Environment Configuration

### Required Variables

```bash
# Database
DATABASE_URL=postgresql://rdios_user:PASSWORD@localhost:5433/enterprise_retail_db
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Redis
REDIS_URL=redis://localhost:6379/0

# Authentication
JWT_SECRET_KEY=<generate-random-key>
POS_JWT_SECRET_KEY=<generate-random-key>

# WhatsApp Integration
MSG91_API_KEY=<your-api-key>
MSG91_SENDER_ID=R-DIOS

# Frontend
VITE_API_URL=https://api.yourdomain.com

# Production
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### Generate Secure Keys

```bash
python3 << 'EOF'
import secrets

print("JWT_SECRET_KEY=" + secrets.token_urlsafe(32))
print("POS_JWT_SECRET_KEY=" + secrets.token_urlsafe(32))
print("DB_PASSWORD=" + secrets.token_urlsafe(16))
EOF
```

---

## Deployment Checklist

### Pre-Deployment (Use DEPLOYMENT_CHECKLIST.md)

**Security:**
- [ ] All secrets rotated
- [ ] SSL certificate valid
- [ ] No hardcoded secrets in code
- [ ] Input validation on all endpoints

**Testing:**
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] Performance benchmarks acceptable
- [ ] Security tests passed

**Infrastructure:**
- [ ] PostgreSQL 14 ready
- [ ] Redis ready
- [ ] Server resources adequate
- [ ] Backups configured

### Deployment Steps

```bash
# 1. Backup existing database
pg_dump -h localhost -U rdios_user enterprise_retail_db | gzip > backup.sql.gz

# 2. Pull latest code
git pull origin main

# 3. Update environment
source .env

# 4. Migrate database
python3 << 'EOF'
from api.db import Base, engine
from api.db.models import *
Base.metadata.create_all(bind=engine)
print("✅ Database migrated")
EOF

# 5. Start services
docker-compose -f docker-compose.prod.yml up -d

# 6. Run smoke tests
curl http://localhost:8000/health
curl http://localhost:5173

# 7. Monitor for 24 hours
docker-compose logs -f backend
```

### Post-Deployment

- [ ] All services healthy
- [ ] Endpoints responding
- [ ] Transactions processing
- [ ] Logs being written
- [ ] Monitoring active
- [ ] No errors in first hour
- [ ] Performance acceptable

---

## Monitoring & Operations

### Health Checks

```bash
# API Health
curl http://localhost:8000/health

# Database
psql -h localhost -U rdios_user -d enterprise_retail_db -c "SELECT 1"

# Redis
redis-cli ping

# Services
docker-compose ps
systemctl status rdios-backend  # if using systemd
```

### Viewing Logs

```bash
# Docker logs
docker-compose logs -f backend          # Last 100 lines following
docker-compose logs -f backend -n 500   # Last 500 lines

# System logs
tail -f /var/log/rdios-backend.log
tail -f /var/log/rdios-celery.log

# PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql.log
```

### Performance Monitoring

```bash
# Real-time metrics
docker stats

# Historical data
docker stats --no-stream

# Disk usage
du -sh /var/lib/docker/volumes/

# Connection count
psql -U rdios_user -d enterprise_retail_db -c \
  "SELECT count(*) FROM pg_stat_activity"
```

---

## Backup & Recovery

### Automated Backups

```bash
#!/bin/bash
# /usr/local/bin/rdios-backup.sh

BACKUP_DIR="/backups/rdios"
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d_%H%M%S)

# Database backup
pg_dump -h localhost -U rdios_user enterprise_retail_db | \
    gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Keep only 7 days
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete

echo "✅ Backup: $BACKUP_DIR/db_$DATE.sql.gz"
```

### Schedule with Cron

```bash
# Daily backups at 2 AM
0 2 * * * /usr/local/bin/rdios-backup.sh

# Edit crontab
sudo crontab -e
```

### Restore from Backup

```bash
# Stop services
docker-compose down

# Restore database
gunzip < /backups/rdios/db_YYYYMMDD_HHMMSS.sql.gz | \
  psql -h localhost -U rdios_user -d enterprise_retail_db

# Restart services
docker-compose up -d
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs backend

# Check port availability
sudo netstat -tulpn | grep 8000

# Check database connection
psql -h localhost -U rdios_user -d enterprise_retail_db -c "SELECT 1"

# Rebuild container
docker-compose build --no-cache backend
docker-compose up -d backend
```

### Database Issues

```bash
# Connection pooling issue
docker-compose restart postgres redis backend

# Query too slow
psql -U rdios_user -d enterprise_retail_db
# \timing on
# SELECT COUNT(*) FROM sales;

# Check table sizes
psql -U rdios_user -d enterprise_retail_db -c \
  "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) \
   FROM pg_tables ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC"
```

### Performance Issues

```bash
# Check Redis
redis-cli INFO stats

# Clear cache if needed
redis-cli FLUSHALL

# Check slow queries
psql -U rdios_user -d enterprise_retail_db
# SELECT query, calls, total_time FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10
```

### WhatsApp Integration Issues

```bash
# Check circuit breaker status
python3 << 'EOF'
from api.services.whatsapp_service import get_circuit_status
print(get_circuit_status())
EOF

# Check logs
docker-compose logs backend | grep -i whatsapp

# Test MSG91 API manually
curl "https://control.msg91.com/api/sendhttp?authkey=KEY&mobiles=91XXXXXXXXXX&message=test&sender=R-DIOS"
```

---

## Rollback Procedure

```bash
# 1. Stop current deployment
docker-compose down

# 2. Restore database
gunzip < /backups/rdios/db_LAST_GOOD.sql.gz | \
  psql -h localhost -U rdios_user -d enterprise_retail_db

# 3. Revert code
git revert HEAD
# or
git checkout <previous_commit>

# 4. Restart services
docker-compose up -d

# 5. Verify
curl http://localhost:8000/health

# 6. Document incident
# Create incident report with:
# - What went wrong
# - Root cause
# - How it was fixed
# - Prevention for future
```

---

## Support Resources

### Documentation
- [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - Pre/post deployment checks
- [PHASE_1_COMPLETION_REPORT.md](PHASE_1_COMPLETION_REPORT.md) - Feature documentation
- [PHASE_1_QUICK_REFERENCE.md](PHASE_1_QUICK_REFERENCE.md) - API examples

### Commands
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health: http://localhost:8000/health

### Emergency Contacts
- **On-Call:** [Phone/Email]
- **Management:** [Phone/Email]
- **Support:** [Email/Slack]

---

**Version:** 1.0  
**Status:** Production Ready ✅  
**Last Review:** February 18, 2026
