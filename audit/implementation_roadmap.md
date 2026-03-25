# Implementation Roadmap (Priority Ordered)

Based on the audit, here is the immediate remediation plan to get ERIS to a stable production candidate:

### Phase 1: Code Deletion & Cleanup (Immediate)
1. Delete the `backend/app/api/` folder. It contains 54+ legacy routers that are dangerously out of sync with your new data models and are not executing anyway.
2. Remove the mock endpoints (like `get_dashboard_stats`) from `main.py`.

### Phase 2: Router Re-Integration
1. Migrate the vital endpoints (POS, Auth, Admin) from the deleted legacy code into the new modular `backend/app/routers/` structure.
2. Ensure they use the central Postgres `SessionLocal` correctly.
3. Wire them into `main.py` using `app.include_router()`.

### Phase 3: Dashboard DB Connections
1. Replace the static arrays in `main.py` and analytics routers with actual SQLAlchemy ORM queries against the live `Sale` and `Product` tables.

### Phase 4: Frontend Pipeline
1. Verify that `npm run dev` in the React frontend successfully contacts the newly mapped endpoints without 404ing.
2. Strip hardcoded environment secrets from `.env.example`.
