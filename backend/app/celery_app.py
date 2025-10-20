"""
Celery configuration for async task processing
"""
import os
from celery import Celery

# Get Celery broker URL from environment
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')

# Create Celery app
celery_app = Celery(
    'bizcard_crm',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=['app.tasks']
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max per task
    task_soft_time_limit=240,  # 4 minutes soft limit
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks to prevent memory leaks
    task_acks_late=True,  # Acknowledge task after completion
    task_reject_on_worker_lost=True,  # Reject task if worker is lost
    result_expires=3600,  # Results expire after 1 hour
)

# Task routing (optional, for multiple queues)
celery_app.conf.task_routes = {
    'app.tasks.process_batch_upload': {'queue': 'batch_processing'},
    'app.tasks.process_single_card': {'queue': 'card_processing'},
}

# Beat schedule (for periodic tasks, if needed)
celery_app.conf.beat_schedule = {
    # Example: clean up old results every hour
    'cleanup-results': {
        'task': 'app.tasks.cleanup_old_results',
        'schedule': 3600.0,  # Every hour
    },
}

if __name__ == '__main__':
    celery_app.start()

