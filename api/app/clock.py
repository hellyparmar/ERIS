"""Business clock: 'today' and 'now' in the organization's time zone (not the server's, which is often UTC)."""
from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

_tz = ZoneInfo("Asia/Kolkata")


def set_timezone(name: str | None) -> None:
    global _tz
    try:
        _tz = ZoneInfo(name or "Asia/Kolkata")
    except (ZoneInfoNotFoundError, ValueError):
        _tz = ZoneInfo("Asia/Kolkata")


def now() -> datetime:
    """Naive local datetime in the business time zone (how sale times are stored)."""
    return datetime.now(_tz).replace(tzinfo=None, microsecond=0)


def today() -> date:
    return now().date()


def load_from_db(db) -> None:
    from sqlalchemy import select

    from app.models import Organization

    org = db.scalar(select(Organization))
    if org:
        set_timezone(org.timezone)
