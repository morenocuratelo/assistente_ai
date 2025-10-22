"""
ProjectSelector component.

Componente specializzato per la selezione e gestione progetti
con interfaccia ottimizzata e stato visuale.
"""

import streamlit as st
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

from .base import BaseComponent

logger = logging.getLogger(__name__)


class ProjectSelector(BaseComponent):
    """Selettore progetti avanzato con gestione stato."""

    def __init__(self, on_project_change: Optional[Callable] = None):
        """Inizializza ProjectSelector.

        Args:
            on_project_change: Callback per cambio progetto
        """
        super().__init__(component_id="project_selector", title="Project Selector")
        self.on_project_change = on_project_change
        self.selected_project = None
        self.projects_cache = []

        # Inizializza servizi
        self._initialize_services()

    def _initialize_services(self):
        """Inizializza servizi per gestione progetti."""
        try:
            # Import servizi necessari
            from src.services.project_service import ProjectService, create_project_service
            from src.database.repositories.project_repository import ProjectRepository, create_project_repository

            # Usa database esistente
            db_path = "db_memoria/metadata.sqlite"
            self.project_service = create_project_service(db_path)

            logger.info("✅ ProjectSelector servizi inizializzati")

        except Exception as e:
            logger.error(f"❌ Errore inizializzazione ProjectSelector: {e}")
            st.error(f"Errore inizializzazione ProjectSelector: {e}")

    def render_compact(self):
        """Render versione compatta per sidebar."""
        try:
            projects = self._get_projects_list()

            if projects:
                # Dropdown selezione progetto
                project_names = ["Nessun progetto"] + [p.get('name', 'Senza nome') for p in projects]
                current_selection = st.selectbox(
                    "📚 Progetto attivo",
                    project_names,
                    key="project_selector_compact",
                    help="Seleziona progetto attivo"
                )

                if current_selection != "Nessun progetto":
                    selected_project = next(
                        (p for p in projects if p.get('name') == current_selection),
                        None
                    )

                    if selected_project and selected_project != self.selected_project:
                        self._set_active_project(selected_project)
                        if self.on_project_change:
                            self.on_project_change(selected_project)

                # Info progetto attivo
                if self.selected_project:
                    st.caption(f"📍 {self.selected_project.get('name', 'N/A')} - {self.selected_project.get('type', 'N/A')}")

            else:
                st.caption("📭 Nessun progetto")
                if st.button("➕ Crea", key="create_project_compact", help="Crea nuovo progetto"):
                    st.session_state.show_project_creator = True

        except Exception as e:
            st.error(f"Errore ProjectSelector compatto: {e}")

    def render_expanded(self):
        """Render versione espansa per pagina dedicata."""
        st.header("📚 Gestione Progetti")

        # Toolbar principale
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            search_query = st.text_input("🔍 Cerca progetti", key="project_search")

        with col2:
            type_filter = st.selectbox(
                "📂 Tipo",
                ["Tutti", "Ricerca", "Studio", "Personale", "Lavoro"],
                key="project_type_filter"
            )

        with col3:
            if st.button("➕ Nuovo Progetto", type="primary", key="create_project_main"):
                st.session_state.show_project_creator = True

        st.markdown("---")

        try:
            projects = self._get_projects_list()

            # Applica filtri
            if search_query:
                projects = [p for p in projects if search_query.lower() in p.get('name', '').lower()]
            if type_filter != "Tutti":
                projects = [p for p in projects if p.get('type') == type_filter]

            if projects:
                st.subheader(f"📋 Progetti ({len(projects)})")

                # Layout griglia progetti
                cols_per_row = 3
                for i in range(0, len(projects), cols_per_row):
                    cols = st.columns(cols_per_row)

                    for j, project in enumerate(projects[i:i + cols_per_row]):
                        with cols[j]:
                            self._render_project_card(project)

                # Progetto attivo highlight
                if self.selected_project:
                    st.markdown("---")
                    st.subheader("📍 Progetto Attivo")
                    self._render_project_card(self.selected_project, active=True)

            else:
                st.info("📭 Nessun progetto trovato")
                self._render_empty_state()

        except Exception as e:
            st.error(f"❌ Errore caricamento progetti: {e}")

    def _render_project_card(self, project: Dict[str, Any], active: bool = False):
        """Render card progetto con azioni."""
        card_class = "project-card-active" if active else "project-card"

        with st.container():
            st.markdown(f"""
            <div class="project-card {'active' if active else ''}">
                <h4>{project.get('name', 'Senza nome')}</h4>
                <p><strong>Tipo:</strong> {project.get('type', 'N/A')}</p>
                <p><strong>Documenti:</strong> {project.get('document_count', 0)}</p>
                <p><strong>Creato:</strong> {project.get('created_at', 'N/A')[:10]}</p>
            </div>
            """, unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("👁️ Apri", key=f"open_{project.get('id')}", use_container_width=True):
                    self._set_active_project(project)
                    if self.on_project_change:
                        self.on_project_change(project)
                    st.rerun()

            with col2:
                if st.button("✏️ Modifica", key=f"edit_{project.get('id')}", use_container_width=True):
                    st.session_state.edit_project = project
                    st.rerun()

            with col3:
                if st.button("🗑️ Elimina", key=f"delete_{project.get('id')}", use_container_width=True):
                    if st.session_state.get(f"confirm_delete_{project.get('id')}", False):
                        self._delete_project(project.get('id'))
                        st.rerun()
                    else:
                        st.session_state[f"confirm_delete_{project.get('id')}"] = True
                        st.warning(f"Clicca di nuovo per confermare eliminazione di '{project.get('name')}'")
                        st.rerun()

    def _render_empty_state(self):
        """Render stato vuoto con call-to-action."""
        st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <h3>🚀 Inizia con i Progetti</h3>
            <p>I progetti ti aiutano a organizzare i tuoi documenti e ricerche.</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            if st.button("➕ Crea il tuo primo progetto", type="primary", use_container_width=True):
                st.session_state.show_project_creator = True

    def render_project_creator(self):
        """Render modal creazione progetto."""
        with st.expander("➕ Crea Nuovo Progetto", expanded=True):
            with st.form("create_project_form"):
                name = st.text_input("Nome Progetto *", key="new_project_name")
                project_type = st.selectbox(
                    "Tipo Progetto",
                    ["Ricerca", "Studio", "Personale", "Lavoro"],
                    key="new_project_type"
                )
                description = st.text_area("Descrizione", key="new_project_description")

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("✅ Crea", type="primary"):
                        if name.strip():
                            success = self._create_project(name.strip(), project_type, description)
                            if success:
                                st.success(f"✅ Progetto '{name}' creato!")
                                st.session_state.show_project_creator = False
                                st.rerun()
                            else:
                                st.error("❌ Errore creazione progetto")
                        else:
                            st.error("Il nome del progetto è obbligatorio")

                with col2:
                    if st.form_submit_button("❌ Annulla"):
                        st.session_state.show_project_creator = False
                        st.rerun()

    def _get_projects_list(self) -> List[Dict[str, Any]]:
        """Recupera lista progetti dal servizio."""
        try:
            # Prima controlla cache
            if self.projects_cache:
                return self.projects_cache

            # Recupera dal servizio
            result = self.project_service.get_all_projects()
            if result.success:
                self.projects_cache = result.data
                return result.data
            else:
                logger.warning(f"Errore recupero progetti: {result.message}")
                return []

        except Exception as e:
            logger.error(f"Errore _get_projects_list: {e}")
            return []

    def _set_active_project(self, project: Dict[str, Any]):
        """Imposta progetto attivo."""
        try:
            self.selected_project = project

            # Aggiorna session state solo se Streamlit è in esecuzione
            try:
                st.session_state.active_project = project
            except:
                # Ignora errori session state in test environment
                pass

            # Aggiorna cache
            if project not in self.projects_cache:
                self.projects_cache.append(project)

            # Chiama callback se fornito
            if self.on_project_change:
                self.on_project_change(project)

            logger.info(f"Progetto attivo impostato: {project.get('name')}")

            # Mostra feedback solo se Streamlit è in esecuzione
            try:
                st.success(f"📍 Progetto '{project.get('name')}' attivato")
            except:
                # Ignora errori UI in test environment
                pass

        except Exception as e:
            logger.error(f"Errore impostazione progetto attivo: {e}")
            try:
                st.error(f"Errore attivazione progetto: {e}")
            except:
                # Ignora errori UI in test environment
                pass

    def _create_project(self, name: str, project_type: str, description: str = "") -> bool:
        """Crea nuovo progetto."""
        try:
            result = self.project_service.create_project({
                'name': name,
                'type': project_type,
                'description': description,
                'created_at': datetime.now().isoformat(),
                'document_count': 0
            })

            if result.success:
                # Invalida cache
                self.projects_cache = []
                logger.info(f"Progetto creato: {name}")
                return True
            else:
                logger.error(f"Errore creazione progetto: {result.message}")
                return False

        except Exception as e:
            logger.error(f"Errore _create_project: {e}")
            return False

    def _delete_project(self, project_id: Any) -> bool:
        """Elimina progetto."""
        try:
            result = self.project_service.delete_project(project_id)

            if result.success:
                # Invalida cache e rimuovi da selezione
                self.projects_cache = [p for p in self.projects_cache if p.get('id') != project_id]

                if self.selected_project and self.selected_project.get('id') == project_id:
                    self.selected_project = None
                    if 'active_project' in st.session_state:
                        del st.session_state.active_project

                st.success("✅ Progetto eliminato")
                logger.info(f"Progetto eliminato: {project_id}")
                return True
            else:
                st.error(f"❌ Errore eliminazione: {result.message}")
                return False

        except Exception as e:
            logger.error(f"Errore _delete_project: {e}")
            st.error(f"Errore eliminazione progetto: {e}")
            return False

    def get_active_project(self) -> Optional[Dict[str, Any]]:
        """Restituisce progetto attualmente attivo."""
        return self.selected_project

    def refresh_projects(self):
        """Aggiorna cache progetti."""
        self.projects_cache = []
        logger.info("Cache progetti aggiornata")

    def render(self):
        """Render componente principale."""
        # Determina modalità rendering
        if st.session_state.get('show_project_creator', False):
            self.render_project_creator()
        else:
            # Layout principale
            col1, col2 = st.columns([1, 3])

            with col1:
                self.render_compact()

            with col2:
                self.render_expanded()


def create_project_selector(on_project_change: Optional[Callable] = None) -> ProjectSelector:
    """Factory function per creare ProjectSelector."""
    return ProjectSelector(on_project_change)
