# R-DIOS v5.0 - Production Deployment Plan

**Version**: 5.0.0  
**Date**: January 2026  
**Status**: Pre-Production Ready  
**Timeline**: 2-Week Deployment

---

## 🎯 Deployment Overview

**Objective**: Deploy R-DIOS v5.0 Operational Backbone to production environment

**Scope**: 
- 49 API endpoints across 5 modules
- 232k rows of real retail data
- Transaction Engine, Communication Hub, Community Commerce
- PostgreSQL database with 13 tables
- Redis caching layer
- Celery async workers

**Success Criteria**:
- 99.9% uptime
- <200ms API response time (p95)
- Support 10,000 concurrent users
- ₹500/day WhatsApp budget adherence

---

## 📋 Pre-Deployment Checklist

### 1. Infrastructure Requirements

**Compute** (AWS/Azure/GCP):
- [ ] 2x Application servers (4 vCPU, 16GB RAM each)
- [ ] 1x PostgreSQL server (8 vCPU, 32GB RAM)
- [ ] 1x Redis server (2 vCPU, 8GB RAM)
- [ ] 1x Celery worker (4 vCPU, 8GB RAM)
- [ ] Load balancer (managed service)

**Storage**:
- [ ] 500GB SSD for PostgreSQL
- [ ] 100GB SSD for application files
- [ ] 200GB S3 bucket for PDFs/media

