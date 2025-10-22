"""
Questo file assicura che le task definite in altri moduli
siano registrate correttamente nell'applicazione Celery.
"""
# Importa l'app Celery centralizzata
from celery_app import celery_app

# Importa le task in modo che Celery possa trovarle.
# Anche se non usiamo 'process_document_task' direttamente qui,
# l'import è necessario per la registrazione.
from archivista_processing import process_document_task

# Qui potresti aggiungere future configurazioni di task pianificate (Beat)
# celery_app.conf.beat_schedule = { ... }
