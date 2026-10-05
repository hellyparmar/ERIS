"""Keep an untouched demo database current.

A demo generated weeks ago would show empty "today/this week" views. If the database only contains generated
demo sales (nothing entered by a user), all dates are shifted forward by whole weeks so weekday patterns stay
intact. Real data is never modified.
"""
from __future__ import annotations

import logging
from datetime import timedelta

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app import clock
from app.config import settings
from app.models import Sale

log = logging.getLogger(__name__)

# (table, [date columns], [datetime columns])
SHIFT_COLUMNS = [
    ("sales", ["sale_date"], ["sold_at", "created_at"]),
    ("sale_items", ["sale_date"], []),
    ("purchase_orders", ["order_date", "expected_date", "received_date"], ["created_at"]),
    ("stock_movements", [], ["created_at"]),
    ("customers", [], ["created_at"]),
    ("inventory", [], ["updated_at"]),
    ("outlets", ["opened_on"], []),
    ("promotions", ["start_date", "end_date"], ["created_at"]),
    ("price_history", ["effective_from"], []),
    ("stockout_events", ["start_date", "end_date"], []),
    ("anomaly_labels", ["day"], []),
    ("dataset_info", ["period_start", "period_end"], []),
    ("invoices", [], ["issued_at"]),
    ("weather_daily", ["day"], []),
    # saved forecasts move with the data, so they can still be served without refitting
    ("forecast_runs", ["data_start", "data_end"], ["created_at"]),
    ("forecast_results", ["day"], []),
]
FAR = 36500  # shift via a far-away date so unique (city, day) keys never collide mid-update


def is_untouched_demo(db: Session) -> bool:
    sources = dict(db.execute(select(Sale.source, func.count(Sale.id)).group_by(Sale.source)).all())
    return bool(sources) and set(sources) == {"synthetic"}


def shift_demo_dates(db: Session) -> int:
    """Shift demo data so its last day is yesterday (in whole weeks). Returns days shifted."""
    latest = db.scalar(select(func.max(Sale.sale_date)))
    if latest is None or not is_untouched_demo(db):
        return 0
    from app.models import DatasetInfo

    ds = db.scalar(select(DatasetInfo).order_by(DatasetInfo.id.desc()))
    if settings.SEED_END_DATE or (ds and (ds.parameters or {}).get("fixed_end_date")):
        return 0  # the dataset was generated to end on a chosen date: keep it there
    gap = (clock.today() - timedelta(days=1) - latest).days
    days = (gap // 7) * 7
    if days <= 0:
        return 0
    sqlite = db.get_bind().dialect.name == "sqlite"

    def shift(table: str, date_cols: list[str], dt_cols: list[str], n: int) -> None:
        sets = []
        for col in date_cols:
            sets.append(f"{col} = date({col}, '{n:+d} days')" if sqlite else f"{col} = {col} + ({n})")
        for col in dt_cols:
            sets.append(f"{col} = datetime({col}, '{n:+d} days')" if sqlite
                        else f"{col} = {col} + interval '{n} days'")
        db.execute(text(f"UPDATE {table} SET {', '.join(sets)}"))

    for table, date_cols, dt_cols in SHIFT_COLUMNS:
        if table == "weather_daily":
            shift(table, date_cols, dt_cols, days + FAR)
            shift(table, date_cols, dt_cols, -FAR)
        else:
            shift(table, date_cols, dt_cols, days)
    db.execute(text("UPDATE weather_daily SET is_forecast = (day > :y)"), {"y": clock.today() - timedelta(days=1)})
    db.commit()
    log.info("Demo data shifted forward by %s days to stay current", days)
    return days
