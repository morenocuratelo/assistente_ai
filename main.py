import streamlit as st
import os
import pandas as pd
import json
import time
import threading
from datetime import datetime
from llama_index.core import PromptTemplate, Settings, StorageContext, load_index_from_storage
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter

from config import initialize_services, get_chat_llm
from file_utils import setup_database, get_papers_dataframe, delete_paper, update_paper_metadata
import prompt_manager
import knowledge_structure

# --- CONFIGURAZIONE ---
DB_STORAGE_DIR = "db_memoria"
DOCS_TO_PROCESS_DIR = "documenti_da_processare"
ARCHIVISTA_STATUS_FILE = os.path.join(DB_STORAGE_DIR, "archivista_status.json")

# --- INIZIALIZZAZIONE ---
st.set_page_config(page_title="Archivista AI v2.1", layout="wide")

if 'initialized' not in st.session_state:
    initialize_services()
    setup_database()
    st.session_state.initialized = True

# --- NUOVE VARIABILI PER IL LOG TEMPORANEO ---
if 'log_messages' not in st.session_state:
    st.session_state.log_messages = []
if 'auto_scan_completed' not in st.session_state:
    st.session_state.auto_scan_completed = False

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Ciao! Sono Archivista AI."}]
if 'selected_paper' not in st.session_state:
    st.session_state.selected_paper = None

def get_archivista_status():
    try:
        with open(ARCHIVISTA_STATUS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"status": "Inattivo", "file": None}

def add_log_message(message):
    """Aggiunge un messaggio al log temporaneo e mantiene solo gli ultimi 4 messaggi."""
    current_time = datetime.now().strftime("%H:%M:%S")
    st.session_state.log_messages.append(f"[{current_time}] {message}")
    # Mantieni solo gli ultimi 4 messaggi
    if len(st.session_state.log_messages) > 4:
        st.session_state.log_messages = st.session_state.log_messages[-4:]

def scan_and_process_documents():
    """
    Scansiona la cartella e invia i nuovi documenti al worker Celery.
    """
    try:
        # Importa la task da dove è definita
        from archivista_processing import process_document_task

        supported_extensions = ['.pdf', '.docx', '.rtf', '.html', '.htm', '.txt']
        new_files = [f for f in os.listdir(DOCS_TO_PROCESS_DIR) if any(f.lower().endswith(ext) for ext in supported_extensions)]
        if not new_files:
            add_log_message("Nessun nuovo documento da processare.")
            return

        add_log_message(f"Trovati {len(new_files)} nuovi documenti da processare")

        # Proviamo a inviare ogni file come task separata al worker
        sent = 0
        for file_name in new_files:
            file_path = os.path.join(DOCS_TO_PROCESS_DIR, file_name)
            try:
                add_log_message(f"Avvio processamento: {file_name}")
                process_document_task.delay(file_path)
                sent += 1
                add_log_message(f"File {file_name} inviato per processamento")
            except Exception:
                # Se Celery/Redis non è disponibile, eseguiamo localmente per non bloccare l'utente
                add_log_message("Broker Celery non disponibile: esecuzione locale")
                try:
                    # call the task function synchronously
                    process_document_task(file_path)
                    sent += 1
                    add_log_message(f"File {file_name} processato localmente")
                except Exception as e_local:
                    add_log_message(f"Errore processamento {file_name}: {str(e_local)[:50]}...")

        add_log_message(f"{sent} documenti inviati per il processamento")
        add_log_message("L'archivio si aggiornerà automaticamente al completamento.")
    except Exception as e:
        add_log_message(f"Errore durante la scansione: {str(e)[:50]}...")

def auto_scan_at_startup():
    """Esegue la scansione automatica all'avvio se non è già stata completata."""
    if not st.session_state.auto_scan_completed:
        add_log_message("Avvio scansione automatica documenti...")
        scan_and_process_documents()
        st.session_state.auto_scan_completed = True

