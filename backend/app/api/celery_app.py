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
)

# Auto-discover tasks in tasks module
celery_app.autodiscover_tasks(['app.tasks'])

if __name__ == '__main__':
    celery_app.start()
