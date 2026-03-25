# Cleanup Candidates

The codebase is currently bloated by 8GB largely due to local models, untracked environment caches, or orphaned data.

### 1. Legacy API Directory (`backend/app/api/`)
This entire directory is a primary cleanup candidate. It represents the codebase *before* the Phase 6 refactoring, containing disjointed `routers/`, `services/`, and `events/` that are not imported into the FastAPI application. Removing it will clear 50+ unused python files that are generating false-positives in code searches.

### 2. Mock Data in `main.py`
The `main.py` router file is overloaded with over 100 lines of static hardcoded dictionaries:
- `get_dashboard_stats()`
- `get_recent_sales()`
- `get_low_stock()`
- `get_loyalty_dashboard()`

These implementations should be safely eradicated and moved to real ORM queries.

### 3. Dependency Bloat
Your `/backend/.venv/` environment or `node_modules` might contain extensive bloat. 
Also, you have `.sql` backup files in the project root (`rdios_backup_20260120...`) which should be moved to a secure backup volume rather than tracking in the development folder.
