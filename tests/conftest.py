"""
Configuration and fixtures for pytest.
Shared fixtures and utilities for all tests.
"""

import os
import tempfile
import shutil
import sqlite3
from typing import Generator, Dict, Any
from pathlib import Path

import pytest
import streamlit as st
from unittest.mock import Mock, MagicMock

# Test database paths
TEST_DB_DIR = Path(__file__).parent / "test_data"
TEST_DB_PATH = TEST_DB_DIR / "test_metadata.sqlite"
TEST_DB_BACKUP_PATH = TEST_DB_DIR / "test_metadata_backup.sqlite"

# Ensure test directories exist
TEST_DB_DIR.mkdir(exist_ok=True)

@pytest.fixture(scope="session")
def test_db_path() -> Path:
    """Path to test database."""
    return TEST_DB_PATH

@pytest.fixture(scope="session")
def test_backup_path() -> Path:
    """Path to test database backup."""
    return TEST_DB_BACKUP_PATH

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

@pytest.fixture
def sample_files_dir(temp_dir: Path) -> Path:
    """Directory with sample test files."""
    files_dir = temp_dir / "sample_files"
    files_dir.mkdir(exist_ok=True)

    # Create sample files
    sample_pdf = files_dir / "sample.pdf"
    sample_pdf.write_text("Sample PDF content")

    sample_txt = files_dir / "sample.txt"
    sample_txt.write_text("Sample text content")

    return files_dir

@pytest.fixture
def in_memory_db() -> Generator[sqlite3.Connection, None, None]:
    """In-memory SQLite database for fast testing."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    # Create basic tables for testing
    conn.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(100) UNIQUE NOT NULL,
            email VARCHAR(255),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name VARCHAR(255) UNIQUE NOT NULL,
            title VARCHAR(500),
            content_hash VARCHAR(64),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    yield conn
    conn.close()

@pytest.fixture
def mock_streamlit_session() -> Generator[Mock, None, None]:
    """Mock Streamlit session state."""
    mock_session = Mock()

    # Mock session state
    mock_session_state = {
        'user_id': 'test_user_123',
        'username': 'test_user',
        'initialized': True,
        'log_messages': []
    }

    def getitem(key: str) -> Any:
        return mock_session_state[key]

    def setitem(key: str, value: Any) -> None:
        mock_session_state[key] = value

    def contains(key: str) -> bool:
        return key in mock_session_state

    mock_session.__getitem__ = getitem
    mock_session.__setitem__ = setitem
    mock_session.__contains__ = contains

    with pytest.MonkeyPatch().context() as m:
        m.setattr(st, "session_state", mock_session)
        yield mock_session

@pytest.fixture
def mock_config() -> Dict[str, Any]:
    """Mock configuration for testing."""
    return {
        'database': {
            'url': 'sqlite:///test.db',
            'pool_size': 5,
            'timeout': 30
        },
        'ai': {
            'model_name': 'test-model',
            'temperature': 0.7,
            'max_tokens': 1000
        },
        'app': {
            'debug': True,
            'secret_key': 'test-secret-key'
        }
    }

@pytest.fixture
def mock_llm() -> Mock:
    """Mock LLM for testing AI functionality."""
    mock = Mock()
    mock.complete.return_value = "Mock AI response"
    mock.stream_complete.return_value = iter(["Mock", " AI", " response"])
    return mock

@pytest.fixture
def mock_document_repository() -> Mock:
    """Mock document repository."""
    mock = Mock()

    # Mock return values
    mock.get_by_id.return_value = {
        'id': 1,
        'file_name': 'test.pdf',
        'title': 'Test Document'
    }

    mock.get_all.return_value = [
        {'id': 1, 'file_name': 'test1.pdf', 'title': 'Test 1'},
        {'id': 2, 'file_name': 'test2.pdf', 'title': 'Test 2'}
    ]

    mock.create.return_value = {'id': 3, 'file_name': 'new.pdf'}
    mock.update.return_value = True
    mock.delete.return_value = True

    return mock

@pytest.fixture
def mock_user_repository() -> Mock:
    """Mock user repository."""
    mock = Mock()

    mock.get_by_id.return_value = {
        'id': 1,
        'username': 'testuser',
        'email': 'test@example.com'
    }

    mock.create.return_value = {'id': 2, 'username': 'newuser'}
    mock.authenticate.return_value = {'id': 1, 'username': 'testuser'}

    return mock

@pytest.fixture
def sample_document_data() -> Dict[str, Any]:
    """Sample document data for testing."""
    return {
        'file_name': 'test_document.pdf',
        'title': 'Test Document Title',
        'content': 'This is sample document content for testing purposes.',
        'category_id': 'TEST/CAT001',
        'authors': 'Test Author',
        'year': 2024
    }

@pytest.fixture
def sample_user_data() -> Dict[str, Any]:
    """Sample user data for testing."""
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'preferences': {
            'theme': 'dark',
            'language': 'it'
        }
    }

@pytest.fixture
def api_client() -> Mock:
    """Mock API client for external service testing."""
    mock = Mock()

    # Mock successful responses
    mock.post.return_value.status_code = 200
    mock.post.return_value.json.return_value = {'success': True}

    mock.get.return_value.status_code = 200
    mock.get.return_value.json.return_value = {'data': 'test'}

    return mock

@pytest.fixture(autouse=True)
def setup_test_environment() -> Generator[None, None]:
    """Setup automatico per tutti i test."""
    # Set environment variables for testing
    original_env = os.environ.copy()

    os.environ.update({
        'ENVIRONMENT': 'test',
        'DEBUG': 'true',
        'DATABASE_URL': 'sqlite:///:memory:',
        'AI_MODEL': 'test-model'
    })

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)

@pytest.fixture
def benchmark_data() -> Dict[str, Any]:
    """Data for performance benchmarking."""
    return {
        'documents': [
            {'id': i, 'content': f'Content {i}' * 100}
            for i in range(100)
        ],
        'queries': [
            'test query 1',
            'test query 2',
            'test query 3'
        ]
    }

# Utility functions for tests

def create_test_user(conn: sqlite3.Connection, username: str = "testuser") -> int:
    """Create a test user in the database."""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, email) VALUES (?, ?)",
        (username, f"{username}@example.com")
    )
    conn.commit()
    return cursor.lastrowid

def create_test_document(conn: sqlite3.Connection, file_name: str = "test.pdf") -> int:
    """Create a test document in the database."""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO documents (file_name, title) VALUES (?, ?)",
        (file_name, f"Test Document {file_name}")
    )
    conn.commit()
    return cursor.lastrowid

def assert_database_tables_exist(conn: sqlite3.Connection, tables: list[str]) -> None:
    """Assert that required tables exist in database."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name IN ({})".format(
            ','.join('?' * len(tables))
        ),
        tables
    )
    existing_tables = {row[0] for row in cursor.fetchall()}
    missing_tables = set(tables) - existing_tables
    assert not missing_tables, f"Missing tables: {missing_tables}"

