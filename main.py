import streamlit as st
import os
import time
import json
import pandas as pd
from datetime import datetime

# Import delle funzionalità condivise
from config import initialize_services, get_chat_llm
from file_utils import (
    setup_database, get_papers_dataframe, update_paper_metadata,
    get_today_planned_sessions, generate_study_schedule, get_study_insights,
    get_user_tasks, get_user_courses, get_course_lectures, implement_generated_schedule
)
import knowledge_structure

# --- CONFIGURAZIONE ---
DB_STORAGE_DIR = "db_memoria"
DOCS_TO_PROCESS_DIR = "documenti_da_processare"
ARCHIVISTA_STATUS_FILE = os.path.join(DB_STORAGE_DIR, "archivista_status.json")

# --- INIZIALIZZAZIONE ---
st.set_page_config(
    page_title="Archivista AI v2.3",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ensure required directories exist
os.makedirs(DB_STORAGE_DIR, exist_ok=True)
os.makedirs(DOCS_TO_PROCESS_DIR, exist_ok=True)

# Blocco di inizializzazione eseguito una sola volta per sessione
if 'initialized' not in st.session_state:
    # Inizializza i servizi LLM e di embedding
    initialize_services()
    # Configura il database dei metadati
    setup_database()

    st.session_state.initialized = True
    st.session_state.log_messages = []
    st.session_state.auto_scan_completed = False

    # Navigation state for new architecture
    st.session_state.current_view = 'chat'

# --- FUNZIONI DI UTILITÀ (condivise tra tutte le pagine) ---

def get_archivista_status():
    """Legge lo stato corrente del processo di indicizzazione da un file JSON."""
    try:
        if not os.path.exists(DB_STORAGE_DIR):
            return {"status": "Inattivo", "file": None, "timestamp": datetime.now().isoformat()}

        with open(ARCHIVISTA_STATUS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"status": "Inattivo", "file": None, "timestamp": datetime.now().isoformat()}

def add_log_message(message):
    """Aggiunge un messaggio al log temporaneo nell'interfaccia."""
    current_time = datetime.now().strftime("%H:%M:%S")
    st.session_state.log_messages.insert(0, f"[{current_time}] {message}")
    if len(st.session_state.log_messages) > 5:
        st.session_state.log_messages.pop()

def scan_and_process_documents(files_to_process=None):
    """
    Scansiona la cartella di input o processa una lista specifica di file
    inviandoli al worker Celery.
    """
    try:
        from archivista_processing import process_document_task

        if files_to_process is None:
            supported_extensions = ['.pdf', '.docx', '.rtf', '.html', '.htm', '.txt']
            files_to_process = [f for f in os.listdir(DOCS_TO_PROCESS_DIR) if any(f.lower().endswith(ext) for ext in supported_extensions)]
            if not files_to_process:
                add_log_message("Nessun nuovo documento trovato.")
                return

        add_log_message(f"Trovati {len(files_to_process)} documenti.")

        sent_tasks = 0
        for file_name in files_to_process:
            file_path = os.path.join(DOCS_TO_PROCESS_DIR, file_name)
            if os.path.exists(file_path):
                try:
                    process_document_task.delay(file_path)
                    add_log_message(f"Inviato per processamento: {file_name}")
                    sent_tasks += 1
                except Exception as e:
                    add_log_message(f"Broker non disponibile. Errore: {e}")
                    st.error("Errore di connessione con il sistema di code (Redis/Celery). L'elaborazione in background è disabilitata.")
                    return

        if sent_tasks > 0:
            add_log_message(f"{sent_tasks} documenti inviati al worker.")
            st.toast("✅ Elaborazione avviata in background!")

    except Exception as e:
        add_log_message(f"Errore scansione: {e}")
        st.error(f"Errore critico durante la scansione: {e}")

def auto_scan_at_startup():
    """Esegue la scansione automatica all'avvio se non è già stata fatta."""
    if not st.session_state.auto_scan_completed:
        add_log_message("Scansione automatica all'avvio...")
        scan_and_process_documents()
        st.session_state.auto_scan_completed = True

# --- SIDEBAR DI NAVIGAZIONE PERSISTENTE ---

def render_navigation_sidebar():
    """Render the persistent sidebar navigation shared across all pages."""
    with st.sidebar:
        st.title("🤖 Archivista AI")

        # Main Navigation - Chat First approach
        st.markdown("### 🧭 Navigazione")

        # Authentication-aware navigation
        if 'user_id' in st.session_state and st.session_state['user_id']:
            # User is logged in - show chat button
            if st.button(
                "💬 Chat",
                key="nav_chat",
                use_container_width=True,
                type="primary",
                help="Chatta con i tuoi documenti (Pagina principale)"
            ):
                st.switch_page("pages/1_Chat.py")

            # Logout button
            if st.button(
                f"🚪 Logout ({st.session_state.get('username', 'User')})",
                key="nav_logout",
                use_container_width=True,
                type="secondary",
                help="Disconnetti dal sistema"
            ):
                # Clear session state
                for key in ['user_id', 'username', 'current_session_id']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
        else:
            # User not logged in - show login button
            if st.button(
                "🔐 Login",
                key="nav_login",
                use_container_width=True,
                type="primary",
                help="Accedi al sistema per iniziare a chattare"
            ):
                st.switch_page("pages/login.py")

        # Archive button
        if st.button(
            "🗂️ Archivio",
            key="nav_archive",
            use_container_width=True,
            type="secondary",
            help="Esplora e gestisci i documenti"
        ):
            st.switch_page("pages/2_Archivio.py")

        # Editor button
        if st.button(
            "📝 Editor",
            key="nav_editor",
            use_container_width=True,
            type="secondary",
            help="Modifica anteprime e documenti"
        ):
            st.switch_page("pages/3_Editor.py")

        # New Document button
        if st.button(
            "✨ Nuovo",
            key="nav_new",
            use_container_width=True,
            type="secondary",
            help="Crea nuovo documento"
        ):
            st.switch_page("pages/4_Nuovo.py")

        # Carriera button (Academic section)
        if st.button(
            "🎓 Carriera",
            key="nav_carriera",
            use_container_width=True,
            type="secondary",
            help="Gestisci carriera accademica"
        ):
            st.switch_page("pages/5_Carriera.py")

        # Grafo del Conoscenza button (Phase 3)
        if st.button(
            "🧠 Grafo",
            key="nav_grafo",
            use_container_width=True,
            type="secondary",
            help="Esplora il grafo della conoscenza"
        ):
            st.switch_page("pages/6_Grafo.py")

        st.divider()

        # Document Upload Section
        st.markdown("### ➕ Aggiungi Documenti")
        uploaded_files = st.file_uploader(
            "Trascina i file qui",
            accept_multiple_files=True,
            type=['pdf', 'docx', 'txt', 'rtf', 'html', 'htm'],
            label_visibility="collapsed"
        )

        # Academic association (only for logged-in users)
        academic_association = False
        selected_course_id = None
        selected_lecture_id = None
        material_type = "other"

        if 'user_id' in st.session_state and st.session_state['user_id']:
            academic_association = st.checkbox("🎓 Associa a corso accademico", help="Collega i documenti caricati a un corso o lezione")

            if academic_association:
                from file_utils import get_user_courses, get_course_lectures

                user_id = st.session_state['user_id']
                courses = get_user_courses(user_id)
                course_options = ["Seleziona..."] + [f"{c['course_name']} ({c['course_code'] or 'No Code'})" for c in courses]

                selected_course_option = st.selectbox("Corso", course_options, help="Seleziona il corso associato")
                if selected_course_option != "Seleziona...":
                    course_name = selected_course_option.split(' (')[0]
                    selected_course = next((c for c in courses if c['course_name'] == course_name), None)
                    if selected_course:
                        selected_course_id = selected_course['id']
                        lectures = get_course_lectures(selected_course_id)
                        lecture_options = ["Nessuna lezione specifica"] + [f"{l['lecture_title']} ({l['lecture_date'] or 'No Date'})" for l in lectures]

                        selected_lecture_option = st.selectbox("Lezione (opzionale)", lecture_options)
                        if selected_lecture_option != "Nessuna lezione specifica":
                            lecture_title = selected_lecture_option.split(' (')[0]
                            selected_lecture = next((l for l in lectures if l['lecture_title'] == lecture_title), None)
                            if selected_lecture:
                                selected_lecture_id = selected_lecture['id']

                        material_type = st.selectbox("Tipo Materiale", ["lecture_notes", "handout", "assignment", "reading", "other"],
                                                   format_func=lambda x: x.replace('_', ' ').title(), help="Tipo di materiale didattico")

        if uploaded_files:
            saved_files = []
            for uploaded_file in uploaded_files:
                save_path = os.path.join(DOCS_TO_PROCESS_DIR, uploaded_file.name)
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                saved_files.append(uploaded_file.name)

            if saved_files:
                add_log_message(f"Caricati {len(saved_files)} file.")

                # Create material associations if academic data provided
                if academic_association and selected_course_id:
                    from file_utils import create_material
                    user_id = st.session_state['user_id']

                    for file_name in saved_files:
                        try:
                            material_id = create_material(
                                lecture_id=selected_lecture_id,
                                course_id=selected_course_id,
                                file_name=file_name,
                                material_type=material_type
                            )
                            add_log_message(f"Associato {file_name} al corso accademico.")
                        except Exception as e:
                            add_log_message(f"Errore associazione {file_name}: {e}")

                scan_and_process_documents(files_to_process=saved_files)
                st.rerun()

        if st.button("🔍 Controlla Nuovi File", use_container_width=True):
            scan_and_process_documents()

        st.divider()

        # Status Section (Simplified)
        st.markdown("### 📊 Stato Sistema")
        status = get_archivista_status()
        status_text = status.get('status', 'Inattivo')

        if "Errore" in status_text:
            st.error(f"❌ {status_text.replace('Errore: ', '')}")
        elif status_text not in ["Inattivo", "Completato"]:
            st.info(f"⏳ {status_text}")
        else:
            st.success(f"✅ {status_text}")

        # Small log expander
        if st.session_state.log_messages:
            with st.expander(f"📋 Log ({len(st.session_state.log_messages)} messaggi)"):
                for msg in st.session_state.log_messages[-3:]:  # Show only last 3
                    st.text(msg)

# --- MAIN ENTRY POINT ---

def get_today_summary(user_id):
    """Generate AI-powered "Oggi nel campus" summary"""
    try:
        from config import get_chat_llm
        # Get today's tasks
        tasks = get_user_tasks(user_id)
        today_tasks = [t for t in tasks if t.get('due_date') and t['due_date'][:10] == datetime.now().strftime('%Y-%m-%d')]

        # Get recent lectures
        courses = get_user_courses(user_id)
        recent_lectures = []
        for course in courses:
            lectures = get_course_lectures(course['id'])
            recent = [l for l in lectures if l.get('lecture_date') and
                     (datetime.now().date() - datetime.fromisoformat(l['lecture_date']).date()).days <= 7]
            recent_lectures.extend(recent)

        # Generate smart summary using AI
        chat_llm = get_chat_llm()
        context = f"""
        Utente ha: {len(today_tasks)} task scadenti oggi, {len(recent_lectures)} lezioni negli ultimi 7 giorni, {len(courses)} corsi attivi.
        Task di oggi: {[t['task_title'] for t in today_tasks[:3]]}
        """

        prompt = f"""
        Genera un breve riassunto motivazionale per lo studente universitario, basato sui seguenti dati:
        {context}

        Scrivi in Italiano, massimo 2-3 frasi incoraggianti e pratiche su cosa fare oggi nel suo percorso di studio.
        """

        summary = str(chat_llm.complete(prompt)).strip()
        return summary if summary else "Oggi è un ottimo giorno per studiare! Continua il tuo percorso di apprendimento."

    except Exception as e:
        print(f"Errore generazione summary: {e}")
        return "Benvenuti nell'applicazione di apprendimento intelligente!"

def get_top_urgent_tasks(user_id, limit=5):
    """Get 3-5 most urgent tasks"""
    try:
        tasks = get_user_tasks(user_id)
        # Simple priority sorting (high first, then medium, then low)
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        urgent_tasks = sorted(
            [t for t in tasks if t['status'] in ['pending', 'in_progress']],
            key=lambda x: (
                priority_order.get(x.get('priority', 'medium'), 2),
                x.get('due_date') or '9999-12-31'
            ),
            reverse=True
        )
        return urgent_tasks[:limit]
    except Exception as e:
        print(f"Errore recupero task urgenti: {e}")
        return []

def main():
    """Main entry point - now serves as the intelligent dashboard."""

    # Esecuzione allo startup
    auto_scan_at_startup()

    # Render sidebar persistente
    render_navigation_sidebar()

    # Se utente non loggato, mostra pagina di benvenuto
    if 'user_id' not in st.session_state or not st.session_state['user_id']:
        show_welcome_dashboard()
        return

    # Dashboard per utente autenticato
    user_id = st.session_state['user_id']
    username = st.session_state.get('username', 'Utente')

    # Header principale
    st.title("🎓 Il Tuo Centro di Comando Accademico")
    st.markdown(f"**Benvenuto, {username}!** Questa è la tua dashboard intelligente per il percorso di studio.")

    st.divider()

    # "Oggi nel campus" section
    st.subheader("🏫 Oggi nel campus")
    with st.container():
        today_summary = get_today_summary(user_id)
        st.info(today_summary)

    # To-Do List principali
    st.subheader("🎯 Attività Principali")
    urgent_tasks = get_top_urgent_tasks(user_id)

    if urgent_tasks:
        cols = st.columns(min(len(urgent_tasks), 3))
        for i, task in enumerate(urgent_tasks):
            with cols[i % len(cols)]:
                priority_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
                status_icon = {'pending': '⏳', 'in_progress': '🔄'}

                st.markdown(f"""
                <div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 12px; margin-bottom: 8px; background-color: #fafafa;">
                    <h5>{status_icon.get(task['status'], '⏳')} {task['task_title'][:30]}{'...' if len(task['task_title']) > 30 else ''}</h5>
                    <p style="font-size: 0.9em; color: #666;">{priority_icon.get(task.get('priority', 'medium'), '🟡')} Priorità {task.get('priority', 'medium').title()}</p>
                    {f'<p style="font-size: 0.8em;">📅 Scadenza: {task.get("due_date", "N/A")[:10]}</p>' if task.get('due_date') else ''}
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("🎉 Tutte le attività completate! Continua così!")

    # Studio Pianificato per Oggi (Assistente Calendarizzatore IA)
    st.subheader("📅 Studio Pianificato per Oggi")
    today_sessions = get_today_planned_sessions(user_id)

    if today_sessions:
        st.success(f"🎯 **{len(today_sessions)} sessioni pianificate** per oggi dall'IA!")

        for i, session in enumerate(today_sessions):
            col_a, col_b = st.columns([3, 1])
            with col_a:
                duration = session.get('planned_duration', 60)
                priority = session.get('priority_score', 0.5)
                priority_icon = '🔴' if priority > 0.7 else '🟡' if priority > 0.4 else '🟢'

                topics = session.get('topics_covered', [])
                topic_text = topics[0] if topics else "Studio generale"

                st.markdown(f"""
                <div style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 12px; margin-bottom: 8px; background-color: #f8f9fa;">
                    <h5>{priority_icon} {topic_text[:40]}{'...' if len(topic_text) > 40 else ''}</h5>
                    <p style="font-size: 0.9em; color: #666;">⏱️ {duration} minuti | Priorità: {priority:.1f}/1.0</p>
                    {f'<p style="font-size: 0.8em; font-style: italic;">💡 {session.get("ai_recommendation", "")[:100]}</p>' if session.get("ai_recommendation") else ''}
                </div>
                """, unsafe_allow_html=True)

                # Mostra task collegati se esistono
                if session.get('course_name'):
                    st.caption(f"📚 Corso: {session['course_name']}")

            with col_b:
                if st.button(f"▶️ Inizia", key=f"start_session_{session['id']}", use_container_width=True):
                    st.info("Avvio sessione di studio...")
                    # Qui si potrebbe avviare un timer o collegare a funzionalità di tracking
                if st.button("✏️", key=f"edit_session_{session['id']}", help="Modifica"):
                    st.info("Modifica sessione da implementare")

        # Insight sul pattern di studio
        st.divider()
        insights = get_study_insights(user_id)
        if 'insight' in insights:
            st.info(f"📊 **Il tuo profilo di studio:** {insights['insight']}")

    else:
        # Genera automaticamente un piano se non esistono sessioni pianificate
        if st.button("🤖 Genera Piano di Studio IA", key="generate_schedule", help="L'IA analizzerà i tuoi impegni e creerà un calendario personalizzato"):
            with st.spinner("🔍 Analizzo i tuoi dati e genero un piano di studio intelligente..."):
                try:
                    schedule = generate_study_schedule(user_id, days_ahead=7)
                    sessions_created = implement_generated_schedule(user_id, schedule)

                    if sessions_created > 0:
                        st.success(f"✅ Creato piano di studio con {sessions_created} sessioni! Ricarica per vedere i suggerimenti.")
                        st.rerun()
                    else:
                        st.info("📝 Nessuna sessione urgente da pianificare ora. Aggiungi più contenuti per suggerimenti migliori!")

                except Exception as e:
                    st.error(f"Errore generazione piano: {str(e)}")
                    st.info("💡 Assicurati di avere corsi e lezioni caricate per suggerimenti personalizzati.")

    # Accesso Rapido
    st.subheader("⚡ Accesso Rapido")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📹 Registra Lezione", key="quick_record_lecture", use_container_width=True):
            st.switch_page("pages/5_🎓_Carriera.py")

    with col2:
        if st.button("📚 Corsi & Lezioni", key="quick_courses", use_container_width=True):
            st.switch_page("pages/5_🎓_Carriera.py")

    with col3:
        if st.button("📤 Carica Documento", key="quick_upload", use_container_width=True):
            # Enable upload section
            st.session_state['show_upload'] = True
            st.rerun()

    with col4:
        if st.button("💬 Chat Rapida", key="quick_chat", use_container_width=True):
            st.switch_page("pages/1_💬_Chat.py")

    # Upload section (usually hidden, shown when quick upload clicked)
    if st.session_state.get('show_upload'):
        st.divider()
        st.subheader("📤 Carica Nuovo Documento")
        # We'll use the existing upload logic from sidebar, but show it prominently here
        show_academic_upload_form(user_id)

    # Metriche rapide del sistema
    st.divider()
    st.subheader("📊 Il Tuo Apprendimento")

    papers_df = get_papers_dataframe()
    courses = get_user_courses(user_id)
    tasks = get_user_tasks(user_id)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📚 Documenti", len(papers_df))
    with col2:
        st.metric("🎓 Corsi", len(courses))
    with col3:
        completed = len([t for t in tasks if t['status'] == 'completed'])
        total_tasks = len(tasks)
        st.metric("✅ Task Completati", f"{completed}/{total_tasks}")
    with col4:
        # Estimated study hours (basic calculation)
        study_hours = sum([t.get('duration_minutes', 0) for t in tasks]) / 60
        st.metric("🕒 Ore Studio", f"{study_hours:.1f}")

def show_welcome_dashboard():
    """Dashboard di benvenuto per utenti non autenticati"""
    st.markdown("# 🤖 Archivista AI - Il Tuo Assistente di Studio Intelligente")
    st.markdown("### 💡 Trasforma il tuo apprendimento con l'AI")

    st.info("🎓 **Per studenti universitari che vogliono:**\n\n"
            "- Organizzare appunti e documenti per materia\n"
            "- Ricevere suggerimenti di studio personalizzati\n"
            "- Gestire compiti e scadenze automaticamente\n"
            "- Chattare con i propri documenti per chiarire dubbi\n"
            "- Esplorare connessioni tra argomenti diversi")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🌟 Funzionalità Principali\n"
                   "- **📚 Archiviazione Intelligente**: I documenti vengono analizzati dall'AI e organizzati automaticamente\n"
                   "- **🔍 Chat Contestuale**: Chiedi alla tua biblioteca personale e ricevi risposte precise\n"
                   "- **🎯 Task Manager IA**: L'AI genera automaticamente liste di attività da documenti\n"
                   "- **🧠 Grafo della Conoscenza**: Vedi come si collegano i concetti tra i tuoi corsi")

    with col2:
        st.markdown("### 🚀 Nuovo: Ciclo dello Studio Intelligente\n"
                   "- **Dashboard Proattiva**: Ogni giorno l'IA ti mostra cosa studiare\n"
                   "- **Carica → Organizza → Studia**: Flusso semplificato per apprendere\n"
                   "- **Tutorials**: Guida alle migliori pratiche di studio\n"
                   "- **Analytics**: Monitora i tuoi progressi di apprendimento")

        if st.button("🔐 Inizia Ora → Login", type="primary", use_container_width=True):
            st.switch_page("pages/login.py")

    # Statistiche dell'applicazione
    st.divider()
    papers_df = get_papers_dataframe()

    if not papers_df.empty:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("📚 Documenti Indicizzati", len(papers_df))
        with col2:
            categories = papers_df['category_id'].nunique()
            st.metric("📂 Categorie", categories)
        with col3:
            processed = len(papers_df[papers_df['formatted_preview'].notna()])
            st.metric("🤖 Elaborati dall'AI", processed)

def show_academic_upload_form(user_id):
    """Form di upload accademico semplificato e intelligente"""
    with st.form("academic_upload_form"):
        st.markdown("**Carica documenti accademici con associazione intelligente**")

        # Permette selezione multipla di file
        uploaded_files = st.file_uploader(
            "Seleziona file (PDF, DOCX, TXT, etc.)",
            accept_multiple_files=True,
            type=['pdf', 'docx', 'txt', 'rtf', 'html', 'htm', 'pptx', 'xlsx']
        )

        if uploaded_files:
            st.success(f"📎 {len(uploaded_files)} file selezionati")

            # Selettori accademici (responsero sempre quando ci sono file)
            # Get user courses for the selectors
            from file_utils import get_user_courses, get_course_lectures

            courses = get_user_courses(user_id)
            course_options = ["Seleziona corso..."] + [f"{c['course_name']} ({c['course_code'] or 'No Code'})" for c in courses]

            selected_course_option = st.selectbox(
                "📚 A quale corso appartiene?",
                course_options,
                help="Associa questi documenti a un corso specifico per organizzare meglio il tuo studio"
            )

            selected_course_id = None
            selected_lecture_id = None

            if selected_course_option != "Seleziona corso...":
                course_name = selected_course_option.split(' (')[0]
                selected_course = next((c for c in courses if c['course_name'] == course_name), None)
                if selected_course:
                    selected_course_id = selected_course['id']

                    lectures = get_course_lectures(selected_course_id)
                    lecture_options = ["Nessuna lezione specifica"] + [f"{l['lecture_title']} ({l['lecture_date'] or 'No Date'})" for l in lectures]

                    selected_lecture_option = st.selectbox(
                        "📝 Seleziona lezione (opzionale)",
                        lecture_options,
                        help="Se questi sono appunti o materiali di una lezione specifica"
                    )

                    if selected_lecture_option != "Nessuna lezione specifica":
                        lecture_title = selected_lecture_option.split(' (')[0]
                        selected_lecture = next((l for l in lectures if l['lecture_title'] == lecture_title), None)
                        if selected_lecture:
                            selected_lecture_id = selected_lecture['id']

            material_type = st.selectbox(
                "📄 Tipo di materiale",
                ["lecture_notes", "handout", "assignment", "reading", "other"],
                format_func=lambda x: {
                    "lecture_notes": "📝 Appunti di lezione",
                    "handout": "📋 Dispensa",
                    "assignment": "📝 Compito/Esame",
                    "reading": "📖 Lettura consigliata",
                    "other": "🔄 Altro"
                }.get(x, x.title().replace('_', ' '))
            )

        submit_button = st.form_submit_button("🚀 Carica e Elabora con AI", type="primary", use_container_width=True)

        if submit_button and uploaded_files:
            # Salva i file e avvía processamento
            saved_files = []
            for uploaded_file in uploaded_files:
                save_path = os.path.join(DOCS_TO_PROCESS_DIR, uploaded_file.name)
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                saved_files.append(uploaded_file.name)

            if saved_files:
                # Associa i materiali se selezionato corso/lezioni
                if selected_course_id:
                    from file_utils import create_material
                    for file_name in saved_files:
                        try:
                            create_material(
                                lecture_id=selected_lecture_id,
                                course_id=selected_course_id,
                                file_name=file_name,
                                material_type=material_type
                            )
                        except Exception as e:
                            st.error(f"Errore associazione {file_name}: {e}")

                # Avvía processamento
                scan_and_process_documents(files_to_process=saved_files)

                st.success(f"✅ Caricati {len(saved_files)} documenti! Elaborazione AI avviata in background.")
                st.session_state['show_upload'] = False
                st.rerun()
        elif submit_button:
            st.error("Seleziona almeno un file da caricare")

if __name__ == "__main__":
    main()
