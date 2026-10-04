"""Prepare a ready-to-serve demo database ahead of time (used by the Docker build).

    python -m app.seed.bake [--no-evaluation]

A small hosted instance (e.g. Render's free plan, about a tenth of a CPU) needs about ten minutes to generate the
two-year demo and minutes for its first forecasts. Doing that work while the image is built means a new or
woken-up instance serves complete data at once:

1. generate the synthetic demo (if the database is empty),
2. perform a few genuine operations as the demo users (GST invoices, a part delivery, a stock count, a transfer),
   so Invoices and the Audit log have real entries,
3. pre-compute the forecasts each demo account opens first (total, every outlet, every category and the best
   sellers, for each outlet scope a demo user has), so they are answered from the saved results,
4. store a model-comparison evaluation for the Model comparison page,
5. store every demo user's answers to the pages' default requests in the response cache,
6. compact the SQLite file.
"""
from __future__ import annotations

import argparse
import logging
import time
from datetime import timedelta

from sqlalchemy import func, select

from app.db import SessionLocal, engine, migrate

log = logging.getLogger("eris.bake")
HORIZON = 30  # the longest horizon offered in the app; shorter ones are served from the same result


def _say(msg: str) -> None:
    print(msg, flush=True)


def generate_if_empty() -> None:
    from app.models import User
    from app.seed.__main__ import seed_kwargs
    from app.seed.generator import generate_demo_data, release_memory

    with SessionLocal() as db:
        if db.scalar(select(func.count(User.id))):
            _say("database already has data - generation skipped")
            return
        generate_demo_data(db, **seed_kwargs(), log=_say)
    release_memory()


def outlet_scopes() -> list[list[int] | None]:
    """The distinct outlet sets of the demo accounts (None = all outlets, as an admin sees them)."""
    from app.models import User
    from app.security import scoped_outlet_ids

    scopes: list[list[int] | None] = []
    with SessionLocal() as db:
        for user in db.scalars(select(User).where(User.is_active.is_(True))).all():
            ids = scoped_outlet_ids(user)
            ids = sorted(ids) if ids else None
            if ids not in scopes:
                scopes.append(ids)
    return scopes


def prewarm_forecasts(products: int = 10) -> int:
    from app.models import Category, Outlet, Product, SaleItem
    from app.services import forecasting as F

    done = 0
    t0 = time.time()
    with SessionLocal() as db:
        outlets = db.scalars(select(Outlet.id).where(Outlet.is_active.is_(True)).order_by(Outlet.id)).all()
        categories = db.scalars(select(Category.id).order_by(Category.id)).all()
        best = db.scalars(select(Product.id).join(SaleItem, SaleItem.product_id == Product.id)
                          .group_by(Product.id).order_by(func.sum(SaleItem.line_total).desc()).limit(products)).all()
        specs = [F.build_spec(db, "outlet", o, None) for o in outlets]
        for scope in outlet_scopes():
            specs.append(F.build_spec(db, "total", None, scope))
            specs += [F.build_spec(db, "category", c, scope) for c in categories]
            specs += [F.build_spec(db, "product", p, scope) for p in best]
        for i, spec in enumerate(specs, 1):
            try:
                # whole-business and outlet forecasts appear in the run history; the rest only speed things up
                F.forecast_series(db, spec, horizon=HORIZON, persist=spec.scope in ("total", "outlet"))
                done += 1
            except ValueError as exc:  # too little history for this series - the app explains it the same way
                _say(f"  skipped {spec.label}: {exc}")
            if i % 10 == 0:
                _say(f"  forecasts {i}/{len(specs)} ({time.time() - t0:.0f}s)")
    _say(f"pre-computed {done} forecasts in {time.time() - t0:.0f}s")
    return done


def store_evaluation(origins: int = 2, products: int = 5) -> None:
    from app.evaluation import evaluate, save_run
    from app.models import ForecastRun

    with SessionLocal() as db:
        if db.scalar(select(ForecastRun.id).where(ForecastRun.run_type == "evaluation", ForecastRun.status == "ok")):
            _say("an evaluation is already stored - skipped")
            return
        t0 = time.time()
        df = evaluate(db, origins=origins, horizon=28, products=products, progress=lambda m: None)
        save_run(db, df, origins, 28, time.time() - t0, None)
    _say(f"stored the model-comparison evaluation in {time.time() - t0:.0f}s")


def _client():
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)


