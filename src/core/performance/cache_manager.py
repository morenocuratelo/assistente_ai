"""
Comprehensive Cache Management System for Archived Documents

This module provides centralized cache management for all cache systems in the application:
- Streamlit UI caches
- Performance optimizer caches
- Search engine caches
- Knowledge graph caches
- File processing caches

Author: Cline
Created: 2025
"""

import logging
import time
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
import traceback

from ..errors.error_handler import handle_errors


@dataclass
class CacheOperationResult:
    """Result of a cache operation."""
    operation: str
    success: bool
    entries_cleared: int = 0
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CacheStatus:
    """Status information for all cache systems."""
    timestamp: datetime = field(default_factory=datetime.now)
    cache_systems: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    total_entries: int = 0
    last_cleanup: Optional[datetime] = None


class DocumentCacheManager:
    """
    Centralized cache management system for archived documents.

    This class provides a unified interface to manage all cache systems
    used throughout the application for document processing and archiving.
    """

    def __init__(self):
        """Initialize the cache manager."""
        self.logger = logging.getLogger(__name__)
        self._operation_history: List[CacheOperationResult] = []
        self._max_history_size = 100

    @handle_errors(operation="clear_all_caches", component="cache_manager")
    def clear_all_caches(self, include_streamlit: bool = True) -> Dict[str, CacheOperationResult]:
        """
        Clear all cache systems in the application.

        Args:
            include_streamlit: Whether to include Streamlit UI caches

        Returns:
            Dictionary mapping operation names to their results
        """
        self.logger.info("Starting comprehensive cache cleanup")
        start_time = time.time()

        results = {}

        try:
            # Clear Streamlit caches
            if include_streamlit:
                results['streamlit'] = self._clear_streamlit_caches()

            # Clear performance optimizer caches
            results['performance_optimizer'] = self._clear_performance_optimizer_caches()

            # Clear search engine caches
            results['search_engine'] = self._clear_search_engine_caches()

            # Clear knowledge graph caches
            results['knowledge_graph'] = self._clear_knowledge_graph_caches()

            # Clear file processing caches
            results['file_processing'] = self._clear_file_processing_caches()

            # Clear model caches
            results['model_cache'] = self._clear_model_caches()

            # Clear vector store caches (LlamaIndex + ChromaDB)
            results['vector_store'] = self._clear_vector_store_caches()

            total_time = (time.time() - start_time) * 1000
            self.logger.info(f"Cache cleanup completed in {total_time:.1f}ms")

            # Record operation
            self._record_operation(CacheOperationResult(
                operation="clear_all_caches",
                success=True,
                entries_cleared=sum(r.entries_cleared for r in results.values()),
                execution_time_ms=total_time
            ))

            return results

        except Exception as e:
            error_msg = f"Error during comprehensive cache cleanup: {str(e)}"
            self.logger.error(error_msg, extra={
                'traceback': traceback.format_exc()
            })

            # Record failed operation
            self._record_operation(CacheOperationResult(
                operation="clear_all_caches",
                success=False,
                error_message=error_msg,
                execution_time_ms=(time.time() - start_time) * 1000
            ))

            raise

    @handle_errors(operation="clear_streamlit_caches", component="cache_manager")
    def clear_streamlit_caches(self) -> CacheOperationResult:
        """Clear all Streamlit UI caches."""
        return self._clear_streamlit_caches()

    @handle_errors(operation="clear_performance_caches", component="cache_manager")
    def clear_performance_optimizer_caches(self) -> CacheOperationResult:
        """Clear performance optimizer caches."""
        return self._clear_performance_optimizer_caches()

    @handle_errors(operation="clear_search_caches", component="cache_manager")
    def clear_search_engine_caches(self) -> CacheOperationResult:
        """Clear search engine caches."""
        return self._clear_search_engine_caches()

    @handle_errors(operation="clear_knowledge_graph_caches", component="cache_manager")
    def clear_knowledge_graph_caches(self) -> CacheOperationResult:
        """Clear knowledge graph caches."""
        return self._clear_knowledge_graph_caches()

    def _clear_streamlit_caches(self) -> CacheOperationResult:
        """Clear Streamlit UI caches."""
        start_time = time.time()

        try:
            import streamlit as st

            # Clear all Streamlit cache data
            st.cache_data.clear()

            # Clear resource caches if available
            if hasattr(st, 'cache_resource'):
                st.cache_resource.clear()

            execution_time = (time.time() - start_time) * 1000

            result = CacheOperationResult(
                operation="clear_streamlit_caches",
                success=True,
                entries_cleared=1,  # Streamlit doesn't report count
                execution_time_ms=execution_time
            )

            self.logger.info(f"Streamlit caches cleared in {execution_time:.1f}ms")
            return result

        except ImportError:
            # Streamlit not available
            execution_time = (time.time() - start_time) * 1000
            result = CacheOperationResult(
                operation="clear_streamlit_caches",
                success=True,
                entries_cleared=0,
                execution_time_ms=execution_time,
                error_message="Streamlit not available"
            )
            return result

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Error clearing Streamlit caches: {str(e)}"
            self.logger.error(error_msg)

            return CacheOperationResult(
                operation="clear_streamlit_caches",
                success=False,
                error_message=error_msg,
                execution_time_ms=execution_time
            )

    def _clear_performance_optimizer_caches(self) -> CacheOperationResult:
        """Clear performance optimizer caches."""
        start_time = time.time()

        try:
            from .optimizer import clear_all_caches, get_performance_optimizer

            # Clear the global performance optimizer cache
            entries_cleared = clear_all_caches()

            # Also clear the performance optimizer instance cache
            optimizer = get_performance_optimizer()
            additional_cleared = optimizer.cache.clear()

            total_cleared = entries_cleared + additional_cleared
            execution_time = (time.time() - start_time) * 1000

            result = CacheOperationResult(
                operation="clear_performance_optimizer_caches",
                success=True,
                entries_cleared=total_cleared,
                execution_time_ms=execution_time
            )

            self.logger.info(f"Performance optimizer caches cleared: {total_cleared} entries in {execution_time:.1f}ms")
            return result

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Error clearing performance optimizer caches: {str(e)}"
            self.logger.error(error_msg)

            return CacheOperationResult(
                operation="clear_performance_optimizer_caches",
                success=False,
                error_message=error_msg,
                execution_time_ms=execution_time
            )

    def _clear_search_engine_caches(self) -> CacheOperationResult:
        """Clear search engine caches."""
        start_time = time.time()

        try:
            from ...services.archive.search_engine import SearchEngine

            # Create search engine instance and clear its cache
            search_engine = SearchEngine()
            initial_cache_size = len(search_engine._search_cache)

            search_engine.clear_search_cache()

            # Calculate cleared entries
            cleared_entries = initial_cache_size  # Approximation

            execution_time = (time.time() - start_time) * 1000

            result = CacheOperationResult(
                operation="clear_search_engine_caches",
                success=True,
                entries_cleared=cleared_entries,
                execution_time_ms=execution_time
            )

            self.logger.info(f"Search engine caches cleared: {cleared_entries} entries in {execution_time:.1f}ms")
            return result

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Error clearing search engine caches: {str(e)}"
            self.logger.error(error_msg)

            return CacheOperationResult(
                operation="clear_search_engine_caches",
                success=False,
                error_message=error_msg,
                execution_time_ms=execution_time
            )

    def _clear_knowledge_graph_caches(self) -> CacheOperationResult:
        """Clear knowledge graph caches."""
        start_time = time.time()

        try:
            from ...services.ai.knowledge_graph import KnowledgeGraphService

            # Create knowledge graph service and clear its cache
            kg_service = KnowledgeGraphService()
            initial_cache_size = len(kg_service.graph_cache)

            kg_service.clear_graph_cache()

            # Calculate cleared entries
            cleared_entries = initial_cache_size  # Approximation

            execution_time = (time.time() - start_time) * 1000

            result = CacheOperationResult(
                operation="clear_knowledge_graph_caches",
                success=True,
                entries_cleared=cleared_entries,
                execution_time_ms=execution_time
            )

            self.logger.info(f"Knowledge graph caches cleared: {cleared_entries} entries in {execution_time:.1f}ms")
            return result

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Error clearing knowledge graph caches: {str(e)}"
            self.logger.error(error_msg)

            return CacheOperationResult(
                operation="clear_knowledge_graph_caches",
                success=False,
                error_message=error_msg,
                execution_time_ms=execution_time
            )

    def _clear_file_processing_caches(self) -> CacheOperationResult:
        """Clear file processing caches."""
        start_time = time.time()

        try:
            # Clear file processing cache from performance_optimizer.py
            cache_file = "db_memoria/file_cache.json"

            cleared_entries = 0
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                    cleared_entries = len(cache_data)

                # Clear the cache file
                os.remove(cache_file)
                self.logger.info(f"Removed file processing cache file: {cache_file}")
            else:
                self.logger.info("File processing cache file not found, nothing to clear")

            execution_time = (time.time() - start_time) * 1000

            result = CacheOperationResult(
                operation="clear_file_processing_caches",
                success=True,
                entries_cleared=cleared_entries,
                execution_time_ms=execution_time
            )

            return result

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Error clearing file processing caches: {str(e)}"
            self.logger.error(error_msg)

            return CacheOperationResult(
                operation="clear_file_processing_caches",
                success=False,
                error_message=error_msg,
                execution_time_ms=execution_time
            )

    def _clear_model_caches(self) -> CacheOperationResult:
        """Clear AI model caches."""
        start_time = time.time()

        try:
            # Clear model cache directory if it exists
            model_cache_dir = "model_cache"
            cleared_entries = 0

            if os.path.exists(model_cache_dir):
                # Count files before deletion
                for root, dirs, files in os.walk(model_cache_dir):
                    cleared_entries += len(files)

                # Remove the entire cache directory
                import shutil
                shutil.rmtree(model_cache_dir)

                self.logger.info(f"Removed model cache directory: {model_cache_dir}")
            else:
                self.logger.info("Model cache directory not found, nothing to clear")

            execution_time = (time.time() - start_time) * 1000

            result = CacheOperationResult(
                operation="clear_model_caches",
                success=True,
                entries_cleared=cleared_entries,
                execution_time_ms=execution_time
            )

            return result

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Error clearing model caches: {str(e)}"
            self.logger.error(error_msg)

            return CacheOperationResult(
                operation="clear_model_caches",
                success=False,
                error_message=error_msg,
                execution_time_ms=execution_time
            )

    def _clear_vector_store_caches(self) -> CacheOperationResult:
        """Clear LlamaIndex VectorStore and ChromaDB caches."""
        start_time = time.time()

        try:
            cleared_entries = 0

            # Clear ChromaDB collection
            try:
                import chromadb
                from llama_index.vector_stores.chroma import ChromaVectorStore

                db = chromadb.PersistentClient(path="db_memoria")

                # Check if "documents" collection exists and count items
                try:
                    collection = db.get_collection("documents")
                    cleared_entries = collection.count()
                    # Delete and recreate the collection
                    db.delete_collection("documents")
                    db.create_collection("documents")
                    self.logger.info(f"Cleared ChromaDB collection 'documents' with {cleared_entries} items")
                except ValueError:
                    # Collection doesn't exist yet
                    self.logger.info("ChromaDB collection 'documents' doesn't exist, nothing to clear")

            except ImportError:
                self.logger.warning("ChromaDB not available, cannot clear vector store")
            except Exception as e:
                self.logger.error(f"Error clearing ChromaDB: {e}")

            # Clear LlamaIndex storage files
            storage_dir = "db_memoria"
            if os.path.exists(storage_dir):
                # Remove LlamaIndex storage files (but keep the metadata.sqlite)
                for item in os.listdir(storage_dir):
                    item_path = os.path.join(storage_dir, item)
                    if item != "metadata.sqlite" and item != "metadata.db":  # Keep the papers database
                        try:
                            if os.path.isfile(item_path):
                                os.remove(item_path)
                                self.logger.info(f"Removed LlamaIndex storage file: {item}")
                            elif os.path.isdir(item_path):
                                import shutil
                                shutil.rmtree(item_path)
                                self.logger.info(f"Removed LlamaIndex storage directory: {item}")
                        except Exception as e:
                            self.logger.error(f"Error removing {item_path}: {e}")

            execution_time = (time.time() - start_time) * 1000

            result = CacheOperationResult(
                operation="clear_vector_store_caches",
                success=True,
                entries_cleared=cleared_entries,
                execution_time_ms=execution_time
            )

            return result

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = f"Error clearing vector store caches: {str(e)}"
            self.logger.error(error_msg)

            return CacheOperationResult(
                operation="clear_vector_store_caches",
                success=False,
                error_message=error_msg,
                execution_time_ms=execution_time
            )

    def get_cache_status(self) -> CacheStatus:
        """Get comprehensive status of all cache systems."""
        status = CacheStatus()

        try:
            # Check Streamlit cache status
            try:
                import streamlit as st
                status.cache_systems['streamlit'] = {
                    'available': True,
                    'status': 'active'
                }
            except ImportError:
                status.cache_systems['streamlit'] = {
                    'available': False,
                    'status': 'not_available'
                }

            # Check performance optimizer cache
            try:
                from .optimizer import get_performance_optimizer
                optimizer = get_performance_optimizer()
                cache_stats = optimizer.cache.get_stats()
                status.cache_systems['performance_optimizer'] = {
                    'available': True,
                    'entries': cache_stats.get('total_entries', 0),
                    'stats': cache_stats
                }
                status.total_entries += cache_stats.get('total_entries', 0)
            except Exception as e:
                status.cache_systems['performance_optimizer'] = {
                    'available': False,
                    'error': str(e)
                }

            # Check search engine cache
            try:
                from ...services.archive.search_engine import SearchEngine
                search_engine = SearchEngine()
                cache_size = len(search_engine._search_cache)
                status.cache_systems['search_engine'] = {
                    'available': True,
                    'entries': cache_size
                }
                status.total_entries += cache_size
            except Exception as e:
                status.cache_systems['search_engine'] = {
                    'available': False,
                    'error': str(e)
                }

            # Check knowledge graph cache
            try:
                from ...services.ai.knowledge_graph import KnowledgeGraphService
                kg_service = KnowledgeGraphService()
                cache_size = len(kg_service.graph_cache)
                status.cache_systems['knowledge_graph'] = {
                    'available': True,
                    'entries': cache_size
                }
                status.total_entries += cache_size
            except Exception as e:
                status.cache_systems['knowledge_graph'] = {
                    'available': False,
                    'error': str(e)
                }

            # Check file processing cache
            cache_file = "db_memoria/file_cache.json"
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r') as f:
                        cache_data = json.load(f)
                        entries = len(cache_data)
                        status.cache_systems['file_processing'] = {
                            'available': True,
                            'entries': entries,
                            'file_path': cache_file
                        }
                        status.total_entries += entries
                except Exception as e:
                    status.cache_systems['file_processing'] = {
                        'available': False,
                        'error': str(e)
                    }
            else:
                status.cache_systems['file_processing'] = {
                    'available': True,
                    'entries': 0,
                    'file_path': cache_file
                }

            # Check model cache
            model_cache_dir = "model_cache"
            if os.path.exists(model_cache_dir):
                try:
                    entries = 0
                    for root, dirs, files in os.walk(model_cache_dir):
                        entries += len(files)

                    status.cache_systems['model_cache'] = {
                        'available': True,
                        'entries': entries,
                        'directory': model_cache_dir
                    }
                    status.total_entries += entries
                except Exception as e:
                    status.cache_systems['model_cache'] = {
                        'available': False,
                        'error': str(e)
                    }
            else:
                status.cache_systems['model_cache'] = {
                    'available': True,
                    'entries': 0,
                    'directory': model_cache_dir
                }

            # Check vector store cache (ChromaDB)
            try:
                import chromadb
                db = chromadb.PersistentClient(path="db_memoria")
                try:
                    collection = db.get_collection("documents")
                    entries = collection.count()
                    status.cache_systems['vector_store'] = {
                        'available': True,
                        'entries': entries,
                        'collection': 'documents'
                    }
                    status.total_entries += entries
                except ValueError:
                    # Collection doesn't exist
                    status.cache_systems['vector_store'] = {
                        'available': True,
                        'entries': 0,
                        'collection': 'documents'
                    }
            except ImportError:
                status.cache_systems['vector_store'] = {
                    'available': False,
                    'error': 'ChromaDB not available'
                }
            except Exception as e:
                status.cache_systems['vector_store'] = {
                    'available': False,
                    'error': str(e)
                }

        except Exception as e:
            self.logger.error(f"Error getting cache status: {str(e)}")
            status.cache_systems['error'] = str(e)

        return status

    def get_operation_history(self, limit: int = 10) -> List[CacheOperationResult]:
        """Get recent cache operation history."""
        return self._operation_history[-limit:] if self._operation_history else []

    def _record_operation(self, result: CacheOperationResult) -> None:
        """Record a cache operation in history."""
        self._operation_history.append(result)

        # Maintain history size limit
        if len(self._operation_history) > self._max_history_size:
            self._operation_history = self._operation_history[-self._max_history_size:]


