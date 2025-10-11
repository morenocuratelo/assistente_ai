# Configuration Layer - Fase 0
"""
Sistema configurazione unificato per Archivista AI.

Questo modulo fornisce:
- Configurazione centralizzata percorsi database
- Supporto multi-progetto (preparazione Fase 1)
- Gestione environment-based configuration
- Factory pattern per istanze database
"""

__version__ = "0.1.0"
__author__ = "Archivista AI - Fase 0"

from .database_config import DatabaseConfig
from .project_config import ProjectConfig

__all__ = [
    'DatabaseConfig',
    'ProjectConfig'
]
