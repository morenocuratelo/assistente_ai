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
    get_user_tasks, get_user_courses, get_course_lectures, implement_generated_schedule,
    record_user_activity, get_dashboard_data, check_first_time_user, mark_user_not_new
)
import knowledge_structure

# Import UX components for enhanced experience
from ux_components import show_welcome_modal, show_guided_tour, show_contextual_help
from smart_suggestions import record_user_action

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
    """Main entry point - Intelligent Dashboard with 2-3 column layout."""

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

    # Initialize UX components for this user
    from ux_components import init_ux_session
    init_ux_session(user_id)

    # Record dashboard access for behavior tracking
    record_user_activity(user_id, 'accessed_dashboard', 'dashboard', 'main')

    # Check if first-time user and show onboarding
    is_first_time = check_first_time_user(user_id)
    if is_first_time:
        show_new_user_dashboard(user_id, username)
        return

    # Header principale con navigazione rapida
    st.title("🎓 Dashboard Intelligente")
    st.caption(f"**Benvenuto, {username}!** Centro di comando personalizzato per il tuo apprendimento.")

    # Quick navigation header
    col_nav1, col_nav2, col_nav3, col_nav4 = st.columns(4)
    with col_nav1:
        if st.button("🎯 Wizards", help="Guide interattive", key="header_wizards"):
            record_user_activity(user_id, 'accessed_workflow_wizards', 'navigation', 'header')
            st.switch_page("pages/7_Workflow_Wizards.py")
    with col_nav2:
        if st.button("📊 Feedback", help="Monitoraggio operazioni", key="header_feedback"):
            record_user_activity(user_id, 'accessed_feedback_dashboard', 'navigation', 'header')
            st.switch_page("pages/8_Feedback_Dashboard.py")
    with col_nav3:
        if st.button("🤖 Smart AI", help="Suggerimenti personalizzati", key="header_smart"):
            record_user_activity(user_id, 'accessed_smart_suggestions', 'navigation', 'header')
            st.switch_page("pages/9_Smart_Suggestions.py")
    with col_nav4:
        if st.button("❓ Guida", help="Aiuto e supporto", key="header_help"):
            from ux_components import show_contextual_help
            show_contextual_help("dashboard_overview")

    st.divider()

    # Layout principale a 2 colonne
    col_left, col_right = st.columns([0.65, 0.35])

    # --- COLONNA SINISTRA: Interazione Principale ---
    with col_left:
        # Widget Comando Universale / Chat
        st.markdown("### 💬 Comando Universale")
        st.caption("Fai domande, dai comandi, o inizia una conversazione con i tuoi documenti")

        # Universal command input
        universal_command = st.text_input(
            "🎯 Cosa vuoi fare oggi?",
            placeholder="Es: 'Riassumi i documenti di matematica' o 'Pianifica il mio studio'",
            key="universal_command",
            help="Comando naturale in italiano - l'AI capirà cosa intendi!"
        )

        if universal_command.strip():
            # Process universal command
            process_universal_command(user_id, universal_command.strip())

        st.markdown("---")

        # Azioni Rapide
        st.markdown("### ⚡ Azioni Rapide")

        action_col1, action_col2 = st.columns(2)

        with action_col1:
            if st.button("📤 Carica Documento", use_container_width=True, type="primary"):
                record_user_activity(user_id, 'quick_upload_document', 'action', 'dashboard')
                st.session_state['show_quick_upload'] = True
                st.rerun()

            if st.button("🎯 Workflow Wizard", use_container_width=True):
                record_user_activity(user_id, 'quick_workflow_wizard', 'action', 'dashboard')
                st.switch_page("pages/7_Workflow_Wizards.py")

        with action_col2:
            if st.button("📚 Esplora Archivio", use_container_width=True):
                record_user_activity(user_id, 'quick_explore_archive', 'action', 'dashboard')
                st.switch_page("pages/2_Archivio.py")

            if st.button("🤖 Suggerimenti AI", use_container_width=True):
                record_user_activity(user_id, 'quick_smart_suggestions', 'action', 'dashboard')
                st.switch_page("pages/9_Smart_Suggestions.py")

        # Show quick upload form if triggered
        if st.session_state.get('show_quick_upload'):
            st.markdown("---")
            show_quick_upload_form(user_id)

    # --- COLONNA DESTRA: Informazioni e Accessi Rapidi ---
    with col_right:
        # Documenti Recenti
        st.markdown("### 📄 Documenti Recenti")

        try:
            recent_docs = get_recent_documents(user_id, limit=3)
            if recent_docs:
                for doc in recent_docs:
                    doc_title = doc.get('title', doc['file_name'])
                    last_accessed = doc.get('last_accessed', 'N/A')[:10] if doc.get('last_accessed') else 'N/A'

                    with st.expander(f"📄 {doc_title[:30]}..."):
                        st.caption(f"📅 Ultimo accesso: {last_accessed}")
                        st.caption(f"📂 Categoria: {doc.get('category_name', 'N/A')}")

                        col_view, col_edit = st.columns(2)
                        with col_view:
                            if st.button("👁️ Visualizza", key=f"view_recent_{doc['file_name']}", use_container_width=True):
                                record_user_activity(user_id, 'view_recent_document', 'document', doc['file_name'])
                                st.switch_page("pages/2_Archivio.py")
                        with col_edit:
                            if st.button("✏️ Modifica", key=f"edit_recent_{doc['file_name']}", use_container_width=True):
                                record_user_activity(user_id, 'edit_recent_document', 'document', doc['file_name'])
                                st.session_state['edit_paper'] = doc['file_name']
                                st.switch_page("pages/3_Editor.py")
            else:
                st.info("📭 Nessun documento recente")
                if st.button("📤 Carica Primo Documento", use_container_width=True):
                    st.session_state['show_quick_upload'] = True
                    st.rerun()

        except Exception as e:
            st.error(f"Errore nel caricamento documenti recenti: {e}")

        st.markdown("---")

        # File Recenti (Upload)
        st.markdown("### 📁 File Caricati di Recente")

        try:
            recent_uploads = get_recent_uploads(user_id, limit=3)
            if recent_uploads:
                for upload in recent_uploads:
                    upload_date = upload.get('upload_date', 'N/A')[:10] if upload.get('upload_date') else 'N/A'

                    with st.expander(f"📄 {upload['file_name'][:30]}..."):
                        st.caption(f"📅 Caricato: {upload_date}")
                        st.caption(f"📊 Dimensione: {upload['size'] // 1024} KB")

                        if st.button("🔍 Processa", key=f"process_recent_{upload['file_name']}", use_container_width=True):
                            record_user_activity(user_id, 'reprocess_recent_upload', 'document', upload['file_name'])
                            scan_and_process_documents([upload['file_name']])
            else:
                st.info("📭 Nessun upload recente")

        except Exception as e:
            st.error(f"Errore nel caricamento upload recenti: {e}")

        st.markdown("---")

        # Statistiche Rapide
        st.markdown("### 📊 Statistiche Rapide")

        try:
            papers_df = get_papers_dataframe()
            courses = get_user_courses(user_id)
            tasks = get_user_tasks(user_id)

            col1, col2 = st.columns(2)

            with col1:
                st.metric("📚 Documenti", len(papers_df))
                st.metric("🎓 Corsi Attivi", len(courses))

            with col2:
                completed_tasks = len([t for t in tasks if t['status'] == 'completed'])
                st.metric("✅ Task Completati", f"{completed_tasks}/{len(tasks)}")
                st.metric("🤖 AI Processed", len(papers_df[papers_df['formatted_preview'].notna()]))

        except Exception as e:
            st.error(f"Errore nel caricamento statistiche: {e}")

        # Quick insights
        st.markdown("---")
        st.markdown("### 💡 Insight del Giorno")

        try:
            # Get activity summary for insights
            activity_summary = get_user_activity_summary(user_id, days=1)

            if activity_summary['general_stats'].get('total_actions', 0) > 0:
                st.info(f"🔥 **Attivo oggi!** {activity_summary['general_stats']['total_actions']} azioni registrate.")
            else:
                st.info("💪 **Pronto per iniziare!** La tua dashboard ti aspetta.")

        except Exception as e:
            st.info("🌟 **Benvenuto!** Inizia caricando documenti o creando contenuti.")

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