# --- UI ---
# Esegui la scansione automatica all'avvio
auto_scan_at_startup()

with st.sidebar:
    st.title("Archivista AI")
    status = get_archivista_status()
    st.markdown(f"**Stato:** {status['status']}")
    if status.get('file'): st.markdown(f"**File:** `{status['file']}`")
    st.divider()

    # Log temporaneo nella sidebar
    if st.session_state.log_messages:
        st.subheader("📋 Log Attività")
        for log_msg in st.session_state.log_messages:
            st.text(log_msg)
        st.divider()

    if st.button("🔍 Scansiona Nuovi Documenti", use_container_width=True, type="primary"):
        scan_and_process_documents()
    st.divider()
    
    st.title("Filtri Chat")
    category_choices = knowledge_structure.get_category_choices()
    selected_category_id = st.selectbox(
        "Filtra per Categoria:",
        options=[opt[0] for opt in category_choices],
        format_func=lambda x: dict(category_choices).get(x, "Tutte")
    )

st.title("📚 Archivio della Conoscenza")
col_archive, col_chat = st.columns([0.45, 0.55])

with col_archive:
    st.header("🗂️ Documenti Categorizzati")
    papers_df = get_papers_dataframe()

    if not papers_df.empty:
        for category, group in papers_df.groupby(['category_id', 'category_name']):
            category_id, category_name = category
            if category_id != "UNCATEGORIZED/C00" or not group.empty:
                with st.expander(f"**{category_name}** ({len(group)} doc/s)"):
                    for _, row in group.iterrows():
                        if st.button(f"📄 {row.get('title', row['file_name'])}", key=row['file_name'], use_container_width=True):
                             st.session_state.selected_paper = row['file_name']
                             st.rerun()
    else:
        st.info(f"L'archivio è vuoto. Aggiungi file in `{DOCS_TO_PROCESS_DIR}` e scansiona.")

with col_chat:
    st.header("💬 Chat con l'Archivio")
    
    chat_context_info = "su tutti i documenti."
    filters = None

    if st.session_state.selected_paper:
        chat_context_info = f"sul documento: **{st.session_state.selected_paper}**"
        filters = MetadataFilters(filters=[ExactMatchFilter(key="file_name", value=st.session_state.selected_paper)])
        if st.button("Deseleziona documento", key="deselect"):
            st.session_state.selected_paper = None
            st.rerun()
    elif selected_category_id != "Tutte":
        chat_context_info = f"sulla categoria: **{dict(category_choices).get(selected_category_id)}**"
        filters = MetadataFilters(filters=[ExactMatchFilter(key="category_id", value=selected_category_id)])

    st.info(f"Stai chattando {chat_context_info}")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Fai una domanda..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("L'AI sta pensando..."):
                try:
                    storage_context = StorageContext.from_defaults(persist_dir=DB_STORAGE_DIR)
                    # Load the most recent index (the last one in the index_store)
                    # Ensure embed_model is set before loading index
                    if Settings.embed_model is None:
                        print("Embedding model not set, reinitializing services...")
                        initialize_services()
                    index = load_index_from_storage(storage_context)

                    # Get chat LLM for better responses
                    chat_llm = get_chat_llm()
                    if chat_llm is None:
                        st.error("Chat LLM non disponibile. Verifica che Ollama sia in esecuzione.")
                        st.stop()

                    query_engine = index.as_query_engine(
                        filters=filters,
                        similarity_top_k=3,
                        llm=chat_llm
                    )
                    response = query_engine.query(prompt)
                    st.markdown(str(response))
                    st.session_state.messages.append({"role": "assistant", "content": str(response)})
                except ValueError as e:
                    if "No index in storage context" in str(e):
                        st.warning("L'archivio è vuoto. Aggiungi documenti per iniziare a chattare.")
                    else:
                        st.error(f"Errore durante la query: {e}")
                except Exception as e:
                    st.error(f"Errore durante la query: {e}")
