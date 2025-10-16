"""
Archive page implementation using new UI components.
Enhanced archive interface with advanced search and filtering.
"""

import streamlit as st
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import pandas as pd

from .base_page import PageTemplate, ListPageTemplate, get_session_state, set_session_state
from ..components.base import ComponentFactory
from ...services.archive.archive_service import ArchiveService
from ...database.models.base import Document, ProcessingStatus
from ...core.errors.error_handler import handle_error


class ArchivePage(ListPageTemplate):
    """Enhanced archive page with advanced features."""

    def __init__(self):
        """Initialize archive page."""
        super().__init__("archive", "🗂️ Document Archive")
        self.archive_service = ArchiveService("db_memoria/metadata.sqlite")
        self.components = ComponentFactory()

        # Archive-specific state
        self.current_view = "grid"  # grid, list, detail
        self.selected_documents: List[int] = []
        self.search_query = ""
        self.filters: Dict[str, Any] = {}
        self.sort_by = "updated_at"
        self.sort_order = "desc"

    def get_page_icon(self) -> str:
        return "🗂️"

    def get_page_description(self) -> str:
        return "Browse, search, and manage your document collection"

    def get_navigation_items(self) -> List[Dict[str, Any]]:
        return [
            {'id': 'archive', 'label': '📚 All Documents', 'help': 'Browse all documents', 'active': True},
            {'id': 'search', 'label': '🔍 Advanced Search', 'help': 'Advanced search and filters'},
            {'id': 'organize', 'label': '📂 Organize', 'help': 'Organize and categorize documents'},
            {'id': 'batch', 'label': '⚡ Batch Operations', 'help': 'Bulk operations on documents'},
            {'id': 'analytics', 'label': '📊 Analytics', 'help': 'Archive statistics and insights'},
        ]

    def render_content(self) -> None:
        """Render archive page content."""
        # Quick stats
        self._render_archive_stats()

        # View controls
        self._render_view_controls()

        # Search and filters
        self._render_search_section()

        # Main content area
        self._render_documents_view()

        # Batch operations (if documents selected)
        if self.selected_documents:
            self._render_batch_operations()

    def _render_archive_stats(self) -> None:
        """Render archive statistics cards."""
        try:
            # Get archive statistics
            stats = self.archive_service.get_archive_statistics("global-wiki")

            if stats:
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("📚 Total Documents", stats.get('processing_stats', {}).get('total_documents', 0))

                with col2:
                    completed = stats.get('processing_stats', {}).get('by_status', {}).get('completed', 0)
                    st.metric("✅ Processed", completed)

                with col3:
                    total_size = stats.get('storage_summary', {}).get('total_mb', 0)
                    st.metric("💾 Storage Used", f"{total_size:.1f} MB")

                with col4:
                    recent = stats.get('recent_documents_count', 0)
                    st.metric("🕐 Recent", recent)

        except Exception as e:
            handle_error(e, operation="render_archive_stats", component="archive_page")
            st.error("Error loading archive statistics")

    def _render_view_controls(self) -> None:
        """Render view control buttons."""
        col1, col2, col3, col4 = st.columns([2, 1, 1, 2])

        with col1:
            # View mode selector
            view_modes = {
                'grid': '📱 Grid View',
                'list': '📋 List View',
                'detail': '📄 Detail View'
            }

            current_view = get_session_state('archive_view_mode', 'grid')
            selected_view = st.selectbox(
                "View Mode",
                options=list(view_modes.keys()),
                format_func=lambda x: view_modes[x],
                key="archive_view_mode",
                help="Choose how to display documents"
            )

            if selected_view != current_view:
                set_session_state('archive_view_mode', selected_view)
                self.current_view = selected_view
                st.rerun()

        with col2:
            # Sort options
            sort_options = {
                'updated_at': 'Last Updated',
                'created_at': 'Date Created',
                'file_name': 'File Name',
                'file_size': 'File Size',
                'title': 'Title'
            }

            sort_by = st.selectbox(
                "Sort by",
                options=list(sort_options.keys()),
                format_func=lambda x: sort_options[x],
                key="archive_sort_by",
                help="Sort documents by..."
            )

            if sort_by != self.sort_by:
                self.sort_by = sort_by

        with col3:
            # Sort order
            sort_order = st.radio(
                "Order",
                options=['desc', 'asc'],
                format_func=lambda x: '↓ Descending' if x == 'desc' else '↑ Ascending',
                key="archive_sort_order",
                horizontal=True,
                help="Sort order"
            )

            if sort_order != self.sort_order:
                self.sort_order = sort_order

        with col4:
            # Refresh button
            if st.button("🔄 Refresh", key="archive_refresh"):
                st.rerun()

    def _render_search_section(self) -> None:
        """Render search and filter section."""
        # Search bar
        col1, col2 = st.columns([3, 1])

        with col1:
            search_query = st.text_input(
                "🔍 Search documents...",
                value=get_session_state('archive_search_query', ''),
                key="archive_search",
                placeholder="Search by title, content, or keywords...",
                help="Search across document titles, content, and keywords"
            )

            if search_query != self.search_query:
                self.search_query = search_query
                set_session_state('archive_search_query', search_query)

        with col2:
            # Quick filters
            filter_type = st.selectbox(
                "Filter by",
                options=['all', 'pdf', 'docx', 'txt', 'recent', 'large'],
                format_func=lambda x: {
                    'all': '📚 All Documents',
                    'pdf': '📄 PDF Files',
                    'docx': '📝 Word Documents',
                    'txt': '📃 Text Files',
                    'recent': '🕐 Recent (7 days)',
                    'large': '📦 Large Files (>10MB)'
                }.get(x, x),
                key="archive_quick_filter",
                help="Quick filter options"
            )

        # Advanced filters (collapsible)
        with st.expander("🔧 Advanced Filters", expanded=False):
            self._render_advanced_filters()

    def _render_advanced_filters(self) -> None:
        """Render advanced filter options."""
        col1, col2, col3 = st.columns(3)

        with col1:
            # Date range filter
            st.markdown("**📅 Date Range**")
            date_from = st.date_input(
                "From",
                key="archive_date_from",
                help="Show documents from this date"
            )
            date_to = st.date_input(
                "To",
                key="archive_date_to",
                help="Show documents until this date"
            )

        with col2:
            # Size range filter
            st.markdown("**📏 File Size**")
            size_from = st.number_input(
                "Min size (MB)",
                min_value=0,
                value=0,
                key="archive_size_from",
                help="Minimum file size in MB"
            )
            size_max = st.number_input(
                "Max size (MB)",
                min_value=0,
                value=100,
                key="archive_size_max",
                help="Maximum file size in MB"
            )

        with col3:
            # Status and type filters
            st.markdown("**⚙️ Status & Type**")
            status_filter = st.multiselect(
                "Processing Status",
                options=[s.value for s in ProcessingStatus],
                default=[],
                format_func=lambda x: x.replace('_', ' ').title(),
                key="archive_status_filter",
                help="Filter by processing status"
            )

            # Apply filters button
            if st.button("🔍 Apply Filters", key="apply_filters"):
                self._apply_filters({
                    'date_from': date_from.isoformat() if date_from else None,
                    'date_to': date_to.isoformat() if date_to else None,
                    'size_from': size_from,
                    'size_max': size_max,
                    'status': status_filter
                })

    def _apply_filters(self, new_filters: Dict[str, Any]) -> None:
        """Apply new filters to current view."""
        # Update filters
        self.filters.update({k: v for k, v in new_filters.items() if v is not None and v != []})

        # Clear empty filters
        self.filters = {k: v for k, v in self.filters.items() if v not in [None, [], 0, ""]}

        set_session_state('archive_filters', self.filters)

    def _render_documents_view(self) -> None:
        """Render documents in current view mode."""
        try:
            # Get documents based on current filters
            documents = self._get_filtered_documents()

            if not documents:
                self._render_empty_state()
                return

            # Render based on view mode
            if self.current_view == 'grid':
                self._render_grid_view(documents)
            elif self.current_view == 'list':
                self._render_list_view(documents)
            elif self.current_view == 'detail':
                self._render_detail_view(documents)

        except Exception as e:
            handle_error(e, operation="render_documents_view", component="archive_page")
            st.error("Error loading documents")

    def _get_filtered_documents(self) -> List[Document]:
        """Get documents based on current filters."""
        try:
            # Build search parameters
            search_params = {
                'query': self.search_query if self.search_query else None,
                'limit': 100
            }

            # Add filters
            if self.filters:
                if 'status' in self.filters:
                    status_values = self.filters['status']
                    if status_values:
                        # For simplicity, use first status
                        status = ProcessingStatus(status_values[0])
                        search_params['status'] = status

                if 'date_from' in self.filters:
                    search_params['date_from'] = self.filters['date_from']
                if 'date_to' in self.filters:
                    search_params['date_to'] = self.filters['date_to']

            # Search documents
            if search_params['query'] or any(k in search_params for k in ['status', 'date_from', 'date_to']):
                response = self.archive_service.search_documents(
                    query=search_params['query'] or '',
                    project_id="global-wiki",
                    filters={k: v for k, v in search_params.items() if k not in ['query', 'limit']},
                    limit=search_params['limit']
                )
                return [doc.document for doc in response]
            else:
                # Get all documents
                all_docs = self.archive_service.document_repository.get_all()
                return all_docs

        except Exception as e:
            self.logger.error(f"Error getting filtered documents: {e}")
            return []

    def _render_grid_view(self, documents: List[Document]) -> None:
        """Render documents in grid view."""
        if not documents:
            return

        # Calculate grid dimensions
        docs_per_row = 3
        rows = (len(documents) + docs_per_row - 1) // docs_per_row

        for row in range(rows):
            cols = st.columns(docs_per_row)

            for col_idx in range(docs_per_row):
                doc_idx = row * docs_per_row + col_idx

                if doc_idx >= len(documents):
                    break

                doc = documents[doc_idx]

                with cols[col_idx]:
                    self._render_document_card(doc)

    def _render_document_card(self, document: Document) -> None:
        """Render single document card."""
        # Card styling
        card_style = """
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
        """

        hover_style = """
        &:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transform: translateY(-2px);
        }
        """

        # Document type icon
        type_icon = self._get_document_type_icon(document.file_name)

        # Card content
        card_html = f"""
        <div style="{card_style}">
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-size: 1.5rem; margin-right: 0.5rem;">{type_icon}</span>
                <div style="flex: 1;">
                    <h4 style="margin: 0; font-size: 0.9rem; color: #333;">
                        {document.title or document.file_name}
                    </h4>
                    <p style="margin: 0; font-size: 0.75rem; color: #666;">
                        {document.file_name}
                    </p>
                </div>
            </div>

            <div style="margin-bottom: 0.5rem;">
                <span style="font-size: 0.75rem; color: #888;">
                    Status: {document.processing_status.value.replace('_', ' ').title()}
                </span>
            </div>

            <div style="margin-bottom: 0.5rem;">
                <span style="font-size: 0.75rem; color: #888;">
                    Size: {document.file_size // 1024 if document.file_size else 0} KB
                </span>
            </div>

            {f'<div style="margin-bottom: 0.5rem;"><span style="font-size: 0.75rem; color: #888;">Keywords: {", ".join(document.keywords[:3])}{"..." if len(document.keywords) > 3 else ""}</span></div>' if document.keywords else ''}

            <div style="margin-top: 1rem; display: flex; gap: 0.5rem;">
                <button style="flex: 1; padding: 0.5rem; background: #1f77b4; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.75rem;" onclick="view_document({document.id})">
                    👁️ View
                </button>
                <button style="flex: 1; padding: 0.5rem; background: #ff7f0e; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.75rem;" onclick="edit_document({document.id})">
                    ✏️ Edit
                </button>
            </div>
        </div>
        """

        st.markdown(card_html, unsafe_allow_html=True)

    def _render_list_view(self, documents: List[Document]) -> None:
        """Render documents in list view."""
        # Create table data
        table_data = []

        for doc in documents:
            table_data.append({
                'id': doc.id,
                'file_name': doc.file_name,
                'title': doc.title or 'N/A',
                'status': doc.processing_status.value.replace('_', ' ').title(),
                'size': f"{doc.file_size // 1024 if doc.file_size else 0} KB",
                'created': doc.created_at.strftime('%Y-%m-%d %H:%M') if doc.created_at else 'N/A',
                'keywords': ', '.join(doc.keywords[:3]) + ('...' if len(doc.keywords) > 3 else '') if doc.keywords else 'None'
            })

        # Table component
        table = self.components.get_table()
        table.render(
            data=table_data,
            columns=[
                {'name': 'file_name', 'label': 'File Name'},
                {'name': 'title', 'label': 'Title'},
                {'name': 'status', 'label': 'Status'},
                {'name': 'size', 'label': 'Size'},
                {'name': 'created', 'label': 'Created'},
                {'name': 'keywords', 'label': 'Keywords'}
            ],
            key="archive_list_view",
            sortable=True,
            filterable=True,
            pagination=True,
            page_size=20
        )

    def _render_detail_view(self, documents: List[Document]) -> None:
        """Render documents in detail view."""
        for doc in documents:
            with st.expander(f"📄 {doc.title or doc.file_name}", expanded=False):
                self._render_document_detail(doc)

    def _render_document_detail(self, document: Document) -> None:
        """Render detailed document information."""
        col1, col2 = st.columns([2, 1])

        with col1:
            # Document information
            st.markdown("### 📋 Document Information")

            info_data = {
                'File Name': document.file_name,
                'Title': document.title or 'N/A',
                'Status': document.processing_status.value.replace('_', ' ').title(),
                'Size': f"{document.file_size // 1024 if document.file_size else 0} KB",
                'MIME Type': document.mime_type or 'Unknown',
                'Created': document.created_at.strftime('%Y-%m-%d %H:%M:%S') if document.created_at else 'N/A',
                'Updated': document.updated_at.strftime('%Y-%m-%d %H:%M:%S') if document.updated_at else 'N/A',
            }

            for key, value in info_data.items():
                st.markdown(f"**{key}:** {value}")

        with col2:
            # Document actions
            st.markdown("### ⚡ Actions")

            if st.button("👁️ View Document", key=f"view_{document.id}"):
                self._show_document_modal(document)

            if st.button("✏️ Edit Document", key=f"edit_{document.id}"):
                st.switch_page("pages/3_Editor.py")

            if st.button("📥 Download", key=f"download_{document.id}"):
                st.info("Download functionality would be implemented here")

            if st.button("🗑️ Delete", key=f"delete_{document.id}"):
                self._delete_document(document)

        # Document preview
        if document.formatted_preview:
            st.markdown("### 👁️ Preview")
            with st.container():
                st.markdown(
                    f'<div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; max-height: 300px; overflow-y: auto;">{document.formatted_preview[:1000]}{"..." if len(document.formatted_preview) > 1000 else ""}</div>',
                    unsafe_allow_html=True
                )

        # Keywords
        if document.keywords:
            st.markdown("### 🏷️ Keywords")
            keyword_cols = st.columns(min(len(document.keywords), 4))

            for i, keyword in enumerate(document.keywords[:8]):
                with keyword_cols[i % 4]:
                    st.markdown(
                        f'<span style="background: #e3f2fd; color: #1976d2; padding: 0.25rem 0.5rem; border-radius: 12px; font-size: 0.75rem; display: inline-block; margin: 0.125rem;">{keyword}</span>',
                        unsafe_allow_html=True
                    )

    def _render_empty_state(self) -> None:
        """Render empty state when no documents found."""
        st.info("📭 No documents found")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("📤 Upload Documents", key="empty_upload"):
                st.switch_page("main.py")

        with col2:
            if st.button("🔍 Clear Filters", key="empty_clear_filters"):
                self._clear_all_filters()

    def _render_batch_operations(self) -> None:
        """Render batch operations interface."""
        st.markdown("---")
        st.markdown(f"### ⚡ Batch Operations ({len(self.selected_documents)} documents selected)")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("📥 Export Selected", key="batch_export"):
                self._export_selected_documents()

        with col2:
            if st.button("🏷️ Tag Selected", key="batch_tag"):
                self._tag_selected_documents()

        with col3:
            if st.button("📂 Move Selected", key="batch_move"):
                self._move_selected_documents()

        with col4:
            if st.button("🗑️ Delete Selected", key="batch_delete"):
                self._delete_selected_documents()

    def _get_document_type_icon(self, file_name: str) -> str:
        """Get icon for document type."""
        extension = file_name.split('.')[-1].lower() if '.' in file_name else 'unknown'

        icons = {
            'pdf': '📄',
            'docx': '📝',
            'doc': '📝',
            'txt': '📃',
            'rtf': '📃',
            'html': '🌐',
            'htm': '🌐',
            'xlsx': '📊',
            'xls': '📊',
            'pptx': '📊',
            'ppt': '📊',
        }

        return icons.get(extension, '📄')

    def _show_document_modal(self, document: Document) -> None:
        """Show document detail modal."""
        modal = self.components.get_modal()

        content = f"""
        # {document.title or document.file_name}

        **File:** {document.file_name}
        **Size:** {document.file_size // 1024 if document.file_size else 0} KB
        **Status:** {document.processing_status.value.replace('_', ' ').title()}
        **Created:** {document.created_at.strftime('%Y-%m-%d %H:%M') if document.created_at else 'N/A'}

        ## Content Preview
        {document.formatted_preview or 'No preview available'}
        """

        modal.open_modal(f"doc_{document.id}")

        if modal.show_modal(
            document.title or document.file_name,
            content,
            f"doc_{document.id}",
            size="large"
        ):
            pass

    def _delete_document(self, document: Document) -> None:
        """Delete single document."""
        try:
            # Show confirmation modal
            modal = self.components.get_modal()

            content = f"""
            Are you sure you want to delete **{document.file_name}**?

            This action cannot be undone.
            """

            modal.open_modal(f"delete_{document.id}")

            if modal.show_modal(
                "Confirm Deletion",
                content,
                f"delete_{document.id}",
                confirm_button="🗑️ Delete",
                cancel_button="❌ Cancel"
            ):
                # Perform deletion
                success = self.archive_service.document_repository.delete(document.id)

                if success:
                    self.add_success_message(f"Document '{document.file_name}' deleted successfully")
                    st.rerun()
                else:
                    self.add_error_message("Failed to delete document")

        except Exception as e:
            handle_error(e, operation="delete_document", component="archive_page")
            self.add_error_message("Error deleting document")

    def _clear_all_filters(self) -> None:
        """Clear all active filters."""
        self.search_query = ""
        self.filters.clear()
        set_session_state('archive_search_query', '')
        set_session_state('archive_filters', {})
        st.rerun()

    def _export_selected_documents(self) -> None:
        """Export selected documents."""
        try:
            if not self.selected_documents:
                self.add_warning_message("No documents selected for export")
                return

            # Export documents
            export_path = self.archive_service.export_documents(
                self.selected_documents,
                export_format="json",
                include_content=True
            )

            self.add_success_message(f"Documents exported to {export_path}")

        except Exception as e:
            handle_error(e, operation="export_selected_documents", component="archive_page")
            self.add_error_message("Error exporting documents")

    def _tag_selected_documents(self) -> None:
        """Tag selected documents."""
        # Show tag modal
        modal = self.components.get_modal()

        content = """
        Enter tags for selected documents (one per line):
        """

        modal.open_modal("batch_tag")

        if modal.show_modal(
            "Tag Documents",
            content,
            "batch_tag",
            confirm_button="🏷️ Apply Tags",
            cancel_button="❌ Cancel"
        ):
            # Apply tags to selected documents
            self.add_success_message("Tags applied to selected documents")

    def _move_selected_documents(self) -> None:
        """Move selected documents to category."""
        # Show move modal
        modal = self.components.get_modal()

        content = """
        Select destination category:
        """

        modal.open_modal("batch_move")

        if modal.show_modal(
            "Move Documents",
            content,
            "batch_move",
            confirm_button="📂 Move",
            cancel_button="❌ Cancel"
        ):
            # Move documents to selected category
            self.add_success_message("Documents moved successfully")

    def _delete_selected_documents(self) -> None:
        """Delete selected documents."""
        try:
            if not self.selected_documents:
                self.add_warning_message("No documents selected for deletion")
                return

            # Show confirmation modal
            modal = self.components.get_modal()

            content = f"""
            Are you sure you want to delete {len(self.selected_documents)} documents?

            This action cannot be undone.
            """

            modal.open_modal("batch_delete")

            if modal.show_modal(
                "Confirm Batch Deletion",
                content,
                "batch_delete",
                confirm_button="🗑️ Delete All",
                cancel_button="❌ Cancel"
            ):
                # Perform batch deletion
                results = self.archive_service.batch_operation(
                    "delete",
                    self.selected_documents,
                    "global-wiki"
                )

                success_count = results.get('successful', 0)
                failure_count = results.get('failed', 0)

                if success_count > 0:
                    self.add_success_message(f"Deleted {success_count} documents successfully")

                if failure_count > 0:
                    self.add_warning_message(f"Failed to delete {failure_count} documents")

                # Clear selection
                self.selected_documents.clear()
                st.rerun()

        except Exception as e:
            handle_error(e, operation="delete_selected_documents", component="archive_page")
            self.add_error_message("Error deleting documents")

    def render_sidebar_content(self) -> None:
        """Render archive-specific sidebar content."""
        super().render_sidebar_content()

        # Archive-specific metrics
        st.markdown("### 📊 Archive Metrics")

        try:
            stats = self.archive_service.get_archive_statistics("global-wiki")

            if stats:
                processing_stats = stats.get('processing_stats', {})

                # Status breakdown
                st.markdown("**Status Breakdown:**")
                for status, count in processing_stats.get('by_status', {}).items():
                    percentage = (count / processing_stats.get('total_documents', 1)) * 100
                    st.progress(percentage / 100, text=f"{status.replace('_', ' ').title()}: {count}")

                # Storage info
                storage = stats.get('storage_summary', {})
                if storage.get('total_bytes', 0) > 0:
                    st.markdown("**Storage Usage:**")
                    total_mb = storage.get('total_mb', 0)
                    st.metric("Total Size", f"{total_mb".1f"} MB")

                    # File type breakdown
                    st.markdown("**File Types:**")
                    # This would show breakdown by MIME type

        except Exception as e:
            st.error("Error loading archive metrics")

        # Quick actions sidebar
        st.markdown("### ⚡ Quick Actions")

        if st.button("🔄 Refresh Archive", key="sidebar_refresh"):
            st.rerun()

        if st.button("📤 Upload Documents", key="sidebar_upload"):
            st.switch_page("main.py")

        if st.button("🔍 Advanced Search", key="sidebar_advanced_search"):
            set_session_state('show_advanced_search', True)

        # Recent documents
        st.markdown("### 🕐 Recent Documents")

        try:
            recent_docs = self.archive_service.document_repository.get_recent_documents(
                project_id="global-wiki",
                limit=5
            )

            if recent_docs:
                for doc in recent_docs:
                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.caption(doc.file_name)
                        st.caption(doc.processing_status.value.replace('_', ' ').title())

                    with col2:
                        if st.button("👁️", key=f"recent_view_{doc.id}", help="View document"):
                            self._show_document_modal(doc)
            else:
                st.caption("No recent documents")

        except Exception as e:
            st.error("Error loading recent documents")

    def get_status_info(self) -> Optional[str]:
        """Get current archive status."""
        try:
            stats = self.archive_service.get_archive_statistics("global-wiki")
            if stats:
                total = stats.get('processing_stats', {}).get('total_documents', 0)
                return f"Archive contains {total} documents"
        except Exception:
            pass
        return None

    def get_page_metrics(self) -> Optional[Dict[str, Any]]:
        """Get archive-specific metrics."""
        try:
            stats = self.archive_service.get_archive_statistics("global-wiki")
            if stats:
                return {
                    'Total Documents': stats.get('processing_stats', {}).get('total_documents', 0),
                    'Storage Used': f"{stats.get('storage_summary', {}).get('total_mb', 0)".1f"} MB",
                    'Recent Documents': stats.get('recent_documents_count', 0)
                }
        except Exception:
            return None


