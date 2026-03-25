# Production Deployment Checklist - ERIS

This checklist ensures that the Enterprise Retail Intelligence System (ERIS) is correctly hardened, monitored, and scaled for a production environment.

## Pre-Deployment

- [ ] **All tests passing**: Run `python -m pytest tests/test_workflows.py -v` and ensure zero failures.
- [ ] **Security audit complete**: Use `bandit` or `safety` on dependencies.
- [ ] **Credentials rotated and secured**: No hardcoded passwords in `docker-compose.yml`.
- [ ] **Environment variables set correctly**: Ensure `ENVIRONMENT=production`.
- [ ] **Database backups configured**: automated daily snapshots.
- [ ] **Monitoring setup (Prometheus + Grafana)**: Dashboards verified.
- [ ] **Logging configured (centralized)**: `LOG_LEVEL=INFO` or `WARNING`.
- [ ] **Rate limiting tested**: `@limiter` working on auth endpoints.
- [ ] **CORS origins restricted**: `CORS_ORIGINS` set to the production domain.
- [ ] **SSL/TLS certificates obtained**: Let's Encrypt or similar.

## Database

- [ ] **Migrations tested**: `alembic upgrade head` verified on a staging clone.
- [ ] **Connection pooling configured**: `max_overflow=10`, `pool_size=5`.
- [ ] **Backup strategy implemented**: `pg_dump` with S3 storage.
- [ ] **Indexes created for performance**: Verified indexes on `organization_id` and `transaction_date`.

## Performance

- [ ] **API load tested (100+ concurrent users)**: Use `locust` to verify response times.
- [ ] **Database queries optimized**: No N+1 query issues in analytics.
- [ ] **Caching implemented (Redis)**: Cache headers and Redis backend verified.
- [ ] **CDN for static assets (if applicable)**: Cloudfront or Cloudflare.

## Monitoring

- [ ] **Health check endpoint working**: `/health` returning 200.
- [ ] **Metrics being collected**: Prometheus scraping `/metrics`.
- [ ] **Alerts configured (PagerDuty/email)**: Critical thresholds set.
- [ ] **Error tracking (Sentry)**: Sentry DSN configured in `.env`.

## Documentation

- [ ] **API documentation complete**: `/docs` and `/redoc` fully enriched.
- [ ] **Runbooks created**: Disaster recovery, scaling, and rollback.
- [ ] **Architecture diagrams updated**: Reflected in `README.md`.
- [ ] **Change log maintained**: `CHANGELOG.md` updated for v1.0.0.

## Deployment

- [ ] **Docker images built and tagged**: e.g., `eris-backend:v1.0.0`.
- [ ] **docker-compose.yml for production**: Hardened resource limits and policies.
- [ ] **Reverse proxy configured (Nginx)**: Serving over HTTPS.
- [ ] **Firewall rules set**: Only ports 80/443 open to world.
- [ ] **Auto-scaling configured (if cloud)**: K8s or ECS scaling policies.
