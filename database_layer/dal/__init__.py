# Data Access Layer (DAL) - Fase 0
"""
Data Access Layer centralizzato per la preparazione alla transizione multi-progetto.

Questo modulo fornisce:
- Repository pattern per accesso dati strutturato
- Gestione errori centralizzata
- Logging strutturato operazioni database
- Foundation per supporto multi-progetto
"""

__version__ = "0.1.0"
__author__ = "Archivista AI - Fase 0"

from .base_repository import BaseRepository
from .document_repository import DocumentRepository
from .user_repository import UserRepository
from .project_repository import ProjectRepository

__all__ = [
    'BaseRepository',
    'DocumentRepository',
    'UserRepository',
    'ProjectRepository'
]
