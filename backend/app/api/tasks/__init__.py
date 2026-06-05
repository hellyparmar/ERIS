# Celery Tasks - Init
from app.api.tasks import forecasting_tasks

__all__ = ['forecasting_tasks']

try:
    from app.api.tasks import external_factors, invoices, reports, maintenance
    __all__.extend(['external_factors', 'invoices', 'reports', 'maintenance'])
except ImportError:
    pass
