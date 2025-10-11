# Main Application - Project-Aware Version
"""
Versione progetto-aware di main.py per dimostrare integrazione
dopo migrazione multi-progetto.

Questa versione mostra come:
1. Integrare project switcher nella sidebar
2. Filtrare operazioni per progetto attivo
3. Mantenere contesto progetto tra pagine
4. Mostrare solo dati progetto selezionato
"""

import streamlit as st
import os
from datetime import datetime

# Import nuovo sistema progetti
from database_layer.dal.project_service import ProjectService
from database_layer.dal.project_repository import ProjectRepository
from database_layer.config_layer.project_config import ProjectConfig
from database_layer.context.execution_context import ExecutionContext

# Import funzionalità esistenti (adattate per progetto)
from file_utils import get_papers_dataframe, get_user_courses, get_user_tasks

def render_project_aware_sidebar():
    """Sidebar con project switcher integrato"""
    with st.sidebar:
        st.title("🤖 Archivista AI")

        # Project Switcher Section
        st.markdown("### 🏗️ Progetto Attivo")

        # Ottieni progetti utente
        project_service = ProjectService()
        projects = project_service.get_user_projects_with_stats(st.session_state['user_id'])

        if projects:
            # Crea opzioni dropdown
            project_options = {}
            current_project_name = "Seleziona progetto..."

            for project in projects:
                display_name = f"{project['name']}"
                if project.get('is_default', 0) == 1:
                    display_name += " ⭐ (Attivo)"
                    current_project_name = display_name

                project_options[display_name] = project['id']

            # Dropdown selezione progetto
            selected_display = st.selectbox(
                "Seleziona progetto:",
                options=["Seleziona progetto..."] + list(project_options.keys()),
                index=0 if st.session_state.get('current_project_id') is None else (
                    list(project_options.keys()).index(current_project_name)
                    if current_project_name in project_options else 0
                ),
                key="main_project_selector"
            )

            # Gestisci cambio progetto
            if selected_display != "Seleziona progetto...":
                new_project_id = project_options[selected_display]

                if new_project_id != st.session_state.get('current_project_id'):
                    # Cambia progetto attivo
                    switch_result = project_service.switch_user_project(
                        st.session_state['user_id'],
                        new_project_id
                    )

                    if switch_result['success']:
                        st.session_state.current_project_id = new_project_id
                        st.success(f"✅ Progetto cambiato: {selected_display.split(' ')[0]}")
                        st.rerun()
                    else:
                        st.error(f"❌ Errore cambio progetto: {switch_result.get('message')}")
            else:
                st.session_state.current_project_id = None

            # Mostra info progetto attivo
            if st.session_state.get('current_project_id'):
                current_project = next((p for p in projects if p['id'] == st.session_state.current_project_id), None)
                if current_project:
                    st.markdown("**📋 Info Progetto:**")
                    st.caption(f"📄 Documenti: {current_project.get('stats', {}).get('documents_count', 0)}")
                    st.caption(f"🎓 Corsi: {current_project.get('stats', {}).get('courses_count', 0)}")
                    st.caption(f"✅ Attività: {current_project.get('stats', {}).get('tasks_count', 0)}")

                    # Pulsante gestione progetti
                    if st.button("⚙️ Gestisci Progetti", key="manage_projects", use_container_width=True):
                        st.switch_page("pages/0_Projects.py")
        else:
            st.info("📭 Nessun progetto trovato")
            if st.button("📁 Crea Primo Progetto", key="create_first_project", use_container_width=True):
                st.switch_page("pages/0_Projects.py")

        st.divider()

        # Navigazione principale (filtrata per progetto)
        st.markdown("### 🧭 Navigazione")

        # Verifica progetto attivo per navigazione
        current_project_id = st.session_state.get('current_project_id')

        if current_project_id:
            # Navigazione progetto-aware
            nav_col1, nav_col2 = st.columns(2)

            with nav_col1:
                if st.button("💬 Chat", key="nav_chat", use_container_width=True):
                    st.switch_page("pages/1_Chat.py")

                if st.button("📚 Archivio", key="nav_archive", use_container_width=True):
                    st.switch_page("pages/2_Archivio.py")

            with nav_col2:
                if st.button("📝 Editor", key="nav_editor", use_container_width=True):
                    st.switch_page("pages/3_Editor.py")

                if st.button("🎓 Carriera", key="nav_carriera", use_container_width=True):
                    st.switch_page("pages/5_Carriera.py")

            # Navigazione avanzata
            st.markdown("**🔧 Funzioni Avanzate:**")
            adv_col1, adv_col2 = st.columns(2)

            with adv_col1:
                if st.button("🧠 Grafo", key="nav_grafo", use_container_width=True):
                    st.switch_page("pages/6_Grafo.py")

            with adv_col2:
                if st.button("🎯 Wizards", key="nav_wizards", use_container_width=True):
                    st.switch_page("pages/7_Workflow_Wizards.py")

        else:
            # Navigazione senza progetto (fallback)
            st.warning("⚠️ Seleziona un progetto per accedere alle funzionalità")

            if st.button("📁 Vai a Gestione Progetti", key="goto_projects", type="primary", use_container_width=True):
                st.switch_page("pages/0_Projects.py")

        st.divider()

        # Document Upload (progetto-aware)
        if current_project_id:
            st.markdown("### ➕ Aggiungi Documenti")

            # File uploader progetto-aware
            uploaded_files = st.file_uploader(
                "Trascina file qui",
                accept_multiple_files=True,
                type=['pdf', 'docx', 'txt', 'rtf', 'html', 'htm'],
                label_visibility="collapsed",
                key="project_aware_uploader"
            )

            if uploaded_files:
                st.success(f"📎 {len(uploaded_files)} file selezionati per progetto {current_project_id}")

                if st.button("🚀 Carica nel Progetto Attivo", key="upload_to_project", type="primary", use_container_width=True):
                    # Qui implementeresti caricamento progetto-aware
                    st.info("📤 Caricamento progetto-aware da implementare dopo migrazione")

        st.divider()

        # Status progetto-aware
        if current_project_id:
            st.markdown("### 📊 Stato Progetto")

            # Status specifico progetto
            try:
                project_repo = ProjectRepository()
                project = project_repo.find_by_id(current_project_id)

                if project:
                    st.success(f"✅ Progetto: {project['name']}")

                    # Attività recente progetto
                    activity = project_repo.get_project_activity_summary(current_project_id, days=1)
                    if activity.get('total_activity', 0) > 0:
                        st.info(f"🔥 Attivo oggi: {activity['total_activity']} operazioni")
                    else:
                        st.caption("💤 Nessuna attività recente")

            except Exception as e:
                st.error(f"Errore stato progetto: {e}")