def show_new_user_dashboard(user_id: str, username: str):
    """Dashboard speciale per nuovi utenti con onboarding guidato."""
    st.title("🎉 Benvenuto in Archivista AI!")
    st.markdown(f"**Ciao {username}!** Iniziamo il tuo viaggio di apprendimento intelligente.")

    # Welcome message with balloons effect
    st.balloons()

    st.info("""
    🎓 **Archivista AI** è il tuo assistente personale per l'apprendimento universitario.

    **In questa dashboard intelligente puoi:**
    - 📤 **Caricare documenti** e farli elaborare dall'AI
    - 💬 **Chattare** con i tuoi documenti per chiarire dubbi
    - 📚 **Esplorare l'archivio** organizzato per categorie
    - 🎯 **Usare workflow guidati** per operazioni complesse
    - 🤖 **Ricevere suggerimenti** personalizzati basati sul tuo utilizzo
    """)

    st.markdown("---")

    # First action guidance
    st.markdown("### 🚀 Il Tuo Primo Passo")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📤 Carica il Tuo Primo Documento")
        st.info("Inizia caricando appunti, dispense o qualsiasi documento di studio.")

        if st.button("📤 Carica Documento", key="first_upload", type="primary", use_container_width=True):
            record_user_activity(user_id, 'first_document_upload_attempt', 'action', 'onboarding')
            st.session_state['show_first_upload'] = True
            st.rerun()

    with col2:
        st.markdown("#### ✨ Crea Contenuto Originale")
        st.info("Oppure crea il tuo primo documento direttamente nell'app.")

        if st.button("✨ Crea Documento", key="first_create", use_container_width=True):
            record_user_activity(user_id, 'first_document_creation_attempt', 'action', 'onboarding')
            st.switch_page("pages/4_Nuovo.py")

    # Show first upload form if triggered
    if st.session_state.get('show_first_upload'):
        st.markdown("---")
        show_first_time_upload_form(user_id)

    # Quick tips for new users
    st.markdown("---")
    st.markdown("### 💡 Suggerimenti per Iniziare Bene")

    tips = [
        "**📚 Inizia con pochi documenti** per vedere come funziona il sistema",
        "**🎯 Usa titoli descrittivi** per aiutare l'AI a categorizzare correttamente",
        "**📂 Organizza per categorie** per trovare facilmente i tuoi documenti",
        "**💬 Fai domande specifiche** quando chatti con i tuoi documenti"
    ]

    for tip in tips:
        st.markdown(f"• {tip}")

    # Complete onboarding button
    st.markdown("---")
    if st.button("✅ Ho Capito, Iniziamo!", key="complete_onboarding", type="primary", use_container_width=True):
        mark_user_not_new(user_id)
        record_user_activity(user_id, 'completed_new_user_onboarding', 'milestone', 'onboarding')
        st.success("🎉 Onboarding completato! Benvenuto nella community di Archivista AI!")
        st.rerun()

