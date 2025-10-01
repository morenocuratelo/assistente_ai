#!/usr/bin/env python3
"""
File Explorer UI Components - Phase 2 Implementation
Three-column layout with tree navigation, file view, and AI details panel.
"""

import streamlit as st
import pandas as pd
from file_utils import get_archive_tree
import os

def create_three_column_layout():
    """Create the main three-column layout for the file explorer."""
    col1, col2, col3 = st.columns([0.15, 0.55, 0.30])

    with col1:
        st.markdown("### 🗂️ Navigazione")
        st.markdown("---")
        display_archive_tree()

    with col2:
        st.markdown("### 📁 Contenuto")
        st.markdown("---")
        display_file_view()

    with col3:
        st.markdown("### 🤖 Dettagli AI")
        st.markdown("---")
        display_ai_details_panel()

def display_archive_tree():
    """Display the archive tree using recursive expanders."""
    archive_tree = get_archive_tree()

    if not archive_tree:
        st.info("📭 Nessun archivio trovato. La directory 'Dall_Origine_alla_Complessita' potrebbe essere vuota.")
        return

    def render_tree_node(node, node_key, level=0):
        """Recursively render tree nodes with expanders."""
        for key, value in node.items():
            if isinstance(value, dict) and value.get('type') in ['part', 'chapter']:
                node_type = value.get('type', 'unknown')
                node_name = value.get('name', key)
                node_path = value.get('path', key)

                # Create unique key for this node
                expander_key = f"expander_{node_key}_{key}_{level}"

                # Icon based on type
                if node_type == 'part':
                    icon = "📂"
                    # Parts are always expanded by default
                    with st.expander(f"{icon} {node_name}", expanded=True):
                        # Add click button for part selection
                        if st.button(
                            "📂 Seleziona Parte",
                            key=f"select_part_{node_path}",
                            help=f"Seleziona {node_name}"
                        ):
                            st.session_state.selected_category = node_path
                            st.session_state.selected_category_name = node_name
                            st.session_state.selected_category_type = 'part'
                            st.rerun()

                        # Render children (chapters)
                        if 'children' in value and value['children']:
                            render_tree_node(value['children'], f"{node_key}_{key}", level + 1)

                elif node_type == 'chapter':
                    icon = "📁"
                    # Chapters start collapsed
                    with st.expander(f"{icon} {node_name}", expanded=False):
                        # Add click button for chapter selection
                        if st.button(
                            "📁 Seleziona Capitolo",
                            key=f"select_chapter_{node_path}",
                            help=f"Seleziona {node_name}"
                        ):
                            st.session_state.selected_category = node_path
                            st.session_state.selected_category_name = node_name
                            st.session_state.selected_category_type = 'chapter'
                            st.rerun()

                        # Show files in this chapter if any
                        if 'files' in value and value['files']:
                            for file_obj in value['files']:
                                status_icon = "✅" if file_obj['status'] == 'indexed' else "❌"
                                st.markdown(
                                    f"{status_icon} {file_obj['name']} ({file_obj['extension']})"
                                )

    # Render the tree
    render_tree_node(archive_tree, "root")

def display_file_view():
    """Display files and subdirectories for the selected category."""
    # Initialize session state if needed
    if 'selected_category' not in st.session_state:
        st.session_state.selected_category = None
        st.session_state.selected_category_name = "Tutte le categorie"
        st.session_state.selected_category_type = None

    # Display current selection
    if st.session_state.selected_category:
        st.markdown(f"**Categoria selezionata:** {st.session_state.selected_category_name}")
        st.markdown(f"**Path:** `{st.session_state.selected_category}`")

        # Add view mode selector
        col_a, col_b = st.columns([0.3, 0.7])
        with col_a:
            view_mode = st.radio(
                "Vista",
                ["Lista", "Griglia"],
                key="view_mode",
                horizontal=True
            )

        # Get files for selected category
        files_data = get_files_for_category(st.session_state.selected_category)

        if not files_data:
            st.info("📭 Nessun file trovato in questa categoria.")
            return

        # Display files based on view mode
        if view_mode == "Lista":
            display_list_view(files_data)
        else:
            display_grid_view(files_data)
    else:
        st.info("👈 Seleziona una categoria dalla navigazione per visualizzare i file.")

def get_files_for_category(category_path):
    """Get all files for a specific category path."""
    if not category_path:
        return []

    archive_tree = get_archive_tree()
    files_data = []

    def extract_files_from_node(node, current_path=""):
        """Recursively extract files from the tree."""
        for key, value in node.items():
            if isinstance(value, dict):
                node_path = f"{current_path}/{key}" if current_path else key

                # Check if this node matches our selected category
                if node_path == category_path and 'files' in value:
                    files_data.extend(value['files'])

                # Continue searching in children
                if 'children' in value and value['children']:
                    extract_files_from_node(value['children'], node_path)

    extract_files_from_node(archive_tree)
    return files_data