def render_project_aware_dashboard():
    """Dashboard principale progetto-aware"""
    st.title("🎓 Dashboard Progetto")

    current_project_id = st.session_state.get('current_project_id')

    if not current_project_id:
        # Nessun progetto selezionato
        st.info("👋 **Seleziona un progetto** dalla sidebar per iniziare!")

        col1, col2 = st.columns([1, 2])

        with col1:
            if st.button("📁 Gestisci Progetti", type="primary", use_container_width=True):
                st.switch_page("pages/0_Projects.py")

        with col2:
            st.markdown("""
            **🚀 Per iniziare:**

            1. **Crea o seleziona** un progetto dalla sidebar
            2. **Carica documenti** nel progetto attivo
            3. **Esplora funzionalità** progetto-aware

            Ogni progetto mantiene i suoi dati separati!
            """)

        return

    # Dashboard progetto attivo
    project_repo = ProjectRepository()
    project = project_repo.find_by_id(current_project_id)

    if project:
        st.caption(f"**Progetto attivo:** {project['name']}")

        # Metriche progetto
        stats = project_repo.get_project_stats(current_project_id)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("📚 Documenti", stats.get('documents_count', 0))
        with col2:
            st.metric("🎓 Corsi", stats.get('courses_count', 0))
        with col3:
            st.metric("✅ Attività", stats.get('tasks_count', 0))
        with col4:
            st.metric("💬 Chat", stats.get('chat_sessions_count', 0))

        st.divider()

        # Contenuto progetto-aware
        render_project_content(current_project_id)

