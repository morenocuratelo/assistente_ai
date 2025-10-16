"""
Base page template system for consistent page structure.
Provides standardized layout, navigation, and state management.
"""

import streamlit as st
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import logging

from ..components.base import ComponentFactory, ComponentConfig
from ...config.settings import get_config
from ...core.errors.error_handler import get_error_handler


class PageTemplate:
    """Base template for all application pages."""

    def __init__(self, page_id: str, title: str, config: Optional[ComponentConfig] = None):
        """Initialize page template.

        Args:
            page_id: Unique page identifier
            title: Page title
            config: UI configuration
        """
        self.page_id = page_id
        self.title = title
        self.config = config or ComponentConfig()
        self.components = ComponentFactory()
        self.logger = logging.getLogger(__name__)

        # Page state
        self.breadcrumbs: List[Dict[str, str]] = []
        self.error_messages: List[str] = []
        self.success_messages: List[str] = []
        self.warning_messages: List[str] = []

    def render(self) -> None:
        """Render complete page with standard structure."""
        # Setup page configuration
        self._setup_page()

        # Render header
        self._render_header()

        # Render navigation
        self._render_navigation()

        # Render breadcrumbs
        self._render_breadcrumbs()

        # Render main content (to be implemented by subclasses)
        self.render_content()

        # Render footer
        self._render_footer()

        # Handle notifications
        self._render_notifications()

    def _setup_page(self) -> None:
        """Setup page configuration."""
        st.set_page_config(
            page_title=f"{self.title} - {get_config().app_name}",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # Initialize session state for this page
        if 'current_page' not in st.session_state:
            st.session_state.current_page = self.page_id

        if 'page_load_time' not in st.session_state:
            st.session_state.page_load_time = datetime.utcnow()

    def _render_header(self) -> None:
        """Render page header."""
        # Main header with title and actions
        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            # Page title with icon
            icon = self.get_page_icon()
            st.title(f"{icon} {self.title}")

            # Page description
            description = self.get_page_description()
            if description:
                st.caption(description)

        with col2:
            # Quick actions
            self._render_quick_actions()

        with col3:
            # Page status and info
            self._render_page_status()

        st.divider()

    def _render_navigation(self) -> None:
        """Render navigation sidebar."""
        navigation_items = self.get_navigation_items()

        with st.sidebar:
            # Navigation component
            nav = self.components.get_navigation(self.config)
            selected_item = nav.render_sidebar(navigation_items)

            if selected_item:
                self.handle_navigation(selected_item)

            st.divider()

            # Page-specific sidebar content
            self.render_sidebar_content()

    def _render_breadcrumbs(self) -> None:
        """Render breadcrumb navigation."""
        if self.breadcrumbs:
            nav = self.components.get_navigation(self.config)
            nav.render_breadcrumbs(self.breadcrumbs)

    def _render_quick_actions(self) -> None:
        """Render quick action buttons."""
        # Default quick actions - can be overridden
        if st.button("🔄 Refresh", key=f"{self.page_id}_refresh"):
            st.rerun()

        if st.button("❓ Help", key=f"{self.page_id}_help"):
            self.show_help()

    def _render_page_status(self) -> None:
        """Render page status information."""
        # Show last update time
        if 'page_load_time' in st.session_state:
            load_time = st.session_state.page_load_time
            st.caption(f"Last updated: {load_time.strftime('%H:%M:%S')}")

        # Show page-specific status
        status_info = self.get_status_info()
        if status_info:
            st.info(status_info)

    def _render_footer(self) -> None:
        """Render page footer."""
        st.divider()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.caption(f"Page: {self.page_id}")

        with col2:
            config = get_config()
            st.caption(f"Environment: {config.environment}")

        with col3:
            if 'page_load_time' in st.session_state:
                load_time = st.session_state.page_load_time
                st.caption(f"Loaded: {load_time.strftime('%H:%M:%S')}")

    def _render_notifications(self) -> None:
        """Render any pending notifications."""
        notification = self.components.get_notification(self.config)

        for message in self.error_messages:
            notification.show_error(message)

        for message in self.warning_messages:
            notification.show_warning(message)

        for message in self.success_messages:
            notification.show_success(message)

        # Clear messages after displaying
        self.error_messages.clear()
        self.warning_messages.clear()
        self.success_messages.clear()

    def render_content(self) -> None:
        """Render main page content. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement render_content()")

    def render_sidebar_content(self) -> None:
        """Render page-specific sidebar content. Can be overridden."""
        # Default sidebar content
        st.markdown("### 📊 Page Info")
        st.info(f"Current page: {self.page_id}")

        # Page-specific metrics
        metrics = self.get_page_metrics()
        if metrics:
            for key, value in metrics.items():
                st.metric(key, value)

    def get_page_icon(self) -> str:
        """Get icon for this page. Can be overridden."""
        return "📄"

    def get_page_description(self) -> str:
        """Get description for this page. Can be overridden."""
        return ""

    def get_navigation_items(self) -> List[Dict[str, Any]]:
        """Get navigation items for sidebar. Can be overridden."""
        return [
            {'id': 'dashboard', 'label': '🏠 Dashboard', 'help': 'Main dashboard'},
            {'id': 'chat', 'label': '💬 Chat', 'help': 'Chat with documents'},
            {'id': 'archive', 'label': '🗂️ Archive', 'help': 'Document archive'},
            {'id': 'editor', 'label': '📝 Editor', 'help': 'Document editor'},
            {'id': 'settings', 'label': '⚙️ Settings', 'help': 'Application settings'},
        ]

    def get_status_info(self) -> Optional[str]:
        """Get current status information. Can be overridden."""
        return None

    def get_page_metrics(self) -> Optional[Dict[str, Any]]:
        """Get page-specific metrics. Can be overridden."""
        return None

    def handle_navigation(self, item_id: str) -> None:
        """Handle navigation item selection.

        Args:
            item_id: Selected navigation item ID
        """
        # Update current page
        st.session_state.current_page = item_id

        # Navigate to selected page
        page_mapping = {
            'dashboard': 'main.py',
            'chat': 'pages/1_Chat.py',
            'archive': 'pages/2_Archivio.py',
            'editor': 'pages/3_Editor.py',
            'settings': 'pages/4_Nuovo.py',  # Placeholder
        }

        if item_id in page_mapping:
            try:
                st.switch_page(page_mapping[item_id])
            except Exception as e:
                self.logger.error(f"Navigation error to {item_id}: {e}")
                st.error(f"Error navigating to {item_id}")

    def show_help(self) -> None:
        """Show page-specific help."""
        help_content = self.get_help_content()

        modal = self.components.get_modal(self.config)
        modal.open_modal(f"{self.page_id}_help")

        if modal.show_modal(
            "Help",
            help_content,
            f"{self.page_id}_help",
            size="large"
        ):
            pass  # Modal closed

    def get_help_content(self) -> str:
        """Get help content for this page. Can be overridden."""
        return f"""
        # {self.title} Help

        This is the help content for the {self.title} page.

        ## Features
        - Feature 1 description
        - Feature 2 description

        ## Usage
        1. Step 1
        2. Step 2
        3. Step 3

        For more help, contact support.
        """

    def add_breadcrumb(self, label: str, path: str) -> None:
        """Add breadcrumb item.

        Args:
            label: Breadcrumb label
            path: Navigation path
        """
        self.breadcrumbs.append({'label': label, 'path': path})

    def set_breadcrumbs(self, breadcrumbs: List[Dict[str, str]]) -> None:
        """Set breadcrumb navigation.

        Args:
            breadcrumbs: List of breadcrumb items
        """
        self.breadcrumbs = breadcrumbs

    def add_error_message(self, message: str) -> None:
        """Add error message to display.

        Args:
            message: Error message
        """
        self.error_messages.append(message)

    def add_success_message(self, message: str) -> None:
        """Add success message to display.

        Args:
            message: Success message
        """
        self.success_messages.append(message)

    def add_warning_message(self, message: str) -> None:
        """Add warning message to display.

        Args:
            message: Warning message
        """
        self.warning_messages.append(message)

    def handle_error(self, error: Exception, operation: str = "page_operation") -> None:
        """Handle error with proper logging and user feedback.

        Args:
            error: Exception to handle
            operation: Operation that caused the error
        """
        # Log error
        error_handler = get_error_handler()
        error_result = error_handler.handle_error(
            error,
            operation=operation,
            component=f"page_{self.page_id}"
        )

        # Add user-friendly error message
        self.add_error_message(f"Operation failed: {error_result.message}")

        # Add recovery suggestion if available
        if error_result.recovery_suggestions:
            self.add_warning_message(f"Suggestion: {error_result.recovery_suggestions}")


class StateManager:
    """Centralized state management for pages."""

    def __init__(self):
        """Initialize state manager."""
        self.logger = logging.getLogger(__name__)
        self._state_listeners: Dict[str, List[Callable]] = {}
        self._state_validators: Dict[str, Callable] = {}

    def get_state(self, key: str, default: Any = None) -> Any:
        """Get state value.

        Args:
            key: State key
            default: Default value if key not found

        Returns:
            State value or default
        """
        return st.session_state.get(key, default)

    def set_state(self, key: str, value: Any, validate: bool = True) -> bool:
        """Set state value with optional validation.

        Args:
            key: State key
            value: State value
            validate: Whether to validate the value

        Returns:
            True if state was set successfully
        """
        try:
            # Validate if validator exists
            if validate and key in self._state_validators:
                validator = self._state_validators[key]
                if not validator(value):
                    self.logger.warning(f"State validation failed for {key}")
                    return False

            # Set state
            st.session_state[key] = value

            # Notify listeners
            self._notify_state_listeners(key, value)

            return True

        except Exception as e:
            self.logger.error(f"Error setting state {key}: {e}")
            return False

    def update_state(self, updates: Dict[str, Any]) -> bool:
        """Update multiple state values.

        Args:
            updates: Dictionary of state updates

        Returns:
            True if all updates successful
        """
        for key, value in updates.items():
            if not self.set_state(key, value):
                return False
        return True

    def clear_state(self, key: str) -> bool:
        """Clear state value.

        Args:
            key: State key to clear

        Returns:
            True if cleared successfully
        """
        try:
            if key in st.session_state:
                del st.session_state[key]
                self._notify_state_listeners(key, None)
            return True
        except Exception as e:
            self.logger.error(f"Error clearing state {key}: {e}")
            return False

    def register_state_listener(self, key: str, listener: Callable) -> None:
        """Register listener for state changes.

        Args:
            key: State key to listen to
            listener: Listener function
        """
        if key not in self._state_listeners:
            self._state_listeners[key] = []
        self._state_listeners[key].append(listener)

    def register_state_validator(self, key: str, validator: Callable) -> None:
        """Register validator for state value.

        Args:
            key: State key to validate
            validator: Validator function that returns bool
        """
        self._state_validators[key] = validator

    def _notify_state_listeners(self, key: str, value: Any) -> None:
        """Notify listeners of state changes."""
        if key in self._state_listeners:
            for listener in self._state_listeners[key]:
                try:
                    listener(key, value)
                except Exception as e:
                    self.logger.error(f"Error notifying state listener: {e}")

    def get_state_summary(self) -> Dict[str, Any]:
        """Get summary of current state.

        Returns:
            Dictionary with state summary
        """
        return {
            'total_keys': len(st.session_state),
            'state_keys': list(st.session_state.keys()),
            'state_types': {
                k: type(v).__name__ for k, v in st.session_state.items()
            },
            'timestamp': datetime.utcnow().isoformat()
        }

    def cleanup_expired_state(self, max_age_hours: int = 24) -> int:
        """Clean up expired state values.

        Args:
            max_age_hours: Maximum age in hours

        Returns:
            Number of items cleaned up
        """
        # This would be more sophisticated in a real implementation
        # For now, just return 0
        return 0


class PageRegistry:
    """Registry for managing page templates."""

    def __init__(self):
        """Initialize page registry."""
        self.pages: Dict[str, PageTemplate] = {}
        self.state_manager = StateManager()
        self.logger = logging.getLogger(__name__)

    def register_page(self, page: PageTemplate) -> None:
        """Register page template.

        Args:
            page: Page template to register
        """
        self.pages[page.page_id] = page
        self.logger.info(f"Page registered: {page.page_id}")

    def get_page(self, page_id: str) -> Optional[PageTemplate]:
        """Get page template by ID.

        Args:
            page_id: Page ID to retrieve

        Returns:
            Page template if found, None otherwise
        """
        return self.pages.get(page_id)

    def get_all_pages(self) -> List[PageTemplate]:
        """Get all registered pages.

        Returns:
            List of all page templates
        """
        return list(self.pages.values())

    def get_navigation_structure(self) -> List[Dict[str, Any]]:
        """Get navigation structure for all pages.

        Returns:
            List of navigation items
        """
        navigation = []

        for page in self.pages.values():
            nav_items = page.get_navigation_items()
            navigation.extend(nav_items)

        return navigation


# Global instances
_page_registry: Optional[PageRegistry] = None
_state_manager: Optional[StateManager] = None


def get_page_registry() -> PageRegistry:
    """Get global page registry instance."""
    global _page_registry
    if _page_registry is None:
        _page_registry = PageRegistry()
    return _page_registry


def get_state_manager() -> StateManager:
    """Get global state manager instance."""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager


def register_page(page: PageTemplate) -> None:
    """Register page template globally."""
    get_page_registry().register_page(page)


def get_page(page_id: str) -> Optional[PageTemplate]:
    """Get page template by ID globally."""
    return get_page_registry().get_page(page_id)


# Convenience functions for state management

def get_session_state(key: str, default: Any = None) -> Any:
    """Get session state value."""
    return get_state_manager().get_state(key, default)


def set_session_state(key: str, value: Any, validate: bool = True) -> bool:
    """Set session state value."""
    return get_state_manager().set_state(key, value, validate)


def update_session_state(updates: Dict[str, Any]) -> bool:
    """Update multiple session state values."""
    return get_state_manager().update_state(updates)


def clear_session_state(key: str) -> bool:
    """Clear session state value."""
    return get_state_manager().clear_state(key)


# Error state templates

class ErrorStateTemplate:
    """Templates for error states."""

    @staticmethod
    def render_not_found(resource: str = "Resource") -> None:
        """Render 404 not found state."""
        st.error(f"❌ {resource} Not Found")
        st.info(f"The requested {resource.lower()} could not be found.")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🏠 Go to Dashboard"):
                st.switch_page("main.py")

        with col2:
            if st.button("🔍 Search Again"):
                st.rerun()

    @staticmethod
    def render_access_denied(resource: str = "Resource") -> None:
        """Render 403 access denied state."""
        st.error("🔒 Access Denied")
        st.info(f"You don't have permission to access this {resource.lower()}.")

        if st.button("🔐 Login"):
            st.switch_page("pages/login.py")

    @staticmethod
    def render_server_error(operation: str = "Operation") -> None:
        """Render 500 server error state."""
        st.error("⚠️ Server Error")
        st.info(f"An error occurred during the {operation.lower()}. Please try again.")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔄 Retry"):
                st.rerun()

        with col2:
            if st.button("📞 Contact Support"):
                # Could open support modal or redirect
                st.info("Support contact information would be displayed here.")

    @staticmethod
    def render_loading_state(message: str = "Loading...") -> None:
        """Render loading state."""
        loading = ComponentFactory().get_loading()

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            loading.render_spinner(message)

    @staticmethod
    def render_empty_state(
        title: str = "No Data",
        message: str = "No data to display",
        action_label: str = None,
        action_callback: Callable = None
    ) -> None:
        """Render empty state."""
        st.info(f"📭 {title}")
        st.caption(message)

        if action_label and action_callback:
            if st.button(action_label):
                action_callback()


# Success state templates

class SuccessStateTemplate:
    """Templates for success states."""

    @staticmethod
    def render_operation_success(
        operation: str,
        details: Optional[str] = None,
        next_action: Optional[Dict[str, Any]] = None
    ) -> None:
        """Render successful operation state."""
        st.success(f"✅ {operation} Completed Successfully")

        if details:
            st.info(details)

        if next_action:
            if st.button(next_action['label']):
                if next_action['callback']:
                    next_action['callback']()

    @staticmethod
    def render_data_updated(
        item_type: str = "Data",
        next_steps: Optional[List[str]] = None
    ) -> None:
        """Render data updated state."""
        st.success(f"✅ {item_type} Updated Successfully")

        if next_steps:
            with st.expander("🎯 Next Steps"):
                for step in next_steps:
                    st.markdown(f"• {step}")


# Layout utilities

class LayoutManager:
    """Manager for consistent layout patterns."""

    @staticmethod
    def create_two_column_layout() -> tuple:
        """Create two-column layout.

        Returns:
            Tuple of two column objects
        """
        return st.columns([2, 1])

    @staticmethod
    def create_three_column_layout() -> tuple:
        """Create three-column layout.

        Returns:
            Tuple of three column objects
        """
        return st.columns(3)

    @staticmethod
    def create_dashboard_layout() -> tuple:
        """Create dashboard layout with sidebar and main content.

        Returns:
            Tuple of (sidebar, main_content) columns
        """
        return st.columns([1, 3])

    @staticmethod
    def create_content_with_sidebar(sidebar_content: Callable, main_content: Callable) -> None:
        """Create layout with sidebar and main content.

        Args:
            sidebar_content: Function to render sidebar content
            main_content: Function to render main content
        """
        col1, col2 = st.columns([1, 3])

        with col1:
            sidebar_content()

        with col2:
            main_content()

    @staticmethod
    def create_tabbed_interface(tabs: Dict[str, Callable]) -> Optional[str]:
        """Create tabbed interface.

        Args:
            tabs: Dictionary of tab names to content functions

        Returns:
            Active tab name if available
        """
        tab_names = list(tabs.keys())

        if len(tab_names) == 1:
            # Single tab
            tabs[tab_names[0]]()
            return tab_names[0]

        # Multiple tabs
        selected_tab = st.tabs(tab_names)

        for i, tab_name in enumerate(tab_names):
            with selected_tab[i]:
                tabs[tab_name]()

        return None


# Page-specific templates

class DashboardPageTemplate(PageTemplate):
    """Template for dashboard pages."""

    def get_page_icon(self) -> str:
        return "📊"

    def get_page_description(self) -> str:
        return "Monitor your activities and view key metrics"

    def get_navigation_items(self) -> List[Dict[str, Any]]:
        return [
            {'id': 'overview', 'label': '📈 Overview', 'help': 'Dashboard overview', 'active': True},
            {'id': 'analytics', 'label': '📊 Analytics', 'help': 'Detailed analytics'},
            {'id': 'reports', 'label': '📋 Reports', 'help': 'Generate reports'},
        ]


class FormPageTemplate(PageTemplate):
    """Template for form pages."""

    def get_page_icon(self) -> str:
        return "📝"

    def get_page_description(self) -> str:
        return "Create or edit content"

    def get_quick_actions(self) -> List[Dict[str, Any]]:
        return [
            {'label': '💾 Save Draft', 'action': 'save_draft'},
            {'label': '👁️ Preview', 'action': 'preview'},
            {'label': '📤 Publish', 'action': 'publish'},
        ]


class ListPageTemplate(PageTemplate):
    """Template for list/data pages."""

    def get_page_icon(self) -> str:
        return "📋"

    def get_page_description(self) -> str:
        return "Browse and manage your data"

    def get_quick_actions(self) -> List[Dict[str, Any]]:
        return [
            {'label': '➕ Add New', 'action': 'add_new'},
            {'label': '🔍 Advanced Search', 'action': 'advanced_search'},
            {'label': '📊 Export', 'action': 'export'},
        ]


# Page factory for easy page creation

class PageFactory:
    """Factory for creating page templates."""

    @staticmethod
    def create_dashboard_page(page_id: str, title: str) -> DashboardPageTemplate:
        """Create dashboard page template."""
        return DashboardPageTemplate(page_id, title)

    @staticmethod
    def create_form_page(page_id: str, title: str) -> FormPageTemplate:
        """Create form page template."""
        return FormPageTemplate(page_id, title)

    @staticmethod
    def create_list_page(page_id: str, title: str) -> ListPageTemplate:
        """Create list page template."""
        return ListPageTemplate(page_id, title)

    @staticmethod
    def create_custom_page(
        page_id: str,
        title: str,
        icon: str = "📄",
        base_template: type = PageTemplate
    ) -> PageTemplate:
        """Create custom page template.

        Args:
            page_id: Page identifier
            title: Page title
            icon: Page icon
            base_template: Base template class

        Returns:
            Custom page template
        """
        class CustomPage(base_template):
            def get_page_icon(self) -> str:
                return icon

        return CustomPage(page_id, title)
