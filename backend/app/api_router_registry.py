from fastapi import APIRouter

from app.routers import (
    admin, analytics, auth, causal_analysis,
    customers, forecasting, gst_billing,
    health as main_health, integrations as main_integrations, inventory, models, notifications,
    sales, webhooks, ai_assistant as ai_assistant_routes
)
from app.routers.inventory import categories_router
from app.routers import (
    alerts, employees, enterprise,
    messages, suppliers, reports_data,
    contacts, outlets, user_settings
)

api_router = APIRouter()

# -----------------------
# AUTHENTICATION
# -----------------------
api_router.include_router(auth.router, tags=["Authentication"])

# -----------------------
# CORE DOMAINS (Consolidated)
# -----------------------
api_router.include_router(sales.router, tags=["Sales"])
api_router.include_router(analytics.router, tags=["Analytics/Dashboard"])
api_router.include_router(forecasting.router, tags=["Forecasting"])
api_router.include_router(customers.router, tags=["Customers"])
api_router.include_router(gst_billing.router, tags=["GST"])
api_router.include_router(notifications.router, tags=["Notifications"])

# -----------------------
# INVENTORY
# -----------------------
api_router.include_router(inventory.router, tags=["Inventory"])
api_router.include_router(categories_router, tags=["Categories"])

# -----------------------
# BILLING & INVOICING
# -----------------------
# Consolidated into gst_billing

# -----------------------
# AI & INTELLIGENCE
# -----------------------
api_router.include_router(ai_assistant_routes.router, tags=["AI Assistant"])
api_router.include_router(models.router, tags=["Model Management"])

# -----------------------
# HEALTH & MONITORING
# -----------------------
api_router.include_router(main_health.router, tags=["Health"])

# -----------------------
# INTEGRATIONS & THIRD-PARTY
# -----------------------
api_router.include_router(main_integrations.router, tags=["Integrations"])

# -----------------------
# OPERATIONS & OTHERS
# -----------------------
api_router.include_router(employees.router, tags=["Employee Management"])
api_router.include_router(suppliers.router, tags=["Supplier Management"])
api_router.include_router(causal_analysis.router, tags=["Causal Analysis"])
api_router.include_router(alerts.router, tags=["Alerts"])
api_router.include_router(messages.router, tags=["Communication Hub"])
api_router.include_router(admin.router, tags=["Admin"])
api_router.include_router(webhooks.router, tags=["Webhooks"])
api_router.include_router(contacts.router, tags=["Contacts"])
api_router.include_router(outlets.router, tags=["Outlets"])
api_router.include_router(user_settings.router, tags=["User Settings"])
api_router.include_router(enterprise.router, tags=["Enterprise"])
api_router.include_router(reports_data.router, tags=["Reports & Data"])