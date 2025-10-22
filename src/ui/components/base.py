"""
Componenti base per l'architettura unificata di Archivista AI.

Questo modulo fornisce componenti riutilizzabili per costruire
l'interfaccia unificata che sostituirà le 12 pagine sparse.
"""

import streamlit as st
from typing import Dict, List, Optional, Any, Callable
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class BaseComponent(ABC):
    """Classe base per tutti i componenti UI."""

    def __init__(self, component_id: str, title: str = "", **kwargs):
        self.component_id = component_id
        self.title = title
        self.kwargs = kwargs
        self.logger = logging.getLogger(f"{__name__}.{component_id}")

    @abstractmethod
    def render(self) -> None:
        """Render del componente."""
        pass

    def get_state(self, key: str, default: Any = None) -> Any:
        """Ottieni stato componente dal session state."""
        return st.session_state.get(f"{self.component_id}_{key}", default)

    def set_state(self, key: str, value: Any) -> None:
        """Imposta stato componente nel session state."""
        st.session_state[f"{self.component_id}_{key}"] = value

    def clear_state(self) -> None:
        """Pulisce tutto lo stato del componente."""
        keys_to_remove = [
            k for k in st.session_state.keys()
            if k.startswith(f"{self.component_id}_")
        ]
        for key in keys_to_remove:
            del st.session_state[key]

class CollapsibleSidebar(BaseComponent):
    """Sidebar collassabile intelligente per navigazione principale."""

    def __init__(self):
        super().__init__("collapsible_sidebar", "Navigazione")
        self.is_collapsed = self.get_state("is_collapsed", True)
        self.current_page = self.get_state("current_page", "chat")

        # Definizione menu navigazione
        self.menu_items = [
            {"id": "chat", "label": "💬 Chat", "icon": "💬", "description": "Chatta con i tuoi documenti"},
            {"id": "archive", "label": "🗂️ Archivio", "icon": "🗂️", "description": "Esplora e gestisci i file"},
            {"id": "dashboard", "label": "📊 Dashboard", "icon": "📊", "description": "Visualizza statistiche"},
            {"id": "projects", "label": "📚 Projects", "icon": "📚", "description": "Gestione progetti"},
            {"id": "carriera", "label": "🎓 Carriera", "icon": "🎓", "description": "Planner accademico"},
            {"id": "grafo", "label": "🧠 Grafo", "icon": "🧠", "description": "Visualizza connessioni"},
            {"id": "settings", "label": "⚙️ Impostazioni", "icon": "⚙️", "description": "Configurazioni"}
        ]

    def render(self) -> None:
        """Render della sidebar collassabile."""
        with st.sidebar:
            # Header sidebar
            if not self.is_collapsed:
                st.title(self.title)

                # Toggle collapse button
                if st.button("◀️ Comprimi", key="collapse_sidebar"):
                    self.is_collapsed = True
                    self.set_state("is_collapsed", True)
                    st.rerun()
            else:
                # Show expand button when collapsed
                if st.button("▶️", key="expand_sidebar", help="Espandi navigazione"):
                    self.is_collapsed = False
                    self.set_state("is_collapsed", False)
                    st.rerun()

            if not self.is_collapsed:
                st.markdown("---")

                # Menu items
                for item in self.menu_items:
                    is_active = self.current_page == item["id"]

                    # Button styling based on active state
                    button_type = "primary" if is_active else "secondary"

                    if st.button(
                        f"{item['icon']} {item['label']}" if not self.is_collapsed else item['icon'],
                        key=f"nav_{item['id']}",
                        use_container_width=True,
                        type=button_type,
                        help=item['description']
                    ):
                        self.current_page = item["id"]
                        self.set_state("current_page", item["id"])
                        st.rerun()

                # Status section (quando espansa)
                st.markdown("---")
                st.markdown("### 📊 Stato")
                st.info("✅ Sistema operativo")

                # Quick actions (quando espansa)
                st.markdown("### ⚡ Azioni")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📤 Nuovo", key="quick_new", use_container_width=True):
                        st.session_state.show_document_creator = True
                with col2:
                    if st.button("🔍 Cerca", key="quick_search", use_container_width=True):
                        st.session_state.show_global_search = True

    def get_current_page(self) -> str:
        """Restituisce la pagina attualmente selezionata."""
        return self.current_page

