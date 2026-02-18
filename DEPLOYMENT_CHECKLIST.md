# DEPLOYMENT CHECKLIST
## Enterprise Retail Intelligence System v3.0

**Deployment Date:** [DATE]  
**Environment:** [DEVELOPMENT/STAGING/PRODUCTION]  
**Deployed By:** [NAME]  
**Approval:** [AUTHORIZED BY]

---

## 🔐 PRE-DEPLOYMENT SECURITY

### Secrets Management
- [ ] All secrets rotated (JWT keys, API keys, DB passwords)
- [ ] Secrets stored in secure vault (not in .env)
- [ ] `.env` file NOT committed to version control
- [ ] `.gitignore` includes `.env`, `*.key`, `*.pem`
- [ ] Production database password changed
- [ ] MSG91 API key verified and valid
- [ ] CORS origins configured for production domain only

### SSL/TLS Certificate
- [ ] SSL certificate obtained and valid
- [ ] Certificate not expired
- [ ] Private key secured
- [ ] Certificate chain complete
- [ ] Certificate auto-renewal configured (if applicable)

### Code Security
- [ ] No hardcoded secrets in code
- [ ] No debug statements in production code
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention verified (parameterized queries)
- [ ] XSS protection enabled
- [ ] CSRF tokens configured
- [ ] Rate limiting enabled (100 req/min minimum)

---

## 📋 PRE-DEPLOYMENT TESTING

### Unit Tests
- [ ] All unit tests passing
- [ ] Test coverage > 80%
- [ ] Error handling tested
- [ ] Edge cases covered

### Integration Tests
- [ ] Database integration tested
- [ ] API endpoints tested
- [ ] Authentication flows verified
- [ ] Manager override workflow tested
- [ ] Day open/close workflow tested
- [ ] Offline queue sync tested
- [ ] WhatsApp integration tested (if live)

### Performance Tests
- [ ] Load test completed (100+ concurrent users)
- [ ] Response times < 500ms (average)
- [ ] P99 response time < 1000ms
- [ ] Database queries optimized
- [ ] Redis cache working
- [ ] Pagination tested

### Security Tests
- [ ] Security testing completed
- [ ] No critical vulnerabilities found
- [ ] OWASP top 10 checklist passed
- [ ] Rate limiting functional
- [ ] Protected endpoints require auth
- [ ] SQL injection tested and blocked
- [ ] CORS policy tested

### End-to-End Tests
- [ ] Complete transaction flow tested
- [ ] Cashier login and transaction flow
- [ ] Manager approval workflow
- [ ] Day open and close
- [ ] Offline transaction sync
- [ ] Receipt generation (print + WhatsApp)
- [ ] Error handling and recovery

---

## 🏗️ INFRASTRUCTURE PREPARATION

### Database
- [ ] PostgreSQL version verified (14.x)
- [ ] Database created and migrated
- [ ] All 22 tables present
- [ ] Indexes created (10 indexes on high-traffic tables)
- [ ] Connection pooling configured
- [ ] Backups configured (daily minimum)
- [ ] Backup tested and verified
- [ ] Point-in-time recovery tested

### Redis
- [ ] Redis installed and configured
- [ ] Connection pooling enabled
- [ ] Persistence (AOF) enabled
- [ ] Memory limit set (512MB minimum)
- [ ] Eviction policy configured (allkeys-lru)
- [ ] Replication configured (if HA needed)

### Server
- [ ] Server specifications met (2GB RAM minimum, 20GB storage)
- [ ] OS security updates applied
- [ ] Firewall configured
- [ ] SSH hardened (key-based auth only)
- [ ] Monitoring agent installed
- [ ] Log rotation configured

### Docker (if using)
- [ ] Docker installed and updated
- [ ] Docker compose file validated
- [ ] Docker images built and tested
- [ ] Docker networks configured
- [ ] Volume permissions set correctly
- [ ] Container health checks working

---

## 📦 DEPLOYMENT STEPS

### Pre-Deployment Backup
- [ ] Database backed up
- [ ] Configuration backed up
- [ ] Previous version backed up
- [ ] Rollback plan documented

### Code Deployment
- [ ] Code pulled from repository
- [ ] `git log` shows correct commit
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Frontend built (`npm run build`)
- [ ] Static files collected
- [ ] Environment variables set
- [ ] Database migrations run (`alembic upgrade head`)
- [ ] Search indexes updated (if applicable)

### Application Startup
- [ ] FastAPI backend started
- [ ] `http://localhost:8000/health` returns 200
- [ ] Frontend accessible at expected URL
- [ ] Celery worker started
- [ ] Celery beat started (if scheduled tasks)
- [ ] All 291 API routes registered
- [ ] All 9 auth endpoints accessible

### Smoke Tests
- [ ] Health endpoint responding
- [ ] Manager login works
- [ ] Cashier login works
- [ ] Token refresh works
- [ ] Dashboard loads
- [ ] API documentation (Swagger) accessible
- [ ] Database queries working

---

