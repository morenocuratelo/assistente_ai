# Pagina Progetti - Gestione Progetti Multi-Tenant
"""
Pagina principale per gestione progetti in Archivista AI.

Fornisce:
- Lista progetti utente con statistiche
- Creazione nuovi progetti
- Modifica progetti esistenti
- Eliminazione progetti
- Switch progetto attivo
- Importazione/esportazione progetti
"""

import streamlit as st
import json
from datetime import datetime
from database_layer.dal.project_service import ProjectService
from database_layer.dal.project_repository import ProjectRepository
from database_layer.config_layer.project_config import ProjectConfig

# --- AUTHENTICATION CHECK ---
if 'user_id' not in st.session_state or not st.session_state['user_id']:
    st.error("🚫 Accesso negato. Effettua prima il login.")
    st.stop()

user_id = st.session_state['user_id']
username = st.session_state.get('username', 'User')

# --- PAGE CONFIG ---
st.set_page_config(page_title="📁 Progetti - Archivista AI", page_icon="📁", layout="wide")
st.title("📁 Gestione Progetti")
st.caption(f"**{username}** - Organizza il tuo lavoro in spazi dedicati")

# --- INITIALIZATION ---
if 'current_project_id' not in st.session_state:
    st.session_state.current_project_id = None

if 'show_create_project' not in st.session_state:
    st.session_state.show_create_project = False

if 'show_edit_project' not in st.session_state:
    st.session_state.show_edit_project = False

if 'project_to_edit' not in st.session_state:
    st.session_state.project_to_edit = None

# --- SERVICES ---
@st.cache_resource
def get_project_service():
    """Service per gestione progetti"""
    return ProjectService()

@st.cache_data(ttl=30)
def get_user_projects(_user_id):
    """Progetti utente con cache"""
    service = get_project_service()
    return service.get_user_projects_with_stats(_user_id)

# --- SIDEBAR ---
with st.sidebar:
    st.header("🎯 Navigazione Rapida")

    # Project Switcher
    projects = get_user_projects(user_id)

    if projects:
        st.subheader("🔄 Cambia Progetto")

        # Dropdown selezione progetto
        project_options = ["Seleziona progetto..."]
        project_dict = {}

        for project in projects:
            display_name = f"{project['name']}"
            if project.get('is_default', 0) == 1:
                display_name += " ⭐ (Attivo)"
            elif project.get('stats', {}).get('total_items', 0) == 0:
                display_name += " (Vuoto)"

            project_options.append(display_name)
            project_dict[display_name] = project['id']

        current_project_name = "Seleziona progetto..."
        if st.session_state.current_project_id:
            current_project = next((p for p in projects if p['id'] == st.session_state.current_project_id), None)
            if current_project:
                current_project_name = f"{current_project['name']} ⭐"

        selected_display = st.selectbox(
            "Progetto attivo:",
            options=project_options,
            index=0 if current_project_name == "Seleziona progetto..." else (
                next(i for i, opt in enumerate(project_options) if opt.startswith(current_project_name.split(' ')[0]))
                if current_project_name != "Seleziona progetto..." else 0
            ),
            key="project_selector"
        )

        if selected_display != "Seleziona progetto...":
            new_project_id = project_dict[selected_display]
            if new_project_id != st.session_state.current_project_id:
                # Cambia progetto attivo
                service = get_project_service()
                result = service.switch_user_project(user_id, new_project_id)

                if result['success']:
                    st.session_state.current_project_id = new_project_id
                    st.success(f"✅ Progetto cambiato: {selected_display.split(' ')[0]}")
                    st.rerun()
                else:
                    st.error(f"❌ Errore cambio progetto: {result.get('message', 'Errore sconosciuto')}")
    else:
        st.info("📭 Nessun progetto trovato")

    st.divider()

    # Quick Actions
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Nuovo", key="quick_create", use_container_width=True):
            st.session_state.show_create_project = True
            st.session_state.show_edit_project = False
    with col2:
        if st.button("📊 Dashboard", key="quick_dashboard", use_container_width=True):
            st.switch_page("main.py")

    # Current Project Info
    if st.session_state.current_project_id:
        current_project = next((p for p in projects if p['id'] == st.session_state.current_project_id), None)
        if current_project:
            st.subheader("📋 Progetto Attivo")
            st.info(f"**{current_project['name']}**")
            st.caption(f"Documenti: {current_project.get('stats', {}).get('documents_count', 0)}")
            st.caption(f"Corsi: {current_project.get('stats', {}).get('courses_count', 0)}")
            st.caption(f"Attività: {current_project.get('stats', {}).get('tasks_count', 0)}")

