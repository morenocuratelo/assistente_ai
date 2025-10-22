"""
Componenti UI per dashboard unificata.

Esporta tutti i componenti UI implementati nella Fase 3.
"""

from .base import (
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
    create_header_bar,
)

from .unified_dashboard import UnifiedDashboard, create_unified_dashboard

__all__ = [
    'BaseComponent',
    'UnifiedDashboard',
    'create_unified_dashboard',
    'CollapsibleSidebar',
    'create_collapsible_sidebar',
    'ModalLoginForm',
    'create_modal_login',
    'MinimalChatInterface',
    'create_minimal_chat',
    'ContextualFileManager',
    'create_file_context_manager',
    'HeaderBar',
    'create_header_bar',
]
