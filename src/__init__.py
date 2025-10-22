"""
Architettura unificata di Archivista AI.

Questo modulo principale organizza tutti i componenti necessari
per sostituire gradualmente le 12 pagine sparse esistenti.
"""

# Versione architettura unificata
__version__ = "1.0.0"
__author__ = "Archivista AI Team"

# Import componenti principali
from .ui import (
    BaseComponent,
    CollapsibleSidebar,
    ModalLoginForm,
    MinimalChatInterface,
    ContextualFileManager,
    HeaderBar,
    create_collapsible_sidebar,
    create_modal_login,
    create_minimal_chat,
    create_file_context_manager,
    create_header_bar
)

from .services import (
    # Service layer Fase 2
    BaseService,
    DocumentService,
    UserService,
    ChatService,

    # Servizi esistenti
    ServiceManager,
    service_manager,
    get_service_manager,
    initialize_services,
    get_service_status
)

__all__ = [
    # Version info
    '__version__',
    '__author__',

    # UI Components
    'BaseComponent',
    'CollapsibleSidebar',
    'ModalLoginForm',
    'MinimalChatInterface',
    'ContextualFileManager',
    'HeaderBar',

    # UI Factories
    'create_collapsible_sidebar',
    'create_modal_login',
    'create_minimal_chat',
    'create_file_context_manager',
    'create_header_bar',

    # Services Fase 2
    'BaseService',
    'DocumentService',
    'UserService',
    'ChatService',

    # Servizi esistenti
    'ServiceManager',
    'service_manager',
    'get_service_manager',
    'initialize_services',
    'get_service_status'
]
