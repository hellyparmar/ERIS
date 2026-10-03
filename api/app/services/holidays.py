"""Retail calendar: Indian festivals and events that move F&B demand.

Used both by the demo-data generator (to create realistic spikes) and by the
forecasting models (as known future regressors), so forecasts anticipate festivals.
"""
from datetime import date, timedelta

# (name, date, days_before_effect, days_after_effect)
EVENTS: list[tuple[str, date, int, int]] = [
    ("Holi", date(2024, 3, 25), 3, 0),
    ("Raksha Bandhan", date(2024, 8, 19), 4, 0),
    ("Ganesh Chaturthi", date(2024, 9, 7), 3, 2),
    ("Navratri", date(2024, 10, 3), 0, 8),
    ("Diwali", date(2024, 11, 1), 12, 2),
    ("Christmas", date(2024, 12, 25), 4, 0),
    ("New Year", date(2024, 12, 31), 2, 1),
    ("Holi", date(2025, 3, 14), 3, 0),
    ("Eid", date(2025, 3, 31), 2, 1),
    ("Raksha Bandhan", date(2025, 8, 9), 4, 0),
    ("Ganesh Chaturthi", date(2025, 8, 27), 3, 2),
    ("Navratri", date(2025, 9, 22), 0, 8),
    ("Diwali", date(2025, 10, 20), 12, 2),
    ("Christmas", date(2025, 12, 25), 4, 0),
    ("New Year", date(2025, 12, 31), 2, 1),
    ("Holi", date(2026, 3, 4), 3, 0),
    ("Eid", date(2026, 3, 20), 2, 1),
    ("Raksha Bandhan", date(2026, 8, 28), 4, 0),
    ("Ganesh Chaturthi", date(2026, 9, 14), 3, 2),
    ("Navratri", date(2026, 10, 11), 0, 8),
    ("Diwali", date(2026, 11, 8), 12, 2),
    ("Christmas", date(2026, 12, 25), 4, 0),
    ("New Year", date(2026, 12, 31), 2, 1),
    ("Holi", date(2027, 3, 22), 3, 0),
    ("Raksha Bandhan", date(2027, 8, 17), 4, 0),
    ("Diwali", date(2027, 10, 29), 12, 2),
    ("Christmas", date(2027, 12, 25), 4, 0),
    ("New Year", date(2027, 12, 31), 2, 1),
]


def event_window(d: date) -> tuple[str, int] | None:
    """Return (event name, days until event; negative = after) if d falls in an event window."""
    for name, day, before, after in EVENTS:
        delta = (day - d).days
        if -after <= delta <= before:
            return name, delta
    return None


def holidays_frame():
    """Holidays in Prophet's format (holiday, ds, lower_window, upper_window)."""
    import pandas as pd

    return pd.DataFrame(
        [
            {"holiday": name, "ds": pd.Timestamp(day), "lower_window": -before, "upper_window": after}
            for name, day, before, after in EVENTS
        ]
    )


def upcoming_events(start: date, days: int) -> list[dict]:
    end = start + timedelta(days=days)
    return [
        {"name": name, "date": day.isoformat(), "days_away": (day - start).days}
        for name, day, _, _ in EVENTS
        if start <= day <= end
    ]
