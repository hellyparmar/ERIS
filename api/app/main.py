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

from app.config import settings
from app.db import SessionLocal, create_tables
from app.routers import auth, catalog, imports, insights, inventory, outlets, partners, sales
from app.routers import settings as settings_router
from app.state import seeding_state, set_seeding

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("eris")
WEB_DIST = Path(__file__).resolve().parents[2] / "web" / "dist"


def _bootstrap() -> None:
    """Create tables; generate demo data on an empty database; keep an untouched demo current."""
    from app.models import User
    from app.seed.refresh import shift_demo_dates

    create_tables()
    with SessionLocal() as db:
        has_users = db.scalar(select(func.count(User.id))) or 0
        if has_users:
            try:
                shift_demo_dates(db)
            except Exception:  # never block startup
                log.exception("demo date refresh failed")
            return
    if not settings.SEED_DEMO_DATA:
        log.warning("Empty database and SEED_DEMO_DATA=false: run `python -m app.seed` or create an admin user.")
        return

    def seed() -> None:
        from app.seed.generator import generate_demo_data

        set_seeding(True, "Generating demo data (about a minute)...")
        try:
            with SessionLocal() as db:
                generate_demo_data(db, days=settings.SEED_DAYS, seed=settings.SEED_RANDOM_STATE,
                                   log=lambda m: (log.info(m), set_seeding(True, m.strip())))
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
    version="2.0.0",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

for r in (auth, settings_router, outlets, catalog, partners, inventory, sales, imports, insights):
    app.include_router(r.router)


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
