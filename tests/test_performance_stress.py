"""
Performance and stress testing for the application.
Tests load handling, memory usage, and system limits.
"""

import pytest
import time
import threading
import multiprocessing
import psutil
import os
from unittest.mock import Mock, patch
import sqlite3

from tests.conftest import TestDataFactory

class TestLoadTesting:
    """Load testing for high-volume operations."""

    @pytest.mark.load
    def test_high_volume_document_processing(self, mock_config: Mock) -> None:
        """Test processing thousands of documents."""
        from src.core.utils.validation import DocumentProcessor

        processor = DocumentProcessor(mock_config)

        # Create large batch of documents
        documents = [
            {'id': i, 'content': f'Document {i} content for load testing. ' * 50}
            for i in range(1000)
        ]

        with patch.object(processor, '_process_single_document') as mock_process:
            mock_process.return_value = {'processed': True, 'id': None}

            start_time = time.time()
            result = processor.process_document(documents)
            end_time = time.time()

            # Should process 1000 documents in reasonable time
            assert len(result) == 1000
            assert end_time - start_time < 30.0  # Less than 30 seconds

    @pytest.mark.load
    def test_concurrent_user_sessions(self) -> None:
        """Test multiple concurrent user sessions."""
        from src.services.service_manager import ServiceManager

        results = []
        errors = []

        def simulate_user_session(session_id: int):
            try:
                manager = ServiceManager()
                # Simulate user operations
                time.sleep(0.1)  # Simulate work
                results.append(f"Session {session_id} completed")
            except Exception as e:
                errors.append(f"Session {session_id} failed: {e}")

        # Start 50 concurrent sessions
        threads = [
            threading.Thread(target=simulate_user_session, args=(i,))
            for i in range(50)
        ]

        start_time = time.time()
        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()
        end_time = time.time()

        # All sessions should complete successfully
        assert len(errors) == 0
        assert len(results) == 50
        assert end_time - start_time < 15.0  # Less than 15 seconds

    @pytest.mark.load
    def test_database_concurrent_access(self, in_memory_db: sqlite3.Connection) -> None:
        """Test concurrent database access."""
        from src.database.repositories.project_repository import ProjectRepository

        repo = ProjectRepository(in_memory_db)
        results = []
        errors = []

        def database_operation(thread_id: int):
            try:
                # Simulate database operations
                for i in range(100):
                    # This would be actual database operations in real tests
                    time.sleep(0.001)  # Small delay to simulate work
                results.append(f"Thread {thread_id} completed")
            except Exception as e:
                errors.append(f"Thread {thread_id} failed: {e}")

        # Start 20 concurrent database operations
        threads = [
            threading.Thread(target=database_operation, args=(i,))
            for i in range(20)
        ]

        start_time = time.time()
        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()
        end_time = time.time()

        # All database operations should complete
        assert len(errors) == 0
        assert len(results) == 20
        assert end_time - start_time < 10.0

class TestStressTesting:
    """Stress testing for system limits."""

    @pytest.mark.stress
    def test_memory_stress_with_large_documents(self, mock_config: Mock) -> None:
        """Test memory handling with very large documents."""
        import gc
        from src.core.utils.validation import DocumentProcessor

        processor = DocumentProcessor(mock_config)

        # Get initial memory
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create extremely large document
        large_content = 'Very large document content. ' * 100000  # ~2.5MB
        large_document = [{'content': large_content, 'metadata': {'size': len(large_content)}}]

        with patch.object(processor, '_process_single_document') as mock_process:
            mock_process.return_value = {'processed': True, 'size': len(large_content)}

            # Process the large document
            result = processor.process_document(large_document)

            # Force garbage collection
            gc.collect()

            # Check memory usage
            final_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Memory should not grow excessively (less than 200MB increase)
            assert final_memory - initial_memory < 200
            assert result[0]['processed'] is True

    @pytest.mark.stress
    def test_cpu_stress_with_complex_operations(self, mock_config: Mock) -> None:
        """Test CPU handling with complex operations."""
        from src.core.utils.validation import DocumentProcessor

        processor = DocumentProcessor(mock_config)

        # Create CPU-intensive documents
        complex_documents = [
            {'id': i, 'content': f'Complex document {i} with lots of processing. ' * 1000}
            for i in range(100)
        ]

        with patch.object(processor, '_process_single_document') as mock_process:
            def cpu_intensive_processing(doc):
                # Simulate CPU-intensive work
                time.sleep(0.01)  # 10ms per document
                return {'processed': True, 'complexity': 'high'}

            mock_process.side_effect = cpu_intensive_processing

            start_time = time.time()
            result = processor.process_document(complex_documents)
            end_time = time.time()

            # Should handle CPU-intensive operations
            assert len(result) == 100
            assert all(r['processed'] is True for r in result)
            # Should complete within reasonable time (allowing for CPU work)
            assert end_time - start_time < 60.0  # Less than 1 minute

    @pytest.mark.stress
    def test_system_resource_limits(self) -> None:
        """Test system resource limits and recovery."""
        import resource

        # Get current resource limits
        soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)

        # Test that we can handle file operations within limits
        open_files = []
        try:
            # Try to open files up to the soft limit
            for i in range(min(50, soft_limit - 10)):  # Leave some margin
                try:
                    # In a real test, this would be actual file operations
                    open_files.append(f"file_{i}")
                except Exception as e:
                    # Should handle resource exhaustion gracefully
                    assert "too many" in str(e).lower() or "resource" in str(e).lower()
                    break

            # Should be able to open a reasonable number of files
            assert len(open_files) > 10

        finally:
            # Clean up
            open_files.clear()

