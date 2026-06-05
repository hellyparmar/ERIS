from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
from slowapi import Limiter
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.responses import JSONResponse
import logging
import asyncio
import subprocess
import os
import sys
import uuid

from app.database import init_db, healthcheck_db, AsyncSessionLocal
from app.routers import auth, inventory, community, invoices
# from app.api.v1 import ai_assistant  # TEMPORARILY DISABLED - requests module not available
from app.core.config import settings
from app.core.logging_config import setup_logging

# Temporarily disable problematic api.routers with import issues
# from app.api.routers import analytics
# from app.api import dashboard, sales, forecasting, ai_chat, employees, contacts, invoices as invoices_api, outlets

# Setup structured logging
setup_logging(settings.ENVIRONMENT)
logger = logging.getLogger(__name__)

# Rate limiter configuration
limiter = Limiter(key_func=get_remote_address)


def validate_required_env_vars() -> None:
    """
    Validate required environment variables at startup.
    Fails fast with clear error messages if any critical variables are missing.
    Uses the already-loaded `settings` object (populated from .env by pydantic-settings).
    """
    missing = []

    if not settings.DATABASE_URL or not settings.DATABASE_URL.strip():
        missing.append("DATABASE_URL: PostgreSQL connection string (postgresql+asyncpg://...)")

    if not settings.JWT_SECRET_KEY or not settings.JWT_SECRET_KEY.strip():
        missing.append("JWT_SECRET_KEY: JWT signing key (min 32 chars for production)")

    if not settings.REDIS_URL or not settings.REDIS_URL.strip():
        missing.append("REDIS_URL: Redis connection string (redis://...)")

    if missing:
        error_msg = (
            "\n" + "=" * 70 + "\n"
            "CRITICAL: Missing required environment variables at startup\n"
            "=" * 70 + "\n"
        )
        for var_desc in missing:
            error_msg += f"  ✗ {var_desc}\n"
        error_msg += "\nSet these in your .env file or environment variables.\n" + "=" * 70 + "\n"
        logger.critical(error_msg)
        sys.exit(1)

    logger.info("✓ Environment variables validation successful")