def render_project_content(project_id):
    """Render contenuto specifico progetto"""
    tab_chat, tab_docs, tab_courses, tab_tasks = st.tabs([
        "💬 Chat Progetto",
        "📚 Documenti Progetto",
        "🎓 Corsi Progetto",
        "✅ Attività Progetto"
    ])

    with tab_chat:
        st.markdown("#### 💬 Chat Contestuale Progetto")
        st.info(f"💭 Chat relativa al progetto: {project_id}")

        # Qui integreresti chat progetto-aware
        st.markdown("*Chat progetto-aware da implementare dopo migrazione*")

        if st.button("💬 Apri Chat Completa", key="open_project_chat"):
            st.switch_page("pages/1_Chat.py")

    with tab_docs:
        st.markdown("#### 📚 Documenti Progetto")

        try:
            # Filtra documenti per progetto (dopo migrazione)
            papers_df = get_papers_dataframe()

            # Nota: Dopo migrazione, filtreresti per project_id
            project_docs = papers_df  # Placeholder

            if not project_docs.empty:
                st.info(f"📄 **{len(project_docs)} documenti** nel progetto")

                # Mostra documenti progetto
                for _, doc in project_docs.head(5).iterrows():
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.markdown(f"**{doc.get('title', doc['file_name'])}**")
                        st.caption(f"📂 {doc.get('category_name', 'N/A')} | 📅 {doc.get('publication_year', 'N/A')}")

                    with col2:
                        if st.button("👁️", key=f"view_proj_doc_{doc['file_name']}", help="Visualizza"):
                            st.info(f"Visualizzazione documento progetto: {doc['file_name']}")

            else:
                st.info("📭 Nessun documento nel progetto")
                if st.button("📤 Carica Documenti", key="upload_project_docs"):
                    st.info("Upload progetto-aware da implementare")

        except Exception as e:
            st.error(f"Errore caricamento documenti progetto: {e}")

    with tab_courses:
        st.markdown("#### 🎓 Corsi Progetto")

        try:
            # Corsi progetto (dopo migrazione)
            user_courses = get_user_courses(st.session_state['user_id'])

            # Nota: Dopo migrazione, filtreresti per project_id
            project_courses = user_courses  # Placeholder

            if project_courses:
                st.info(f"🎓 **{len(project_courses)} corsi** nel progetto")

                for course in project_courses[:3]:  # Mostra primi 3
                    with st.expander(f"📖 {course['course_name']}"):
                        st.caption(f"Codice: {course.get('course_code', 'N/A')}")
                        if course.get('description'):
                            st.info(course['description'])

                        if st.button("👁️ Apri Corso", key=f"open_course_{course['id']}"):
                            st.switch_page("pages/5_Carriera.py")

            else:
                st.info("📭 Nessun corso nel progetto")

        except Exception as e:
            st.error(f"Errore caricamento corsi progetto: {e}")

    with tab_tasks:
        st.markdown("#### ✅ Attività Progetto")

        try:
            # Attività progetto (dopo migrazione)
            user_tasks = get_user_tasks(st.session_state['user_id'])

            # Nota: Dopo migrazione, filtreresti per project_id
            project_tasks = user_tasks  # Placeholder

            if project_tasks:
                st.info(f"✅ **{len(project_tasks)} attività** nel progetto")

                # Mostra attività per stato
                pending_tasks = [t for t in project_tasks if t['status'] == 'pending']
                in_progress_tasks = [t for t in project_tasks if t['status'] == 'in_progress']
                completed_tasks = [t for t in project_tasks if t['status'] == 'completed']

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("⏳ Pending", len(pending_tasks))
                with col2:
                    st.metric("🔄 In Progress", len(in_progress_tasks))
                with col3:
                    st.metric("✅ Completed", len(completed_tasks))

                # Mostra alcune attività recenti
                st.markdown("**📋 Attività Recenti:**")
                for task in project_tasks[:5]:
                    status_icon = {
                        'pending': '⏳',
                        'in_progress': '🔄',
                        'completed': '✅'
                    }.get(task['status'], '❓')

                    st.markdown(f"{status_icon} **{task['task_title']}**")
                    if task.get('due_date'):
                        st.caption(f"📅 Scadenza: {task['due_date'][:10]}")

            else:
                st.info("📭 Nessuna attività nel progetto")

        except Exception as e:
            st.error(f"Errore caricamento attività progetto: {e}")

def main_project_aware():
    """Main function progetto-aware"""
    st.set_page_config(
        page_title="Archivista AI - Progetto Aware",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Verifica autenticazione
    if 'user_id' not in st.session_state or not st.session_state['user_id']:
        st.error("**Accesso Negato** 🔒")
        if st.button("🔐 Vai al Login"):
            st.switch_page("pages/login.py")
        return

    # Render sidebar progetto-aware
    render_project_aware_sidebar()

    # Render dashboard progetto-aware
    render_project_aware_dashboard()

    # Footer progetto-aware
    st.divider()

    current_project_id = st.session_state.get('current_project_id')
    if current_project_id:
        st.caption(f"📋 **Contesto:** Progetto attivo: {current_project_id} | Utente: {st.session_state.get('username', 'User')}")
    else:
        st.caption("📋 **Contesto:** Seleziona un progetto per iniziare | Utente: {st.session_state.get('username', 'User')}")

if __name__ == "__main__":
    main_project_aware()