# Performance testing utilities

@pytest.fixture
def performance_thresholds() -> Dict[str, float]:
    """Performance thresholds for benchmarking."""
    return {
        'database_query': 0.1,  # 100ms
        'document_processing': 2.0,  # 2 seconds
        'ai_response': 5.0,  # 5 seconds
        'ui_rendering': 0.5,  # 500ms
    }

def measure_execution_time(func: callable, *args, **kwargs) -> float:
    """Measure execution time of a function."""
    import time
    start = time.time()
    func(*args, **kwargs)
    return time.time() - start

# Test data factories

class TestDataFactory:
    """Factory for creating test data."""

    @staticmethod
    def create_document(overrides: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create document test data."""
        data = {
            'file_name': 'test_document.pdf',
            'title': 'Test Document',
            'content': 'Sample content',
            'category_id': 'TEST/001',
            'authors': 'Test Author',
            'year': 2024
        }
        if overrides:
            data.update(overrides)
        return data

    @staticmethod
    def create_user(overrides: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create user test data."""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'preferences': {'theme': 'light'}
        }
        if overrides:
            data.update(overrides)
        return data

    @staticmethod
    def create_course(overrides: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create course test data."""
        data = {
            'course_name': 'Test Course',
            'course_code': 'TC001',
            'description': 'Test course description'
        }
        if overrides:
            data.update(overrides)
        return data

# Pytest configuration

def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "database: mark test as database related"
    )
    config.addinivalue_line(
        "markers", "ai: mark test as AI/ML related"
    )
    config.addinivalue_line(
        "markers", "ui: mark test as UI related"
    )

def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add unit marker to tests in test_unit_*.py
        if "test_unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)

        # Add integration marker to tests in test_integration_*.py
        if "test_integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Add database marker to tests that use database fixtures
        if "database" in str(item.fixturenames):
            item.add_marker(pytest.mark.database)

        # Add slow marker to tests with 'slow' in name
        if "slow" in item.nodeid.lower():
            item.add_marker(pytest.mark.slow)
