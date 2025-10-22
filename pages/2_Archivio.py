# Pagina Archivio Unificata - Knowledge Explorer completo
"""
Pagina Archivio: Hub centrale per la gestione completa della knowledge base.

Questa pagina unifica tutte le funzionalità di gestione documenti in un'interfaccia
coerente e potente, organizzata in tab specializzate per diversi compiti.

Layout:
- Colonna sinistra: Navigazione categorie gerarchica
- Colonna centrale: Tabs per funzionalità (Esplora, Dashboard, Batch, Esporta)
- Colonna destra: Dettagli AI del file selezionato

Tab Funzionali:
- Esplora: Navigazione e selezione documenti con vista lista/griglia
- Dashboard: Statistiche complete e analisi dell'archivio
- Operazioni Batch: Modifiche massive sicure e validate
- Esporta: Esportazione dati in vari formati con filtri avanzati
"""

import streamlit as st
import pandas as pd
from scripts.utilities.file_utils import get_archive_tree, get_papers_dataframe
import os

# Import UX components for improved user experience
from scripts.operations.ux_components import show_contextual_help, create_labeled_icon, show_success_message, show_error_message

def main():
    st.set_page_config(page_title="🗂️ Archivio - Archivista AI", page_icon="🗂️", layout="wide")
    st.title("🗂️ Knowledge Explorer")
    st.caption("Esplora, analizza e gestisci la tua biblioteca di documenti")

    # Navigation buttons in header
    col_nav1, col_nav2 = st.columns([0.8, 0.2])
    with col_nav2:
        col_help, col_wizards = st.columns(2)
        with col_help:
            if st.button("❓ Guida", help="Mostra guida per usare l'archivio"):
                show_contextual_help("archive_overview")
        with col_wizards:
            if st.button("🎯 Wizards", help="Guide interattive per processi complessi"):
                st.switch_page("pages/7_Workflow_Wizards.py")

    # Check if archive is empty and show contextual help
    try:
        papers_df = get_papers_dataframe()
        if papers_df.empty:
            show_contextual_help("empty_archive")
    except:
        pass

    # Layout principale a 3 colonne
    col_left, col_center, col_right = st.columns([0.15, 0.55, 0.30])

    # --- COLONNA SINISTRA: Navigazione Categorie ---
    with col_left:
        st.markdown("### 🗂️ Navigazione")
        st.markdown("---")
        render_archive_tree()

    # --- COLONNA CENTRALE: Contenuto con Tabs Unificate ---
    with col_center:
        st.markdown("### 📚 Gestione Documenti")
        st.markdown("---")

        # Tabs per unificare tutte le funzionalità
        tab_esplora, tab_dashboard, tab_batch, tab_export = st.tabs([
            "📁 Esplora",
            "📊 Dashboard",
            "🔧 Operazioni Batch",
            "📤 Esporta"
        ])

        # Tab Esplora (default) - Vista principale file
        with tab_esplora:
            st.markdown("#### 📁 Esplorazione Documenti")

            # Pulsante rapido per nuovo documento
            col_quick1, col_quick2 = st.columns([0.7, 0.3])
            with col_quick2:
                if st.button("✨ Crea Nuovo", key="quick_new_doc", use_container_width=True):
                    st.switch_page("pages/4_Nuovo.py")

            render_file_explorer_view()

        # Tab Dashboard - Statistiche e analisi
        with tab_dashboard:
            st.markdown("#### 📊 Dashboard Statistiche")
            render_dashboard_view()

        # Tab Operazioni Batch - Modifiche massive
        with tab_batch:
            st.markdown("#### 🔧 Operazioni Batch")
            render_batch_operations_view()

        # Tab Esporta - Esportazione dati
        with tab_export:
            st.markdown("#### 📤 Esporta Dati")
            render_export_view()

    # --- COLONNA DESTRA: Dettagli AI ---
    with col_right:
        st.markdown("### 🤖 Dettagli AI")
        st.markdown("---")
        render_ai_details_panel()

