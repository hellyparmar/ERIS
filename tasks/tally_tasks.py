"""
Celery tasks for scheduled Tally synchronization.

Schedule example (add to celery beat schedule in celery_app.py or settings):

    CELERYBEAT_SCHEDULE = {
        'tally-full-sync': {
            'task': 'tasks.tally_tasks.scheduled_full_sync',
            'schedule': crontab(minute=0, hour='*/1'),  # every hour
        },
    }
"""

from __future__ import annotations

import logging
import os
from datetime import date, timedelta
from typing import Any, Callable, TypeVar

_F = TypeVar("_F", bound=Callable[..., Any])

logger = logging.getLogger(__name__)

# Guard: only import Celery when it is actually available
try:
    from celery import shared_task
    _CELERY_AVAILABLE = True
except ImportError:
    _CELERY_AVAILABLE = False

    def shared_task(_fn: Any = None, **kwargs: Any) -> Any:  # type: ignore[misc]
        """No-op fallback so the rest of the module is importable without Celery."""
        def decorator(f: _F) -> _F:
            return f
        if _fn is not None:
            return _fn
        return decorator


@shared_task(  # type: ignore[operator]
    bind=True,
    name="tasks.tally_tasks.ping_tally",
    max_retries=3,
    default_retry_delay=60,
)
def ping_tally(self) -> dict:
    """
    Health-check task: verify Tally is reachable.
    Runs before every sync to avoid silent failures.
    """
    from api.integrations.tally.sync_service import TallySyncService
    svc = TallySyncService()
    status = svc.check_status()
    result = status.dict()
    if not status.connected:
        logger.warning("Tally is not reachable: %s", status.error)
    else:
        logger.info("Tally ping OK — company: %s", status.company_name)
    return result


@shared_task(  # type: ignore[operator]
    bind=True,
    name="tasks.tally_tasks.sync_today_sales",
    max_retries=3,
    default_retry_delay=300,
)
def sync_today_sales(self, sales: list) -> dict:
    """
    Export a list of today's POS sales to Tally.

    Args:
        sales: List of sale dicts (same format as SaleExportRequest)
    """
    from api.integrations.tally.sync_service import TallySyncService
    try:
        svc = TallySyncService()
        # Confirm connectivity
        status = svc.check_status()
        if not status.connected:
            raise RuntimeError(f"Tally unreachable: {status.error}")

        result = svc.bulk_export_sales(sales)
        logger.info(
            "sync_today_sales: exported %d/%d sales. errors=%d",
            result.created + result.updated, result.total, len(result.errors)
        )
        return result.dict()

    except Exception as exc:
        logger.error("sync_today_sales failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(  # type: ignore[operator]
    bind=True,
    name="tasks.tally_tasks.import_tally_ledgers",
    max_retries=2,
    default_retry_delay=120,
)
def import_tally_ledgers(self) -> dict:
    """
    Import all ledgers from Tally into R-DIOS.
    Typically run once per day (or on demand).
    """
    from api.integrations.tally.sync_service import TallySyncService
    try:
        svc = TallySyncService()
        result = svc.import_ledgers()
        logger.info("import_tally_ledgers: %s", result.message)
        return result.dict()
    except Exception as exc:
        logger.error("import_tally_ledgers failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(  # type: ignore[operator]
    bind=True,
    name="tasks.tally_tasks.import_tally_stock_items",
    max_retries=2,
    default_retry_delay=120,
)
def import_tally_stock_items(self) -> dict:
    """
    Import all stock items from Tally into R-DIOS.
    Run daily to keep product catalogue in sync.
    """
    from api.integrations.tally.sync_service import TallySyncService
    try:
        svc = TallySyncService()
        result = svc.import_stock_items()
        logger.info("import_tally_stock_items: %s", result.message)
        return result.dict()
    except Exception as exc:
        logger.error("import_tally_stock_items failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(  # type: ignore[operator]
    bind=True,
    name="tasks.tally_tasks.scheduled_full_sync",
    max_retries=2,
    default_retry_delay=600,
)
def scheduled_full_sync(self) -> dict:
    """
    Full scheduled sync: import ledgers + stock items, then export yesterday's sales.
    Designed to run every hour via Celery Beat.
    """
    from api.integrations.tally.sync_service import TallySyncService
    results = {}

    try:
        svc = TallySyncService()
        status = svc.check_status()
        results["connection"] = status.dict()

        if not status.connected:
            results["skipped"] = True
            results["reason"] = status.error
            return results

        # Import
        results["ledgers"]      = svc.import_ledgers().dict()
        results["stock_items"]  = svc.import_stock_items().dict()

        # Export yesterday's vouchers to validate round-trip
        yesterday = date.today() - timedelta(days=1)
        results["vouchers_import"] = svc.import_vouchers(
            voucher_type="Sales",
            from_date=yesterday,
            to_date=yesterday,
        ).dict()

        logger.info("scheduled_full_sync completed successfully")
        return results

    except Exception as exc:
        logger.error("scheduled_full_sync failed: %s", exc)
        raise self.retry(exc=exc)
