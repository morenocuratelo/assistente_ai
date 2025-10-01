import streamlit as st
import os
import time
import json
import pandas as pd
from datetime import datetime
from llama_index.core import Settings, StorageContext, load_index_from_storage
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter

from config import initialize_services, get_chat_llm
from file_utils import setup_database, get_papers_dataframe, update_paper_metadata
import knowledge_structure

# --- CONFIGURAZIONE ---
DB_STORAGE_DIR = "db_memoria"
DOCS_TO_PROCESS_DIR = "documenti_da_processare"
ARCHIVISTA_STATUS_FILE = os.path.join(DB_STORAGE_DIR, "archivista_status.json")

# --- INIZIALIZZAZIONE ---
st.set_page_config(page_title="Archivista AI v2.3", layout="wide")

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
    st.session_state.messages = [{"role": "assistant", "content": "Ciao! Sono Archivista AI. Puoi trascinare i tuoi documenti nella barra laterale per iniziare."}]
    st.session_state.selected_paper = None

    # Navigation state for new architecture
    st.session_state.current_view = 'chat'

def get_archivista_status():
    """Legge lo stato corrente del processo di indicizzazione da un file JSON."""
    try:
        # Verifica che la directory esista
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

def show_temporary_success(message, duration=3):
    """Mostra un messaggio di successo temporaneo che scompare automaticamente."""
    st.session_state.temp_notification = {
        'message': message,
        'type': 'success',
        'timestamp': time.time(),
        'duration': duration
    }

def show_temporary_error(message, duration=5):
    """Mostra un messaggio di errore temporaneo che scompare automaticamente."""
    st.session_state.temp_notification = {
        'message': message,
        'type': 'error',
        'timestamp': time.time(),
        'duration': duration
    }

def display_temporary_notifications():
    """Visualizza le notifiche temporanee se presenti."""
    if 'temp_notification' in st.session_state:
        notification = st.session_state.temp_notification
        elapsed = time.time() - notification['timestamp']

        if elapsed < notification['duration']:
            if notification['type'] == 'success':
                st.success(f"✅ {notification['message']}")
            elif notification['type'] == 'error':
                st.error(f"❌ {notification['message']}")
        else:
            # Rimuovi notifica scaduta
            del st.session_state.temp_notification

def preserve_editor_state():
    """Preserva lo stato corrente dell'editor."""
    if 'edit_paper' in st.session_state:
        st.session_state.editor_state = {
            'edit_paper': st.session_state.edit_paper,
            'show_live_preview': st.session_state.get('show_live_preview', False),
            'edit_timestamp': time.time()
        }

def restore_editor_state():
    """Ripristina lo stato dell'editor se disponibile."""
    if 'editor_state' in st.session_state:
        state = st.session_state.editor_state
        # Ripristina solo se lo stato è recente (entro 30 secondi)
        if time.time() - state.get('edit_timestamp', 0) < 30:
            st.session_state.edit_paper = state['edit_paper']
            if state['show_live_preview']:
                st.session_state.show_live_preview = True

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

def get_original_file_path(row):
    """
    Trova il percorso del file originale nella cartella di archivio categorizzata.
    """
    try:
        category_id = row.get('category_id', '')
        file_name = row.get('file_name', '')

        if category_id and file_name:
            # Costruisci il percorso nella cartella categorizzata
            categorized_path = os.path.join("Dall_Origine_alla_Complessita", *category_id.split('/'), file_name)
            if os.path.exists(categorized_path):
                return categorized_path

        # Fallback: cerca nella cartella documenti_da_processare
        fallback_path = os.path.join(DOCS_TO_PROCESS_DIR, file_name)
        if os.path.exists(fallback_path):
            return fallback_path

        return None
    except Exception as e:
        st.error(f"Errore nella ricerca del file: {e}")
        return None

def display_pdf_pages(file_path):
    """
    Converte le pagine del PDF in immagini e le mostra usando PyMuPDF.
    """
    try:
        import fitz  # PyMuPDF

        # Apri il PDF
        doc = fitz.open(file_path)

        if len(doc) == 0:
            st.warning("📄 Il PDF non contiene pagine.")
            return

        # Mostra informazioni sul documento
        st.info(f"📊 PDF con {len(doc)} pagine")

        # Crea un selettore per scegliere la pagina (se più di una pagina)
        if len(doc) > 1:
            page_number = st.selectbox(
                "Seleziona pagina:",
                options=range(len(doc)),
                format_func=lambda x: f"Pagina {x + 1}",
                key="pdf_page_selector"
            )
        else:
            page_number = 0

        # Converte la pagina selezionata in immagine
        page = doc.load_page(page_number)

        # Renderizza la pagina come immagine (zoom 2x per qualità)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))

        # Converte in formato PIL Image
        img_data = pix.tobytes("png")
        from PIL import Image
        import io

        image = Image.open(io.BytesIO(img_data))

        # Mostra l'immagine
        st.image(image, caption=f"Pagina {page_number + 1} di {len(doc)}", use_column_width=True)

        # Chiudi il documento
        doc.close()

    except ImportError:
        st.error("❌ PyMuPDF non è installato correttamente.")
    except Exception as e:
        st.error(f"❌ Errore nella visualizzazione del PDF: {e}")
        st.info("Assicurati che il file sia un PDF valido e che PyMuPDF sia installato correttamente.")