def show_first_time_upload_form(user_id: str):
    """Form di upload semplificato per nuovi utenti."""
    with st.form("first_time_upload"):
        st.markdown("**🎯 Carica il tuo primo documento**")

        first_file = st.file_uploader(
            "Seleziona un documento (PDF, Word, TXT, etc.)",
            type=['pdf', 'docx', 'txt', 'rtf', 'html', 'htm'],
            help="Inizia con un documento di studio, appunti o dispense"
        )

        if first_file:
            st.success(f"📎 File selezionato: {first_file.name}")

            # Simple category selection for new users
            simple_category = st.selectbox(
                "📂 Categoria (opzionale)",
                ["Nessuna categoria", "P1_IL_PALCOSCENICO_COSMICO_E_BIOLOGICO/C01", "P2_L_ASCESA_DEL_GENERE_HOMO/C04", "UNCATEGORIZED/C00"],
                help="Scegli una categoria per organizzare il documento"
            )

        submit_first = st.form_submit_button("🚀 Carica e Inizia l'Esplorazione!", type="primary", use_container_width=True)

        if submit_first and first_file:
            # Save file
            save_path = os.path.join(DOCS_TO_PROCESS_DIR, first_file.name)
            with open(save_path, "wb") as f:
                f.write(first_file.getbuffer())

            # Mark user as not new
            mark_user_not_new(user_id)

            # Record first upload
            record_user_activity(user_id, 'first_document_uploaded', 'document', first_file.name, {
                'category': simple_category,
                'size': len(first_file.getbuffer()),
                'is_first_upload': True
            })

            # Start processing
            scan_and_process_documents([first_file.name])

            st.success("🎉 Primo documento caricato con successo!")
            st.info("🔄 L'AI sta elaborando il documento. Tra poco apparirà nell'archivio!")

            # Show next steps
            st.markdown("**🎯 Prossimi passi consigliati:**")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💬 Prova la Chat", key="first_chat"):
                    st.switch_page("pages/1_Chat.py")
            with col2:
                if st.button("📚 Esplora Archivio", key="first_archive"):
                    st.switch_page("pages/2_Archivio.py")

            st.rerun()

