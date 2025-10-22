import streamlit as st
import pandas as pd
import json
from datetime import datetime, date
from scripts.utilities.file_utils import (
    get_user_courses, create_course, update_course, delete_course,
    get_course_lectures, create_lecture, update_lecture,
    get_user_tasks, create_task, update_task, delete_task,
    get_papers_dataframe, get_archive_tree
)
from tools.knowledge_structure import KNOWLEDGE_BASE_STRUCTURE

# --- STILE CSS ---
st.markdown("""
<style>
    .course-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
        background-color: #f9f9f9;
    }
    .task-card {
        border: 1px solid #e1e1e1;
        border-radius: 6px;
        padding: 12px;
        margin-bottom: 8px;
        background-color: white;
    }
    .task-completed {
        background-color: #f0f8f0;
        border-color: #28a745;
    }
    .task-pending {
        background-color: #fff3cd;
        border-color: #ffc107;
    }
    .task-in-progress {
        background-color: #cce7ff;
        border-color: #007bff;
    }
    .priority-high {
        color: #dc3545;
        font-weight: bold;
    }
    .priority-medium {
        color: #ffc107;
    }
    .priority-low {
        color: #28a745;
    }
    .keyword-tag {
        display: inline-block;
        background-color: #e9ecef;
        color: #495057;
        padding: 2px 8px;
        margin: 2px;
        border-radius: 12px;
        font-size: 0.8em;
    }
</style>
""", unsafe_allow_html=True)

# --- AUTHENTICATION CHECK ---
if 'user_id' not in st.session_state or not st.session_state['user_id']:
    st.error("🚫 Accesso negato. Effettua prima il login.")
    st.stop()

user_id = st.session_state['user_id']
username = st.session_state.get('username', 'User')

# --- PAGE CONFIG ---
st.title("🎓 Carriera Accademica")
st.markdown(f"**Benvenuto, {username}!** Gestisci i tuoi corsi universitari, lezioni, materiali e attività.")

# Quick access to Knowledge Graph
if st.button("🧠 📊 Esplora Grafo della Conoscenza", help="Visualizza le connessioni concettuali estratte dai tuoi documenti"):
    st.switch_page("pages/6_Grafo.py")

st.divider()

# --- SESSION STATE MANAGEMENT ---
if 'selected_course_id' not in st.session_state:
    st.session_state.selected_course_id = None
if 'selected_lecture_id' not in st.session_state:
    st.session_state.selected_lecture_id = None
if 'show_course_form' not in st.session_state:
    st.session_state.show_course_form = False
if 'show_lecture_form' not in st.session_state:
    st.session_state.show_lecture_form = False
if 'show_task_form' not in st.session_state:
    st.session_state.show_task_form = False

# --- FUNCTIONS ---
def format_date(date_str):
    """Format date for display"""
    if not date_str:
        return ""
    try:
        return datetime.fromisoformat(date_str).strftime("%d/%m/%Y")
    except:
        return date_str

def get_priority_color(priority):
    """Get color class for priority"""
    colors = {'low': 'priority-low', 'medium': 'priority-medium', 'high': 'priority-high'}
    return colors.get(priority, 'priority-medium')

def get_task_status_color(status):
    """Get color class for task status"""
    colors = {'pending': 'task-pending', 'in_progress': 'task-in-progress', 'completed': 'task-completed', 'cancelled': 'task-completed'}
    return colors.get(status, 'task-pending')

