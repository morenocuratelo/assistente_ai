"""
Script verifica rapida servizi Fase 2.

Test veloce per verificare che le implementazioni funzionino correttamente.
Può essere eseguito direttamente con Python per una verifica immediata.
"""

import sys
import os
import sqlite3
import traceback
from pathlib import Path

# Aggiungi src al path per import
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_imports():
    """Test importazioni servizi."""
    print("🔄 Test importazioni servizi...")

    try:
        from src.services.base_service import BaseService
        from src.services.document_service import DocumentService
        from src.services.user_service import UserService
        from src.services.chat_service import ChatService
        from src.database.models.base import BaseDBModel, DatabaseResponse
        from src.database.models.document import Document, DocumentCreate, DocumentUpdate
        from src.database.models.user import User, UserCreate, UserUpdate
        from src.database.models.chat import Chat, ChatCreate, ChatUpdate, Message, MessageCreate

        print("✅ Tutti gli import funzionano correttamente")
        return True

    except ImportError as e:
        print(f"❌ Errore importazione: {e}")
        return False
    except Exception as e:
        print(f"❌ Errore generico: {e}")
        return False

def test_database_connection():
    """Test connessione database."""
    print("🔄 Test connessione database...")

    try:
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row

        # Test query semplice
        cursor = conn.execute("SELECT 1 as test")
        result = cursor.fetchone()
        assert result['test'] == 1

        conn.close()
        print("✅ Connessione database funziona")
        return True

    except Exception as e:
        print(f"❌ Errore database: {e}")
        return False

def test_model_creation():
    """Test creazione modelli."""
    print("🔄 Test creazione modelli...")

    try:
        from src.database.models.document import DocumentCreate
        from src.database.models.user import UserCreate
        from src.database.models.chat import ChatCreate, MessageCreate

        # Test DocumentCreate
        doc_data = {
            "file_name": "test.pdf",
            "title": "Test Document",
            "authors": "Test Author",
            "publication_year": 2024,
            "category_id": "TEST/001"
        }
        doc_create = DocumentCreate(**doc_data)
        assert doc_create.file_name == "test.pdf"

        # Test UserCreate
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password_hash": "hash123",
            "first_name": "Test",
            "last_name": "User"
        }
        user_create = UserCreate(**user_data)
        assert user_create.username == "testuser"

        # Test ChatCreate
        chat_data = {
            "title": "Test Chat",
            "user_id": 1,
            "is_active": True
        }
        chat_create = ChatCreate(**chat_data)
        assert chat_create.title == "Test Chat"

        # Test MessageCreate
        message_data = {
            "chat_id": 1,
            "role": "user",
            "content": "Ciao",
            "timestamp": "2024-01-01T10:00:00Z",
            "metadata": "{}",
            "tokens": 1,
            "model": "test-model",
            "temperature": 0.7
        }
        message_create = MessageCreate(**message_data)
        assert message_create.role == "user"

        print("✅ Creazione modelli funziona")
        return True

    except Exception as e:
        print(f"❌ Errore creazione modelli: {e}")
        traceback.print_exc()
        return False

def test_repository_creation():
    """Test creazione repository."""
    print("🔄 Test creazione repository...")

    try:
        from src.database.repositories.document_repository import DocumentRepository
        from src.database.repositories.user_repository import UserRepository
        from src.database.repositories.chat_repository import ChatRepository

        # Test con database in memoria
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row

        # Crea repository
        doc_repo = DocumentRepository(conn)
        user_repo = UserRepository(conn)
        chat_repo = ChatRepository(conn)

        # Verifica inizializzazione
        assert doc_repo is not None
        assert user_repo is not None
        assert chat_repo is not None

        # Verifica creazione tabelle
        cursor = conn.cursor()

        # Controlla tabella papers
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='papers'")
        assert cursor.fetchone() is not None

        # Controlla tabella users
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        assert cursor.fetchone() is not None

        # Controlla tabella chats
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chats'")
        assert cursor.fetchone() is not None

        # Controlla tabella messages
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages'")
        assert cursor.fetchone() is not None

        conn.close()

        print("✅ Repository e tabelle create correttamente")
        return True

    except Exception as e:
        print(f"❌ Errore repository: {e}")
        traceback.print_exc()
        return False

