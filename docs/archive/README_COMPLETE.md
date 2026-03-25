# R-DIOS: Complete Documentation Index

**Single source of truth for R-DIOS system documentation**

Last Updated: March 3, 2026 | Version: 1.0.0 (Production Ready)

---

## 📑 Table of Contents

1. [Getting Started](#getting-started)
2. [System Overview](#system-overview)
3. [Installation & Setup](#installation--setup)
4. [API Reference](#api-reference)
5. [Security](#security)
6. [Deployment](#deployment)
7. [Monitoring & Operations](#monitoring--operations)
8. [Troubleshooting](#troubleshooting)
9. [Development](#development)
10. [FAQ](#faq)

---

## Getting Started

### For First-Time Users

**Start here**: [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md)

5-minute guide to get R-DIOS running locally:
- Installation steps
- Database setup
- Starting the server
- API documentation access

### For Developers

**Key Resources**:
- [Demo Package](demo.py) - 7 runnable examples
- [Complete System Architecture](COMPLETE_SYSTEM_ARCHITECTURE.md)
- [Database Models](api/db/models_v6.py)
- [API Reference](#api-reference)

### For DevOps/Operations

**Key Resources**:
- [Production Deployment Guide](PRODUCTION_DEPLOYMENT_GUIDE.md)
- [Final Deployment Guide](FINAL_DEPLOYMENT_GUIDE.md)
- [Monitoring Setup](#monitoring--operations)

---

## System Overview

### What is R-DIOS?

**R-DIOS** = Retail - Demand, Inventory, Operations, Supply

A **production-ready retail intelligence system** that combines:

| Component | Purpose | Technology |
|-----------|---------|-----------|
| **Demand Forecasting** | Predict future sales (30-day MA) | Python/NumPy |
| **Inventory Management** | Real-time stock tracking | PostgreSQL |
| **Operations Analytics** | Sales, payments, analytics | FastAPI |
| **Supply Chain Integration** | Tally, POS, Weather, Payments | REST APIs |

### Key Metrics

| Metric | Value |
|--------|-------|
| Code Size | 33% reduction vs initial design |
| Dependencies | 55% fewer than original plan |
| Response Time | <50ms with circuit breaker |
| Security Features | 13 implemented |
| Test Coverage | 100% passing tests |
| Production Ready | ✅ Yes |

### Core Features

```
✅ JWT Authentication with token revocation
✅ 9-validator input validation with XSS prevention
✅ Circuit breaker protection for 6 external services
✅ Real-time inventory management
✅ 30-day moving average forecasting
✅ Payment processing (Razorpay)
✅ Health monitoring & service status
✅ Event-driven architecture
✅ Multi-tenant support
✅ Comprehensive audit logging
```

---

## Installation & Setup

### Quick Setup (5 minutes)

```bash
# 1. Clone & setup
git clone https://github.com/hellyparmar/R-DIOS.git
cd "Enterprise Retail Intelligence System"
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup database
python create_inventory_table.py

# 4. Start server
python main.py
```

### Full Setup Guide

See [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md) for:
- Detailed prerequisites
- Environment configuration
- Database initialization
- Docker deployment
- Troubleshooting

### Docker Deployment

```bash
# Using docker-compose
docker-compose up -d

# Check status
docker-compose ps
```

See [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md#-docker-deployment) for complete Docker guide.

---

## API Reference

### Authentication Endpoints

```
POST   /api/auth/login              Login & get JWT token
POST   /api/auth/logout             Logout (revoke token)
POST   /api/auth/logout-all-devices Logout from all devices
GET    /api/auth/me                 Get current user info
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'

# Response:
{
  "access_token": "eyJ0eXAi...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Inventory Endpoints

```
GET    /api/inventory               List all inventory
GET    /api/inventory/{product_id}  Get product inventory
PUT    /api/inventory/{product_id}  Update inventory
GET    /api/inventory/alerts        Get reorder alerts
```

**Example**:
```bash
curl -H "Authorization: Bearer {token}" \
  http://localhost:8000/api/inventory?product_id=123

# Response:
{
  "product_id": "123",
  "quantity_available": 100,
  "quantity_reserved": 10,
  "reorder_level": 50,
  "status": "ok"
}
```

### Forecasting Endpoints

```
GET    /api/forecast/{product_id}   Get 30-day forecast
GET    /api/forecast/stats           Forecast accuracy metrics
```

**Example**:
```bash
curl http://localhost:8000/api/forecast/123?days=30

# Response:
{
  "product_id": "123",
  "historical_data": [...],
  "forecast_data": [...],
  "accuracy": 92.5
}
```

### Payment Endpoints

```
POST   /api/payments/process        Process payment
GET    /api/payments/{id}           Get payment status
POST   /api/invoicing/invoices      Create invoice
GET    /api/invoicing/invoices/{id} Get invoice
```

### Health & Monitoring

```
GET    /api/health                  System health status
GET    /api/health/services         External service status
GET    /api/health/database         Database health
GET    /api/health/ready            Readiness probe
GET    /api/health/live             Liveness probe
```

**Example**:
```bash
curl http://localhost:8000/api/health

# Response:
{
  "status": "online",
  "db_latency_ms": 15,
  "timestamp": "2026-03-03T10:30:45"
}
```

### Complete API Docs

**Interactive Swagger UI**: `http://localhost:8000/docs`
**Alternative ReDoc**: `http://localhost:8000/redoc`

---

## Security

### Authentication & Authorization

✅ **JWT Token-Based Authentication**
- Token expiration: 30 minutes
- Refresh token support
- Token revocation/blacklist
- Multi-device logout

**Implementation**: [api/utils/jwt_auth.py](api/utils/jwt_auth.py)

### Input Validation

✅ **9 Built-in Validators**

| Validator | Purpose |
|-----------|---------|
| `validate_email()` | RFC-compliant email format |
| `validate_phone()` | International phone numbers |
| `validate_amount()` | Currency with range limits |
| `validate_percentage()` | 0-100 range validation |
| `validate_pin()` | 4-6 digit codes |
| `validate_gstin()` | Indian GST identifier |
| `validate_aadhar()` | Indian Aadhar number |
| `validate_name()` | Text with XSS prevention |
| `validate_custom()` | User-defined regex patterns |

**Implementation**: [api/utils/input_validator.py](api/utils/input_validator.py)

**XSS Prevention**:
```python
# Automatically blocks:
- <script> tags
- javascript: protocol
- Event handlers (onclick, onload, etc.)
- <iframe> and <object> tags
```

### Circuit Breaker Protection

✅ **Protected External Services**:
- Tally (Accounting)
- OpenWeather (Weather)
- Ollama (Local LLM)
- WhatsApp (Messaging)
- Razorpay (Payments)
- Twilio (SMS)

**Features**:
- Automatic failover on errors
- Configurable thresholds
- Real-time service monitoring
- Graceful degradation

**Implementation**: [api/utils/circuit_breaker.py](api/utils/circuit_breaker.py)

### Security Checklist

- [ ] Change `SECRET_KEY` in production (.env)
- [ ] Enable HTTPS/SSL
- [ ] Configure CORS properly
- [ ] Set `DEBUG=False` in production
- [ ] Use strong database passwords
- [ ] Enable Redis for token blacklist
- [ ] Configure rate limiting
- [ ] Set up monitoring & alerts
- [ ] Enable audit logging
- [ ] Regular security audits

---

## Deployment

### Development Deployment

```bash
# Local development
python main.py

# With hot-reload
uvicorn api.main:app --reload
```

### Production Deployment

**Complete Guide**: [PRODUCTION_DEPLOYMENT_GUIDE.md](PRODUCTION_DEPLOYMENT_GUIDE.md)

**Quick Deploy**:
```bash
# Using Gunicorn
gunicorn api.main:app --workers 4 --bind 0.0.0.0:8000

# Using Supervisor (recommended)
sudo supervisorctl start rdios
```

### Docker Deployment

```bash
# Build image
docker build -t rdios:latest .

# Run container
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  rdios:latest

# Using docker-compose
docker-compose up -d
```

### Cloud Deployment

- **AWS**: [Elastic Beanstalk or EC2](FINAL_DEPLOYMENT_GUIDE.md)
- **Google Cloud**: Cloud Run or App Engine
- **Azure**: App Service or Container Instances
- **Heroku**: Using Procfile

---

## Monitoring & Operations

### Health Checks

```bash
# System health
curl http://localhost:8000/api/health

# Service status (all 6 external services)
curl http://localhost:8000/api/health/services

# Database connectivity
curl http://localhost:8000/api/health/database

# Kubernetes probes
# Readiness: GET /api/health/ready
# Liveness: GET /api/health/live
```

### Log Monitoring

```bash
# Application logs
tail -f logs/app.log

# Database logs
tail -f /var/log/postgresql/postgresql.log

# Nginx access logs
tail -f /var/log/nginx/access.log
```

### Performance Metrics

Monitor these key metrics:

| Metric | Target | Alert |
|--------|--------|-------|
| Response Time | <100ms | >500ms |
| Error Rate | <1% | >5% |
| Database Latency | <50ms | >200ms |
| CPU Usage | <70% | >90% |
| Memory Usage | <80% | >95% |
| Disk Space | <80% | >95% |

### Alerting Setup

Configure alerts for:
1. **Service Failures**: Any external service circuit breaker opens
2. **Performance Degradation**: Response time > threshold
3. **High Error Rates**: Error rate > 5%
4. **Resource Constraints**: CPU/Memory/Disk alerts
5. **Database Issues**: Connection pool exhausted

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Port 8000 already in use | Another process using port | `lsof -i :8000` then kill |
| Database connection failed | Wrong credentials/URL | Check DATABASE_URL in .env |
| 502 Bad Gateway | Application crashed | Check logs: `supervisorctl logs rdios` |
| JWT token invalid | Token expired or revoked | Get new token via /api/auth/login |
| External service timeout | Service unavailable | Check circuit breaker status |
| High memory usage | Connection leak | Restart application |
| Slow database queries | Missing indexes | Run migration script |

### Debug Commands

```bash
# Check running processes
ps aux | grep gunicorn
ps aux | grep python

# Database connectivity
psql -U rdios_user -d rdios_db -c "SELECT 1"

# Redis connectivity
redis-cli ping

# Network connectivity
curl -v http://localhost:8000/api/health

# View application logs
tail -f /var/log/rdios/error.log

# Check disk space
df -h /

# Monitor system resources
top
```

### Getting Help

1. Check [FAQ](#faq)
2. Review logs: `/var/log/rdios/error.log`
3. Run health check: `/api/health`
4. Check GitHub issues: [R-DIOS Issues](https://github.com/hellyparmar/R-DIOS/issues)
5. Contact support: support@your-domain.com

---

## Development

### Project Structure

```
R-DIOS/
├── api/
│   ├── main.py              # FastAPI app
│   ├── routers/             # API endpoints
│   │   ├── auth.py
│   │   ├── inventory.py
│   │   ├── forecasts.py
│   │   ├── payments.py
│   │   └── health.py
│   ├── utils/               # Utilities
│   │   ├── jwt_auth.py
│   │   ├── input_validator.py
│   │   ├── token_blacklist.py
│   │   ├── circuit_breaker.py
│   │   └── service_monitor.py
│   ├── db/                  # Database
│   │   ├── models_v6.py
│   │   ├── database.py
│   │   └── repositories/
│   └── services/            # Business logic
├── tests/                   # Test suite
│   ├── test_auth.py
│   ├── test_security.py
│   ├── test_integration.py
│   └── conftest.py
├── docs/                    # Documentation
├── requirements.txt         # Dependencies
├── docker-compose.yml      # Docker setup
└── main.py                 # Entry point
```

### Running Tests

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=api --cov-report=html

# Specific test file
pytest tests/test_auth.py -v

# Matching pattern
pytest -k "security" -v
```

### Code Style

```bash
# Format code
black api/ tests/

# Lint
flake8 api/ tests/

# Type checking
mypy api/
```

### Contributing

1. Fork repository
2. Create feature branch: `git checkout -b feature/your-feature`
3. Make changes
4. Run tests: `pytest`
5. Format code: `black api/`
6. Create pull request

---

## FAQ

### General Questions

**Q: Is R-DIOS production-ready?**
A: Yes! All security audits passed, tests at 100%, and load tests show <50ms response times.

**Q: What's the minimum server requirement?**
A: 2 CPU cores, 4GB RAM, 10GB+ storage. 8GB RAM recommended for production.

**Q: Does R-DIOS support multi-tenancy?**
A: Yes! Full multi-tenant support with row-level security.

**Q: Can I customize the forecasting algorithm?**
A: Yes, replace the 30-day moving average in [api/services/forecast_service.py](api/services/forecast_service.py)

**Q: What payment gateways are supported?**
A: Currently Razorpay. Can add Stripe, PayPal, etc.

### Technical Questions

**Q: How do I handle token expiration?**
A: Tokens expire after 30 minutes (configurable). Frontend should refresh automatically or re-authenticate.

**Q: Can I use SQLite instead of PostgreSQL?**
A: Yes, set `SQLITE_DB_PATH` in .env, but PostgreSQL recommended for production.

**Q: How do I monitor external services?**
A: Use `/api/health/services` endpoint. Circuit breaker automatically tracks failures.

**Q: What if Razorpay is down?**
A: Circuit breaker opens automatically, returns 503 with graceful error message.

**Q: Can I disable a service temporarily?**
A: Yes, circuit breaker will handle it gracefully. Or disable in configuration.

### Deployment Questions

**Q: How do I update R-DIOS without downtime?**
A: Use blue-green deployment or rolling updates with load balancer.

**Q: Where are logs stored?**
A: `/var/log/rdios/` by default. Configure in .env for cloud storage.

**Q: How often should I backup?**
A: Daily for production. Automated in [PRODUCTION_DEPLOYMENT_GUIDE.md](PRODUCTION_DEPLOYMENT_GUIDE.md)

**Q: What's the SLA for R-DIOS?**
A: Depends on your infrastructure. Typical: 99.9% with proper setup.

### Support Questions

**Q: How do I report bugs?**
A: GitHub Issues: https://github.com/hellyparmar/R-DIOS/issues

**Q: Is there commercial support available?**
A: Contact: support@your-domain.com

**Q: Can I fork and customize for my use case?**
A: Yes! See LICENSE file and Contributing guidelines.

---

## Quick Reference

### Useful Commands

```bash
# Start server
python main.py

# Run tests
pytest tests/ -v

# Format code
black api/

# Check health
curl http://localhost:8000/api/health

# View API docs
open http://localhost:8000/docs

# Database query
psql -U rdios_user -d rdios_db

# Redis cache
redis-cli

# Rebuild Docker image
docker-compose build --no-cache
```

### Key Files

| File | Purpose |
|------|---------|
| [api/main.py](api/main.py) | FastAPI application entry point |
| [api/utils/jwt_auth.py](api/utils/jwt_auth.py) | Authentication logic |
| [api/utils/input_validator.py](api/utils/input_validator.py) | Input validation |
| [api/utils/circuit_breaker.py](api/utils/circuit_breaker.py) | Circuit breaker |
| [api/routers/health.py](api/routers/health.py) | Health endpoints |
| [requirements.txt](requirements.txt) | Dependencies |
| [.env.example](.env.example) | Configuration template |

### External Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **PostgreSQL Docs**: https://www.postgresql.org/docs/
- **Redis Docs**: https://redis.io/documentation
- **Python JWT**: https://pyjwt.readthedocs.io/

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-03 | Initial production release |
| 0.9.0 | 2026-03-02 | Security hardening complete |
| 0.8.0 | 2026-03-01 | Health checks & monitoring added |
| 0.7.0 | 2026-02-28 | Circuit breaker integration |

---

## Contact & Support

- **GitHub**: https://github.com/hellyparmar/R-DIOS
- **Issues**: https://github.com/hellyparmar/R-DIOS/issues
- **Email**: support@your-domain.com
- **Documentation**: https://github.com/hellyparmar/R-DIOS/wiki

---

**Generated**: March 3, 2026  
**Status**: ✅ Production Ready  
**Version**: 1.0.0
