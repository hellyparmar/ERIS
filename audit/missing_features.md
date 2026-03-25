# Missing Features

The following necessary mechanics were outlined in your phase documentation but are currently unimplemented or disconnected:

1. **Authentication & Authorization Guarding**: 
   The application lacks active JWT enforcement globally. Endpoint protection middleware is largely absent or still buried in the disconnected legacy `backend/app/api/middleware` folder.
   
2. **Point of Sale (POS) Mutator Endpoints**:
   You have the AI Assistant querying database data, but the core system endpoints required to actually log a sale (e.g. `POST /pos/checkout`) are not routed in `main.py`.

3. **Live Dashboard Analytics**:
   Currently returning completely fabricated mock data (`1250000 total_revenue`). The system needs dynamic SQL aggregates resolving real-time data from multitenant tables.

4. **Multi-Tenant Row Level Security (RLS)**:
   The user configuration specifies a Postgres environment with RLS for multi-tenancy, but the active endpoint integrations in `main.py` do not enforce `tenant_id` session verification per request.
