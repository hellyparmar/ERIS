"""Keep an untouched demo database current.

A demo generated weeks ago would show empty "today/this week" views. If the database only contains generated
demo sales (nothing entered by a user), all dates are shifted forward by whole weeks so weekday patterns stay
intact. Real data is never modified.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

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
]


def is_untouched_demo(db: Session) -> bool:
    sources = dict(db.execute(select(Sale.source, func.count(Sale.id)).group_by(Sale.source)).all())
    return bool(sources) and set(sources) == {"demo"}


def shift_demo_dates(db: Session) -> int:
    """Shift demo data so its last day is yesterday (in whole weeks). Returns days shifted."""
    latest = db.scalar(select(func.max(Sale.sale_date)))
    if latest is None or not is_untouched_demo(db):
        return 0
    gap = (date.today() - timedelta(days=1) - latest).days
    days = (gap // 7) * 7
    if days <= 0:
        return 0
    for table, date_cols, dt_cols in SHIFT_COLUMNS:
        sets = []
        for col in date_cols:
            sets.append(f"{col} = date({col}, '+{days} days')" if settings.is_sqlite else f"{col} = {col} + {days}")
        for col in dt_cols:
            sets.append(f"{col} = datetime({col}, '+{days} days')" if settings.is_sqlite
                        else f"{col} = {col} + interval '{days} days'")
        db.execute(text(f"UPDATE {table} SET {', '.join(sets)}"))
    db.commit()
    log.info("Demo data shifted forward by %s days to stay current", days)
    return days
