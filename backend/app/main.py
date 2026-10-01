from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
import logging
import asyncio
import uuid
import os
from typing import Optional
from urllib.parse import urlparse

from app.database import init_db, healthcheck_db
from app.core.config import settings
from app.core.logging_config import setup_logging

from app.services.scheduler import start_scheduler
from app.middleware.rate_limiter import limiter

setup_logging(settings.ENVIRONMENT)
logger = logging.getLogger(__name__)

DISALLOWED_PLACEHOLDERS = {
    "change_me",
    "change_me_or_leave_blank",
    "changeme",
    "your_secret_key",
    "your-secret-key",
    "your-super-secret-key",
    "dev_secret",
    "secret",
    "placeholder",
    "dummy",
    "xxx",
    "todo",
    "replace_me",
}


def is_placeholder_secret(val: Optional[str]) -> bool:
    if not val or not str(val).strip():
        return True
    cleaned = str(val).strip().lower()
    return cleaned in DISALLOWED_PLACEHOLDERS or cleaned.startswith("change_me")


def validate_required_env_vars() -> None:
    missing = []
    database_url = os.getenv("DATABASE_URL")
    jwt_secret = os.getenv("JWT_SECRET_KEY") or os.getenv("JWT_SECRET")

    if is_placeholder_secret(database_url):
        missing.append(
            "DATABASE_URL: PostgreSQL connection string (postgresql+asyncpg://...) - missing or placeholder value"
        )
    if is_placeholder_secret(jwt_secret):
        missing.append(
            "JWT_SECRET / JWT_SECRET_KEY: JWT signing key (min 32 chars for production) - missing or placeholder value"
        )
    if missing:
        error_msg = (
            "\n" + "=" * 70 + "\n"
            "CRITICAL: Missing or placeholder required environment variables at startup\n"
            "=" * 70 + "\n"
        )
        for var_desc in missing:
            error_msg += f"  * {var_desc}\n"
        error_msg += "\nSet real credentials in your .env file or environment variables.\n" + "=" * 70 + "\n"
        logger.critical(error_msg)
        raise RuntimeError(error_msg)
    logger.info("Environment variables validation successful")


async def check_database_connection() -> bool:
    try:
        max_retries = 5
        retry_delay = 2
        for attempt in range(max_retries):
            is_healthy = await healthcheck_db()
            if is_healthy:
                logger.info("Database connection successful")
                return True
            if attempt < max_retries - 1:
                logger.warning(f"Database connection attempt {attempt + 1}/{max_retries} failed, retrying...")
                await asyncio.sleep(retry_delay)
        logger.error("Database connection failed after all retries")
        return False
    except Exception as e:
        logger.error(f"Database health check exception: {e}")
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("ERIS API Starting Up")
    logger.info("=" * 60)
    try:
        validate_required_env_vars()
        if settings.ENVIRONMENT != "test":
            logger.info("Initializing database models...")
            await init_db()

            logger.info("Bootstrapping essential records...")
            from app.database import AsyncSessionLocal
            from app.seed_database import bootstrap_essentials

            async with AsyncSessionLocal() as session:
                await bootstrap_essentials(session)

            logger.info("Checking database connectivity...")
            db_ok = await check_database_connection()
            if not db_ok:
                logger.warning("Database connection check failed, continuing startup")
            start_scheduler()
        else:
            logger.info("Test environment: external startup services are disabled")
        logger.info("=" * 60)
        logger.info("ERIS API Ready")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"Startup error: {e}", exc_info=True)
        raise
    yield
    logger.info("ERIS API shutting down...")


app = FastAPI(title="ERIS API", description="Enterprise Retail Intelligence System", version="1.0.0", lifespan=lifespan)


def add_request_id_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


if settings.ENVIRONMENT == "production":
    allowed_hosts = ["localhost", "127.0.0.1", "*.onrender.com"]
    if settings.ALLOWED_ORIGINS and settings.ALLOWED_ORIGINS != "*":
        allowed_hosts.extend(
            parsed.hostname
            for origin in settings.ALLOWED_ORIGINS.split(",")
            if (parsed := urlparse(origin.strip())).hostname
        )
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=sorted(set(allowed_hosts)),
    )
    logger.info("TrustedHost middleware enabled")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[host.strip() for host in settings.ALLOWED_ORIGINS.split(",")]
    if settings.ALLOWED_ORIGINS and settings.ALLOWED_ORIGINS != "*"
    else ["http://localhost:5173", "http://localhost:3000", "http://localhost:4173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info("CORS configured")

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
logger.info("Rate limiting middleware enabled")

add_request_id_middleware(app)
logger.info("Request ID tracking enabled")


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please try again later."},
        headers={"Retry-After": "60", "X-Request-ID": getattr(request.state, "request_id", "unknown")},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"Unhandled exception for request {request_id}: {exc}", exc_info=True)
    content = {"error": "Internal server error", "request_id": request_id, "status": 500}
    if settings.ENVIRONMENT != "production":
        content["detail"] = str(exc)

    return JSONResponse(status_code=500, content=content, headers={"X-Request-ID": request_id})


from app.api_router_registry import api_router  # noqa: E402 - routes mount after middleware and handlers

# All endpoints are mounted under the canonical /api/v1 prefix
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ERIS API", "version": "1.0.0", "environment": settings.ENVIRONMENT}


@app.get("/")
async def root():
    return {
        "message": "ERIS API is running",
        "documentation": "/docs",
        "service": "Enterprise Retail Intelligence System",
    }
