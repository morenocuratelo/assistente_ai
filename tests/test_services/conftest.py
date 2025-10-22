"""
Fixture specifiche per test servizi.

Estende le fixture comuni con fixture specifiche per i servizi implementati.
"""

import pytest
import unittest
import sqlite3
from unittest.mock import Mock
from pathlib import Path

from src.services.document_service import DocumentService
from src.services.user_service import UserService
from src.services.chat_service import ChatService
from src.database.repositories.document_repository import DocumentRepository
from src.database.repositories.user_repository import UserRepository
from src.database.repositories.chat_repository import ChatRepository

@pytest.fixture
def test_db_for_services():
    """Database di test per servizi."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    # Crea tabelle necessarie
    conn.execute("""
        CREATE TABLE papers (
            file_name TEXT PRIMARY KEY,
            title TEXT,
            authors TEXT,
            publication_year INTEGER,
            category_id TEXT,
            category_name TEXT,
            formatted_preview TEXT,
            processed_at TEXT,
            file_size INTEGER,
            mime_type TEXT,
            keywords TEXT,
            ai_tasks TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT,
            is_active BOOLEAN DEFAULT 1,
            is_admin BOOLEAN DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            last_login TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            user_id INTEGER,
            is_active BOOLEAN DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            metadata TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            metadata TEXT,
            tokens INTEGER,
            model TEXT,
            temperature REAL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (chat_id) REFERENCES chats (id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    return conn

@pytest.fixture
def document_repository(test_db_for_services):
    """Repository documenti per test."""
    return DocumentRepository(test_db_for_services)

# Compatibility shim: some tests use pytest.mock.patch; provide alias to unittest.mock
pytest.mock = unittest.mock

@pytest.fixture
def user_repository(test_db_for_services):
    """Repository utenti per test."""
    return UserRepository(test_db_for_services)

@pytest.fixture
def chat_repository(test_db_for_services):
    """Repository chat per test."""
    return ChatRepository(test_db_for_services)

@pytest.fixture
def document_service(request, document_repository):
    """Service documenti per test.

    If test is marked as 'unit', use a Mock repository so tests can set return_value/side_effect on methods.
    """
    # If running a unit test, provide a mock repository
    if request.node.get_closest_marker('unit') is not None:
        mock_repo = Mock(spec=type(document_repository))
        # Default mock behaviors
        mock_repo.get_by_filename.return_value = None
        mock_repo.get_all.return_value = []
        mock_repo.create.return_value = None
        mock_repo.update.return_value = False
        mock_repo.delete.return_value = False
        mock_repo.search_documents.return_value = []
        mock_repo.get_documents_by_category.return_value = []
        mock_repo.get_recent_documents.return_value = []
        mock_repo.get_all_documents.return_value = None
        return DocumentService(mock_repo)

    # Integration-style: use real repository
    return DocumentService(document_repository)

@pytest.fixture
def user_service(user_repository):
    """Service utenti per test."""
    return UserService(user_repository)

@pytest.fixture
def chat_service(chat_repository):
    """Service chat per test."""
    return ChatService(chat_repository)

@pytest.fixture
def mock_document_repository():
    """Mock document repository."""
    mock = Mock(spec=DocumentRepository)

    # Mock metodi principali
    mock.get_by_filename.return_value = None
    mock.get_all.return_value = []
    mock.create.return_value = None
    mock.update.return_value = False
    mock.delete.return_value = False
    mock.search_documents.return_value = []
    mock.get_documents_by_category.return_value = []
    mock.get_recent_documents.return_value = []

    return mock

@pytest.fixture
def mock_user_repository():
    """Mock user repository."""
    mock = Mock(spec=UserRepository)

    mock.get_by_id.return_value = None
    mock.get_by_username.return_value = None
    mock.get_by_email.return_value = None
    mock.get_all.return_value = []
    mock.create.return_value = None
    mock.update.return_value = False
    mock.delete.return_value = False
    mock.authenticate_user.return_value = None

    return mock

@pytest.fixture
def mock_chat_repository():
    """Mock chat repository."""
    mock = Mock(spec=ChatRepository)

    mock.get_by_id.return_value = None
    mock.get_all.return_value = []
    mock.create.return_value = None
    mock.update.return_value = False
    mock.delete.return_value = False
    mock.get_chats_by_user.return_value = []
    mock.get_recent_chats.return_value = []
    mock.add_message.return_value = None
    mock.get_messages_by_chat_id.return_value = []

    return mock

@pytest.fixture
def sample_document_data():
    """Dati documento di test."""
    return {
        "file_name": "test_document.pdf",
        "title": "Test Document Title",
        "authors": "Test Author",
        "publication_year": 2024,
        "category_id": "TEST/001",
        "category_name": "Test Category",
        "formatted_preview": "Test preview content",
        "file_size": 1024,
        "mime_type": "application/pdf",
        # keywords as list and ai_tasks as dict to match pydantic models
        "keywords": ["test", "document"],
        "ai_tasks": {"summarize": True, "analyze": True}
    }

@pytest.fixture
def sample_user_data():
    """Dati utente di test."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "User",
        "is_active": True,
        "is_admin": False
    }

@pytest.fixture
def sample_chat_data():
    """Dati chat di test."""
    return {
        "title": "Test Chat",
        "user_id": 1,
        "is_active": True,
        "metadata": '{"topic": "test"}'
    }

@pytest.fixture
def sample_message_data():
    """Dati messaggio di test."""
    return {
        "role": "user",
        "content": "Ciao, come stai?",
        "timestamp": "2024-01-01T10:00:00Z",
        "metadata": '{"type": "text"}',
        "tokens": 5,
        "model": "gpt-3.5-turbo",
        "temperature": 0.7
    }

@pytest.fixture
def mock_document_service(mock_document_repository):
    """Mock document service."""
    return DocumentService(mock_document_repository)

@pytest.fixture
def mock_user_service(mock_user_repository):
    """Mock user service."""
    return UserService(mock_user_repository)

@pytest.fixture
def mock_chat_service(mock_chat_repository):
    """Mock chat service."""
    return ChatService(mock_chat_repository)

# Utility per creare dati di test nel database

def create_test_document_in_db(repository, data=None):
    """Crea documento di test nel database."""
    if data is None:
        data = {
            "file_name": "test.pdf",
            "title": "Test Document",
            "authors": "Test Author",
            "publication_year": 2024,
            "category_id": "TEST/001"
        }

    try:
        doc_create = type('DocumentCreate', (), data)()
        return repository.create(doc_create)
    except Exception:
        return None

def create_test_user_in_db(repository, data=None):
    """Crea utente di test nel database."""
    if data is None:
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password_hash": "hashed_password",
            "first_name": "Test",
            "last_name": "User"
        }

    try:
        user_create = type('UserCreate', (), data)()
        return repository.create(user_create)
    except Exception:
        return None

def create_test_chat_in_db(repository, data=None):
    """Crea chat di test nel database."""
    if data is None:
        data = {
            "title": "Test Chat",
            "user_id": 1,
            "is_active": True
        }

    try:
        chat_create = type('ChatCreate', (), data)()
        return repository.create(chat_create)
    except Exception:
        return None
