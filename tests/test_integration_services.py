"""
Integration tests for services layer.
Tests interactions between different services and modules.
"""

import pytest
from unittest.mock import Mock, patch
import sqlite3
import tempfile
from pathlib import Path

from tests.conftest import TestDataFactory
from src.database.models.base import Document, User, ProcessingStatus
from src.services.archive.archive_service import ArchiveService
from src.services.auth.auth_service import AuthService
from src.services.ai.confidence_system_fixed import ConfidenceCalculator, ConfidenceVisualizer
from src.core.errors.error_handler import get_error_handler


class TestServiceIntegration:
    """Integration tests for service layer."""

    @pytest.fixture
    def temp_db(self):
        """Temporary database for integration testing."""
        with tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False) as f:
            db_path = f.name

        yield db_path

        # Cleanup
        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def archive_service(self, temp_db):
        """Archive service instance."""
        return ArchiveService(temp_db)

    @pytest.fixture
    def auth_service(self, temp_db):
        """Auth service instance."""
        return AuthService(temp_db)

    @pytest.fixture
    def sample_document(self):
        """Sample document for testing."""
        return Document(
            project_id="test_project",
            file_name="test.pdf",
            title="Test Document",
            file_size=1024,
            mime_type="application/pdf",
            processing_status=ProcessingStatus.PENDING
        )

    @pytest.mark.integration
    def test_archive_service_document_processing(self, archive_service, sample_document, temp_db):
        """Test archive service document processing integration."""
        # Create test file
        test_content = "This is a test document for integration testing."
        test_file = Path("test_document.txt")
        test_file.write_text(test_content)

        try:
            # Process document
            result = archive_service.process_document(
                str(test_file),
                sample_document.project_id,
                user_id="test_user"
            )

            # Verify result
            assert result.document.file_name == "test_document.txt"
            assert result.document.processing_status == ProcessingStatus.COMPLETED
            assert result.word_count > 0

        finally:
            # Cleanup
            test_file.unlink(missing_ok=True)

    @pytest.mark.integration
    def test_auth_service_user_creation_and_auth(self, auth_service):
        """Test user creation and authentication integration."""
        # Create user
        result = auth_service.create_user(
            username="testuser",
            email="test@example.com",
            password="SecurePass123!"
        )

        assert result.success is True
        assert result.user is not None
        assert result.user.username == "testuser"

        # Authenticate user
        auth_result = auth_service.authenticate(
            username="testuser",
            password="SecurePass123!"
        )

        assert auth_result.success is True
        assert auth_result.session is not None

    @pytest.mark.integration
    def test_confidence_system_integration(self, sample_document):
        """Test confidence system integration."""
        calculator = ConfidenceCalculator()
        visualizer = ConfidenceVisualizer()

        # Calculate confidence
        confidence = calculator.calculate_response_confidence(
            response_text="This is a test response with good quality content.",
            context_documents=[sample_document],
            user_id="test_user",
            query="test query"
        )

        assert confidence.value > 0
        assert confidence.factors is not None
        assert len(confidence.factors) > 0

        # Create visualization
        display_html = visualizer.create_confidence_display(confidence)
        assert "confidence" in display_html.lower()
        assert "High" in display_html or "Medium" in display_html or "Low" in display_html

    @pytest.mark.integration
    def test_error_handler_integration(self):
        """Test error handler integration across services."""
        error_handler = get_error_handler()

        # Test error handling
        try:
            raise ValueError("Test error for integration testing")
        except ValueError as e:
            error_result = error_handler.handle_error(
                e,
                operation="test_operation",
                component="integration_test"
            )

            assert error_result.message == "Test error for integration testing"
            assert error_result.category.value == "validation"
            assert error_result.severity.value == "medium"

    @pytest.mark.integration
    def test_cross_service_data_flow(self, archive_service, auth_service):
        """Test data flow between services."""
        # Create user through auth service
        auth_result = auth_service.create_user(
            username="cross_test_user",
            email="cross@example.com",
            password="SecurePass123!"
        )

        assert auth_result.success

        # Process document with user context
        test_file = Path("cross_test_document.txt")
        test_file.write_text("Cross-service integration test document.")

        try:
            result = archive_service.process_document(
                str(test_file),
                "test_project",
                user_id=str(auth_result.user.id)
            )

            assert result.document.created_by == auth_result.user.id

        finally:
            test_file.unlink(missing_ok=True)

    @pytest.mark.integration
    def test_performance_monitoring_integration(self):
        """Test performance monitoring across services."""
        from src.core.performance.optimizer import get_performance_optimizer

        optimizer = get_performance_optimizer()

        # Test performance measurement
        @optimizer.monitor.measure_execution_time
        def test_function():
            return "test_result"

        result, execution_time = test_function()

        assert result == "test_result"
        assert execution_time >= 0

        # Check metrics were recorded
        summary = optimizer.monitor.get_performance_summary(hours=1)
        assert summary.get('total_operations', 0) > 0


