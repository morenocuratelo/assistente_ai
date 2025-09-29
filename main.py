import streamlit as st
import os
import time
import json
from datetime import datetime
from llama_index.core import Settings, StorageContext, load_index_from_storage
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter

from config import initialize_services, get_chat_llm
from file_utils import setup_database, get_papers_dataframe
import knowledge_structure

# --- CONFIGURAZIONE ---
DB_STORAGE_DIR = "db_memoria"
DOCS_TO_PROCESS_DIR = "documenti_da_processare"
ARCHIVISTA_STATUS_FILE = os.path.join(DB_STORAGE_DIR, "archivista_status.json")

# --- INIZIALIZZAZIONE ---
st.set_page_config(page_title="Archivista AI v2.3", layout="wide")

# Blocco di inizializzazione eseguito una sola volta per sessione
if 'initialized' not in st.session_state:
    # Inizializza i servizi LLM e di embedding
    initialize_services()
    # Configura il database dei metadati
    setup_database()
    
    st.session_state.initialized = True
    st.session_state.log_messages = []
    st.session_state.auto_scan_completed = False
    st.session_state.messages = [{"role": "assistant", "content": "Ciao! Sono Archivista AI. Puoi trascinare i tuoi documenti nella barra laterale per iniziare."}]
    st.session_state.selected_paper = None

def get_archivista_status():
    """Legge lo stato corrente del processo di indicizzazione da un file JSON."""
    try:
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

# --- ESECUZIONE ALLO STARTUP ---
auto_scan_at_startup()

# --- UI: SIDEBAR ---
with st.sidebar:
    st.title("Archivista AI")
    
    st.subheader("Aggiungi Documenti")
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

    if st.button("🔍 Controlla Nuovi File Manualmente", use_container_width=True):
        scan_and_process_documents()

    if st.button("🧹 Pulisci Database", use_container_width=True, help="Rimuove i riferimenti a file inesistenti"):
        from file_utils import cleanup_missing_files
        removed_count = cleanup_missing_files()
        if removed_count > 0:
            st.success(f"✅ Pulizia completata! Rimossi {removed_count} riferimenti a file inesistenti.")
            st.rerun()
        else:
            st.info("✅ Database già pulito. Nessun file inesistente trovato.")

    st.divider()

    st.subheader("Stato Elaborazione")
    status_placeholder = st.empty()
    log_placeholder = st.empty()

    with status_placeholder.container():
        status = get_archivista_status()
        status_text = status.get('status', 'Inattivo')
        
        is_processing = status_text not in ["Inattivo", "Completato"] and "Errore" not in status_text
        is_error = "Errore" in status_text

        if is_error:
            st.error(f"**❌ Errore:** {status_text.replace('Errore: ', '')}\n\n**File:** `{status.get('file', 'N/A')}`")
        elif is_processing:
            st.info(f"**⏳ Stato:** {status_text}\n\n**File:** `{status.get('file', 'N/A')}`")
        else:
            st.success(f"**✅ Stato:** {status_text}")

    with log_placeholder.container():
        if st.session_state.log_messages:
            st.markdown("---")
            for msg in st.session_state.log_messages:
                st.text(msg)

    st.divider()
    
    st.title("Filtri Chat")
    category_choices = knowledge_structure.get_category_choices()
    selected_category_id = st.selectbox(
        "Filtra per Categoria:",
        options=[opt[0] for opt in category_choices],
        format_func=lambda x: dict(category_choices).get(x, "Tutte")
    )

# --- UI: MAIN CONTENT ---
st.title("📚 Archivio della Conoscenza")
col_archive, col_chat = st.columns([0.45, 0.55])

with col_archive:
    st.header("🗂️ Documenti Categorizzati")
    papers_df = get_papers_dataframe()
    if not papers_df.empty:
        # Ordina le categorie, mettendo 'UNCATEGORIZED' per ultima se esiste
        sorted_categories = sorted(papers_df.groupby(['category_id', 'category_name']), key=lambda x: (x[0][0].startswith('UNCATEGORIZED'), x[0][1]))
        for category, group in sorted_categories:
            category_id, category_name = category
            with st.expander(f"**{category_name}** ({len(group)} doc/s)"):
                for _, row in group.iterrows():
                    if st.button(f"📄 {row.get('title', row['file_name'])}", key=row['file_name'], use_container_width=True):
                         st.session_state.selected_paper = row['file_name']
                         st.rerun()
    else:
        st.info(f"L'archivio è vuoto. Aggiungi file tramite drag & drop nella barra laterale.")

with col_chat:
    st.header("💬 Chat con l'Archivio")
    filters = None
    if st.session_state.selected_paper:
        chat_context_info = f"sul documento: **{st.session_state.selected_paper}**"
        filters = MetadataFilters(filters=[ExactMatchFilter(key="file_name", value=st.session_state.selected_paper)])
        if st.button(" torna alla chat globale", key="deselect"):
            st.session_state.selected_paper = None
            st.rerun()
    elif selected_category_id != "Tutte":
        chat_context_info = f"sulla categoria: **{dict(category_choices).get(selected_category_id)}**"
        filters = MetadataFilters(filters=[ExactMatchFilter(key="category_id", value=selected_category_id)])
    else:
        chat_context_info = "su tutti i documenti."

    st.info(f"Stai chattando {chat_context_info}")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]): st.markdown(message["content"])

    if prompt := st.chat_input("Fai una domanda..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("L'AI sta pensando..."):
                try:
                    storage_context = StorageContext.from_defaults(persist_dir=DB_STORAGE_DIR)
                    if Settings.embed_model is None: initialize_services()
                    
                    # Carica l'indice dallo storage
                    index = load_index_from_storage(storage_context)
                    
                    chat_llm = get_chat_llm()
                    if chat_llm is None:
                        st.error("Chat LLM non disponibile. Verifica che Ollama sia in esecuzione.")
                        st.stop()
                        
                    query_engine = index.as_query_engine(filters=filters, similarity_top_k=3, llm=chat_llm)
                    response = query_engine.query(prompt)
                    st.markdown(str(response))
                    st.session_state.messages.append({"role": "assistant", "content": str(response)})
                except ValueError as e:
                    if "No index in storage context" in str(e) or "docstore.json not found" in str(e):
                        st.warning("L'archivio è vuoto o in fase di creazione. Aggiungi documenti e attendi il completamento per poter chattare.")
                    else:
                        st.error(f"Errore durante la query: {e}")
                except Exception as e:
                    st.error(f"Si è verificato un errore imprevisto durante la query: {e}")

# --- Meccanismo di Auto-Refresh ---
# Controlla lo stato e forza un refresh della pagina se un file è in elaborazione
# per dare un feedback visivo all'utente.
try:
    status_now = get_archivista_status()
    if status_now['status'] not in ["Inattivo", "Completato"] and "Errore" not in status_now['status']:
        time.sleep(3) # Attendi 3 secondi per non sovraccaricare il server
        st.rerun()
except Exception:
    # Ignora errori di lettura del file di stato che potrebbero verificarsi durante il reset
    pass
