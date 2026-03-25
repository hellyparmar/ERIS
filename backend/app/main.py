from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import random
from app.config import settings
from app.utils.errors import (
    AppException, 
    app_exception_handler, 
    http_exception_handler, 
    generic_exception_handler
)
from app.utils.logging import logger
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.middleware.metrics import MetricsMiddleware, metrics_endpoint
from fastapi import Request, HTTPException

# Tally integration router
try:
    from app.routers.integrations import router as tally_integrations_router
    _TALLY_ROUTER_LOADED = True
except ImportError:
    _TALLY_ROUTER_LOADED = False

# GST integration router
try:
    from app.routers.gst import router as gst_router
    _GST_ROUTER_LOADED = True
except ImportError:
    _GST_ROUTER_LOADED = False

# Notification integration router
try:
    from app.routers.notifications import router as notifications_router
    _NOTIFICATIONS_ROUTER_LOADED = True
except ImportError:
    _NOTIFICATIONS_ROUTER_LOADED = False

# AI Assistant router
try:
    from app.routers.assistant import router as assistant_router
    _ASSISTANT_ROUTER_LOADED = True
except ImportError:
    _ASSISTANT_ROUTER_LOADED = False

# Security Middleware
from app.middleware.rate_limiter import limiter

app = FastAPI(
    title="ERIS API",
    description="""
    Enterprise Retail Intelligence System (ERIS) Backend API.
    
    Provides multitenant retail management, AI-driven forecasting, 
    and natural language retail intelligence.
    
    * **Auth**: JWT-based multitenant authentication.
    * **Sales**: POS and history management.
    * **Inventory**: Stock tracking and alerts.
    * **Intelligence**: ARIMA forecasting and SHAP analysis.
    * **Assistant**: RAG-enhanced AI chat.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/v1/openapi.json"
)

# Register Limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Security Middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "testserver", "*.googleapis.com", "host.docker.internal"]
)

# CORS - Restricted origins in production
# In production, set ALLOWED_ORIGINS in .env as a comma-separated list
allowed_origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:3000",
]
if hasattr(settings, "ALLOWED_ORIGINS") and settings.ALLOWED_ORIGINS:
    allowed_origins = settings.ALLOWED_ORIGINS.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins, # Keep existing logic for allowed_origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.middleware.metrics import MetricsMiddleware
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

# Prometheus Metrics Middleware
app.add_middleware(MetricsMiddleware)

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    # Attempt to serve the logo as a favicon
    # We use the generated artifact path for now to ensure it works immediately
    favicon_path = "/home/petpooja/.gemini/antigravity/brain/f4abecea-6f9c-4fbe-aea1-9761c543d9a1/eris_favicon_1774350393895.png"
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    return Response(status_code=204)

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ERIS API - Enterprise Retail Intelligence System</title>
        <style>
            :root {
                --primary: #38bdf8;
                --bg: #0f172a;
                --card: #1e293b;
                --text: #f8fafc;
                --muted: #94a3b8;
            }
            body {
                background-color: var(--bg);
                color: var(--text);
                font-family: 'Inter', -apple-system, system-ui, sans-serif;
                margin: 0;
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
            }
            .container {
                text-align: center;
                background-color: var(--card);
                padding: 3rem;
                border-radius: 1.5rem;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
                border: 1px solid #334155;
                max-width: 500px;
                width: 90%;
            }
            .logo {
                width: 80px;
                height: 80px;
                margin-bottom: 1.5rem;
                border-radius: 50%;
                border: 2px solid var(--primary);
                padding: 5px;
            }
            h1 {
                font-size: 2.5rem;
                margin: 0;
                background: linear-gradient(to right, #38bdf8, #818cf8);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            p {
                color: var(--muted);
                font-size: 1.1rem;
                margin-bottom: 2rem;
            }
            .nav-box {
                display: flex;
                flex-direction: column;
                gap: 1rem;
            }
            .btn {
                background-color: var(--primary);
                color: var(--bg);
                padding: 0.875rem 1.5rem;
                border-radius: 0.75rem;
                text-decoration: none;
                font-weight: 700;
                font-size: 1rem;
                transition: transform 0.2s, background-color 0.2s;
            }
            .btn:hover {
                background-color: #7dd3fc;
                transform: translateY(-2px);
            }
            .btn-secondary {
                background-color: transparent;
                border: 1px solid #475569;
                color: var(--text);
            }
            .btn-secondary:hover {
                background-color: #334155;
            }
            .status {
                margin-top: 2rem;
                font-size: 0.875rem;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 0.5rem;
                color: #4ade80;
            }
            .pulse {
                width: 8px;
                height: 8px;
                background-color: #4ade80;
                border-radius: 50%;
                box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.7);
                animation: pulse 2s infinite;
            }
            @keyframes pulse {
                0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.7); }
                70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(74, 222, 128, 0); }
                100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(74, 222, 128, 0); }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <img src="/favicon.ico" alt="ERIS Logo" class="logo">
            <h1>ERIS API</h1>
            <p>Enterprise Retail Intelligence System v1.0</p>
            <div class="nav-box">
                <a href="/docs" class="btn">Explore API Documentation</a>
                <a href="/redoc" class="btn btn-secondary">System Snapshot (ReDoc)</a>
            </div>
            <div class="status">
                <div class="pulse"></div>
                Backend Operational - Production Ready
            </div>
        </div>
    </body>
    </html>
    """

from app.routers import (
    health, 
    analytics, 
    assistant, 
    auth, 
    inventory, 
    sales, 
    customers, 
    notifications, 
    gst, 
    integrations,
    admin,
    dashboard,
    intelligence
)

# Standard App Routers
app.include_router(health.router) # Provides /health/, /health/ready, /health/live
app.include_router(auth.router)
app.include_router(inventory.router)
app.include_router(sales.router)
app.include_router(customers.router)
app.include_router(analytics.router)
app.include_router(assistant.router)
app.include_router(notifications.router)
app.include_router(gst.router)
app.include_router(integrations.router)
app.include_router(admin.router)
app.include_router(dashboard.router)
app.include_router(intelligence.router)

# Prometheus Metrics Endpoint (Integrated via Middleware)
@app.get("/metrics")
async def get_metrics_endpoint():
    """Scrape endpoint for Prometheus"""
    return metrics_endpoint()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)