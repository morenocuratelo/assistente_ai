"""
Framework di Diagnosi e Gestione Errori per il Flusso di Processamento
Implementazione completa del sistema di tracciamento e gestione errori.
"""
import os
import json
import time
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import traceback

from file_utils import db_connect, get_papers_dataframe
import streamlit as st

# --- CONFIGURAZIONE ---
DB_STORAGE_DIR = "db_memoria"
QUARANTINE_DIR = os.path.join(DB_STORAGE_DIR, "quarantine")
ERROR_LOG_DIR = os.path.join(DB_STORAGE_DIR, "error_logs")
PROCESSING_METRICS_DIR = os.path.join(DB_STORAGE_DIR, "metrics")

# Crea directory necessarie
for dir_path in [QUARANTINE_DIR, ERROR_LOG_DIR, PROCESSING_METRICS_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# --- ENUMERAZIONI PER GLI STATI ---

class ProcessingState(Enum):
    """Stati di processamento del documento secondo la versione 2.0"""
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    FAILED_PARSING = "FAILED_PARSING"
    FAILED_EXTRACTION_API = "FAILED_EXTRACTION_API"
    FAILED_EXTRACTION_FORMAT = "FAILED_EXTRACTION_FORMAT"
    FAILED_INDEXING = "FAILED_INDEXING"
    FAILED_ARCHIVING = "FAILED_ARCHIVING"
    COMPLETED = "COMPLETED"
    MANUAL_INTERVENTION_REQUIRED = "MANUAL_INTERVENTION_REQUIRED"

class ErrorCategory(Enum):
    """Categorie di errore per classificazione"""
    IO_ERROR = "IOError"
    CONNECTION_ERROR = "ConnectionError"
    API_ERROR = "APIError"
    FORMAT_ERROR = "FormatError"
    INDEXING_ERROR = "IndexingError"
    ARCHIVING_ERROR = "ArchivingError"
    PERMISSION_ERROR = "PermissionError"
    VALIDATION_ERROR = "ValidationError"
    TIMEOUT_ERROR = "TimeoutError"
    UNKNOWN_ERROR = "UnknownError"

class ErrorSeverity(Enum):
    """Severità degli errori"""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class ProcessingPhase(Enum):
    """Fasi del processamento"""
    PHASE_1 = "phase_1"  # Innesco e accodamento
    PHASE_2 = "phase_2"  # Parsing e lettura
    PHASE_3 = "phase_3"  # Estrazione conoscenza
    PHASE_4 = "phase_4"  # Indicizzazione
    PHASE_5 = "phase_5"  # Archiviazione

# --- DATACLASS PER I METADATI ---

@dataclass
class ProcessingMetadata:
    """Metadati del processamento per tracciamento completo"""
    file_name: str
    file_size: int
    file_extension: str
    processing_state: str  # Cambiato da ProcessingState a str per compatibilità JSON
    current_phase: str     # Cambiato da ProcessingPhase a str per compatibilità JSON
    celery_task_id: Optional[str] = None
    worker_node: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    phase_started_at: Optional[datetime] = None
    phase_completed_at: Optional[datetime] = None
    total_processing_time: Optional[float] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    quarantine_path: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

@dataclass
class ErrorRecord:
    """Record strutturato per gli errori"""
    file_name: str
    processing_state: ProcessingState
    error_category: ErrorCategory
    error_severity: ErrorSeverity
    error_message: str
    error_details: Dict[str, Any]
    celery_task_id: Optional[str] = None
    worker_node: Optional[str] = None
    stack_trace: Optional[str] = None
    resolution_status: str = "open"
    resolution_notes: Optional[str] = None
    created_at: datetime = None
    resolved_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class ProcessingMetrics:
    """Metriche di processamento aggregate"""
    date_period: str  # 'YYYY-MM-DD' o 'YYYY-MM-DD HH'
    total_files: int = 0
    files_pending: int = 0
    files_processing: int = 0
    files_completed: int = 0
    files_failed: int = 0
    avg_processing_time: Optional[float] = None
    error_rate: float = 0.0
    quarantine_count: int = 0
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

# --- GESTORE PRINCIPALE DEL FRAMEWORK ---

class ErrorDiagnosisFramework:
    """
    Framework principale per la diagnosi e gestione degli errori di processamento.
    Implementa il sistema completo di tracciamento, logging e recovery.
    """

    def __init__(self):
        self.logger = self._setup_logger()
        self._ensure_directories()

    def _setup_logger(self) -> logging.Logger:
        """Configura il logger strutturato"""
        logger = logging.getLogger("ErrorDiagnosisFramework")
        logger.setLevel(logging.DEBUG)

        # Crea formatter strutturato
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s'
        )

        # File handler per errori
        error_handler = logging.FileHandler(os.path.join(ERROR_LOG_DIR, "processing_errors.log"))
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)

        # File handler per tutti i log
        general_handler = logging.FileHandler(os.path.join(ERROR_LOG_DIR, "processing.log"))
        general_handler.setLevel(logging.INFO)
        general_handler.setFormatter(formatter)

        logger.addHandler(error_handler)
        logger.addHandler(general_handler)

        return logger

    def _ensure_directories(self):
        """Assicura che tutte le directory necessarie esistano"""
        for dir_path in [QUARANTINE_DIR, ERROR_LOG_DIR, PROCESSING_METRICS_DIR]:
            os.makedirs(dir_path, exist_ok=True)

    def generate_correlation_id(self) -> str:
        """Genera un ID di correlazione univoco per tracciare le operazioni"""
        return f"{int(time.time() * 1000)}_{os.getpid()}"

    # --- GESTIONE STATO PROCESSAMENTO ---

    def initialize_processing_status(self, file_name: str, file_path: str) -> str:
        """
        Inizializza lo stato di processamento per un nuovo file.

        Args:
            file_name: Nome del file
            file_path: Percorso completo del file

        Returns:
            str: Correlation ID per tracciare l'operazione
        """
        correlation_id = self.generate_correlation_id()

        try:
            # Ottieni metadati del file
            file_stat = os.stat(file_path)
            file_size = file_stat.st_size
            file_extension = os.path.splitext(file_name)[1].lower()

            # Crea metadati di processamento
            metadata = ProcessingMetadata(
                file_name=file_name,
                file_size=file_size,
                file_extension=file_extension,
                processing_state=ProcessingState.PENDING.value,
                current_phase=ProcessingPhase.PHASE_1.value
            )

            # Salva nel database
            with db_connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO document_processing_status
                    (file_name, processing_state, current_phase, processing_metadata, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    file_name,
                    metadata.processing_state,
                    metadata.current_phase,
                    json.dumps(asdict(metadata), default=str),  # Convert datetime objects to strings
                    metadata.created_at.isoformat(),
                    metadata.updated_at.isoformat()
                ))
                conn.commit()

            self.logger.info(f"Initialized processing status for {file_name}", extra={"correlation_id": correlation_id})
            return correlation_id

        except Exception as e:
            self.logger.error(f"Failed to initialize processing status for {file_name}: {e}",
                            extra={"correlation_id": correlation_id})
            # Always return correlation_id even on failure for proper error tracking
            return correlation_id

    def update_processing_state(self, file_name: str, new_state: ProcessingState,
                              phase: ProcessingPhase = None, error_message: str = None,
                              error_details: Dict[str, Any] = None, correlation_id: str = None) -> bool:
        """
        Aggiorna lo stato di processamento di un file.

        Args:
            file_name: Nome del file
            new_state: Nuovo stato di processamento
            phase: Fase corrente (opzionale)
            error_message: Messaggio di errore (opzionale)
            error_details: Dettagli tecnici dell'errore (opzionale)
            correlation_id: ID di correlazione per tracciamento

        Returns:
            bool: True se l'aggiornamento è riuscito
        """
        if correlation_id is None:
            correlation_id = self.generate_correlation_id()

        try:
            with db_connect() as conn:
                cursor = conn.cursor()

                # Recupera stato attuale
                cursor.execute("SELECT * FROM document_processing_status WHERE file_name = ?", (file_name,))
                current = cursor.fetchone()

                if not current:
                    self.logger.warning(f"No processing status found for {file_name}, creating new",
                                      extra={"correlation_id": correlation_id})
                    return self.initialize_processing_status(file_name, file_name) is not None

                # Aggiorna stato
                update_time = datetime.now()
                update_fields = ["processing_state = ?", "updated_at = ?"]
                values = [new_state.value, update_time.isoformat()]

                if phase:
                    update_fields.append("current_phase = ?")
                    values.append(phase.value)

                if error_message:
                    update_fields.append("error_message = ?")
                    values.append(error_message)

                if error_details:
                    update_fields.append("error_details = ?")
                    values.append(json.dumps(error_details))

                # Gestisci transizioni di fase
                if phase and current['current_phase'] != phase.value:
                    update_fields.extend(["phase_started_at = ?", "phase_completed_at = ?"])
                    values.extend([update_time.isoformat(), None])

                values.append(file_name)

                query = f"UPDATE document_processing_status SET {', '.join(update_fields)} WHERE file_name = ?"
                cursor.execute(query, tuple(values))
                conn.commit()

            # Log della transizione
            self.logger.info(f"State transition: {file_name} -> {new_state.value}",
                           extra={"correlation_id": correlation_id})

            return True

        except Exception as e:
            self.logger.error(f"Failed to update processing state for {file_name}: {e}",
                            extra={"correlation_id": correlation_id})
            return False

    def get_processing_status(self, file_name: str) -> Optional[ProcessingMetadata]:
        """
        Recupera lo stato di processamento di un file.

        Args:
            file_name: Nome del file

        Returns:
            ProcessingMetadata o None se non trovato
        """
        try:
            with db_connect() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM document_processing_status WHERE file_name = ?", (file_name,))
                row = cursor.fetchone()

                if row:
                    metadata_dict = json.loads(row['processing_metadata']) if row['processing_metadata'] else {}
                    return ProcessingMetadata(
                        file_name=row['file_name'],
                        file_size=metadata_dict.get('file_size', 0),
                        file_extension=metadata_dict.get('file_extension', ''),
                        processing_state=row['processing_state'],  # Già stringa dal DB
                        current_phase=row['current_phase'],        # Già stringa dal DB
                        celery_task_id=row['celery_task_id'],
                        worker_node=row['worker_node'],
                        retry_count=row['retry_count'],
                        max_retries=row['max_retries'],
                        error_message=row['error_message'],
                        quarantine_path=row['quarantine_path'],
                        created_at=datetime.fromisoformat(row['created_at']),
                        updated_at=datetime.fromisoformat(row['updated_at'])
                    )
                return None

        except Exception as e:
            self.logger.error(f"Failed to get processing status for {file_name}: {e}")
            return None

    # --- GESTIONE ERRORI ---

    def record_error(self, error_record: ErrorRecord, correlation_id: str = None) -> bool:
        """
        Registra un errore nel sistema di log strutturato.

        Args:
            error_record: Record dell'errore da registrare
            correlation_id: ID di correlazione per tracciamento

        Returns:
            bool: True se la registrazione è riuscita
        """
        if correlation_id is None:
            correlation_id = self.generate_correlation_id()

        try:
            # Salva nel database
            with db_connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO processing_error_log
                    (file_name, processing_state, error_category, error_type, error_message,
                     error_details, celery_task_id, worker_node, resolution_status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    error_record.file_name,
                    error_record.processing_state.value,
                    error_record.error_category.value,
                    error_record.error_severity.value,
                    error_record.error_message,
                    json.dumps(error_record.error_details),
                    error_record.celery_task_id,
                    error_record.worker_node,
                    error_record.resolution_status,
                    error_record.created_at.isoformat()
                ))
                conn.commit()

            # Log strutturato
            log_level = {
                ErrorSeverity.CRITICAL: logging.CRITICAL,
                ErrorSeverity.ERROR: logging.ERROR,
                ErrorSeverity.WARNING: logging.WARNING,
                ErrorSeverity.INFO: logging.INFO
            }.get(error_record.error_severity, logging.ERROR)

            self.logger.log(
                log_level,
                f"Processing error in {error_record.file_name}: {error_record.error_message}",
                extra={
                    "correlation_id": correlation_id,
                    "file_name": error_record.file_name,
                    "error_category": error_record.error_category.value,
                    "error_severity": error_record.error_severity.value,
                    "processing_state": error_record.processing_state.value
                }
            )

            return True

        except Exception as e:
            self.logger.error(f"Failed to record error: {e}", extra={"correlation_id": correlation_id})
            return False

    def classify_error(self, exception: Exception, file_name: str, processing_phase: ProcessingPhase) -> ErrorRecord:
        """
        Classifica automaticamente un'eccezione in un ErrorRecord strutturato.

        Args:
            exception: Eccezione da classificare
            file_name: Nome del file in processamento
            processing_phase: Fase in cui si è verificato l'errore

        Returns:
            ErrorRecord: Record dell'errore classificato
        """
        error_message = str(exception)
        error_details = {
            "exception_type": type(exception).__name__,
            "exception_args": exception.args,
            "traceback": traceback.format_exc()
        }

        # Classificazione basata sul tipo di eccezione e messaggio
        error_category = ErrorCategory.UNKNOWN_ERROR
        error_severity = ErrorSeverity.ERROR

        if isinstance(exception, (IOError, OSError)):
            error_category = ErrorCategory.IO_ERROR
            if "permission" in error_message.lower():
                error_category = ErrorCategory.PERMISSION_ERROR
            error_severity = ErrorSeverity.CRITICAL
        elif isinstance(exception, ConnectionError):
            error_category = ErrorCategory.CONNECTION_ERROR
            error_severity = ErrorSeverity.CRITICAL
        elif isinstance(exception, TimeoutError):
            error_category = ErrorCategory.TIMEOUT_ERROR
            error_severity = ErrorSeverity.WARNING
        elif "api" in error_message.lower() or "llm" in error_message.lower():
            error_category = ErrorCategory.API_ERROR
            error_severity = ErrorSeverity.ERROR
        elif "json" in error_message.lower() or "format" in error_message.lower():
            error_category = ErrorCategory.FORMAT_ERROR
            error_severity = ErrorSeverity.ERROR
        elif "index" in error_message.lower() or "database" in error_message.lower():
            error_category = ErrorCategory.INDEXING_ERROR
            error_severity = ErrorSeverity.CRITICAL

        # Determina stato di processamento basato sulla fase
        processing_state = self._determine_failure_state(processing_phase, error_category)

        return ErrorRecord(
            file_name=file_name,
            processing_state=processing_state,
            error_category=error_category,
            error_severity=error_severity,
            error_message=error_message,
            error_details=error_details
        )

    def _determine_failure_state(self, phase: ProcessingPhase, error_category: ErrorCategory) -> ProcessingState:
        """Determina lo stato di fallimento basato sulla fase e categoria di errore"""
        state_mapping = {
            ProcessingPhase.PHASE_1: ProcessingState.FAILED_PARSING,
            ProcessingPhase.PHASE_2: ProcessingState.FAILED_PARSING,
            ProcessingPhase.PHASE_3: {
                ErrorCategory.API_ERROR: ProcessingState.FAILED_EXTRACTION_API,
                ErrorCategory.FORMAT_ERROR: ProcessingState.FAILED_EXTRACTION_FORMAT,
                ErrorCategory.CONNECTION_ERROR: ProcessingState.FAILED_EXTRACTION_API,
                ErrorCategory.TIMEOUT_ERROR: ProcessingState.FAILED_EXTRACTION_API,
            }.get(error_category, ProcessingState.FAILED_EXTRACTION_API),
            ProcessingPhase.PHASE_4: ProcessingState.FAILED_INDEXING,
            ProcessingPhase.PHASE_5: ProcessingState.FAILED_ARCHIVING
        }

        return state_mapping.get(phase, ProcessingState.MANUAL_INTERVENTION_REQUIRED)

    # --- GESTIONE QUARANTENA ---

    def move_to_quarantine(self, file_name: str, original_path: str,
                          failure_reason: str, error_details: Dict[str, Any] = None) -> str:
        """
        Sposta un file nella quarantena per analisi successiva.

        Args:
            file_name: Nome del file
            original_path: Percorso originale del file
            failure_reason: Motivo del fallimento
            error_details: Dettagli tecnici dell'errore

        Returns:
            str: Percorso del file in quarantena
        """
        try:
            # Crea sottodirectory basata sulla data
            today = datetime.now().strftime("%Y%m%d")
            quarantine_subdir = os.path.join(QUARANTINE_DIR, today)
            os.makedirs(quarantine_subdir, exist_ok=True)

            # Percorso destinazione
            dest_path = os.path.join(quarantine_subdir, file_name)

            # Sposta il file se esiste
            if os.path.exists(original_path):
                import shutil
                shutil.move(original_path, dest_path)
            else:
                # Crea file placeholder se il file originale non esiste
                with open(dest_path, 'w') as f:
                    f.write(f"Placeholder for failed file: {file_name}\nOriginal path: {original_path}\nFailure reason: {failure_reason}\n")

            # Registra in database
            with db_connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO quarantine_files
                    (file_name, original_path, quarantine_path, failure_reason, failure_category, error_details, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    file_name,
                    original_path,
                    dest_path,
                    failure_reason,
                    error_details.get('error_category', 'UnknownError') if error_details else 'UnknownError',
                    json.dumps(error_details) if error_details else None,
                    datetime.now().isoformat()
                ))
                conn.commit()

            self.logger.info(f"Moved {file_name} to quarantine: {dest_path}")
            return dest_path

        except Exception as e:
            self.logger.error(f"Failed to move {file_name} to quarantine: {e}")
            raise

    def get_quarantined_files(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Recupera lista dei file in quarantena"""
        try:
            with db_connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM quarantine_files
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (limit,))

                files = cursor.fetchall()
                return [dict(file) for file in files]

        except Exception as e:
            self.logger.error(f"Failed to get quarantined files: {e}")
            return []

    # --- GESTIONE METRICHE ---

    def update_processing_metrics(self, date_period: str = None) -> ProcessingMetrics:
        """
        Aggiorna le metriche di processamento per il periodo specificato.

        Args:
            date_period: Periodo in formato 'YYYY-MM-DD' (default: oggi)

        Returns:
            ProcessingMetrics: Metriche aggiornate
        """
        if date_period is None:
            date_period = datetime.now().strftime("%Y-%m-%d")

        try:
            with db_connect() as conn:
                cursor = conn.cursor()

                # Conta documenti per stato
                cursor.execute("""
                    SELECT processing_state, COUNT(*) as count
                    FROM document_processing_status
                    WHERE DATE(created_at) = DATE(?)
                    GROUP BY processing_state
                """, (date_period,))

                state_counts = dict(cursor.fetchall())

                # Calcola metriche
                total_files = sum(state_counts.values())
                files_pending = state_counts.get(ProcessingState.PENDING.value, 0)
                files_processing = state_counts.get(ProcessingState.PROCESSING.value, 0) + state_counts.get(ProcessingState.QUEUED.value, 0)
                files_completed = state_counts.get(ProcessingState.COMPLETED.value, 0)
                files_failed = sum([
                    state_counts.get(state.value, 0) for state in ProcessingState
                    if state.value.startswith('FAILED_')
                ])

                # Conta quarantena
                cursor.execute("""
                    SELECT COUNT(*) as count FROM quarantine_files
                    WHERE DATE(created_at) = DATE(?)
                """, (date_period,))
                quarantine_count = cursor.fetchone()['count']

                # Calcola tasso di errore
                error_rate = (files_failed / total_files * 100) if total_files > 0 else 0.0

                metrics = ProcessingMetrics(
                    date_period=date_period,
                    total_files=total_files,
                    files_pending=files_pending,
                    files_processing=files_processing,
                    files_completed=files_completed,
                    files_failed=files_failed,
                    error_rate=error_rate,
                    quarantine_count=quarantine_count
                )

                # Salva nel database
                cursor.execute("""
                    INSERT OR REPLACE INTO processing_metrics
                    (date_period, total_files, files_pending, files_processing,
                     files_completed, files_failed, error_rate, quarantine_count, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    date_period,
                    metrics.total_files,
                    metrics.files_pending,
                    metrics.files_processing,
                    metrics.files_completed,
                    metrics.files_failed,
                    metrics.error_rate,
                    metrics.quarantine_count,
                    metrics.created_at.isoformat()
                ))
                conn.commit()

                return metrics

        except Exception as e:
            self.logger.error(f"Failed to update processing metrics: {e}")
            return ProcessingMetrics(date_period=date_period)

    def get_processing_metrics(self, days: int = 7) -> List[ProcessingMetrics]:
        """Recupera metriche di processamento per gli ultimi giorni"""
        try:
            with db_connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM processing_metrics
                    WHERE date_period >= DATE('now', ?)
                    ORDER BY date_period DESC
                """, (f"-{days} days",))

                metrics = cursor.fetchall()
                return [ProcessingMetrics(**dict(metric)) for metric in metrics]

        except Exception as e:
            self.logger.error(f"Failed to get processing metrics: {e}")
            return []

    # --- RECOVERY E RETRY ---

    def should_retry(self, file_name: str) -> bool:
        """
        Determina se un file dovrebbe essere ritentato.

        Args:
            file_name: Nome del file

        Returns:
            bool: True se dovrebbe essere ritentato
        """
        try:
            with db_connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT retry_count, max_retries, processing_state
                    FROM document_processing_status
                    WHERE file_name = ?
                """, (file_name,))

                result = cursor.fetchone()
                if result:
                    return (result['retry_count'] < result['max_retries'] and
                           result['processing_state'] != ProcessingState.COMPLETED.value)

                return False

        except Exception as e:
            self.logger.error(f"Failed to check retry eligibility for {file_name}: {e}")
            return False

    def increment_retry_count(self, file_name: str) -> bool:
        """Incrementa il contatore di retry per un file"""
        try:
            with db_connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE document_processing_status
                    SET retry_count = retry_count + 1, updated_at = ?
                    WHERE file_name = ?
                """, (datetime.now().isoformat(), file_name))
                conn.commit()
                return True

        except Exception as e:
            self.logger.error(f"Failed to increment retry count for {file_name}: {e}")
            return False

    def reset_processing_status(self, file_name: str) -> bool:
        """
        Resetta lo stato di processamento per permettere un nuovo tentativo.

        Args:
            file_name: Nome del file

        Returns:
            bool: True se il reset è riuscito
        """
        try:
            with db_connect() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE document_processing_status
                    SET processing_state = ?, current_phase = ?, error_message = ?,
                        retry_count = 0, updated_at = ?
                    WHERE file_name = ?
                """, (
                    ProcessingState.PENDING.value,
                    ProcessingPhase.PHASE_1.value,
                    None,
                    datetime.now().isoformat(),
                    file_name
                ))
                conn.commit()

            self.logger.info(f"Reset processing status for {file_name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to reset processing status for {file_name}: {e}")
            return False

