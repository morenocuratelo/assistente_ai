"""
Modelli database.

Esporta tutti i modelli Pydantic per il sistema.
"""

from .base import (
    BaseDBModel,
    DatabaseResponse,
    PaginationParams,
    PaginatedResponse
)
from .document import (
    Document,
    DocumentCreate,
    DocumentUpdate
)
from .user import (
    User,
    UserCreate,
    UserUpdate
)
from .chat import (
    Chat,
    ChatCreate,
    ChatUpdate,
    Message,
    MessageCreate,
    MessageUpdate,
    # Legacy models
    ChatSession,
    ChatMessage,
    ChatSessionCreate,
    ChatMessageCreate
)

__all__ = [
    # Base models
    'BaseDBModel',
    'DatabaseResponse',
    'PaginationParams',
    'PaginatedResponse',

    # Document models
    'Document',
    'DocumentCreate',
    'DocumentUpdate',

    # User models
    'User',
    'UserCreate',
    'UserUpdate',

    # Chat models
    'Chat',
    'ChatCreate',
    'ChatUpdate',
    'Message',
    'MessageCreate',
    'MessageUpdate',

    # Legacy chat models
    'ChatSession',
    'ChatMessage',
    'ChatSessionCreate',
    'ChatMessageCreate'
]