def display_kanban_task(task, column_type):
    """Display a task in Kanban board format"""
    status_class = get_task_status_color(task['status'])
    priority_class = get_priority_color(task['priority'])

    priority_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
    status_icon = {'pending': '⏳', 'in_progress': '🔄', 'completed': '✅', 'cancelled': '❌'}

    st.markdown(f"""
    <div class="task-card {status_class}" style="margin-bottom: 10px; padding: 10px;">
        <h5>{status_icon[task['status']]} {task['task_title'][:25]}{'...' if len(task['task_title']) > 25 else ''}</h5>
        <p style="font-size: 0.85em; margin: 5px 0;"><span class="keyword-tag {priority_class}">🔥 {task['priority'].title()}</span></p>
        {f'<p style="font-size: 0.8em;">📅 {format_date(task.get("due_date"))}</p>' if task.get('due_date') else ''}
    </div>
    """, unsafe_allow_html=True)

    # Task actions
    col_a, col_b = st.columns([1,1])
    with col_a:
        if task['status'] != 'completed':
            if st.button("✅", key=f"complete_task_{task['id']}_{column_type}", help="Completa"):
                update_task(task['id'], status='completed')
                st.rerun()
    with col_b:
        if st.button("📝", key=f"edit_task_{task['id']}_{column_type}", help="Modifica"):
            st.info("Modifica task da implementare")

# --- SIDEBAR MENU ---
with st.sidebar:
    st.header("📚 Navigazione Carriera")

    # Courses Menu
    st.subheader("📖 Corsi")
    courses = get_user_courses(user_id)

    if courses:
        for course in courses:
            if st.button(f"• {course['course_name']}", key=f"course_{course['id']}", use_container_width=True):
                st.session_state.selected_course_id = course['id']
                st.session_state.selected_lecture_id = None
                st.rerun()
    else:
        st.info("Nessun corso trovato. Crea il primo corso!")

    st.divider()

    # Action Buttons
    if st.button("➕ Nuovo Corso", use_container_width=True):
        st.session_state.show_course_form = True
        st.session_state.show_lecture_form = False
        st.session_state.show_task_form = False
        st.rerun()

    if st.session_state.selected_course_id:
        if st.button("➕ Nuova Lezione", use_container_width=True):
            st.session_state.show_lecture_form = True
            st.session_state.show_task_form = False
            st.rerun()

    if st.button("🎯 Gestiona Attività", use_container_width=True):
        st.session_state.show_task_form = True
        st.session_state.show_course_form = False
        st.session_state.show_lecture_form = False
        st.rerun()

    st.divider()

    # Statistics
    st.subheader("📊 Statistiche")
    if courses:
        total_courses = len(courses)
        total_lectures = sum(len(get_course_lectures(course['id'])) for course in courses)
        total_tasks = len(get_user_tasks(user_id))
        completed_tasks = len([t for t in get_user_tasks(user_id) if t['status'] == 'completed'])

        st.metric("Corsi", total_courses)
        st.metric("Lezioni", total_lectures)
        st.metric("Attività", f"{completed_tasks}/{total_tasks}")

# --- MAIN CONTENT ---

# Handle form displays in session state
if st.session_state.show_course_form:
    st.header("🆕 Nuovo Corso")

    with st.form("course_form"):
        course_name = st.text_input("Nome Corso*", placeholder="es. Programmazione Python")
        course_code = st.text_input("Codice Corso", placeholder="es. INFO101")
        description = st.text_area("Descrizione", height=100)

        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("💾 Crea Corso")
        with col2:
            cancel = st.form_submit_button("❌ Annulla")

        if submit and course_name.strip():
            try:
                create_course(user_id, course_name.strip(), course_code.strip() if course_code else None, description.strip() if description else None)
                st.success("✅ Corso creato con successo!")
                st.session_state.show_course_form = False
                if 'selected_course_id' in st.session_state:
                    del st.session_state.selected_course_id
                st.rerun()
            except Exception as e:
                st.error(f"❌ Errore nella creazione del corso: {e}")
        elif submit:
            st.error("⚠️ Il nome del corso è obbligatorio")

        if cancel:
            st.session_state.show_course_form = False
            st.rerun()

