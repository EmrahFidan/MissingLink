"""
Celery Configuration
Faz 4.1: Asenkron İşleme Yapılandırması
"""

from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

# Redis URL
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Celery instance
celery_app = Celery(
    "missinglink",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['app.tasks.ctgan_tasks', 'app.tasks.processing_tasks']
)

# Celery Configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Istanbul',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3000,  # 50 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    result_expires=3600,  # Results expire after 1 hour
    broker_connection_retry_on_startup=True,
)

# Task routes
celery_app.conf.task_routes = {
    'app.tasks.ctgan_tasks.*': {'queue': 'ctgan'},
    'app.tasks.processing_tasks.*': {'queue': 'processing'},
}