def display_list_view(files_data):
    """Display files in list view format with selection and context menu."""
    if not files_data:
        st.info("Nessun file da visualizzare.")
        return

    st.markdown("**File nella categoria selezionata:**")

    # Track selected files for bulk operations
    selected_files = []

    for i, file_obj in enumerate(files_data):
        # Determine file appearance based on selection
        is_selected = (st.session_state.get('selected_file') == file_obj)
        selection_style = "background-color: #e3f2fd; border-left: 4px solid #2196f3;" if is_selected else ""

        # Status and icon
        if file_obj['status'] == 'indexed':
            status_icon = "✅"
            status_text = "Indicizzato"
        else:
            status_icon = "⏳"
            status_text = "Non indicizzato"

        # File type icon
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

        # Create file row
        col1, col2, col3, col4 = st.columns([0.05, 0.60, 0.20, 0.15])

        with col1:
            # Checkbox for multi-selection
            selected = st.checkbox("", key=f"file_select_{i}")
            if selected:
                selected_files.append(file_obj)

        with col2:
            # Clickable file info
            file_display_name = file_obj.get('title', file_obj['name'])

            if st.button(
                f"{type_icon} {status_icon} **{file_display_name}**",
                key=f"select_file_{i}",
                help=f"Clicca per selezionare: {file_obj['name']}"
            ):
                st.session_state.selected_file = file_obj
                st.session_state.selected_file_name = file_obj['name']
                st.rerun()

            # File details
            st.caption(
                f"Dimensione: {file_obj['size'] / 1024:.1f} KB | "
                f"Anno: {file_obj.get('publication_year', 'N/A')} | "
                f"Autori: {file_obj.get('authors', 'N/A')[:40]}{'...' if len(file_obj.get('authors', '')) > 40 else ''}"
            )

        with col3:
            # Quick actions
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("👁️", key=f"view_{i}", help="Visualizza"):
                    st.info(f"Visualizzazione file: {file_obj['name']}")
            with col_b:
                if st.button("📋", key=f"copy_{i}", help="Copia percorso"):
                    st.success(f"Percorso copiato: {file_obj['path']}")

        with col4:
            # Context menu
            with st.popover("⋮", help="Azioni"):
                st.markdown(f"**{file_obj['name']}**")

                if st.button("📝 Rinomina", key=f"rename_{i}"):
                    st.session_state.action_file = file_obj
                    st.session_state.action_type = 'rename'
                    st.rerun()

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

    # Bulk actions for selected files
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
    """Display files in grid view format with selection and context menu."""
    if not files_data:
        st.info("Nessun file da visualizzare.")
        return

    st.markdown("**Vista Griglia:**")

    # Calculate number of columns for grid
    n_cols = 3
    files_per_row = n_cols

    for i in range(0, len(files_data), files_per_row):
        cols = st.columns(n_cols)

        for j in range(files_per_row):
            if i + j < len(files_data):
                file_obj = files_data[i + j]

                with cols[j]:
                    # Determine selection styling
                    is_selected = (st.session_state.get('selected_file') == file_obj)
                    selection_style = "border: 2px solid #2196f3; background-color: #f0f8ff;" if is_selected else ""

                    # File card
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

                    # Action buttons for grid view
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
                        # Context menu for grid view
                        with st.popover("⋮"):
                            st.markdown(f"**{file_obj['name']}**")

                            if st.button("📝 Rinomina", key=f"grid_rename_{i}_{j}"):
                                st.session_state.action_file = file_obj
                                st.session_state.action_type = 'rename'
                                st.rerun()

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

def display_ai_details_panel():
    """Display the AI details panel for selected files."""
    # Initialize session state for file selection
    if 'selected_file' not in st.session_state:
        st.session_state.selected_file = None

    if st.session_state.selected_file:
        file_obj = st.session_state.selected_file

        st.markdown(f"**📄 File Selezionato:** {file_obj['name']}")

        # File metadata
        st.markdown("**📋 Metadati:**")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**Titolo:** {file_obj.get('title', 'N/A')}")
            st.markdown(f"**Autori:** {file_obj.get('authors', 'N/A')}")
            st.markdown(f"**Anno:** {file_obj.get('publication_year', 'N/A')}")

        with col2:
            st.markdown(f"**Dimensione:** {file_obj['size'] / 1024:.1f} KB")
            st.markdown(f"**Tipo:** {file_obj.get('extension', 'N/A').upper()}")
            st.markdown(f"**Stato:** {'Indicizzato' if file_obj['status'] == 'indexed' else 'Non indicizzato'}")

        # AI Preview
        if file_obj.get('formatted_preview'):
            st.markdown("**🤖 Anteprima AI:**")
            st.info(file_obj['formatted_preview'])
        else:
            st.warning("⚠️ Nessuna anteprima AI disponibile per questo file.")

        # AI Actions
        st.markdown("**⚡ Azioni AI:**")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📝 Riassumi", help="Genera un nuovo riassunto"):
                st.info("🚧 Funzione di riassunto non ancora implementata")

        with col2:
            if st.button("🌐 Traduci", help="Traduci anteprima in altra lingua"):
                st.info("🚧 Funzione di traduzione non ancora implementata")

        with col3:
            if st.button("🔍 Entità", help="Estrai entità chiave"):
                st.info("🚧 Funzione di estrazione entità non ancora implementata")

        # Edit preview button
        if st.button("✏️ Modifica Anteprima", help="Passa alla modalità di modifica"):
            st.info("🚧 Modalità di modifica non ancora implementata")

    else:
        st.info("👈 Seleziona un file dalla vista centrale per visualizzare i dettagli AI.")

