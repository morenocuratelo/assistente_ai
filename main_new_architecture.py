#!/usr/bin/env python3
"""
Archivista AI - New Navigation Architecture
Modern sidebar-based navigation with toggle between Chat View and File Explorer
"""

import streamlit as st
import os
import time
import json
import pandas as pd
from datetime import datetime
from llama_index.core import Settings, StorageContext, load_index_from_storage
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter

from config import initialize_services, get_chat_llm
from file_utils import setup_database, get_papers_dataframe, update_paper_metadata, delete_paper
import knowledge_structure

# --- CONFIGURATION ---
DB_STORAGE_DIR = "db_memoria"
DOCS_TO_PROCESS_DIR = "documenti_da_processare"
ARCHIVISTA_STATUS_FILE = os.path.join(DB_STORAGE_DIR, "archivista_status.json")

# --- INITIALIZATION ---
st.set_page_config(page_title="Archivista AI v2.3", layout="wide")

# Ensure required directories exist
os.makedirs(DB_STORAGE_DIR, exist_ok=True)
os.makedirs(DOCS_TO_PROCESS_DIR, exist_ok=True)

# Initialize session state
if 'initialized' not in st.session_state:
    initialize_services()
    setup_database()

    st.session_state.initialized = True
    st.session_state.log_messages = []
    st.session_state.auto_scan_completed = False
    st.session_state.messages = [{"role": "assistant", "content": "Ciao! Sono Archivista AI. Puoi trascinare i tuoi documenti nella barra laterale per iniziare."}]
    st.session_state.selected_paper = None
    st.session_state.current_view = 'chat'  # New navigation state

# --- UTILITY FUNCTIONS ---
def get_archivista_status():
    """Get current processing status."""
    try:
        if not os.path.exists(DB_STORAGE_DIR):
            return {"status": "Inattivo", "file": None, "timestamp": datetime.now().isoformat()}
        with open(ARCHIVISTA_STATUS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"status": "Inattivo", "file": None, "timestamp": datetime.now().isoformat()}

def add_log_message(message):
    """Add message to log."""
    current_time = datetime.now().strftime("%H:%M:%S")
    st.session_state.log_messages.insert(0, f"[{current_time}] {message}")
    if len(st.session_state.log_messages) > 5:
        st.session_state.log_messages.pop()

def show_temporary_success(message, duration=3):
    """Show temporary success message."""
    st.session_state.temp_notification = {
        'message': message,
        'type': 'success',
        'timestamp': time.time(),
        'duration': duration
    }

def show_temporary_error(message, duration=5):
    """Show temporary error message."""
    st.session_state.temp_notification = {
        'message': message,
        'type': 'error',
        'timestamp': time.time(),
        'duration': duration
    }

def display_temporary_notifications():
    """Display temporary notifications if present."""
    if 'temp_notification' in st.session_state:
        notification = st.session_state.temp_notification
        elapsed = time.time() - notification['timestamp']

        if elapsed < notification['duration']:
            if notification['type'] == 'success':
                st.success(f"✅ {notification['message']}")
            elif notification['type'] == 'error':
                st.error(f"❌ {notification['message']}")
        else:
            del st.session_state.temp_notification

def scan_and_process_documents(files_to_process=None):
    """Scan and process documents with Celery."""
    try:
        from archivista_processing import process_document_task

        if files_to_process is None:
            supported_extensions = ['.pdf', '.docx', '.rtf', '.html', '.htm', '.txt', '.pptx']
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
                    st.error("Errore di connessione con il sistema di code.")
                    return

        if sent_tasks > 0:
            add_log_message(f"{sent_tasks} documenti inviati al worker.")
            st.toast("✅ Elaborazione avviata in background!")

    except Exception as e:
        add_log_message(f"Errore scansione: {e}")
        st.error(f"Errore critico durante la scansione: {e}")

def get_original_file_path(row):
    """Find the original file path."""
    try:
        category_id = row.get('category_id', '')
        file_name = row.get('file_name', '')

        if category_id and file_name:
            categorized_path = os.path.join("Dall_Origine_alla_Complessita", *category_id.split('/'), file_name)
            if os.path.exists(categorized_path):
                return categorized_path

        fallback_path = os.path.join(DOCS_TO_PROCESS_DIR, file_name)
        if os.path.exists(fallback_path):
            return fallback_path

        return None
    except Exception as e:
        st.error(f"Errore nella ricerca del file: {e}")
        return None

# --- SIDEBAR NAVIGATION ---
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
            type=['pdf', 'docx', 'txt', 'rtf', 'html', 'htm', 'pptx'],
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
                for msg in st.session_state.log_messages[:3]:
                    st.text(msg)