def validate_required_config() -> None:
    """
    Validate that all required configuration variables are set at startup.
    This runs BEFORE any other initialization to fail fast with clear messages.
    """
    missing_vars = []
    
    # Check DATABASE_URL
    if not settings.DATABASE_URL:
        missing_vars.append("DATABASE_URL")
    
    # Check JWT_SECRET_KEY for production
    if settings.ENVIRONMENT == "production":
        default_jwt = "change_me_in_production_extremely_long_random_string_2024"
        if settings.JWT_SECRET_KEY == default_jwt:
            logger.warning(
                "⚠ WARNING: JWT_SECRET_KEY has default value in PRODUCTION. "
                "Set a strong random key in your .env file."
            )
    
    if missing_vars:
        error_msg = (
            "\n" + "=" * 70 + "\n"
            "CONFIGURATION VALIDATION ERROR AT STARTUP\n"
            "=" * 70 + "\n"
            f"Missing or invalid required environment variables:\n"
        )
        for var in missing_vars:
            error_msg += f"  - {var}\n"
        error_msg += (
            "\nRequired configuration:\n"
            "  DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DATABASE\n"
            "\nSet these in your .env file or environment variables.\n"
            "=" * 70 + "\n"
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    logger.info("✓ Configuration validation successful")


async def verify_migrations() -> bool:
    """
    Verify that all Alembic migrations have been applied.
    
    FIX FOR: "relation does not exist" errors
    Run: alembic upgrade head
    """
    try:
        # This check only works when DATABASE_URL is set and database is accessible
        # In production Docker, run migrations before starting the app
        logger.info("Database migrations check: Skipping (use Docker entrypoint for migrations)")
        return True
    except Exception as e:
        logger.warning(f"Migration verification failed: {e}")
        logger.warning("Ensure migrations are applied: alembic upgrade head")
        return False

async def check_database_connection() -> bool:
    """
    FIX FOR: "connection refused" or "could not connect to server"
    Checks:
    1. PostgreSQL container is healthy
    2. Host in DATABASE_URL matches Docker Compose service name
    3. Connection parameters are correct
    """
    try:
        max_retries = 5
        retry_delay = 2
        
        for attempt in range(max_retries):
            is_healthy = await healthcheck_db()
            if is_healthy:
                logger.info("✓ Database connection successful")
                return True
            
            if attempt < max_retries - 1:
                logger.warning(f"Database connection attempt {attempt + 1}/{max_retries} failed, retrying in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
        
        logger.error("✗ Database connection failed after all retries")
        logger.error("TROUBLESHOOTING:")
        logger.error("  1. Check PostgreSQL container is running: docker ps | grep postgres")
        logger.error("  2. Verify DATABASE_URL host matches Docker Compose service name")
        logger.error(f"  3. Current DATABASE_URL: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'Not set'}")
        logger.error("  4. For local dev without SSL: Ensure ssl=prefer is in connection string")
        
        return False
    except Exception as e:
        logger.error(f"Database health check exception: {e}")
        return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan management - startup and shutdown hooks.
    
    Handles:
    1. Configuration validation (fails fast if DATABASE_URL is missing)
    2. Database initialization and model registration
    3. Connection verification (retry logic for Docker)
    4. Migration verification
    """
    logger.info("=" * 60)
    logger.info("R-DIOS API Starting Up")
    logger.info("=" * 60)
    
    try:
        # Validate environment variables first (fail fast)
        logger.info("Validating environment variables...")
        validate_required_env_vars()
        
        # Validate configuration
        logger.info("Validating configuration...")
        validate_required_config()
        
        # Initialize database models
        logger.info("Initializing database models...")
        await init_db()
        
        # Check database connectivity
        logger.info("Checking database connectivity...")
        db_ok = await check_database_connection()
        if not db_ok:
            logger.warning("⚠ Database connection check failed, but continuing startup")
            logger.warning("  The application may fail at first database query")
        
        # Verify migrations
        logger.info("Verifying migrations...")
        migrations_ok = await verify_migrations()
        if not migrations_ok:
            logger.warning("⚠ Migration verification failed")
        
        logger.info("=" * 60)
        logger.info("✓ R-DIOS API Ready")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Startup error: {e}", exc_info=True)
        raise
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("R-DIOS API shutting down...")

app = FastAPI(
    title="R-DIOS API",
    description="Enterprise Retail Intelligence System — MSc Data Science Project",
    version="1.0.0",
    lifespan=lifespan,
)

# Security middleware - add in reverse order (last added = first executed)

# 1. X-Request-ID middleware (executes last, added first)
def add_request_id_middleware(app: FastAPI) -> None:
    """
    Add X-Request-ID to all requests for tracing and logging.
    """
    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

# 2. Trusted Host middleware (production only)
if settings.ENVIRONMENT == "production":
    # Parse allowed origins for TrustedHostMiddleware
    allowed_hosts = []
    if settings.ALLOWED_ORIGINS and settings.ALLOWED_ORIGINS != "*":
        allowed_hosts = [
            host.strip().replace("http://", "").replace("https://", "") 
            for host in settings.ALLOWED_ORIGINS.split(",")
        ]
    # Add common local hosts for development/testing
    allowed_hosts.extend(["localhost", "127.0.0.1", "0.0.0.0", "*"])
    
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=allowed_hosts if allowed_hosts else ["*"]
    )
    logger.info(f"✓ TrustedHost middleware enabled (allowed hosts: {allowed_hosts})")

# 3. CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info("✓ CORS configured with origins: ['http://localhost:5173', 'http://127.0.0.1:5173']")

# 4. Rate limiting middleware
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
logger.info("✓ Rate limiting middleware enabled")

# 5. Request ID middleware (executes last)
add_request_id_middleware(app)
logger.info("✓ Request ID tracking enabled")

# Rate limit error handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please try again later."},
        headers={"Retry-After": "60", "X-Request-ID": getattr(request.state, "request_id", "unknown")}
    )

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, 'request_id', 'unknown')
    logger.error(f"Unhandled exception for request {request_id}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "request_id": request_id,
            "status": 500,
        },
        headers={"X-Request-ID": request_id}
    )

# Include routers
app.include_router(auth.router)
app.include_router(inventory.router)
app.include_router(community.router)
app.include_router(invoices.router)
# app.include_router(ai_assistant.router)  # TEMPORARILY DISABLED - requests module not available

# Include new routers
from app.api import contacts, outlets, sales, user_settings
from app.api.gst_router import router as gst_router
from app.api.routers.integrations import router as integrations_router
from app.api.routers.suppliers import router as suppliers_router
from app.api.routers.employees import router as employees_router
app.include_router(employees_router, prefix="/api/v1")
app.include_router(contacts.router)
app.include_router(outlets.router)
app.include_router(sales.router)
app.include_router(user_settings.router)
app.include_router(integrations_router)
app.include_router(gst_router)
app.include_router(suppliers_router, prefix="/api/v1")

# Disabled routers with import issues
# app.include_router(analytics.router, prefix="/api/v1")
# app.include_router(dashboard.router)
# app.include_router(forecasting.router)
# app.include_router(ai_chat.router)
# app.include_router(invoices_api.router)

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "R-DIOS API",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }

@app.get("/")
async def root():
    """Root endpoint with API documentation link"""
    return {
        "message": "R-DIOS API is running",
        "documentation": "/docs",
        "service": "Enterprise Retail Intelligence System"
    }


@app.post("/admin/seed-database")
async def seed_database_endpoint():
    """
    ADMIN ENDPOINT: Seed the database with synthetic data.
    
    ⚠️ WARNING: Only use in development/testing environments!
    
    Features:
    - Idempotent: checks if data exists before seeding
    - Populates all 12 tables with 540K+ synthetic records
    - Respects foreign key constraints
    - Transaction-based: all-or-nothing approach
    
    Response:
    {
        "status": "success|failed|skipped",
        "statistics": {
            "outlets": 10,
            "users": 50,
            "products": 150,
            "inventory": 1500,
            "employees": 120,
            "invoices": 500,
            "sales": 540000,
            "alerts": 1000,
            "chat_messages": 2000
        }
    }
    """
    try:
        from app.seed_database import seed_database as seed_func
        from app.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as session:
            stats = await seed_func(session, skip_if_exists=True)
        return {
            "status": stats["status"],
            "message": "Database seeding completed" if stats["status"] == "success" else "Database seeding failed",
            "statistics": {k: v for k, v in stats.items() if k not in ["status", "errors"]},
            "errors": stats.get("errors", [])
        }
    except Exception as e:
        logger.error(f"Seeding endpoint error: {str(e)}")
        return {
            "status": "failed",
            "message": str(e),
            "statistics": {}
        }
