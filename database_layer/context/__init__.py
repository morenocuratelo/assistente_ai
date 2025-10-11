# Execution Context - Fase 0
"""
Sistema contesto esecuzione per Archivista AI.

Questo modulo fornisce:
- Gestione stato applicazione globale
- Supporto contesto progetto (preparazione Fase 1)
- Context manager per operazioni sicure
- Dependency injection foundation
"""

__version__ = "0.1.0"
__author__ = "Archivista AI - Fase 0"

from .execution_context import ExecutionContext
from .context_manager import ContextManager

__all__ = [
    'ExecutionContext',
    'ContextManager'
]