# --- VIEW RENDERERS ---
def render_chat_view():
    """Render the optimized chat view."""
    st.markdown("# 💬 Chat con l'Archivio")
    st.caption("Fai domande sui tuoi documenti e ottieni risposte intelligenti")

    # Chat filters
    st.markdown("### 🔧 Filtri Chat")

    col1, col2, col3 = st.columns([0.3, 0.3, 0.4])

    with col1:
        category_choices = knowledge_structure.get_category_choices()
        selected_category_id = st.selectbox(
            "Categoria:",
            options=["Tutte"] + [opt[0] for opt in category_choices],
            format_func=lambda x: dict(category_choices).get(x, "Tutte le categorie") if x != "Tutte" else "Tutte le categorie",
            key="chat_category_filter",
            label_visibility="collapsed"
        )

    with col2:
        papers_df = get_papers_dataframe()
        selected_doc_title = st.selectbox(
            "Documento:",
            options=["Tutti"] + papers_df['file_name'].tolist(),
            format_func=lambda x: "Tutti i documenti" if x == "Tutti" else next((row.get('title', row['file_name']) for _, row in papers_df.iterrows() if row['file_name'] == x), x),
            key="chat_document_filter",
            label_visibility="collapsed"
        )

    with col3:
        if st.button("🗑️ Cancella Filtri", use_container_width=True):
            if 'chat_category_filter' in st.session_state:
                del st.session_state.chat_category_filter
            if 'chat_document_filter' in st.session_state:
                del st.session_state.chat_document_filter
            st.rerun()

    # Show current context and setup variables
    selected_file_name = None
    if selected_doc_title != "Tutti i documenti":
        # Find the corresponding file_name for the selected title
        matching_rows = papers_df[papers_df['file_name'] == selected_doc_title]
        if not matching_rows.empty:
            selected_file_name = matching_rows.iloc[0]['file_name']
            display_title = matching_rows.iloc[0].get('title', selected_file_name)
            st.info(f"💬 Contesto attivo: **{display_title}**")
        else:
            st.info("💬 Contesto attivo: **Tutti i documenti**")
    elif selected_category_id != "Tutte":
        st.info(f"💬 Contesto attivo: Categoria **{dict(category_choices).get(selected_category_id)}**")
    else:
        st.info("💬 Contesto attivo: **Tutti i documenti**")

    st.divider()

    # Chat messages
    st.markdown("### 💭 Conversazione")

    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Fai una domanda sui tuoi documenti..."):
        st.session_state.messages.append({"role": "user", "content": prompt})

        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)

        # Generate response
        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner("🤔 L'AI sta pensando..."):
                    try:
                        # Setup filters
                        filters = None
                        if selected_doc_title != "Tutti i documenti":
                            filters = MetadataFilters(filters=[ExactMatchFilter(key="file_name", value=selected_file_name)])
                        elif selected_category_id != "Tutte":
                            filters = MetadataFilters(filters=[ExactMatchFilter(key="category_id", value=selected_category_id)])

                        # Get response
                        chat_llm = get_chat_llm()
                        if chat_llm is None:
                            raise ConnectionError("Chat LLM non disponibile.")

                        # Check archive availability
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

                        st.markdown(response_content)
                        st.session_state.messages.append({"role": "assistant", "content": response_content})

                    except Exception as e:
                        st.error(f"❌ Errore: {e}")
                        error_message = f"Si è verificato un errore: {e}"
                        st.session_state.messages.append({"role": "assistant", "content": error_message})

def render_archive_view():
    """Render the archive view - ONLY File Explorer."""
    st.markdown("# 🗂️ Knowledge Explorer")

    # Only File Explorer - no toggle here
    try:
        from file_explorer_ui import create_three_column_layout, handle_file_actions
        handle_file_actions()
        create_three_column_layout()
    except ImportError as e:
        st.error(f"❌ Impossibile caricare File Explorer: {e}")
        st.info("🔧 Assicurati che il modulo file_explorer_ui sia disponibile.")

