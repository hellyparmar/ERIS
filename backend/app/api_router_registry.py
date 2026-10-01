from fastapi import APIRouter

from app.routers import (
    analytics,
    auth,
    customers,
    forecasting,
    gst_billing,
    inventory,
    sales,
    ai_assistant as ai_assistant_routes,
)
from app.routers.inventory import categories_router
from app.routers import alerts, suppliers, reports_data, outlets, user_settings, audit

api_router = APIRouter()

# -----------------------
# AUTHENTICATION
# -----------------------
api_router.include_router(auth.router, tags=["Authentication"])
api_router.include_router(audit.router, tags=["Audit"])

# -----------------------
# CORE DOMAINS (Consolidated)
# -----------------------
api_router.include_router(sales.router, tags=["Sales"])
api_router.include_router(analytics.router, tags=["Analytics/Dashboard"])
api_router.include_router(forecasting.router, tags=["Forecasting"])
api_router.include_router(customers.router, tags=["Customers"])
api_router.include_router(gst_billing.router, tags=["GST"])

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
# -----------------------
# OPERATIONS & OTHERS
# -----------------------
api_router.include_router(suppliers.router, tags=["Supplier Management"])
api_router.include_router(alerts.router, tags=["Alerts"])
api_router.include_router(outlets.router, tags=["Outlets"])
api_router.include_router(user_settings.router, tags=["User Settings"])
api_router.include_router(reports_data.router, tags=["Reports & Data"])
api_router.include_router(reports_data.data_router, tags=["Data imports"])