def display_text_content(file_path):
    """
    Mostra il contenuto testuale estratto per file non-PDF.
    """
    try:
        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext == '.txt':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                st.info(f"📄 File di testo (.txt) - {len(content)} caratteri")
                # Mostra solo i primi 5000 caratteri per non sovraccaricare l'interfaccia
                display_text = content[:5000] + ("..." if len(content) > 5000 else "")
                st.text_area("Contenuto del file:", value=display_text, height=300, disabled=True)
            except UnicodeDecodeError:
                st.warning("⚠️ Impossibile leggere il file di testo con codifica UTF-8.")

        elif file_ext == '.docx':
            try:
                from docx import Document as DocxDocument
                doc = DocxDocument(file_path)
                content = '\n'.join([paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()])
                st.info(f"📄 Documento Word (.docx) - {len(content)} caratteri")
                display_text = content[:5000] + ("..." if len(content) > 5000 else "")
                st.text_area("Contenuto del documento:", value=display_text, height=300, disabled=True)
            except Exception as e:
                st.warning(f"⚠️ Errore nella lettura del file .docx: {e}")

        elif file_ext in ['.html', '.htm']:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                st.info(f"📄 Pagina HTML (.html) - {len(content)} caratteri")

                # Estrai e mostra solo il testo senza tag HTML
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(content, 'html.parser')
                text_content = soup.get_text()

                display_text = text_content[:5000] + ("..." if len(text_content) > 5000 else "")
                st.text_area("Contenuto testuale:", value=display_text, height=300, disabled=True)
            except Exception as e:
                st.warning(f"⚠️ Errore nella lettura del file HTML: {e}")

        elif file_ext == '.rtf':
            try:
                from striprtf.striprtf import rtf_to_text
                with open(file_path, 'r', encoding='utf-8') as f:
                    rtf_content = f.read()
                content = rtf_to_text(rtf_content)
                st.info(f"📄 Documento RTF (.rtf) - {len(content)} caratteri")
                display_text = content[:5000] + ("..." if len(content) > 5000 else "")
                st.text_area("Contenuto del documento:", value=display_text, height=300, disabled=True)
            except Exception as e:
                st.warning(f"⚠️ Errore nella lettura del file RTF: {e}")

        else:
            st.info(f"📄 File {file_ext} - Visualizzazione non supportata")
            st.text(f"Percorso: {file_path}")

    except Exception as e:
        st.error(f"❌ Errore nella visualizzazione del file: {e}")

def display_chat_archive_view():
    """
    Enhanced chat-focused archive view optimized for document selection and chat context.
    """
    st.markdown("### 💬 Selezione Documenti per Chat")
    st.info("📋 Usa questa vista per selezionare documenti da aggiungere al contesto della chat.")

    papers_df = get_papers_dataframe()

    if papers_df.empty:
        st.info("📭 L'archivio è vuoto. Aggiungi documenti tramite la barra laterale per iniziare.")
        return

    # Search and filter section
    st.markdown("#### 🔍 Ricerca e Filtri")

    col1, col2, col3 = st.columns([0.4, 0.3, 0.3])

    with col1:
        search_query = st.text_input(
            "🔍 Cerca documenti:",
            placeholder="Titolo, autore, contenuto...",
            key="chat_archive_search"
        )

    with col2:
        # Quick category filter
        quick_category = st.selectbox(
            "📂 Categoria rapida:",
            ["Tutte"] + [cat[0] for cat in knowledge_structure.get_category_choices()],
            key="quick_category_filter"
        )

    with col3:
        # Sort options
        sort_option = st.selectbox(
            "📊 Ordina per:",
            ["Titolo", "Anno", "Autore", "Categoria"],
            key="chat_sort_option"
        )

    # Apply filters
    filtered_df = papers_df.copy()

    if search_query:
        search_lower = search_query.lower()
        filtered_df = filtered_df[
            filtered_df['title'].str.lower().str.contains(search_lower, na=False) |
            filtered_df['authors'].str.lower().str.contains(search_lower, na=False) |
            filtered_df['formatted_preview'].str.lower().str.contains(search_lower, na=False)
        ]

    if quick_category != "Tutte":
        filtered_df = filtered_df[filtered_df['category_id'] == quick_category]

    # Apply sorting
    sort_columns = {
        "Titolo": 'title',
        "Anno": 'publication_year',
        "Autore": 'authors',
        "Categoria": 'category_name'
    }

    if not filtered_df.empty:
        # Handle NaN values for sorting
        filtered_df = filtered_df.sort_values(
            sort_columns[sort_option],
            na_position='last'
        )

    # Display results
    if filtered_df.empty:
        st.warning(f"⚠️ Nessun documento trovato per i filtri selezionati.")
        if st.button("🗑️ Cancella Filtri", key="clear_chat_filters"):
            # Clear filter state
            if 'chat_archive_search' in st.session_state:
                del st.session_state.chat_archive_search
            if 'quick_category_filter' in st.session_state:
                del st.session_state.quick_category_filter
            st.rerun()
    else:
        st.success(f"✅ {len(filtered_df)} documenti trovati")

        # Group by category for better organization
        categories_in_results = filtered_df['category_id'].unique()

        if len(categories_in_results) > 1:
            # Multi-category view
            for category_id in categories_in_results:
                category_docs = filtered_df[filtered_df['category_id'] == category_id]
                category_name = category_docs['category_name'].iloc[0] if not category_docs.empty else "Senza categoria"

                with st.expander(f"📂 {category_name} ({len(category_docs)} documenti)", expanded=True):
                    display_document_cards(category_docs)
        else:
            # Single category view - show as grid
            display_document_cards(filtered_df)

