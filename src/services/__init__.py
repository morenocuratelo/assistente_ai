"""
Service layer per logica business.

Fornisce servizi per operazioni business sui dati.
"""

from .base_service import BaseService
from .document_service import DocumentService
from .user_service import UserService
from .chat_service import ChatService
from .project_service import ProjectService
from .career_service import CareerService

# Performance optimization
from ..core.performance.optimization import (
    performance_optimizer,
    cache_result,
    measure_performance,
    optimize_memory,
    get_system_performance,
    preload_common_data
)

# Import servizi esistenti se presenti
try:
    from .service_manager import ServiceManager
    from .service_manager import service_manager, get_service_manager, initialize_services, get_service_status
    _HAS_EXISTING_SERVICES = True
except ImportError:
    _HAS_EXISTING_SERVICES = False

__all__ = [
    'BaseService',
    'DocumentService',
    'UserService',
    'ChatService',
    'ProjectService',
    'CareerService',
    'performance_optimizer',
    'cache_result',
    'measure_performance',
    'optimize_memory',
    'get_system_performance',
    'preload_common_data'
]

# Aggiungi servizi esistenti se presenti
if _HAS_EXISTING_SERVICES:
    __all__.extend([
        'ServiceManager',
        'service_manager',
        'get_service_manager',
        'initialize_services',
        'get_service_status'
    ])
