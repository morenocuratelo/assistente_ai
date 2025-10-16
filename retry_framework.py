"""
Sistema di Retry Intelligente con Backoff Esponenziale
Implementa logica di retry avanzata per il processamento documenti.
"""
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import logging

from error_diagnosis_framework import (
    error_framework,
    ProcessingState,
    ProcessingPhase,
    ErrorCategory,
    ErrorSeverity
)

# --- CONFIGURAZIONE RETRY ---

class RetryConfig:
    """Configurazione per il sistema di retry"""

    def __init__(self):
        # Retry per categoria errore
        self.max_retries_by_category = {
            ErrorCategory.IO_ERROR: 5,
            ErrorCategory.CONNECTION_ERROR: 3,
            ErrorCategory.API_ERROR: 2,
            ErrorCategory.FORMAT_ERROR: 1,
            ErrorCategory.INDEXING_ERROR: 3,
            ErrorCategory.ARCHIVING_ERROR: 2,
            ErrorCategory.PERMISSION_ERROR: 1,
            ErrorCategory.TIMEOUT_ERROR: 3,
            ErrorCategory.VALIDATION_ERROR: 1,
            ErrorCategory.UNKNOWN_ERROR: 2
        }

        # Backoff esponenziale ( secondi )
        self.base_delay = 30  # Base delay 30 secondi
        self.max_delay = 3600  # Max delay 1 ora
        self.exponential_base = 2  # Base esponenziale
        self.jitter = True  # Aggiungi jitter per evitare thundering herd

        # Timeout per fase
        self.phase_timeouts = {
            ProcessingPhase.PHASE_1: 60,    # 1 minuto
            ProcessingPhase.PHASE_2: 300,   # 5 minuti
            ProcessingPhase.PHASE_3: 600,   # 10 minuti
            ProcessingPhase.PHASE_4: 300,   # 5 minuti
            ProcessingPhase.PHASE_5: 120    # 2 minuti
        }

class RetryStrategy:
    """Strategia di retry per un singolo file"""

    def __init__(self, file_name: str, error_category: ErrorCategory):
        self.file_name = file_name
        self.error_category = error_category
        self.attempts = 0
        self.last_attempt = None
        self.next_retry = None
        self.config = RetryConfig()

    def should_retry(self) -> bool:
        """Determina se il file dovrebbe essere ritentato"""
        max_retries = self.config.max_retries_by_category.get(self.error_category, 2)
        return self.attempts < max_retries

    def calculate_next_retry(self) -> datetime:
        """Calcola quando dovrebbe avvenire il prossimo retry"""
        if not self.should_retry():
            return None

        # Backoff esponenziale con jitter
        base_delay = self.config.base_delay
        exponential_delay = base_delay * (self.config.exponential_base ** self.attempts)

        # Applica max delay
        delay = min(exponential_delay, self.config.max_delay)

        # Aggiungi jitter (±25%)
        if self.config.jitter:
            jitter_range = delay * 0.25
            jitter = random.uniform(-jitter_range, jitter_range)
            delay += jitter

        next_retry = datetime.now() + timedelta(seconds=int(delay))
        self.next_retry = next_retry
        return next_retry

    def record_attempt(self):
        """Registra un tentativo di retry"""
        self.attempts += 1
        self.last_attempt = datetime.now()