class ModalLoginForm(BaseComponent):
    """Form di login in modal popup."""

    def __init__(self):
        super().__init__("modal_login", "Login")
        self.show_modal = self.get_state("show_modal", False)
        self.is_login_mode = self.get_state("is_login_mode", True)

    def render(self) -> None:
        """Render del modal login."""
        if self.show_modal:
            @st.dialog("🔐 Accesso Archivista AI")
            def login_dialog():
                # Toggle tra login e registrazione
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔑 Login", type="primary" if self.is_login_mode else "secondary",
                               use_container_width=True):
                        self.is_login_mode = True
                        self.set_state("is_login_mode", True)
                        st.rerun()
                with col2:
                    if st.button("📝 Registrazione", type="primary" if not self.is_login_mode else "secondary",
                               use_container_width=True):
                        self.is_login_mode = False
                        self.set_state("is_login_mode", False)
                        st.rerun()

                st.markdown("---")

                if self.is_login_mode:
                    self._render_login_form()
                else:
                    self._render_register_form()

            login_dialog()

    def _render_login_form(self) -> None:
        """Render form di login."""
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Inserisci username")
            password = st.text_input("Password", type="password", placeholder="Inserisci password")

            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("🔑 Accedi", type="primary", use_container_width=True):
                    if self._authenticate_user(username, password):
                        self.show_modal = False
                        self.set_state("show_modal", False)
                        st.success("✅ Login effettuato con successo!")
                        st.rerun()
                    else:
                        st.error("❌ Username o password non validi")

            with col2:
                if st.form_submit_button("❌ Annulla", use_container_width=True):
                    self.show_modal = False
                    self.set_state("show_modal", False)
                    st.rerun()

    def _render_register_form(self) -> None:
        """Render form di registrazione."""
        with st.form("register_form"):
            new_username = st.text_input("Username*", placeholder="Scegli username")
            new_password = st.text_input("Password*", type="password", placeholder="Scegli password")
            confirm_password = st.text_input("Conferma Password*", type="password", placeholder="Ripeti password")

            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("📝 Registrati", type="primary", use_container_width=True):
                    if self._register_user(new_username, new_password, confirm_password):
                        st.success("✅ Registrazione completata!")
                        st.rerun()

            with col2:
                if st.form_submit_button("❌ Annulla", use_container_width=True):
                    self.show_modal = False
                    self.set_state("show_modal", False)
                    st.rerun()

    def _authenticate_user(self, username: str, password: str) -> bool:
        """Autentica utente (simulazione)."""
        try:
            from file_utils import authenticate_user
            user = authenticate_user(username, password)
            if user:
                st.session_state.user_id = user['id']
                st.session_state.username = user['username']
                return True
            return False
        except Exception as e:
            self.logger.error(f"Errore autenticazione: {e}")
            return False

    def _register_user(self, username: str, password: str, confirm_password: str) -> bool:
        """Registra nuovo utente (simulazione)."""
        try:
            if not username or not password:
                st.error("❌ Tutti i campi sono obbligatori")
                return False

            if password != confirm_password:
                st.error("❌ Le password non corrispondono")
                return False

            from file_utils import create_user
            create_user(username, password)

            # Auto-login dopo registrazione
            if self._authenticate_user(username, password):
                self.show_modal = False
                self.set_state("show_modal", False)
                return True

            return False
        except Exception as e:
            st.error(f"❌ Errore registrazione: {e}")
            return False

    def show_login_modal(self) -> None:
        """Mostra il modal di login."""
        self.show_modal = True
        self.set_state("show_modal", True)