elif st.session_state.show_lecture_form and st.session_state.selected_course_id:
    st.header("🆕 Nuova Lezione")

    with st.form("lecture_form"):
        lecture_title = st.text_input("Titolo Lezione*", placeholder="es. Introduzione alle Variabili")
        lecture_date = st.date_input("Data Lezione", value=date.today())
        description = st.text_area("Descrizione", height=80)

        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("💾 Crea Lezione")
        with col2:
            cancel = st.form_submit_button("❌ Annulla")

        if submit and lecture_title.strip():
            try:
                create_lecture(st.session_state.selected_course_id, lecture_title.strip(), lecture_date.isoformat(), description.strip() if description else None)
                st.success("✅ Lezione creata con successo!")
                st.session_state.show_lecture_form = False
                st.rerun()
            except Exception as e:
                st.error(f"❌ Errore nella creazione della lezione: {e}")
        elif submit:
            st.error("⚠️ Il titolo della lezione è obbligatorio")

        if cancel:
            st.session_state.show_lecture_form = False
            st.rerun()

elif st.session_state.show_task_form:
    st.header("🎯 Gestione Attività")

    # Show existing tasks
    tasks = get_user_tasks(user_id)
    if tasks:
        st.subheader("📋 Attività Attuali")
        for task in tasks:
            status_class = get_task_status_color(task['status'])
            priority_class = get_priority_color(task['priority'])

            priority_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
            status_icon = {'pending': '⏳', 'in_progress': '🔄', 'completed': '✅', 'cancelled': '❌'}

            st.markdown(f"""
            <div class="task-card {status_class}">
                <h4>{status_icon[task['status']]} {task['task_title']}</h4>
                <p>{task['task_description'] or 'Nessuna descrizione'}</p>
                <div>
                    <span class="keyword-tag {priority_class}">🔥 Priorità {task['priority'].upper()}</span>
                    <span class="keyword-tag">{task['task_type'].replace('_', ' ').title()}</span>
                    {f'<span class="keyword-tag">📅 Scadenza: {format_date(task["due_date"])}</span>' if task['due_date'] else ''}
                </div>
            </div>
            """, unsafe_allow_html=True)

            col1, col2, col3 = st.columns([1,1,1])
            with col1:
                if st.button("✏️ Modifica", key=f"edit_task_{task['id']}", use_container_width=True):
                    st.info("Funzione di modifica attività da implementare")
            with col2:
                if task['status'] != 'completed':
                    if st.button("✅ Completa", key=f"complete_task_{task['id']}", use_container_width=True):
                        update_task(task['id'], status='completed')
                        st.rerun()
            with col3:
                if st.button("🗑️ Elimina", key=f"delete_task_{task['id']}", use_container_width=True):
                    try:
                        delete_task(task['id'])
                        st.success("Attività eliminata!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Errore nell'eliminazione: {e}")
    else:
        st.info("Nessuna attività trovata. Saranno generate automaticamente dai documenti caricati.")

    # New task form
    st.subheader("➕ Nuova Attività")
    with st.form("task_form"):
        task_title = st.text_input("Titolo Attività*", placeholder="es. Ripassa teoremi fondamentali")
        task_description = st.text_area("Descrizione", height=80)
        priority = st.selectbox("Priorità", ["low", "medium", "high"], index=1)
        task_type = st.selectbox("Tipo", ["short_term", "medium_term", "long_term"], format_func=lambda x: x.replace('_', ' ').title(), index=0)
        due_date = st.date_input("Scadenza (opzionale)")

        courses_for_task = get_user_courses(user_id)
        course_options = ["Nessuno"] + [f"{c['course_name']} ({c['course_code'] or 'No Code'})" for c in courses_for_task]
        selected_course = st.selectbox("Corso Associato", course_options)

        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("💾 Crea Attività")
        with col2:
            cancel = st.form_submit_button("❌ Annulla")

        if submit and task_title.strip():
            course_id = None
            if selected_course != "Nessuno":
                course_name = selected_course.split(' (')[0]
                course = next((c for c in courses_for_task if c['course_name'] == course_name), None)
                if course:
                    course_id = course['id']

            try:
                create_task(
                    user_id=user_id,
                    course_id=course_id,
                    task_title=task_title.strip(),
                    task_description=task_description.strip() if task_description else None,
                    priority=priority,
                    task_type=task_type,
                    due_date=due_date.isoformat()
                )
                st.success("✅ Attività creata con successo!")
                st.session_state.show_task_form = False
                st.rerun()
            except Exception as e:
                st.error(f"❌ Errore nella creazione dell'attività: {e}")
        elif submit:
            st.error("⚠️ Il titolo dell'attività è obbligatorio")

        if cancel:
            st.session_state.show_task_form = False
            st.rerun()