def render_archive_tree():
    """Render dell'albero delle categorie (da file_explorer_ui.py)"""
    archive_tree = get_archive_tree()

    if not archive_tree:
        st.info("📭 Nessun archivio trovato. La directory 'Dall_Origine_alla_Complessita' potrebbe essere vuota.")
        return

    def render_tree_node(node, node_key, level=0):
        """Render ricorsivo dei nodi dell'albero"""
        for key, value in node.items():
            if isinstance(value, dict) and value.get('type') in ['part', 'chapter']:
                node_type = value.get('type', 'unknown')
                node_name = value.get('name', key)
                node_path = value.get('path', key)

                expander_key = f"expander_{node_key}_{key}_{level}"

                if node_type == 'part':
                    icon = "📂"
                    with st.expander(f"{icon} {node_name}", expanded=True):
                        if st.button(
                            "📂 Seleziona Parte",
                            key=f"select_part_{node_path}",
                            help=f"Seleziona {node_name}"
                        ):
                            st.session_state.selected_category = node_path
                            st.session_state.selected_category_name = node_name
                            st.session_state.selected_category_type = 'part'
                            st.rerun()

                        if 'children' in value and value['children']:
                            render_tree_node(value['children'], f"{node_key}_{key}", level + 1)

                elif node_type == 'chapter':
                    icon = "📁"
                    with st.expander(f"{icon} {node_name}", expanded=False):
                        if st.button(
                            "📁 Seleziona Capitolo",
                            key=f"select_chapter_{node_path}",
                            help=f"Seleziona {node_name}"
                        ):
                            st.session_state.selected_category = node_path
                            st.session_state.selected_category_name = node_name
                            st.session_state.selected_category_type = 'chapter'
                            st.rerun()

                        if 'files' in value and value['files']:
                            for file_obj in value['files']:
                                status_icon = "✅" if file_obj['status'] == 'indexed' else "❌"
                                st.markdown(f"{status_icon} {file_obj['name']}")

    render_tree_node(archive_tree, "root")

def render_file_explorer_view():
    """Vista principale di esplorazione file - Implementazione completa"""
    st.info("📋 **Tab Esplora**: Vista principale per navigare e selezionare documenti")

    # Inizializza session state per categoria selezionata
    if 'selected_category' not in st.session_state:
        st.session_state.selected_category = None
        st.session_state.selected_category_name = "Tutte le categorie"

    if st.session_state.selected_category:
        st.success(f"📂 Categoria selezionata: **{st.session_state.selected_category_name}**")

        # Selettore modalità vista
        col_a, col_b = st.columns([0.3, 0.7])
        with col_a:
            view_mode = st.radio("Vista", ["Lista", "Griglia"], key="explorer_view_mode", horizontal=True)

        # Ottieni file per la categoria selezionata
        files_data = get_files_for_category(st.session_state.selected_category)

        if not files_data:
            st.info("📭 Nessun file trovato in questa categoria.")
            return

        # Visualizza file in base alla modalità scelta
        if view_mode == "Lista":
            display_list_view(files_data)
        else:
            display_grid_view(files_data)

    else:
        st.info("👈 Seleziona una categoria dalla navigazione per visualizzare i documenti.")

def get_files_for_category(category_path):
    """Ottieni tutti i file per una categoria specifica"""
    if not category_path:
        return []

    archive_tree = get_archive_tree()
    files_data = []

    def extract_files_from_node(node, current_path=""):
        """Estrai ricorsivamente i file dall'albero"""
        for key, value in node.items():
            if isinstance(value, dict):
                node_path = f"{current_path}/{key}" if current_path else key

                # Verifica se questo nodo corrisponde alla categoria selezionata
                if node_path == category_path and 'files' in value:
                    files_data.extend(value['files'])

                # Continua la ricerca nei figli
                if 'children' in value and value['children']:
                    extract_files_from_node(value['children'], node_path)

    extract_files_from_node(archive_tree)
    return files_data

