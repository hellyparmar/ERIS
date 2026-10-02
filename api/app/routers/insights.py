"""Dashboard, analytics, forecasting, alerts and the AI assistant."""
import threading
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import ChatMessage, ForecastRun, Sale, User
from app.routers.common import get_or_404, page_response, paginate
from app.schemas import ChatIn
from app.security import get_current_user, require_manager, scoped_outlet_ids
from app.services import analytics as A
from app.services import forecasting as F
from app.services.alerts import compute_alerts
from app.services.assistant import engine, llm
from app.state import job_state, set_job

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
        fc = F.forecast_series(db, spec, horizon=14, persist=False)
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
        result = F.forecast_series(db, spec, horizon=horizon, model=model, user_id=user.id)
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
            fc = F.forecast_series(db, F.build_spec(db, "outlet", o.id, None), horizon=horizon, persist=False)
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



# ------------------------------------------------------------------------------------------ model runs
def run_dict(r: ForecastRun, detail: bool = False) -> dict:
    d = {"id": r.id, "run_type": r.run_type, "scope": r.scope, "target": r.target, "series": r.series_label,
         "horizon": r.horizon, "data_start": r.data_start.isoformat() if r.data_start else None,
         "data_end": r.data_end.isoformat() if r.data_end else None, "selected_model": r.selected_model,
         "selected_label": F.MODEL_LABELS.get(r.selected_model, r.selected_model) if r.selected_model else None,
         "model_version": r.model_version, "status": r.status, "error": r.error,
         "duration_seconds": r.duration_seconds, "created_at": r.created_at.isoformat() if r.created_at else None}
    if detail:
        d.update(metrics=r.metrics, parameters=r.parameters, features=r.features,
                 results=[{"date": x.day.isoformat(), "yhat": x.yhat, "lower": x.lower, "upper": x.upper}
                          for x in sorted(r.results, key=lambda x: x.day)])
    else:
        sel = next((m for m in (r.metrics or []) if m.get("selected")), None)
        d["wape"] = sel.get("wape") if sel else None
    return d


def _run_visible(user: User, run: ForecastRun) -> bool:
    """Admins see every run; others only runs limited to outlets they are assigned to (evaluations are org-wide
    model-quality summaries and visible to everyone)."""
    if user.role == "admin" or run.run_type == "evaluation":
        return True
    return bool(run.outlet_ids) and set(run.outlet_ids) <= set(user.outlet_ids)


@router.get("/forecast/runs")
def forecast_runs(run_type: str = "forecast", page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=200),
                  user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = select(ForecastRun).where(ForecastRun.run_type == run_type).order_by(ForecastRun.id.desc())
    if user.role == "admin" or run_type == "evaluation":
        rows, total = paginate(db, q, page, page_size)
        return page_response([run_dict(r[0]) for r in rows], total, page, page_size)
    visible = [r for r in db.scalars(q.limit(2000)).all() if _run_visible(user, r)]
    chunk = visible[(page - 1) * page_size: page * page_size]
    return page_response([run_dict(r) for r in chunk], len(visible), page, page_size)


@router.get("/forecast/runs/{run_id}")
def forecast_run(run_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    run = get_or_404(db, ForecastRun, run_id, "Forecast run")
    if not _run_visible(user, run):
        raise HTTPException(403, "This forecast run covers outlets you are not assigned to")
    return run_dict(run, detail=True)


def _run_evaluation(origins: int, products: int, user_id: int) -> None:
    import time as _t

    from app.db import SessionLocal
    from app.evaluation import evaluate, save_run

    set_job("evaluation", running=True, message="Starting rolling-origin evaluation...", started=_t.time())
    try:
        with SessionLocal() as db:
            t0 = _t.time()
            df = evaluate(db, origins=origins, horizon=28, products=products,
                          progress=lambda m: set_job("evaluation", message=m))
            run_id = save_run(db, df, origins, 28, _t.time() - t0, user_id)
        set_job("evaluation", running=False, message="Evaluation finished", run_id=run_id)
    except Exception as exc:  # surfaced through the status endpoint
        set_job("evaluation", running=False, message=f"Evaluation failed: {exc}")


@router.post("/forecast/evaluations", status_code=202)
def start_evaluation(origins: int = Query(2, ge=1, le=4), products: int = Query(5, ge=0, le=20),
                     user: User = Depends(require_manager)):
    """Run the rolling-origin model comparison in the background (a few minutes)."""
    if job_state("evaluation").get("running"):
        raise HTTPException(409, "An evaluation is already running")
    threading.Thread(target=_run_evaluation, args=(origins, products, user.id), daemon=True).start()
    return {"started": True}


@router.get("/forecast/evaluations/latest")
def latest_evaluation(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    run = db.scalar(select(ForecastRun).where(ForecastRun.run_type == "evaluation").order_by(ForecastRun.id.desc()))
    return {"job": job_state("evaluation"), "run": run_dict(run, detail=True) if run else None}


@router.get("/forecast/stockout-risk")
def stockout_risk(days: int = Query(14, ge=1, le=60), outlet_id: int | None = None,
                  user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = F.stockout_risk(db, days, scoped_outlet_ids(user, outlet_id))
    return {"days": days, "items": rows, "lost_revenue_estimate": round(sum(r["lost_revenue_estimate"] for r in rows), 2)}


# ------------------------------------------------------------------------------------------ anomalies & drivers
@router.get("/anomalies")
def anomalies(period: str = "90d", outlet_id: int | None = None, start: date | None = None, end: date | None = None,
              user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.services import anomalies as AN

    outlet_ids = scoped_outlet_ids(user, outlet_id)
    rng = _range(db, period, start, end)
    found = AN.detect(db, rng.start, rng.end, outlet_ids)
    for a in found:
        a["explanation"] = AN.explain(db, a)
    return {
        "range": rng.as_dict(),
        "method": {"z_threshold": AN.Z_THRESHOLD, "festival_z": AN.FESTIVAL_Z, "heavy_rain_mm": AN.HEAVY_RAIN_MM},
        "anomalies": found,
        "suspicious_lines": AN.suspicious_lines(db, rng.start, rng.end, outlet_ids),
        "evaluation": AN.score_against_labels(db, found, rng.start, rng.end, outlet_ids),
    }


@router.get("/analytics/drivers")
def revenue_drivers(period: str = "7d", outlet_id: int | None = None, start: date | None = None,
                    end: date | None = None, compare_start: date | None = None, compare_end: date | None = None,
                    user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.services import drivers as D

    outlet_ids = scoped_outlet_ids(user, outlet_id)
    rng = _range(db, period, start, end)
    if (compare_start is None) != (compare_end is None):
        raise HTTPException(422, "Give both compare_start and compare_end, or neither.")
    if compare_start and compare_end and compare_start > compare_end:
        compare_start, compare_end = compare_end, compare_start
    return D.explain_change(db, rng.start, rng.end, compare_start, compare_end, outlet_ids)
