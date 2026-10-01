"""Dashboard, analytics, forecasting, alerts and the AI assistant."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import ChatMessage, Sale, User
from app.schemas import ChatIn
from app.security import get_current_user, scoped_outlet_ids
from app.services import analytics as A
from app.services import forecasting as F
from app.services.alerts import compute_alerts
from app.services.assistant import engine, llm

router = APIRouter(prefix="/api", tags=["insights"])


def _range(db: Session, period: str | None, start: date | None, end: date | None) -> A.DateRange:
    return A.resolve_period(db, period, start, end)


# ------------------------------------------------------------------------------------------ dashboard
@router.get("/dashboard")
def dashboard(period: str = "30d", outlet_id: int | None = None, start: date | None = None, end: date | None = None,
              user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    outlet_ids = scoped_outlet_ids(user, outlet_id)
    rng = _range(db, period, start, end)
    recent = db.scalars(select(Sale).where(Sale.status == "completed", *([Sale.outlet_id.in_(outlet_ids)] if outlet_ids else []))
                        .order_by(Sale.sold_at.desc(), Sale.id.desc()).limit(8)).all()
    forecast = None
    try:
        spec = F.build_spec(db, "total", None, outlet_ids)
        fc = F.forecast_series(db, spec, horizon=14)
        forecast = {"summary": fc["summary"], "forecast": fc["forecast"], "model_label": fc["model_label"],
                    "events": fc["events"]}
    except Exception:
        pass
    return {
        "range": rng.as_dict(),
        "data_as_of": A.anchor_date(db).isoformat(),
        "kpis": A.kpis_with_comparison(db, rng, outlet_ids),
        "trend": A.revenue_series(db, rng, outlet_ids, "week" if rng.days > 92 else "day"),
        "previous_trend": A.revenue_series(db, rng.previous(), outlet_ids, "week" if rng.days > 92 else "day"),
        "top_products": A.top_products(db, rng, outlet_ids, 6),
        "outlets": A.outlet_performance(db, rng, outlet_ids),
        "categories": A.category_breakdown(db, rng, outlet_ids),
        "payments": A.payment_mix(db, rng, outlet_ids),
        "recent_sales": [{"id": s.id, "invoice_no": s.invoice_no, "outlet": s.outlet.name, "sold_at": s.sold_at.isoformat(),
                          "total": s.total, "items": s.items_count, "payment_method": s.payment_method,
                          "customer": s.customer.name if s.customer else None, "status": s.status} for s in recent],
        "alerts": compute_alerts(db, outlet_ids)[:6],
        "forecast": forecast,
    }


@router.get("/alerts")
def alerts(outlet_id: int | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return compute_alerts(db, scoped_outlet_ids(user, outlet_id))


# ------------------------------------------------------------------------------------------ analytics
@router.get("/analytics/sales")
def analytics_sales(period: str = "90d", outlet_id: int | None = None, category_id: int | None = None,
                    granularity: str = Query("auto", pattern="^(auto|day|week|month)$"), start: date | None = None,
                    end: date | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    outlet_ids = scoped_outlet_ids(user, outlet_id)
    rng = _range(db, period, start, end)
    gran = granularity if granularity != "auto" else ("month" if rng.days > 180 else "week" if rng.days > 60 else "day")
    return {
        "range": rng.as_dict(), "granularity": gran,
        "kpis": A.kpis_with_comparison(db, rng, outlet_ids),
        "series": A.revenue_series(db, rng, outlet_ids, gran, category_id=category_id),
        "channels": A.channel_mix(db, rng, outlet_ids),
        "payments": A.payment_mix(db, rng, outlet_ids),
        "baskets": A.basket_distribution(db, rng, outlet_ids),
        "heatmap": A.hourly_heatmap(db, rng, outlet_ids),
    }


@router.get("/analytics/products")
def analytics_products(period: str = "90d", outlet_id: int | None = None, start: date | None = None,
                       end: date | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    outlet_ids = scoped_outlet_ids(user, outlet_id)
    rng = _range(db, period, start, end)
    abc = A.abc_analysis(db, rng, outlet_ids)
    prev = {p["product_id"]: p for p in A.top_products(db, rng.previous(), outlet_ids, 10_000)}
    for p in abc["products"]:
        before = prev.get(p["product_id"])
        p["change_pct"] = A.pct_change(p["revenue"], before["revenue"]) if before else None
    return {"range": rng.as_dict(), **abc, "categories": A.category_breakdown(db, rng, outlet_ids),
            "affinity": A.product_affinity(db, rng, outlet_ids, limit=15)}


@router.get("/analytics/outlets")
def analytics_outlets(period: str = "90d", start: date | None = None, end: date | None = None,
                      user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    outlet_ids = scoped_outlet_ids(user)
    rng = _range(db, period, start, end)
    gran = "month" if rng.days > 180 else "week" if rng.days > 45 else "day"
    outlets = A.outlet_performance(db, rng, outlet_ids)
    series = {o["outlet_id"]: A.revenue_series(db, rng, [o["outlet_id"]], gran) for o in outlets}
    merged: dict[str, dict] = {}
    for o in outlets:
        for point in series[o["outlet_id"]]:
            merged.setdefault(point["date"], {"date": point["date"]})[o["name"]] = point["revenue"]
    return {"range": rng.as_dict(), "granularity": gran, "outlets": outlets,
            "series": sorted(merged.values(), key=lambda r: r["date"])}


@router.get("/analytics/customers")
def analytics_customers(period: str = "90d", outlet_id: int | None = None, start: date | None = None,
                        end: date | None = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    outlet_ids = scoped_outlet_ids(user, outlet_id)
    rng = _range(db, period, start, end)
    return {"range": rng.as_dict(), **A.customer_segments(db, outlet_ids),
            "repeat": A.repeat_rate(db, rng, outlet_ids), "top": A.top_customers(db, rng, outlet_ids, 15)}


# ------------------------------------------------------------------------------------------ forecasting
@router.get("/forecast/models")
def forecast_models(_: User = Depends(get_current_user)):
    return [{"id": m, "label": F.MODEL_LABELS[m]} for m in F.available_models()]


@router.get("/forecast")
def forecast(scope: str = Query("total", pattern="^(total|outlet|category|product)$"), target_id: int | None = None,
             outlet_id: int | None = None, horizon: int = Query(30, ge=7, le=90), model: str = "auto",
             user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    outlet_ids = scoped_outlet_ids(user, outlet_id)
    if scope == "outlet":
        target_id = target_id or (outlet_ids[0] if outlet_ids else None)
    try:
        spec = F.build_spec(db, scope, target_id, outlet_ids)
        result = F.forecast_series(db, spec, horizon=horizon, model=model)
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from None
    except PermissionError as exc:
        raise HTTPException(403, str(exc)) from None
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from None
    if scope == "product":
        result = {**result, "stock_plan": F.product_stock_plan(db, spec.product_id, result, outlet_ids)}
    return result


@router.get("/forecast/outlets")
def forecast_by_outlet(horizon: int = Query(30, ge=7, le=90), user: User = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    """Next-period forecast for every outlet (for the comparison table)."""
    out = []
    from app.models import Outlet

    ids = scoped_outlet_ids(user)
    q = select(Outlet).where(Outlet.is_active.is_(True)).order_by(Outlet.id)
    if ids:
        q = q.where(Outlet.id.in_(ids))
    for o in db.scalars(q).all():
        try:
            fc = F.forecast_series(db, F.build_spec(db, "outlet", o.id, None), horizon=horizon)
            sel = next(e for e in fc["evaluation"] if e.get("selected"))
            out.append({"outlet_id": o.id, "outlet": o.name, "forecast_total": fc["summary"]["horizon_total"],
                        "last_period": fc["summary"]["last_30_days"] if horizon >= 30 else fc["summary"]["last_7_days"],
                        "change_pct": fc["summary"]["change_vs_last_30_pct"] if horizon >= 30 else fc["summary"]["change_vs_last_7_pct"],
                        "model": fc["model_label"], "wape": sel.get("wape")})
        except ValueError:
            continue
    return out


# ------------------------------------------------------------------------------------------ assistant
@router.post("/assistant/chat")
def chat(body: ChatIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return engine.answer(db, user, body.message)


@router.get("/assistant/history")
def chat_history(limit: int = Query(40, le=200), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    msgs = db.scalars(select(ChatMessage).where(ChatMessage.user_id == user.id).order_by(ChatMessage.id.desc())
                      .limit(limit)).all()
    return [{"id": m.id, "role": m.role, "content": m.content, **(m.payload or {}),
             "created_at": m.created_at.isoformat() if m.created_at else None} for m in reversed(msgs)]


@router.delete("/assistant/history")
def clear_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.execute(delete(ChatMessage).where(ChatMessage.user_id == user.id))
    db.commit()
    return {"ok": True}


@router.get("/assistant/status")
def assistant_status(_: User = Depends(get_current_user)):
    st = llm.status(force=True)
    return {"engine": "ERIS analytics engine" + (f" + {st['model']} (Ollama)" if st["available"] else ""),
            "llm": st,
            "suggestions": ["How is business this week?", "What should I reorder?", "Forecast sales for next week",
                            "Top 5 products this month", "Which outlet performed best last month?",
                            "Which customers are at risk?", "How can I increase sales?",
                            "Which products are bought together?"]}