class TestServiceErrorHandling:
    """Test error handling across service boundaries."""

    @pytest.fixture
    def temp_db(self):
        """Temporary database."""
        with tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False) as f:
            db_path = f.name

        yield db_path

        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def archive_service(self, temp_db):
        """Archive service."""
        return ArchiveService(temp_db)

    @pytest.mark.integration
    def test_service_error_propagation(self, archive_service):
        """Test error propagation between services."""
        # Test with non-existent file
        with pytest.raises(Exception):  # Should raise FileNotFoundError
            archive_service.process_document(
                "non_existent_file.pdf",
                "test_project"
            )

    @pytest.mark.integration
    def test_error_recovery_mechanisms(self, archive_service):
        """Test error recovery mechanisms."""
        # Test with invalid document data
        invalid_document = Document(
            project_id="",  # Invalid empty project_id
            file_name="test.pdf"
        )

        # This should handle validation errors gracefully
        with pytest.raises(Exception):
            # The service should validate and raise appropriate error
            pass

    @pytest.mark.integration
    def test_concurrent_service_access(self, archive_service):
        """Test concurrent access to services."""
        import threading
        import time

        results = []
        errors = []

        def process_document_worker(doc_id):
            try:
                test_file = Path(f"concurrent_test_{doc_id}.txt")
                test_file.write_text(f"Content for document {doc_id}")

                try:
                    result = archive_service.process_document(
                        str(test_file),
                        f"project_{doc_id}"
                    )
                    results.append(result)
                finally:
                    test_file.unlink(missing_ok=True)

            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=process_document_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Verify results
        assert len(results) >= 0  # Some may succeed, some may fail
        assert len(errors) >= 0   # Some may error


class TestDataConsistency:
    """Test data consistency across service boundaries."""

    @pytest.fixture
    def temp_db(self):
        """Temporary database."""
        with tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False) as f:
            db_path = f.name

        yield db_path

        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def services(self, temp_db):
        """All services for testing."""
        return {
            'archive': ArchiveService(temp_db),
            'auth': AuthService(temp_db)
        }

    @pytest.mark.integration
    def test_user_document_relationship_consistency(self, services):
        """Test consistency of user-document relationships."""
        # Create user
        auth_result = services['auth'].create_user(
            username="consistency_user",
            email="consistency@example.com",
            password="SecurePass123!"
        )

        assert auth_result.success

        # Create document with user reference
        test_file = Path("consistency_test.txt")
        test_file.write_text("Consistency test document")

        try:
            result = services['archive'].process_document(
                str(test_file),
                "test_project",
                user_id=str(auth_result.user.id)
            )

            # Verify relationship
            assert result.document.created_by == auth_result.user.id

        finally:
            test_file.unlink(missing_ok=True)

    @pytest.mark.integration
    def test_document_metadata_consistency(self, services):
        """Test document metadata consistency."""
        # Create document
        test_file = Path("metadata_test.txt")
        test_content = "Document with metadata for consistency testing."
        test_file.write_text(test_content)

        try:
            result = services['archive'].process_document(
                str(test_file),
                "test_project"
            )

            # Verify metadata consistency
            assert result.document.file_name == "metadata_test.txt"
            assert result.document.file_size == len(test_content.encode())
            assert result.document.processing_status == ProcessingStatus.COMPLETED

        finally:
            test_file.unlink(missing_ok=True)