# --- ISTANZA GLOBALE ---
error_framework = ErrorDiagnosisFramework()

# --- FUNZIONI DI UTILITÀ PUBBLICHE ---

def get_processing_status_summary() -> Dict[str, Any]:
    """Restituisce un riassunto dello stato di processamento di tutti i file"""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()

            # Conta per stato
            cursor.execute("""
                SELECT processing_state, COUNT(*) as count
                FROM document_processing_status
                GROUP BY processing_state
            """)

            state_counts = dict(cursor.fetchall())

            # File recenti
            cursor.execute("""
                SELECT file_name, processing_state, updated_at
                FROM document_processing_status
                ORDER BY updated_at DESC
                LIMIT 10
            """)

            recent_files = [dict(row) for row in cursor.fetchall()]

            # Errori recenti
            cursor.execute("""
                SELECT file_name, error_message, created_at
                FROM processing_error_log
                WHERE resolution_status = 'open'
                ORDER BY created_at DESC
                LIMIT 5
            """)

            recent_errors = [dict(row) for row in cursor.fetchall()]

            return {
                "state_counts": state_counts,
                "recent_files": recent_files,
                "recent_errors": recent_errors,
                "total_files": sum(state_counts.values()),
                "failed_files": sum([
                    count for state, count in state_counts.items()
                    if state.startswith('FAILED_')
                ])
            }

    except Exception as e:
        st.error(f"Errore nel recupero riassunto processamento: {e}")
        return {"state_counts": {}, "recent_files": [], "recent_errors": []}