def display_document_cards(documents_df):
    """
    Display documents as interactive cards optimized for chat context selection.
    """
    # Calculate grid layout
    docs_per_row = 3
    total_docs = len(documents_df)

    for i in range(0, total_docs, docs_per_row):
        cols = st.columns(docs_per_row)

        for j in range(docs_per_row):
            if i + j < total_docs:
                doc = documents_df.iloc[i + j]

                with cols[j]:
                    # Document card
                    with st.container():
                        # Header with title and status
                        title = doc.get('title', doc['file_name'])
                        status_icon = "✅" if doc.get('formatted_preview') else "⏳"
                        category_name = doc.get('category_name', 'Senza categoria')

                        st.markdown(f"**{status_icon} {title}**")
                        st.caption(f"📂 {category_name}")

                        # Metadata
                        metadata_parts = []
                        if doc.get('authors'):
                            metadata_parts.append(f"👥 {doc['authors']}")
                        if doc.get('publication_year'):
                            metadata_parts.append(f"📅 {doc['publication_year']}")

                        if metadata_parts:
                            st.caption(" | ".join(metadata_parts))

                        # Preview snippet if available
                        if doc.get('formatted_preview'):
                            preview = doc['formatted_preview'][:100] + "..." if len(doc['formatted_preview']) > 100 else doc['formatted_preview']
                            st.caption(f"📄 {preview}")

                        # Action buttons
                        col_a, col_b, col_c = st.columns([1, 1, 1])

                        with col_a:
                            # Add to chat context
                            if st.button(
                                "💬 Chat",
                                key=f"chat_context_{doc['file_name']}",
                                help="Aggiungi al contesto chat",
                                use_container_width=True
                            ):
                                st.session_state.selected_paper = doc['file_name']
                                st.success(f"✅ '{title}' aggiunto al contesto chat!")
                                st.info("💡 Vai alla tab Chat per iniziare la conversazione.")

                        with col_b:
                            # Quick preview
                            if st.button(
                                "👁️",
                                key=f"quick_preview_{doc['file_name']}",
                                help="Anteprima rapida",
                                use_container_width=True
                            ):
                                st.session_state.quick_preview_doc = doc['file_name']
                                st.rerun()

                        with col_c:
                            # More options
                            with st.popover("⋮"):
                                st.markdown(f"**{title}**")

                                if st.button("📋 Copia Info", key=f"copy_info_{doc['file_name']}"):
                                    import pyperclip
                                    info_text = f"Titolo: {title}\nAutori: {doc.get('authors', 'N/A')}\nAnno: {doc.get('publication_year', 'N/A')}\nCategoria: {category_name}"
                                    try:
                                        pyperclip.copy(info_text)
                                        st.success("📋 Info copiate negli appunti!")
                                    except:
                                        st.text_area("Info documento:", value=info_text, height=100)
                                        st.info("📋 Seleziona e copia manualmente")

                                if st.button("🔗 Link Chat", key=f"link_chat_{doc['file_name']}"):
                                    st.info("🔗 Usa questo documento nel contesto della chat")

# --- UI: QUICK PREVIEW MODAL ---
if 'quick_preview_doc' in st.session_state:
    papers_df = get_papers_dataframe()
    preview_row = papers_df[papers_df['file_name'] == st.session_state.quick_preview_doc]

    if not preview_row.empty:
        row = preview_row.iloc[0]

        st.markdown("---")
        st.subheader(f"👁️ Anteprima Rapida: {row.get('title', row['file_name'])}")

        # Two-column layout for preview
        col1, col2 = st.columns([0.6, 0.4])

        with col1:
            st.markdown("**📋 Informazioni Documento:**")
            st.markdown(f"**Titolo:** {row.get('title', 'N/A')}")
            st.markdown(f"**Autori:** {row.get('authors', 'N/A')}")
            st.markdown(f"**Anno:** {row.get('publication_year', 'N/A')}")
            st.markdown(f"**Categoria:** {row.get('category_name', 'N/A')}")

            if row.get('formatted_preview'):
                st.markdown("**📖 Anteprima:**")
                st.info(row['formatted_preview'])
            else:
                st.warning("⚠️ Nessuna anteprima disponibile")

        with col2:
            st.markdown("**⚡ Azioni Rapide:**")

            if st.button("💬 Usa nel Chat", key="use_in_chat", use_container_width=True):
                st.session_state.selected_paper = row['file_name']
                st.success("✅ Documento aggiunto al contesto chat!")
                del st.session_state.quick_preview_doc
                st.rerun()

            if st.button("📝 Modifica Anteprima", key="edit_from_preview", use_container_width=True):
                st.session_state.edit_paper = row['file_name']
                del st.session_state.quick_preview_doc
                st.rerun()

            # Show file path if available
            file_path = get_original_file_path(row)
            if file_path:
                st.info(f"📁 File: `{os.path.basename(file_path)}`")

        # Close button
        st.markdown("---")
        if st.button("✖️ Chiudi Anteprima", key="close_quick_preview", use_container_width=True):
            del st.session_state.quick_preview_doc
            st.rerun()
    else:
        st.error("❌ Documento non trovato.")
        if st.button("✖️ Chiudi", key="close_preview_error"):
            del st.session_state.quick_preview_doc
            st.rerun()

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
            # Se c'è un errore con docstore.json, mostra un messaggio più user-friendly
            if "docstore.json" in status_text and "No such file or directory" in status_text:
                st.info("**📁 Stato:** Inattivo (Database non ancora creato)")
            else:
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

# --- UI: PREVIEW MODAL ---
if 'preview_paper' in st.session_state and st.session_state.preview_paper:
    papers_df = get_papers_dataframe()
    preview_row = papers_df[papers_df['file_name'] == st.session_state.preview_paper]

    if not preview_row.empty:
        row = preview_row.iloc[0]
        preview_text = row.get('formatted_preview', '')

        if preview_text:
            st.markdown("---")  # Separatore visivo
            st.subheader(f"📖 Anteprima: {row.get('title', row['file_name'])}")

            # Display preview in an expander for better UX
            with st.expander("📋 Visualizza anteprima completa", expanded=True):
                st.markdown(preview_text)

            # Edit and Close buttons
            col_edit, col_close = st.columns([0.5, 0.5])
            with col_edit:
                if st.button("✏️ Modifica Anteprima", key="edit_preview", use_container_width=True):
                    st.session_state.edit_paper = st.session_state.preview_paper
                    del st.session_state.preview_paper
                    st.rerun()
            with col_close:
                if st.button("✖️ Chiudi anteprima", key="close_preview", use_container_width=True):
                    del st.session_state.preview_paper
                    st.rerun()
        else:
            st.warning("⚠️ Anteprima non disponibile per questo documento.")
            if st.button("✖️ Chiudi", key="close_preview_no_content"):
                del st.session_state.preview_paper
                st.rerun()
    else:
        st.error("❌ Documento non trovato.")
        if st.button("✖️ Chiudi", key="close_preview_error"):
            del st.session_state.preview_paper
            st.rerun()