## 🔧 POST-DEPLOYMENT VERIFICATION

### Functionality Tests
- [ ] Manager override system operational
  - [ ] Discount approval endpoint working
  - [ ] Refund approval endpoint working
  - [ ] Override codes generating correctly

- [ ] Day operations operational
  - [ ] Day open endpoint working
  - [ ] Day close endpoint working
  - [ ] Cash reconciliation calculating correctly

- [ ] Offline features operational
  - [ ] Offline queue storing transactions
  - [ ] Sync endpoint accessible
  - [ ] Duplicate detection working

- [ ] Receipt delivery operational
  - [ ] WhatsApp messages sending (or queued)
  - [ ] Fallback working if primary fails
  - [ ] Circuit breaker protecting service

### Performance Verification
- [ ] Response times acceptable
- [ ] Database connections stable
- [ ] Redis cache working
- [ ] No memory leaks (monitoring for 1 hour)
- [ ] Error rate < 0.1%
- [ ] Throughput >= 50 req/s

### Logging & Monitoring
- [ ] Logs being written to correct location
- [ ] Log level appropriate (INFO in production)
- [ ] Monitoring dashboard showing metrics
- [ ] Alerts configured for critical issues
- [ ] Error tracking working (Sentry if configured)

### User Acceptance
- [ ] Manager tested complete workflow
- [ ] Cashier tested complete workflow
- [ ] Admin tested all features
- [ ] No critical issues reported
- [ ] Performance acceptable to users

---

## 🚨 ROLLBACK PROCEDURE

### If Issues Found
- [ ] Stop all services
- [ ] Restore database from backup
- [ ] Restore application code from previous version
- [ ] Restart services
- [ ] Verify functionality restored
- [ ] Document root cause
- [ ] Create incident report

### Rollback Commands
```bash
# Restore from backup
pg_restore -d enterprise_retail_db backup.sql

# Revert code
git revert <commit_hash>

# Restart services
docker-compose down
docker-compose up -d
```

---

## 📊 POST-DEPLOYMENT MONITORING (24 hours)

### Hour 1-4: Critical Monitoring
- [ ] Error rate stable (< 0.1%)
- [ ] Response times consistent
- [ ] Database performance stable
- [ ] No unusual memory usage
- [ ] No connection pool exhaustion
- [ ] Authentication working reliably
- [ ] All features operational

### Hour 4-12: Standard Monitoring
- [ ] Transactions processing correctly
- [ ] Offline sync working
- [ ] Receipt delivery (WhatsApp) working
- [ ] No cascading failures
- [ ] System stable under normal load

### Hour 12-24: Extended Monitoring
- [ ] Day close reconciliation working
- [ ] Audit logs being recorded
- [ ] Cache hit rates acceptable (> 70%)
- [ ] Database backups running
- [ ] No unplanned restarts

---

## 📝 DOCUMENTATION

### Updated Documentation
- [ ] Deployment guide updated
- [ ] Configuration documented
- [ ] Known issues documented
- [ ] Troubleshooting guide updated
- [ ] API documentation current
- [ ] Database schema documented

### Knowledge Transfer
- [ ] Operations team trained
- [ ] Monitoring dashboard explained
- [ ] Alert procedures documented
- [ ] Escalation path defined
- [ ] On-call rotation established

---

## 🎯 GO-LIVE DECISION

### Sign-Off
- [ ] All tests passed
- [ ] Security review approved
- [ ] Performance acceptable
- [ ] Stakeholders approved
- [ ] Operations team ready
- [ ] Support team ready

### Final Checklist
- [ ] All checkbox items completed
- [ ] No critical issues outstanding
- [ ] Rollback plan ready
- [ ] Monitoring active
- [ ] Documentation complete

**GO-LIVE APPROVED:** [ ] Yes [ ] No

**Approved By:** _________________________  
**Date/Time:** _________________________

---

## 📞 SUPPORT CONTACTS

### In Case of Issues
- **Primary Contact:** [NAME] - [PHONE]
- **Secondary Contact:** [NAME] - [PHONE]
- **Management:** [NAME] - [EMAIL]
- **Escalation:** [NAME] - [EMAIL]

### Useful Commands

#### View Logs
```bash
docker-compose logs -f backend
docker-compose logs -f celery_worker
tail -f logs/app.log
```

#### Check Health
```bash
curl http://localhost:8000/health
docker-compose ps
docker stats
```

#### Database
```bash
psql -h localhost -U rdios_user -d enterprise_retail_db
```

#### Redis
```bash
redis-cli ping
redis-cli MONITOR
```

---

## 🎉 DEPLOYMENT COMPLETE

**Deployment Status:** [SUCCESS/ROLLBACK]  
**Completion Time:** [TIME]  
**Issues Found:** [NUMBER]  
**Critical Issues:** [NUMBER]  

**Notes:**
```
[Add any additional notes about deployment]
```

---

**Document Version:** 1.0  
**Last Updated:** February 18, 2026  
**Next Review:** [DATE]