def test_service_creation():
    """Test creazione servizi."""
    print("🔄 Test creazione servizi...")

    try:
        from src.services.document_service import DocumentService
        from src.services.user_service import UserService
        from src.services.chat_service import ChatService

        # Crea servizi con repository mock
        from unittest.mock import Mock

        mock_doc_repo = Mock()
        mock_user_repo = Mock()
        mock_chat_repo = Mock()

        doc_service = DocumentService(mock_doc_repo)
        user_service = UserService(mock_user_repo)
        chat_service = ChatService(mock_chat_repo)

        # Verifica inizializzazione
        assert doc_service is not None
        assert user_service is not None
        assert chat_service is not None

        # Verifica repository assegnati
        assert doc_service.repository is mock_doc_repo
        assert user_service.repository is mock_user_repo
        assert chat_service.repository is mock_chat_repo

        print("✅ Servizi creati correttamente")
        return True

    except Exception as e:
        print(f"❌ Errore servizi: {e}")
        traceback.print_exc()
        return False

def test_service_methods():
    """Test metodi servizi."""
    print("🔄 Test metodi servizi...")

    try:
        from src.services.document_service import DocumentService
        from unittest.mock import Mock

        # Crea servizio con mock
        mock_repo = Mock()
        doc_service = DocumentService(mock_repo)

        # Test metodi esistono
        required_methods = [
            'get_by_id', 'get_by_filename', 'get_all', 'get_all_as_dataframe',
            'create', 'update', 'update_metadata', 'delete', 'search_documents',
            'get_documents_by_category', 'get_recent_documents', 'get_document_stats',
            'bulk_update_documents'
        ]

        for method_name in required_methods:
            assert hasattr(doc_service, method_name), f"Metodo {method_name} mancante"
            method = getattr(doc_service, method_name)
            assert callable(method), f"{method_name} non è callable"

        # Test risposta standardizzata
        response = doc_service._create_response(True, "Test message", {"test": "data"})
        assert response.success is True
        assert response.message == "Test message"
        assert response.data == {"test": "data"}
        assert response.error is None

        # Test gestione errori
        error_response = doc_service._handle_error(Exception("Test error"), "test operation")
        assert error_response.success is False
        assert "Test error" in error_response.error

        print("✅ Metodi servizi funzionano")
        return True

    except Exception as e:
        print(f"❌ Errore metodi servizi: {e}")
        traceback.print_exc()
        return False

