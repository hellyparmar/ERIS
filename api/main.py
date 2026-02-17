"""
Enterprise Retail Intelligence System v3.0
FASTAPI MAIN APPLICATION

RESTful API connecting Python ML pipeline to React dashboard.
Auto-generates Swagger documentation at /docs

Author: R-DIOS Team
Version: 3.0.0
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os
import logging
from contextlib import asynccontextmanager
from api.services.scheduler import start_scheduler

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import routers
from api.routers import (
    analytics, predictions, data, models, analytics_advanced, inventory, invoices,
    messages, community, health, monitoring, auth, circuit_health,
    sales_analytics, crud_v2,
    dashboard, tally_integration, odoo_sync,
    reports, enterprise, # New router
    weather,  # Weather API router
    pos_auth, inventory_control, customers, loyalty # Phase 1-3 routers
)


# Import middleware
from api.middleware.rate_limiter import APIRateLimitMiddleware

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start Scheduler
    scheduler = start_scheduler()
    yield
    # Shutdown: Stop Scheduler
    scheduler.shutdown()

# Initialize FastAPI app
app = FastAPI(
    title="R-DIOS API",
    description="Enterprise Retail Intelligence System - ML-Powered Analytics API",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS - Allow frontend access
# Configure CORS - Allow frontend access
cors_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:5175",
    "http://127.0.0.1:5175",
    "http://localhost:5176",
    "http://127.0.0.1:5176"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiting
app.add_middleware(APIRateLimitMiddleware, requests_per_minute=100)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc) if os.getenv('ENVIRONMENT') == 'development' else "An error occurred"
        }
    )

# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "version": "3.0.0",
        "environment": os.getenv('ENVIRONMENT', 'development')
    }

# Include routers
# Authentication (public endpoints - no auth required)
app.include_router(auth.router, tags=["Authentication"])

# JWT Authentication Router (DISABLED - using unified auth.py)
# from api.routers import auth_login
# app.include_router(auth_login.router, tags=["JWT Authentication"])

# Health & Monitoring (public for load balancers)
app.include_router(health.router, tags=["System Health"])
app.include_router(monitoring.router, tags=["Monitoring"])
app.include_router(circuit_health.router, tags=["Circuit Breakers"])

# WebSocket for Real-time Updates
from api.websocket_manager import websocket_endpoint
@app.websocket("/api/ws")
async def websocket(websocket):
    await websocket_endpoint(websocket)

# Business endpoints (will add auth protection gradually)
from api.routers import pos, alerts
app.include_router(products.router, tags=["Products"])
app.include_router(sales.router, tags=["Sales"])
app.include_router(inventory.router, tags=["Inventory"])
app.include_router(alerts.router, tags=["Alerts"])
app.include_router(forecasting.router, tags=["ML Forecasting"])
app.include_router(reports.router, tags=["Reports"])
app.include_router(pos_auth.router, tags=["POS Authentication"])
app.include_router(inventory_control.router, tags=["Inventory Control"])
app.include_router(customers.router, tags=["Customers"])  # Phase 3
app.include_router(loyalty.router, tags=["Loyalty Program"])    # Phase 3
app.include_router(analytics.router, prefix="/api/v1", tags=["Analytics"])
app.include_router(analytics_advanced.router, tags=["Advanced Analytics"])
app.include_router(weather.router, tags=["Weather"])  # Weather API endpoints
app.include_router(pos.router, tags=["POS"])
app.include_router(invoices.router, tags=["Transaction Engine"])
app.include_router(messages.router, tags=["Communication Hub"])
app.include_router(community.router, tags=["Community Commerce"])
app.include_router(predictions.router, prefix="/api/v1", tags=["Predictions"])
app.include_router(data.router, prefix="/api/v1", tags=["Data Management"])
app.include_router(models.router, prefix="/api/v1", tags=["Model Management"])

# R-DIOS v6.0 Thesis Module Endpoints
app.include_router(sales_analytics.router, tags=["Sales Analytics"])
app.include_router(crud_v2.router, tags=["CRUD v2"])
app.include_router(tally_integration.router, tags=["Tally Integration"])
app.include_router(odoo_sync.router, tags=["Odoo Sync"])
app.include_router(reports.router, tags=["Reports"])
app.include_router(enterprise.router, tags=["Enterprise"])

# Loyalty Program (Next-Gen Loyalty Module)
from api.routers import loyalty
app.include_router(loyalty.router, tags=["Loyalty Program"])

# Export functionality
from api.routers import export
app.include_router(export.router, tags=["Export"])

# Import and register new analytics routers
from api.routers import inventory_analytics, customer_analytics
logger.info("Registering Inventory and Customer Analytics routers")
app.include_router(inventory_analytics.router, tags=["Inventory Analytics"])
app.include_router(customer_analytics.router, tags=["Customer Analytics"])

# ML Pipeline Endpoints
from api.routers import forecasting
app.include_router(forecasting.router, tags=["ML Forecasting"])

# Invoicing & Billing (Phase 2B)
from api.routers import invoicing_v2
app.include_router(invoicing_v2.router, tags=["Invoicing & Billing"])

# POS Integration (Phase 2B - POS Integration)
from api.routers import pos_integration
app.include_router(pos_integration.router, tags=["POS Integration"])

# Bill Management (Phase 2B - Bill Management)
from api.routers import bill_management
app.include_router(bill_management.router, tags=["Bill Management"])

# Causal Inference Endpoints
from api.routers import causal
app.include_router(causal.router, tags=["Causal Inference"])

# Unified Dashboard
from api.routers import dashboard
app.include_router(dashboard.router, tags=["Dashboard"])

# AI Assistant
from api.routes import ai_assistant
app.include_router(ai_assistant.router, tags=["AI Assistant"])

# Advanced Forecasting (Prophet)
from api.routers import forecasting_advanced
app.include_router(forecasting_advanced.router, tags=["Advanced Forecasting"])

# Root endpoint
@app.get("/", tags=["System"])
async def root():
    """API root endpoint with documentation links."""
    return {
        "message": "R-DIOS API v3.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

# Petpooja Restaurant API
from api.routes import petpooja
from api.routes import petpooja_menu
app.include_router(petpooja.router, tags=["Petpooja Restaurant"])
app.include_router(petpooja_menu.router, tags=["Petpooja Menu"])
