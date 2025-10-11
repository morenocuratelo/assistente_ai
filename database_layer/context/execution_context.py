# Execution Context - Contesto esecuzione applicazione
"""
Classe centrale per gestione stato applicazione in Archivista AI.

Fornisce:
- Gestione stato globale applicazione
- Supporto contesto progetto (preparazione Fase 1)
- Configurazione servizi centralizzata
- Dependency injection container
- Session management
"""

import logging
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime
from contextvars import ContextVar
from dataclasses import dataclass, field
from .context_manager import ContextManager

logger = logging.getLogger('ExecutionContext')

@dataclass
class ApplicationState:
    """Stato applicazione globale"""
    initialized: bool = False
    current_user_id: Optional[int] = None
    current_project_id: Optional[str] = None
    session_id: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.now)
    request_count: int = 0
    error_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Converte stato a dizionario"""
        return {
            'initialized': self.initialized,
            'current_user_id': self.current_user_id,
            'current_project_id': self.current_project_id,
            'session_id': self.session_id,
            'start_time': self.start_time.isoformat(),
            'request_count': self.request_count,
            'error_count': self.error_count,
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds()
        }

class ExecutionContext:
    """
    Contesto esecuzione principale applicazione.

    Gestisce stato globale e fornisce servizi centralizzati
    per preparazione supporto multi-progetto.
    """

    # Context variable per gestione thread-local
    _current_context: ContextVar[Optional['ExecutionContext']] = ContextVar('current_context', default=None)

    def __init__(self, project_id: str = None, user_id: int = None):
        """
        Inizializza contesto esecuzione.

        Args:
            project_id: ID progetto attivo (Fase 1)
            user_id: ID utente corrente
        """
        self.project_id = project_id
        self.user_id = user_id

        # Stato applicazione
        self.app_state = ApplicationState(
            current_user_id=user_id,
            current_project_id=project_id
        )

        # Servizi centralizzati
        self._services = {}
        self._repositories = {}

        # Context manager
        self.context_manager = ContextManager()

        # Lock per operazioni thread-safe
        self._lock = threading.Lock()

        logger.info(f"ExecutionContext creato - Progetto: {project_id}, Utente: {user_id}")

    @classmethod
    def get_current(cls) -> Optional['ExecutionContext']:
        """Restituisce contesto esecuzione corrente"""
        return cls._current_context.get()

    @classmethod
    def set_current(cls, context: 'ExecutionContext'):
        """Imposta contesto esecuzione corrente"""
        cls._current_context.set(context)

    def initialize(self) -> bool:
        """
        Inizializza contesto e servizi.

        Returns:
            True se inizializzato con successo
        """
        try:
            with self._lock:
                if self.app_state.initialized:
                    logger.warning("Contesto già inizializzato")
                    return True

                # Inizializza servizi base
                self._initialize_services()

                # Inizializza repository
                self._initialize_repositories()

                # Marca come inizializzato
                self.app_state.initialized = True

                logger.info("Contesto esecuzione inizializzato con successo")
                return True

        except Exception as e:
            logger.error(f"Errore inizializzazione contesto: {e}")
            self.app_state.error_count += 1
            return False

    def _initialize_services(self):
        """Inizializza servizi centralizzati"""
        try:
            # Servizi di configurazione
            from ..config_layer.database_config import DatabaseConfig
            from ..config_layer.project_config import ProjectConfig

            db_config = DatabaseConfig(project_id=self.project_id)
            project_config = ProjectConfig(self.project_id) if self.project_id else None

            self._services.update({
                'database_config': db_config,
                'project_config': project_config,
                'initialization_time': datetime.now().isoformat()
            })

            logger.debug("Servizi configurazione inizializzati")

        except Exception as e:
            logger.error(f"Errore inizializzazione servizi configurazione: {e}")
            raise

    def _initialize_repositories(self):
        """Inizializza repository con contesto"""
        try:
            from ..dal.document_repository import DocumentRepository
            from ..dal.user_repository import UserRepository

            # Crea repository con configurazione contesto
            db_config = self._services['database_config']

            # Crea connessione database per repository
            # Nota: In implementazione reale, useremmo connection pooling
            test_connection = self._create_test_connection()

            document_repo = DocumentRepository(db_config.get_database_path())
            user_repo = UserRepository(db_config.get_database_path())

            self._repositories.update({
                'document': document_repo,
                'user': user_repo,
                'test_connection': test_connection
            })

            logger.debug("Repository inizializzati con contesto")

        except Exception as e:
            logger.error(f"Errore inizializzazione repository: {e}")
            raise

    def _create_test_connection(self):
        """Crea connessione test per validazione"""
        try:
            db_config = self._services['database_config']
            db_path = db_config.get_database_path()

            # Crea directory se necessario
            db_config.ensure_directories_exist()

            # Test connessione
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            conn.execute("SELECT 1")  # Test query semplice
            conn.close()

            return True

        except Exception as e:
            logger.error(f"Errore test connessione database: {e}")
            return False

    def get_service(self, service_name: str) -> Any:
        """
        Restituisce servizio registrato.

        Args:
            service_name: Nome servizio

        Returns:
            Servizio richiesto o None
        """
        return self._services.get(service_name)

    def get_repository(self, repository_name: str) -> Any:
        """
        Restituisce repository registrato.

        Args:
            repository_name: Nome repository

        Returns:
            Repository richiesto o None
        """
        return self._repositories.get(repository_name)

    def register_service(self, name: str, service: Any):
        """
        Registra nuovo servizio.

        Args:
            name: Nome servizio
            service: Istanza servizio
        """
        with self._lock:
            self._services[name] = service
            logger.debug(f"Servizio registrato: {name}")

    def register_repository(self, name: str, repository: Any):
        """
        Registra nuovo repository.

        Args:
            name: Nome repository
            repository: Istanza repository
        """
        with self._lock:
            self._repositories[name] = repository
            logger.debug(f"Repository registrato: {name}")

    def get_user_context(self) -> Dict[str, Any]:
        """
        Restituisce contesto utente corrente.

        Returns:
            Dizionario contesto utente
        """
        return {
            'user_id': self.user_id,
            'project_id': self.project_id,
            'session_id': self.app_state.session_id,
            'authenticated': self.user_id is not None,
            'project_active': self.project_id is not None
        }

    def switch_project(self, new_project_id: str) -> bool:
        """
        Cambia progetto attivo (Fase 1).

        Args:
            new_project_id: Nuovo ID progetto

        Returns:
            True se cambiato con successo
        """
        try:
            # Validazione progetto
            if not self._validate_project(new_project_id):
                logger.error(f"Progetto non valido: {new_project_id}")
                return False

            old_project_id = self.project_id
            self.project_id = new_project_id

            # Aggiorna stato applicazione
            self.app_state.current_project_id = new_project_id

            # Reinizializza servizi per nuovo progetto
            self._reinitialize_for_project()

            logger.info(f"Progetto cambiato: {old_project_id} -> {new_project_id}")
            return True

        except Exception as e:
            logger.error(f"Errore cambio progetto: {e}")
            return False

    def _validate_project(self, project_id: str) -> bool:
        """
        Valida progetto.

        Args:
            project_id: ID progetto da validare

        Returns:
            True se progetto valido
        """
        if not project_id or not project_id.strip():
            return False

        # In implementazione completa, verificare esistenza progetto
        # e permessi utente

        return True

    def _reinitialize_for_project(self):
        """Reinizializza servizi per nuovo progetto"""
        try:
            # Reinizializza configurazione
            from ..config_layer.database_config import DatabaseConfig
            from ..config_layer.project_config import ProjectConfig

            db_config = DatabaseConfig(project_id=self.project_id)
            project_config = ProjectConfig(self.project_id) if self.project_id else None

            self._services.update({
                'database_config': db_config,
                'project_config': project_config
            })

            # Reinizializza repository con nuovo contesto
            self._initialize_repositories()

            logger.debug(f"Servizi reinizializzati per progetto: {self.project_id}")

        except Exception as e:
            logger.error(f"Errore reinizializzazione progetto: {e}")
            raise

    def execute_in_context(self, operation_name: str, operation_func, *args, **kwargs):
        """
        Esegue operazione nel contesto corrente.

        Args:
            operation_name: Nome operazione per logging
            operation_func: Funzione da eseguire
            *args, **kwargs: Argomenti funzione

        Returns:
            Risultato operazione
        """
        try:
            # Incrementa contatore richieste
            self.app_state.request_count += 1

            # Log operazione
            logger.debug(f"Esecuzione operazione: {operation_name}")

            # Esegue operazione
            result = operation_func(*args, **kwargs)

            logger.debug(f"Operazione completata: {operation_name}")
            return result

        except Exception as e:
            # Incrementa contatore errori
            self.app_state.error_count += 1
            logger.error(f"Errore operazione {operation_name}: {e}")
            raise

    def get_context_info(self) -> Dict[str, Any]:
        """
        Restituisce informazioni contesto completo.

        Returns:
            Dizionario informazioni contesto
        """
        return {
            'execution_context': {
                'project_id': self.project_id,
                'user_id': self.user_id,
                'session_id': self.app_state.session_id
            },
            'application_state': self.app_state.to_dict(),
            'services_count': len(self._services),
            'repositories_count': len(self._repositories),
            'context_manager': self.context_manager.get_context_info()
        }

    def cleanup(self):
        """Pulisce risorse contesto"""
        try:
            # Chiudi repository
            for repo in self._repositories.values():
                if hasattr(repo, 'close_connection'):
                    repo.close_connection()

            # Reset stato
            self.app_state.request_count = 0
            self.app_state.error_count = 0

            logger.info("Contesto esecuzione pulito")

        except Exception as e:
            logger.error(f"Errore pulizia contesto: {e}")

    def __enter__(self):
        """Context manager entry"""
        self.set_current(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()
        self.set_current(None)

    def __repr__(self) -> str:
        """Rappresentazione contesto"""
        return f"ExecutionContext(project_id={self.project_id}, user_id={self.user_id}, initialized={self.app_state.initialized})"
