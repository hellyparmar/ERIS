"""Anomaly detection on daily outlet revenue + suspicious transactions, scored against ground truth.

Method (robust and explainable, no training needed):
1. Daily revenue per outlet is divided by the outlet's weekday profile (median revenue per weekday / overall median).
2. The de-seasonalised series is compared with a centred 15-day rolling median ("expected level").
3. The log ratio actual/expected is turned into a robust z-score with the median absolute deviation (MAD).
4. |z| >= 3.5 is an anomaly. Festival days must reach |z| >= 6 because the calendar already explains big swings.
5. Open days with zero sales are always anomalies (closure / outage).
6. Dips on days with heavy rain (>= 40 mm in the outlet's city) are reported as "explained by weather": footfall
   genuinely falls on such days, so they are context rather than incidents and are not counted as false alarms.

Transaction-level check: a bill line whose quantity is more than 20x the product's median line quantity (and at
least 30 units) is flagged as a suspicious entry (typical data-entry error such as an extra "00").

When the synthetic generator's AnomalyLabel ground truth exists, detection is scored with precision / recall.
"""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import AnomalyLabel, Customer, Outlet, Product, Sale, SaleItem, WeatherDaily
from app.services import analytics as A
from app.services.holidays import event_window

Z_THRESHOLD = 3.5
FESTIVAL_Z = 6.0  # festival days must be far more extreme to count
HEAVY_RAIN_MM = 40.0


def daily_outlet_revenue(db: Session, start: date, end: date, outlet_ids: list[int] | None) -> pd.DataFrame:
    q = select(Sale.outlet_id, Sale.sale_date, func.sum(Sale.total), func.count(Sale.id)).where(
        A.COMPLETED, Sale.sale_date >= start, Sale.sale_date <= end)
    if outlet_ids:
        q = q.where(Sale.outlet_id.in_(outlet_ids))
    rows = db.execute(q.group_by(Sale.outlet_id, Sale.sale_date)).all()
    return pd.DataFrame(rows, columns=["outlet_id", "day", "revenue", "bills"])