class MinimalChatInterface(BaseComponent):
    """Interfaccia chat minimalista centrale."""

    def __init__(self):
        super().__init__("minimal_chat", "Chat")
        self.messages = self.get_state("messages", [
            {"role": "assistant", "content": "Ciao! Sono Archivista AI. Come posso aiutarti oggi?"}
        ])
        self.waiting_for_response = self.get_state("waiting_for_response", False)

    def render(self) -> None:
        """Render dell'interfaccia chat minimalista."""
        # Container chat principale
        chat_container = st.container()

        with chat_container:
            # Header chat
            st.markdown("### 💬 Chat con l'Archivio")

            # Area messaggi
            st.markdown("#### 💭 Conversazione")

            # Mostra messaggi esistenti
            for message in self.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            # Input chat
            if not self.waiting_for_response:
                user_input = st.chat_input(
                    "Fai una domanda sui tuoi documenti...",
                    key="main_chat_input"
                )

                if user_input:
                    self._handle_user_message(user_input)

            # Pulsante aggiungi file accanto all'input
            st.markdown("---")
            col1, col2 = st.columns([0.1, 0.9])

            with col1:
                if st.button("➕", key="add_file_button", help="Aggiungi file come contesto"):
                    st.session_state.show_file_context_menu = True

            with col2:
                if st.session_state.get("show_file_context_menu", False):
                    self._render_file_context_menu()

    def _handle_user_message(self, message: str) -> None:
        """Gestisce messaggio utente."""
        # Aggiungi messaggio utente
        self.messages.append({"role": "user", "content": message})
        self.set_state("messages", self.messages)

        # Simula risposta AI (da sostituire con logica reale)
        self.waiting_for_response = True
        self.set_state("waiting_for_response", True)

        # Qui andrebbe la logica di generazione risposta
        # Per ora simuliamo una risposta dopo un delay
        import time
        time.sleep(1)

        response = f"Grazie per il tuo messaggio: '{message}'. Questa è una risposta simulata. La logica AI verrà integrata nella prossima fase."
        self.messages.append({"role": "assistant", "content": response})
        self.set_state("messages", self.messages)

        self.waiting_for_response = False
        self.set_state("waiting_for_response", False)

        st.rerun()

    def _render_file_context_menu(self) -> None:
        """Render menu contesto file."""
        st.markdown("**📎 Aggiungi File come Contesto**")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📄 Carica File", key="upload_file"):
                st.info("🚀 Caricamento file da implementare")

        with col2:
            if st.button("📂 Dall'Archivio", key="from_archive"):
                st.info("🚀 Selezione da archivio da implementare")

        with col3:
            if st.button("🔗 Incolla URL", key="paste_url"):
                st.info("🚀 Incolla URL da implementare")

        if st.button("❌ Chiudi Menu", key="close_file_menu"):
            st.session_state.show_file_context_menu = False
            st.rerun()

