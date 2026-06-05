"""
Celery Configuration for R-DIOS
Async task queue for PDF generation, bulk operations, scheduled jobs
"""

import os
from celery import Celery
from celery.schedules import crontab

# Create Celery app
celery_app = Celery(
    'rdios',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
)

# Configuration
celery_app.conf.update(
    # Serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Timezone
    timezone='Asia/Kolkata',
    enable_utc=True,
    
    # Task settings
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max
    task_soft_time_limit=240,  # 4 minutes soft limit
    
    # Results
    result_expires=3600,  # 1 hour
    result_backend_transport_options={'master_name': 'mymaster'},
    
    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,  # Restart after 1000 tasks (prevent memory leaks)
    
    # Scheduled tasks (Celery Beat)
    beat_schedule={
        # Daily tasks
        'sync-external-factors-daily': {
            'task': 'api.tasks.external_factors.sync_daily_factors',
            'schedule': crontab(hour=1, minute=0),  # 1 AM daily
        },
        'mark-overdue-invoices': {
            'task': 'api.tasks.invoices.mark_overdue_invoices',
            'schedule': crontab(hour=0, minute=30),  # 12:30 AM daily
        },
        'send-payment-reminders': {
            'task': 'api.tasks.invoices.send_payment_reminders',
            'schedule': crontab(hour=10, minute=0),  # 10 AM daily
        },
        
        # Weekly tasks
        'generate-weekly-reports': {
            'task': 'api.tasks.reports.generate_weekly_summary',
            'schedule': crontab(hour=8, minute=0, day_of_week=1),  # Monday 8 AM
        },
        'cleanup-old-cache': {
            'task': 'api.tasks.maintenance.cleanup_cache',
            'schedule': crontab(hour=3, minute=0, day_of_week=0),  # Sunday 3 AM
        },
        
        # Hourly tasks
        'sync-weather-data': {
            'task': 'api.tasks.external_factors.sync_weather',
            'schedule': crontab(minute=0),  # Every hour
        },
        
        # Alert monitoring (every 15 minutes)
        'run-alert-engine': {
            'task': 'alerts.run_alert_engine',
            'schedule': crontab(minute='*/15'),  # Every 15 minutes
        },
    }
)

# Auto-discover tasks in tasks module
celery_app.autodiscover_tasks(['api.tasks'])

if __name__ == '__main__':
    celery_app.start()
