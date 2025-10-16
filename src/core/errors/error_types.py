"""
Error types and custom exceptions for Archivista AI.
Centralized error definitions with proper categorization and context.
"""

from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


class ErrorSeverity(Enum):
    """Severità errori."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Categorie errori."""
    VALIDATION = "validation"
    DATABASE = "database"
    FILE_SYSTEM = "file_system"
    AI_SERVICE = "ai_service"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NETWORK = "network"
    CONFIGURATION = "configuration"
    PROCESSING = "processing"
    EXTERNAL_SERVICE = "external_service"
    SYSTEM = "system"


@dataclass
class ErrorContext:
    """Contesto errore per debugging e tracciamento."""
    user_id: Optional[str]
    operation: str
    component: str
    timestamp: datetime
    metadata: Dict[str, Any]
    session_id: Optional[str] = None
    request_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converte contesto in dizionario."""
        return {
            'user_id': self.user_id,
            'operation': self.operation,
            'component': self.component,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata,
            'session_id': self.session_id,
            'request_id': self.request_id,
        }


@dataclass
class ErrorResult:
    """Risultato errore strutturato."""
    error_id: str
    message: str
    category: ErrorCategory
    severity: ErrorSeverity
    context: ErrorContext
    stack_trace: Optional[str] = None
    recovery_suggestions: Optional[str] = None
    is_retryable: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Converte errore in dizionario."""
        return {
            'error_id': self.error_id,
            'message': self.message,
            'category': self.category.value,
            'severity': self.severity.value,
            'context': self.context.to_dict(),
            'stack_trace': self.stack_trace,
            'recovery_suggestions': self.recovery_suggestions,
            'is_retryable': self.is_retryable,
            'timestamp': self.context.timestamp.isoformat(),
        }


class ArchivistaError(Exception):
    """Eccezione base per errori Archivista."""

    def __init__(
        self,
        message: str,
        error_code: str,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[ErrorContext] = None,
        is_retryable: bool = False,
        recovery_suggestions: Optional[str] = None
    ):
        super().__init__(message)
        self.error_code = error_code
        self.category = category
        self.severity = severity
        self.context = context or ErrorContext(
            user_id=None,
            operation="unknown",
            component="unknown",
            timestamp=datetime.utcnow(),
            metadata={}
        )
        self.is_retryable = is_retryable
        self.recovery_suggestions = recovery_suggestions
        self.error_id = f"{error_code}_{int(datetime.utcnow().timestamp())}"

    def to_result(self) -> ErrorResult:
        """Converte eccezione in ErrorResult."""
        return ErrorResult(
            error_id=self.error_id,
            message=str(self),
            category=self.category,
            severity=self.severity,
            context=self.context,
            stack_trace=self._get_stack_trace(),
            recovery_suggestions=self.recovery_suggestions,
            is_retryable=self.is_retryable
        )

    def _get_stack_trace(self) -> Optional[str]:
        """Recupera stack trace errore."""
        import traceback
        try:
            return traceback.format_exc()
        except Exception:
            return None


# Database Errors

class DatabaseError(ArchivistaError):
    """Errore operazioni database."""

    def __init__(
        self,
        message: str,
        operation: str,
        table: Optional[str] = None,
        context: Optional[ErrorContext] = None
    ):
        super().__init__(
            message,
            error_code="DATABASE_ERROR",
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH,
            context=context or ErrorContext(
                user_id=None,
                operation=operation,
                component="database",
                timestamp=datetime.utcnow(),
                metadata={'table': table} if table else {}
            ),
            is_retryable=True,
            recovery_suggestions="Verifica connessione database e integrità dati"
        )


class ConnectionError(DatabaseError):
    """Errore connessione database."""

    def __init__(self, message: str = "Impossibile connettersi al database"):
        super().__init__(
            message,
            operation="connection",
            severity=ErrorSeverity.CRITICAL,
            is_retryable=True,
            recovery_suggestions="Verifica configurazione database e connettività di rete"
        )


class QueryError(DatabaseError):
    """Errore esecuzione query."""

    def __init__(self, message: str, query: str, params: Optional[tuple] = None):
        super().__init__(
            message,
            operation="query",
            severity=ErrorSeverity.HIGH,
            is_retryable=True,
            recovery_suggestions="Verifica sintassi query e validità parametri"
        )
        self.query = query
        self.params = params


class MigrationError(DatabaseError):
    """Errore migrazione database."""

    def __init__(self, message: str, version: str):
        super().__init__(
            message,
            operation="migration",
            severity=ErrorSeverity.CRITICAL,
            is_retryable=False,
            recovery_suggestions="Esegui backup e ripristino database, contatta supporto"
        )
        self.version = version