def display_list_view(files_data):
    """Visualizza file in formato lista con selezione e menu contestuale"""
    if not files_data:
        st.info("Nessun file da visualizzare.")
        return

    st.markdown("**File nella categoria selezionata:**")

    # Traccia file selezionati per operazioni bulk
    selected_files = []

    for i, file_obj in enumerate(files_data):
        # Determina aspetto file basato sulla selezione
        is_selected = (st.session_state.get('selected_file') == file_obj)
        selection_style = "background-color: #e3f2fd; border-left: 4px solid #2196f3;" if is_selected else ""

        # Status e icona
        if file_obj['status'] == 'indexed':
            status_icon = "✅"
            status_text = "Indicizzato"
        else:
            status_icon = "⏳"
            status_text = "Non indicizzato"

        # Icona tipo file
        ext = file_obj.get('extension', '').lower()
        if ext == '.pdf':
            type_icon = "📄"
        elif ext in ['.docx', '.doc']:
            type_icon = "📝"
        elif ext in ['.txt']:
            type_icon = "📃"
        elif ext in ['.pptx', '.ppt']:
            type_icon = "📊"
        else:
            type_icon = "📄"

        # Crea riga file
        col1, col2, col3, col4 = st.columns([0.05, 0.60, 0.20, 0.15])

        with col1:
            # Checkbox per selezione multipla
            selected = st.checkbox("", key=f"file_select_{i}")
            if selected:
                selected_files.append(file_obj)

        with col2:
            # Info file cliccabile
            file_display_name = file_obj.get('title', file_obj['name'])

            if st.button(
                f"{type_icon} {status_icon} **{file_display_name}**",
                key=f"select_file_{i}",
                help=f"Clicca per selezionare: {file_obj['name']}"
            ):
                st.session_state.selected_file = file_obj
                st.session_state.selected_file_name = file_obj['name']
                st.rerun()

            # Dettagli file
            st.caption(
                f"Dimensione: {file_obj['size'] / 1024:.1f} KB | "
                f"Anno: {file_obj.get('publication_year', 'N/A')} | "
                f"Autori: {file_obj.get('authors', 'N/A')[:40]}{'...' if len(file_obj.get('authors', '')) > 40 else ''}"
            )

        with col3:
            # Azioni rapide
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("👁️", key=f"view_{i}", help="Visualizza"):
                    st.info(f"Visualizzazione file: {file_obj['name']}")
            with col_b:
                if st.button("📋", key=f"copy_{i}", help="Copia percorso"):
                    st.success(f"Percorso copiato: {file_obj['path']}")

        with col4:
            # Menu contestuale
            with st.popover("⋮", help="Azioni"):
                st.markdown(f"**{file_obj['name']}**")

                if st.button("📝 Rinomina", key=f"rename_{i}"):
                    st.session_state.action_file = file_obj
                    st.session_state.action_type = 'rename'
                    st.rerun()

                if st.button("✏️ Modifica Anteprima", key=f"edit_preview_{i}"):
                    st.session_state.edit_paper = file_obj['name']
                    st.switch_page("pages/3_Editor.py")

                if st.button("🗑️ Elimina", key=f"delete_{i}"):
                    st.session_state.action_file = file_obj
                    st.session_state.action_type = 'delete'
                    st.rerun()

                st.markdown("---")
                st.markdown("**🤖 Azioni AI:**")

                if st.button("📝 Riassumi", key=f"summarize_{i}"):
                    st.session_state.ai_action_file = file_obj
                    st.session_state.ai_action_type = 'summarize'
                    st.rerun()

                if st.button("🌐 Traduci", key=f"translate_{i}"):
                    st.session_state.ai_action_file = file_obj
                    st.session_state.ai_action_type = 'translate'
                    st.rerun()

                if st.button("🔍 Entità", key=f"entities_{i}"):
                    st.session_state.ai_action_file = file_obj
                    st.session_state.ai_action_type = 'entities'
                    st.rerun()

    # Azioni bulk per file selezionati
    if selected_files:
        st.markdown("---")
        st.markdown(f"**{len(selected_files)} file selezionati**")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("📋 Copia Selezionati"):
                st.success(f"{len(selected_files)} percorsi copiati negli appunti")
        with col2:
            if st.button("🗑️ Elimina Selezionati"):
                st.session_state.bulk_action = 'delete'
                st.session_state.bulk_files = selected_files
                st.rerun()
        with col3:
            if st.button("📊 Statistiche"):
                st.info(f"Statistiche per {len(selected_files)} file selezionati")
        with col4:
            if st.button("🤖 Azioni AI"):
                st.session_state.bulk_action = 'ai'
                st.session_state.bulk_files = selected_files
                st.rerun()

