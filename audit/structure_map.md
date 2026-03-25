# ERIS Directory Structure Audit

## Current Architecture Map

The backend is currently structured inside `backend/app/` with a mix of active features and legacy components:

```text
backend/app/
├── routers/            # REGISTERED: Active feature routers (assistant, gst, integrations, notifications)
├── models/             # REGISTERED: Database models (database.py, multitenant_models.py, tenant_context.py)
├── ml/                 # REGISTERED: AI logic (llm_provider, rag_service, populate_rag)
├── integrations/       # REGISTERED: External services (tally, gst)
├── notifications/      # REGISTERED: Centralized notification manager
├── tasks/              # REGISTERED: Celery async background workers
├── api/                # UNREGISTERED / DEAD CODE: Legacy v1/v2 routes and services.
│   ├── routers/        # Over 54+ legacy files (inventory_control.py, admin_panel.py, etc.)
│   ├── services/       # Disconnected legacy services
│   ├── middleware/     # Redundant rls_middleware.py
│   └── events/         # Handlers not registered via fastAPI Lifespan
└── main.py             # Active Application Entry Point
```

## Discrepancies vs Expected Documentation
- **Duplicate Routers**: The `app/api/routers/` directory contains an older, flatter version of the codebase. These routers are **not** imported inside `main.py`.
- **Refactoring Midpoint**: The project appears to have successfully migrated core functionalities to modular packages (`app/routers/`, `app/integrations/`) but failed to clean up the legacy `api/` folder.
