"""
Service base per operazioni business.

Fornisce funzionalità comuni per tutti i servizi.
"""

import logging
from typing import Any, Dict, List, Optional, Type, TypeVar
from abc import ABC, abstractmethod

from ..database.models.base import DatabaseResponse, PaginationParams, PaginatedResponse
from ..database.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)

T = TypeVar('T')

class BaseService(ABC):
    """Service base astratto."""

    def __init__(self, repository: BaseRepository):
        """Inizializza service."""
        self.repository = repository
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def _create_response(self, success: bool, message: str, data: Any = None, error: str = None) -> DatabaseResponse:
        """Crea risposta standard."""
        return DatabaseResponse(
            success=success,
            message=message,
            data=data,
            error=error
        )

    def _handle_error(self, error: Exception, operation: str) -> DatabaseResponse:
        """Gestisce errori operazioni."""
        error_msg = f"Errore durante {operation}: {str(error)}"
        self.logger.error(error_msg, exc_info=True)
        return self._create_response(False, error_msg, error=error_msg)

    @abstractmethod
    def get_by_id(self, id: int) -> DatabaseResponse:
        """Recupera entità per ID."""
        pass

    @abstractmethod
    def get_all(self, filters: Dict[str, Any] = None) -> DatabaseResponse:
        """Recupera tutte le entità."""
        pass

    @abstractmethod
    def create(self, data: Any) -> DatabaseResponse:
        """Crea nuova entità."""
        pass

    @abstractmethod
    def update(self, id: int, data: Any) -> DatabaseResponse:
        """Aggiorna entità."""
        pass

    @abstractmethod
    def delete(self, id: int) -> DatabaseResponse:
        """Elimina entità."""
        pass