# --- MAIN CONTENT ---

# Handle form displays
if st.session_state.show_create_project:
    render_create_project_form()
elif st.session_state.show_edit_project and st.session_state.project_to_edit:
    render_edit_project_form(st.session_state.project_to_edit)
else:
    render_projects_dashboard()

def render_projects_dashboard():
    """Dashboard principale progetti"""
    st.header("📂 I Miei Progetti")

    # Quick Stats
    projects = get_user_projects(user_id)
    total_projects = len(projects)
    active_project = next((p for p in projects if p.get('is_default', 0) == 1), None)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📁 Progetti Totali", total_projects)
    with col2:
        total_docs = sum(p.get('stats', {}).get('documents_count', 0) for p in projects)
        st.metric("📚 Documenti Totali", total_docs)
    with col3:
        total_courses = sum(p.get('stats', {}).get('courses_count', 0) for p in projects)
        st.metric("🎓 Corsi Totali", total_courses)
    with col4:
        total_tasks = sum(p.get('stats', {}).get('tasks_count', 0) for p in projects)
        st.metric("✅ Attività Totali", total_tasks)

    st.divider()

    if not projects:
        # No projects yet
        render_empty_projects_state()
    else:
        # Projects grid/list
        render_projects_grid(projects)

def render_empty_projects_state():
    """Stato vuoto - nessun progetto"""
    st.info("🚀 **Benvenuto!** Crea il tuo primo progetto per iniziare.")

    col1, col2 = st.columns([1, 2])

    with col1:
        if st.button("➕ Crea Primo Progetto", type="primary", use_container_width=True):
            st.session_state.show_create_project = True
            st.rerun()

    with col2:
        st.markdown("""
        **💡 Suggerimenti per iniziare:**

        • **Progetto Università** - Per documenti accademici
        • **Progetto Lavoro** - Per documenti professionali
        • **Progetto Personale** - Per uso privato

        Ogni progetto mantiene i dati separati e organizzati!
        """)

def render_projects_grid(projects):
    """Render grid progetti con azioni"""
    st.subheader("📋 Progetti Disponibili")

    # Filter and sort projects
    sorted_projects = sorted(projects, key=lambda p: (
        0 if p.get('is_default', 0) == 1 else 1,  # Default first
        p.get('stats', {}).get('total_items', 0),  # Then by activity
        p['name']  # Finally alphabetically
    ), reverse=True)

    # Projects per row
    projects_per_row = 2

    for i in range(0, len(sorted_projects), projects_per_row):
        cols = st.columns(projects_per_row)

        for j in range(projects_per_row):
            if i + j < len(sorted_projects):
                project = sorted_projects[i + j]
                render_project_card(project, cols[j])

