"""
UI Layer per l'architettura unificata di Archivista AI.

Questo modulo organizza tutti i componenti UI necessari per
sostituire gradualmente le 12 pagine sparse esistenti.
"""

from .components import (
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

__all__ = [
    # Base classes
    'BaseComponent',

    # Componenti principali
    'CollapsibleSidebar',
    'ModalLoginForm',
    'MinimalChatInterface',
    'ContextualFileManager',
    'HeaderBar',

    # Factory functions
    'create_collapsible_sidebar',
    'create_modal_login',
    'create_minimal_chat',
    'create_file_context_manager',
    'create_header_bar'
]
