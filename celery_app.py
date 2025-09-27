"""
Configurazione Celery centralizzata per evitare import circolari.
"""
import os
from celery import Celery
from celery.schedules import crontab # <-- Importa crontab

REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

celery_app = Celery(
    'archivista_ai',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['archivista_processing']
)

celery_app.conf.update(
    timezone='Europe/Rome',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    worker_prefetch_multiplier=1,
)

# --- TASK PIANIFICATE (Beat Schedule) ---
celery_app.conf.beat_schedule = {
    # La tua task di pulizia, eseguita ogni giorno alle 2:30 del mattino
    'cleanup-daily': {
        'task': 'archivista.cleanup_old_data',
        'schedule': crontab(hour=2, minute=30),
    },
    # La nuova task di scansione automatica, eseguita ogni 10 minuti
    'scan-for-docs-periodic': {
        'task': 'archivista.scan_new_documents_periodic',
        'schedule': crontab(minute='*/10'), # Esegui ogni 10 minuti
    },
}