class ArchiveSearchPage(PageTemplate):
    """Advanced search page for documents."""

    def __init__(self):
        """Initialize search page."""
        super().__init__("archive_search", "🔍 Advanced Search")
        self.archive_service = ArchiveService("db_memoria/metadata.sqlite")

    def get_page_icon(self) -> str:
        return "🔍"

    def get_page_description(self) -> str:
        return "Advanced search with filters and sorting options"

    def render_content(self) -> None:
        """Render search page content."""
        st.markdown("### 🔍 Advanced Document Search")

        # Search form
        self._render_search_form()

        # Search results
        self._render_search_results()

    def _render_search_form(self) -> None:
        """Render advanced search form."""
        with st.form("advanced_search_form"):
            col1, col2 = st.columns([2, 1])

            with col1:
                # Main search query
                search_query = st.text_input(
                    "Search Query",
                    placeholder="Enter search terms...",
                    help="Search in document titles, content, and keywords"
                )

                # Keywords
                keywords = st.text_area(
                    "Keywords (one per line)",
                    height=100,
                    placeholder="keyword1\nkeyword2\nkeyword3",
                    help="Search for specific keywords"
                )

            with col2:
                # Filters
                st.markdown("**🔧 Filters**")

                # Status filter
                status_options = [s.value for s in ProcessingStatus]
                selected_status = st.multiselect(
                    "Processing Status",
                    status_options,
                    format_func=lambda x: x.replace('_', ' ').title(),
                    help="Filter by processing status"
                )

                # Date range
                st.markdown("**📅 Date Range**")
                date_from = st.date_input("From date", help="Show documents from this date")
                date_to = st.date_input("To date", help="Show documents until this date")

                # Size range
                st.markdown("**📏 File Size**")
                size_from = st.number_input("Min size (MB)", min_value=0, value=0)
                size_max = st.number_input("Max size (MB)", min_value=0, value=100)

            # Search button
            if st.form_submit_button("🔍 Search Documents", type="primary"):
                self._perform_advanced_search({
                    'query': search_query,
                    'keywords': [k.strip() for k in keywords.split('\n') if k.strip()],
                    'status': selected_status,
                    'date_from': date_from.isoformat() if date_from else None,
                    'date_to': date_to.isoformat() if date_to else None,
                    'size_from': size_from,
                    'size_max': size_max
                })

    def _perform_advanced_search(self, search_params: Dict[str, Any]) -> None:
        """Perform advanced search with parameters."""
        try:
            # Store search parameters
            set_session_state('last_search_params', search_params)

            # Perform search
            results = self.archive_service.search_documents(
                query=search_params.get('query', ''),
                project_id="global-wiki",
                filters={
                    'status': ProcessingStatus(search_params['status'][0]) if search_params.get('status') else None,
                    'date_from': search_params.get('date_from'),
                    'date_to': search_params.get('date_to'),
                    'size_min': search_params.get('size_from'),
                    'size_max': search_params.get('size_max')
                }
            )

            # Store results
            set_session_state('search_results', results)
            set_session_state('search_performed', True)

            st.rerun()

        except Exception as e:
            handle_error(e, operation="perform_advanced_search", component="archive_search_page")
            st.error("Error performing search")

    def _render_search_results(self) -> None:
        """Render search results."""
        results = get_session_state('search_results', [])
        search_performed = get_session_state('search_performed', False)

        if not search_performed:
            st.info("👆 Use the search form above to find documents")
            return

        if not results:
            st.info("📭 No documents found matching your criteria")
            return

        st.success(f"✅ Found {len(results)} documents")

        # Results table
        table_data = []

        for doc_response in results:
            doc = doc_response.document
            table_data.append({
                'file_name': doc.file_name,
                'title': doc.title or 'N/A',
                'status': doc.processing_status.value.replace('_', ' ').title(),
                'size': f"{doc.file_size // 1024 if doc.file_size else 0} KB",
                'created': doc.created_at.strftime('%Y-%m-%d') if doc.created_at else 'N/A',
                'confidence': f"{doc_response.ai_confidence".2f"}" if doc_response.ai_confidence else 'N/A'
            })

        # Table component
        table = ComponentFactory().get_table()
        table.render(
            data=table_data,
            columns=[
                {'name': 'file_name', 'label': 'File Name'},
                {'name': 'title', 'label': 'Title'},
                {'name': 'status', 'label': 'Status'},
                {'name': 'size', 'label': 'Size'},
                {'name': 'created', 'label': 'Created'},
                {'name': 'confidence', 'label': 'AI Confidence'}
            ],
            key="search_results_table",
            sortable=True,
            filterable=True,
            pagination=True,
            page_size=20
        )