def get_error_dashboard_data() -> Dict[str, Any]:
    """Recupera dati per la dashboard degli errori"""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()

            # Errori per categoria
            cursor.execute("""
                SELECT error_category, COUNT(*) as count
                FROM processing_error_log
                WHERE resolution_status = 'open'
                GROUP BY error_category
                ORDER BY count DESC
            """)

            errors_by_category = [dict(row) for row in cursor.fetchall()]

            # Errori per severità
            cursor.execute("""
                SELECT error_type, COUNT(*) as count
                FROM processing_error_log
                WHERE resolution_status = 'open'
                GROUP BY error_type
                ORDER BY count DESC
            """)

            errors_by_severity = [dict(row) for row in cursor.fetchall()]

            # Trend errori (ultimi 7 giorni)
            cursor.execute("""
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM processing_error_log
                WHERE created_at >= DATE('now', '-7 days')
                GROUP BY DATE(created_at)
                ORDER BY date
            """)

            error_trends = [dict(row) for row in cursor.fetchall()]

            return {
                "errors_by_category": errors_by_category,
                "errors_by_severity": errors_by_severity,
                "error_trends": error_trends,
                "total_open_errors": sum(error['count'] for error in errors_by_category)
            }

    except Exception as e:
        st.error(f"Errore nel recupero dati dashboard errori: {e}")
        return {"errors_by_category": [], "errors_by_severity": [], "error_trends": []}

def resolve_error(error_id: int, resolution_notes: str, resolution_status: str = "resolved") -> bool:
    """
    Risolve un errore registrato.

    Args:
        error_id: ID dell'errore da risolvere
        resolution_notes: Note sulla risoluzione
        resolution_status: Stato di risoluzione ('resolved', 'ignored', 'investigating')

    Returns:
        bool: True se la risoluzione è riuscita
    """
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE processing_error_log
                SET resolution_status = ?, resolution_notes = ?, resolved_at = ?
                WHERE id = ?
            """, (resolution_status, resolution_notes, datetime.now().isoformat(), error_id))
            conn.commit()

        return True

    except Exception as e:
        st.error(f"Errore nella risoluzione errore: {e}")
        return False

def get_files_requiring_intervention() -> List[Dict[str, Any]]:
    """Recupera file che richiedono intervento manuale"""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM document_processing_status
                WHERE processing_state IN (?, ?)
                ORDER BY updated_at DESC
            """, (ProcessingState.MANUAL_INTERVENTION_REQUIRED.value, ProcessingState.FAILED_PARSING.value))

            files = cursor.fetchall()
            return [dict(file) for file in files]

    except Exception as e:
        st.error(f"Errore nel recupero file per intervento: {e}")
        return []