**Network**:
- [ ] VPC with private/public subnets
- [ ] Security groups configured
- [ ] SSL certificate (Let's Encrypt or ACM)

### 2. External Services

- [ ] Twilio account (WhatsApp Business API)
- [ ] SendGrid/AWS SES (email fallback)
- [ ] CloudWatch/Datadog (monitoring)
- [ ] Sentry (error tracking)
- [ ] GitHub Actions (CI/CD)

### 3. Database Migration

- [ ] Backup development database
- [ ] Install Alembic
- [ ] Generate migration scripts
- [ ] Test migration on staging
- [ ] Schedule production migration (low-traffic window)

### 4. Environment Configuration

- [ ] Production `.env` file created
- [ ] Secrets stored in AWS Secrets Manager
- [ ] Database credentials rotated
- [ ] API keys configured
- [ ] CORS origins set

---

## 🚀 Deployment Steps

### Phase 1: Infrastructure Setup (Day 1-2)

#### Step 1.1: Provision Servers
```bash
# Using Terraform (infrastructure as code)
cd terraform/
terraform init
terraform plan -out=rdios-prod.plan
terraform apply rdios-prod.plan

# Provisions:
# - 2x EC2 t3.xlarge (app servers)
# - 1x RDS PostgreSQL db.m5.2xlarge
# - 1x ElastiCache Redis cache.m5.large
# - 1x EC2 t3.large (Celery worker)
# - ALB (Application Load Balancer)
```

#### Step 1.2: Network Configuration
```bash
# Configure VPC
- VPC: 10.0.0.0/16
- Public Subnet: 10.0.1.0/24 (Load Balancer)
- Private Subnet: 10.0.2.0/24 (App Servers)
- Private Subnet: 10.0.3.0/24 (Database)

# Security Groups
- ALB: Allow 443 from 0.0.0.0/0
- App: Allow 8000 from ALB
- DB: Allow 5432 from App
- Redis: Allow 6379 from App+Celery
```

#### Step 1.3: Install Dependencies
```bash
# On each app server
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3-pip nginx supervisor

# Clone repository
git clone https://github.com/yourorg/rdios.git
cd rdios

# Install Python dependencies
pip3 install -r requirements.txt
pip3 install -r requirements-phase0.txt
pip3 install -r requirements-phase2.txt
pip3 install gunicorn uvicorn[standard] alembic celery redis
```

### Phase 2: Database Setup (Day 3)

#### Step 2.1: Install Alembic
```bash
cd api/
alembic init migrations

# Edit alembic.ini
sqlalchemy.url = postgresql://user:pass@rds-endpoint:5432/rdios_prod

# Edit migrations/env.py
from db.models import Base
target_metadata = Base.metadata
```

#### Step 2.2: Generate Migration
```bash
# Create initial migration
alembic revision --autogenerate -m "Initial schema - 13 tables"

# Review generated migration
cat migrations/versions/001_initial_schema.py

# Apply to staging first
DATABASE_URL=postgresql://staging alembic upgrade head

# If successful, apply to production
DATABASE_URL=postgresql://production alembic upgrade head
```

#### Step 2.3: Load Data
```bash
# Backup first
pg_dump rdios_dev > backup_dev_$(date +%Y%m%d).sql

# Load enriched data
cd scripts/data_processing/
python load_to_database.py --env production

# Verify
psql -h rds-endpoint -U rdios_user -d rdios_prod -c "
  SELECT 
    'products' as table, COUNT(*) as rows FROM products
    UNION ALL
    SELECT 'customers', COUNT(*) FROM customers
    UNION ALL
    SELECT 'sales', COUNT(*) FROM sales;
"
```

### Phase 3: Application Deployment (Day 4-5)

#### Step 3.1: Configure Gunicorn
```python
# gunicorn_config.py
bind = "0.0.0.0:8000"
workers = 4  # (2 * CPU cores) + 1
worker_class = "uvicorn.workers.UvicornWorker"
max_requests = 1000
max_requests_jitter = 50
timeout = 120
keepalive = 5
accesslog = "/var/log/rdios/access.log"
errorlog = "/var/log/rdios/error.log"
loglevel = "info"
```

#### Step 3.2: Setup Supervisor
```ini
# /etc/supervisor/conf.d/rdios.conf
[program:rdios]
command=/usr/local/bin/gunicorn api.main:app -c gunicorn_config.py
directory=/opt/rdios
user=rdios
autostart=true
autorestart=true
stdout_logfile=/var/log/rdios/app.log
stderr_logfile=/var/log/rdios/app_error.log
environment=PYTHONPATH="/opt/rdios"
```

#### Step 3.3: Configure Nginx
```nginx
# /etc/nginx/sites-available/rdios
upstream rdios_app {
    server 10.0.2.10:8000;  # App server 1
    server 10.0.2.11:8000;  # App server 2
}

server {
    listen 80;
    server_name api.rdios.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.rdios.com;
    
    ssl_certificate /etc/letsencrypt/live/api.rdios.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.rdios.com/privkey.pem;
    
    client_max_body_size 20M;
    
    location / {
        proxy_pass http://rdios_app;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_connect_timeout 120s;
        proxy_read_timeout 120s;
    }
    
    location /static {
        alias /opt/rdios/static;
        expires 30d;
    }
}
```

### Phase 4: Celery Worker Setup (Day 6)

#### Step 4.1: Configure Celery
```python
# api/celery_app.py
from celery import Celery
from celery.schedules import crontab

app = Celery('rdios', broker='redis://redis-endpoint:6379/0')

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Kolkata',
    enable_utc=True,
    
    # Scheduled tasks
    beat_schedule={
        'send-payment-reminders': {
            'task': 'services.async_tasks.send_bulk_reminders',
            'schedule': crontab(hour=10, minute=0),  # 10 AM daily
        },
        'mark-overdue-invoices': {
            'task': 'services.async_tasks.mark_overdue_invoices',
            'schedule': crontab(hour=0, minute=0),  # Midnight
        },
        'generate-daily-reports': {
            'task': 'services.async_tasks.generate_daily_reports',
            'schedule': crontab(hour=6, minute=0),  # 6 AM daily
        }
    }
)
```

#### Step 4.2: Supervisor Config for Celery
```ini
# /etc/supervisor/conf.d/celery.conf
[program:celery_worker]
command=/usr/local/bin/celery -A api.celery_app worker --loglevel=info
directory=/opt/rdios
user=rdios
autostart=true
autorestart=true
stdout_logfile=/var/log/rdios/celery_worker.log

[program:celery_beat]
command=/usr/local/bin/celery -A api.celery_app beat --loglevel=info
directory=/opt/rdios
user=rdios
autostart=true
autorestart=true
stdout_logfile=/var/log/rdios/celery_beat.log
```

### Phase 5: Monitoring & Logging (Day 7)

#### Step 5.1: Setup CloudWatch
```bash
# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb

# Configure metrics
cat > /opt/aws/amazon-cloudwatch-agent/etc/config.json <<EOF
{
  "metrics": {
    "namespace": "RDIOS/Production",
    "metrics_collected": {
      "cpu": {"measurement": [{"name": "cpu_usage_idle"}]},
      "mem": {"measurement": [{"name": "mem_used_percent"}]},
      "disk": {"measurement": [{"name": "used_percent"}]}
    }
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/rdios/app.log",
            "log_group_name": "/rdios/production/app",
            "log_stream_name": "{instance_id}"
          }
        ]
      }
    }
  }
}
EOF

sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config -m ec2 -s -c file:/opt/aws/amazon-cloudwatch-agent/etc/config.json
```

#### Step 5.2: Setup Sentry
```python
# api/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    environment="production",
    traces_sample_rate=0.1,  # 10% of requests
    integrations=[FastApiIntegration()]
)
```

### Phase 6: Testing & Validation (Day 8-10)

#### Step 6.1: Health Checks
```bash
# Test basic health
curl https://api.rdios.com/health
# Expected: {"status": "healthy", "timestamp": "..."}

# Test detailed health
curl https://api.rdios.com/health/detailed
# Expected: All checks show "ok"
```

#### Step 6.2: Load Testing
```bash
# Install Apache Bench
sudo apt install apache2-utils

# Test invoice creation endpoint
ab -n 1000 -c 100 -T "application/json" \
   -p invoice_payload.json \
   https://api.rdios.com/api/invoices/create

# Expected: >95% success rate, <200ms average response
```

#### Step 6.3: End-to-End Testing
```python
# scripts/e2e_test.py
import requests

API_BASE = "https://api.rdios.com"

# Test 1: Create invoice
response = requests.post(f"{API_BASE}/api/invoices/create", json={
    "sale_id": 1,
    "payment_terms_days": 30
})
assert response.status_code == 201
invoice_id = response.json()["id"]

# Test 2: Record payment
response = requests.post(f"{API_BASE}/api/invoices/record-payment", json={
    "invoice_id": invoice_id,
    "amount": 5000.00,
    "payment_method": "upi"
})
assert response.status_code == 201

# Test 3: Send message
response = requests.post(f"{API_BASE}/api/messages/send", json={
    "sender_type": "customer",
    "sender_id": 1,
    "recipient_type": "staff",
    "recipient_id": 1,
    "subject": "Test",
    "body": "Production test message",
    "channel": "in_app"
})
assert response.status_code == 201

print("✅ All E2E tests passed!")
```

### Phase 7: Go-Live (Day 11-14)

#### Step 7.1: DNS Configuration
```bash
# Update DNS to point to Load Balancer
# api.rdios.com → CNAME → rdios-alb-123456.us-east-1.elb.amazonaws.com

# Wait for propagation
dig api.rdios.com
```

#### Step 7.2: Enable Let's Encrypt SSL
```bash
sudo certbot --nginx -d api.rdios.com
sudo systemctl reload nginx
```

#### Step 7.3: Gradual Rollout
```
Day 11: 10% of traffic → Monitor for 24 hours
Day 12: 50% of traffic → Monitor for 24 hours
Day 13: 100% of traffic → Full production
Day 14: Stabilization & optimization
```

---

## 🔒 Security Hardening

### 1. Application Security
```python
# api/middleware/security.py
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app.add_middleware(HTTPSRedirectMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["api.rdios.com"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://rdios.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/invoices")
@limiter.limit("100/minute")
async def get_invoices(request: Request):
    pass
```

### 2. Database Security
```sql
-- Create read-only user for reporting
CREATE USER rdios_readonly WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE rdios_prod TO rdios_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO rdios_readonly;

-- Row-level security
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
CREATE POLICY invoices_isolation ON invoices
  FOR ALL
  TO rdios_user
  USING (customer_id = current_setting('app.current_customer_id')::int);
```

### 3. Secrets Management
```bash
# Store secrets in AWS Secrets Manager
aws secretsmanager create-secret \
  --name rdios/production/database \
  --secret-string '{"username":"rdios_user","password":"..."}'

# Fetch in application
import boto3

client = boto3.client('secretsmanager')
response = client.get_secret_value(SecretId='rdios/production/database')
db_creds = json.loads(response['SecretString'])
```

---

## 📊 Monitoring & Alerts

### CloudWatch Alarms
```bash
# High CPU alarm
aws cloudwatch put-metric-alarm \
  --alarm-name rdios-high-cpu \
  --alarm-description "CPU exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:sns:us-east-1:123456789:rdios-alerts

# High error rate
aws cloudwatch put-metric-alarm \
  --alarm-name rdios-high-errors \
  --metric-name 5XXError \
  --namespace AWS/ApplicationELB \
  --statistic Sum \
  --period 60 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1
```

### Custom Metrics
```python
# api/middleware/metrics.py
from prometheus_client import Counter, Histogram

request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')

@app.middleware("http")
async def track_metrics(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    request_count.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    request_duration.observe(duration)
    return response
```

---

## 🔄 Backup & Recovery

### Automated Backups
```bash
# PostgreSQL automated backups (AWS RDS)
aws rds modify-db-instance \
  --db-instance-identifier rdios-prod \
  --backup-retention-period 30 \
  --preferred-backup-window "03:00-04:00"

# Application files backup (daily)
0 2 * * * tar -czf /backups/rdios-$(date +\%Y\%m\%d).tar.gz /opt/rdios
0 3 * * * aws s3 cp /backups/*.tar.gz s3://rdios-backups/
```

### Disaster Recovery Plan
```
RTO (Recovery Time Objective): 4 hours
RPO (Recovery Point Objective): 1 hour

Steps:
1. Notify team (Alert sent via PagerDuty)
2. Assess damage (Check CloudWatch, Sentry)
3. Restore from backup (Latest automated backup)
4. Validate data integrity (Run integrity checks)
5. Redirect traffic (Update DNS if needed)
6. Post-mortem (Document lessons learned)
```

---

## 📈 Performance Optimization

### Database Indexes
```sql
-- Invoice queries
CREATE INDEX CONCURRENTLY idx_invoices_customer_status 
  ON invoices(customer_id, payment_status) 
  WHERE payment_status IN ('pending', 'partial', 'overdue');

-- Message queries
CREATE INDEX CONCURRENTLY idx_messages_recipient_unread 
  ON messages(recipient_id, recipient_type, read_at) 
  WHERE read_at IS NULL;

-- Sales analytics
CREATE INDEX CONCURRENTLY idx_sales_date_product 
  ON sales(transaction_date DESC, product_id);
```

### Caching Strategy
```python
# api/middleware/cache.py
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://redis-endpoint:6379")
    FastAPICache.init(RedisBackend(redis), prefix="rdios-cache")

@app.get("/api/invoices/stats/summary")
@cache(expire=600)  # Cache for 10 minutes
async def get_stats():
    # Expensive aggregation query
    return compute_stats()
```

---

## ✅ Post-Deployment Checklist

### Day 1
- [ ] All health checks passing
- [ ] No critical errors in Sentry
- [ ] Response times <200ms (p95)
- [ ] Database connections stable
- [ ] Redis cache hit rate >70%

### Week 1
- [ ] Monitor daily active users
- [ ] Track WhatsApp costs (<₹500/day)
- [ ] Review error logs daily
- [ ] Validate backup restoration
- [ ] Load test with 5,000 concurrent users

### Month 1
- [ ] 99.9% uptime achieved
- [ ] Cost optimization review
- [ ] User feedback collected
- [ ] Performance baseline established
- [ ] Disaster recovery drill conducted

---

## 💰 Cost Estimate

| Component | Specification | Monthly Cost |
|-----------|--------------|--------------|
| App Servers (2x) | EC2 t3.xlarge | $300 |
| Database | RDS PostgreSQL m5.2xlarge | $600 |
| Redis | ElastiCache m5.large | $150 |
| Celery Worker | EC2 t3.large | $75 |
| Load Balancer | ALB | $25 |
| S3 Storage | 200GB | $5 |
| CloudWatch | Logs + Metrics | $50 |
| Sentry | 10k events/month | $29 |
| Twilio WhatsApp | 9k messages/month | $100 |
| SendGrid Email | 50k emails/month | $20 |
| **Total** | | **~$1,354/month** |

**₹ Conversion** (@ $1 = ₹83): **~₹112,000/month**

---

## 🎯 Success Metrics

**Technical**:
- Uptime: >99.9% (8.76 hours downtime/year max)
- Response Time: <200ms (p95)
- Error Rate: <0.1%
- Database Query Time: <50ms (p95)

**Business**:
- Invoice Processing: 10,000/day capacity
- WhatsApp Delivery: 95% success rate
- Cost Per Transaction: <₹1
- Customer Satisfaction: >4.5/5

---

**Deployment Owner**: DevOps Team  
**Approval Required**: CTO, Head of Engineering  
**Go-Live Date**: TBD (2 weeks from approval)  
**Document Status**: Ready for Review v1.0