class ContextualFileManager(BaseComponent):
    """Gestore file contesto per chat."""

    def __init__(self):
        super().__init__("file_context_manager", "File Contesto")
        self.max_context_files = 5  # Limite definito nel blueprint
        self.context_files = self.get_state("context_files", [])

    def render(self) -> None:
        """Render del gestore file contesto."""
        if not self.context_files:
            st.info("📭 Nessun file nel contesto. Usa il pulsante + per aggiungere documenti.")
            return

        st.markdown(f"### 📋 File nel Contesto ({len(self.context_files)}/{self.max_context_files})")

        for i, file_info in enumerate(self.context_files):
            col1, col2, col3 = st.columns([0.7, 0.15, 0.15])

            with col1:
                st.markdown(f"📄 **{file_info.get('name', 'Documento')}**")
                st.caption(f"Tipo: {file_info.get('type', 'N/A')} | Dimensione: {file_info.get('size', 'N/A')}")

            with col2:
                if st.button("👁️", key=f"view_file_{i}", help="Visualizza"):
                    self._show_file_preview(file_info)

            with col3:
                if st.button("🗑️", key=f"remove_file_{i}", help="Rimuovi dal contesto"):
                    self.context_files.pop(i)
                    self.set_state("context_files", self.context_files)
                    st.rerun()

    def add_context_file(self, file_info: Dict[str, Any]) -> bool:
        """Aggiunge file al contesto."""
        if len(self.context_files) >= self.max_context_files:
            st.error(f"❌ Limite massimo di {self.max_context_files} file nel contesto raggiunto")
            return False

        self.context_files.append(file_info)
        self.set_state("context_files", self.context_files)
        return True

    def _show_file_preview(self, file_info: Dict[str, Any]) -> None:
        """Mostra anteprima file."""
        st.info(f"📄 **Anteprima: {file_info.get('name', 'Documento')}**")
        st.json(file_info)  # Mostra metadati file

class HeaderBar(BaseComponent):
    """Barra header principale con controlli globali."""

    def __init__(self):
        super().__init__("header_bar", "Header")
        self.show_login_modal = self.get_state("show_login_modal", False)

    def render(self) -> None:
        """Render header principale."""
        col1, col2, col3 = st.columns([0.7, 0.15, 0.15])

        with col1:
            st.title("📚 Archivista AI")

        with col2:
            # Placeholder per notifiche future
            pass

        with col3:
            if st.button("🔐 Login", key="header_login", type="secondary"):
                self.show_login_modal = True
                self.set_state("show_login_modal", True)
                st.rerun()

        # Render modal login se richiesto
        if self.show_login_modal:
            login_modal = ModalLoginForm()
            login_modal.render()

# Factory functions per creare componenti

def create_collapsible_sidebar() -> CollapsibleSidebar:
    """Factory per creare sidebar collassabile."""
    return CollapsibleSidebar()

def create_modal_login() -> ModalLoginForm:
    """Factory per creare modal login."""
    return ModalLoginForm()

def create_minimal_chat() -> MinimalChatInterface:
    """Factory per creare interfaccia chat minimalista."""
    return MinimalChatInterface()

def create_file_context_manager() -> ContextualFileManager:
    """Factory per creare gestore file contesto."""
    return ContextualFileManager()

def create_header_bar() -> HeaderBar:
    """Factory per creare header principale."""
    return HeaderBar()

# Factory e configurazione componenti

class ComponentConfig:
    """Configurazione componente."""

    def __init__(self, **kwargs):
        self.config = kwargs

    def get(self, key: str, default: Any = None) -> Any:
        """Ottieni valore configurazione."""
        return self.config.get(key, default)

class ComponentFactory:
    """Factory per creazione componenti."""

    @staticmethod
    def create_component(component_type: str, config: ComponentConfig = None, **kwargs) -> BaseComponent:
        """Crea componente del tipo specificato."""
        if config is None:
            config = ComponentConfig()

        if component_type == "sidebar":
            return CollapsibleSidebar()
        elif component_type == "login":
            return ModalLoginForm()
        elif component_type == "chat":
            return MinimalChatInterface()
        elif component_type == "file_manager":
            return ContextualFileManager()
        elif component_type == "header":
            return HeaderBar()
        else:
            raise ValueError(f"Tipo componente sconosciuto: {component_type}")

# Export componenti principali
__all__ = [
    'BaseComponent',
    'CollapsibleSidebar',
    'ModalLoginForm',
    'MinimalChatInterface',
    'ContextualFileManager',
    'HeaderBar',
    'ComponentFactory',
    'ComponentConfig',
    'create_collapsible_sidebar',
    'create_modal_login',
    'create_minimal_chat',
    'create_file_context_manager',
    'create_header_bar'
]
