"""ERIS - Enterprise Retail Intelligence System: FastAPI application."""
import logging
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select

from app import clock
from app.config import settings
from app.db import SessionLocal, migrate, write_engine
from app.routers import auth, catalog, imports, insights, inventory, outlets, partners, records, sales
from app.routers import settings as settings_router
from app.services import audit as _audit  # noqa: F401  (registers the audit hook)
from app.services import forecasting as F
from app.services import response_cache
from app.state import seeding_state, set_seeding

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("eris")
DEFAULT_SECRET = "dev-only-secret-change-me-in-production-0123456789"
WEB_DIST = Path(__file__).resolve().parents[2] / "web" / "dist"


def _refresh_demo_dates() -> None:
    from app.seed.refresh import shift_demo_dates
    from app.services import analytics as A

    try:
        with SessionLocal(bind=write_engine()) as db:
            if shift_demo_dates(db):
                F.clear_cache()
                A._CACHE.clear()
    except Exception:  # never break the running app
        log.exception("demo date refresh failed")


def _bootstrap() -> None:
    """Create tables; generate demo data on an empty database; keep an untouched demo current."""
    from app.models import User

    if settings.JWT_SECRET_KEY == DEFAULT_SECRET or len(settings.JWT_SECRET_KEY) < 32:
        if settings.ENVIRONMENT == "production":
            raise RuntimeError("Set a strong JWT_SECRET_KEY (32+ random characters) before running in production")
        log.warning("Using a development JWT secret - set JWT_SECRET_KEY for any shared deployment")
    migrate()
    with SessionLocal() as db:
        clock.load_from_db(db)
        has_users = db.scalar(select(func.count(User.id))) or 0
        if has_users:
            # moving a stale demo forward rewrites every dated row: done in the background in one transaction,
            # so the app answers at once (from the previous dates) instead of after a minute on a small server
            threading.Thread(target=_refresh_demo_dates, daemon=True).start()
            return
    if not settings.SEED_DEMO_DATA:
        if settings.INITIAL_ADMIN_EMAIL and settings.INITIAL_ADMIN_PASSWORD:
            from app.manage import create_admin

            create_admin(settings.INITIAL_ADMIN_EMAIL, settings.INITIAL_ADMIN_PASSWORD, "Administrator")
            log.info("Created the first admin %s", settings.INITIAL_ADMIN_EMAIL)
        else:
            log.warning("Empty database and SEED_DEMO_DATA=false: create the first admin with "
                        "`python -m app.manage create-admin --email you@example.com` (or set INITIAL_ADMIN_EMAIL "
                        "and INITIAL_ADMIN_PASSWORD), or generate demo data with `python -m app.seed`.")
        return

    def seed() -> None:
        from app.seed.__main__ import seed_kwargs
        from app.seed.generator import generate_demo_data, release_memory

        set_seeding(True, "Generating demo data (about a minute)...")
        try:
            with SessionLocal() as db:
                generate_demo_data(db, **seed_kwargs(), log=lambda m: (log.info(m), set_seeding(True, m.strip())))
            release_memory()
            set_seeding(False, "Demo data ready")
        except Exception as exc:
            log.exception("demo data generation failed")
            set_seeding(False, f"Demo data generation failed: {exc}")

    threading.Thread(target=seed, daemon=True).start()


@asynccontextmanager
async def lifespan(_: FastAPI):
    _bootstrap()
    yield


app = FastAPI(
    title="ERIS API",
    description="Enterprise Retail Intelligence System - sales, inventory, forecasting and an AI assistant "
                "for multi-outlet retailers.",
    version="3.0.0",
    lifespan=lifespan,
)
app.middleware("http")(response_cache.middleware)  # analytics answers reused while the data is unchanged

# CORS matters only when the web app is hosted on another origin (e.g. Vercel with VITE_API_URL pointing here)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_origin_regex=settings.CORS_ORIGIN_REGEX,
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
                   expose_headers=["Content-Disposition"])  # lets the browser read export file names

for r in (auth, settings_router, outlets, catalog, partners, inventory, sales, imports, insights, records):
    app.include_router(r.router)


@app.exception_handler(F.ForecastBusy)
async def forecast_busy(_: Request, exc: F.ForecastBusy):
    return JSONResponse(status_code=503, content={"detail": str(exc)},
                        headers={"Retry-After": "5", "Cache-Control": "no-store"})


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    log.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Something went wrong on the server. Please try again."})


@app.get("/api/health", tags=["system"])
def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": app.version, "seeding": seeding_state()}


# Serve the built web app (web/dist) from the same process when it exists.
if WEB_DIST.exists():
    app.mount("/assets", StaticFiles(directory=WEB_DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        file = WEB_DIST / path
        if path and file.is_file() and WEB_DIST in file.resolve().parents:
            return FileResponse(file)
        return FileResponse(WEB_DIST / "index.html")
