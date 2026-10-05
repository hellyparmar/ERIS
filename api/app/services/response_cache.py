"""Response cache for the heavy, read-only analytics endpoints.

A dashboard or analytics page runs a dozen aggregations over two years of sales: about three seconds of work on a
laptop, half a minute on a small hosted server (Render's free plan has about a tenth of a CPU and forgets its
memory when it sleeps). Answers are therefore kept in the database, per user and request, and reused while the
data is unchanged. The Docker build fills the cache for the demo accounts' default views.

An answer is reused only when all of these are identical to when it was stored:

- the user (their role and outlets decide what they may see),
- the path and query string,
- the data version: newest audit-log entry (every change a user makes is audited), newest stock movement,
  number and newest id of sales and the newest sale date (periods such as "last 30 days" end there),
- the code version (a hash of the application's source files).
"""
from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

from sqlalchemy import delete, func, select
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import Response

log = logging.getLogger(__name__)

# GET endpoints whose answers depend only on the data and the user (exports and lists stay live)
CACHED_PREFIXES = ("/api/dashboard", "/api/alerts", "/api/analytics/", "/api/anomalies", "/api/forecast/outlets",
                   "/api/forecast/stockout-risk", "/api/reports/", "/api/inventory/reorder")
CACHED_EXACT = ("/api/forecast",)
NEVER = ("/export",)
MAX_ROWS = 5000


def _code_version() -> str:
    h = hashlib.sha1()
    for path in sorted(Path(__file__).resolve().parents[1].rglob("*.py")):
        h.update(path.read_bytes())
    return h.hexdigest()[:12]


CODE_VERSION = _code_version()


def is_cacheable(request: Request) -> bool:
    path = request.url.path
    if request.method != "GET" or any(n in path for n in NEVER):
        return False
    return path in CACHED_EXACT or path.startswith(CACHED_PREFIXES)


def _user_id(request: Request) -> int | None:
    from app.security import decode_token

    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        return None
    try:
        return int(decode_token(auth.split(" ", 1)[1], "access")["sub"])
    except Exception:  # invalid or expired: let the endpoint answer (401)
        return None


def data_version(db) -> str:
    from app.models import AuditLog, Sale, StockMovement

    audit = db.scalar(select(func.max(AuditLog.id)))
    moves = db.scalar(select(func.max(StockMovement.id)))
    sales = db.execute(select(func.count(Sale.id), func.max(Sale.id), func.max(Sale.sale_date))).one()
    # deliberately not the calendar date: answers are anchored to the last day of data, so a demo whose data
    # does not change keeps its (pre-computed) answers; any sale, stock change or edit starts a new version
    return f"{CODE_VERSION}|{audit}|{moves}|{sales[0]}|{sales[1]}|{sales[2]}"


def _key(user_id: int, request: Request) -> str:
    query = "&".join(sorted(f"{k}={v}" for k, v in request.query_params.multi_items() if v != ""))
    return hashlib.sha256(f"{user_id}|{request.url.path}|{query}".encode()).hexdigest()


def _lookup(key: str, user_id: int) -> tuple[str | None, str | None]:
    """(data version, cached body). No version when the user may not be served (the endpoint answers 401)."""
    from app.db import SessionLocal
    from app.models import ResponseCache, User

    with SessionLocal() as db:
        user = db.get(User, user_id)
        if user is None or not user.is_active:  # the same check as get_current_user
            return None, None
        version = data_version(db)
        row = db.get(ResponseCache, key)
        return version, (row.body if row is not None and row.version == version else None)


def _store(key: str, version: str, body: str) -> None:
    from app.db import write_session
    from app.models import ResponseCache

    try:
        with write_session() as db:
            row = db.get(ResponseCache, key)
            if row is None:
                db.add(ResponseCache(key=key, version=version, body=body))
            else:
                row.version, row.body = version, body
            db.flush()
            if (db.scalar(select(func.count()).select_from(ResponseCache)) or 0) > MAX_ROWS:
                db.execute(delete(ResponseCache).where(ResponseCache.version != version))
            db.commit()
    except Exception:  # a busy database must never fail the request itself
        log.warning("could not store a cached response", exc_info=True)


async def middleware(request: Request, call_next):
    if not is_cacheable(request):
        return await call_next(request)
    user_id = await run_in_threadpool(_user_id, request)
    if user_id is None:
        return await call_next(request)
    key = _key(user_id, request)
    try:
        version, body = await run_in_threadpool(_lookup, key, user_id)
    except Exception:
        log.warning("response cache unavailable", exc_info=True)
        return await call_next(request)
    if version is None:
        return await call_next(request)
    if body is not None:
        return Response(body, media_type="application/json", headers={"X-Cache": "hit"})
    response = await call_next(request)
    if response.status_code != 200 or not response.headers.get("content-type", "").startswith("application/json") \
            or "no-store" in response.headers.get("cache-control", ""):
        return response
    chunks = [chunk async for chunk in response.body_iterator]
    raw = b"".join(c if isinstance(c, bytes) else c.encode() for c in chunks)
    text = raw.decode()
    try:
        json.loads(text)
    except ValueError:
        return Response(raw, status_code=response.status_code, media_type=response.media_type)
    await run_in_threadpool(_store, key, version, text)
    headers = {k: v for k, v in response.headers.items() if k.lower() not in ("content-length",)}
    headers["X-Cache"] = "miss"
    return Response(raw, status_code=200, headers=headers, media_type="application/json")