def process_universal_command(user_id: str, command: str):
    """Processa il comando universale dell'utente."""
    try:
        # Record the command attempt
        record_user_activity(user_id, 'universal_command_used', 'command', 'dashboard', {
            'command_text': command[:100]  # Limit for privacy
        })

        # Simple command parsing and routing
        command_lower = command.lower()

        # Document-related commands
        if any(word in command_lower for word in ['carica', 'upload', 'documento', 'file']):
            st.session_state['show_quick_upload'] = True
            st.success("📤 Ti mostro il form di caricamento!")
            st.rerun()

        # Chat/search commands
        elif any(word in command_lower for word in ['cerca', 'trova', 'chiedi', 'dimmi', 'spiega']):
            # Pre-fill chat with the command
            st.session_state['universal_chat_command'] = command
            st.switch_page("pages/1_Chat.py")

        # Archive exploration
        elif any(word in command_lower for word in ['archivio', 'documenti', 'esplora']):
            st.switch_page("pages/2_Archivio.py")

        # Creation commands
        elif any(word in command_lower for word in ['crea', 'nuovo', 'scrivi']):
            st.switch_page("pages/4_Nuovo.py")

        # Help commands
        elif any(word in command_lower for word in ['aiuto', 'guida', 'come']):
            from ux_components import show_contextual_help
            show_contextual_help("general_help")

        # Default: go to chat
        else:
            st.session_state['universal_chat_command'] = command
            st.switch_page("pages/1_Chat.py")

    except Exception as e:
        st.error(f"Errore nel processamento comando: {e}")
        # Fallback to chat
        st.session_state['universal_chat_command'] = command
        st.switch_page("pages/1_Chat.py")

def show_quick_upload_form(user_id: str):
    """Form di upload rapido per la dashboard."""
    with st.form("quick_upload_form"):
        st.markdown("**📤 Upload Rapido**")

        files = st.file_uploader(
            "Seleziona file",
            accept_multiple_files=True,
            type=['pdf', 'docx', 'txt', 'rtf', 'html', 'htm']
        )

        if files:
            st.success(f"📎 {len(files)} file selezionati")

        submit_upload = st.form_submit_button("🚀 Carica", type="primary", use_container_width=True)

        if submit_upload and files:
            saved_files = []
            for file in files:
                save_path = os.path.join(DOCS_TO_PROCESS_DIR, file.name)
                with open(save_path, "wb") as f:
                    f.write(file.getbuffer())
                saved_files.append(file.name)

            if saved_files:
                # Record upload activity
                for file_name in saved_files:
                    record_user_activity(user_id, 'quick_upload', 'document', file_name)

                # Start processing
                scan_and_process_documents(saved_files)

                st.success(f"✅ {len(saved_files)} documenti caricati e inviati per processamento!")
                st.session_state['show_quick_upload'] = False
                st.rerun()

if __name__ == "__main__":
    main()