def handle_file_actions():
    """Handle file operations like rename, delete, and AI actions."""

    # Handle single file actions
    if 'action_file' in st.session_state and 'action_type' in st.session_state:
        file_obj = st.session_state.action_file
        action = st.session_state.action_type

        if action == 'rename':
            st.markdown("### 📝 Rinomina File")
            st.markdown(f"**File corrente:** {file_obj['name']}")

            # Get current title or filename
            current_title = file_obj.get('title', file_obj['name'])

            with st.form("rename_form"):
                st.markdown("**Nuovo titolo:**")
                new_title = st.text_input(
                    "Titolo",
                    value=current_title,
                    key="rename_title_input"
                )

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Salva"):
                        if new_title and new_title != current_title:
                            # Update in database
                            success = update_paper_metadata(file_obj['name'], {'title': new_title})
                            if success:
                                st.success(f"✅ File rinominato in: {new_title}")
                                # Clear action state
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
                        # Clear action state
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

    # Handle AI actions
    if 'ai_action_file' in st.session_state and 'ai_action_type' in st.session_state:
        file_obj = st.session_state.ai_action_file
        action = st.session_state.ai_action_type

        st.markdown(f"### 🤖 Azione AI: {action.title()}")
        st.markdown(f"**File:** {file_obj['name']}")

        if st.button("▶️ Esegui Azione"):
            st.info(f"🚧 Azione '{action}' avviata per il file {file_obj['name']}")
            st.info("Questa funzionalità sarà implementata con l'integrazione Celery")

            # Here you would trigger the appropriate Celery task
            # For now, just show placeholder
            if action == 'summarize':
                st.info("📝 Generazione riassunto in corso...")
            elif action == 'translate':
                st.info("🌐 Traduzione in corso...")
            elif action == 'entities':
                st.info("🔍 Estrazione entità in corso...")

        if st.button("❌ Chiudi"):
            del st.session_state.ai_action_file
            del st.session_state.ai_action_type
            st.rerun()

    # Handle bulk actions
    if 'bulk_action' in st.session_state and 'bulk_files' in st.session_state:
        action = st.session_state.bulk_action
        files = st.session_state.bulk_files

        st.markdown(f"### 📋 Azione Multipla: {action.title()}")
        st.markdown(f"**File selezionati:** {len(files)}")

        if action == 'delete':
            st.warning("⚠️ Eliminazione multipla - Questa azione non può essere annullata!")

            if st.button(f"🗑️ Elimina {len(files)} file", type="primary"):
                success_count = 0
                for file_obj in files:
                    if delete_paper(file_obj['name']):
                        success_count += 1

                if success_count == len(files):
                    st.success(f"✅ Eliminati {success_count} file con successo!")
                else:
                    st.warning(f"⚠️ Eliminati {success_count}/{len(files)} file")

                # Clear bulk action state
                del st.session_state.bulk_action
                del st.session_state.bulk_files
                st.rerun()

        elif action == 'ai':
            st.markdown("**Azione AI per file multipli**")
            ai_options = ["Riassumi", "Traduci", "Entità"]
            selected_ai_action = st.selectbox("Scegli azione AI", ai_options)

            if st.button(f"▶️ Esegui {selected_ai_action}"):
                st.info(f"🚧 Avvio {selected_ai_action} per {len(files)} file...")
                # Clear bulk action state
                del st.session_state.bulk_action
                del st.session_state.bulk_files
                st.rerun()

        if st.button("❌ Annulla"):
            del st.session_state.bulk_action
            del st.session_state.bulk_files
            st.rerun()

def main():
    """Main function to run the file explorer UI."""
    st.set_page_config(
        page_title="File Explorer - Assistente AI",
        page_icon="🗂️",
        layout="wide"
    )

    st.title("🗂️ File Explorer")
    st.markdown("Naviga e gestisci la tua biblioteca di documenti")

    # Handle any pending file actions
    handle_file_actions()

    # Create the three-column layout
    create_three_column_layout()

if __name__ == "__main__":
    main()
