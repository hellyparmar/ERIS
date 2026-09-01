# Deploy Reference (Archived)

The files in this directory are **outdated reference copies** of previous docker-compose
configurations. They are preserved for historical reference but are **not maintained**
and should **not** be used for active development or deployment.

## Active compose file

Use `docker-compose.yml` at the project root — that is the single source of truth.

## Known issues in these archived files

| File | Issue |
|------|-------|
| `docker-compose.prod.yml` | Celery worker uses wrong module path (`api.tasks.celery_app`); uses deprecated `CORS_ORIGINS` env var name |
| `docker-compose.production.yml` | Celery worker uses wrong module path (`app.tasks`); uses `SECRET_KEY` instead of `JWT_SECRET_KEY` |
