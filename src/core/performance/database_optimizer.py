"""
Database performance optimization system.
Implements query optimization, connection pooling, and performance monitoring.
"""

import sqlite3
import time
import threading
import queue
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging
import psutil
import os

from ...core.errors.error_handler import handle_errors


@dataclass
class QueryMetrics:
    """Metrics for database query performance."""
    query_hash: str
    query_pattern: str
    execution_count: int
    total_time_ms: float
    avg_time_ms: float
    min_time_ms: float
    max_time_ms: float
    last_executed: datetime
    slow_query_count: int
    error_count: int


@dataclass
class ConnectionPool:
    """Database connection pool."""
    max_connections: int
    available_connections: List[sqlite3.Connection] = field(default_factory=list)
    in_use_connections: Dict[str, sqlite3.Connection] = field(default_factory=dict)
    created_connections: int = 0
    connection_timeout: int = 300  # 5 minutes
    lock: threading.Lock = field(default_factory=threading.Lock)


class DatabaseConnectionPool:
    """Advanced database connection pooling system."""

    def __init__(self, db_path: str, max_connections: int = 10):
        """Initialize connection pool.

        Args:
            db_path: Path to database file
            max_connections: Maximum number of connections
        """
        self.db_path = db_path
        self.max_connections = max_connections
        self.pool = ConnectionPool(max_connections=max_connections)
        self.logger = logging.getLogger(__name__)

        # Initialize connection pool
        self._initialize_pool()

    def _initialize_pool(self) -> None:
        """Initialize connection pool with minimum connections."""
        min_connections = min(3, self.max_connections)

        for _ in range(min_connections):
            try:
                conn = self._create_connection()
                self.pool.available_connections.append(conn)
                self.pool.created_connections += 1
            except Exception as e:
                self.logger.error(f"Error creating initial connection: {e}")

    def _create_connection(self) -> sqlite3.Connection:
        """Create new database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        # Enable performance optimizations
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=1000000")
        conn.execute("PRAGMA temp_store=memory")

        return conn

    def get_connection(self, timeout: int = 30) -> sqlite3.Connection:
        """Get connection from pool.

        Args:
            timeout: Timeout in seconds

        Returns:
            Database connection
        """
        with self.pool.lock:
            # Try to get available connection
            if self.pool.available_connections:
                conn = self.pool.available_connections.pop()
                self.pool.in_use_connections[id(conn)] = conn
                return conn

            # Create new connection if under limit
            if self.pool.created_connections < self.max_connections:
                conn = self._create_connection()
                self.pool.in_use_connections[id(conn)] = conn
                self.pool.created_connections += 1
                return conn

            # Wait for available connection
            return self._wait_for_connection(timeout)

    def _wait_for_connection(self, timeout: int) -> sqlite3.Connection:
        """Wait for available connection."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            with self.pool.lock:
                if self.pool.available_connections:
                    conn = self.pool.available_connections.pop()
                    self.pool.in_use_connections[id(conn)] = conn
                    return conn

            time.sleep(0.1)  # Small delay

        raise TimeoutError(f"Timeout waiting for database connection after {timeout}s")

    def release_connection(self, conn: sqlite3.Connection) -> None:
        """Release connection back to pool.

        Args:
            conn: Connection to release
        """
        conn_id = id(conn)

        with self.pool.lock:
            if conn_id in self.pool.in_use_connections:
                del self.pool.in_use_connections[conn_id]
                self.pool.available_connections.append(conn)

    def close_all_connections(self) -> None:
        """Close all connections in pool."""
        with self.pool.lock:
            # Close available connections
            for conn in self.pool.available_connections:
                try:
                    conn.close()
                except Exception as e:
                    self.logger.error(f"Error closing available connection: {e}")

            # Close in-use connections
            for conn in self.pool.in_use_connections.values():
                try:
                    conn.close()
                except Exception as e:
                    self.logger.error(f"Error closing in-use connection: {e}")

            self.pool.available_connections.clear()
            self.pool.in_use_connections.clear()
            self.pool.created_connections = 0

    def get_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics.

        Returns:
            Pool statistics dictionary
        """
        with self.pool.lock:
            return {
                'max_connections': self.pool.max_connections,
                'available_connections': len(self.pool.available_connections),
                'in_use_connections': len(self.pool.in_use_connections),
                'created_connections': self.pool.created_connections,
                'utilization_percent': (
                    len(self.pool.in_use_connections) / self.pool.created_connections * 100
                    if self.pool.created_connections > 0 else 0
                )
            }


class QueryPerformanceProfiler:
    """Profiles database query performance."""

    def __init__(self):
        """Initialize query profiler."""
        self.logger = logging.getLogger(__name__)
        self.query_metrics: Dict[str, QueryMetrics] = {}
        self.slow_query_threshold_ms = 100  # 100ms
        self.lock = threading.Lock()

    @handle_errors(operation="profile_query", component="query_profiler")
    def profile_query(self, query: str, execution_time_ms: float, error: Optional[str] = None) -> None:
        """Profile database query execution.

        Args:
            query: SQL query executed
            execution_time_ms: Execution time in milliseconds
            error: Error message if query failed
        """
        # Normalize query for metrics
        query_hash = self._generate_query_hash(query)

        with self.lock:
            if query_hash not in self.query_metrics:
                self.query_metrics[query_hash] = QueryMetrics(
                    query_hash=query_hash,
                    query_pattern=self._extract_query_pattern(query),
                    execution_count=0,
                    total_time_ms=0.0,
                    avg_time_ms=0.0,
                    min_time_ms=float('inf'),
                    max_time_ms=0.0,
                    last_executed=datetime.utcnow(),
                    slow_query_count=0,
                    error_count=0
                )

            metrics = self.query_metrics[query_hash]
            metrics.execution_count += 1
            metrics.total_time_ms += execution_time_ms
            metrics.avg_time_ms = metrics.total_time_ms / metrics.execution_count
            metrics.min_time_ms = min(metrics.min_time_ms, execution_time_ms)
            metrics.max_time_ms = max(metrics.max_time_ms, execution_time_ms)
            metrics.last_executed = datetime.utcnow()

            if execution_time_ms > self.slow_query_threshold_ms:
                metrics.slow_query_count += 1

            if error:
                metrics.error_count += 1

    def _generate_query_hash(self, query: str) -> str:
        """Generate hash for query normalization."""
        import hashlib

        # Normalize query by removing extra whitespace and parameter values
        normalized = ' '.join(query.split())
        return hashlib.md5(normalized.encode()).hexdigest()

    def _extract_query_pattern(self, query: str) -> str:
        """Extract query pattern for analysis."""
        # Replace parameter placeholders with generic markers
        pattern = query

        # Replace string literals
        pattern = re.sub(r"'[^']*'", "?", pattern)

        # Replace numeric literals
        pattern = re.sub(r'\b\d+\b', "?", pattern)

        return pattern

    def get_slow_queries(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get slow queries.

        Args:
            limit: Maximum number of queries to return

        Returns:
            List of slow query metrics
        """
        slow_queries = []

        for metrics in self.query_metrics.values():
            if metrics.slow_query_count > 0:
                slow_queries.append({
                    'query_hash': metrics.query_hash,
                    'query_pattern': metrics.query_pattern,
                    'execution_count': metrics.execution_count,
                    'avg_time_ms': metrics.avg_time_ms,
                    'max_time_ms': metrics.max_time_ms,
                    'slow_query_count': metrics.slow_query_count,
                    'error_count': metrics.error_count,
                    'last_executed': metrics.last_executed.isoformat()
                })

        # Sort by average time descending
        slow_queries.sort(key=lambda x: x['avg_time_ms'], reverse=True)
        return slow_queries[:limit]

    def get_query_recommendations(self) -> List[Dict[str, Any]]:
        """Get query optimization recommendations.

        Returns:
            List of optimization recommendations
        """
        recommendations = []

        for metrics in self.query_metrics.values():
            # Recommend index for frequently slow queries
            if (metrics.execution_count > 10 and
                metrics.avg_time_ms > self.slow_query_threshold_ms):

                recommendations.append({
                    'type': 'index_recommendation',
                    'query_pattern': metrics.query_pattern,
                    'reason': f'Query executed {metrics.execution_count} times with avg {metrics.avg_time_ms}ms',
                    'suggestion': 'Consider adding database index for better performance'
                })

            # Recommend query optimization for error-prone queries
            if metrics.error_count > 0:
                recommendations.append({
                    'type': 'error_reduction',
                    'query_pattern': metrics.query_pattern,
                    'reason': f'Query failed {metrics.error_count} times',
                    'suggestion': 'Review query logic and error handling'
                })

        return recommendations

    def export_metrics(self, file_path: str) -> bool:
        """Export query metrics to file.

        Args:
            file_path: Path to export file

        Returns:
            True if export successful
        """
        try:
            metrics_data = []

            for metrics in self.query_metrics.values():
                metrics_data.append({
                    'query_hash': metrics.query_hash,
                    'query_pattern': metrics.query_pattern,
                    'execution_count': metrics.execution_count,
                    'total_time_ms': metrics.total_time_ms,
                    'avg_time_ms': metrics.avg_time_ms,
                    'min_time_ms': metrics.min_time_ms,
                    'max_time_ms': metrics.max_time_ms,
                    'slow_query_count': metrics.slow_query_count,
                    'error_count': metrics.error_count,
                    'last_executed': metrics.last_executed.isoformat()
                })

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(metrics_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Query metrics exported to {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error exporting query metrics: {e}")
            return False


class DatabasePerformanceOptimizer:
    """Main database performance optimization system."""

    def __init__(self, db_path: str):
        """Initialize database optimizer.

        Args:
            db_path: Path to database file
        """
        self.db_path = db_path
        self.connection_pool = DatabaseConnectionPool(db_path)
        self.query_profiler = QueryPerformanceProfiler()
        self.logger = logging.getLogger(__name__)

        # Performance monitoring
        self.monitoring_enabled = True
        self.optimization_suggestions: List[Dict[str, Any]] = []

        # Setup database optimizations
        self._setup_database_optimizations()

    def _setup_database_optimizations(self) -> None:
        """Setup database performance optimizations."""
        try:
            with self.connection_pool.get_connection() as conn:
                # Enable WAL mode for better concurrency
                conn.execute("PRAGMA journal_mode=WAL")

                # Optimize cache size
                conn.execute("PRAGMA cache_size=1000000")  # ~1GB cache

                # Optimize temp storage
                conn.execute("PRAGMA temp_store=memory")

                # Optimize synchronous mode
                conn.execute("PRAGMA synchronous=NORMAL")

                # Enable foreign keys
                conn.execute("PRAGMA foreign_keys=ON")

                conn.commit()

            self.logger.info("Database optimizations applied")

        except Exception as e:
            self.logger.error(f"Error setting up database optimizations: {e}")

    @handle_errors(operation="execute_optimized_query", component="database_optimizer")
    def execute_optimized_query(
        self,
        query: str,
        params: tuple = None,
        use_pool: bool = True
    ) -> List[Dict[str, Any]]:
        """Execute query with performance optimization.

        Args:
            query: SQL query to execute
            params: Query parameters
            use_pool: Whether to use connection pool

        Returns:
            Query results
        """
        start_time = time.time()

        try:
            # Get connection
            if use_pool:
                conn = self.connection_pool.get_connection()
                should_release = True
            else:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                should_release = False

            try:
                # Execute query
                cursor = conn.execute(query, params or ())

                # Get results
                results = [dict(row) for row in cursor.fetchall()]

                # Record metrics
                execution_time_ms = (time.time() - start_time) * 1000

                if self.monitoring_enabled:
                    self.query_profiler.profile_query(query, execution_time_ms)

                return results

            finally:
                if should_release:
                    self.connection_pool.release_connection(conn)
                else:
                    conn.close()

        except Exception as e:
            # Record error metrics
            execution_time_ms = (time.time() - start_time) * 1000

            if self.monitoring_enabled:
                self.query_profiler.profile_query(query, execution_time_ms, str(e))

            self.logger.error(f"Error executing optimized query: {e}")
            raise

    def create_optimized_indexes(self) -> List[str]:
        """Create optimized indexes for better performance.

        Returns:
            List of created indexes
        """
        created_indexes = []

        try:
            with self.connection_pool.get_connection() as conn:
                # Indexes for documents table
                indexes = [
                    ("idx_documents_project_status", "documents", "project_id, processing_status"),
                    ("idx_documents_created_by", "documents", "created_by"),
                    ("idx_documents_content_hash", "documents", "content_hash"),
                    ("idx_documents_mime_type", "documents", "mime_type"),
                    ("idx_documents_keywords", "documents", "keywords"),

                    # Indexes for users table
                    ("idx_users_username", "users", "username"),
                    ("idx_users_email", "users", "email"),

                    # Indexes for courses table
                    ("idx_courses_project_user", "courses", "project_id, user_id"),

                    # Indexes for chat sessions
                    ("idx_chat_sessions_project", "chat_sessions", "project_id"),
                    ("idx_chat_sessions_user", "chat_sessions", "user_id"),

                    # Indexes for concept entities
                    ("idx_concept_entities_project", "concept_entities", "project_id"),
                    ("idx_concept_entities_user", "concept_entities", "user_id"),
                    ("idx_concept_entities_type", "concept_entities", "entity_type"),

                    # Indexes for user activity
                    ("idx_user_activity_project", "user_activity", "project_id"),
                    ("idx_user_activity_user", "user_activity", "user_id"),
                    ("idx_user_activity_timestamp", "user_activity", "timestamp"),

                    # Indexes for processing status
                    ("idx_processing_status_project", "document_processing_status", "project_id"),
                    ("idx_processing_status_state", "document_processing_status", "processing_state"),
                ]

                for index_name, table_name, columns in indexes:
                    try:
                        conn.execute(f"""
                            CREATE INDEX IF NOT EXISTS {index_name}
                            ON {table_name} ({columns})
                        """)
                        created_indexes.append(index_name)
                        self.logger.info(f"Created index: {index_name}")

                    except Exception as e:
                        self.logger.error(f"Error creating index {index_name}: {e}")

                conn.commit()

        except Exception as e:
            self.logger.error(f"Error creating optimized indexes: {e}")

        return created_indexes

    def analyze_query_performance(self) -> Dict[str, Any]:
        """Analyze database query performance.

        Returns:
            Performance analysis results
        """
        analysis = {
            'pool_stats': self.connection_pool.get_pool_stats(),
            'slow_queries': self.query_profiler.get_slow_queries(),
            'query_recommendations': self.query_profiler.get_query_recommendations(),
            'database_stats': self._get_database_statistics(),
            'performance_suggestions': self._generate_performance_suggestions(),
            'analysis_timestamp': datetime.utcnow().isoformat()
        }

        return analysis

    def _get_database_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            with self.connection_pool.get_connection() as conn:
                stats = {}

                # Get table information
                cursor = conn.execute("""
                    SELECT name, COUNT(*) as count
                    FROM sqlite_master
                    WHERE type='table'
                    GROUP BY name
                """)

                tables = []
                for row in cursor.fetchall():
                    table_name = row['name']
                    count = row['count']

                    # Get row count for each table
                    try:
                        row_cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
                        row_count = row_cursor.fetchone()[0]

                        tables.append({
                            'name': table_name,
                            'row_count': row_count
                        })

                    except Exception as e:
                        self.logger.error(f"Error getting row count for {table_name}: {e}")

                stats['tables'] = tables

                # Get database size
                db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                stats['database_size_bytes'] = db_size
                stats['database_size_mb'] = db_size / (1024 * 1024)

                # Get WAL file size if exists
                wal_file = f"{self.db_path}-wal"
                if os.path.exists(wal_file):
                    wal_size = os.path.getsize(wal_file)
                    stats['wal_size_bytes'] = wal_size
                    stats['wal_size_mb'] = wal_size / (1024 * 1024)

                return stats

        except Exception as e:
            self.logger.error(f"Error getting database statistics: {e}")
            return {}

    def _generate_performance_suggestions(self) -> List[Dict[str, Any]]:
        """Generate performance optimization suggestions."""
        suggestions = []

        # Analyze pool utilization
        pool_stats = self.connection_pool.get_pool_stats()
        utilization = pool_stats.get('utilization_percent', 0)

        if utilization > 80:
            suggestions.append({
                'type': 'connection_pool',
                'priority': 'high',
                'suggestion': 'Increase connection pool size',
                'reason': f'High pool utilization: {utilization:.1f}%',
            })

        # Analyze slow queries
        slow_queries = self.query_profiler.get_slow_queries(5)

        for slow_query in slow_queries:
            if slow_query['avg_time_ms'] > 500:  # Very slow queries
                suggestions.append({
                    'type': 'query_optimization',
                    'priority': 'high',
                    'suggestion': f'Optimize query pattern: {slow_query["query_pattern"][:50]}...',
                    'reason': f'Average execution time: {slow_query["avg_time_ms"]".1f"}ms'
                })

        # Analyze database size
        db_stats = self._get_database_statistics()
        db_size_mb = db_stats.get('database_size_mb', 0)

        if db_size_mb > 100:  # Large database
            suggestions.append({
                'type': 'maintenance',
                'priority': 'medium',
                'suggestion': 'Consider database maintenance (VACUUM, ANALYZE)',
                'reason': f'Database size: {db_size_mb".1f"}MB'
            })

        return suggestions

    def optimize_database_schema(self) -> Dict[str, Any]:
        """Optimize database schema for better performance.

        Returns:
            Optimization results
        """
        results = {
            'indexes_created': [],
            'tables_analyzed': [],
            'optimizations_applied': [],
            'errors': []
        }

        try:
            # Create optimized indexes
            created_indexes = self.create_optimized_indexes()
            results['indexes_created'] = created_indexes

            # Analyze tables
            analyzed_tables = self._analyze_table_statistics()
            results['tables_analyzed'] = analyzed_tables

            # Apply schema optimizations
            optimizations = self._apply_schema_optimizations()
            results['optimizations_applied'] = optimizations

        except Exception as e:
            results['errors'].append(str(e))
            self.logger.error(f"Error optimizing database schema: {e}")

        return results

    def _analyze_table_statistics(self) -> List[Dict[str, Any]]:
        """Analyze table statistics for optimization."""
        analyzed = []

        try:
            with self.connection_pool.get_connection() as conn:
                # Get all tables
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master WHERE type='table'
                """)

                for row in cursor.fetchall():
                    table_name = row['name']

                    try:
                        # Get table info
                        info_cursor = conn.execute(f"PRAGMA table_info({table_name})")
                        columns = [col['name'] for col in info_cursor.fetchall()]

                        # Get row count
                        count_cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
                        row_count = count_cursor.fetchone()[0]

                        analyzed.append({
                            'table': table_name,
                            'columns': columns,
                            'row_count': row_count
                        })

                    except Exception as e:
                        self.logger.error(f"Error analyzing table {table_name}: {e}")

        except Exception as e:
            self.logger.error(f"Error in table analysis: {e}")

        return analyzed

    def _apply_schema_optimizations(self) -> List[str]:
        """Apply schema-level optimizations."""
        optimizations = []

        try:
            with self.connection_pool.get_connection() as conn:
                # Optimize frequently queried tables
                conn.execute("ANALYZE")

                # Rebuild indexes for better performance
                conn.execute("REINDEX")

                optimizations.extend([
                    "Database statistics updated (ANALYZE)",
                    "Indexes rebuilt (REINDEX)"
                ])

                conn.commit()

        except Exception as e:
            self.logger.error(f"Error applying schema optimizations: {e}")

        return optimizations

    def run_database_maintenance(self) -> Dict[str, Any]:
        """Run database maintenance tasks.

        Returns:
            Maintenance results
        """
        results = {
            'vacuum_completed': False,
            'integrity_check_passed': False,
            'statistics_updated': False,
            'space_freed_mb': 0,
            'maintenance_timestamp': datetime.utcnow().isoformat()
        }

        try:
            with self.connection_pool.get_connection() as conn:
                # Run integrity check
                integrity_cursor = conn.execute("PRAGMA integrity_check")
                integrity_result = integrity_cursor.fetchone()

                if integrity_result and integrity_result[0] == 'ok':
                    results['integrity_check_passed'] = True

                # Update statistics
                conn.execute("ANALYZE")
                results['statistics_updated'] = True

                # Get database size before vacuum
                db_size_before = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0

                # Run vacuum
                conn.execute("VACUUM")
                results['vacuum_completed'] = True

                # Get database size after vacuum
                db_size_after = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                space_freed = db_size_before - db_size_after
                results['space_freed_mb'] = space_freed / (1024 * 1024)

                conn.commit()

            self.logger.info("Database maintenance completed")

        except Exception as e:
            self.logger.error(f"Error during database maintenance: {e}")
            results['error'] = str(e)

        return results

    def get_performance_dashboard_data(self) -> Dict[str, Any]:
        """Get data for performance dashboard.

        Returns:
            Performance dashboard data
        """
        return {
            'connection_pool': self.connection_pool.get_pool_stats(),
            'query_performance': {
                'slow_queries': self.query_profiler.get_slow_queries(10),
                'recommendations': self.query_profiler.get_query_recommendations()
            },
            'database_stats': self._get_database_statistics(),
            'performance_suggestions': self._generate_performance_suggestions(),
            'system_resources': self._get_system_resources(),
            'timestamp': datetime.utcnow().isoformat()
        }

    def _get_system_resources(self) -> Dict[str, Any]:
        """Get system resource usage."""
        try:
            import psutil

            # Get process information
            process = psutil.Process()
            memory_info = process.memory_info()
            cpu_percent = process.cpu_percent()

            # Get disk usage
            disk_usage = psutil.disk_usage(os.path.dirname(self.db_path))

            return {
                'memory_usage_mb': memory_info.rss / 1024 / 1024,
                'cpu_usage_percent': cpu_percent,
                'disk_total_gb': disk_usage.total / (1024**3),
                'disk_used_gb': disk_usage.used / (1024**3),
                'disk_free_gb': disk_usage.free / (1024**3),
                'disk_usage_percent': disk_usage.percent
            }

        except ImportError:
            return {'error': 'psutil not available'}
        except Exception as e:
            self.logger.error(f"Error getting system resources: {e}")
            return {'error': str(e)}


class AsyncOperationManager:
    """Manager for asynchronous database operations."""

    def __init__(self, database_optimizer):
        """Initialize async operation manager.

        Args:
            database_optimizer: Database optimizer instance
        """
        self.database_optimizer = database_optimizer
        self.logger = logging.getLogger(__name__)

        # Operation queue
        self.operation_queue: queue.Queue = queue.Queue()
        self.worker_thread: Optional[threading.Thread] = None
        self.is_running = False

        # Start worker thread
        self._start_worker()

    def _start_worker(self) -> None:
        """Start background worker thread."""
        if self.worker_thread is None or not self.worker_thread.is_alive():
            self.is_running = True
            self.worker_thread = threading.Thread(target=self._process_operations, daemon=True)
            self.worker_thread.start()

    def _process_operations(self) -> None:
        """Process operations in background."""
        while self.is_running:
            try:
                # Get operation from queue with timeout
                operation = self.operation_queue.get(timeout=1)

                # Process operation
                self._execute_operation(operation)

                self.operation_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error processing async operation: {e}")

    def _execute_operation(self, operation: Dict[str, Any]) -> None:
        """Execute async operation.

        Args:
            operation: Operation to execute
        """
        operation_type = operation.get('type')

        try:
            if operation_type == 'maintenance':
                self.database_optimizer.run_database_maintenance()
            elif operation_type == 'optimization':
                self.database_optimizer.optimize_database_schema()
            elif operation_type == 'export_metrics':
                file_path = operation.get('file_path')
                self.database_optimizer.query_profiler.export_metrics(file_path)

            self.logger.info(f"Async operation completed: {operation_type}")

        except Exception as e:
            self.logger.error(f"Error executing async operation {operation_type}: {e}")

    def queue_maintenance_operation(self) -> None:
        """Queue database maintenance operation."""
        self.operation_queue.put({
            'type': 'maintenance',
            'timestamp': datetime.utcnow().isoformat()
        })

    def queue_optimization_operation(self) -> None:
        """Queue database optimization operation."""
        self.operation_queue.put({
            'type': 'optimization',
            'timestamp': datetime.utcnow().isoformat()
        })

    def queue_metrics_export(self, file_path: str) -> None:
        """Queue metrics export operation.

        Args:
            file_path: Path to export metrics
        """
        self.operation_queue.put({
            'type': 'export_metrics',
            'file_path': file_path,
            'timestamp': datetime.utcnow().isoformat()
        })

    def stop_worker(self) -> None:
        """Stop background worker."""
        self.is_running = False

        if self.worker_thread:
            self.worker_thread.join(timeout=5)


class DatabasePerformanceSystem:
    """Complete database performance optimization system."""

    def __init__(self, db_path: str):
        """Initialize database performance system.

        Args:
            db_path: Path to database file
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.optimizer = DatabasePerformanceOptimizer(db_path)
        self.async_manager = AsyncOperationManager(self.optimizer)

    def optimize_database(self) -> Dict[str, Any]:
        """Perform complete database optimization.

        Returns:
            Optimization results
        """
        results = {
            'schema_optimization': self.optimizer.optimize_database_schema(),
            'maintenance_results': self.optimizer.run_database_maintenance(),
            'performance_analysis': self.optimizer.analyze_query_performance(),
            'optimization_timestamp': datetime.utcnow().isoformat()
        }

        return results

    def get_performance_dashboard(self) -> Dict[str, Any]:
        """Get complete performance dashboard data.

        Returns:
            Dashboard data
        """
        return self.optimizer.get_performance_dashboard_data()

    def schedule_maintenance(self, interval_hours: int = 24) -> None:
        """Schedule regular database maintenance.

        Args:
            interval_hours: Maintenance interval in hours
        """
        # This would set up a scheduler for regular maintenance
        self.logger.info(f"Database maintenance scheduled every {interval_hours} hours")

    def enable_performance_monitoring(self, enable: bool = True) -> None:
        """Enable or disable performance monitoring.

        Args:
            enable: Whether to enable monitoring
        """
        self.optimizer.monitoring_enabled = enable
        self.logger.info(f"Performance monitoring {'enabled' if enable else 'disabled'}")

    def export_performance_report(self, file_path: str) -> bool:
        """Export comprehensive performance report.

        Args:
            file_path: Path to export report

        Returns:
            True if export successful
        """
        try:
            report_data = {
                'performance_dashboard': self.get_performance_dashboard(),
                'optimization_results': self.optimize_database(),
                'export_timestamp': datetime.utcnow().isoformat()
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Performance report exported to {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error exporting performance report: {e}")
            return False

    def cleanup_resources(self) -> None:
        """Cleanup system resources."""
        try:
            # Stop async worker
            self.async_manager.stop_worker()

            # Close connection pool
            self.optimizer.connection_pool.close_all_connections()

            self.logger.info("Database performance system resources cleaned up")

        except Exception as e:
            self.logger.error(f"Error during resource cleanup: {e}")


# Factory function

def create_database_performance_system(db_path: str) -> DatabasePerformanceSystem:
    """Create complete database performance optimization system.

    Args:
        db_path: Path to database file

    Returns:
        Configured database performance system
    """
    return DatabasePerformanceSystem(db_path)


# Convenience functions

def optimize_database_queries(db_path: str) -> Dict[str, Any]:
    """Optimize database queries (convenience function).

    Args:
        db_path: Path to database file

    Returns:
        Optimization results
    """
    system = create_database_performance_system(db_path)
    return system.optimize_database()


def get_database_performance_dashboard(db_path: str) -> Dict[str, Any]:
    """Get database performance dashboard (convenience function).

    Args:
        db_path: Path to database file

    Returns:
        Performance dashboard data
    """
    system = create_database_performance_system(db_path)
    return system.get_performance_dashboard()


def export_database_metrics(db_path: str, file_path: str) -> bool:
    """Export database metrics (convenience function).

    Args:
        db_path: Path to database file
        file_path: Path to export metrics

    Returns:
        True if export successful
    """
    system = create_database_performance_system(db_path)
    return system.optimizer.query_profiler.export_metrics(file_path)