# File System Errors

class FileSystemError(ArchivistaError):
    """Errore operazioni file system."""

    def __init__(
        self,
        message: str,
        file_path: str,
        operation: str = "file_operation",
        context: Optional[ErrorContext] = None
    ):
        super().__init__(
            message,
            error_code="FILESYSTEM_ERROR",
            category=ErrorCategory.FILE_SYSTEM,
            severity=ErrorSeverity.HIGH,
            context=context or ErrorContext(
                user_id=None,
                operation=operation,
                component="filesystem",
                timestamp=datetime.utcnow(),
                metadata={'file_path': file_path}
            ),
            is_retryable=True,
            recovery_suggestions="Verifica permessi file e spazio disponibile"
        )
        self.file_path = file_path


class FileNotFoundError(FileSystemError):
    """File non trovato."""

    def __init__(self, file_path: str):
        super().__init__(
            f"File non trovato: {file_path}",
            file_path,
            operation="read",
            severity=ErrorSeverity.MEDIUM,
            recovery_suggestions="Verifica percorso file e presenza file"
        )


class PermissionError(FileSystemError):
    """Errore permessi file."""

    def __init__(self, file_path: str, operation: str = "access"):
        super().__init__(
            f"Permessi insufficienti per {operation}: {file_path}",
            file_path,
            operation=operation,
            severity=ErrorSeverity.HIGH,
            recovery_suggestions="Verifica permessi file e diritti utente"
        )


class DiskSpaceError(FileSystemError):
    """Spazio disco insufficiente."""

    def __init__(self, required_space: int, available_space: int):
        super().__init__(
            f"Spazio insufficiente. Richiesto: {required_space}MB, Disponibile: {available_space}MB",
            "",
            operation="write",
            severity=ErrorSeverity.HIGH,
            recovery_suggestions="Libera spazio disco o aumenta capacità storage"
        )
        self.required_space = required_space
        self.available_space = available_space


# AI Service Errors

class AIServiceError(ArchivistaError):
    """Errore servizio AI."""

    def __init__(
        self,
        message: str,
        model: Optional[str] = None,
        operation: str = "ai_operation",
        context: Optional[ErrorContext] = None
    ):
        super().__init__(
            message,
            error_code="AI_SERVICE_ERROR",
            category=ErrorCategory.AI_SERVICE,
            severity=ErrorSeverity.HIGH,
            context=context or ErrorContext(
                user_id=None,
                operation=operation,
                component="ai_service",
                timestamp=datetime.utcnow(),
                metadata={'model': model} if model else {}
            ),
            is_retryable=True,
            recovery_suggestions="Verifica configurazione AI e connettività servizio"
        )
        self.model = model


class ModelNotAvailableError(AIServiceError):
    """Modello AI non disponibile."""

    def __init__(self, model: str):
        super().__init__(
            f"Modello non disponibile: {model}",
            model=model,
            operation="model_access",
            severity=ErrorSeverity.HIGH,
            recovery_suggestions="Verifica disponibilità modello o usa modello alternativo"
        )


class TokenLimitError(AIServiceError):
    """Limite token superato."""

    def __init__(self, requested_tokens: int, max_tokens: int):
        super().__init__(
            f"Limite token superato. Richiesto: {requested_tokens}, Massimo: {max_tokens}",
            operation="token_processing",
            severity=ErrorSeverity.MEDIUM,
            recovery_suggestions="Riduci lunghezza input o aumenta limite token"
        )
        self.requested_tokens = requested_tokens
        self.max_tokens = max_tokens


class ConfidenceThresholdError(AIServiceError):
    """Soglia confidenza non raggiunta."""

    def __init__(self, confidence: float, threshold: float):
        super().__init__(
            f"Confidenza troppo bassa: {confidence:.2f} < {threshold:.2f}",
            operation="confidence_check",
            severity=ErrorSeverity.LOW,
            recovery_suggestions="Verifica qualità input o regola soglia confidenza"
        )
        self.confidence = confidence
        self.threshold = threshold


# Authentication & Authorization Errors

class AuthenticationError(ArchivistaError):
    """Errore autenticazione."""

    def __init__(
        self,
        message: str = "Errore autenticazione",
        username: Optional[str] = None,
        context: Optional[ErrorContext] = None
    ):
        super().__init__(
            message,
            error_code="AUTHENTICATION_ERROR",
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            context=context or ErrorContext(
                user_id=username,
                operation="authentication",
                component="auth",
                timestamp=datetime.utcnow(),
                metadata={'username': username} if username else {}
            ),
            is_retryable=False,
            recovery_suggestions="Verifica credenziali e riprova"
        )
        self.username = username