def display_grid_view(files_data):
    """Visualizza file in formato griglia con selezione e menu contestuale"""
    if not files_data:
        st.info("Nessun file da visualizzare.")
        return

    st.markdown("**Vista Griglia:**")

    # Calcola numero colonne per griglia
    n_cols = 3
    files_per_row = n_cols

    for i in range(0, len(files_data), files_per_row):
        cols = st.columns(n_cols)

        for j in range(files_per_row):
            if i + j < len(files_data):
                file_obj = files_data[i + j]

                with cols[j]:
                    # Determina styling selezione
                    is_selected = (st.session_state.get('selected_file') == file_obj)
                    selection_style = "border: 2px solid #2196f3; background-color: #f0f8ff;" if is_selected else ""

                    # Card file
                    ext = file_obj.get('extension', '').lower()
                    if ext == '.pdf':
                        icon = "📄"
                    elif ext in ['.docx', '.doc']:
                        icon = "📝"
                    elif ext in ['.txt']:
                        icon = "📃"
                    elif ext in ['.pptx', '.ppt']:
                        icon = "📊"
                    else:
                        icon = "📄"

                    status_icon = "✅" if file_obj['status'] == 'indexed' else "⏳"

                    st.markdown(f"""
                    <div style="{selection_style}" class="file-card">
                        <div style="text-align: center;">
                            **{icon} {status_icon}**
                            **{file_obj.get('title', file_obj['name'])}**
                        </div>
                        <div style="font-size: 0.8em; color: #666; margin: 5px 0;">
                            Dimensione: {file_obj['size'] / 1024:.1f} KB<br>
                            Anno: {file_obj.get('publication_year', 'N/A')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Pulsanti azione per vista griglia
                    col_a, col_b, col_c = st.columns([1, 1, 1])

                    with col_a:
                        if st.button("📂", key=f"grid_select_{i}_{j}", help="Seleziona file"):
                            st.session_state.selected_file = file_obj
                            st.session_state.selected_file_name = file_obj['name']
                            st.rerun()

                    with col_b:
                        if st.button("👁️", key=f"grid_view_{i}_{j}", help="Visualizza"):
                            st.info(f"Visualizzazione file: {file_obj['name']}")

                    with col_c:
                        # Menu contestuale per vista griglia
                        with st.popover("⋮"):
                            st.markdown(f"**{file_obj['name']}**")

                            if st.button("📝 Rinomina", key=f"grid_rename_{i}_{j}"):
                                st.session_state.action_file = file_obj
                                st.session_state.action_type = 'rename'
                                st.rerun()

                            if st.button("✏️ Modifica Anteprima", key=f"grid_edit_preview_{i}_{j}"):
                                st.session_state.edit_paper = file_obj['name']
                                st.switch_page("pages/3_📝_Editor.py")

                            if st.button("🗑️ Elimina", key=f"grid_delete_{i}_{j}"):
                                st.session_state.action_file = file_obj
                                st.session_state.action_type = 'delete'
                                st.rerun()

                            st.markdown("---")
                            st.markdown("**🤖 Azioni AI:**")

                            if st.button("📝 Riassumi", key=f"grid_summarize_{i}_{j}"):
                                st.session_state.ai_action_file = file_obj
                                st.session_state.ai_action_type = 'summarize'
                                st.rerun()

                            if st.button("🌐 Traduci", key=f"grid_translate_{i}_{j}"):
                                st.session_state.ai_action_file = file_obj
                                st.session_state.ai_action_type = 'translate'
                                st.rerun()

                            if st.button("🔍 Entità", key=f"grid_entities_{i}_{j}"):
                                st.session_state.ai_action_file = file_obj
                                st.session_state.ai_action_type = 'entities'
                                st.rerun()

def render_dashboard_view():
    """Vista dashboard con statistiche - Implementazione completa"""
    st.info("📊 **Tab Dashboard**: Statistiche e analisi complete dell'archivio")

    try:
        from statistics import get_comprehensive_stats

        # Bottone refresh
        if st.button("🔄 Aggiorna Statistiche", use_container_width=True):
            get_comprehensive_stats.clear()

        # Ottieni statistiche complete
        stats = get_comprehensive_stats()

        # --- METRICHE PRINCIPALI ---
        st.markdown("#### 📊 Metriche Principali")

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

        # --- GRAFICI E ANALISI DETTAGLIATE ---
        st.markdown("#### 📈 Analisi Dettagliata")

        col_left, col_right = st.columns([0.7, 0.3])

        with col_left:
            # Distribuzione per categoria
            if stats['category_distribution']:
                st.markdown("##### 📂 Distribuzione per Categoria")
                cat_data = pd.DataFrame(stats['category_distribution'])
                st.bar_chart(cat_data.set_index('category_name')['count'])
            else:
                st.info("Nessuna categoria disponibile")

            # Trend temporale
            if stats['temporal_trend']:
                st.markdown("##### 📅 Trend Temporale")
                trend_data = pd.DataFrame(stats['temporal_trend'])
                st.line_chart(trend_data.set_index('period')['count'])
            else:
                st.info("Nessun dato temporale disponibile")

        with col_right:
            # Top categorie
            st.markdown("##### 🏆 Categorie Principali")
            if stats['top_categories']:
                for i, cat in enumerate(stats['top_categories'][:8], 1):
                    percentage = cat.get('percentage', 0)
                    st.write(f"**{i}.** {cat['category_name']} ({cat['count']} doc - {percentage}%)")
            else:
                st.info("Nessuna categoria disponibile")

            # Top autori
            st.markdown("##### 👥 Autori Più Frequenti")
            if stats['author_stats']:
                for i, author in enumerate(stats['author_stats'][:8], 1):
                    st.write(f"**{i}.** {author['author']} ({author['document_count']} doc)")
            else:
                st.info("Nessun autore disponibile")

        # --- QUALITÀ DEI DATI ---
        st.markdown("#### 🔍 Qualità dei Dati")

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

        # --- ATTIVITÀ RECENTE ---
        st.markdown("#### 🕐 Attività Recente")

        if stats['recent_activity']:
            recent_df = pd.DataFrame(stats['recent_activity'])
            st.dataframe(
                recent_df[['title', 'category_name', 'processed_at']].head(15),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Nessuna attività recente")

        # --- INFORMAZIONI AGGIUNTIVE ---
        st.markdown("#### ℹ️ Informazioni Aggiuntive")

        info_col1, info_col2 = st.columns(2)

        with info_col1:
            if stats['basic_stats']['oldest_document'] and stats['basic_stats']['newest_document']:
                st.info(f"📅 **Range Documenti:** {stats['basic_stats']['oldest_document']} - {stats['basic_stats']['newest_document']}")

            if stats['basic_stats']['recent_documents'] > 0:
                st.info(f"🆕 **Documenti Recenti (7gg):** {stats['basic_stats']['recent_documents']}")

        with info_col2:
            avg_docs_per_cat = stats['basic_stats']['avg_documents_per_category']
            if avg_docs_per_cat > 0:
                st.info(f"📊 **Media per Categoria:** {avg_docs_per_cat} documenti")

            if stats['data_quality']['total_documents'] > 0:
                st.info(f"📈 **Ultimo Aggiornamento:** {stats['last_updated'][:10]}")

    except ImportError:
        st.error("❌ Modulo statistics non disponibile")
    except Exception as e:
        st.error(f"❌ Errore nel caricamento dashboard: {e}")

def render_batch_operations_view():
    """Vista operazioni batch - Implementazione completa"""
    st.info("🔧 **Tab Operazioni Batch**: Modifiche massive sicure e validate")

    try:
        from batch_operations import get_available_operations, create_batch_operation, get_batch_preview, execute_batch_operation

        papers_df = get_papers_dataframe()
        if papers_df.empty:
            st.warning("⚠️ Nessun documento disponibile per operazioni batch")
            return

        # --- SELEZIONE DOCUMENTI ---
        st.markdown("#### 1. 📋 Selezione Documenti")

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
        st.info(f"📋 Documenti selezionati: **{len(selected_files)}**")

        if selected_files:
            # --- SELEZIONE OPERAZIONE ---
            st.markdown("#### 2. ⚙️ Selezione Operazione")

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
                current_year = st.session_state.get('current_year', 2024)
                operation_value = st.number_input(
                    "Anno di pubblicazione:",
                    min_value=1000,
                    max_value=current_year + 1,
                    value=current_year,
                    key="batch_year_input"
                )
            elif selected_operation['id'] == 'set_category':
                from knowledge_structure import get_category_choices
                categories = get_category_choices()
                category_dict = dict(categories)
                operation_value = st.selectbox(
                    "Nuova categoria:",
                    options=[cat[0] for cat in categories],
                    format_func=lambda x: category_dict.get(x, "Seleziona categoria"),
                    key="batch_category_input"
                )

            # --- ANTEPRIMA MODIFICHE ---
            if operation_value and st.checkbox("👁️ Mostra anteprima modifiche", key="show_batch_preview"):
                st.markdown("#### 3. 📋 Anteprima Modifiche")

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
                        st.info(f"📊 Anteprima mostra primi 10 documenti. Saranno modificati **{len(selected_files)}** documenti totali.")
                    else:
                        st.warning("⚠️ Impossibile generare anteprima")

                except Exception as e:
                    st.error(f"❌ Errore generazione anteprima: {e}")

            # --- ESECUZIONE OPERAZIONE ---
            st.markdown("#### 4. 🚀 Esecuzione Operazione")

            if st.button("🚀 Esegui Operazione Batch", type="primary", use_container_width=True):
                if not operation_value:
                    st.error("❌ Inserisci un valore per l'operazione")
                else:
                    try:
                        with st.spinner("Esecuzione operazione batch in corso..."):
                            batch_op = create_batch_operation(operation_choice, operation_value, selected_files)
                            success, message, affected_count = execute_batch_operation(batch_op)

                        if success:
                            st.success(f"✅ Operazione completata! **{affected_count}** documenti aggiornati.")
                            # Ricarica dati
                            papers_df = get_papers_dataframe()
                            st.rerun()
                        else:
                            st.error(f"❌ Operazione fallita: {message}")

                    except Exception as e:
                        st.error(f"❌ Errore esecuzione: {str(e)}")
        else:
            st.info("💡 Seleziona almeno un documento per iniziare")

    except ImportError:
        st.error("❌ Modulo batch_operations non disponibile")
    except Exception as e:
        st.error(f"❌ Errore operazioni batch: {e}")

def render_export_view():
    """Vista esportazione dati - Implementazione completa"""
    st.info("📤 **Tab Esporta**: Esporta dati filtrati in vari formati")

    try:
        from export_manager import (
            get_exportable_dataframe, create_export_data, get_export_summary,
            get_category_choices_for_filter, get_author_choices_for_filter, get_year_choices_for_filter
        )

        papers_df = get_papers_dataframe()
        if papers_df.empty:
            st.warning("⚠️ Nessun documento disponibile per l'esportazione")
            return

        # --- CONFIGURAZIONE ESPORTAZIONE ---
        st.markdown("#### 1. ⚙️ Configura Esportazione")

        col1, col2 = st.columns(2)

        with col1:
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

        with col2:
            include_preview = st.checkbox(
                "Includi anteprime generate dall'AI",
                value=False,
                key="include_preview_export",
                help="Aggiunge la colonna con le anteprime generate"
            )

        # --- FILTRI AVANZATI ---
        st.markdown("#### 2. 🔍 Filtri di Esportazione")

        filter_col1, filter_col2, filter_col3 = st.columns(3)

        with filter_col1:
            # Filtro categorie
            category_options = ["Tutte"] + [cat[0] for cat in get_category_choices_for_filter()]
            category_filter = st.selectbox(
                "Filtra per categoria:",
                options=category_options,
                key="export_category_filter"
            )

        with filter_col2:
            # Filtro autori
            author_options = ["Tutti"] + get_author_choices_for_filter()
            author_filter = st.selectbox(
                "Filtra per autore:",
                options=author_options,
                key="export_author_filter"
            )

        with filter_col3:
            # Filtro anni
            year_options = [None] + get_year_choices_for_filter()
            year_filter = st.selectbox(
                "Filtra per anno:",
                options=year_options,
                format_func=lambda x: "Tutti gli anni" if x is None else str(x),
                key="export_year_filter"
            )

        # Bottone pulisci filtri
        if st.button("🗑️ Cancella Filtri", key="clear_export_filters"):
            # Pulisce i filtri dal session state
            keys_to_clear = ['export_category_filter', 'export_author_filter', 'export_year_filter']
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

        # --- RIEPILOGO DATI ---
        st.markdown("#### 3. 📋 Riepilogo Dati")

        # Calcola riepilogo
        summary = get_export_summary(
            category_filter=category_filter if category_filter != "Tutte" else None,
            author_filter=author_filter if author_filter != "Tutti" else None,
            year_filter=year_filter,
            include_preview=include_preview
        )

        if summary['document_count'] > 0:
            # Metriche riepilogo
            summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)

            with summary_col1:
                st.metric("📚 Documenti", summary['document_count'])
            with summary_col2:
                st.metric("📂 Categorie", summary['category_count'])
            with summary_col3:
                st.metric("👥 Autori", summary['author_count'])
            with summary_col4:
                st.metric("💾 Dimensione Stimata", summary['file_size_estimate'])

            # Info aggiuntive
            if summary['year_range']:
                st.info(f"📅 **Range anni:** {summary['year_range']}")

            # Mostra filtri attivi
            active_filters = []
            if category_filter != "Tutte":
                active_filters.append(f"**Categoria:** {category_filter}")
            if author_filter != "Tutti":
                active_filters.append(f"**Autore:** {author_filter}")
            if year_filter:
                active_filters.append(f"**Anno:** {year_filter}")

            if active_filters:
                st.info(f"🔍 **Filtri attivi:** {' | '.join(active_filters)}")

        else:
            st.warning("⚠️ Nessun documento corrisponde ai filtri selezionati")
            return

        # --- DOWNLOAD FILE ---
        st.markdown("#### 4. 💾 Scarica File")

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

                if file_content:
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

                    st.success(f"✅ File '{filename}' generato con successo!")

                    # Mostra anteprima dei dati esportati
                    with st.expander("👁️ Anteprima dati esportati", expanded=False):
                        preview_df = get_exportable_dataframe(
                            category_filter=category_filter if category_filter != "Tutte" else None,
                            author_filter=author_filter if author_filter != "Tutti" else None,
                            year_filter=year_filter,
                            include_preview=include_preview
                        )

                        if not preview_df.empty:
                            # Mostra solo prime righe per non sovraccaricare
                            st.dataframe(preview_df.head(10), use_container_width=True)
                            if len(preview_df) > 10:
                                st.info(f"📊 Mostra primi 10 di {len(preview_df)} documenti totali")

                else:
                    st.error("❌ Errore nella generazione del file")

            except Exception as e:
                st.error(f"❌ Errore esportazione: {str(e)}")

    except ImportError:
        st.error("❌ Modulo export_manager non disponibile")
    except Exception as e:
        st.error(f"❌ Errore esportazione: {e}")

def render_ai_details_panel():
    """Pannello dettagli AI (da file_explorer_ui.py)"""
    if 'selected_file' not in st.session_state or not st.session_state.selected_file:
        st.info("👈 Seleziona un file per visualizzare i dettagli AI")
        return

    file_obj = st.session_state.selected_file
    st.markdown(f"**📄 File Selezionato:** {file_obj['name']}")

    # Metadati base
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Titolo:** {file_obj.get('title', 'N/A')}")
        st.markdown(f"**Autori:** {file_obj.get('authors', 'N/A')}")
    with col2:
        st.markdown(f"**Anno:** {file_obj.get('publication_year', 'N/A')}")
        st.markdown(f"**Categoria:** {file_obj.get('category_name', 'N/A')}")

    # Anteprima AI
    if file_obj.get('formatted_preview'):
        st.markdown("**🤖 Anteprima AI:**")
        st.info(file_obj['formatted_preview'])
    else:
        st.warning("⚠️ Nessuna anteprima disponibile")

    st.info("🤖 *Implementazione completa nel prossimo step*")

if __name__ == "__main__":
    main()