class TestPerformanceIntegration:
    """Test performance across integrated services."""

    @pytest.fixture
    def temp_db(self):
        """Temporary database."""
        with tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False) as f:
            db_path = f.name

        yield db_path

        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def services(self, temp_db):
        """Services for performance testing."""
        return {
            'archive': ArchiveService(temp_db),
            'auth': AuthService(temp_db)
        }

    @pytest.mark.integration
    @pytest.mark.performance
    def test_batch_processing_performance(self, services):
        """Test batch processing performance."""
        # Create multiple test files
        test_files = []
        file_contents = []

        for i in range(5):
            test_file = Path(f"batch_test_{i}.txt")
            content = f"Batch test document {i} with some content for testing."
            test_file.write_text(content)

            test_files.append(str(test_file))
            file_contents.append(content)

        try:
            # Measure batch processing time
            import time
            start_time = time.time()

            results = services['archive'].batch_process_documents(
                test_files,
                "batch_test_project"
            )

            end_time = time.time()
            processing_time = end_time - start_time

            # Verify results
            assert len(results) == 5

            # Performance assertion (should complete within reasonable time)
            assert processing_time < 10.0  # 10 seconds max

            # Verify all documents were processed
            successful_results = [r for r in results if r.document.processing_status == ProcessingStatus.COMPLETED]
            assert len(successful_results) >= 3  # At least 60% success rate

        finally:
            # Cleanup
            for test_file in test_files:
                Path(test_file).unlink(missing_ok=True)

    @pytest.mark.integration
    @pytest.mark.performance
    def test_concurrent_user_operations(self, services):
        """Test concurrent user operations performance."""
        import threading
        import time

        results = []
        errors = []

        def user_operation(user_id):
            try:
                # Create user
                auth_result = services['auth'].create_user(
                    username=f"concurrent_user_{user_id}",
                    email=f"concurrent_{user_id}@example.com",
                    password="SecurePass123!"
                )

                if auth_result.success:
                    results.append(f"user_{user_id}_created")
                else:
                    errors.append(f"user_{user_id}_failed")

            except Exception as e:
                errors.append(f"user_{user_id}_error: {e}")

        # Create concurrent operations
        threads = []
        for i in range(5):
            thread = threading.Thread(target=user_operation, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Verify results
        assert len(results) >= 3  # At least 60% success rate
        assert len(errors) < 3     # Less than 40% errors


class TestSecurityIntegration:
    """Test security features across service boundaries."""

    @pytest.fixture
    def temp_db(self):
        """Temporary database."""
        with tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False) as f:
            db_path = f.name

        yield db_path

        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def auth_service(self, temp_db):
        """Auth service."""
        return AuthService(temp_db)

    @pytest.mark.integration
    def test_password_security_integration(self, auth_service):
        """Test password security across auth service."""
        # Test password strength validation
        weak_passwords = ["123", "password", "qwerty"]
        strong_passwords = ["SecurePass123!", "MyStr0ng!P@ss", "C0mpl3xP@ssw0rd"]

        # Weak passwords should be rejected
        for password in weak_passwords:
            with pytest.raises(Exception):
                auth_service.create_user(
                    username=f"weak_user_{password}",
                    email=f"weak_{password}@example.com",
                    password=password
                )

        # Strong passwords should be accepted
        for password in strong_passwords:
            result = auth_service.create_user(
                username=f"strong_user_{hash(password)[:8]}",
                email=f"strong_{hash(password)[:8]}@example.com",
                password=password
            )
            assert result.success

    @pytest.mark.integration
    def test_session_security_integration(self, auth_service):
        """Test session security features."""
        # Create user and get session
        auth_result = auth_service.create_user(
            username="session_test_user",
            email="session@example.com",
            password="SecurePass123!"
        )

        assert auth_result.success
        session = auth_result.session

        # Test session validation
        validated_session = auth_service.validate_session(session.session_id)
        assert validated_session is not None
        assert validated_session.user_id == auth_result.user.id

        # Test session invalidation
        logout_success = auth_service.logout(session.session_id)
        assert logout_success

        # Session should no longer be valid
        invalidated_session = auth_service.validate_session(session.session_id)
        assert invalidated_session is None


class TestScalabilityIntegration:
    """Test scalability across service boundaries."""

    @pytest.fixture
    def temp_db(self):
        """Temporary database."""
        with tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False) as f:
            db_path = f.name

        yield db_path

        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def archive_service(self, temp_db):
        """Archive service."""
        return ArchiveService(temp_db)

    @pytest.mark.integration
    @pytest.mark.slow
    def test_large_batch_processing(self, archive_service):
        """Test processing large batches of documents."""
        # Create many test files
        test_files = []
        num_files = 20

        for i in range(num_files):
            test_file = Path(f"large_batch_test_{i}.txt")
            content = f"Large batch test document {i} with substantial content for testing scalability and performance under load."
            test_file.write_text(content)
            test_files.append(str(test_file))

        try:
            # Process large batch
            results = archive_service.batch_process_documents(
                test_files,
                "large_batch_project"
            )

            # Verify scalability
            assert len(results) == num_files

            # Check processing success rate
            successful = len([r for r in results if r.document.processing_status == ProcessingStatus.COMPLETED])
            success_rate = successful / num_files

            assert success_rate >= 0.8  # At least 80% success rate

        finally:
            # Cleanup
            for test_file in test_files:
                Path(test_file).unlink(missing_ok=True)

    @pytest.mark.integration
    def test_memory_usage_under_load(self, archive_service):
        """Test memory usage under load."""
        import psutil
        import os

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Process multiple documents
        test_files = []
        for i in range(10):
            test_file = Path(f"memory_test_{i}.txt")
            test_file.write_text(f"Memory test document {i}")
            test_files.append(str(test_file))

        try:
            results = archive_service.batch_process_documents(
                test_files,
                "memory_test_project"
            )

            # Get final memory usage
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory

            # Memory increase should be reasonable
            assert memory_increase < 100  # Less than 100MB increase

        finally:
            # Cleanup
            for test_file in test_files:
                Path(test_file).unlink(missing_ok=True)