else:
    # --- DASHBOARD PRINCIPALE ---

    # Overview Metrics
    col1, col2, col3, col4 = st.columns(4)
    courses = get_user_courses(user_id)
    tasks = get_user_tasks(user_id)
    papers_df = get_papers_dataframe()
    total_materials = len(papers_df)

    with col1:
        st.metric("📚 Corsi", len(courses))
    with col2:
        total_lectures = sum(len(get_course_lectures(c['id'])) for c in courses)
        st.metric("📝 Lezioni", total_lectures)
    with col3:
        st.metric("📄 Materiali", total_materials)
    with col4:
        completed_tasks = len([t for t in tasks if t['status'] == 'completed'])
        st.metric("✅ Attività Completate", f"{completed_tasks}/{len(tasks)}")

    st.divider()

    # Selected Course View - Unified tabbed interface
    if st.session_state.selected_course_id:
        courses = get_user_courses(user_id)
        selected_course = next((c for c in courses if c['id'] == st.session_state.selected_course_id), None)

        if selected_course:
            st.header(f"📖 {selected_course['course_name']}")
            if selected_course['course_code']:
                st.subheader(f"Codice: {selected_course['course_code']}")
            if selected_course['description']:
                st.info(selected_course['description'])

            # Course actions row
            col1, col2, col3 = st.columns([1,1,1])
            with col1:
                if st.button("⬅️ Torna ai Corsi", use_container_width=True):
                    st.session_state.selected_course_id = None
                    st.rerun()
            with col2:
                if st.button("✏️ Modifica Corso", use_container_width=True):
                    st.info("Funzione di modifica corso da implementare")
            with col3:
                if st.button("💬 Chat su questo Corso", use_container_width=True):
                    st.switch_page("pages/1_💬_Chat.py")

            st.divider()

            # Tabbed interface for course content
            tab_lezioni, tab_compiti, tab_archivio = st.tabs([
                "📝 Lezioni",
                "🎯 Compiti & Esami",
                "🗂️ Archivio Corso"
            ])

            # Tab 1: Lezioni (chronological list with materials, keywords, tasks)
            with tab_lezioni:
                st.subheader("📚 Lezioni - Cronologia Completa")

                lectures = get_course_lectures(selected_course['id'])

                if lectures:
                    # Sort by date, newest first
                    lectures_sorted = sorted(lectures, key=lambda x: x.get('lecture_date', '1970-01-01'), reverse=True)

                    for lecture in lectures_sorted:
                        with st.expander(
                            f"🗓️ {format_date(lecture.get('lecture_date'))} - {lecture['lecture_title']}",
                            expanded=False
                        ):
                            # Description
                            if lecture['description']:
                                st.info(lecture['description'])

                            # AI-Extracted Keywords
                            if lecture.get('keywords'):
                                st.markdown("**🏷️ Parole Chiave Estratte dall'AI:**")
                                keywords_html = " ".join([f'<span class="keyword-tag">{kw}</span>' for kw in lecture['keywords'][:10]])
                                st.markdown(keywords_html, unsafe_allow_html=True)
                            else:
                                st.caption("🔄 Parole chiave verranno estratte automaticamente dai documenti caricati.")

                            # Associated Materials
                            from file_utils import get_materials_for_lecture
                            materials = get_materials_for_lecture(lecture['id'])

                            if materials:
                                st.markdown("**📋 Materiali della Lezione:**")
                                for material in materials:
                                    col_a, col_b = st.columns([4,1])
                                    with col_a:
                                        st.write(f"📄 {material['file_name']} ({material['material_type']})")
                                    with col_b:
                                        if st.button("👁️", key=f"view_mat_{material['id']}", help="Visualizza materiale"):
                                            st.info("Visualizzazione materiale da implementare")

                            # AI-Generated Tasks for this lecture
                            st.markdown("**🎯 Attività Raccomandate dall'AI:**")
                            course_tasks = [t for t in get_user_tasks(user_id) if t.get('lecture_id') == lecture['id']]

                            if course_tasks:
                                for task in course_tasks:
                                    priority_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
                                    status_icon = {'pending': '⏳', 'in_progress': '🔄', 'completed': '✅'}

                                    st.markdown(f"""
                                    {status_icon[task['status']]} **{task['task_title']}**
                                    - Priorità: <span style='color:{priority_icon[task['priority']] if task['priority'] in priority_icon.keys() else "#666"};font-weight:bold;'>{task['priority'].upper()}</span>
                                    {"- Scadenza: " + format_date(task.get('due_date')) if task.get('due_date') else ""}
                                    """, unsafe_allow_html=True)

                                    if task['task_description']:
                                        st.caption(task['task_description'])
                            else:
                                st.caption("📝 Carica documenti relativi a questa lezione per ricevere suggerimenti di attività dall'AI.")

                            # Actions
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                if st.button("➕ Carica Materiale", key=f"upload_lecture_{lecture['id']}", use_container_width=True):
                                    st.info("Funzione 'Carica materiale per lezione' da collegare alla dashboard principale")
                            with col2:
                                if st.button("🎯 Aggiungi Task", key=f"add_task_lecture_{lecture['id']}", use_container_width=True):
                                    st.session_state.selected_lecture_id = lecture['id']
                                    st.session_state.show_task_form = True
                                    st.rerun()
                            with col3:
                                if st.button("✏️ Modifica", key=f"edit_lecture_{lecture['id']}", use_container_width=True):
                                    st.info("Modifica lezione da implementare")

                else:
                    st.info("📝 **Nessuna lezione per questo corso.**")

                    col1, col2 = st.columns([1,3])
                    with col1:
                        if st.button("➕ Crea Prima Lezione", type="primary", use_container_width=True):
                            st.session_state.show_lecture_form = True
                            st.rerun()
                    with col2:
                        st.markdown("*Le lezioni appaiono ordinate per data. Ogni lezione può avere materiali associati, parole chiave AI e attività raccomandate.*")

            # Tab 2: Compiti & Esami (Kanban board style)
            with tab_compiti:
                st.subheader("🎯 Compiti, Esami e Attività")

                # Kanban board columns
                tasks = get_user_tasks(user_id)
                course_tasks = [t for t in tasks if t.get('course_id') == selected_course['id']]

                # Filter by task type for this academic context
                short_term_tasks = [t for t in course_tasks if t['task_type'] == 'short_term']
                medium_term_tasks = [t for t in course_tasks if t['task_type'] == 'medium_term']
                long_term_tasks = [t for t in course_tasks if t['task_type'] == 'long_term']

                col1, col2, col3 = st.columns(3)

                # Short-term column (Questa Settimana)
                with col1:
                    st.markdown("### 🗓️ Questa Settimana")
                    if short_term_tasks:
                        for task in short_term_tasks:
                            display_kanban_task(task, "short")
                    else:
                        st.caption("Nessun compito a breve termine")

                # Medium-term column (Prossimi Giorni)
                with col2:
                    st.markdown("### 📅 Prossimi Giorni")
                    if medium_term_tasks:
                        for task in medium_term_tasks:
                            display_kanban_task(task, "medium")
                    else:
                        st.caption("Nessun compito a medio termine")

                # Long-term column (Esami, Progetti)
                with col3:
                    st.markdown("### 🎓 Esami & Progetti")
                    if long_term_tasks:
                        for task in long_term_tasks:
                            display_kanban_task(task, "long")
                    else:
                        st.caption("Nessun esame o progetto a lungo termine")

                # Add new task button
                st.divider()
                col1, col2 = st.columns([1,4])
                with col1:
                    if st.button("➕ Nuovo Compito", type="primary", use_container_width=True):
                        st.session_state.selected_lecture_id = None  # Reset lecture selection
                        st.session_state.show_task_form = True
                        st.rerun()

                st.info("💡 **Suggerimento:** Le attività vengono generate automaticamente quando carichi documenti accademici!")

            # Tab 3: Archivio Corso (filtered document library)
            with tab_archivio:
                st.subheader("🗂️ Archivio Corso - Materiali Digitali")

                # Filter documents by course association
                papers_df = get_papers_dataframe()
                # For now, show all documents - in future, filter by course/material associations
                course_materials = papers_df  # Placeholder - should filter by course_id

                if not course_materials.empty:
                    st.info(f"📚 **{len(course_materials)} documenti** disponibili nel corso.")

                    # Simple list view of documents
                    for _, doc in course_materials.head(10).iterrows():
                        col1, col2 = st.columns([3,1])
                        with col1:
                            st.markdown(f"""
                            **📄 {doc['title'] or doc['file_name']}**
                            - *{doc['category_name']}*
                            - Autori: {doc.get('authors', 'N/A') or 'N/A'}
                            """)
                        with col2:
                            if st.button("👁️ Visualizza", key=f"view_doc_{doc['file_name']}", use_container_width=True):
                                st.session_state.edit_paper = doc['file_name']
                                st.switch_page("pages/3_📝_Editor.py")

                        # Show AI keywords if available
                        try:
                            keywords = json.loads(doc.get('keywords', '[]'))
                            if keywords:
                                keyword_tags = " ".join([f'<span class="keyword-tag">{kw}</span>' for kw in keywords[:6]])
                                st.markdown(f"**Keywords AI:** {keyword_tags}", unsafe_allow_html=True)
                        except:
                            pass

                        # Show AI tasks if available
                        try:
                            ai_tasks = json.loads(doc.get('ai_tasks', '{}'))
                            if ai_tasks:
                                st.caption("✅ Attività AI generate disponibili")
                        except:
                            pass

                        st.divider()
                else:
                    st.info("📭 **Nessun documento trovato per questo corso.**")
                    st.markdown("Carica materiali direttamente associati al corso per riempire l'archivio!")

                    col1, col2 = st.columns([1,3])
                    with col1:
                        if st.button("📤 Carica Materiale", type="primary", use_container_width=True):
                            st.switch_page("main.py")  # Go to dashboard for upload
    # Course Grid View - when no specific course selected
    st.header("📚 I Tuoi Corsi")

    if courses:
        # Course grid
        n_cols = 2
        for i in range(0, len(courses), n_cols):
            cols = st.columns(n_cols)
            for j in range(n_cols):
                if i + j < len(courses):
                    course = courses[i + j]
                    with cols[j]:
                        # Course card
                        st.markdown(f"""
                        <div class="course-card">
                            <h3>{course['course_name']}</h3>
                            <p><strong>Codice:</strong> {course['course_code'] or 'N/A'}</p>
                            <p>{course['description'] or 'Nessuna descrizione'}</p>
                            <p><small>Creato: {course['created_at'][:10]}</small></p>
                        </div>
                        """, unsafe_allow_html=True)

                        # Quick actions
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button("👁️ Apri", key=f"open_course_{course['id']}", use_container_width=True):
                                st.session_state.selected_course_id = course['id']
                                st.rerun()
                        with col_b:
                            if st.button("✏️ Modifica", key=f"edit_course_{course['id']}", use_container_width=True):
                                st.info("Modifica corso da implementare")
    else:
        # No courses yet
        st.info("🎓 **Nessun corso trovato!**")
        st.markdown("Crea il tuo primo corso per organizzare i documenti di studio.")

        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("➕ Crea Corso", type="primary", use_container_width=True):
                st.session_state.show_course_form = True
                st.rerun()
        with col2:
            st.markdown("*Oppure carica documenti nella dashboard principale per iniziare automaticamente*")