def test_full_integration():
    """Test integrazione completa."""
    print("🔄 Test integrazione completa...")

    try:
        # Crea database con tutte le tabelle
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row

        # Crea tabelle
        conn.execute("""
            CREATE TABLE papers (
                file_name TEXT PRIMARY KEY, title TEXT, authors TEXT,
                publication_year INTEGER, category_id TEXT, category_name TEXT,
                formatted_preview TEXT, processed_at TEXT, file_size INTEGER,
                mime_type TEXT, keywords TEXT, ai_tasks TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
                first_name TEXT, last_name TEXT, is_active BOOLEAN DEFAULT 1,
                is_admin BOOLEAN DEFAULT 0, created_at TEXT NOT NULL,
                updated_at TEXT, last_login TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
                user_id INTEGER, is_active BOOLEAN DEFAULT 1,
                created_at TEXT NOT NULL, updated_at TEXT, metadata TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER NOT NULL,
                role TEXT NOT NULL, content TEXT NOT NULL, timestamp TEXT NOT NULL,
                metadata TEXT, tokens INTEGER, model TEXT, temperature REAL,
                created_at TEXT NOT NULL, FOREIGN KEY (chat_id) REFERENCES chats (id)
            )
        """)

        conn.commit()

        # Crea servizi reali
        from src.services.document_service import DocumentService
        from src.services.user_service import UserService
        from src.services.chat_service import ChatService
        from src.database.repositories.document_repository import DocumentRepository
        from src.database.repositories.user_repository import UserRepository
        from src.database.repositories.chat_repository import ChatRepository

        doc_repo = DocumentRepository(conn)
        user_repo = UserRepository(conn)
        chat_repo = ChatRepository(conn)

        doc_service = DocumentService(doc_repo)
        user_service = UserService(user_repo)
        chat_service = ChatService(chat_repo)

        # Test operazioni base
        # 1. Crea utente
        user_data = {
            "username": "integration_user",
            "email": "integration@example.com",
            "password_hash": "integration_hash",
            "first_name": "Integration",
            "last_name": "User"
        }

        user_result = user_service.create(user_data)
        assert user_result.success is True
        user_id = user_result.data['id']

        # 2. Crea documento
        doc_data = {
            "file_name": "integration_test.pdf",
            "title": "Integration Test Document",
            "authors": "Integration Author",
            "publication_year": 2024,
            "category_id": "INTEGRATION/TEST"
        }

        doc_result = doc_service.create(doc_data)
        assert doc_result.success is True

        # 3. Crea chat
        chat_data = {
            "title": "Integration Chat",
            "user_id": user_id,
            "is_active": True
        }

        chat_result = chat_service.create(chat_data)
        assert chat_result.success is True
        chat_id = chat_result.data['id']

        # 4. Aggiungi messaggio
        message_data = {
            "chat_id": chat_id,
            "role": "user",
            "content": "Questo è un test di integrazione",
            "timestamp": "2024-01-01T10:00:00Z",
            "metadata": '{"type": "text"}',
            "tokens": 8,
            "model": "integration-model",
            "temperature": 0.7
        }

        message_result = chat_service.add_message(chat_id, message_data)
        assert message_result.success is True

        # 5. Verifica relazioni
        # Recupera chat utente
        user_chats = chat_service.get_chats_by_user(user_id)
        assert user_chats.success is True
        assert len(user_chats.data) == 1

        # Recupera documento
        get_doc = doc_service.get_by_filename("integration_test.pdf")
        assert get_doc.success is True

        # Recupera chat con messaggi
        chat_with_messages = chat_service.get_chat_with_messages(chat_id)
        assert chat_with_messages.success is True
        assert len(chat_with_messages.data['messages']) == 1

        conn.close()

        print("✅ Integrazione completa funziona perfettamente")
        return True

    except Exception as e:
        print(f"❌ Errore integrazione: {e}")
        traceback.print_exc()
        return False

def main():
    """Funzione principale test."""
    print("🚀 Inizio verifica implementazioni Fase 2")
    print("=" * 50)

    tests = [
        ("Importazioni", test_imports),
        ("Database", test_database_connection),
        ("Modelli", test_model_creation),
        ("Repository", test_repository_creation),
        ("Servizi", test_service_creation),
        ("Metodi servizi", test_service_methods),
        ("Integrazione completa", test_full_integration)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n{'=' * 20}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSATO")
            else:
                print(f"❌ {test_name}: FALLITO")
        except Exception as e:
            print(f"❌ {test_name}: ERRORE - {e}")
        print(f"{'=' * 20}")

    print(f"\n{'=' * 50}")
    print(f"📊 Risultati: {passed}/{total} test passati")

    if passed == total:
        print("🎉 Tutte le implementazioni della Fase 2 funzionano correttamente!")
        print("✅ Pronto per procedere con Fase 3 - UI Components")
        return True
    else:
        print("⚠️  Alcuni test sono falliti. Verificare implementazioni.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
