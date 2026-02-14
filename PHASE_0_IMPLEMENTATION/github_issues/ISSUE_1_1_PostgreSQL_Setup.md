# Task 1.1: PostgreSQL Infrastructure Setup
**Owner:** DevOps Lead  
**Duration:** 4 hours  
**Deadline:** Feb 17, 6:00 PM IST  
**Priority:** 🔴 CRITICAL (Blocks all other tasks)  
**Phase:** Phase 0 - Critical Blockers

---

## Description

Set up PostgreSQL database infrastructure for production. Current system uses SQLite which crashes with 26K products. PostgreSQL will handle 424K+ records and scale to 10K+ retailers.

## Acceptance Criteria

- [ ] PostgreSQL server online (AWS RDS or Docker)
- [ ] Database `enterprise_retail` created
- [ ] Connection tested from API application
- [ ] Connection pooling configured (pool_size=10)
- [ ] Backup strategy configured & tested
- [ ] Documentation: connection string, credentials, port
- [ ] Team can connect to database

## Technical Specifications

**Option A: AWS RDS (Recommended for Production)**
```
Instance Class: db.t3.micro
Storage: 20 GB (auto-scaling enabled)
Engine: PostgreSQL 13+
Multi-AZ: No (for dev, enable for production)
Backup retention: 7 days
Port: 5432
```

**Option B: Docker (Development)**
```
Container: postgres:13-alpine
Port: 5432
Volume: postgres_data
Environment: POSTGRES_PASSWORD, POSTGRES_DB
```

## Setup Steps

### Step 1: Launch PostgreSQL
**AWS RDS:**
```bash
# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier enterprise-retail-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username postgres \
  --master-user-password [SECURE_PASSWORD] \
  --allocated-storage 20
```

**Docker:**
```bash
docker run -d \
  --name postgres_enterprise \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=enterprise_retail \
  -p 5432:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:13-alpine
```

### Step 2: Create Database
```sql
CREATE DATABASE enterprise_retail;
CREATE USER app_user WITH PASSWORD 'app_password';
ALTER ROLE app_user SET client_encoding TO 'utf8';
ALTER ROLE app_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE app_user SET default_transaction_deferrable TO on;
ALTER ROLE app_user SET default_transaction_deferrable TO on;
GRANT ALL PRIVILEGES ON DATABASE enterprise_retail TO app_user;
```

### Step 3: Configure Connection Pool
```python
# In main.py
from sqlalchemy.pool import QueuePool

DATABASE_URL = "postgresql://app_user:app_password@localhost:5432/enterprise_retail"

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    pool_pre_ping=True
)
```

### Step 4: Test Connection
```bash
# From API server
psql -h localhost -U app_user -d enterprise_retail -c "SELECT 1;"

# Should return: 1
```

### Step 5: Setup Backups
```bash
# Automated daily backups
pg_dump -h localhost -U postgres enterprise_retail > backup_$(date +%Y%m%d).sql
```

## Related Issues
- #1.2 PostgreSQL Schema Creation
- #1.3 Data Migration

## Links
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [AWS RDS Docs](https://docs.aws.amazon.com/rds/)
- [Docker Postgres](https://hub.docker.com/_/postgres/)

## Definition of Done
✅ PostgreSQL server responding to connections  
✅ Database created and ready for schema  
✅ Connection string documented  
✅ Team briefed on credentials (secure storage)  
✅ Backup plan in place
