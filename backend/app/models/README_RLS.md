# Multi-Tenant Row Level Security (RLS) Guidelines

## Overview
This application enforces multi-tenancy isolation using PostgreSQL Native Row-Level Security (RLS). This ensures that queries executed at the database level cannot access data belonging to other organizations, mitigating the risk of cross-tenant data leakage if application-level filters are missed.

## Important: RLS Coverage Limits
**RLS is explicitly ENFORCED on ONLY the following six core tables:**
1. `outlets`
2. `products`
3. `inventory`
4. `sales_transactions`
5. `customers`
6. `invoices`

**It is NOT enforced on other tables such as `users`, `categories`, `suppliers`, etc.**

### Why?
Enforcing RLS on high-churn transactional data and core business entities provides the highest security return. Applying it to highly shared reference tables or internal mapping tables can lead to operational complexity and performance degradation.

## Adding New Models
If you create a new model that requires strict tenant isolation:
1. Ensure the model inherits a `tenant_id` column mapped to `organizations.tenant_id`.
2. Generate an Alembic migration to enable RLS:
   ```sql
   ALTER TABLE new_table ENABLE ROW LEVEL SECURITY;
   CREATE POLICY new_table_tenant_isolation ON new_table 
       USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
   ```

## Sync / Async Workers
All background jobs (Celery), forecasting tasks, and sync utilities interacting with the protected tables MUST set the `app.current_tenant_id` configuration parameter before executing queries.

- Use the updated `get_db_sync(tenant_id=...)` context manager which automatically provisions the `set_config` parameters for the session.
- Queries executed against these 6 tables without the `app.current_tenant_id` configuration set will throw a `psycopg2.errors.UndefinedObject` error to prevent accidental data spillage.
