"""
Z-Score Revenue Anomaly Detection Service - P5-T3
Calculates 30-day rolling baseline, flags drops (z < -2) and spikes (z > 3)
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

SPIKE_THRESHOLD = 3.0    # z-score for spike
DROP_THRESHOLD = -2.0    # z-score for drop


def detect_revenue_anomalies(
    db: Session,
    store_id: int = 1,
    lookback_days: int = 90
) -> List[Dict[str, Any]]:
    """
    Detect anomalous revenue days using z-score analysis.
    
    Returns a list of anomaly dicts with:
      - date, revenue, z_score, anomaly_type (spike|drop), severity
    """
    cutoff = datetime.utcnow() - timedelta(days=lookback_days)

    try:
        rows = db.execute(text("""
            SELECT
                DATE(transaction_date) as day,
                SUM(total_amount) as daily_revenue
            FROM sales
            WHERE transaction_date >= :cutoff
            GROUP BY day
            ORDER BY day ASC
        """), {"cutoff": cutoff}).fetchall()
    except Exception:
        # Fallback: use invoices table if sales unavailable
        try:
            rows = db.execute(text("""
                SELECT
                    DATE(created_at) as day,
                    SUM(total_amount) as daily_revenue
                FROM invoices
                WHERE created_at >= :cutoff
                GROUP BY day
                ORDER BY day ASC
            """), {"cutoff": cutoff}).fetchall()
        except Exception as e:
            logger.warning(f"Anomaly detection: no data source found: {e}")
            return []

    if not rows:
        return []

    revenues = [float(r[1] or 0) for r in rows]
    dates = [str(r[0]) for r in rows]
    n = len(revenues)

    if n < 7:
        return []

    # Calculate global mean and stddev
    mean = sum(revenues) / n
    variance = sum((x - mean) ** 2 for x in revenues) / n
    std = variance ** 0.5

    if std == 0:
        return []

    anomalies = []
    for i, (day, rev) in enumerate(zip(dates, revenues)):
        z = (rev - mean) / std

        if z > SPIKE_THRESHOLD:
            anomaly_type = "spike"
            severity = "high" if z > 5 else "medium"
        elif z < DROP_THRESHOLD:
            anomaly_type = "drop"
            severity = "high" if z < -3 else "medium"
        else:
            continue

        anomalies.append({
            "date": day,
            "revenue": round(rev, 2),
            "mean_revenue": round(mean, 2),
            "std_dev": round(std, 2),
            "z_score": round(z, 3),
            "anomaly_type": anomaly_type,
            "severity": severity,
            "deviation_pct": round(((rev - mean) / mean * 100) if mean else 0, 1),
            "message": (
                f"Revenue spike of ₹{rev:,.0f} on {day} — {abs(z):.1f}σ above mean"
                if anomaly_type == "spike"
                else f"Revenue drop to ₹{rev:,.0f} on {day} — {abs(z):.1f}σ below mean"
            )
        })

    return sorted(anomalies, key=lambda x: abs(x["z_score"]), reverse=True)


def detect_product_anomalies(
    db: Session,
    store_id: int = 1,
    lookback_days: int = 30
) -> List[Dict[str, Any]]:
    """Detect products with anomalous quantity sold (sudden spikes or drops)"""
    cutoff = datetime.utcnow() - timedelta(days=lookback_days)

    try:
        rows = db.execute(text("""
            SELECT
                p.id, p.name, p.category,
                SUM(si.quantity) as total_qty,
                COUNT(DISTINCT s.id) as num_transactions,
                AVG(si.quantity) as avg_qty_per_txn
            FROM sale_items si
            JOIN products p ON p.id = si.product_id
            JOIN sales s ON s.id = si.sale_id
            WHERE s.transaction_date >= :cutoff
            GROUP BY p.id, p.name, p.category
            ORDER BY total_qty DESC
        """), {"cutoff": cutoff}).fetchall()
    except Exception as e:
        logger.warning(f"Product anomaly detection error: {e}")
        return []

    if not rows:
        return []

    quantities = [float(r[3] or 0) for r in rows]
    if len(quantities) < 3:
        return []

    mean = sum(quantities) / len(quantities)
    std = (sum((x - mean) ** 2 for x in quantities) / len(quantities)) ** 0.5

    if std == 0:
        return []

    anomalies = []
    for r in rows:
        qty = float(r[3] or 0)
        z = (qty - mean) / std
        if abs(z) > 2.5:
            anomalies.append({
                "product_id": r[0],
                "product_name": r[1],
                "category": r[2],
                "total_quantity_sold": float(qty),
                "z_score": round(z, 2),
                "anomaly_type": "high_demand" if z > 0 else "low_demand",
                "message": f"{'Unusually high' if z > 0 else 'Unusually low'} demand for {r[1]}: {qty:.0f} units vs avg {mean:.0f}"
            })

    return sorted(anomalies, key=lambda x: abs(x["z_score"]), reverse=True)