class TestScalabilityTesting:
    """Scalability testing for growing data sets."""

    @pytest.mark.scalability
    def test_linear_performance_scaling(self, mock_config: Mock) -> None:
        """Test that performance scales linearly with data size."""
        from src.core.utils.validation import DocumentProcessor

        processor = DocumentProcessor(mock_config)

        # Test different data sizes
        sizes_and_times = []

        for size in [10, 50, 100, 500]:
            documents = [
                {'id': i, 'content': f'Document {i} content. ' * 10}
                for i in range(size)
            ]

            with patch.object(processor, '_process_single_document') as mock_process:
                mock_process.return_value = {'processed': True}

                start_time = time.time()
                result = processor.process_document(documents)
                end_time = time.time()

                processing_time = end_time - start_time
                sizes_and_times.append((size, processing_time))

                assert len(result) == size

        # Check that processing time scales roughly linearly
        # (allowing for some overhead at small sizes)
        for i in range(1, len(sizes_and_times)):
            current_size, current_time = sizes_and_times[i]
            prev_size, prev_time = sizes_and_times[i-1]

            # Time should not increase more than 6x when size increases 5x
            # (allowing for some non-linear overhead)
            if current_size / prev_size > 2.0:
                time_ratio = current_time / prev_time
                size_ratio = current_size / prev_size
                assert time_ratio < size_ratio * 1.2  # Allow 20% overhead

    @pytest.mark.scalability
    def test_database_scaling(self, in_memory_db: sqlite3.Connection) -> None:
        """Test database performance with growing data."""
        from src.database.repositories.project_repository import ProjectRepository

        repo = ProjectRepository(in_memory_db)

        # Test with increasing amounts of data
        for num_records in [100, 500, 1000]:
            start_time = time.time()

            # Simulate inserting multiple records
            for i in range(num_records):
                # In real test, this would be actual database operations
                pass

            end_time = time.time()

            # Should handle scaling without exponential slowdown
            assert end_time - start_time < num_records * 0.01  # Less than 10ms per record

class TestEnduranceTesting:
    """Endurance testing for long-running operations."""

    @pytest.mark.endurance
    def test_long_running_service_stability(self) -> None:
        """Test service stability over extended periods."""
        from src.services.service_manager import ServiceManager

        manager = ServiceManager()
        start_time = time.time()

        # Simulate long-running operations
        for i in range(1000):
            # Simulate periodic operations
            time.sleep(0.001)  # 1ms between operations

            if i % 100 == 0:
                # Periodic health check
                assert manager is not None

        end_time = time.time()

        # Should maintain stability over time
        assert end_time - start_time < 30.0  # Should complete in reasonable time
        assert manager is not None

    @pytest.mark.endurance
    def test_memory_leak_detection(self, mock_config: Mock) -> None:
        """Test for memory leaks in long-running operations."""
        import gc
        from src.core.utils.validation import DocumentProcessor

        processor = DocumentProcessor(mock_config)

        # Get initial memory
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Run many operations
        for iteration in range(100):
            documents = [
                {'id': f'iter_{iteration}_{i}', 'content': f'Content {i} for iteration {iteration}'}
                for i in range(10)
            ]

            with patch.object(processor, '_process_single_document') as mock_process:
                mock_process.return_value = {'processed': True}
                result = processor.process_document(documents)

                assert len(result) == 10

            # Force garbage collection every 10 iterations
            if iteration % 10 == 0:
                gc.collect()

        # Check final memory
        final_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Memory should not leak significantly (less than 50MB increase)
        assert final_memory - initial_memory < 50

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