# --- UI: EDIT INTERFACE ---
if 'edit_paper' in st.session_state and st.session_state.edit_paper:
    # Visualizza notifiche temporanee se presenti
    display_temporary_notifications()
    papers_df = get_papers_dataframe()
    edit_row = papers_df[papers_df['file_name'] == st.session_state.edit_paper]

    if not edit_row.empty:
        row = edit_row.iloc[0]
        current_content = row.get('formatted_preview', '')

        st.markdown("---")
        st.subheader(f"✏️ Modifica Anteprima: {row.get('title', row['file_name'])}")

        # Two-column layout
        col_left, col_right = st.columns([0.5, 0.5])

        with col_left:
            st.markdown("### 📝 Editor")
            st.markdown("*Modifica il contenuto Markdown dell'anteprima:*")

            # Text area for editing
            edited_content = st.text_area(
                "Contenuto anteprima",
                value=current_content,
                height=400,
                key="edit_text_area",
                label_visibility="collapsed"
            )

            # Action buttons
            col_save, col_cancel, col_preview = st.columns([0.33, 0.33, 0.34])
            with col_save:
                if st.button("💾 Salva Modifiche", key="save_edit", use_container_width=True):
                    # Preserva lo stato prima del salvataggio
                    preserve_editor_state()

                    if update_paper_metadata(st.session_state.edit_paper, {'formatted_preview': edited_content}):
                        # Usa il nuovo sistema di notifiche temporanee
                        show_temporary_success(f"Modifiche salvate per: {row.get('title', row['file_name'])}")
                        add_log_message(f"Anteprima aggiornata: {row.get('title', row['file_name'])}")

                        # Mantieni l'editor aperto senza refresh completo
                        # Ricarica solo i dati necessari
                        papers_df = get_papers_dataframe()
                        if not papers_df.empty:
                            updated_row = papers_df[papers_df['file_name'] == st.session_state.edit_paper]
                            if not updated_row.empty:
                                # Aggiorna il contenuto corrente con i dati salvati
                                current_content = updated_row.iloc[0].get('formatted_preview', '')

                        # Non chiudere l'editor, lascia che l'utente continui a lavorare
                        st.rerun()
                    else:
                        show_temporary_error("Errore nel salvataggio delle modifiche.")

            with col_cancel:
                if st.button("❌ Annulla", key="cancel_edit", use_container_width=True):
                    del st.session_state.edit_paper
                    st.rerun()

            with col_preview:
                if st.button("👁️ Anteprima Live", key="live_preview", use_container_width=True):
                    st.session_state.show_live_preview = not st.session_state.get('show_live_preview', False)
                    st.rerun()

        with col_right:
            st.markdown("### 📄 Visualizzatore Documento")

            # Get file path for the original document
            file_path = get_original_file_path(row)
            if file_path and os.path.exists(file_path):
                if file_path.lower().endswith('.pdf'):
                    st.markdown("*Visualizzazione pagine del PDF originale:*")
                    display_pdf_pages(file_path)
                else:
                    st.markdown("*Contenuto del documento originale:*")
                    display_text_content(file_path)
            else:
                st.warning(f"⚠️ File originale non trovato: {row['file_name']}")

            # Live preview section
            if st.session_state.get('show_live_preview', False):
                st.markdown("---")
                st.markdown("### 👁️ Anteprima Live")
                st.markdown("*Come apparirà l'anteprima dopo il salvataggio:*")
                st.markdown(edited_content)

    else:
        st.error("❌ Documento non trovato.")
        if st.button("✖️ Chiudi", key="close_edit_error"):
            del st.session_state.edit_paper
            st.rerun()

# --- UI: NEW SIDEBAR NAVIGATION ---
def render_navigation_sidebar():
    """Render the new simplified sidebar navigation."""
    with st.sidebar:
        st.title("Archivista AI")

        # Main Navigation
        st.markdown("### 🧭 Navigazione")

        # Chat button (default)
        if st.button(
            "💬 Chat",
            key="nav_chat",
            use_container_width=True,
            type="primary" if st.session_state.current_view == 'chat' else "secondary",
            help="Chatta con i tuoi documenti"
        ):
            st.session_state.current_view = 'chat'
            st.rerun()

        # Archive button
        if st.button(
            "🗂️ Archivio",
            key="nav_archive",
            use_container_width=True,
            type="primary" if st.session_state.current_view == 'archive' else "secondary",
            help="Esplora e gestisci i file"
        ):
            st.session_state.current_view = 'archive'
            st.rerun()

        # Dashboard button
        if st.button(
            "📊 Dashboard",
            key="nav_dashboard",
            use_container_width=True,
            type="primary" if st.session_state.current_view == 'dashboard' else "secondary",
            help="Visualizza statistiche"
        ):
            st.session_state.current_view = 'dashboard'
            st.rerun()

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
        st.markdown("### 📊 Stato")
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
                for msg in st.session_state.log_messages[:3]:  # Show only last 3
                    st.text(msg)

