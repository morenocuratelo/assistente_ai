import streamlit as st
import os
import time
import json
import pandas as pd
from datetime import datetime

# Import delle funzionalità condivise
from config import initialize_services, get_chat_llm
from file_utils import setup_database, get_papers_dataframe, update_paper_metadata
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

        # Chat button (primary - this is our main page)
        if st.button(
            "💬 Chat",
            key="nav_chat",
            use_container_width=True,
            type="primary",
            help="Chatta con i tuoi documenti (Pagina principale)"
        ):
            st.switch_page("pages/1_💬_Chat.py")

        # Archive button
        if st.button(
            "🗂️ Archivio",
            key="nav_archive",
            use_container_width=True,
            type="secondary",
            help="Esplora e gestisci i documenti"
        ):
            st.switch_page("pages/2_🗂️_Archivio.py")

        # Editor button
        if st.button(
            "📝 Editor",
            key="nav_editor",
            use_container_width=True,
            type="secondary",
            help="Modifica anteprime e documenti"
        ):
            st.switch_page("pages/3_📝_Editor.py")

        # New Document button
        if st.button(
            "✨ Nuovo",
            key="nav_new",
            use_container_width=True,
            type="secondary",
            help="Crea nuovo documento"
        ):
            st.switch_page("pages/4_✨_Nuovo.py")

        st.divider()

        # Document Upload Section
        st.markdown("### ➕ Aggiungi Documenti")
        uploaded_files = st.file_uploader(
            "Trascina i file qui",
            accept_multiple_files=True,
            type=['pdf', 'docx', 'txt', 'rtf', 'html', 'htm'],
            label_visibility="collapsed"
        )

        if uploaded_files:
            saved_files = []
            for uploaded_file in uploaded_files:
                save_path = os.path.join(DOCS_TO_PROCESS_DIR, uploaded_file.name)
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                saved_files.append(uploaded_file.name)
            if saved_files:
                add_log_message(f"Caricati {len(saved_files)} file.")
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

def main():
    """Main entry point with persistent sidebar navigation."""

    # Esecuzione allo startup
    auto_scan_at_startup()

    # Render sidebar persistente
    render_navigation_sidebar()

    # Contenuto principale - delegato alle pagine
    st.markdown("# 🤖 Archivista AI")
    st.markdown("### 🏠 Homepage - Naviga tramite la sidebar")

    # Info sulla nuova architettura
    st.info("🎉 **Architettura Completa Multi-Pagina Attiva!**")
    st.markdown("""
    **Naviga utilizzando la sidebar:**
    - 💬 **Chat**: La tua interfaccia principale per chattare con i documenti
    - 🗂️ **Archivio**: Esplora e gestisci la tua biblioteca di documenti
    - 📝 **Editor**: Modifica anteprime generate dall'AI
    - ✨ **Nuovo**: Crea nuova conoscenza direttamente nell'applicazione

    **Ogni pagina è ottimizzata per il suo compito specifico!**
    """)

    # Metriche rapide
    papers_df = get_papers_dataframe()
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("📚 Documenti", len(papers_df))
    with col2:
        categories = papers_df['category_id'].nunique() if not papers_df.empty else 0
        st.metric("📂 Categorie", categories)
    with col3:
        st.metric("✅ Indicizzati", len(papers_df[papers_df['formatted_preview'].notna()]) if not papers_df.empty else 0)

if __name__ == "__main__":
    main()