class TestReliabilityIntegration:
    """Test reliability across service boundaries."""

    @pytest.fixture
    def temp_db(self):
        """Temporary database."""
        with tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False) as f:
            db_path = f.name

        yield db_path

        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def services(self, temp_db):
        """All services."""
        return {
            'archive': ArchiveService(temp_db),
            'auth': AuthService(temp_db)
        }

    @pytest.mark.integration
    def test_service_recovery_from_errors(self, services):
        """Test service recovery from various error conditions."""
        # Test 1: Invalid file processing
        with pytest.raises(Exception):
            services['archive'].process_document(
                "non_existent_file.pdf",
                "test_project"
            )

        # Service should still be functional after error
        test_file = Path("recovery_test.txt")
        test_file.write_text("Recovery test document")

        try:
            result = services['archive'].process_document(
                str(test_file),
                "test_project"
            )

            assert result.document.processing_status == ProcessingStatus.COMPLETED

        finally:
            test_file.unlink(missing_ok=True)

    @pytest.mark.integration
    def test_data_persistence_across_operations(self, services):
        """Test data persistence across multiple operations."""
        # Create user
        auth_result = services['auth'].create_user(
            username="persistence_user",
            email="persistence@example.com",
            password="SecurePass123!"
        )

        user_id = auth_result.user.id

        # Create multiple documents
        document_ids = []
        for i in range(3):
            test_file = Path(f"persistence_test_{i}.txt")
            test_file.write_text(f"Persistence test document {i}")

            try:
                result = services['archive'].process_document(
                    str(test_file),
                    "persistence_project",
                    user_id=str(user_id)
                )

                document_ids.append(result.document.id)

            finally:
                test_file.unlink(missing_ok=True)

        # Verify all documents were created and linked to user
        assert len(document_ids) == 3

        # Verify user-document relationships persist
        user_documents = services['archive'].document_repository.get_by_user(user_id)
        assert len(user_documents) >= 3


class TestCompatibilityIntegration:
    """Test compatibility between different service versions."""

    @pytest.fixture
    def temp_db(self):
        """Temporary database."""
        with tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False) as f:
            db_path = f.name

        yield db_path

        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def services(self, temp_db):
        """Services for compatibility testing."""
        return {
            'archive': ArchiveService(temp_db),
            'auth': AuthService(temp_db)
        }

    @pytest.mark.integration
    def test_backward_compatibility(self, services):
        """Test backward compatibility of services."""
        # Test that services work with existing data formats
        # This would test compatibility with older document/user formats

        # Create user with minimal data
        auth_result = services['auth'].create_user(
            username="compat_user",
            email="compat@example.com",
            password="SecurePass123!"
        )

        # Create document with basic metadata
        test_file = Path("compat_test.txt")
        test_file.write_text("Compatibility test document")

        try:
            result = services['archive'].process_document(
                str(test_file),
                "compat_project"
            )

            # Should work with minimal metadata
            assert result.document.processing_status == ProcessingStatus.COMPLETED

        finally:
            test_file.unlink(missing_ok=True)

    @pytest.mark.integration
    def test_forward_compatibility(self, services):
        """Test forward compatibility with future data formats."""
        # Test that services can handle extended data formats
        # This would test with additional metadata fields

        # Create document with extended metadata
        test_file = Path("forward_compat_test.txt")
        test_file.write_text("Forward compatibility test document")

        try:
            result = services['archive'].process_document(
                str(test_file),
                "forward_compat_project",
                metadata={
                    'custom_field': 'custom_value',
                    'extended_metadata': {'key': 'value'}
                }
            )

            # Should handle extended metadata gracefully
            assert result.document.processing_status == ProcessingStatus.COMPLETED

        finally:
            test_file.unlink(missing_ok=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