class RetryManager:
    """Gestore centrale per il sistema di retry"""

    def __init__(self):
        self.config = RetryConfig()
        self.retry_strategies: Dict[str, RetryStrategy] = {}
        self.logger = logging.getLogger("RetryManager")

    def register_file_for_retry(self, file_name: str, error_category: ErrorCategory) -> bool:
        """
        Registra un file per il sistema di retry.

        Args:
            file_name: Nome del file
            error_category: Categoria dell'errore che ha causato il fallimento

        Returns:
            bool: True se registrato con successo
        """
        if file_name in self.retry_strategies:
            # Aggiorna strategia esistente
            strategy = self.retry_strategies[file_name]
            strategy.error_category = error_category
            strategy.record_attempt()
        else:
            # Crea nuova strategia
            strategy = RetryStrategy(file_name, error_category)
            strategy.record_attempt()
            self.retry_strategies[file_name] = strategy

        # Calcola prossimo retry
        next_retry = strategy.calculate_next_retry()

        self.logger.info(f"Registered {file_name} for retry (attempt {strategy.attempts}, next: {next_retry})")

        return True

    def get_files_ready_for_retry(self) -> List[str]:
        """
        Recupera lista di file pronti per il retry.

        Returns:
            List[str]: Lista di nomi file pronti per il retry
        """
        ready_files = []
        current_time = datetime.now()

        for file_name, strategy in self.retry_strategies.items():
            if (strategy.should_retry() and
                strategy.next_retry and
                current_time >= strategy.next_retry):

                # Verifica che il file non sia attualmente in processamento
                current_status = error_framework.get_processing_status(file_name)
                if (current_status and
                    current_status.processing_state not in [ProcessingState.PROCESSING, ProcessingState.QUEUED]):
                    ready_files.append(file_name)

        return ready_files

    def get_retry_statistics(self) -> Dict[str, int]:
        """Recupera statistiche sui retry"""
        stats = {
            'total_files_in_retry': len(self.retry_strategies),
            'files_ready_for_retry': len(self.get_files_ready_for_retry()),
            'files_exhausted_retries': 0
        }

        for strategy in self.retry_strategies.values():
            if not strategy.should_retry():
                stats['files_exhausted_retries'] += 1

        return stats

    def cleanup_old_strategies(self, max_age_hours: int = 24):
        """Pulisce strategie di retry vecchie"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        files_to_remove = []

        for file_name, strategy in self.retry_strategies.items():
            if (strategy.last_attempt and strategy.last_attempt < cutoff_time):
                files_to_remove.append(file_name)

        for file_name in files_to_remove:
            del self.retry_strategies[file_name]
            self.logger.info(f"Cleaned up old retry strategy for {file_name}")

        return len(files_to_remove)

# --- ISTANZA GLOBALE ---
retry_manager = RetryManager()

# --- FUNZIONI DI UTILITÀ PUBBLICHE ---

def schedule_file_for_retry(file_name: str, error_category: ErrorCategory) -> bool:
    """
    Schedula un file per il retry automatico.

    Args:
        file_name: Nome del file da ritentare
        error_category: Categoria dell'errore

    Returns:
        bool: True se schedulato con successo
    """
    return retry_manager.register_file_for_retry(file_name, error_category)

def get_files_ready_for_retry() -> List[str]:
    """Recupera file pronti per il retry"""
    return retry_manager.get_files_ready_for_retry()

def get_retry_info(file_name: str) -> Optional[Dict]:
    """Recupera informazioni retry per un file"""
    strategy = retry_manager.retry_strategies.get(file_name)
    if strategy:
        return {
            'attempts': strategy.attempts,
            'max_retries': strategy.config.max_retries_by_category.get(strategy.error_category, 2),
            'next_retry': strategy.next_retry.isoformat() if strategy.next_retry else None,
            'last_attempt': strategy.last_attempt.isoformat() if strategy.last_attempt else None,
            'should_retry': strategy.should_retry()
        }
    return None

def process_retry_queue():
    """
    Processa la coda di retry e restituisce file pronti per essere ritentati.
    Da chiamare periodicamente dal sistema principale.
    """
    ready_files = get_files_ready_for_retry()

    for file_name in ready_files:
        try:
            # Resetta stato processamento per permettere nuovo tentativo
            success = error_framework.reset_processing_status(file_name)
            if success:
                retry_manager.logger.info(f"Reset processing status for retry: {file_name}")

                # Qui dovresti chiamare il task di processamento
                # from archivista_processing import process_document_task
                # process_document_task.delay(file_path)

            else:
                retry_manager.logger.error(f"Failed to reset processing status for {file_name}")

        except Exception as e:
            retry_manager.logger.error(f"Error processing retry for {file_name}: {e}")

    return ready_files

# --- DECORATORE PER FUNZIONI CON RETRY ---

def with_retry(max_attempts: int = 3, base_delay: float = 1.0,
               exponential_base: float = 2.0, jitter: bool = True):
    """
    Decoratore per aggiungere logica di retry a funzioni.

    Args:
        max_attempts: Numero massimo di tentativi
        base_delay: Delay base in secondi
        exponential_base: Base per backoff esponenziale
        jitter: Se aggiungere jitter random

    Returns:
        Decoratore funzione
    """
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)

                except Exception as e:
                    last_exception = e

                    if attempt < max_attempts - 1:
                        # Calcola delay con backoff esponenziale
                        delay = base_delay * (exponential_base ** attempt)

                        if jitter:
                            # Aggiungi jitter (±25%)
                            jitter_range = delay * 0.25
                            delay += random.uniform(-jitter_range, jitter_range)

                        print(f"⏳ Retry {attempt + 1}/{max_attempts} after {delay:.1f}s: {e}")
                        time.sleep(delay)

            # Se arriviamo qui, tutti i retry sono falliti
            raise last_exception

        return wrapper
    return decorator

# --- TASK CELERY PER RETRY AUTOMATICO ---

@celery_app.task(name='archivista.retry_failed_files')
def retry_failed_files_task():
    """
    Task Celery per processare automaticamente i file pronti per il retry.
    Da schedulare periodicamente (es. ogni 5 minuti).
    """
    try:
        ready_files = process_retry_queue()

        if ready_files:
            print(f"🔄 Ritentato {len(ready_files)} file: {', '.join(ready_files[:5])}{'...' if len(ready_files) > 5 else ''}")

            # Qui dovresti effettivamente chiamare il task di processamento
            # for file_name in ready_files:
            #     file_path = trova_file_path(file_name)
            #     process_document_task.delay(file_path)

        return {
            'status': 'success',
            'files_retried': len(ready_files),
            'files_ready': len(get_files_ready_for_retry())
        }

    except Exception as e:
        print(f"❌ Errore nel task retry automatico: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }

# --- MONITORAGGIO RETRY ---

def get_retry_dashboard_data() -> Dict:
    """Recupera dati per dashboard retry"""
    try:
        stats = retry_manager.get_retry_statistics()

        # File pronti per retry con dettagli
        ready_files = get_files_ready_for_retry()
        ready_files_details = []

        for file_name in ready_files:
            retry_info = get_retry_info(file_name)
            if retry_info:
                ready_files_details.append({
                    'file_name': file_name,
                    **retry_info
                })

        # Strategie attive
        active_strategies = []
        for file_name, strategy in retry_manager.retry_strategies.items():
            active_strategies.append({
                'file_name': file_name,
                'attempts': strategy.attempts,
                'error_category': strategy.error_category.value,
                'next_retry': strategy.next_retry.isoformat() if strategy.next_retry else None,
                'last_attempt': strategy.last_attempt.isoformat() if strategy.last_attempt else None
            })

        return {
            'statistics': stats,
            'ready_files': ready_files_details,
            'active_strategies': active_strategies[:20],  # Limita a 20 per performance
            'total_active_strategies': len(active_strategies)
        }

    except Exception as e:
        print(f"❌ Errore nel recupero dati retry dashboard: {e}")
        return {
            'statistics': {'total_files_in_retry': 0, 'files_ready_for_retry': 0, 'files_exhausted_retries': 0},
            'ready_files': [],
            'active_strategies': []
        }

# --- INTEGRAZIONE CON FRAMEWORK ERRORI ---

def handle_error_with_retry(file_name: str, exception: Exception, processing_phase: ProcessingPhase):
    """
    Gestisce un errore applicando automaticamente la strategia di retry appropriata.

    Args:
        file_name: Nome del file che ha avuto l'errore
        exception: Eccezione che si è verificata
        processing_phase: Fase in cui si è verificato l'errore

    Returns:
        Dict con informazioni sul retry
    """
    try:
        # Classifica errore
        error_record = error_framework.classify_error(exception, file_name, processing_phase)

        # Determina se applicare retry
        should_retry = error_framework.should_retry(file_name)

        if should_retry:
            # Registra per retry
            schedule_file_for_retry(file_name, error_record.error_category)

            return {
                'action': 'retry_scheduled',
                'retry_count': error_framework.get_processing_status(file_name).retry_count,
                'next_retry': get_retry_info(file_name).get('next_retry'),
                'error_category': error_record.error_category.value
            }
        else:
            return {
                'action': 'no_retry',
                'reason': 'max_retries_exceeded',
                'error_category': error_record.error_category.value
            }

    except Exception as e:
        print(f"❌ Errore nella gestione retry per {file_name}: {e}")
        return {
            'action': 'error_in_retry_logic',
            'error': str(e)
        }

# --- UTILITIES PER TESTING ---

def simulate_error_scenarios():
    """Funzione per simulare diversi scenari di errore per testing"""
    scenarios = [
        (IOError("File not found"), ProcessingPhase.PHASE_2, "test_file_1.pdf"),
        (ConnectionError("Connection timeout"), ProcessingPhase.PHASE_3, "test_file_2.pdf"),
        (ValueError("Invalid JSON format"), ProcessingPhase.PHASE_3, "test_file_3.pdf"),
        (TimeoutError("Operation timed out"), ProcessingPhase.PHASE_4, "test_file_4.pdf"),
    ]

    results = []
    for exception, phase, file_name in scenarios:
        result = handle_error_with_retry(file_name, exception, phase)
        results.append({
            'file_name': file_name,
            'exception': type(exception).__name__,
            'phase': phase.value,
            'result': result
        })

    return results

if __name__ == "__main__":
    # Test del sistema di retry
    print("🧪 Testing Retry Framework...")

    test_results = simulate_error_scenarios()
    for result in test_results:
        print(f"📄 {result['file_name']}: {result['exception']} -> {result['result']['action']}")

    print(f"\n📊 Retry Statistics: {retry_manager.get_retry_statistics()}")