class InvalidCredentialsError(AuthenticationError):
    """Credenziali non valide."""

    def __init__(self, username: str):
        super().__init__(
            "Credenziali non valide",
            username=username,
            recovery_suggestions="Verifica username e password"
        )


class AccountLockedError(AuthenticationError):
    """Account bloccato."""

    def __init__(self, username: str, lockout_duration: int):
        super().__init__(
            f"Account temporaneamente bloccato per {lockout_duration} minuti",
            username=username,
            recovery_suggestions=f"Attendi {lockout_duration} minuti o contatta supporto"
        )
        self.lockout_duration = lockout_duration


class AuthorizationError(ArchivistaError):
    """Errore autorizzazione."""

    def __init__(
        self,
        message: str,
        resource: str,
        required_permission: str,
        user_id: Optional[str] = None,
        context: Optional[ErrorContext] = None
    ):
        super().__init__(
            message,
            error_code="AUTHORIZATION_ERROR",
            category=ErrorCategory.AUTHORIZATION,
            severity=ErrorSeverity.HIGH,
            context=context or ErrorContext(
                user_id=user_id,
                operation="authorization",
                component="auth",
                timestamp=datetime.utcnow(),
                metadata={
                    'resource': resource,
                    'required_permission': required_permission
                }
            ),
            is_retryable=False,
            recovery_suggestions="Verifica permessi utente o contatta amministratore"
        )
        self.resource = resource
        self.required_permission = required_permission


class InsufficientPermissionsError(AuthorizationError):
    """Permessi insufficienti."""

    def __init__(self, resource: str, required_permission: str, user_id: str):
        super().__init__(
            f"Permessi insufficienti per accedere a: {resource}",
            resource=resource,
            required_permission=required_permission,
            user_id=user_id,
            recovery_suggestions="Richiedi permessi necessari o contatta amministratore"
        )


# Validation Errors

class ValidationError(ArchivistaError):
    """Errore validazione input."""

    def __init__(
        self,
        message: str,
        field: str,
        value: Any,
        context: Optional[ErrorContext] = None
    ):
        super().__init__(
            message,
            error_code="VALIDATION_ERROR",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            context=context or ErrorContext(
                user_id=None,
                operation="validation",
                component="validation",
                timestamp=datetime.utcnow(),
                metadata={'field': field, 'value': str(value)}
            ),
            is_retryable=False,
            recovery_suggestions="Correggi input e riprova"
        )
        self.field = field
        self.value = value


class InvalidFormatError(ValidationError):
    """Formato input non valido."""

    def __init__(self, field: str, expected_format: str, actual_value: Any):
        super().__init__(
            f"Formato non valido per {field}. Atteso: {expected_format}",
            field=field,
            value=actual_value,
            recovery_suggestions=f"Usa formato corretto: {expected_format}"
        )
        self.expected_format = expected_format


class MissingRequiredFieldError(ValidationError):
    """Campo obbligatorio mancante."""

    def __init__(self, field: str):
        super().__init__(
            f"Campo obbligatorio mancante: {field}",
            field=field,
            value=None,
            recovery_suggestions=f"Fornisci valore per campo: {field}"
        )


class OutOfRangeError(ValidationError):
    """Valore fuori range."""

    def __init__(self, field: str, value: Any, min_val: Any, max_val: Any):
        super().__init__(
            f"Valore {value} fuori range [{min_val}, {max_val}] per campo {field}",
            field=field,
            value=value,
            recovery_suggestions=f"Usa valore tra {min_val} e {max_val}"
        )
        self.min_val = min_val
        self.max_val = max_val


# Processing Errors

class ProcessingError(ArchivistaError):
    """Errore processamento documenti."""

    def __init__(
        self,
        message: str,
        file_path: str,
        stage: str = "unknown",
        context: Optional[ErrorContext] = None
    ):
        super().__init__(
            message,
            error_code="PROCESSING_ERROR",
            category=ErrorCategory.PROCESSING,
            severity=ErrorSeverity.HIGH,
            context=context or ErrorContext(
                user_id=None,
                operation="document_processing",
                component="processor",
                timestamp=datetime.utcnow(),
                metadata={'file_path': file_path, 'stage': stage}
            ),
            is_retryable=True,
            recovery_suggestions="Verifica formato file e riprova"
        )
        self.file_path = file_path
        self.stage = stage