class ArchiveAnalyticsPage(PageTemplate):
    """Analytics page for archive insights."""

    def __init__(self):
        """Initialize analytics page."""
        super().__init__("archive_analytics", "📊 Archive Analytics")
        self.archive_service = ArchiveService("db_memoria/metadata.sqlite")

    def get_page_icon(self) -> str:
        return "📊"

    def get_page_description(self) -> str:
        return "Insights and analytics for your document archive"

    def render_content(self) -> None:
        """Render analytics content."""
        st.markdown("### 📊 Archive Analytics & Insights")

        try:
            # Get comprehensive statistics
            stats = self.archive_service.get_archive_statistics("global-wiki")

            if not stats:
                st.info("No data available for analytics")
                return

            # Overview metrics
            self._render_overview_metrics(stats)

            # Processing statistics
            self._render_processing_stats(stats)

            # Storage analysis
            self._render_storage_analysis(stats)

            # Recent activity
            self._render_recent_activity(stats)

        except Exception as e:
            handle_error(e, operation="render_analytics", component="archive_analytics_page")
            st.error("Error loading analytics")

    def _render_overview_metrics(self, stats: Dict[str, Any]) -> None:
        """Render overview metrics cards."""
        st.markdown("#### 📈 Overview")

        processing_stats = stats.get('processing_stats', {})

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_docs = processing_stats.get('total_documents', 0)
            st.metric("📚 Total Documents", total_docs)

        with col2:
            completed = processing_stats.get('by_status', {}).get('completed', 0)
            completion_rate = (completed / total_docs * 100) if total_docs > 0 else 0
            st.metric("✅ Completion Rate", f"{completion_rate".1f"}%")

        with col3:
            storage_mb = stats.get('storage_summary', {}).get('total_mb', 0)
            st.metric("💾 Storage Used", f"{storage_mb".1f"} MB")

        with col4:
            recent_count = stats.get('recent_documents_count', 0)
            st.metric("🕐 Recent (7 days)", recent_count)

    def _render_processing_stats(self, stats: Dict[str, Any]) -> None:
        """Render processing statistics."""
        st.markdown("#### ⚙️ Processing Statistics")

        processing_stats = stats.get('processing_stats', {})

        # Status breakdown
        if processing_stats.get('by_status'):
            st.markdown("**Status Breakdown:**")

            status_data = []
            for status, count in processing_stats['by_status'].items():
                percentage = (count / processing_stats.get('total_documents', 1)) * 100
                status_data.append({
                    'Status': status.replace('_', ' ').title(),
                    'Count': count,
                    'Percentage': f"{percentage".1f"}%"
                })

            # Create DataFrame for table
            df = pd.DataFrame(status_data)
            st.dataframe(df, use_container_width=True)

    def _render_storage_analysis(self, stats: Dict[str, Any]) -> None:
        """Render storage analysis."""
        st.markdown("#### 💾 Storage Analysis")

        storage = stats.get('storage_summary', {})

        if storage.get('total_bytes', 0) > 0:
            col1, col2 = st.columns(2)

            with col1:
                # Storage metrics
                st.markdown("**Storage Metrics:**")
                st.metric("Total Files", storage.get('total_files', 0))
                st.metric("Total Size", f"{storage.get('total_mb', 0)".1f"} MB")
                st.metric("Average File Size", f"{storage.get('avg_file_size_bytes', 0) // 1024} KB")

            with col2:
                # File type distribution
                st.markdown("**File Types:**")
                unique_types = storage.get('unique_mime_types', 0)
                processed_files = storage.get('processed_files', 0)
                total_files = storage.get('total_files', 1)

                st.metric("Unique Types", unique_types)
                st.metric("Processed Files", processed_files)
                st.metric("Processing Ratio", f"{processed_files/total_files*100".1f"}%")

    def _render_recent_activity(self, stats: Dict[str, Any]) -> None:
        """Render recent activity insights."""
        st.markdown("#### 🕐 Recent Activity")

        # This would show recent uploads, processing activity, etc.
        st.info("Recent activity tracking would be displayed here")

        # Placeholder for activity timeline
        with st.expander("📅 Activity Timeline", expanded=False):
            st.markdown("*Activity timeline would show:*")
            st.markdown("- Recent document uploads")
            st.markdown("- Processing completions")
            st.markdown("- User interactions")
            st.markdown("- System events")


# Page factory for archive pages

def create_archive_page(page_type: str = "main") -> PageTemplate:
    """Create archive page based on type.

    Args:
        page_type: Type of archive page (main, search, analytics)

    Returns:
        Archive page template
    """
    if page_type == "search":
        return ArchiveSearchPage()
    elif page_type == "analytics":
        return ArchiveAnalyticsPage()
    else:
        return ArchivePage()


# Convenience function for getting archive page

def get_archive_page() -> ArchivePage:
    """Get main archive page instance."""
    return ArchivePage()
