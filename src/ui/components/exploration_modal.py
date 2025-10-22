"""
ExplorationModal component.

Componente specializzato per l'esplorazione dettagliata di documenti
con overlay modale e funzionalità avanzate di navigazione.
"""

import streamlit as st
import pandas as pd
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

from .base import BaseComponent

logger = logging.getLogger(__name__)


class ExplorationModal(BaseComponent):
    """Modale esplorazione documenti con funzionalità avanzate."""

    def __init__(self, on_document_select: Optional[Callable] = None):
        """Inizializza ExplorationModal.

        Args:
            on_document_select: Callback per selezione documento
        """
        super().__init__(component_id="exploration_modal", title="Document Explorer")
        self.on_document_select = on_document_select
        self.selected_document = None
        self.explorer_mode = "grid"  # grid, list, detail
        self.search_query = ""
        self.category_filter = "Tutte"
        self.documents_cache = []

        # Inizializza servizi
        self._initialize_services()

    def _initialize_services(self):
        """Inizializza servizi per esplorazione documenti."""
        try:
            # Import servizi necessari
            from src.services.document_service import create_document_service
            from src.services.career_service import create_career_service

            # Usa database esistente
            db_path = "db_memoria/metadata.sqlite"
            self.document_service = create_document_service(db_path)
            self.career_service = create_career_service(db_path)

            logger.info("✅ ExplorationModal servizi inizializzati")

        except Exception as e:
            logger.error(f"❌ Errore inizializzazione ExplorationModal: {e}")
            st.error(f"Errore inizializzazione ExplorationModal: {e}")

    def render_modal(self):
        """Render modale esplorazione documenti."""
        if not st.session_state.get('show_document_explorer', False):
            return

        @st.dialog("🔍 Esplorazione Documenti", width="large")
        def document_explorer():
            # Header modale
            st.header("📚 Esplorazione Documenti")

            # Toolbar esplorazione
            self._render_explorer_toolbar()

            st.markdown("---")

            # Contenuto principale
            if self.explorer_mode == "grid":
                self._render_grid_view()
            elif self.explorer_mode == "list":
                self._render_list_view()
            else:
                self._render_detail_view()

        document_explorer()

    def _render_explorer_toolbar(self):
        """Render toolbar esplorazione."""
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

        with col1:
            # Campo ricerca
            self.search_query = st.text_input(
                "🔍 Cerca documenti",
                value=self.search_query,
                key="explorer_search",
                placeholder="Titolo, autore, categoria..."
            )

        with col2:
            # Filtro categoria
            categories = self._get_available_categories()
            category_options = ["Tutte"] + categories
            self.category_filter = st.selectbox(
                "📂 Categoria",
                category_options,
                key="explorer_category_filter"
            )

        with col3:
            # Modalità visualizzazione
            view_modes = ["Grid", "Lista", "Dettagli"]
            selected_mode = st.selectbox(
                "👁️ Vista",
                view_modes,
                key="explorer_view_mode"
            )
            self.explorer_mode = selected_mode.lower()

        with col4:
            # Azioni
            if st.button("🔄 Aggiorna", key="refresh_explorer"):
                self._refresh_documents()

    def _render_grid_view(self):
        """Render vista griglia documenti."""
        try:
            documents = self._get_filtered_documents()

            if not documents:
                self._render_empty_explorer_state()
                return

            st.subheader(f"📋 Documenti ({len(documents)})")

            # Layout griglia
            cols_per_row = 3
            for i in range(0, len(documents), cols_per_row):
                cols = st.columns(cols_per_row)

                for j, doc in enumerate(documents[i:i + cols_per_row]):
                    with cols[j]:
                        self._render_document_card(doc)

        except Exception as e:
            st.error(f"Errore caricamento griglia: {e}")

    def _render_list_view(self):
        """Render vista lista documenti."""
        try:
            documents = self._get_filtered_documents()

            if not documents:
                self._render_empty_explorer_state()
                return

            st.subheader(f"📋 Documenti ({len(documents)})")

            # Lista documenti
            for doc in documents:
                self._render_document_list_item(doc)

        except Exception as e:
            st.error(f"Errore caricamento lista: {e}")

    def _render_detail_view(self):
        """Render vista dettagliata documento."""
        if not self.selected_document:
            st.info("👈 Seleziona un documento per visualizzare i dettagli")
            return

        try:
            self._render_document_details(self.selected_document)
        except Exception as e:
            st.error(f"Errore caricamento dettagli: {e}")

    def _render_document_card(self, document: Dict[str, Any]):
        """Render card documento per griglia."""
        with st.container():
            # Card styling
            st.markdown(f"""
            <div style="
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 12px;
                background: linear-gradient(135deg, #f8f9fa, #ffffff);
                cursor: pointer;
                transition: all 0.3s ease;
            " onclick="this.style.transform='scale(0.98)'">
                <h5 style="margin-bottom: 8px;">📄 {document.get('title', 'Senza titolo')}</h5>
                <p style="font-size: 0.85em; color: #666; margin: 4px 0;">
                    👤 {document.get('authors', 'Autore sconosciuto')}
                </p>
                <p style="font-size: 0.85em; color: #666; margin: 4px 0;">
                    📂 {document.get('category_name', 'Senza categoria')}
                </p>
                <p style="font-size: 0.8em; color: #888; margin: 4px 0;">
                    📅 {document.get('processed_at', 'N/A')[:10] if document.get('processed_at') else 'N/A'}
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Azioni documento
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("👁️", key=f"view_grid_{document.get('file_name')}", help="Visualizza"):
                    self._select_document(document)

            with col2:
                if st.button("📝", key=f"edit_grid_{document.get('file_name')}", help="Modifica"):
                    self._edit_document(document)

            with col3:
                if st.button("📊", key=f"analyze_grid_{document.get('file_name')}", help="Analizza"):
                    self._analyze_document(document)

    def _render_document_list_item(self, document: Dict[str, Any]):
        """Render elemento lista documento."""
        col1, col2, col3, col4 = st.columns([3, 2, 1, 1])

        with col1:
            st.write(f"**📄 {document.get('title', 'Senza titolo')}**")
            st.caption(f"👤 {document.get('authors', 'Autore sconosciuto')}")

        with col2:
            st.write(f"📂 {document.get('category_name', 'Senza categoria')}")
            st.caption(f"📅 {document.get('processed_at', 'N/A')[:10] if document.get('processed_at') else 'N/A'}")

        with col3:
            if st.button("👁️ Visualizza", key=f"view_list_{document.get('file_name')}"):
                self._select_document(document)

        with col4:
            if st.button("📋 Dettagli", key=f"details_list_{document.get('file_name')}"):
                self._show_document_details(document)

        st.divider()

    def _render_document_details(self, document: Dict[str, Any]):
        """Render dettagli completi documento."""
        st.header(f"📄 {document.get('title', 'Senza titolo')}")

        # Info principali
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📋 Informazioni Base")
            st.write(f"**Titolo:** {document.get('title', 'N/A')}")
            st.write(f"**Autori:** {document.get('authors', 'N/A')}")
            st.write(f"**Anno:** {document.get('publication_year', 'N/A')}")
            st.write(f"**Categoria:** {document.get('category_name', 'N/A')}")

        with col2:
            st.subheader("📊 Metadati")
            st.write(f"**File:** {document.get('file_name', 'N/A')}")
            st.write(f"**Dimensione:** {document.get('file_size', 'N/A')} bytes")
            st.write(f"**Tipo:** {document.get('mime_type', 'N/A')}")
            st.write(f"**Processato:** {document.get('processed_at', 'N/A')}")

        # Keywords AI
        if document.get('keywords'):
            try:
                keywords = json.loads(document.get('keywords', '[]'))
                if keywords:
                    st.subheader("🏷️ Parole Chiave (AI)")
                    keyword_badges = " ".join([f'<span class="keyword-tag">{kw}</span>' for kw in keywords[:10]])
                    st.markdown(keyword_badges, unsafe_allow_html=True)
            except:
                st.caption("⚠️ Errore caricamento parole chiave")

        # Task AI generati
        if document.get('ai_tasks'):
            try:
                ai_tasks = json.loads(document.get('ai_tasks', '{}'))
                if ai_tasks:
                    st.subheader("🎯 Attività Generate (AI)")
                    for task_name, task_data in ai_tasks.items():
                        with st.expander(f"📋 {task_name}"):
                            st.write(f"**Descrizione:** {task_data.get('description', 'N/A')}")
                            st.write(f"**Priorità:** {task_data.get('priority', 'N/A')}")
                            st.write(f"**Tipo:** {task_data.get('task_type', 'N/A')}")
            except:
                st.caption("⚠️ Errore caricamento attività AI")

        # Anteprima formattata
        if document.get('formatted_preview'):
            st.subheader("👁️ Anteprima")
            with st.container():
                st.markdown(document.get('formatted_preview', 'Anteprima non disponibile'))

        # Azioni documento
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("🤖 Chat su Documento", key="chat_doc"):
                self._chat_with_document(document)

        with col2:
            if st.button("📋 Aggiungi a Progetto", key="add_to_project"):
                self._add_to_project(document)

        with col3:
            if st.button("📊 Analisi Avanzata", key="advanced_analysis"):
                self._advanced_analysis(document)

        with col4:
            if st.button("📥 Esporta", key="export_doc"):
                self._export_document(document)

    def _render_empty_explorer_state(self):
        """Render stato vuoto esploratore."""
        st.info("📭 Nessun documento trovato")

        st.markdown("""
        **Suggerimenti per trovare documenti:**

        1. **🔍 Usa la ricerca** - Cerca per titolo, autore o categoria
        2. **📂 Filtra per categoria** - Seleziona una categoria specifica
        3. **📤 Carica nuovi documenti** - Aggiungi documenti al sistema
        4. **🔄 Aggiorna** - Ricarica la lista documenti
        """)

        col1, col2 = st.columns(2)

        with col1:
            if st.button("📤 Carica Documenti", type="primary"):
                st.session_state.show_document_uploader = True

        with col2:
            if st.button("🔄 Aggiorna Lista"):
                self._refresh_documents()

    def _get_filtered_documents(self) -> List[Dict[str, Any]]:
        """Recupera documenti filtrati."""
        try:
            # Prima controlla cache
            if self.documents_cache and not self.search_query and self.category_filter == "Tutte":
                return self.documents_cache

            # Recupera tutti i documenti
            result = self.document_service.get_all()

            if not result.success:
                return []

            documents = result.data

            # Applica filtri
            if self.search_query:
                query_lower = self.search_query.lower()
                documents = [
                    doc for doc in documents
                    if (doc.get('title', '').lower().find(query_lower) != -1 or
                        doc.get('authors', '').lower().find(query_lower) != -1 or
                        doc.get('category_name', '').lower().find(query_lower) != -1)
                ]

            if self.category_filter != "Tutte":
                documents = [
                    doc for doc in documents
                    if doc.get('category_name') == self.category_filter
                ]

            # Aggiorna cache
            self.documents_cache = documents
            return documents

        except Exception as e:
            logger.error(f"Errore filtri documenti: {e}")
            return []

    def _get_available_categories(self) -> List[str]:
        """Ottieni categorie disponibili."""
        try:
            result = self.document_service.get_document_stats()
            if result.success:
                categories = result.data.get('categories', {})
                return list(categories.keys())
            return []
        except Exception:
            return []

    def _refresh_documents(self):
        """Aggiorna lista documenti."""
        try:
            self.documents_cache = []
            st.success("✅ Documenti aggiornati")
        except Exception as e:
            st.error(f"Errore aggiornamento: {e}")

    def _select_document(self, document: Dict[str, Any]):
        """Seleziona documento per visualizzazione."""
        try:
            self.selected_document = document
            if self.on_document_select:
                self.on_document_select(document)
            st.success(f"Documento '{document.get('title')}' selezionato")
        except Exception as e:
            st.error(f"Errore selezione documento: {e}")

    def _show_document_details(self, document: Dict[str, Any]):
        """Mostra dettagli documento."""
        try:
            self.selected_document = document
            self.explorer_mode = "detail"
            st.rerun()
        except Exception as e:
            st.error(f"Errore dettagli documento: {e}")

    def _edit_document(self, document: Dict[str, Any]):
        """Modifica documento."""
        try:
            st.info(f"Modifica documento: {document.get('title')}")
            # Qui andrebbe la logica di modifica
        except Exception as e:
            st.error(f"Errore modifica documento: {e}")

    def _analyze_document(self, document: Dict[str, Any]):
        """Analisi avanzata documento."""
        try:
            st.info(f"Analisi documento: {document.get('title')}")
            # Qui andrebbe la logica di analisi
        except Exception as e:
            st.error(f"Errore analisi documento: {e}")

    def _chat_with_document(self, document: Dict[str, Any]):
        """Avvia chat con documento."""
        try:
            # Aggiungi documento al contesto chat
            if 'context_files' not in st.session_state:
                st.session_state.context_files = []

            if document.get('file_name') not in st.session_state.context_files:
                st.session_state.context_files.append(document.get('file_name'))

            # Passa al tab chat
            st.session_state.active_tab = "chat"
            st.success(f"Documento aggiunto al contesto chat")
            st.rerun()

        except Exception as e:
            st.error(f"Errore chat documento: {e}")

    def _add_to_project(self, document: Dict[str, Any]):
        """Aggiungi documento a progetto."""
        try:
            st.info(f"Aggiungi a progetto: {document.get('title')}")
            # Qui andrebbe la logica di aggiunta a progetto
        except Exception as e:
            st.error(f"Errore aggiunta progetto: {e}")

    def _advanced_analysis(self, document: Dict[str, Any]):
        """Analisi avanzata documento."""
        try:
            st.info(f"Analisi avanzata: {document.get('title')}")
            # Qui andrebbe la logica di analisi avanzata
        except Exception as e:
            st.error(f"Errore analisi avanzata: {e}")

    def _export_document(self, document: Dict[str, Any]):
        """Esporta documento."""
        try:
            st.info(f"Esporta documento: {document.get('title')}")
            # Qui andrebbe la logica di esportazione
        except Exception as e:
            st.error(f"Errore esportazione: {e}")

    def show_modal(self):
        """Mostra modale esplorazione."""
        st.session_state.show_document_explorer = True

    def hide_modal(self):
        """Nascondi modale esplorazione."""
        st.session_state.show_document_explorer = False

    def get_selected_document(self) -> Optional[Dict[str, Any]]:
        """Restituisce documento selezionato."""
        return self.selected_document

    def render(self):
        """Render componente principale."""
        # Render modale se attivo
        self.render_modal()

        # Pulsante per aprire modale
        if st.button("🔍 Esplora Documenti", type="secondary"):
            self.show_modal()
            st.rerun()


def create_exploration_modal(on_document_select: Optional[Callable] = None) -> ExplorationModal:
    """Factory function per creare ExplorationModal."""
    return ExplorationModal(on_document_select)