def render_chat_view():
    """Render the new optimized chat view."""
    st.markdown("# 💬 Chat con l'Archivio")
    st.caption("Fai domande sui tuoi documenti e ottieni risposte intelligenti")

    # Chat filters moved below header, above messages
    st.markdown("### 🔧 Filtri Chat")

    col1, col2, col3 = st.columns([0.3, 0.3, 0.4])

    with col1:
        # Category filter for chat
        category_choices = knowledge_structure.get_category_choices()
        selected_category_id = st.selectbox(
            "Categoria:",
            options=["Tutte"] + [opt[0] for opt in category_choices],
            format_func=lambda x: dict(category_choices).get(x, "Tutte le categorie") if x != "Tutte" else "Tutte le categorie",
            key="chat_category_filter",
            label_visibility="collapsed"
        )

    with col2:
        # Document filter for chat
        papers_df = get_papers_dataframe()
        document_options = ["Tutti"] + papers_df['file_name'].tolist()
        document_titles = ["Tutti i documenti"] + [row.get('title', row['file_name']) for _, row in papers_df.iterrows()]

        selected_doc_title = st.selectbox(
            "Documento:",
            options=["Tutti"] + papers_df['file_name'].tolist(),
            format_func=lambda x: "Tutti i documenti" if x == "Tutti" else next((row.get('title', row['file_name']) for _, row in papers_df.iterrows() if row['file_name'] == x), x),
            key="chat_document_filter",
            label_visibility="collapsed"
        )

    with col3:
        # Clear filters button
        if st.button("🗑️ Cancella Filtri", use_container_width=True):
            if 'chat_category_filter' in st.session_state:
                del st.session_state.chat_category_filter
            if 'chat_document_filter' in st.session_state:
                del st.session_state.chat_document_filter
            st.rerun()

    # Show current context
    if selected_doc_title != "Tutti i documenti":
        selected_file_name = next(row['file_name'] for _, row in papers_df.iterrows() if row.get('title', row['file_name']) == selected_doc_title)
        st.info(f"💬 Contesto attivo: **{selected_doc_title}**")
    elif selected_category_id != "Tutte":
        st.info(f"💬 Contesto attivo: Categoria **{dict(category_choices).get(selected_category_id)}**")
    else:
        st.info("💬 Contesto attivo: **Tutti i documenti**")

    st.divider()

    # Chat messages area
    st.markdown("### 💭 Conversazione")

    # Display chat messages
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Fai una domanda sui tuoi documenti..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)

        # Generate AI response
        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner("🤔 L'AI sta pensando..."):
                    try:
                        # Setup filters based on selections
                        filters = None
                        if selected_doc_title != "Tutti i documenti":
                            filters = MetadataFilters(filters=[ExactMatchFilter(key="file_name", value=selected_file_name)])
                        elif selected_category_id != "Tutte":
                            filters = MetadataFilters(filters=[ExactMatchFilter(key="category_id", value=selected_category_id)])

                        # Get chat response (reusing existing logic)
                        chat_llm = get_chat_llm()
                        if chat_llm is None:
                            raise ConnectionError("Chat LLM non disponibile.")

                        # Check if we can use archive mode
                        db_path = os.path.join(DB_STORAGE_DIR, "docstore.json")
                        index_path = os.path.join(DB_STORAGE_DIR, "index_store.json")
                        all_required_files_exist = all(os.path.exists(p) for p in [db_path, index_path])
                        embed_model_available = Settings.embed_model is not None
                        has_specific_context = selected_doc_title != "Tutti i documenti" or selected_category_id != "Tutte"

                        use_archive_mode = all_required_files_exist and has_specific_context and embed_model_available

                        if use_archive_mode:
                            try:
                                storage_context = StorageContext.from_defaults(persist_dir=DB_STORAGE_DIR)
                                index = load_index_from_storage(storage_context)
                                query_engine = index.as_query_engine(filters=filters, similarity_top_k=3, llm=chat_llm)
                                response = query_engine.query(prompt)
                                response_content = str(response)
                            except:
                                use_archive_mode = False

                        if not use_archive_mode:
                            response = chat_llm.complete(prompt)
                            response_content = str(response)

                        # Display response
                        st.markdown(response_content)
                        st.session_state.messages.append({"role": "assistant", "content": response_content})

                    except Exception as e:
                        st.error(f"❌ Errore nella generazione risposta: {e}")
                        error_message = f"Si è verificato un errore: {e}"
                        st.session_state.messages.append({"role": "assistant", "content": error_message})

def render_archive_view():
    """Render the archive view with toggle between Chat View and File Explorer."""
    st.markdown("# 🗂️ Knowledge Explorer")

    # Toggle between Chat View and File Explorer
    st.markdown("### Modalità Visualizzazione")
    view_mode = st.radio(
        "Scegli la modalità:",
        ["Chat View", "File Explorer"],
        horizontal=True,
        key="archive_view_mode",
        help="Chat View: Selezione documenti ottimizzata | File Explorer: Gestione completa file"
    )

    if view_mode == "Chat View":
        # Use the chat-focused archive view
        display_chat_archive_view()
    else:
        # Use the full File Explorer
        try:
            from file_explorer_ui import create_three_column_layout, handle_file_actions

            # Handle any pending file actions first
            handle_file_actions()

            # Then show the main File Explorer interface
            create_three_column_layout()

        except ImportError as e:
            st.error(f"❌ Impossibile caricare File Explorer: {e}")
            st.info("🔧 Assicurati che il modulo file_explorer_ui sia disponibile.")
            # Fallback to chat view
            display_chat_archive_view()

