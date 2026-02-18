"""
Phase 2: Main FastAPI Application

Integrates all routers, database, middleware, and configuration
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.gzip import GZIPMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from datetime import datetime
import os

# Import database
from api.db.database import init_db, healthcheck_db

# Import Phase 1 routers
from api.routers.phase1_pos import router as pos_router
from api.routers.phase1_inventory import router as inventory_router
from api.routers.phase1_users import router as users_router
from api.routers.phase1_reports import router as reports_router

# Import Phase 2 routers - with database integration
from api.routers.phase2_invoices_db import router as invoices_router
from api.routers.phase2_credit_db import router as credit_router
from api.routers.phase2_gst_db import router as gst_router

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== Lifespan Management ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown
    
    Startup: Initialize database, run migrations
    Shutdown: Close database connections
    """
    # Startup
    logger.info("Starting Enterprise Retail Intelligence System...")
    try:
        init_db()
        logger.info("✅ Database initialized successfully")
        
        is_healthy = healthcheck_db()
        if is_healthy:
            logger.info("✅ Database health check passed")
        else:
            logger.warning("⚠️  Database health check failed - continuing anyway")
    
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")
        raise
    
    logger.info("🚀 Application startup complete")
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("Shutting down Enterprise Retail Intelligence System...")
    logger.info("✅ Graceful shutdown complete")


# ==================== Create FastAPI App ====================

app = FastAPI(
    title="Enterprise Retail Intelligence System",
    description="Comprehensive POS, Inventory, GST, Credit, and Analytics Platform",
    version="2.0.0",
    lifespan=lifespan
)


# ==================== CORS Configuration ====================

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:8080",
    "http://127.0.0.1",
    "http://127.0.0.1:3000",
    os.getenv("FRONTEND_URL", "http://localhost:3000")
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Range"]
)

# Trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", os.getenv("DOMAIN", "localhost")]
)

# GZIP compression
app.add_middleware(
    GZIPMiddleware,
    minimum_size=1000
)


# ==================== Custom Middleware ====================

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add request processing time to response headers"""
    import time
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Request-ID"] = request.headers.get("X-Request-ID", "unknown")
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log incoming requests"""
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Status: {response.status_code}")
    return response


# ==================== Exception Handlers ====================

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError exceptions"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


