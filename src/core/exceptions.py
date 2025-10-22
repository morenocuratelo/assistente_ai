"""Minimal custom exceptions module used by unit tests.

This module provides a small set of exceptions referenced by tests. It is
kept intentionally small; behavior can be expanded as needed.
"""
from typing import Optional


class DocumentProcessingError(Exception):
    def __init__(self, message: str, file_path: Optional[str] = None):
        super().__init__(message)
        self.file_path = file_path


class ConfigurationError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class ServiceError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
