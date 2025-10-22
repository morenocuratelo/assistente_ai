"""
Repository layer per gestione dati.

Fornisce accesso ai dati attraverso repository pattern.
"""

from .base_repository import BaseRepository
from .document_repository import DocumentRepository
from .user_repository import UserRepository
from .chat_repository import ChatRepository
from .project_repository import ProjectRepository
from .career_repository import CareerRepository

__all__ = [
    'BaseRepository',
    'DocumentRepository',
    'UserRepository',
    'ChatRepository',
    'ProjectRepository',
    'CareerRepository'
]