def render_dashboard_view():
    """Render the dashboard view in full width."""
    st.markdown("# 📊 Dashboard Statistiche")

    try:
        from statistics import get_comprehensive_stats

        # Refresh button
        if st.button("🔄 Aggiorna Statistiche", use_container_width=True):
            get_comprehensive_stats.clear()

        # Get comprehensive stats
        stats = get_comprehensive_stats()

        # Main metrics in columns
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="📚 Documenti Totali",
                value=stats['basic_stats']['total_documents']
            )

        with col2:
            st.metric(
                label="📂 Categorie",
                value=stats['basic_stats']['total_categories']
            )

        with col3:
            st.metric(
                label="👥 Autori Unici",
                value=stats['basic_stats']['total_authors']
            )

        with col4:
            st.metric(
                label="⭐ Qualità Dati",
                value=f"{stats['data_quality']['completeness_score']}%"
            )

        # Charts section with full width
        st.markdown("### 📈 Analisi Dettagliata")

        col_left, col_right = st.columns([0.7, 0.3])

        with col_left:
            # Category distribution chart
            if stats['category_distribution']:
                st.markdown("#### 📂 Distribuzione per Categoria")
                cat_data = pd.DataFrame(stats['category_distribution'])
                st.bar_chart(cat_data.set_index('category_name')['count'])
            else:
                st.info("Nessuna categoria disponibile")

            # Temporal trend chart
            if stats['temporal_trend']:
                st.markdown("#### 📅 Trend Temporale")
                trend_data = pd.DataFrame(stats['temporal_trend'])
                st.line_chart(trend_data.set_index('period')['count'])
            else:
                st.info("Nessun dato temporale disponibile")

        with col_right:
            # Top categories
            st.markdown("#### 🏆 Categorie Principali")
            if stats['top_categories']:
                for i, cat in enumerate(stats['top_categories'][:8], 1):
                    percentage = cat.get('percentage', 0)
                    st.write(f"**{i}.** {cat['category_name']} ({cat['count']} doc - {percentage}%)")
            else:
                st.info("Nessuna categoria disponibile")

            # Top authors
            st.markdown("#### 👥 Autori Più Frequenti")
            if stats['author_stats']:
                for i, author in enumerate(stats['author_stats'][:8], 1):
                    st.write(f"**{i}.** {author['author']} ({author['document_count']} doc)")
            else:
                st.info("Nessun autore disponibile")

        # Data quality section
        st.markdown("### 🔍 Qualità dei Dati")

        quality_col1, quality_col2, quality_col3, quality_col4 = st.columns(4)

        with quality_col1:
            st.metric(
                label="✅ Con Anteprima",
                value=f"{stats['data_quality']['docs_with_preview']}/{stats['data_quality']['total_documents']}"
            )

        with quality_col2:
            st.metric(
                label="📅 Con Anno",
                value=f"{stats['data_quality']['docs_with_year']}/{stats['data_quality']['total_documents']}"
            )

        with quality_col3:
            st.metric(
                label="👤 Con Autori",
                value=f"{stats['data_quality']['docs_with_authors']}/{stats['data_quality']['total_documents']}"
            )

        with quality_col4:
            completeness = stats['data_quality']['completeness_score']
            if completeness >= 80:
                st.success(f"⭐ Completezza: {completeness}%")
            elif completeness >= 60:
                st.warning(f"⭐ Completezza: {completeness}%")
            else:
                st.error(f"⭐ Completezza: {completeness}%")

        # Recent activity with full width
        st.markdown("### 🕐 Attività Recente")

        if stats['recent_activity']:
            recent_df = pd.DataFrame(stats['recent_activity'])
            st.dataframe(
                recent_df[['title', 'category_name', 'processed_at']].head(15),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Nessuna attività recente")

    except ImportError:
        st.error("❌ Modulo statistics non disponibile")
    except Exception as e:
        st.error(f"❌ Errore nel caricamento dashboard: {e}")

# --- UI: MAIN CONTENT ---
def render_main_content():
    """Render the main content based on current view."""
    if st.session_state.current_view == 'chat':
        render_chat_view()
    elif st.session_state.current_view == 'archive':
        render_archive_view()
    elif st.session_state.current_view == 'dashboard':
        render_dashboard_view()
    else:
        # Default fallback
        render_chat_view()

# --- TABS CREATION ---
tab_dashboard, tab_archive, tab_batch, tab_export, tab_chat = st.tabs(["📊 Dashboard", "📚 Archivio", "🔧 Batch", "📤 Esporta", "💬 Chat"])

# --- TAB: DASHBOARD ---
with tab_dashboard:
    st.header("📊 Dashboard Statistica")

    try:
        from statistics import get_comprehensive_stats

        # Bottone per refresh manuale
        if st.button("🔄 Aggiorna Statistiche", use_container_width=True):
            # Forza ricarica cache
            get_comprehensive_stats.clear()

        # Ottieni statistiche complete
        stats = get_comprehensive_stats()

        # Layout a colonne per metriche principali
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="📚 Documenti Totali",
                value=stats['basic_stats']['total_documents']
            )

        with col2:
            st.metric(
                label="📂 Categorie",
                value=stats['basic_stats']['total_categories']
            )

        with col3:
            st.metric(
                label="👥 Autori Unici",
                value=stats['basic_stats']['total_authors']
            )

        with col4:
            st.metric(
                label="⭐ Qualità Dati",
                value=f"{stats['data_quality']['completeness_score']}%"
            )

        # Sezioni dettagliate
        col_left, col_right = st.columns([0.6, 0.4])

        with col_left:
            st.subheader("📈 Distribuzione per Categoria")

            if stats['category_distribution']:
                # Crea grafico a barre
                cat_data = pd.DataFrame(stats['category_distribution'])
                st.bar_chart(cat_data.set_index('category_name')['count'])
            else:
                st.info("Nessuna categoria disponibile")

            st.subheader("📅 Trend Temporale")

            if stats['temporal_trend']:
                # Crea grafico linea
                trend_data = pd.DataFrame(stats['temporal_trend'])
                st.line_chart(trend_data.set_index('period')['count'])
            else:
                st.info("Nessun dato temporale disponibile")

        with col_right:
            st.subheader("🏆 Top Categorie")

            if stats['top_categories']:
                for i, cat in enumerate(stats['top_categories'][:8], 1):
                    percentage = cat.get('percentage', 0)
                    st.write(f"**{i}.** {cat['category_name']} ({cat['count']} doc - {percentage}%)")
            else:
                st.info("Nessuna categoria disponibile")

            st.subheader("👥 Autori Più Frequenti")

            if stats['author_stats']:
                for i, author in enumerate(stats['author_stats'][:8], 1):
                    st.write(f"**{i}.** {author['author']} ({author['document_count']} doc)")
            else:
                st.info("Nessun autore disponibile")

        # Sezione qualità dati
        st.subheader("🔍 Qualità dei Dati")

        quality_col1, quality_col2, quality_col3, quality_col4 = st.columns(4)

        with quality_col1:
            st.metric(
                label="✅ Con Anteprima",
                value=f"{stats['data_quality']['docs_with_preview']}/{stats['data_quality']['total_documents']}"
            )

        with quality_col2:
            st.metric(
                label="📅 Con Anno",
                value=f"{stats['data_quality']['docs_with_year']}/{stats['data_quality']['total_documents']}"
            )

        with quality_col3:
            st.metric(
                label="👤 Con Autori",
                value=f"{stats['data_quality']['docs_with_authors']}/{stats['data_quality']['total_documents']}"
            )

        with quality_col4:
            completeness = stats['data_quality']['completeness_score']
            if completeness >= 80:
                st.success(f"⭐ Completezza: {completeness}%")
            elif completeness >= 60:
                st.warning(f"⭐ Completezza: {completeness}%")
            else:
                st.error(f"⭐ Completezza: {completeness}%")

        # Attività recente
        st.subheader("🕐 Attività Recente (7 giorni)")

        if stats['recent_activity']:
            recent_df = pd.DataFrame(stats['recent_activity'])
            st.dataframe(
                recent_df[['title', 'category_name', 'processed_at']].head(10),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Nessuna attività recente")

    except ImportError:
        st.error("❌ Modulo statistics non disponibile")
    except Exception as e:
        st.error(f"❌ Errore nel caricamento dashboard: {e}")

# --- TAB: ARCHIVIO ---
with tab_archive:
    st.header("📚 Archivio & File Explorer")

    # View mode toggle
    st.markdown("### Modalità Visualizzazione")
    view_mode = st.radio(
        "Scegli la modalità di visualizzazione:",
        ["Chat View", "File Explorer"],
        horizontal=True,
        key="archive_view_mode",
        help="Chat View: Selezione documenti per chat | File Explorer: Gestione avanzata file"
    )

    if view_mode == "Chat View":
        # Enhanced Chat-Focused Archive View
        display_chat_archive_view()
    else:
        # Full File Explorer Interface
        try:
            from file_explorer_ui import create_three_column_layout, handle_file_actions

            # Handle any pending file actions first
            handle_file_actions()

            # Then show the main File Explorer interface
            create_three_column_layout()

        except ImportError as e:
            st.error(f"❌ Impossibile caricare File Explorer: {e}")
            st.info("🔧 Assicurati che il modulo file_explorer_ui sia disponibile.")
            # Fallback to chat view
            display_chat_archive_view()

# --- TAB: OPERAZIONI BATCH ---
with tab_batch:
    st.header("🔧 Operazioni Batch")

    try:
        from batch_operations import get_available_operations, create_batch_operation, get_batch_preview, execute_batch_operation

        papers_df = get_papers_dataframe()
        if papers_df.empty:
            st.warning("⚠️ Nessun documento disponibile per operazioni batch")
        else:
            # Selezione documenti
            st.subheader("1. Seleziona Documenti")

            # Checkbox per selezionare tutto
            select_all = st.checkbox("✅ Seleziona Tutti", key="select_all_batch")

            if select_all:
                selected_files = papers_df['file_name'].tolist()
                st.session_state.selected_files_batch = selected_files
            else:
                if 'selected_files_batch' not in st.session_state:
                    st.session_state.selected_files_batch = []

            # Mostra documenti con checkbox
            selected_files = []
            for category, group in papers_df.groupby(['category_id', 'category_name']):
                category_id, category_name = category
                with st.expander(f"**{category_name}** ({len(group)} documenti)"):
                    for _, row in group.iterrows():
                        file_name = row['file_name']
                        is_selected = st.checkbox(
                            f"📄 {row.get('title', file_name)}",
                            key=f"batch_{file_name}",
                            value=file_name in st.session_state.get('selected_files_batch', [])
                        )

                        if is_selected:
                            selected_files.append(file_name)

            st.session_state.selected_files_batch = selected_files
            st.info(f"📋 Documenti selezionati: {len(selected_files)}")

            if selected_files:
                # Selezione operazione
                st.subheader("2. Scegli Operazione")

                operations = get_available_operations()
                operation_choice = st.selectbox(
                    "Operazione da eseguire:",
                    options=[op['id'] for op in operations],
                    format_func=lambda x: next(op['name'] for op in operations if op['id'] == x),
                    key="batch_operation_choice"
                )

                selected_operation = next(op for op in operations if op['id'] == operation_choice)

                # Input valore in base all'operazione
                operation_value = None

                if selected_operation['id'] in ['set_title', 'add_author', 'remove_author']:
                    operation_value = st.text_input(
                        f"Valore per '{selected_operation['name']}':",
                        key=f"batch_value_{selected_operation['id']}"
                    )
                elif selected_operation['id'] == 'set_year':
                    current_year = datetime.now().year
                    operation_value = st.number_input(
                        "Anno di pubblicazione:",
                        min_value=1000,
                        max_value=current_year + 1,
                        value=current_year,
                        key="batch_year_input"
                    )
                elif selected_operation['id'] == 'set_category':
                    categories = knowledge_structure.get_category_choices()
                    category_dict = dict(categories)
                    operation_value = st.selectbox(
                        "Nuova categoria:",
                        options=[cat[0] for cat in categories],
                        format_func=lambda x: category_dict.get(x, "Seleziona categoria"),
                        key="batch_category_input"
                    )

                # Anteprima modifiche
                if operation_value and st.checkbox("👁️ Mostra anteprima modifiche", key="show_batch_preview"):
                    st.subheader("3. Anteprima Modifiche")

                    try:
                        batch_op = create_batch_operation(operation_choice, operation_value, selected_files)
                        preview_data = get_batch_preview(batch_op, papers_df)

                        if preview_data:
                            preview_df = pd.DataFrame(preview_data)
                            st.dataframe(
                                preview_df[['file_name', 'current_title', 'new_title']].head(10),
                                use_container_width=True,
                                hide_index=True
                            )
                            st.info(f"📊 Anteprima mostra primi 10 documenti. Saranno modificati {len(selected_files)} documenti totali.")
                        else:
                            st.warning("⚠️ Impossibile generare anteprima")

                    except Exception as e:
                        st.error(f"❌ Errore generazione anteprima: {e}")

                # Esecuzione operazione
                st.subheader("4. Esegui Operazione")

                if st.button("🚀 Esegui Operazione Batch", type="primary", use_container_width=True):
                    if not operation_value:
                        st.error("❌ Inserisci un valore per l'operazione")
                    else:
                        try:
                            with st.spinner("Esecuzione operazione batch in corso..."):
                                batch_op = create_batch_operation(operation_choice, operation_value, selected_files)
                                success, message, affected_count = execute_batch_operation(batch_op)

                            if success:
                                show_temporary_success(f"Operazione completata! {affected_count} documenti aggiornati.")
                                add_log_message(f"Batch operation: {selected_operation['name']} su {affected_count} documenti")
                                # Ricarica dati
                                papers_df = get_papers_dataframe()
                                st.rerun()
                            else:
                                show_temporary_error(f"Operazione fallita: {message}")

                        except Exception as e:
                            show_temporary_error(f"Errore esecuzione: {str(e)}")
            else:
                st.info("💡 Seleziona almeno un documento per iniziare")

    except ImportError:
        st.error("❌ Modulo batch_operations non disponibile")
    except Exception as e:
        st.error(f"❌ Errore operazioni batch: {e}")

# --- TAB: ESPORTAZIONE ---
with tab_export:
    st.header("📤 Esporta Dati")

    try:
        from export_manager import (
            get_exportable_dataframe, create_export_data, get_export_summary,
            get_category_choices_for_filter, get_author_choices_for_filter, get_year_choices_for_filter
        )

        papers_df = get_papers_dataframe()
        if papers_df.empty:
            st.warning("⚠️ Nessun documento disponibile per l'esportazione")
        else:
            st.subheader("1. Configura Esportazione")

            # Selezione formato
            export_format = st.selectbox(
                "Formato esportazione:",
                options=['csv', 'json', 'excel'],
                format_func=lambda x: {
                    'csv': '📄 CSV (Comma Separated Values)',
                    'json': '📋 JSON (JavaScript Object Notation)',
                    'excel': '📊 Excel (Spreadsheet)'
                }.get(x, x.upper()),
                key="export_format"
            )

            # Opzioni avanzate
            col1, col2 = st.columns(2)

            with col1:
                include_preview = st.checkbox("Includi anteprime", value=False, key="include_preview")

                category_filter = st.selectbox(
                    "Filtra per categoria:",
                    options=["Tutte"] + [cat[0] for cat in get_category_choices_for_filter()],
                    key="export_category_filter"
                )

            with col2:
                author_filter = st.selectbox(
                    "Filtra per autore:",
                    options=["Tutti"] + get_author_choices_for_filter(),
                    key="export_author_filter"
                )

                year_filter = st.selectbox(
                    "Filtra per anno:",
                    options=[None] + get_year_choices_for_filter(),
                    format_func=lambda x: "Tutti gli anni" if x is None else str(x),
                    key="export_year_filter"
                )

            # Riepilogo esportazione
            st.subheader("2. Riepilogo Dati")

            summary = get_export_summary(
                category_filter=category_filter if category_filter != "Tutte" else None,
                author_filter=author_filter if author_filter != "Tutti" else None,
                year_filter=year_filter,
                include_preview=include_preview
            )

            if summary['document_count'] > 0:
                summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)

                with summary_col1:
                    st.metric("📚 Documenti", summary['document_count'])
                with summary_col2:
                    st.metric("📂 Categorie", summary['category_count'])
                with summary_col3:
                    st.metric("👥 Autori", summary['author_count'])
                with summary_col4:
                    st.metric("💾 Dimensione stimata", summary['file_size_estimate'])

                if summary['year_range']:
                    st.info(f"📅 Range anni: {summary['year_range']}")

                # Download button
                st.subheader("3. Scarica File")

                if st.button("⬇️ Genera e Scarica File", type="primary", use_container_width=True):
                    try:
                        with st.spinner("Generazione file in corso..."):
                            filename, file_content = create_export_data(
                                format_type=export_format,
                                category_filter=category_filter if category_filter != "Tutte" else None,
                                author_filter=author_filter if author_filter != "Tutti" else None,
                                year_filter=year_filter,
                                include_preview=include_preview
                            )

                        # Crea download button
                        st.download_button(
                            label=f"💾 Scarica {filename}",
                            data=file_content,
                            file_name=filename,
                            mime={
                                'csv': 'text/csv',
                                'json': 'application/json',
                                'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                            }.get(export_format, 'application/octet-stream'),
                            key="download_export",
                            use_container_width=True
                        )

                        show_temporary_success(f"File '{filename}' generato con successo!")

                    except Exception as e:
                        show_temporary_error(f"Errore generazione file: {str(e)}")
            else:
                st.warning("⚠️ Nessun documento corrisponde ai filtri selezionati")

    except ImportError:
        st.error("❌ Modulo export_manager non disponibile")
    except Exception as e:
        st.error(f"❌ Errore esportazione: {e}")

# --- TAB: CHAT ---
with tab_chat:
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
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("L'AI sta pensando..."):
                try:
                    # Ottieni l'LLM per la chat
                    chat_llm = get_chat_llm()
                    if chat_llm is None:
                        raise ConnectionError("Chat LLM (Ollama) non disponibile.")

                    # Verifica le condizioni per usare l'archivio
                    db_path = os.path.join(DB_STORAGE_DIR, "docstore.json")
                    index_path = os.path.join(DB_STORAGE_DIR, "index_store.json")
                    all_required_files_exist = all(os.path.exists(p) for p in [db_path, index_path])
                    embed_model_available = Settings.embed_model is not None

                    # Verifica se l'utente ha richiesto un contesto specifico
                    has_specific_context = st.session_state.selected_paper or selected_category_id != "Tutte"

                    # Usa la modalità archivio solo se abbiamo tutto il necessario
                    use_archive_mode = all_required_files_exist and has_specific_context and embed_model_available

                    if has_specific_context and not all_required_files_exist:
                        st.info("⚠️ L'archivio è vuoto. Risponderò in modalità chat generica.")

                    if use_archive_mode:
                        try:
                            storage_context = StorageContext.from_defaults(persist_dir=DB_STORAGE_DIR)
                            if Settings.embed_model is None:
                                initialize_services()

                            index = load_index_from_storage(storage_context)
                            query_engine = index.as_query_engine(filters=filters, similarity_top_k=3, llm=chat_llm)
                            response = query_engine.query(prompt)
                            response_content = str(response)
                        except Exception as archive_error:
                            st.warning(f"⚠️ Non è stato possibile interrogare l'archivio. Rispondo in modalità generica.")
                            use_archive_mode = False

                    # Se non stiamo usando la modalità archivio, usa la modalità generica
                    if not use_archive_mode:
                        response = chat_llm.complete(prompt)
                        response_content = str(response)

                    # Aggiorna l'interfaccia con la risposta
                    st.markdown(response_content)
                    st.session_state.messages.append({"role": "assistant", "content": response_content})

                except Exception as e:
                    st.error(f"Si è verificato un errore imprevisto: {e}")
                    error_message = f"Errore critico: {e}"
                    st.session_state.messages.append({"role": "assistant", "content": error_message})


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
