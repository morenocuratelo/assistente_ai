"""
Dashboard unificata principale.

Componente principale che integra tutti i servizi della Fase 2
in un'interfaccia unificata con navigazione a tab.
"""

import streamlit as st
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base import BaseComponent
from ..pages.base_page import BasePage

logger = logging.getLogger(__name__)

# Expose service and repository symbols at module level so tests can patch them
try:
    # Try to eagerly import so normal runtime works and names are available
    from src.services import DocumentService, UserService, ChatService
    from src.database.repositories import DocumentRepository, UserRepository, ChatRepository
except Exception:
    # If imports fail at module import time (tests may patch these names),
    # initialize placeholders that can be replaced later or patched by tests.
    DocumentService = None  # type: ignore
    UserService = None  # type: ignore
    ChatService = None  # type: ignore
    DocumentRepository = None  # type: ignore
    UserRepository = None  # type: ignore
    ChatRepository = None  # type: ignore

class UnifiedDashboard(BaseComponent):
    """Dashboard unificata principale."""

    def __init__(self):
        """Inizializza dashboard unificata."""
        # BaseComponent requires a component_id and optional title
        super().__init__(component_id="unified_dashboard", title="Unified Dashboard")
        self.active_tab = "chat"
        self.sidebar_collapsed = False

        # Inizializza servizi
        self._initialize_services()

    def _initialize_services(self):
        """Inizializza servizi necessari."""
        try:
            # Allow tests to patch module-level names (DocumentService etc.). If the
            # names are not yet available (None), import them now and bind to globals
            global DocumentService, UserService, ChatService
            global DocumentRepository, UserRepository, ChatRepository

            if DocumentService is None or UserService is None or ChatService is None or \
               DocumentRepository is None or UserRepository is None or ChatRepository is None:
                from src.services import DocumentService as _DocumentService, \
                    UserService as _UserService, ChatService as _ChatService
                from src.database.repositories import DocumentRepository as _DocumentRepository, \
                    UserRepository as _UserRepository, ChatRepository as _ChatRepository

                DocumentService = _DocumentService
                UserService = _UserService
                ChatService = _ChatService
                DocumentRepository = _DocumentRepository
                UserRepository = _UserRepository
                ChatRepository = _ChatRepository

            # Usa database esistente o crea connessione di test
            db_path = "db_memoria/metadata.sqlite"

            # Instantiate services using the (possibly patched) classes
            self.document_service = DocumentService(DocumentRepository(db_path))
            self.user_service = UserService(UserRepository(db_path))
            self.chat_service = ChatService(ChatRepository(db_path))

            logger.info("✅ Servizi inizializzati nella dashboard")

        except Exception as e:
            logger.error(f"❌ Errore inizializzazione servizi: {e}")
            st.error(f"Errore inizializzazione servizi: {e}")

    def render_header(self):
        """Render header principale ottimizzato."""
        # Layout header più efficiente
        header_cols = st.columns([0.15, 0.7, 0.15])

        with header_cols[0]:
            # Menu toggle con stato visuale
            menu_icon = "☰" if not self.sidebar_collapsed else "✕"
            if st.button(f"🎯 {menu_icon}", key="menu_toggle", help="Toggle navigazione"):
                self.sidebar_collapsed = not self.sidebar_collapsed
                st.rerun()

        with header_cols[1]:
            # Titolo con sottotitolo dinamico basato sul tab attivo
            tab_titles = {
                "chat": "💬 Chat con AI",
                "archive": "🗂️ Archivio Documenti",
                "dashboard": "📊 Dashboard Statistiche",
                "projects": "📚 Gestione Progetti",
                "career": "🎓 Carriera Accademica",
                "graph": "🧠 Grafo Conoscenza",
                "settings": "⚙️ Impostazioni"
            }

            current_title = tab_titles.get(self.active_tab, "🎯 Archivista AI")
            st.title(current_title)

            # Status bar con informazioni contestuali
            status_info = self._get_status_info()
            if status_info:
                st.caption(f"📍 {status_info}")

        with header_cols[2]:
            # Pulsante wizard contestuale
            if st.button("🎯 Wizard", key="contextual_wizard", help="Avvia wizard contestuale"):
                st.session_state.show_contextual_wizard = True

    def _get_status_info(self):
        """Ottieni informazioni di stato contestuali."""
        try:
            if self.active_tab == "archive":
                # Mostra numero documenti nell'archivio
                result = self.document_service.get_document_stats()
                if result.success:
                    return f"{result.data.get('total_documents', 0)} documenti disponibili"
            elif self.active_tab == "chat":
                # Mostra stato contesto AI
                ai_active = st.session_state.get('ai_context_active', False)
                context_files = len(st.session_state.get('context_files', []))
                return f"AI: {'Attivo' if ai_active else 'Inattivo'} | File: {context_files}/5"
            elif self.active_tab == "dashboard":
                # Mostra ultimo aggiornamento
                return "Aggiornato in tempo reale"
        except Exception:
            pass
        return None

    def _show_quick_stats(self):
        """Mostra statistiche rapide."""
        try:
            stats = self.document_service.get_document_stats()
            if stats.success:
                st.info(f"📊 **Statistiche Rapide:** {stats.data.get('total_documents', 0)} documenti, {len(stats.data.get('categories', {}))} categorie")
        except Exception as e:
            st.error(f"Errore statistiche rapide: {e}")

        # Nota: le azioni rapide vengono renderizzate nel header tramite render_header();
        # qui lasciamo solo la visualizzazione delle statistiche.

    def _render_quick_actions(self):
        """Render azioni rapide contestuali."""
        # Azioni rapide basate sul tab attivo
        if self.active_tab == "chat":
            if st.button("🤖 AI", key="ai_quick", help="Contesto AI"):
                st.session_state.ai_context_active = not st.session_state.get('ai_context_active', False)
        elif self.active_tab == "archive":
            if st.button("📊 Stats", key="archive_quick", help="Statistiche rapide"):
                self._show_quick_stats()
        elif self.active_tab == "dashboard":
            if st.button("🔄 Refresh", key="refresh_quick", help="Aggiorna dati"):
                st.rerun()
        else:
            # Login sempre disponibile
            if st.button("🔐 Login", key="header_login"):
                st.session_state.show_login = True

    def render_sidebar(self):
        """Render sidebar di navigazione ottimizzata."""
        if not self.sidebar_collapsed:
            with st.sidebar:
                st.header("🎯 Navigazione")

                # Tab buttons con descrizioni migliorate
                tabs = {
                    "chat": ("💬", "Chat", "Chatta con i tuoi documenti"),
                    "archive": ("🗂️", "Archivio", "Esplora e gestisci i file"),
                    "dashboard": ("📊", "Dashboard", "Visualizza statistiche"),
                    "projects": ("📚", "Projects", "Gestione progetti"),
                    "career": ("🎓", "Carriera", "Gestione corsi e attività accademiche"),
                    "graph": ("🧠", "Grafo", "Visualizza connessioni"),
                    "settings": ("⚙️", "Impostazioni", "Configurazioni")
                }

                for tab_id, (icon, label, description) in tabs.items():
                    is_active = self.active_tab == tab_id
                    button_type = "primary" if is_active else "secondary"

                    if st.button(
                        f"{icon} {label}",
                        key=f"tab_{tab_id}",
                        type=button_type,
                        use_container_width=True,
                        help=description
                    ):
                        self.active_tab = tab_id
                        st.rerun()

                # Sezione stato sistema
                st.markdown("---")
                st.markdown("### 📊 Stato Sistema")
                try:
                    stats = self.document_service.get_document_stats()
                    if stats.success:
                        st.metric("📄 Documenti", stats.data.get('total_documents', 0))
                        st.metric("📂 Categorie", len(stats.data.get('categories', {})))
                except:
                    st.info("Sistema operativo")

                # Azioni rapide sidebar
                st.markdown("### ⚡ Azioni")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📤 Nuovo", key="sidebar_new", use_container_width=True):
                        st.session_state.show_document_creator = True
                with col2:
                    if st.button("🔍 Cerca", key="sidebar_search", use_container_width=True):
                        st.session_state.show_global_search = True

    def render_file_context_manager(self):
        """Render gestione file contesto ottimizzata."""
        # Layout più compatto e informativo
        context_cols = st.columns([0.2, 0.2, 0.6])

        with context_cols[0]:
            # Pulsante aggiungi file con stato visuale
            file_count = len(st.session_state.get('context_files', []))
            file_icon = "➕" if file_count < 5 else "✅"
            if st.button(f"{file_icon} File", key="add_file_btn", help=f"Aggiungi file al contesto ({file_count}/5)"):
                st.session_state.show_file_manager = True

        with context_cols[1]:
            # Stato AI con toggle visuale
            ai_active = st.session_state.get('ai_context_active', False)
            ai_icon = "🤖" if ai_active else "⚪"
            ai_help = "Contesto AI attivo" if ai_active else "Contesto AI inattivo"
            if st.button(f"{ai_icon} AI", key="ai_context_btn", help=ai_help):
                st.session_state.ai_context_active = not ai_active
                st.rerun()

        with context_cols[2]:
            # Info contesto migliorata
            if file_count > 0:
                files_text = ", ".join([f[:15]+"..." for f in st.session_state.context_files[:2]])
                if file_count > 2:
                    files_text += f" +{file_count-2} altri"
                st.caption(f"📎 {files_text}")
            else:
                st.caption("📎 Nessun file nel contesto")

    def render_chat_tab(self):
        """Render tab chat principale ottimizzato."""
        st.header("💬 Chat con AI")

        # Info contesto chat
        col1, col2 = st.columns([3, 1])
        with col1:
            ai_active = st.session_state.get('ai_context_active', False)
            file_count = len(st.session_state.get('context_files', []))
            st.caption(f"🤖 AI: {'Attiva' if ai_active else 'Inattiva'} | 📎 File contesto: {file_count}/5")
        with col2:
            if st.button("⚙️ Chat Settings", key="chat_settings"):
                st.session_state.show_chat_settings = True

        # Chat interface migliorata
        chat_container = st.container()
        with chat_container:
            # Area messaggi con altezza dinamica
            messages_area = st.container(height=450)

            with messages_area:
                if 'chat_messages' not in st.session_state:
                    st.session_state.chat_messages = []

                # Messaggio di benvenuto se nessuna conversazione
                if not st.session_state.chat_messages:
                    st.info("💭 Inizia una conversazione! Carica documenti nel contesto per domande più specifiche.")

                # Mostra messaggi esistenti
                for msg in st.session_state.chat_messages:
                    with st.chat_message(msg["role"]):
                        st.write(msg["content"])

                        # Mostra timestamp per debug (rimuovere in produzione)
                        if st.session_state.get('show_timestamps', False):
                            st.caption(f"🕒 {msg.get('timestamp', 'N/A')}")

            # Input messaggio con azioni aggiuntive
            col1, col2 = st.columns([4, 1])
            with col1:
                prompt = st.chat_input("Scrivi un messaggio...", key="main_chat_input")
            with col2:
                if st.button("📤 Invia", key="send_message", type="primary"):
                    if prompt:
                        self._handle_chat_message(prompt)
                    else:
                        st.warning("Digita un messaggio prima di inviare")

            # Se utente ha scritto qualcosa, processalo
            if prompt:
                self._handle_chat_message(prompt)

    def _handle_chat_message(self, message: str):
        """Gestisce messaggio chat utente."""
        # Aggiungi messaggio utente
        if 'chat_messages' not in st.session_state:
            st.session_state.chat_messages = []

        st.session_state.chat_messages.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })

        # Simula risposta AI (placeholder per futura integrazione)
        with st.chat_message("assistant"):
            with st.spinner("🤖 AI sta pensando..."):
                # Qui andrebbe la logica di generazione risposta
                import time
                time.sleep(1)

                # Risposta contestuale basata su file nel contesto
                file_count = len(st.session_state.get('context_files', []))
                ai_active = st.session_state.get('ai_context_active', False)

                if ai_active and file_count > 0:
                    response = f"✅ Analizzo i tuoi {file_count} documenti nel contesto: '{message[:50]}...'"
                else:
                    response = f"✅ Ricevuto: '{message[:50]}...'. Carica documenti per risposte più specifiche!"

            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now().isoformat()
            })

        st.rerun()

    def render_archive_tab(self):
        """Render tab archivio documenti con ExplorationModal."""
        st.header("🗂️ Archivio Documenti")

        # Inizializza ExplorationModal se non esiste
        if 'exploration_modal' not in st.session_state:
            try:
                from .exploration_modal import create_exploration_modal
                st.session_state.exploration_modal = create_exploration_modal(
                    on_document_select=self._on_document_select
                )
            except Exception as e:
                st.error(f"Errore inizializzazione ExplorationModal: {e}")
                return

        exploration_modal = st.session_state.exploration_modal

        # Toolbar archivio
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            search_query = st.text_input("🔍 Cerca documenti", key="archive_search")

        with col2:
            category_filter = st.selectbox(
                "📂 Categoria",
                ["Tutte", "TEST/001", "INTEGRATION/TEST", "Altro"],
                key="category_filter"
            )

        with col3:
            if st.button("📊 Statistiche", key="archive_stats"):
                self._show_archive_stats()

        with col4:
            # Pulsante esplorazione avanzata
            if st.button("🔍 Esplora", type="secondary", key="explore_docs"):
                exploration_modal.show_modal()
                st.rerun()

        # Render modale esplorazione
        exploration_modal.render_modal()

        # Contenuto archivio
        try:
            # Recupera documenti usando il servizio
            if category_filter != "Tutte":
                result = self.document_service.get_documents_by_category(category_filter)
            else:
                result = self.document_service.get_all()

            if result.success:
                documents = result.data

                if documents:
                    st.subheader(f"📋 Documenti trovati: {len(documents)}")

                    for doc in documents[:10]:  # Mostra primi 10
                        with st.expander(f"📄 {doc.get('file_name', 'Senza nome')}"):
                            col1, col2 = st.columns([3, 1])

                            with col1:
                                st.write(f"**Titolo:** {doc.get('title', 'N/A')}")
                                st.write(f"**Autori:** {doc.get('authors', 'N/A')}")
                                st.write(f"**Categoria:** {doc.get('category_id', 'N/A')}")

                            with col2:
                                if st.button("👁️ Visualizza", key=f"view_{doc.get('file_name')}"):
                                    st.info(f"Visualizzazione documento: {doc.get('file_name')}")
                else:
                    st.info("📭 Nessun documento trovato")
            else:
                st.error(f"Errore recupero documenti: {result.message}")

        except Exception as e:
            st.error(f"Errore archivio: {e}")

        # Debug info per sviluppo
        if st.session_state.get('debug_mode', False):
            with st.expander("🔧 Debug Archive"):
                st.write("**ExplorationModal Status:**")
                st.write(f"Modal Available: {exploration_modal is not None}")
                st.write(f"Selected Document: {exploration_modal.get_selected_document().get('title') if exploration_modal.get_selected_document() else 'None'}")

    def render_dashboard_tab(self):
        """Render tab dashboard con statistiche ottimizzato."""
        st.header("📊 Dashboard Statistiche")

        # Controlli dashboard
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.caption("📈 Panoramica sistema in tempo reale")
        with col2:
            if st.button("🔄 Aggiorna", key="dashboard_refresh"):
                st.rerun()
        with col3:
            if st.button("📥 Esporta", key="dashboard_export"):
                st.info("Esportazione dati...")

        st.markdown("---")

        # Statistiche principali in card
        try:
            # Documenti stats
            doc_stats = self.document_service.get_document_stats()
            if doc_stats.success:
                st.subheader("📄 Archivio Documenti")
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("� Totale", doc_stats.data.get('total_documents', 0))
                with col2:
                    categories = len(doc_stats.data.get('categories', {}))
                    st.metric("📂 Categorie", categories)
                with col3:
                    recent = doc_stats.data.get('recent_uploads', 0)
                    st.metric("🆕 Recenti", recent)
                with col4:
                    # Calcola crescita (simulata)
                    growth = "+12%"
                    st.metric("📈 Crescita", growth)

                # Grafico categorie (placeholder)
                if doc_stats.data.get('categories'):
                    st.bar_chart(list(doc_stats.data['categories'].values())[:5])

            # Chat stats
            chat_stats = self.chat_service.get_chat_stats()
            if chat_stats.success:
                st.markdown("---")
                st.subheader("💬 Attività Chat")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("💭 Chat Totali", chat_stats.data.get('total_chats', 0))
                with col2:
                    st.metric("📨 Messaggi", chat_stats.data.get('total_messages', 0))
                with col3:
                    avg = chat_stats.data.get('average_messages_per_chat', 0)
                    st.metric("📊 Media/Chat", f"{avg:.1f}")

                # Attività recente (placeholder)
                st.caption("📅 Ultima settimana: +5 chat, +23 messaggi")

        except Exception as e:
            st.error(f"❌ Errore caricamento statistiche: {e}")
            if st.button("🔧 Riprova"):
                st.rerun()

    def render_projects_tab(self):
        """Render tab progetti con ProjectSelector integrato."""
        st.header("📚 Gestione Progetti")

        # Inizializza ProjectSelector se non esiste
        if 'project_selector' not in st.session_state:
            from .project_selector import create_project_selector
            st.session_state.project_selector = create_project_selector(
                on_project_change=self._on_project_change
            )

        # Render ProjectSelector
        project_selector = st.session_state.project_selector
        project_selector.render()

        # Informazioni progetto attivo
        active_project = project_selector.get_active_project()
        if active_project:
            st.markdown("---")
            st.subheader("📍 Progetto Attivo")

            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                st.write(f"**Nome:** {active_project.get('name', 'N/A')}")
                st.write(f"**Tipo:** {active_project.get('type', 'N/A')}")
                st.write(f"**Descrizione:** {active_project.get('description', 'N/A')}")
                st.write(f"**Creato:** {active_project.get('created_at', 'N/A')[:10]}")

            with col2:
                if st.button("📊 Statistiche", key="project_stats"):
                    self._show_project_stats(active_project)

            with col3:
                if st.button("⚙️ Impostazioni", key="project_settings"):
                    st.session_state.show_project_settings = True

        # Debug info per sviluppo
        if st.session_state.get('debug_mode', False):
            with st.expander("🔧 Debug Projects"):
                st.write("**ProjectSelector Status:**")
                st.write(f"Active Project: {active_project.get('name') if active_project else 'None'}")
                st.write(f"Projects Count: {len(project_selector.projects_cache)}")

    def render_career_tab(self):
        """Render tab carriera con AcademicPlanner integrato."""
        st.header("🎓 Carriera Accademica")

        # Inizializza AcademicPlanner se non esiste
        if 'academic_planner' not in st.session_state:
            try:
                from .academic_planner import create_academic_planner
                st.session_state.academic_planner = create_academic_planner(
                    on_task_update=self._on_task_update
                )
            except Exception as e:
                st.error(f"Errore inizializzazione AcademicPlanner: {e}")
                return

        academic_planner = st.session_state.academic_planner

        # Toolbar carriera
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📅 Calendario", type="primary"):
                st.session_state.show_calendar_view = True

        with col2:
            if st.button("🎯 Attività"):
                st.session_state.show_task_manager = True

        with col3:
            if st.button("📊 Panoramica"):
                st.session_state.show_career_overview = True

        st.markdown("---")

        try:
            # Verifica se utente è loggato
            if 'user_id' not in st.session_state or not st.session_state['user_id']:
                st.warning("🔐 Effettua il login per accedere alla gestione carriera")
                return

            # Render AcademicPlanner
            academic_planner.render()

        except Exception as e:
            st.error(f"❌ Errore caricamento carriera: {e}")

        # Debug info per sviluppo
        if st.session_state.get('debug_mode', False):
            with st.expander("🔧 Debug Career"):
                st.write("**AcademicPlanner Status:**")
                st.write(f"User ID: {st.session_state.get('user_id', 'Not logged in')}")
                st.write(f"Planner Available: {academic_planner is not None}")
                st.write(f"Tasks Cache: {len(academic_planner.tasks_cache)}")

    def render_graph_tab(self):
        """Render tab grafo con GraphVisualization integrato."""
        st.header("🧠 Grafo della Conoscenza")

        # Inizializza GraphVisualization se non esiste
        if 'graph_visualization' not in st.session_state:
            try:
                from .graph_visualization import create_graph_visualization
                st.session_state.graph_visualization = create_graph_visualization(
                    on_entity_select=self._on_entity_select
                )
            except Exception as e:
                st.error(f"Errore inizializzazione GraphVisualization: {e}")
                return

        graph_visualization = st.session_state.graph_visualization

        # Render GraphVisualization
        graph_visualization.render()

        # Debug info per sviluppo
        if st.session_state.get('debug_mode', False):
            with st.expander("🔧 Debug Graph"):
                st.write("**GraphVisualization Status:**")
                st.write(f"Graph Data Available: {graph_visualization.graph_data is not None}")
                st.write(f"Filtered Entities: {len(graph_visualization.filtered_entities)}")
                st.write(f"Filtered Relationships: {len(graph_visualization.filtered_relationships)}")

    def render_settings_tab(self):
        """Render tab impostazioni."""
        st.header("⚙️ Impostazioni")

        st.subheader("🔐 Autenticazione")
        if st.button("🔑 Gestisci Account"):
            st.info("Gestione account utente...")

        st.subheader("🎨 Preferenze UI")
        theme = st.selectbox("Tema", ["Chiaro", "Scuro", "Auto"])
        st.selectbox("Lingua", ["Italiano", "Inglese"])

        st.subheader("🤖 Configurazione AI")
        st.slider("Temperatura AI", 0.0, 1.0, 0.7)
        st.selectbox("Modello AI", ["GPT-3.5", "GPT-4", "Ollama"])

        if st.button("💾 Salva Impostazioni"):
            st.success("Impostazioni salvate!")

    def _show_archive_stats(self):
        """Mostra statistiche archivio dettagliate."""
        try:
            stats = self.document_service.get_document_stats()
            if stats.success:
                st.subheader("📊 Statistiche Dettagliate")

                col1, col2 = st.columns(2)

                with col1:
                    st.metric("📄 Totale Documenti", stats.data.get('total_documents', 0))

                    # Categorie più usate
                    categories = stats.data.get('categories', {})
                    if categories:
                        st.write("**Categorie principali:**")
                        for cat, count in list(categories.items())[:5]:
                            st.write(f"• {cat}: {count}")

                with col2:
                    st.metric("🆕 Upload Recenti", stats.data.get('recent_uploads', 0))

                    # Azioni rapide
                    if st.button("📥 Esporta Statistiche"):
                        st.info("Esportazione statistiche...")

        except Exception as e:
            st.error(f"Errore statistiche: {e}")

    def render_active_tab(self):
        """Render tab attualmente attivo."""
        tab_renderers = {
            "chat": self.render_chat_tab,
            "archive": self.render_archive_tab,
            "dashboard": self.render_dashboard_tab,
            "projects": self.render_projects_tab,
            "career": self.render_career_tab,
            "graph": self.render_graph_tab,
            "settings": self.render_settings_tab
        }

        renderer = tab_renderers.get(self.active_tab, self.render_chat_tab)
        renderer()

    def render(self):
        """Render dashboard completa."""
        # Header principale
        self.render_header()

        # Layout principale
        main_col, content_col = st.columns([1, 4])

        with main_col:
            # Sidebar navigazione
            self.render_sidebar()

        with content_col:
            # File context manager
            self.render_file_context_manager()

            # Smart suggestions proattive
            self._render_smart_suggestions()

            # Notifiche globali
            self._render_global_notifications()

            # Contenuto tab attivo
            self.render_active_tab()

    def handle_state_changes(self):
        """Gestisce cambiamenti di stato."""
        # Gestione modali
        if st.session_state.get('show_login', False):
            self._render_login_modal()

        if st.session_state.get('show_file_manager', False):
            self._render_file_manager_modal()

        # Gestione wizard contestuale
        if st.session_state.get('show_contextual_wizard', False):
            self._render_contextual_wizard()

    def _render_login_modal(self):
        """Render modal login."""
        with st.expander("🔐 Login", expanded=True):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔑 Accedi"):
                    try:
                        result = self.user_service.authenticate(username, password)
                        if result.success:
                            st.success("Login effettuato!")
                            st.session_state.user = result.data
                            st.session_state.show_login = False
                            st.rerun()
                        else:
                            st.error("Credenziali non valide")
                    except Exception as e:
                        st.error(f"Errore login: {e}")

            with col2:
                if st.button("❌ Annulla"):
                    st.session_state.show_login = False
                    st.rerun()

    def _render_file_manager_modal(self):
        """Render modal gestione file."""
        with st.expander("📁 Gestione File", expanded=True):
            st.write("**File nel contesto:**")
            if 'context_files' in st.session_state and st.session_state.context_files:
                for file in st.session_state.context_files:
                    st.write(f"• {file}")
            else:
                st.info("Nessun file nel contesto")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("➕ Aggiungi File"):
                    st.info("Selezione file...")

            with col2:
                if st.button("❌ Chiudi"):
                    st.session_state.show_file_manager = False
                    st.rerun()

    def _create_new_project(self, name: str, project_type: str):
        """Crea un nuovo progetto."""
        try:
            # Qui andrebbe la logica di creazione progetto
            # Per ora simula creazione
            st.success(f"✅ Progetto '{name}' creato con tipo '{project_type}'")

            # Aggiungi alla lista progetti (simulazione)
            if 'projects' not in st.session_state:
                st.session_state.projects = []

            new_project = {
                'id': len(st.session_state.projects) + 1,
                'name': name,
                'type': project_type,
                'created_at': datetime.now().isoformat(),
                'document_count': 0
            }

            st.session_state.projects.append(new_project)
            st.rerun()

        except Exception as e:
            st.error(f"❌ Errore creazione progetto: {e}")

    def _get_projects_list(self):
        """Recupera lista progetti dal database."""
        try:
            # Simula recupero progetti (placeholder per futura integrazione)
            if 'projects' in st.session_state:
                return st.session_state.projects
            else:
                # Progetti di esempio per demo
                return [
                    {
                        'id': 1,
                        'name': 'Tesi Laurea',
                        'type': 'Studio',
                        'created_at': '2024-01-15',
                        'document_count': 5
                    },
                    {
                        'id': 2,
                        'name': 'Ricerca AI',
                        'type': 'Ricerca',
                        'created_at': '2024-02-01',
                        'document_count': 12
                    }
                ]
        except Exception as e:
            st.error(f"Errore recupero progetti: {e}")
            return []

    def _check_projects_service(self):
        """Verifica stato servizio progetti."""
        try:
            # Placeholder per verifica servizio
            return "✅ Disponibile"
        except Exception:
            return "❌ Non disponibile"

    def _get_projects_db_status(self):
        """Verifica stato database progetti."""
        try:
            # Placeholder per verifica database
            return "✅ Connesso"
        except Exception:
            return "❌ Disconnesso"

    def _on_project_change(self, project: Dict[str, Any]):
        """Callback per cambio progetto."""
        try:
            st.session_state.active_project = project
            st.success(f"📍 Progetto '{project.get('name')}' attivato")
            logger.info(f"Progetto cambiato: {project.get('name')}")
        except Exception as e:
            logger.error(f"Errore cambio progetto: {e}")
            st.error(f"Errore attivazione progetto: {e}")

    def _show_project_stats(self, project: Dict[str, Any]):
        """Mostra statistiche progetto."""
        try:
            st.subheader(f"📊 Statistiche: {project.get('name')}")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("📄 Documenti", project.get('document_count', 0))

            with col2:
                st.metric("📅 Creato", project.get('created_at', 'N/A')[:10])

            with col3:
                st.metric("📂 Tipo", project.get('type', 'N/A'))

            # Attività recente (placeholder)
            st.caption("📈 Attività recente: Da implementare")

        except Exception as e:
            st.error(f"Errore statistiche progetto: {e}")

    def _render_course_card(self, course: Dict[str, Any], career_service):
        """Render card corso con azioni."""
        with st.container():
            st.markdown(f"""
            <div class="course-card">
                <h4>{course.get('name', 'Senza nome')}</h4>
                <p><strong>Codice:</strong> {course.get('code', 'N/A')}</p>
                <p>{course.get('description', 'Nessuna descrizione')[:100]}{'...' if len(course.get('description', '')) > 100 else ''}</p>
                <p><small>Creato: {course.get('created_at', 'N/A')[:10]}</small></p>
            </div>
            """, unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("👁️ Apri", key=f"open_course_{course.get('id')}", use_container_width=True):
                    st.session_state.selected_course_id = course.get('id')
                    st.success(f"Corso '{course.get('name')}' aperto")
                    st.rerun()

            with col2:
                if st.button("✏️ Modifica", key=f"edit_course_{course.get('id')}", use_container_width=True):
                    st.session_state.edit_course = course
                    st.info("Modifica corso da implementare")

            with col3:
                if st.button("🗑️ Elimina", key=f"delete_course_{course.get('id')}", use_container_width=True):
                    if st.session_state.get(f"confirm_delete_course_{course.get('id')}", False):
                        result = career_service.delete_course(course.get('id'))
                        if result.success:
                            st.success("✅ Corso eliminato")
                            st.rerun()
                        else:
                            st.error(f"❌ Errore eliminazione: {result.message}")
                    else:
                        st.session_state[f"confirm_delete_course_{course.get('id')}"] = True
                        st.warning(f"Clicca di nuovo per confermare eliminazione di '{course.get('name')}'")
                        st.rerun()

    def _render_career_empty_state(self):
        """Render stato vuoto carriera con call-to-action."""
        st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <h3>🎓 Inizia la tua Carriera Accademica</h3>
            <p>Organizza i tuoi corsi, lezioni e attività accademiche in un unico posto.</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            if st.button("➕ Crea il tuo primo corso", type="primary", use_container_width=True):
                st.session_state.show_course_creator = True

    def _show_career_stats(self, career_service):
        """Mostra statistiche carriera."""
        try:
            if 'user_id' not in st.session_state or not st.session_state['user_id']:
                st.warning("🔐 Effettua il login per visualizzare le statistiche")
                return

            user_id = st.session_state['user_id']
            stats_result = career_service.get_user_career_stats(user_id)

            if stats_result.success:
                stats = stats_result.data
                st.subheader("📊 Statistiche Carriera")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("📚 Corsi Totali", stats.get('total_courses', 0))

                with col2:
                    st.metric("📝 Lezioni Totali", stats.get('total_lectures', 0))

                with col3:
                    st.metric("🎯 Attività Totali", stats.get('total_tasks', 0))

                with col4:
                    completion_rate = stats.get('completion_rate', 0)
                    st.metric("✅ Tasso Completamento", f"{completion_rate:.1f}%")

                # Grafico completamento
                if stats.get('total_tasks', 0) > 0:
                    st.caption("📈 Progresso Attività")
                    progress_data = {
                        'Completate': stats.get('completed_tasks', 0),
                        'In Corso': stats.get('total_tasks', 0) - stats.get('completed_tasks', 0)
                    }
                    st.bar_chart(progress_data)
            else:
                st.error(f"Errore recupero statistiche: {stats_result.message}")

        except Exception as e:
            st.error(f"Errore statistiche carriera: {e}")

    def _on_task_update(self, task_id: Any, new_status: str):
        """Callback per aggiornamento attività."""
        try:
            logger.info(f"Attività {task_id} aggiornata a stato: {new_status}")

            # Qui andrebbe la logica di aggiornamento nel database
            # Per ora simula solo il logging

        except Exception as e:
            logger.error(f"Errore aggiornamento attività {task_id}: {e}")
            st.error(f"Errore aggiornamento attività: {e}")

    def _on_document_select(self, document: Dict[str, Any]):
        """Callback per selezione documento."""
        try:
            logger.info(f"Documento selezionato: {document.get('file_name')}")
            st.session_state.selected_document = document
            st.success(f"📄 Documento '{document.get('file_name')}' selezionato")
        except Exception as e:
            logger.error(f"Errore selezione documento: {e}")
            st.error(f"Errore selezione documento: {e}")

    def _on_entity_select(self, entity: Dict[str, Any]):
        """Callback per selezione entità."""
        try:
            logger.info(f"Entità selezionata: {entity.get('entity_name')}")
            st.session_state.selected_entity = entity
            st.success(f"🔵 Entità '{entity.get('entity_name')}' selezionata")
        except Exception as e:
            logger.error(f"Errore selezione entità: {e}")
            st.error(f"Errore selezione entità: {e}")

    def _render_contextual_wizard(self):
        """Render wizard contestuale basato sul tab attivo."""
        try:
            # Import wizard functions
            from workflow_wizards import (
                document_upload_wizard,
                advanced_search_wizard,
                document_editing_wizard,
                batch_operations_wizard
            )

            # Determina wizard contestuale basato su tab attivo
            wizard_map = {
                "archive": ("📤 Caricamento Documenti", "Carica e organizza nuovi documenti", document_upload_wizard),
                "chat": ("🔍 Ricerca Avanzata", "Costruisci query di ricerca complesse", advanced_search_wizard),
                "projects": ("✏️ Modifica Documenti", "Modifica e aggiorna i tuoi documenti", document_editing_wizard),
                "dashboard": ("⚡ Operazioni Batch", "Esegui operazioni su più documenti", batch_operations_wizard),
                "career": ("📤 Caricamento Documenti", "Carica materiali accademici", document_upload_wizard),
                "graph": ("🔍 Ricerca Avanzata", "Esplora connessioni concettuali", advanced_search_wizard)
            }

            wizard_info = wizard_map.get(self.active_tab, ("🎯 Wizard Generico", "Assistente guidato", document_upload_wizard))
            wizard_title, wizard_description, wizard_function = wizard_info

            # Render wizard in un expander
            with st.expander(f"🎯 {wizard_title}", expanded=True):
                st.caption(wizard_description)

                # Esegui wizard
                wizard_function()

                # Pulsante chiudi
                if st.button("❌ Chiudi Wizard", key="close_contextual_wizard"):
                    st.session_state.show_contextual_wizard = False
                    st.rerun()

        except Exception as e:
            st.error(f"❌ Errore wizard contestuale: {e}")
            if st.button("❌ Chiudi", key="close_wizard_error"):
                st.session_state.show_contextual_wizard = False
                st.rerun()

    def _render_smart_suggestions(self):
        """Render smart suggestions proattive."""
        try:
            # Import smart suggestions
            from smart_suggestions import show_smart_suggestions, record_user_action

            # Verifica se utente è loggato
            user_id = st.session_state.get('user_id')
            if not user_id:
                return

            # Determina contesto attuale
            context = {
                'current_page': self.active_tab,
                'has_documents': self._has_documents(),
                'context_key': f"{self.active_tab}_suggestions"
            }

            # Record user action per behavior analysis
            record_user_action(user_id, f'viewed_{self.active_tab}_tab', context)

            # Mostra smart suggestions in un container discreto
            with st.container():
                st.markdown("---")
                show_smart_suggestions(user_id, context)

        except Exception as e:
            # Non mostrare errori per smart suggestions per non disturbare l'utente
            logger.debug(f"Smart suggestions error: {e}")

    def _has_documents(self) -> bool:
        """Verifica se ci sono documenti disponibili."""
        try:
            result = self.document_service.get_document_stats()
            return result.success and result.data.get('total_documents', 0) > 0
        except:
            return False

    def _render_global_notifications(self):
        """Render notifiche globali del sistema."""
        try:
            # Import notification system
            from feedback_system import notification_manager

            # Verifica se utente è loggato
            user_id = st.session_state.get('user_id')
            if not user_id:
                return

            # Mostra notifiche in un container discreto
            with st.container():
                st.markdown("---")
                notification_manager.show_notifications()

        except Exception as e:
            # Non mostrare errori per notifiche per non disturbare l'utente
            logger.debug(f"Global notifications error: {e}")


def create_unified_dashboard() -> UnifiedDashboard:
    """Factory function per creare dashboard unificata."""
    return UnifiedDashboard()
