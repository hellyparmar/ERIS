from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from slowapi import Limiter
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging
import asyncio
import sys
import uuid

from app.database import init_db, healthcheck_db
from app.core.config import settings
from app.core.logging_config import setup_logging

from app.services.scheduler import start_scheduler

setup_logging(settings.ENVIRONMENT)
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)


def validate_required_env_vars() -> None:
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
            error_msg += f"  * {var_desc}\n"
        error_msg += "\nSet these in your .env file or environment variables.\n" + "=" * 70 + "\n"
        logger.critical(error_msg)
        sys.exit(1)
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
        scheduler = start_scheduler()
        logger.info("=" * 60)
        logger.info("ERIS API Ready")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"Startup error: {e}", exc_info=True)
        raise
    yield
    logger.info("ERIS API shutting down...")


app = FastAPI(
    title="ERIS API",
    description="Enterprise Retail Intelligence System",
    version="1.0.0",
    lifespan=lifespan
)


def add_request_id_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


if settings.ENVIRONMENT == "production":
    allowed_hosts = []
    if settings.ALLOWED_ORIGINS and settings.ALLOWED_ORIGINS != "*":
        allowed_hosts = [
            host.strip().replace("http://", "").replace("https://", "")
            for host in settings.ALLOWED_ORIGINS.split(",")
        ]
    allowed_hosts.extend(["localhost", "127.0.0.1", "0.0.0.0", "*"])
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=allowed_hosts if allowed_hosts else ["*"]
    )
    logger.info("TrustedHost middleware enabled")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        host.strip() for host in settings.ALLOWED_ORIGINS.split(",")
    ] if settings.ALLOWED_ORIGINS and settings.ALLOWED_ORIGINS != "*" else ["http://localhost:5173", "http://localhost:3000", "http://localhost:4173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
logger.info("CORS configured")

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
logger.info("Rate limiting middleware enabled")

from app.middleware.rls_middleware import RLSMiddleware
app.add_middleware(RLSMiddleware)
logger.info("RLS middleware enabled")

add_request_id_middleware(app)
logger.info("Request ID tracking enabled")


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please try again later."},
        headers={"Retry-After": "60", "X-Request-ID": getattr(request.state, "request_id", "unknown")}
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, 'request_id', 'unknown')
    logger.error(f"Unhandled exception for request {request_id}: {exc}", exc_info=True)
    content = {"error": "Internal server error", "request_id": request_id, "status": 500}
    if settings.ENVIRONMENT != "production":
        content["detail"] = str(exc)
        
    return JSONResponse(
        status_code=500,
        content=content,
        headers={"X-Request-ID": request_id}
    )


from app.api_router_registry import api_router

# All endpoints are mounted under the canonical /api/v1 prefix
app.include_router(api_router, prefix="/api/v1")

from app.api.websocket_manager import websocket_endpoint
@app.websocket("/api/ws")
async def websocket(websocket):
    await websocket_endpoint(websocket)

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "ERIS API",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }


@app.get("/")
async def root():
    return {
        "message": "ERIS API is running",
        "documentation": "/docs",
        "service": "Enterprise Retail Intelligence System"
    }


@app.post("/admin/seed-database")
async def seed_database_endpoint():
    try:
        from app.tasks.seed_tasks import run_historical_seed
        # Enqueue the background task
        task = run_historical_seed.delay()
        return {
            "status": "pending",
            "message": "Historical data generation started in background",
            "task_id": task.id
        }
    except Exception as e:
        logger.error(f"Seeding endpoint error: {str(e)}")
        return {"status": "failed", "message": str(e), "task_id": None}

@app.get("/admin/seed-database/{task_id}")
async def check_seed_status(task_id: str):
    from celery.result import AsyncResult
    from app.api.celery_app import celery_app
    
    task_result = AsyncResult(task_id, app=celery_app)
    
    response = {
        "task_id": task_id,
        "status": task_result.status,
        "message": ""
    }
    
    if task_result.status == 'SUCCESS':
        result_data = task_result.result
        response["status"] = result_data.get("status", "success")
        response["message"] = "Seeding completed successfully"
        response["statistics"] = result_data.get("records", {})
        if "errors" in result_data and result_data["errors"]:
            response["errors"] = result_data["errors"]
    elif task_result.status == 'FAILURE':
        response["message"] = str(task_result.result)
    elif task_result.status == 'PROGRESS':
        response["message"] = task_result.info.get('message', 'In progress...') if task_result.info else "In progress..."
        
    return response

