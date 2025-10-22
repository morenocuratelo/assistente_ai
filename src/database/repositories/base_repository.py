"""
Repository base per operazioni database.

Fornisce funzionalità comuni per tutti i repository.
"""

import sqlite3
import logging
from typing import Any, Dict, List, Optional, Type, TypeVar
from datetime import datetime
from abc import ABC, abstractmethod

from ..models.base import DatabaseResponse, PaginationParams, PaginatedResponse

logger = logging.getLogger(__name__)

T = TypeVar('T')

class BaseRepository(ABC):
    """Repository base astratto."""

    def __init__(self, db_path=None):
        """Inizializza repository."""
        self.db_path = db_path
        self.db_connection = None
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def get_connection(self) -> sqlite3.Connection:
        """Restituisce connessione database."""
        if isinstance(self.db_path, sqlite3.Connection):
            # Usa connessione esistente ma crea un wrapper thread-safe
            # Per evitare problemi di threading con SQLite, creiamo sempre una nuova connessione
            # se il db_path è una stringa, anche se riceviamo una connessione esistente
            if hasattr(self, '_connection_string'):
                conn = sqlite3.connect(self._connection_string)
                conn.row_factory = sqlite3.Row
                return conn
            else:
                # Fallback per compatibilità
                self.db_path.row_factory = sqlite3.Row
                return self.db_path
        elif isinstance(self.db_path, str):
            # Crea nuova connessione
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            # Salva la stringa per eventuali utilizzi futuri
            self._connection_string = self.db_path
            return conn
        else:
            # Default fallback
            conn = sqlite3.connect("db_memoria/metadata.sqlite")
            conn.row_factory = sqlite3.Row
            self._connection_string = "db_memoria/metadata.sqlite"
            return conn

    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Esegue query e restituisce risultati."""
        try:
            conn = self.get_connection()
            # If the repository was created with an external sqlite3.Connection,
            # do not close it here (it may be shared across callers/tests).
            close_conn = not isinstance(self.db_path, sqlite3.Connection)

            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if cursor.description:
                rows = cursor.fetchall()
                result = [dict(row) for row in rows]
            else:
                result = []

            if close_conn:
                conn.close()

            return result
        except Exception as e:
            self.logger.error(f"Errore esecuzione query: {e}")
            raise

    def execute_update(self, query: str, params: tuple = None) -> bool:
        """Esegue update e restituisce successo."""
        try:
            conn = self.get_connection()
            close_conn = not isinstance(self.db_path, sqlite3.Connection)

            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            conn.commit()

            if close_conn:
                conn.close()

            return True
        except Exception as e:
            self.logger.error(f"Errore esecuzione update: {e}")
            return False

    @abstractmethod
    def get_by_id(self, id: int) -> Optional[Any]:
        """Recupera entità per ID."""
        pass

    @abstractmethod
    def get_all(self, filters: Dict[str, Any] = None) -> List[Any]:
        """Recupera tutte le entità."""
        pass

    @abstractmethod
    def create(self, entity: Any) -> Any:
        """Crea nuova entità."""
        pass

    @abstractmethod
    def update(self, id: int, entity: Any) -> bool:
        """Aggiorna entità."""
        pass

    @abstractmethod
    def delete(self, id: int) -> bool:
        """Elimina entità."""
        pass
