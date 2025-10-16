"""
Unit tests for core functionality.
Tests for basic core modules and utilities.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sqlite3
from pathlib import Path

from tests.conftest import TestDataFactory


class TestDocumentProcessor:
    """Test cases for document processing functionality."""

    def setup_method(self) -> None:
        """Setup for each test method."""
        self.mock_config = Mock()
        self.mock_config.database.url = "sqlite:///test.db"
        self.mock_config.ai.model_name = "test-model"

    @pytest.mark.unit
    def test_document_processor_initialization(self, mock_config: Mock) -> None:
        """Test DocumentProcessor initialization."""
        from src.core.utils.validation import DocumentProcessor

        processor = DocumentProcessor(mock_config)

        assert processor.config == mock_config
        assert hasattr(processor, '_dependencies')

    @pytest.mark.unit
    def test_process_document_success(self, mock_config: Mock, sample_document_data: dict) -> None:
        """Test successful document processing."""
        from src.core.utils.validation import DocumentProcessor

        processor = DocumentProcessor(mock_config)

        # Mock the actual processing
        with patch.object(processor, '_process_single_document') as mock_process:
            mock_process.return_value = {'success': True, 'id': 'doc_123'}

            result = processor.process_document("test.pdf")

            assert result['success'] is True
            assert result['id'] == 'doc_123'
            mock_process.assert_called_once_with("test.pdf")

    @pytest.mark.unit
    def test_process_document_file_not_found(self, mock_config: Mock) -> None:
        """Test document processing with non-existent file."""
        from src.core.utils.validation import DocumentProcessor

        processor = DocumentProcessor(mock_config)

        with patch.object(processor, '_process_single_document') as mock_process:
            from src.core.exceptions import DocumentProcessingError
            mock_process.side_effect = DocumentProcessingError(
                "File not found", "test.pdf"
            )

            with pytest.raises(DocumentProcessingError) as exc_info:
                processor.process_document("nonexistent.pdf")

            assert "File not found" in str(exc_info.value)

    @pytest.mark.unit
    def test_batch_processing(self, mock_config: Mock) -> None:
        """Test batch document processing."""
        from src.core.utils.validation import DocumentProcessor

        processor = DocumentProcessor(mock_config)

        file_paths = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]

        with patch.object(processor, '_process_single_document') as mock_process:
            mock_process.side_effect = [
                {'success': True, 'id': 'doc_1'},
                {'success': True, 'id': 'doc_2'},
                {'success': False, 'id': None, 'error': 'Processing failed'}
            ]

            results = list(processor.process_documents_batch(file_paths))

            assert len(results) == 3
            assert results[0]['success'] is True
            assert results[1]['success'] is True
            assert results[2]['success'] is False
            assert mock_process.call_count == 3


class TestErrorHandler:
    """Test cases for error handling."""

    def setup_method(self) -> None:
        """Setup for each test method."""
        self.error_handler = Mock()

    @pytest.mark.unit
    def test_handle_database_error(self) -> None:
        """Test handling of database errors."""
        from src.core.errors.error_handler import ErrorHandler
        from src.core.errors.error_types import DatabaseError

        handler = ErrorHandler()

        db_error = DatabaseError("Connection failed", "SELECT * FROM users")

        result = handler.handle_error(db_error, {"user_id": "123"})

        assert result.category == "database"
        assert result.severity in ["high", "critical"]
        assert "Connection failed" in result.message

    @pytest.mark.unit
    def test_handle_validation_error(self) -> None:
        """Test handling of validation errors."""
        from src.core.errors.error_handler import ErrorHandler
        from src.core.errors.error_types import ValidationError

        handler = ErrorHandler()

        validation_error = ValidationError("Invalid input", "file_name")

        result = handler.handle_error(validation_error, {"user_id": "123"})

        assert result.category == "validation"
        assert result.severity == "medium"

    @pytest.mark.unit
    def test_error_logging(self) -> None:
        """Test error logging functionality."""
        from src.core.errors.error_handler import ErrorHandler
        from src.core.errors.error_types import ArchivistaError

        handler = ErrorHandler()

        error = ArchivistaError(
            "Test error",
            "TEST_ERROR",
            {"user_id": "123", "operation": "test"}
        )

        # Should not raise exception
        handler.log_error(error)


class TestConfigurationManager:
    """Test cases for configuration management."""

    @pytest.mark.unit
    def test_config_loading(self, mock_config: dict) -> None:
        """Test configuration loading."""
        from src.config.settings import ConfigurationManager

        with patch('src.config.settings.load_config_from_file') as mock_load:
            mock_load.return_value = mock_config

            manager = ConfigurationManager()
            config = manager.get_config()

            assert config.database.url == "sqlite:///test.db"
            assert config.ai.model_name == "test-model"

    @pytest.mark.unit
    def test_config_validation(self) -> None:
        """Test configuration validation."""
        from src.config.validation import ConfigValidator

        valid_config = {
            'database': {'url': 'sqlite:///test.db'},
            'ai': {'model_name': 'test-model'}
        }

        validator = ConfigValidator()
        errors = validator.validate_config(valid_config)

        assert len(errors) == 0

    @pytest.mark.unit
    def test_config_validation_errors(self) -> None:
        """Test configuration validation with errors."""
        from src.config.validation import ConfigValidator

        invalid_config = {
            'database': {},  # Missing required fields
            'ai': {'model_name': ''}  # Empty required field
        }

        validator = ConfigValidator()
        errors = validator.validate_config(invalid_config)

        assert len(errors) > 0
        assert any('database' in error.lower() for error in errors)


class TestEventBus:
    """Test cases for event bus functionality."""

    def setup_method(self) -> None:
        """Setup for each test method."""
        from src.core.events.event_bus import EventBus
        self.event_bus = EventBus()

    @pytest.mark.unit
    def test_event_publishing(self) -> None:
        """Test event publishing."""
        published_events = []

        def test_handler(event):
            published_events.append(event)

        # Subscribe to test event
        self.event_bus.subscribe("test_event", test_handler)

        # Publish event
        test_event = {
            'event_id': '123',
            'event_type': 'test_event',
            'data': {'key': 'value'}
        }

        self.event_bus.publish(test_event)

        assert len(published_events) == 1
        assert published_events[0]['data']['key'] == 'value'

    @pytest.mark.unit
    def test_multiple_subscribers(self) -> None:
        """Test multiple subscribers for same event."""
        received_events = []

        def handler1(event):
            received_events.append(('handler1', event))

        def handler2(event):
            received_events.append(('handler2', event))

        self.event_bus.subscribe("test_event", handler1)
        self.event_bus.subscribe("test_event", handler2)

        test_event = {
            'event_id': '123',
            'event_type': 'test_event',
            'data': {'test': True}
        }

        self.event_bus.publish(test_event)

        assert len(received_events) == 2
        assert ('handler1', test_event) in received_events
        assert ('handler2', test_event) in received_events


class TestRepositoryPattern:
    """Test cases for repository pattern implementation."""

    @pytest.mark.unit
    def test_document_repository_crud(self, in_memory_db: sqlite3.Connection) -> None:
        """Test CRUD operations on document repository."""
        from src.database.repositories.document_repository import DocumentRepository

        repo = DocumentRepository(in_memory_db)

        # Test Create
        document = TestDataFactory.create_document()
        created = repo.create(document)

        assert created['id'] is not None
        assert created['file_name'] == document['file_name']

        # Test Read
        retrieved = repo.get_by_id(created['id'])
        assert retrieved is not None
        assert retrieved['file_name'] == document['file_name']

        # Test Update
        updated = repo.update(created['id'], {'title': 'Updated Title'})
        assert updated is True

        retrieved = repo.get_by_id(created['id'])
        assert retrieved['title'] == 'Updated Title'

        # Test Delete
        deleted = repo.delete(created['id'])
        assert deleted is True

        retrieved = repo.get_by_id(created['id'])
        assert retrieved is None

    @pytest.mark.unit
    def test_user_repository_authentication(self, in_memory_db: sqlite3.Connection) -> None:
        """Test user authentication functionality."""
        from src.database.repositories.user_repository import UserRepository

        repo = UserRepository(in_memory_db)

        # Create test user
        user_data = TestDataFactory.create_user()
        user = repo.create(user_data)

        # Test authentication
        auth_result = repo.authenticate(user['username'], 'password123')

        # Note: This would need proper password hashing in real implementation
        assert auth_result is not None


class TestValidationUtils:
    """Test cases for validation utilities."""

    @pytest.mark.unit
    def test_email_validation(self) -> None:
        """Test email validation."""
        from src.core.utils.validation import validate_email

        # Valid emails
        assert validate_email("test@example.com") is True
        assert validate_email("user.name+tag@domain.co.uk") is True

        # Invalid emails
        assert validate_email("invalid-email") is False
        assert validate_email("@domain.com") is False
        assert validate_email("user@") is False

    @pytest.mark.unit
    def test_file_path_validation(self) -> None:
        """Test file path validation."""
        from src.core.utils.validation import validate_file_path

        # Valid paths
        assert validate_file_path("document.pdf") is True
        assert validate_file_path("folder/document.pdf") is True

        # Invalid paths (security risks)
        assert validate_file_path("../etc/passwd") is False
        assert validate_file_path("../../../sensitive") is False
        assert validate_file_path("C:\\Windows\\System32") is False

    @pytest.mark.unit
    def test_input_sanitization(self) -> None:
        """Test input sanitization."""
        from src.core.utils.validation import sanitize_input

        # Normal input
        assert sanitize_input("Normal text") == "Normal text"

        # Input with potential XSS
        assert "<script>" not in sanitize_input("<script>alert('xss')</script>")
        assert "javascript:" not in sanitize_input("javascript:alert('xss')")


class TestLoggingUtils:
    """Test cases for logging utilities."""

    @pytest.mark.unit
    def test_structured_logging(self) -> None:
        """Test structured logging functionality."""
        from src.core.utils.logging import get_logger

        logger = get_logger("test_module")

        with patch('src.core.utils.logging.logger') as mock_logger:
            logger.info("Test message", extra={"user_id": "123", "action": "test"})

            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args

            # Check that extra data is included
            assert 'user_id' in str(call_args)
            assert 'action' in str(call_args)

    @pytest.mark.unit
    def test_performance_logging(self) -> None:
        """Test performance logging."""
        from src.core.utils.logging import log_performance

        with patch('src.core.utils.logging.get_logger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            @log_performance("test_operation")
            def test_function():
                return "result"

            result = test_function()

            assert result == "result"
            mock_logger.info.assert_called_once()

            # Check performance data in log call
            call_args = mock_logger.info.call_args[1]  # kwargs
            assert 'duration_ms' in call_args


class TestAsyncUtils:
    """Test cases for async utilities."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_async_context_manager(self) -> None:
        """Test async context manager."""
        from src.core.utils.async_utils import AsyncDatabaseConnection

        # This would test the actual async context manager
        # For now, just test that it can be imported and initialized
        pass

    @pytest.mark.unit
    def test_async_helpers(self) -> None:
        """Test async helper functions."""
        import asyncio
        from src.core.utils.async_utils import run_async

        async def async_function():
            await asyncio.sleep(0.01)
            return "async_result"

        # Test running async function in sync context
        result = run_async(async_function())
        assert result == "async_result"