class DocumentProcessingError(ProcessingError):
    """Errore specifico processamento documento."""

    def __init__(self, message: str, file_path: str, stage: str = "processing"):
        super().__init__(
            message,
            file_path=file_path,
            stage=stage,
            recovery_suggestions="Verifica integrità file e formato supportato"
        )


class TextExtractionError(ProcessingError):
    """Errore estrazione testo."""

    def __init__(self, file_path: str, extraction_method: str):
        super().__init__(
            f"Impossibile estrarre testo da: {file_path}",
            file_path=file_path,
            stage="text_extraction",
            recovery_suggestions="Verifica che il file contenga testo estraibile"
        )
        self.extraction_method = extraction_method


class EmbeddingGenerationError(ProcessingError):
    """Errore generazione embeddings."""

    def __init__(self, file_path: str, model: str):
        super().__init__(
            f"Impossibile generare embeddings per: {file_path}",
            file_path=file_path,
            stage="embedding_generation",
            recovery_suggestions="Verifica configurazione modello AI"
        )
        self.model = model


# Network Errors

class NetworkError(ArchivistaError):
    """Errore rete e connettività."""

    def __init__(
        self,
        message: str,
        service: str,
        operation: str = "network_call",
        context: Optional[ErrorContext] = None
    ):
        super().__init__(
            message,
            error_code="NETWORK_ERROR",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            context=context or ErrorContext(
                user_id=None,
                operation=operation,
                component="network",
                timestamp=datetime.utcnow(),
                metadata={'service': service}
            ),
            is_retryable=True,
            recovery_suggestions="Verifica connettività rete e stato servizio"
        )
        self.service = service


class ServiceUnavailableError(NetworkError):
    """Servizio non disponibile."""

    def __init__(self, service: str, url: str):
        super().__init__(
            f"Servizio non disponibile: {service}",
            service=service,
            recovery_suggestions="Verifica stato servizio e configurazione URL"
        )
        self.url = url


class TimeoutError(NetworkError):
    """Timeout operazione."""

    def __init__(self, service: str, timeout_seconds: int):
        super().__init__(
            f"Timeout operazione {service} dopo {timeout_seconds}s",
            service=service,
            recovery_suggestions="Aumenta timeout o verifica performance servizio"
        )
        self.timeout_seconds = timeout_seconds


# Configuration Errors

class ConfigurationError(ArchivistaError):
    """Errore configurazione."""

    def __init__(
        self,
        message: str,
        config_key: str,
        context: Optional[ErrorContext] = None
    ):
        super().__init__(
            message,
            error_code="CONFIGURATION_ERROR",
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.CRITICAL,
            context=context or ErrorContext(
                user_id=None,
                operation="configuration",
                component="config",
                timestamp=datetime.utcnow(),
                metadata={'config_key': config_key}
            ),
            is_retryable=False,
            recovery_suggestions="Verifica configurazione e riavvia applicazione"
        )
        self.config_key = config_key


class MissingConfigurationError(ConfigurationError):
    """Configurazione mancante."""

    def __init__(self, config_key: str, default_value: Any = None):
        super().__init__(
            f"Configurazione mancante: {config_key}",
            config_key=config_key,
            recovery_suggestions=f"Imposta valore per configurazione: {config_key}"
        )
        self.default_value = default_value


class InvalidConfigurationError(ConfigurationError):
    """Configurazione non valida."""

    def __init__(self, config_key: str, value: Any, reason: str):
        super().__init__(
            f"Configurazione non valida per {config_key}: {reason}",
            config_key=config_key,
            recovery_suggestions=f"Correggi valore configurazione: {config_key}"
        )
        self.value = value
        self.reason = reason


# External Service Errors

class ExternalServiceError(ArchivistaError):
    """Errore servizio esterno."""

    def __init__(
        self,
        message: str,
        service_name: str,
        operation: str,
        context: Optional[ErrorContext] = None
    ):
        super().__init__(
            message,
            error_code="EXTERNAL_SERVICE_ERROR",
            category=ErrorCategory.EXTERNAL_SERVICE,
            severity=ErrorSeverity.HIGH,
            context=context or ErrorContext(
                user_id=None,
                operation=operation,
                component="external_service",
                timestamp=datetime.utcnow(),
                metadata={'service_name': service_name}
            ),
            is_retryable=True,
            recovery_suggestions="Verifica stato servizio esterno e configurazione"
        )
        self.service_name = service_name


class RedisError(ExternalServiceError):
    """Errore Redis."""

    def __init__(self, message: str, operation: str = "redis_operation"):
        super().__init__(
            message,
            service_name="redis",
            operation=operation,
            recovery_suggestions="Verifica configurazione Redis e connettività"
        )


