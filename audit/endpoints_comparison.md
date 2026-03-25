# Endpoint Verification & Comparison

An analysis of `backend/app/main.py` reveals the following route registrations. 

## Comparison Table

| Endpoint | Expected (from docs) | Implemented | Status |
|---|---|---|---|
| `GET /` | API Root / Ping | Yes (`main.py`) | Active |
| `GET /health` | System Health | Yes (`main.py`) | Active |
| `GET /metrics` | Prometheus Metrics | Yes (`main.py`) | Active |
| `POST /api/v1/assistant/chat` | AI Chat & RAG | Yes (`routers/assistant.py`) | Active |
| `GET /api/v1/notifications/status` | Verification Status | Yes (`routers/notifications.py`) | Active |
| `POST /api/v1/notifications/test-email`| SMTP Gateway | Yes (`routers/notifications.py`) | Active |
| `POST /api/v1/gst/export/gstr1` | Finance Export | Yes (`routers/gst.py`) | Active |
| `POST /api/v1/tally/sync` | Ext Tally Sync | Yes (`routers/integrations.py`) | Active |
| `GET /api/v1/dashboard/stats` | DB Aggregates | **Mocked Only** (`main.py` limit) | Broken / Needs DB |
| `GET /api/v1/dashboard/realtime` | Live Traffic Metrics | **Mocked Only** (`main.py` limit) | Broken / Needs DB |
| `GET /api/v1/loyalty/*` | Udhaar / Credits | **Mocked Only** (`main.py` limit) | Broken / Needs DB |
| `GET /api/v1/pos/*` | Point of Sale | **Missing** | Disconnected |

## Analysis

- **MISSING ENDPOINTS**: The actual POS, Inventory, and User Auth endpoints are entirely missing from `main.py`. They exist locally within the `backend/app/api/routers/` files, but they are not mounted to the FastAPI app!
- **DUPLICATE ENDPOINTS**: There are multiple mock endpoints defined directly in `main.py` (e.g. `get_dashboard_stats`), which should be housed in a registered router (`routers/dashboard.py`).
- **BROKEN ENDPOINTS**: The analytics endpoints are returning static hardcoded arrays (`mock_invoices`) rather than resolving database queries.