@A.cached
def detect(db: Session, start: date, end: date, outlet_ids: list[int] | None = None) -> list[dict]:
    """Anomalous outlet-days between start and end (history before `start` is used as context).

    Days after the last day that has any sales in the database (e.g. today, before data arrives) are not
    judged - an empty day there means "not loaded yet", not "closed"."""
    latest = A.latest_sale_date(db)
    if latest is None:
        return []
    end = min(end, latest)
    if end < start:
        return []
    ctx_start = start - timedelta(days=70)
    df = daily_outlet_revenue(db, ctx_start, end, outlet_ids)
    if df.empty:
        return []
    outlets = {o.id: o for o in db.scalars(select(Outlet)).all()}
    rain = {(c, d): r for c, d, r in db.execute(select(WeatherDaily.city, WeatherDaily.day, WeatherDaily.rain_mm).where(
        WeatherDaily.day >= start, WeatherDaily.day <= end, WeatherDaily.rain_mm >= HEAVY_RAIN_MM)).all()}
    found = []
    for oid, g in df.groupby("outlet_id"):
        o = outlets.get(oid)
        first_day = max(pd.Timestamp(g["day"].min()), pd.Timestamp(o.opened_on) if o and o.opened_on else pd.Timestamp(ctx_start))
        idx = pd.date_range(first_day, end, freq="D")
        rev = g.set_index(pd.to_datetime(g["day"]))["revenue"].reindex(idx, fill_value=0.0)
        bills = g.set_index(pd.to_datetime(g["day"]))["bills"].reindex(idx, fill_value=0)
        if len(rev) < 35:
            continue
        positive = rev[rev > 0]
        wd = positive.groupby(positive.index.dayofweek).median() / positive.median()
        factor = pd.Series(rev.index.dayofweek, index=rev.index).map(wd).fillna(1.0)
        deseason = rev / factor
        expected_level = deseason.where(deseason > 0).rolling(15, center=True, min_periods=7).median()
        expected = (expected_level * factor).bfill().ffill()
        logr = np.log((rev + 1) / (expected + 1))
        med = float(np.nanmedian(logr[rev > 0]))
        mad = float(np.nanmedian(np.abs(logr[rev > 0] - med))) * 1.4826 or 0.05
        z = (logr - med) / mad
        typical_bills = (bills.rolling(15, center=True, min_periods=7).median()).bfill().ffill()
        for day in rev.index[rev.index >= pd.Timestamp(start)]:
            ev = event_window(day.date())
            zero_day = rev[day] <= 0
            zval = float(z[day])
            limit = FESTIVAL_Z if ev else Z_THRESHOLD
            if not zero_day and abs(zval) < limit:
                continue
            actual, exp = float(rev[day]), float(expected[day])
            rain_mm = rain.get((o.city, day.date())) if o else None
            explained_by = None
            if ev:
                explained_by = f"{ev[0]} period"
            elif rain_mm and actual < exp and not zero_day:
                explained_by = f"heavy rain ({rain_mm:.0f} mm)"
            found.append({
                "day": day.date().isoformat(), "outlet_id": int(oid), "outlet": o.name if o else str(oid),
                "actual": round(actual, 2), "expected": round(exp, 2), "impact": round(actual - exp, 2),
                "change_pct": round((actual - exp) / exp * 100, 1) if exp else None,
                "z_score": round(zval, 1) if np.isfinite(zval) else None,
                "direction": "down" if actual < exp else "up",
                "severity": "critical" if zero_day or abs(zval) >= 6 else "warning",
                "bills": int(bills[day]), "typical_bills": int(typical_bills[day]),
                "festival": ev[0] if ev else None, "explained_by": explained_by,
            })
    found.sort(key=lambda a: (a["day"], a["outlet"]), reverse=True)
    return found


def suspicious_lines(db: Session, start: date, end: date, outlet_ids: list[int] | None = None) -> list[dict]:
    """Bill lines with implausible quantities (likely data-entry errors).

    Business customers (caterers, offices) legitimately buy in bulk, so the typical quantity is computed separately
    for business bills and for retail / walk-in bills.
    """
    is_biz = func.coalesce(Customer.customer_type, "retail") == "business"
    typical_q = select(SaleItem.product_id, is_biz, func.avg(SaleItem.quantity)).join(
        Sale, Sale.id == SaleItem.sale_id).outerjoin(Customer, Customer.id == Sale.customer_id).where(
        SaleItem.sale_date >= end - timedelta(days=180)).group_by(SaleItem.product_id, is_biz)
    typical_by = {(p, bool(b)): float(q) for p, b, q in db.execute(typical_q).all()}
    q = select(SaleItem, Sale.invoice_no, Sale.outlet_id, Product.name, Customer.customer_type).join(
        Sale, Sale.id == SaleItem.sale_id).join(Product, Product.id == SaleItem.product_id).outerjoin(
        Customer, Customer.id == Sale.customer_id).where(A.COMPLETED, SaleItem.sale_date >= start,
                                                         SaleItem.sale_date <= end, SaleItem.quantity >= 30)
    if outlet_ids:
        q = q.where(Sale.outlet_id.in_(outlet_ids))
    names = A.outlet_names(db)
    out = []
    for item, invoice, oid, pname, ctype in db.execute(q).all():
        biz = ctype == "business"
        typical = typical_by.get((item.product_id, biz)) or typical_by.get((item.product_id, False)) or 1.0
        if item.quantity >= 20 * typical:
            out.append({"day": item.sale_date.isoformat(), "sale_id": item.sale_id, "invoice_no": invoice,
                        "outlet_id": oid, "outlet": names.get(oid), "product": pname, "quantity": item.quantity,
                        "typical_quantity": round(typical, 1), "line_total": item.line_total,
                        "customer_type": ctype or "walk-in"})
    return sorted(out, key=lambda r: r["day"], reverse=True)