def render_chat_document_selection():
    """Render chat-focused document selection interface."""
    st.markdown("### 💬 Selezione Documenti per Chat")
    st.info("📋 Usa questa vista per selezionare documenti da aggiungere al contesto della chat.")

    papers_df = get_papers_dataframe()

    if papers_df.empty:
        st.info("📭 L'archivio è vuoto. Aggiungi documenti tramite la barra laterale per iniziare.")
        return

    # Search and filters
    st.markdown("#### 🔍 Ricerca e Filtri")

    col1, col2, col3 = st.columns([0.4, 0.3, 0.3])

    with col1:
        search_query = st.text_input(
            "🔍 Cerca documenti:",
            placeholder="Titolo, autore, contenuto...",
            key="chat_archive_search"
        )

    with col2:
        quick_category = st.selectbox(
            "📂 Categoria rapida:",
            ["Tutte"] + [cat[0] for cat in knowledge_structure.get_category_choices()],
            key="quick_category_filter"
        )

    with col3:
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
        filtered_df = filtered_df.sort_values(sort_columns[sort_option], na_position='last')

    # Display results
    if filtered_df.empty:
        st.warning("⚠️ Nessun documento trovato per i filtri selezionati.")
        if st.button("🗑️ Cancella Filtri", key="clear_chat_filters"):
            if 'chat_archive_search' in st.session_state:
                del st.session_state.chat_archive_search
            if 'quick_category_filter' in st.session_state:
                del st.session_state.quick_category_filter
            st.rerun()
    else:
        st.success(f"✅ {len(filtered_df)} documenti trovati")

        # Group by category
        categories_in_results = filtered_df['category_id'].unique()

        if len(categories_in_results) > 1:
            for category_id in categories_in_results:
                category_docs = filtered_df[filtered_df['category_id'] == category_id]
                category_name = category_docs['category_name'].iloc[0] if not category_docs.empty else "Senza categoria"

                with st.expander(f"📂 {category_name} ({len(category_docs)} documenti)", expanded=True):
                    render_document_cards(category_docs)
        else:
            render_document_cards(filtered_df)

def render_document_cards(documents_df):
    """Render document cards for chat selection."""
    docs_per_row = 3
    total_docs = len(documents_df)

    for i in range(0, total_docs, docs_per_row):
        cols = st.columns(docs_per_row)

        for j in range(docs_per_row):
            if i + j < total_docs:
                doc = documents_df.iloc[i + j]

                with cols[j]:
                    with st.container():
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

                        # Preview snippet
                        if doc.get('formatted_preview'):
                            preview = doc['formatted_preview'][:100] + "..." if len(doc['formatted_preview']) > 100 else doc['formatted_preview']
                            st.caption(f"📄 {preview}")

                        # Action buttons
                        col_a, col_b, col_c = st.columns([1, 1, 1])

                        with col_a:
                            if st.button(
                                "💬 Chat",
                                key=f"chat_context_{doc['file_name']}",
                                help="Aggiungi al contesto chat",
                                use_container_width=True
                            ):
                                st.session_state.selected_paper = doc['file_name']
                                st.success(f"✅ '{title}' aggiunto al contesto chat!")
                                st.info("💡 Vai alla Chat per iniziare la conversazione.")

                        with col_b:
                            if st.button(
                                "👁️",
                                key=f"quick_preview_{doc['file_name']}",
                                help="Anteprima rapida",
                                use_container_width=True
                            ):
                                st.session_state.quick_preview_doc = doc['file_name']
                                st.rerun()

                        with col_c:
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

def render_dashboard_view():
    """Render the dashboard view in full width."""
    st.markdown("# 📊 Dashboard Statistiche")

    try:
        from statistics import get_comprehensive_stats

        if st.button("🔄 Aggiorna Statistiche", use_container_width=True):
            get_comprehensive_stats.clear()

        stats = get_comprehensive_stats()

        # Main metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("📚 Documenti Totali", stats['basic_stats']['total_documents'])
        with col2:
            st.metric("📂 Categorie", stats['basic_stats']['total_categories'])
        with col3:
            st.metric("👥 Autori Unici", stats['basic_stats']['total_authors'])
        with col4:
            st.metric("⭐ Qualità Dati", f"{stats['data_quality']['completeness_score']}%")

        # Charts section
        st.markdown("### 📈 Analisi Dettagliata")

        col_left, col_right = st.columns([0.7, 0.3])

        with col_left:
            if stats['category_distribution']:
                st.markdown("#### 📂 Distribuzione per Categoria")
                cat_data = pd.DataFrame(stats['category_distribution'])
                st.bar_chart(cat_data.set_index('category_name')['count'])
            else:
                st.info("Nessuna categoria disponibile")

            if stats['temporal_trend']:
                st.markdown("#### 📅 Trend Temporale")
                trend_data = pd.DataFrame(stats['temporal_trend'])
                st.line_chart(trend_data.set_index('period')['count'])
            else:
                st.info("Nessun dato temporale disponibile")

        with col_right:
            st.markdown("#### 🏆 Categorie Principali")
            if stats['top_categories']:
                for i, cat in enumerate(stats['top_categories'][:8], 1):
                    percentage = cat.get('percentage', 0)
                    st.write(f"**{i}.** {cat['category_name']} ({cat['count']} doc - {percentage}%)")
            else:
                st.info("Nessuna categoria disponibile")

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
            st.metric("✅ Con Anteprima", f"{stats['data_quality']['docs_with_preview']}/{stats['data_quality']['total_documents']}")
        with quality_col2:
            st.metric("📅 Con Anno", f"{stats['data_quality']['docs_with_year']}/{stats['data_quality']['total_documents']}")
        with quality_col3:
            st.metric("👤 Con Autori", f"{stats['data_quality']['docs_with_authors']}/{stats['data_quality']['total_documents']}")
        with quality_col4:
            completeness = stats['data_quality']['completeness_score']
            if completeness >= 80:
                st.success(f"⭐ Completezza: {completeness}%")
            elif completeness >= 60:
                st.warning(f"⭐ Completezza: {completeness}%")
            else:
                st.error(f"⭐ Completezza: {completeness}%")

        # Recent activity
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