class CeleryError(ExternalServiceError):
    """Errore Celery."""

    def __init__(self, message: str, operation: str = "celery_operation"):
        super().__init__(
            message,
            service_name="celery",
            operation=operation,
            recovery_suggestions="Verifica configurazione Celery e worker attivi"
        )


# System Errors

class SystemError(ArchivistaError):
    """Errore sistema interno."""

    def __init__(
        self,
        message: str,
        component: str,
        context: Optional[ErrorContext] = None
    ):
        super().__init__(
            message,
            error_code="SYSTEM_ERROR",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.CRITICAL,
            context=context or ErrorContext(
                user_id=None,
                operation="system_operation",
                component=component,
                timestamp=datetime.utcnow(),
                metadata={}
            ),
            is_retryable=False,
            recovery_suggestions="Contatta supporto tecnico"
        )
        self.component = component


class MemoryError(SystemError):
    """Errore memoria insufficiente."""

    def __init__(self, required_memory: int, available_memory: int):
        super().__init__(
            f"Memoria insufficiente. Richiesta: {required_memory}MB, Disponibile: {available_memory}MB",
            component="memory_manager",
            recovery_suggestions="Libera memoria o aumenta risorse sistema"
        )
        self.required_memory = required_memory
        self.available_memory = available_memory


class ResourceExhaustedError(SystemError):
    """Risorse esaurite."""

    def __init__(self, resource_type: str, limit: int, current_usage: int):
        super().__init__(
            f"Risorsa esaurita: {resource_type}. Limite: {limit}, Uso attuale: {current_usage}",
            component="resource_manager",
            recovery_suggestions="Aumenta limiti risorse o riduci carico"
        )
        self.resource_type = resource_type
        self.limit = limit
        self.current_usage = current_usage


# Utility functions for error handling

def create_error_context(
    user_id: Optional[str] = None,
    operation: str = "unknown",
    component: str = "unknown",
    metadata: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
    request_id: Optional[str] = None
) -> ErrorContext:
    """Crea contesto errore standardizzato."""
    return ErrorContext(
        user_id=user_id,
        operation=operation,
        component=component,
        timestamp=datetime.utcnow(),
        metadata=metadata or {},
        session_id=session_id,
        request_id=request_id
    )


def classify_error(error: Exception) -> tuple[ErrorCategory, ErrorSeverity]:
    """Classifica eccezione generica in categoria e severità."""
    error_type = type(error).__name__

    # Mappatura errori built-in
    builtin_mapping = {
        'ConnectionError': (ErrorCategory.NETWORK, ErrorSeverity.HIGH),
        'TimeoutError': (ErrorCategory.NETWORK, ErrorSeverity.HIGH),
        'FileNotFoundError': (ErrorCategory.FILE_SYSTEM, ErrorSeverity.MEDIUM),
        'PermissionError': (ErrorCategory.FILE_SYSTEM, ErrorSeverity.HIGH),
        'ValueError': (ErrorCategory.VALIDATION, ErrorSeverity.MEDIUM),
        'TypeError': (ErrorCategory.VALIDATION, ErrorSeverity.MEDIUM),
        'KeyError': (ErrorCategory.VALIDATION, ErrorSeverity.MEDIUM),
        'AttributeError': (ErrorCategory.SYSTEM, ErrorSeverity.MEDIUM),
        'ImportError': (ErrorCategory.SYSTEM, ErrorSeverity.HIGH),
        'ModuleNotFoundError': (ErrorCategory.SYSTEM, ErrorSeverity.HIGH),
        'MemoryError': (ErrorCategory.SYSTEM, ErrorSeverity.CRITICAL),
        'OSError': (ErrorCategory.SYSTEM, ErrorSeverity.HIGH),
    }

    return builtin_mapping.get(error_type, (ErrorCategory.SYSTEM, ErrorSeverity.MEDIUM))


def should_retry_error(error: Exception, attempt_count: int = 1) -> bool:
    """Determina se errore dovrebbe essere ritentato."""
    if attempt_count > 3:
        return False

    # Errori sempre retryable
    always_retry = (
        ConnectionError,
        NetworkError,
        TimeoutError,
        ServiceUnavailableError,
        AIServiceError,
    )

    # Errori mai retryable
    never_retry = (
        ValidationError,
        AuthenticationError,
        AuthorizationError,
        ConfigurationError,
        MissingConfigurationError,
    )

    if isinstance(error, never_retry):
        return False

    if isinstance(error, always_retry):
        return True

    # Per altri errori, decidi basato su categoria
    category, _ = classify_error(error)
    return category in [ErrorCategory.NETWORK, ErrorCategory.EXTERNAL_SERVICE]