class TestSecurityUtils:
    """Test cases for security utilities."""

    @pytest.mark.unit
    def test_password_hashing(self) -> None:
        """Test password hashing functionality."""
        from src.core.utils.security import hash_password, verify_password

        password = "test_password_123"

        # Hash password
        hashed = hash_password(password)
        assert hashed != password
        assert len(hashed) > 20  # Should be reasonably long

        # Verify password
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False

    @pytest.mark.unit
    def test_token_generation(self) -> None:
        """Test token generation for authentication."""
        from src.core.utils.security import generate_token, verify_token

        user_id = "user_123"
        token = generate_token(user_id)

        assert token is not None
        assert len(token) > 10

        # Verify token
        verified_user_id = verify_token(token)
        assert verified_user_id == user_id

    @pytest.mark.unit
    def test_data_encryption(self) -> None:
        """Test data encryption utilities."""
        from src.core.utils.security import encrypt_data, decrypt_data

        sensitive_data = "This is sensitive information"
        key = "test_encryption_key_123"

        # Encrypt data
        encrypted = encrypt_data(sensitive_data, key)
        assert encrypted != sensitive_data

        # Decrypt data
        decrypted = decrypt_data(encrypted, key)
        assert decrypted == sensitive_data


class TestMetricsCollection:
    """Test cases for metrics collection."""

    @pytest.mark.unit
    def test_metrics_recording(self) -> None:
        """Test metrics recording functionality."""
        from src.core.utils.metrics import MetricsCollector

        collector = MetricsCollector()

        # Record some metrics
        collector.record_counter("documents_processed", 1, {"type": "pdf"})
        collector.record_histogram("processing_time", 1.5, {"operation": "ocr"})
        collector.record_gauge("active_users", 42)

        # Retrieve metrics
        counter_value = collector.get_counter("documents_processed")
        histogram_stats = collector.get_histogram_stats("processing_time")
        gauge_value = collector.get_gauge("active_users")

        assert counter_value > 0
        assert histogram_stats['count'] > 0
        assert gauge_value == 42

    @pytest.mark.unit
    def test_performance_monitoring(self) -> None:
        """Test performance monitoring."""
        from src.core.utils.metrics import PerformanceMonitor

        monitor = PerformanceMonitor()

        @monitor.measure("test_function")
        def test_function():
            return "result"

        result = test_function()

        assert result == "result"

        # Check that timing was recorded
        timing = monitor.get_timing("test_function")
        assert timing is not None
        assert timing['count'] >= 1


# Integration-style tests for core functionality

class TestCoreIntegration:
    """Integration tests for core modules."""

    @pytest.mark.integration
    def test_database_connection_management(self, in_memory_db: sqlite3.Connection) -> None:
        """Test database connection management."""
        from src.database.connection import ConnectionManager

        manager = ConnectionManager("sqlite:///:memory:")

        # Test connection acquisition
        conn = manager.get_connection()
        assert conn is not None

        # Test connection usage
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1

        # Test connection release
        manager.release_connection(conn)

    @pytest.mark.integration
    def test_service_container_dependency_injection(self) -> None:
        """Test dependency injection with service container."""
        from src.core.di.container import ServiceContainer

        container = ServiceContainer()

        # Register services
        mock_service = Mock()
        container.register_singleton("test_service", mock_service)

        # Resolve service
        resolved = container.resolve("test_service")
        assert resolved is mock_service

        # Test service usage
        resolved.test_method()
        mock_service.test_method.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