def render_project_card(project, col):
    """Render singola card progetto"""
    with col:
        # Project card styling
        is_active = project.get('is_default', 0) == 1
        card_style = "border: 2px solid #2196f3; background-color: #f0f8ff;" if is_active else ""

        st.markdown(f"""
        <div style="{card_style}" class="project-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h3>{"📁" if not is_active else "📂"} {project['name']}</h3>
                {"⭐" if is_active else ""}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Project description
        if project.get('description'):
            st.caption(project['description'])

        # Project stats
        stats = project.get('stats', {})
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("📄", stats.get('documents_count', 0))
        with col2:
            st.metric("🎓", stats.get('courses_count', 0))
        with col3:
            st.metric("✅", stats.get('tasks_count', 0))
        with col4:
            st.metric("💬", stats.get('chat_sessions_count', 0))

        # Recent activity
        activity = project.get('recent_activity', {})
        if activity.get('total_activity', 0) > 0:
            st.caption(f"🕐 Attività recente: {activity['total_activity']} elementi (7gg)")
        else:
            st.caption("💤 Nessuna attività recente")

        # Project role
        role = project.get('role', 'member')
        role_colors = {
            'owner': '🟢 Owner',
            'admin': '🟡 Admin',
            'member': '🔵 Member',
            'viewer': '⚪ Viewer'
        }
        st.caption(f"Ruolo: {role_colors.get(role, role)}")

        st.markdown("---")

        # Action buttons
        col_a, col_b, col_c, col_d = st.columns(4)

        with col_a:
            if st.button("👁️ Apri", key=f"open_{project['id']}", use_container_width=True):
                # Switch to project
                service = get_project_service()
                result = service.switch_user_project(user_id, project['id'])
                if result['success']:
                    st.session_state.current_project_id = project['id']
                    st.success(f"✅ Progetto attivo: {project['name']}")
                    st.rerun()

        with col_b:
            if st.button("✏️ Modifica", key=f"edit_{project['id']}", use_container_width=True):
                st.session_state.project_to_edit = project['id']
                st.session_state.show_edit_project = True
                st.session_state.show_create_project = False
                st.rerun()

        with col_c:
            if st.button("📤 Esporta", key=f"export_{project['id']}", use_container_width=True):
                st.info("Funzione esportazione progetto da implementare")

        with col_d:
            if st.button("🗑️ Elimina", key=f"delete_{project['id']}", use_container_width=True):
                if role in ['owner']:  # Only owners can delete
                    st.session_state.project_to_delete = project['id']
                    st.rerun()
                else:
                    st.error("❌ Solo il proprietario può eliminare il progetto")

def render_create_project_form():
    """Form creazione nuovo progetto"""
    st.header("➕ Crea Nuovo Progetto")

    with st.form("create_project_form"):
        col1, col2 = st.columns([2, 1])

        with col1:
            project_id = st.text_input(
                "ID Progetto*",
                placeholder="es. universita, lavoro, personale",
                help="ID univoco (solo lettere, numeri, underscore)"
            )

            project_name = st.text_input(
                "Nome Progetto*",
                placeholder="es. Università, Lavoro, Personale",
                help="Nome descrittivo del progetto"
            )

            project_description = st.text_area(
                "Descrizione",
                placeholder="Breve descrizione del progetto...",
                height=80
            )

        with col2:
            st.markdown("### 🎯 Template Progetto")

            template = st.radio(
                "Tipo progetto:",
                options=["default", "academic", "research", "personal"],
                format_func=lambda x: {
                    "default": "📄 Progetto Standard",
                    "academic": "🎓 Progetto Accademico",
                    "research": "🔬 Progetto Ricerca",
                    "personal": "🏠 Progetto Personale"
                }.get(x, x.title()),
                key="project_template"
            )

            st.markdown("**💡 Caratteristiche template:**")

            template_info = {
                "default": "Configurazione base per uso generale",
                "academic": "Ottimizzato per documenti accademici e corsi",
                "research": "Configurazione avanzata per ricerca e analisi",
                "personal": "Impostazioni per uso privato e personale"
            }

            st.info(template_info.get(template, "Template non trovato"))

        # Submit buttons
        col_submit, col_cancel = st.columns([1, 1])

        with col_submit:
            submit = st.form_submit_button("🚀 Crea Progetto", type="primary", use_container_width=True)

        with col_cancel:
            cancel = st.form_submit_button("❌ Annulla", use_container_width=True)

        if submit:
            if not project_id or not project_name:
                st.error("❌ ID progetto e nome sono obbligatori")
            else:
                # Crea progetto
                service = get_project_service()

                try:
                    result = service.create_project_with_validation(
                        project_id.strip(),
                        user_id,
                        project_name.strip(),
                        project_description.strip() if project_description else None
                    )

                    if result['success']:
                        st.success(f"✅ Progetto '{project_name}' creato con successo!")

                        # Switch to new project
                        st.session_state.current_project_id = project_id
                        st.session_state.show_create_project = False

                        st.info("🔄 Ricarica pagina per vedere il nuovo progetto...")
                        st.rerun()
                    else:
                        st.error(f"❌ Errore creazione progetto: {result.get('message', 'Errore sconosciuto')}")

                except Exception as e:
                    st.error(f"❌ Errore creazione progetto: {e}")

        if cancel:
            st.session_state.show_create_project = False
            st.rerun()

def render_edit_project_form(project_id):
    """Form modifica progetto esistente"""
    st.header("✏️ Modifica Progetto")

    try:
        # Ottieni dati progetto
        repo = ProjectRepository()
        project = repo.find_by_id(project_id)

        if not project:
            st.error(f"❌ Progetto non trovato: {project_id}")
            st.session_state.show_edit_project = False
            st.rerun()
            return

        # Verifica permessi modifica
        permissions = repo.get_user_permissions_in_project(user_id, project_id)
        if not permissions['permissions'].get('can_manage_settings'):
            st.error("❌ Permessi insufficienti per modificare progetto")
            st.session_state.show_edit_project = False
            st.rerun()
            return

        with st.form("edit_project_form"):
            # Mostra info progetto corrente
            st.info(f"**Progetto:** {project['name']} | **ID:** {project['id']}")

            # Campi modifica
            new_name = st.text_input(
                "Nome Progetto",
                value=project['name'],
                key="edit_project_name"
            )

            new_description = st.text_area(
                "Descrizione",
                value=project.get('description', ''),
                height=80,
                key="edit_project_description"
            )

            # Template corrente (solo visualizzazione)
            st.caption(f"Template: {project.get('settings', {}).get('template', 'default')}")

            # Submit buttons
            col1, col2, col3 = st.columns([1, 1, 1])

            with col1:
                save = st.form_submit_button("💾 Salva Modifiche", type="primary", use_container_width=True)

            with col2:
                reset = st.form_submit_button("🔄 Ripristina", use_container_width=True)

            with col3:
                cancel = st.form_submit_button("❌ Annulla", use_container_width=True)

            if save:
                if not new_name.strip():
                    st.error("❌ Nome progetto obbligatorio")
                else:
                    # Salva modifiche
                    repo = ProjectRepository()
                    success = repo.update_project(
                        project_id,
                        name=new_name.strip(),
                        description=new_description.strip() if new_description else None
                    )

                    if success:
                        st.success("✅ Progetto aggiornato con successo!")
                        st.session_state.show_edit_project = False
                        st.rerun()
                    else:
                        st.error("❌ Errore salvataggio modifiche")

            if reset:
                # Ripristina valori originali
                st.rerun()

            if cancel:
                st.session_state.show_edit_project = False
                st.session_state.project_to_edit = None
                st.rerun()

    except Exception as e:
        st.error(f"❌ Errore modifica progetto: {e}")
        st.session_state.show_edit_project = False

# --- FOOTER INFO ---
st.divider()

# Current context info
if st.session_state.current_project_id:
    st.caption(f"📋 **Contesto Attuale:** Progetto attivo: {st.session_state.current_project_id}")
else:
    st.caption("📋 **Contesto Attuale:** Nessun progetto attivo")

# Tips
with st.expander("💡 Suggerimenti Utili"):
    st.markdown("""
    **🎯 Best Practices Progetti:**

    • **Nomi descrittivi** - Usa nomi chiari per identificare facilmente i progetti
    • **Separazione logica** - Crea progetti per ambiti diversi (studio, lavoro, personale)
    • **Progetto default** - Usa "Wiki Globale" per documenti generici
    • **Regolare pulizia** - Archivia o elimina progetti non più utilizzati

    **🔐 Sicurezza:**

    • Ogni progetto ha permessi indipendenti
    • Solo owner può eliminare progetto
    • Admin può gestire utenti progetto
    • Member può leggere/scrivere contenuti
    """)

if __name__ == "__main__":
    pass
