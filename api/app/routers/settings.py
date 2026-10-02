import threading

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import clock
from app.config import settings
from app.db import SessionLocal, get_db
from app.models import Customer, DatasetInfo, Organization, Outlet, Product, PurchaseOrder, Sale, SaleItem, Supplier, User
from app.schemas import OrganizationIn
from app.security import get_current_user, require_admin
from app.services import analytics as A
from app.services import forecasting as F
from app.services.assistant import llm
from app.services.audit import audit
from app.state import seeding_state

router = APIRouter(prefix="/api/settings", tags=["settings"])


def org_dict(org: Organization) -> dict:
    return {k: getattr(org, k) for k in ("id", "name", "industry", "currency", "currency_symbol", "timezone", "email",
                                         "phone", "address", "tax_id", "tax_id_is_demo", "state", "state_code",
                                         "low_stock_cover_days")}


@router.get("/organization")
def get_org(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    org = db.scalar(select(Organization))
    if org is None:
        raise HTTPException(404, "Organization not set up")
    return org_dict(org)


@router.put("/organization")
def update_org(body: OrganizationIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    org = db.scalar(select(Organization))
    if org is None:
        org = Organization(**body.model_dump(), tax_id_is_demo=False)
        db.add(org)
    else:
        if body.tax_id != org.tax_id:
            org.tax_id_is_demo = False  # a GSTIN typed in by the user is no longer the generated demo one
        for k, v in body.model_dump().items():
            setattr(org, k, v)
    db.commit()
    clock.set_timezone(org.timezone)
    return org_dict(org)


@router.get("/gst-states")
def gst_states(_: User = Depends(get_current_user)):
    """GST state codes (used for outlet, organization and customer forms)."""
    from app.services.gst import STATES

    return [{"code": k, "name": v} for k, v in sorted(STATES.items())]


@router.get("/system")
def system_info(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    counts = {
        "outlets": db.scalar(select(func.count(Outlet.id))),
        "products": db.scalar(select(func.count(Product.id))),
        "suppliers": db.scalar(select(func.count(Supplier.id))),
        "customers": db.scalar(select(func.count(Customer.id))),
        "sales": db.scalar(select(func.count(Sale.id))),
        "sale_items": db.scalar(select(func.count(SaleItem.id))),
        "purchase_orders": db.scalar(select(func.count(PurchaseOrder.id))),
        "users": db.scalar(select(func.count(User.id))),
    }
    by_source = dict(db.execute(select(Sale.source, func.count(Sale.id)).group_by(Sale.source)).all())
    ds = db.scalar(select(DatasetInfo).order_by(DatasetInfo.id.desc()))
    dataset = None if ds is None else {
        "data_source": ds.data_source, "generator_version": ds.generator_version, "random_seed": ds.random_seed,
        "generated_at": ds.generated_at.isoformat(), "period_start": ds.period_start.isoformat(),
        "period_end": ds.period_end.isoformat(), "parameters": ds.parameters, "row_counts": ds.row_counts}
    return {
        "app": settings.APP_NAME,
        "database": "SQLite" if settings.is_sqlite else "PostgreSQL",
        "counts": counts,
        "sales_by_source": by_source,
        "dataset": dataset,
        "data_from": (A.first_sale_date(db) or None),
        "data_to": (A.latest_sale_date(db) or None),
        "forecast_models": F.available_models(),
        "assistant": llm.status(),
        "seeding": seeding_state(),
    }


def _run_seed() -> None:
    from app.seed.__main__ import seed_kwargs
    from app.seed.generator import generate_demo_data
    from app.state import set_seeding

    set_seeding(True, "Generating demo data...")
    try:
        with SessionLocal() as db:
            generate_demo_data(db, **seed_kwargs(), log=lambda m: set_seeding(True, m.strip()))
        F.clear_cache()
        A._CACHE.clear()
        set_seeding(False, "Demo data ready")
    except Exception as exc:  # pragma: no cover - surfaced through status
        set_seeding(False, f"Demo data generation failed: {exc}")


@router.post("/demo-data")
def regenerate_demo(_: User = Depends(require_admin)):
    """Wipe everything and regenerate the demo organization (runs in the background, ~1 minute)."""
    if seeding_state()["running"]:
        raise HTTPException(409, "Demo data generation is already running")
    threading.Thread(target=_run_seed, daemon=True).start()
    return {"started": True, "message": "Generating demo data. You will be signed out when it finishes - log in "
                                        "again with the demo accounts."}


@router.post("/clear-transactions")
def clear_transactions(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Start fresh with your own data: removes sales, invoices, purchase orders, stock history, customers and all
    synthetic demand drivers (promotions, prices, weather, stockouts, anomaly labels, dataset provenance), keeps
    outlets, products, suppliers and users, and resets every stock level to zero."""
    from sqlalchemy import delete, insert

    from app.models import (
        AnomalyLabel,
        ChatMessage,
        DatasetInfo,
        ForecastResult,
        ForecastRun,
        InventoryItem,
        Invoice,
        PriceHistory,
        Promotion,
        PurchaseOrderItem,
        StockMovement,
        StockoutEvent,
        WeatherDaily,
    )

    for model in (ChatMessage, Invoice, StockMovement, PurchaseOrderItem, PurchaseOrder, SaleItem, Sale, InventoryItem,
                  Customer, ForecastResult, ForecastRun, StockoutEvent, AnomalyLabel, Promotion, PriceHistory,
                  WeatherDaily, DatasetInfo):
        db.execute(delete(model))
    outlets = db.scalars(select(Outlet.id)).all()
    products = db.execute(select(Product.id, Product.reorder_level)).all()
    rows = [{"outlet_id": o, "product_id": p, "quantity": 0.0, "reorder_level": r} for o in outlets for p, r in products]
    if rows:
        db.execute(insert(InventoryItem), rows)
    audit(db, admin, "data.clear", "database", None, "Cleared all transactions to start with own data")
    db.commit()
    F.clear_cache()
    A._CACHE.clear()
    return {"ok": True}
