# Historical One-Off Migration Scripts

This directory archives historical one-off migration and consolidation scripts used during early architecture refactoring phases (Phases 0–3) for the Enterprise Retail Intelligence System (ERIS).

## Historical Context & Scope

- **Domain Consolidations**: Merged split router hierarchies (`app/routers/` vs `app/api/routers/`) and service logic (`app/services/` vs `app/api/services/`) across Analytics, Forecasting, Sales, GST, and Customer domains into unified canonical modules.
- **SQLAlchemy Single Base Unification**: Resolved duplicate model class declarations (`Customer`, `Invoice`, `SaleTransaction`, etc.) and eliminated secondary `declarative_base()` calls into the single canonical `app.models.base.Base`.
- **API Registry & POS Auth**: Replaced ad-hoc route mounts with the centralized `app/api_router_registry.py` under the `/api/v1` prefix.

> **Note**: All logic and database migrations performed by these one-off scripts are now permanently integrated into the active codebase and tracked in Alembic migrations (`backend/alembic/versions/`). These scripts are preserved here for historical reference only and should not be executed against live environments.