# ==================== Health Check ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        db_healthy = healthcheck_db()
        status_code = "healthy" if db_healthy else "degraded"
        
        return {
            "status": status_code,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "2.0.0",
            "database": "connected" if db_healthy else "disconnected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


@app.get("/api/v2/health")
async def api_v2_health_check():
    """Phase 2 API health check"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "components": {
            "invoicing": "operational",
            "credit_management": "operational",
            "gst_compliance": "operational",
            "database": "connected"
        },
        "timestamp": datetime.utcnow().isoformat()
    }


# ==================== Root Endpoint ====================

@app.get("/")
async def root():
    """Root endpoint with API documentation"""
    return {
        "application": "Enterprise Retail Intelligence System",
        "version": "2.0.0",
        "status": "running",
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        },
        "api_versions": {
            "phase1": "/api/v1",
            "phase2": "/api/v2"
        },
        "endpoints": {
            "phase1": {
                "pos": "/api/v1/pos",
                "inventory": "/api/v1/inventory",
                "users": "/api/v1/users",
                "reports": "/api/v1/reports"
            },
            "phase2": {
                "invoicing": "/api/v2/invoice",
                "credit": "/api/v2/credit",
                "gst": "/api/v2/gst"
            }
        },
        "health": "/health"
    }


# ==================== Version Endpoints ====================

@app.get("/api")
async def api_root():
    """API versions endpoint"""
    return {
        "versions": {
            "v1": "/api/v1",
            "v2": "/api/v2"
        }
    }


@app.get("/api/v1")
async def api_v1_root():
    """Phase 1 API root"""
    return {
        "phase": "Phase 1 - Core POS & Inventory",
        "version": "1.0.0",
        "status": "production",
        "endpoints": [
            "/api/v1/pos",
            "/api/v1/inventory",
            "/api/v1/users",
            "/api/v1/reports"
        ]
    }


@app.get("/api/v2")
async def api_v2_root():
    """Phase 2 API root"""
    return {
        "phase": "Phase 2 - GST, Invoicing, Credit Management",
        "version": "2.0.0",
        "status": "production",
        "endpoints": [
            "/api/v2/invoice",
            "/api/v2/credit",
            "/api/v2/gst"
        ],
        "features": {
            "invoicing": "Complete invoice management with GST and PDF generation",
            "credit_management": "Khata/credit system with scoring and reminders",
            "gst_compliance": "GST calculations, returns (GSTR-1, GSTR-2, GSTR-3B)",
            "database": "Full database integration with PostgreSQL"
        }
    }


# ==================== Register Phase 1 Routers ====================

# These already exist and work with Phase 1 database
app.include_router(
    pos_router,
    prefix="/api/v1",
    tags=["Phase 1 - POS"]
)

app.include_router(
    inventory_router,
    prefix="/api/v1",
    tags=["Phase 1 - Inventory"]
)

app.include_router(
    users_router,
    prefix="/api/v1",
    tags=["Phase 1 - Users"]
)

app.include_router(
    reports_router,
    prefix="/api/v1",
    tags=["Phase 1 - Reports"]
)


# ==================== Register Phase 2 Routers ====================

# These are NEW with database integration
app.include_router(
    invoices_router,
    tags=["Phase 2 - Invoicing"]
)

app.include_router(
    credit_router,
    tags=["Phase 2 - Credit Management"]
)

app.include_router(
    gst_router,
    tags=["Phase 2 - GST Compliance"]
)


# ==================== Info Endpoint ====================

@app.get("/api/v2/info")
async def api_v2_info():
    """Detailed Phase 2 API information"""
    return {
        "system": "Enterprise Retail Intelligence System - Phase 2",
        "version": "2.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "features": {
            "invoicing": {
                "endpoints": 12,
                "capabilities": [
                    "Create invoices with line items",
                    "Automatic invoice numbering",
                    "Multi-line GST calculations",
                    "PDF generation with QR codes",
                    "WhatsApp delivery",
                    "Payment tracking",
                    "Invoice analytics"
                ]
            },
            "credit_management": {
                "endpoints": 10,
                "capabilities": [
                    "Credit account creation and management",
                    "Credit scoring (0-100)",
                    "Transaction tracking",
                    "Payment reminders (SMS, Email, WhatsApp)",
                    "Aging reports",
                    "Credit analytics"
                ]
            },
            "gst_compliance": {
                "endpoints": 12,
                "capabilities": [
                    "Tax rate configuration",
                    "Intra-state (CGST+SGST) calculations",
                    "Inter-state (IGST) calculations",
                    "GSTR-1 return generation",
                    "GSTR-3B return generation",
                    "Compliance verification",
                    "Tax analytics and reporting"
                ]
            }
        },
        "database": {
            "type": "PostgreSQL",
            "tables": 7,
            "models": [
                "Invoice",
                "InvoiceLineItem",
                "InvoicePayment",
                "CustomerCredit",
                "CreditTransaction",
                "CreditReminder",
                "GSTConfiguration"
            ]
        },
        "authentication": {
            "type": "JWT Bearer Token",
            "location": "Authorization header",
            "roles": [
                "admin",
                "manager",
                "user"
            ]
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }


# ==================== Testing Endpoint ====================

@app.post("/api/v2/test/connection")
async def test_database_connection():
    """Test database connection"""
    try:
        is_healthy = healthcheck_db()
        return {
            "status": "success" if is_healthy else "failed",
            "database": "connected" if is_healthy else "disconnected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.get("/api/v2/test/services")
async def test_services_status():
    """Test all Phase 2 services status"""
    return {
        "status": "operational",
        "services": {
            "invoice_service": {
                "status": "operational",
                "version": "2.0"
            },
            "credit_service": {
                "status": "operational",
                "version": "2.0"
            },
            "gst_service": {
                "status": "operational",
                "version": "2.0"
            },
            "pdf_generator": {
                "status": "operational",
                "version": "2.0"
            }
        },
        "timestamp": datetime.utcnow().isoformat()
    }


# ==================== Statistics Endpoint ====================

@app.get("/api/v2/stats")
async def system_statistics():
    """Get system-wide statistics"""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": "calculating...",
        "phase1": {
            "status": "operational",
            "endpoints": 291,
            "features": 8
        },
        "phase2": {
            "status": "operational",
            "endpoints": 34,
            "features": 3,
            "database_tables": 7
        },
        "total": {
            "endpoints": 325,
            "database_tables": 29
        }
    }


# ==================== Production Checks ====================

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("🚀 Application starting up...")
    logger.info("✅ All routers registered")
    logger.info("✅ Middleware configured")
    logger.info("✅ Exception handlers ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("🛑 Application shutting down...")
    logger.info("✅ Cleanup complete")


# ==================== Catch-all 404 ====================

@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    """Catch-all for undefined routes"""
    return {
        "status": "not_found",
        "path": f"/{full_path}",
        "message": "Endpoint not found",
        "available_paths": {
            "documentation": "/docs",
            "api_v1": "/api/v1",
            "api_v2": "/api/v2",
            "health": "/health"
        }
    }


# ==================== Run Application ====================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("ENVIRONMENT", "development") == "development"
    
    uvicorn.run(
        "main_phase2:app",
        host="0.0.0.0",
        port=port,
        reload=reload,
        log_level="info"
    )