# Global cache manager instance
_document_cache_manager: Optional[DocumentCacheManager] = None


def get_document_cache_manager() -> DocumentCacheManager:
    """Get global document cache manager instance."""
    global _document_cache_manager
    if _document_cache_manager is None:
        _document_cache_manager = DocumentCacheManager()
    return _document_cache_manager


# Convenience functions for easy access

def clear_all_document_caches(include_streamlit: bool = True) -> Dict[str, CacheOperationResult]:
    """
    Clear all document-related caches.

    Args:
        include_streamlit: Whether to include Streamlit UI caches

    Returns:
        Dictionary of operation results
    """
    manager = get_document_cache_manager()
    return manager.clear_all_caches(include_streamlit)


def clear_streamlit_document_caches() -> CacheOperationResult:
    """Clear only Streamlit document caches."""
    manager = get_document_cache_manager()
    return manager.clear_streamlit_caches()


def clear_performance_document_caches() -> CacheOperationResult:
    """Clear only performance optimizer document caches."""
    manager = get_document_cache_manager()
    return manager.clear_performance_optimizer_caches()


def clear_search_document_caches() -> CacheOperationResult:
    """Clear only search engine document caches."""
    manager = get_document_cache_manager()
    return manager.clear_search_engine_caches()


def clear_knowledge_graph_document_caches() -> CacheOperationResult:
    """Clear only knowledge graph document caches."""
    manager = get_document_cache_manager()
    return manager.clear_knowledge_graph_caches()


def clear_vector_store_document_caches() -> CacheOperationResult:
    """Clear only vector store document caches (LlamaIndex + ChromaDB)."""
    manager = get_document_cache_manager()
    return manager._clear_vector_store_caches()


def get_document_cache_status() -> CacheStatus:
    """Get status of all document cache systems."""
    manager = get_document_cache_manager()
    return manager.get_cache_status()


def get_document_cache_history(limit: int = 10) -> List[CacheOperationResult]:
    """Get recent document cache operation history."""
    manager = get_document_cache_manager()
    return manager.get_operation_history(limit)


# Import required modules for type checking
import os
import json
from typing import Optional