def explain(db: Session, a: dict) -> str:
    """Short evidence-based explanation for one anomalous outlet-day."""
    from app.models import Promotion, StockoutEvent

    day = date.fromisoformat(a["day"])
    parts = []
    if a["actual"] <= 0:
        return "No sales were recorded although the outlet is open - a closure or a billing outage."
    if a["typical_bills"]:
        bills_ch = (a["bills"] - a["typical_bills"]) / a["typical_bills"] * 100
        if abs(bills_ch) >= 25:
            parts.append(f"bills {a['bills']} vs typical {a['typical_bills']} ({bills_ch:+.0f}%)")
    big = db.execute(select(Sale.invoice_no, Sale.total).where(
        A.COMPLETED, Sale.outlet_id == a["outlet_id"], Sale.sale_date == day).order_by(Sale.total.desc()).limit(1)).first()
    if big and a["actual"] and big[1] / a["actual"] >= 0.3:
        parts.append(f"one bill ({big[0]}) was {big[1] / a['actual'] * 100:.0f}% of the day's revenue")
    outlet = db.get(Outlet, a["outlet_id"])
    w = db.scalar(select(WeatherDaily).where(WeatherDaily.city == outlet.city, WeatherDaily.day == day)) if outlet else None
    if w and w.rain_mm >= 25:
        parts.append(f"heavy rain ({w.rain_mm:.0f} mm)")
    promos = db.scalar(select(func.count(Promotion.id)).where(Promotion.start_date <= day, Promotion.end_date >= day))
    if promos:
        parts.append(f"{promos} promotion(s) running")
    outs = db.scalar(select(func.count(StockoutEvent.id)).where(
        StockoutEvent.outlet_id == a["outlet_id"], StockoutEvent.start_date <= day, StockoutEvent.end_date >= day))
    if outs:
        parts.append(f"{outs} product(s) out of stock")
    if a.get("festival"):
        parts.append(f"{a['festival']} period")
    return ("Evidence: " + "; ".join(parts) + ".") if parts else "No single driver stands out in the data."


def score_against_labels(db: Session, detected: list[dict], start: date, end: date,
                         outlet_ids: list[int] | None = None) -> dict | None:
    """Precision / recall of day-level detection versus the generator's injected anomalies."""
    q = select(AnomalyLabel).where(AnomalyLabel.day >= start, AnomalyLabel.day <= end)
    if outlet_ids:
        q = q.where(AnomalyLabel.outlet_id.in_(outlet_ids))
    labels = db.scalars(q).all()
    if not labels:
        return None
    truth = {(lab.outlet_id, lab.day.isoformat()): lab for lab in labels}
    flagged = {(a["outlet_id"], a["day"]) for a in detected if not a.get("explained_by")}
    tp = len(flagged & set(truth))
    fp, fn = len(flagged - set(truth)), len(set(truth) - flagged)
    by_kind: dict[str, dict] = {}
    for key, lab in truth.items():
        k = by_kind.setdefault(lab.kind, {"labelled": 0, "detected": 0})
        k["labelled"] += 1
        k["detected"] += int(key in flagged)
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = 2 * precision * recall / (precision + recall) if precision and recall else None
    return {"labelled": len(truth), "detected": len(flagged), "true_positives": tp, "false_positives": fp,
            "false_negatives": fn, "precision": round(precision, 3) if precision is not None else None,
            "recall": round(recall, 3) if recall is not None else None, "f1": round(f1, 3) if f1 else None,
            "by_kind": by_kind,
            "labels": [{"day": lab.day.isoformat(), "outlet_id": lab.outlet_id, "kind": lab.kind,
                        "description": lab.description, "magnitude": lab.magnitude,
                        "detected": (lab.outlet_id, lab.day.isoformat()) in flagged} for lab in labels]}