def _login(client, email: str) -> dict:
    from app.seed.generator import DEMO_LOGINS, DEMO_PASSWORDS

    key = next(k for _, e, k, _ in DEMO_LOGINS if e == email)
    r = client.post("/api/auth/login", json={"email": email, "password": DEMO_PASSWORDS[key]})
    r.raise_for_status()
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def demo_activity() -> None:
    """A few genuine operations by the demo users, so Invoices and the Audit log are not empty on a fresh demo.

    Everything goes through the API as the respective user (permissions and audit trail included); no sales are
    added, so the demo stays an untouched synthetic dataset.
    """
    from app.models import AuditLog, Customer, InventoryItem, Invoice, PurchaseOrder, Sale

    with SessionLocal() as db:
        if db.scalar(select(func.count(Invoice.id))) or db.scalar(select(func.count(AuditLog.id))):
            _say("demo activity already present - skipped")
            return
        latest = db.scalar(select(func.max(Sale.sale_date)))
        b2b = db.scalars(select(Sale.id).join(Customer, Customer.id == Sale.customer_id).where(
            Customer.customer_type == "business", Sale.status == "completed", Sale.sale_date >= latest - timedelta(days=10))
            .order_by(Sale.id.desc()).limit(8)).all()
        retail = db.scalars(select(Sale.id).where(Sale.status == "completed", Sale.total >= 900, Sale.outlet_id == 1,
                                                  Sale.sale_date >= latest - timedelta(days=3)).order_by(Sale.id.desc()).limit(6)).all()
        open_po = db.scalar(select(PurchaseOrder).where(PurchaseOrder.status == "ordered", PurchaseOrder.outlet_id == 1)
                            .order_by(PurchaseOrder.expected_date))
        po_line = (open_po.id, open_po.items[0].product_id, open_po.items[0].quantity) if open_po and open_po.items else None
        count_fix = db.scalar(select(InventoryItem).where(InventoryItem.outlet_id == 1, InventoryItem.quantity >= 12)
                              .order_by(InventoryItem.product_id))
        count_fix = (count_fix.product_id, count_fix.quantity) if count_fix else None
        transfer = db.scalar(select(InventoryItem).where(InventoryItem.outlet_id == 3, InventoryItem.quantity >= 40)
                             .order_by(InventoryItem.quantity.desc()))
        transfer = transfer.product_id if transfer else None

    done = []
    with _client() as c:
        admin = _login(c, "admin@eris.demo")
        for sale_id in b2b + retail:  # GST invoices for business buyers (B2B) and larger store bills
            if c.post("/api/invoices", headers=admin, json={"sale_id": sale_id}).status_code in (200, 201):
                done.append("invoice")
        manager = _login(c, "priya.and@eris.demo")
        if po_line:  # the outlet manager receives most of a delivery; the rest is still expected
            po_id, product_id, qty = po_line
            arrived = max(1.0, float(int(qty * 0.75)))
            if c.post(f"/api/purchase-orders/{po_id}/receive", headers=manager,
                      json={"items": [{"product_id": product_id, "quantity": arrived}]}).status_code == 200:
                done.append("delivery")
        if count_fix:  # a shelf count finds two units fewer than the system thought
            product_id, qty = count_fix
            if c.post("/api/inventory/adjust", headers=manager, json={
                    "outlet_id": 1, "product_id": product_id, "mode": "set", "quantity": qty - 2,
                    "reason": "adjustment", "note": "Weekly shelf count"}).status_code == 200:
                done.append("count")
        area = _login(c, "arjun.ind@eris.demo")
        if transfer:  # the area manager moves surplus stock from Indiranagar to Whitefield
            if c.post("/api/inventory/transfer", headers=area, json={
                    "from_outlet_id": 3, "to_outlet_id": 5, "product_id": transfer, "quantity": 12,
                    "note": "Rebalance for the weekend"}).status_code == 200:
                done.append("transfer")
    _say(f"demo activity: {len(done)} operations ({', '.join(sorted(set(done)))})")


# The requests the app's pages make by default (captured from the web app), plus the other periods offered on the
# dashboard, drivers and forecasts. Each demo user's answers are stored in the response cache.
WARM_URLS = [
    "/api/alerts",
    *[f"/api/dashboard?period={p}" for p in ("30d", "7d", "90d", "mtd", "ytd")],
    "/api/analytics/sales?period=90d&granularity=auto", "/api/analytics/sales?period=30d&granularity=auto",
    "/api/analytics/products?period=90d", "/api/analytics/outlets?period=90d", "/api/analytics/customers?period=90d",
    *[f"/api/analytics/drivers?period={p}" for p in ("7d", "14d", "30d", "mtd")],
    "/api/anomalies?period=90d", "/api/anomalies?period=30d",
    *[f"/api/forecast?scope=total&horizon={h}&model=auto" for h in (30, 14, 7)],
    "/api/forecast/outlets?horizon=30",
    "/api/inventory/reorder-suggestions",
    "/api/reports/sales-daily?period=30d&limit=100",
]


def warm_cache() -> None:
    """Store every demo user's answers to the pages' default requests (see app/services/response_cache.py)."""
    from app.seed.generator import DEMO_LOGINS

    t0, stored = time.time(), 0
    with _client() as c:
        for _, email, _, _ in DEMO_LOGINS:
            headers = _login(c, email)
            for url in WARM_URLS:
                r = c.get(url, headers=headers)
                stored += r.status_code == 200 and r.headers.get("x-cache") == "miss"
    _say(f"stored {stored} page answers for {len(DEMO_LOGINS)} demo users in {time.time() - t0:.0f}s")


def compact() -> None:
    if engine.dialect.name != "sqlite":
        return
    raw = engine.raw_connection()  # VACUUM cannot run inside a transaction (the pool connection autocommits)
    try:
        cur = raw.cursor()
        cur.execute("VACUUM")
        cur.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        cur.close()
    finally:
        raw.close()
    _say("database compacted")


def main() -> None:
    logging.basicConfig(level=logging.WARNING)
    p = argparse.ArgumentParser(description="Prepare a ready-to-serve ERIS demo database")
    p.add_argument("--no-evaluation", action="store_true", help="skip the model-comparison evaluation")
    p.add_argument("--products", type=int, default=10, help="best-selling products to pre-forecast per scope")
    a = p.parse_args()
    t0 = time.time()
    migrate()
    generate_if_empty()
    demo_activity()
    prewarm_forecasts(a.products)
    if not a.no_evaluation:
        store_evaluation()
    warm_cache()
    compact()
    _say(f"demo database ready in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
