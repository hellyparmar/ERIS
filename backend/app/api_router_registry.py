from fastapi import APIRouter

from app.routers import (
    admin, analytics, auth, pos_auth, causal_analysis,
    customers, forecasting, gst_billing,
    health as main_health, integrations as main_integrations, inventory, models, notifications,
    pos_dayclose, pos_override, pos_sales, sales, webhooks, ai_assistant as ai_assistant_routes
)
from app.routers.inventory import categories_router
from app.routers import (
    alerts, employees, enterprise,
    messages, suppliers, tally_integration, reports_data,
    contacts, outlets, user_settings
)

api_router = APIRouter()

# -----------------------
# AUTHENTICATION
# -----------------------
api_router.include_router(auth.router, tags=["Authentication"])
api_router.include_router(pos_auth.router, tags=["POS Authentication"])

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
# INVENTORY & POS
# -----------------------
api_router.include_router(inventory.router, tags=["Inventory"])
api_router.include_router(categories_router, tags=["Categories"])
api_router.include_router(pos_sales.router, tags=["POS Sales"])
api_router.include_router(pos_override.router, tags=["POS Manager Override"])
api_router.include_router(pos_dayclose.router, tags=["Cash Register Management"])

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
api_router.include_router(tally_integration.router, tags=["Tally Integration"])

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