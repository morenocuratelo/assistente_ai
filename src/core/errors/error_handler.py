"""
Centralized error handler for Archivista AI.
Provides unified error handling, logging, and recovery mechanisms.
"""

import logging
import json
import asyncio
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from collections import defaultdict, deque
import traceback

from .error_types import (
    ArchivistaError,
    ErrorResult,
    ErrorContext,
    ErrorCategory,
    ErrorSeverity,
    create_error_context,
    classify_error,
    should_retry_error
)


class ErrorHandler:
    """Centralized error handler with logging and recovery."""

    def __init__(self):
        """Initialize error handler."""
        self.logger = logging.getLogger(__name__)
        self.error_log: deque = deque(maxlen=1000)  # Keep last 1000 errors
        self.error_stats = defaultdict(int)
        self.recovery_handlers: Dict[str, Callable] = {}
        self.notification_handlers: Dict[ErrorSeverity, List[Callable]] = defaultdict(list)

        # Setup default recovery handlers
        self._setup_default_recovery_handlers()

        # Setup default notification handlers
        self._setup_default_notification_handlers()

    def _setup_default_recovery_handlers(self) -> None:
        """Setup default recovery handlers for common errors."""
        self.register_recovery_handler(
            "database_connection",
            self._recover_database_connection
        )

        self.register_recovery_handler(
            "file_permission",
            self._recover_file_permissions
        )

        self.register_recovery_handler(
            "disk_space",
            self._recover_disk_space
        )

    def _setup_default_notification_handlers(self) -> None:
        """Setup default notification handlers."""
        # Critical errors - immediate notification
        self.register_notification_handler(
            ErrorSeverity.CRITICAL,
            self._notify_critical_error
        )

        # High severity errors - email notification
        self.register_notification_handler(
            ErrorSeverity.HIGH,
            self._notify_high_severity_error
        )

        # Medium severity errors - log only
        self.register_notification_handler(
            ErrorSeverity.MEDIUM,
            self._log_medium_severity_error
        )

    def handle_error(
        self,
        error: Exception,
        context: Optional[ErrorContext] = None,
        user_id: Optional[str] = None,
        operation: str = "unknown",
        component: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ErrorResult:
        """Handle error with full context and recovery.

        Args:
            error: Exception to handle
            context: Error context (optional)
            user_id: User ID for context
            operation: Operation being performed
            component: Component where error occurred
            metadata: Additional metadata

        Returns:
            Structured error result
        """
        # Create context if not provided
        if context is None:
            context = create_error_context(
                user_id=user_id,
                operation=operation,
                component=component,
                metadata=metadata or {}
            )

        # Convert to ArchivistaError if needed
        if not isinstance(error, ArchivistaError):
            category, severity = classify_error(error)
            archivista_error = ArchivistaError(
                message=str(error),
                error_code=f"{category.value.upper()}_ERROR",
                category=category,
                severity=severity,
                context=context,
                is_retryable=should_retry_error(error)
            )
            archivista_error.__cause__ = error
        else:
            archivista_error = error
            archivista_error.context = context

        # Create error result
        error_result = archivista_error.to_result()

        # Log error
        self._log_error(error_result)

        # Update statistics
        self._update_error_stats(error_result)

        # Attempt recovery if applicable
        self._attempt_recovery(error_result)

        # Send notifications
        self._send_notifications(error_result)

        return error_result

    async def handle_error_async(
        self,
        error: Exception,
        context: Optional[ErrorContext] = None,
        **kwargs
    ) -> ErrorResult:
        """Handle error asynchronously."""
        # Run sync handler in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.handle_error,
            error,
            context,
            **kwargs
        )

    def _log_error(self, error_result: ErrorResult) -> None:
        """Log error with structured format."""
        # Add to error log
        self.error_log.append(error_result)

        # Structured logging
        log_data = {
            'error_id': error_result.error_id,
            'category': error_result.category.value,
            'severity': error_result.severity.value,
            'operation': error_result.context.operation,
            'component': error_result.context.component,
            'user_id': error_result.context.user_id,
            'is_retryable': error_result.is_retryable,
        }

        # Log based on severity
        if error_result.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(
                f"Critical error: {error_result.message}",
                extra=log_data,
                exc_info=error_result.stack_trace
            )
        elif error_result.severity == ErrorSeverity.HIGH:
            self.logger.error(
                f"High severity error: {error_result.message}",
                extra=log_data,
                exc_info=error_result.stack_trace
            )
        elif error_result.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(
                f"Medium severity error: {error_result.message}",
                extra=log_data
            )
        else:
            self.logger.info(
                f"Low severity error: {error_result.message}",
                extra=log_data
            )

    def _update_error_stats(self, error_result: ErrorResult) -> None:
        """Update error statistics."""
        # Update counters
        self.error_stats['total'] += 1
        self.error_stats[f'category_{error_result.category.value}'] += 1
        self.error_stats[f'severity_{error_result.severity.value}'] += 1
        self.error_stats[f'component_{error_result.context.component}'] += 1

        # Track by hour for trends
        hour_key = datetime.utcnow().strftime('%Y-%m-%d-%H')
        self.error_stats[f'hourly_{hour_key}'] += 1

    def _attempt_recovery(self, error_result: ErrorResult) -> None:
        """Attempt error recovery if applicable."""
        if not error_result.is_retryable:
            return

        # Find appropriate recovery handler
        recovery_key = self._get_recovery_key(error_result)

        if recovery_key in self.recovery_handlers:
            try:
                self.recovery_handlers[recovery_key](error_result)
                self.logger.info(f"Recovery attempted for error {error_result.error_id}")
            except Exception as recovery_error:
                self.logger.error(
                    f"Recovery failed for error {error_result.error_id}: {recovery_error}"
                )

    def _get_recovery_key(self, error_result: ErrorResult) -> str:
        """Get recovery key for error result."""
        # Map error types to recovery handlers
        recovery_mapping = {
            ErrorCategory.DATABASE: "database_connection",
            ErrorCategory.FILE_SYSTEM: "file_permission",
            ErrorCategory.NETWORK: "network_connection",
            ErrorCategory.EXTERNAL_SERVICE: "external_service",
        }

        return recovery_mapping.get(error_result.category, "default")

    def _send_notifications(self, error_result: ErrorResult) -> None:
        """Send notifications for error."""
        # Get notification handlers for this severity
        handlers = self.notification_handlers.get(error_result.severity, [])

        for handler in handlers:
            try:
                handler(error_result)
            except Exception as notification_error:
                self.logger.error(
                    f"Notification failed for error {error_result.error_id}: {notification_error}"
                )

    def register_recovery_handler(self, error_type: str, handler: Callable) -> None:
        """Register recovery handler for error type.

        Args:
            error_type: Type of error to handle
            handler: Recovery function
        """
        self.recovery_handlers[error_type] = handler
        self.logger.info(f"Recovery handler registered for: {error_type}")

    def register_notification_handler(self, severity: ErrorSeverity, handler: Callable) -> None:
        """Register notification handler for severity level.

        Args:
            severity: Error severity level
            handler: Notification function
        """
        self.notification_handlers[severity].append(handler)
        self.logger.info(f"Notification handler registered for severity: {severity.value}")

    def get_error_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get error statistics for time period.

        Args:
            hours: Hours to look back

        Returns:
            Dictionary with error statistics
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        # Filter recent errors
        recent_errors = [
            error for error in self.error_log
            if error.context.timestamp >= cutoff_time
        ]

        # Calculate stats
        stats = {
            'total_errors': len(recent_errors),
            'errors_by_category': defaultdict(int),
            'errors_by_severity': defaultdict(int),
            'errors_by_component': defaultdict(int),
            'retryable_errors': 0,
            'time_range_hours': hours,
        }

        for error in recent_errors:
            stats['errors_by_category'][error.category.value] += 1
            stats['errors_by_severity'][error.severity.value] += 1
            stats['errors_by_component'][error.context.component] += 1

            if error.is_retryable:
                stats['retryable_errors'] += 1

        return dict(stats)

    def get_recent_errors(
        self,
        limit: int = 50,
        category: Optional[ErrorCategory] = None,
        severity: Optional[ErrorSeverity] = None
    ) -> List[ErrorResult]:
        """Get recent errors with optional filtering.

        Args:
            limit: Maximum number of errors to return
            category: Filter by category
            severity: Filter by severity

        Returns:
            List of recent errors
        """
        errors = list(self.error_log)

        # Apply filters
        if category:
            errors = [e for e in errors if e.category == category]

        if severity:
            errors = [e for e in errors if e.severity == severity]

        # Return most recent first
        return list(reversed(errors))[:limit]

    def create_error_response(self, error_result: ErrorResult) -> Dict[str, Any]:
        """Create standardized error response for API.

        Args:
            error_result: Error result to convert

        Returns:
            Dictionary error response
        """
        response = {
            'success': False,
            'error': {
                'id': error_result.error_id,
                'message': error_result.message,
                'category': error_result.category.value,
                'severity': error_result.severity.value,
                'timestamp': error_result.context.timestamp.isoformat(),
                'is_retryable': error_result.is_retryable,
            }
        }

        # Add recovery suggestions if available
        if error_result.recovery_suggestions:
            response['error']['recovery_suggestions'] = error_result.recovery_suggestions

        # Add context for debugging (only in debug mode)
        if self._is_debug_mode():
            response['error']['context'] = error_result.context.to_dict()
            if error_result.stack_trace:
                response['error']['stack_trace'] = error_result.stack_trace

        return response

    def _is_debug_mode(self) -> bool:
        """Check if application is in debug mode."""
        try:
            from ...config.settings import is_debug_mode
            return is_debug_mode()
        except ImportError:
            return False

    # Default recovery handlers

    def _recover_database_connection(self, error_result: ErrorResult) -> None:
        """Recovery handler for database connection errors."""
        self.logger.info(f"Attempting database connection recovery for error {error_result.error_id}")

        try:
            # Try to reconnect to database
            from ...database.connection import ConnectionManager

            # Reset connection pool
            if hasattr(ConnectionManager, 'reset_pool'):
                ConnectionManager.reset_pool()

            self.logger.info("Database connection recovery completed")

        except Exception as recovery_error:
            self.logger.error(f"Database connection recovery failed: {recovery_error}")

    def _recover_file_permissions(self, error_result: ErrorResult) -> None:
        """Recovery handler for file permission errors."""
        self.logger.info(f"Attempting file permission recovery for error {error_result.error_id}")

        try:
            # Try to fix common permission issues
            file_path = error_result.context.metadata.get('file_path')
            if file_path:
                # Attempt to make file writable
                import os
                if os.path.exists(file_path):
                    current_permissions = os.stat(file_path).st_mode
                    os.chmod(file_path, current_permissions | 0o644)

            self.logger.info("File permission recovery completed")

        except Exception as recovery_error:
            self.logger.error(f"File permission recovery failed: {recovery_error}")

    def _recover_disk_space(self, error_result: ErrorResult) -> None:
        """Recovery handler for disk space errors."""
        self.logger.info(f"Attempting disk space recovery for error {error_result.error_id}")

        try:
            # Try to free up disk space
            from ...core.utils.disk_utils import cleanup_temp_files

            freed_space = cleanup_temp_files()
            self.logger.info(f"Freed {freed_space}MB of disk space")

        except Exception as recovery_error:
            self.logger.error(f"Disk space recovery failed: {recovery_error}")

    # Default notification handlers

    def _notify_critical_error(self, error_result: ErrorResult) -> None:
        """Notification handler for critical errors."""
        self.logger.critical(
            f"CRITICAL ERROR NOTIFICATION: {error_result.message}",
            extra={
                'error_id': error_result.error_id,
                'category': error_result.category.value,
                'component': error_result.context.component,
            }
        )

        # In production, this would send alerts to monitoring systems
        # self._send_alert_to_monitoring(error_result)

    def _notify_high_severity_error(self, error_result: ErrorResult) -> None:
        """Notification handler for high severity errors."""
        self.logger.error(
            f"HIGH SEVERITY ERROR: {error_result.message}",
            extra={
                'error_id': error_result.error_id,
                'category': error_result.category.value,
                'component': error_result.context.component,
            }
        )

    def _log_medium_severity_error(self, error_result: ErrorResult) -> None:
        """Notification handler for medium severity errors."""
        self.logger.warning(
            f"Medium severity error: {error_result.message}",
            extra={
                'error_id': error_result.error_id,
                'category': error_result.category.value,
            }
        )

    def export_error_log(self, file_path: str, format: str = "json") -> bool:
        """Export error log to file.

        Args:
            file_path: Path to export file
            format: Export format (json, csv)

        Returns:
            True if export successful
        """
        try:
            if format.lower() == "json":
                # Export as JSON
                error_data = [error.to_dict() for error in self.error_log]

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(error_data, f, indent=2, ensure_ascii=False)

            elif format.lower() == "csv":
                # Export as CSV
                import csv

                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    if self.error_log:
                        fieldnames = self.error_log[0].to_dict().keys()
                        writer = csv.DictWriter(f, fieldnames=fieldnames)

                        writer.writeheader()
                        for error in self.error_log:
                            writer.writerow(error.to_dict())

            else:
                raise ValueError(f"Unsupported export format: {format}")

            self.logger.info(f"Error log exported to {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error exporting error log: {e}")
            return False

    def clear_error_log(self, older_than_hours: Optional[int] = None) -> int:
        """Clear error log with optional time filter.

        Args:
            older_than_hours: Clear only errors older than X hours

        Returns:
            Number of errors cleared
        """
        if older_than_hours is None:
            # Clear all errors
            count = len(self.error_log)
            self.error_log.clear()
            self.error_stats.clear()
        else:
            # Clear only old errors
            cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
            original_count = len(self.error_log)

            # Remove old errors (from left side of deque)
            while self.error_log and self.error_log[0].context.timestamp < cutoff_time:
                self.error_log.popleft()

            count = original_count - len(self.error_log)

        self.logger.info(f"Cleared {count} errors from log")
        return count

    def get_error_summary(self) -> Dict[str, Any]:
        """Get comprehensive error summary.

        Returns:
            Dictionary with error summary
        """
        return {
            'stats': dict(self.error_stats),
            'recent_errors_count': len(self.error_log),
            'recovery_handlers_count': len(self.recovery_handlers),
            'notification_handlers_count': sum(
                len(handlers) for handlers in self.notification_handlers.values()
            ),
            'oldest_error': (
                self.error_log[0].context.timestamp.isoformat()
                if self.error_log else None
            ),
            'newest_error': (
                self.error_log[-1].context.timestamp.isoformat()
                if self.error_log else None
            ),
        }

    def create_error_report(self, hours: int = 24) -> str:
        """Create human-readable error report.

        Args:
            hours: Hours to include in report

        Returns:
            Formatted error report string
        """
        stats = self.get_error_stats(hours)
        summary = self.get_error_summary()

        report = f"""
# Error Report - Archivista AI
Generated: {datetime.utcnow().isoformat()}

## Summary
- Total errors (24h): {stats['total_errors']}
- Retryable errors: {stats['retryable_errors']}
- Error log size: {summary['recent_errors_count']} entries

## Errors by Category
"""

        for category, count in stats['errors_by_category'].items():
            report += f"- {category}: {count}\n"

        report += "\n## Errors by Severity\n"
        for severity, count in stats['errors_by_severity'].items():
            report += f"- {severity}: {count}\n"

        report += "\n## Top Components with Errors\n"
        for component, count in sorted(
            stats['errors_by_component'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]:
            report += f"- {component}: {count}\n"

        return report


# Global error handler instance
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """Get global error handler instance."""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def handle_error(
    error: Exception,
    context: Optional[ErrorContext] = None,
    **kwargs
) -> ErrorResult:
    """Handle error using global error handler."""
    return get_error_handler().handle_error(error, context, **kwargs)


async def handle_error_async(
    error: Exception,
    context: Optional[ErrorContext] = None,
    **kwargs
) -> ErrorResult:
    """Handle error asynchronously using global error handler."""
    return await get_error_handler().handle_error_async(error, context, **kwargs)


# Convenience functions for common error handling patterns

def handle_validation_error(field: str, value: Any, reason: str) -> ErrorResult:
    """Handle validation error with proper context."""
    from .error_types import ValidationError

    error = ValidationError(
        message=f"Validation failed for {field}: {reason}",
        field=field,
        value=value
    )

    return handle_error(error, operation="validation", component="validator")


def handle_database_error(error: Exception, operation: str, table: str = None) -> ErrorResult:
    """Handle database error with proper context."""
    from .error_types import DatabaseError

    db_error = DatabaseError(
        message=str(error),
        operation=operation,
        table=table
    )

    return handle_error(db_error, operation=operation, component="database")


def handle_file_error(error: Exception, file_path: str, operation: str) -> ErrorResult:
    """Handle file system error with proper context."""
    from .error_types import FileSystemError

    file_error = FileSystemError(
        message=str(error),
        file_path=file_path,
        operation=operation
    )

    return handle_error(file_error, operation=operation, component="filesystem")


def handle_ai_error(error: Exception, model: str = None, operation: str = "ai_operation") -> ErrorResult:
    """Handle AI service error with proper context."""
    from .error_types import AIServiceError

    ai_error = AIServiceError(
        message=str(error),
        model=model,
        operation=operation
    )

    return handle_error(ai_error, operation=operation, component="ai_service")


# Decorator for automatic error handling

def handle_errors(
    operation: str = "unknown",
    component: str = "unknown",
    reraise: bool = False,
    log_success: bool = False
):
    """Decorator for automatic error handling.

    Args:
        operation: Operation name for context
        component: Component name for context
        reraise: Whether to reraise exception after handling
        log_success: Whether to log successful operations
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)

                if log_success:
                    get_error_handler().logger.info(
                        f"Operation completed successfully: {operation}",
                        extra={'operation': operation, 'component': component}
                    )

                return result

            except Exception as error:
                error_result = handle_error(
                    error,
                    operation=operation,
                    component=component
                )

                if reraise:
                    raise error

                return None

        return wrapper
    return decorator


# Async version of error handling decorator

def handle_errors_async(
    operation: str = "unknown",
    component: str = "unknown",
    reraise: bool = False,
    log_success: bool = False
):
    """Async decorator for automatic error handling."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)

                if log_success:
                    get_error_handler().logger.info(
                        f"Async operation completed successfully: {operation}",
                        extra={'operation': operation, 'component': component}
                    )

                return result

            except Exception as error:
                error_result = await handle_error_async(
                    error,
                    operation=operation,
                    component=component
                )

                if reraise:
                    raise error

                return None

        return wrapper
    return decorator