# --- MAIN APPLICATION ---
def main():
    """Main application with new navigation architecture."""

    # Render sidebar navigation
    render_navigation_sidebar()

    # Render main content based on current view
    if st.session_state.current_view == 'chat':
        render_chat_view()
    elif st.session_state.current_view == 'archive':
        render_archive_view()
    elif st.session_state.current_view == 'dashboard':
        render_dashboard_view()
    else:
        render_chat_view()  # Default fallback

    # Handle quick preview modal
    if 'quick_preview_doc' in st.session_state:
        papers_df = get_papers_dataframe()
        preview_row = papers_df[papers_df['file_name'] == st.session_state.quick_preview_doc]

        if not preview_row.empty:
            row = preview_row.iloc[0]

            st.markdown("---")
            st.subheader(f"👁️ Anteprima Rapida: {row.get('title', row['file_name'])}")

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

                if st.button("💬 Usa nel Chat", use_container_width=True):
                    st.session_state.selected_paper = row['file_name']
                    st.success("✅ Documento aggiunto al contesto chat!")
                    del st.session_state.quick_preview_doc
                    st.rerun()

                if st.button("📝 Modifica Anteprima", use_container_width=True):
                    st.session_state.edit_paper = row['file_name']
                    del st.session_state.quick_preview_doc
                    st.rerun()

            if st.button("✖️ Chiudi Anteprima", use_container_width=True):
                del st.session_state.quick_preview_doc
                st.rerun()

    # Handle file actions
    if 'action_file' in st.session_state and 'action_type' in st.session_state:
        file_obj = st.session_state.action_file
        action = st.session_state.action_type

        if action == 'rename':
            st.markdown("### 📝 Rinomina File")
            st.markdown(f"**File corrente:** {file_obj['name']}")

            current_title = file_obj.get('title', file_obj['name'])

            with st.form("rename_form"):
                new_title = st.text_input("Nuovo titolo", value=current_title)

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Salva"):
                        if new_title and new_title != current_title:
                            success = update_paper_metadata(file_obj['name'], {'title': new_title})
                            if success:
                                st.success(f"✅ File rinominato in: {new_title}")
                                del st.session_state.action_file
                                del st.session_state.action_type
                                st.rerun()
                            else:
                                st.error("❌ Errore durante la rinomina")
                        else:
                            st.warning("⚠️ Inserisci un titolo diverso")

                with col2:
                    if st.form_submit_button("❌ Annulla"):
                        del st.session_state.action_file
                        del st.session_state.action_type
                        st.rerun()

        elif action == 'delete':
            st.markdown("### 🗑️ Elimina File")
            st.markdown(f"**File da eliminare:** {file_obj['name']}")
            st.warning("⚠️ Questa azione non può essere annullata!")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Conferma Eliminazione", type="primary"):
                    success = delete_paper(file_obj['name'])
                    if success:
                        st.success(f"✅ File '{file_obj['name']}' eliminato con successo!")
                        del st.session_state.action_file
                        del st.session_state.action_type
                        st.rerun()
                    else:
                        st.error("❌ Errore durante l'eliminazione")

            with col2:
                if st.button("❌ Annulla"):
                    del st.session_state.action_file
                    del st.session_state.action_type
                    st.rerun()

    # Auto-refresh for processing status
    try:
        status_now = get_archivista_status()
        if status_now['status'] not in ["Inattivo", "Completato"] and "Errore" not in status_now['status']:
            time.sleep(3)
            st.rerun()
    except Exception:
        pass

if __name__ == "__main__":
    main()
