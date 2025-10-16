"""
Base UI components for Archivista AI.
Provides consistent styling and behavior across all UI elements.
"""

import streamlit as st
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
import logging


@dataclass
class ComponentConfig:
    """Configuration for UI components."""
    primary_color: str = "#1f77b4"
    secondary_color: str = "#ff7f0e"
    success_color: str = "#2ca02c"
    warning_color: str = "#ff9896"
    danger_color: str = "#d62728"
    background_color: str = "#ffffff"
    text_color: str = "#333333"
    border_radius: str = "8px"
    font_family: str = "Inter, sans-serif"
    font_size_base: str = "14px"
    spacing_unit: str = "1rem"


class BaseComponent:
    """Base class for all UI components."""

    def __init__(self, config: Optional[ComponentConfig] = None):
        """Initialize base component.

        Args:
            config: Component configuration
        """
        self.config = config or ComponentConfig()
        self.logger = logging.getLogger(__name__)

    def apply_base_styles(self) -> None:
        """Apply base styles to the component."""
        st.markdown(f"""
        <style>
        .base-component {{
            font-family: {self.config.font_family};
            font-size: {self.config.font_size_base};
            color: {self.config.text_color};
        }}
        </style>
        """, unsafe_allow_html=True)


class ButtonComponent(BaseComponent):
    """Enhanced button component with consistent styling."""

    def render(
        self,
        label: str,
        key: str,
        on_click: Optional[Callable] = None,
        button_type: str = "primary",
        size: str = "medium",
        disabled: bool = False,
        icon: Optional[str] = None,
        help_text: Optional[str] = None,
        full_width: bool = False
    ) -> bool:
        """Render enhanced button.

        Args:
            label: Button label
            key: Unique key for Streamlit
            on_click: Click handler function
            button_type: Type of button (primary, secondary, success, warning, danger)
            size: Button size (small, medium, large)
            disabled: Whether button is disabled
            icon: Icon to display
            help_text: Help text for tooltip
            full_width: Whether button should take full width

        Returns:
            True if button was clicked
        """
        # Apply base styles
        self.apply_base_styles()

        # Determine button styling
        button_styles = {
            'primary': f"""
                background-color: {self.config.primary_color};
                color: white;
                border: none;
                padding: 0.5rem 1rem;
                border-radius: {self.config.border_radius};
                font-weight: 500;
                cursor: pointer;
            """,
            'secondary': f"""
                background-color: transparent;
                color: {self.config.primary_color};
                border: 2px solid {self.config.primary_color};
                padding: 0.5rem 1rem;
                border-radius: {self.config.border_radius};
                font-weight: 500;
                cursor: pointer;
            """,
            'success': f"""
                background-color: {self.config.success_color};
                color: white;
                border: none;
                padding: 0.5rem 1rem;
                border-radius: {self.config.border_radius};
                font-weight: 500;
                cursor: pointer;
            """,
            'warning': f"""
                background-color: {self.config.warning_color};
                color: white;
                border: none;
                padding: 0.5rem 1rem;
                border-radius: {self.config.border_radius};
                font-weight: 500;
                cursor: pointer;
            """,
            'danger': f"""
                background-color: {self.config.danger_color};
                color: white;
                border: none;
                padding: 0.5rem 1rem;
                border-radius: {self.config.border_radius};
                font-weight: 500;
                cursor: pointer;
            """
        }

        # Size adjustments
        size_adjustments = {
            'small': 'padding: 0.25rem 0.5rem; font-size: 0.875rem;',
            'medium': 'padding: 0.5rem 1rem; font-size: 1rem;',
            'large': 'padding: 0.75rem 1.5rem; font-size: 1.125rem;'
        }

        # Combine styles
        style = button_styles.get(button_type, button_styles['primary'])
        style += size_adjustments.get(size, size_adjustments['medium'])

        if full_width:
            style += 'width: 100%;'

        if disabled:
            style += 'opacity: 0.6; cursor: not-allowed;'

        # Create button with custom styling
        button_html = f"""
        <button
            class="styled-button"
            style="{style}"
            onclick="this.disabled=true; this.style.opacity='0.6';"
            {f'disabled' if disabled else ''}
        >
            {f'{icon} ' if icon else ''}{label}
        </button>
        """

        # Add custom CSS
        st.markdown("""
        <style>
        .styled-button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .styled-button:active {
            transform: translateY(0);
        }
        </style>
        """, unsafe_allow_html=True)

        # Render button
        if on_click:
            clicked = st.button(
                label,
                key=key,
                disabled=disabled,
                help=help_text,
                on_click=on_click
            )
        else:
            clicked = st.button(
                label,
                key=key,
                disabled=disabled,
                help=help_text
            )

        return clicked


class CardComponent(BaseComponent):
    """Card component for content organization."""

    def render(
        self,
        title: str,
        content: str,
        key: str,
        icon: Optional[str] = None,
        actions: Optional[List[Dict[str, Any]]] = None,
        collapsible: bool = False,
        default_expanded: bool = True
    ) -> None:
        """Render card component.

        Args:
            title: Card title
            content: Card content
            key: Unique key for Streamlit
            icon: Icon to display in header
            actions: List of action buttons
            collapsible: Whether card is collapsible
            default_expanded: Default expanded state
        """
        # Apply base styles
        self.apply_base_styles()

        # Card styling
        card_style = f"""
        background-color: {self.config.background_color};
        border: 1px solid #e0e0e0;
        border-radius: {self.config.border_radius};
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        """

        # Header styling
        header_style = """
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #e0e0e0;
        """

        # Content styling
        content_style = """
        line-height: 1.6;
        color: #555;
        """

        # Create card HTML
        header_html = f"""
        <div style="{header_style}">
            {f'<span style="margin-right: 0.5rem;">{icon}</span>' if icon else ''}
            <h3 style="margin: 0; color: {self.config.text_color}; font-size: 1.25rem;">
                {title}
            </h3>
        </div>
        """

        content_html = f"""
        <div style="{content_style}">
            {content}
        </div>
        """

        # Add actions if provided
        if actions:
            actions_html = self._render_card_actions(actions)
            content_html += actions_html

        # Combine card elements
        card_html = f"""
        <div style="{card_style}">
            {header_html}
            {content_html}
        </div>
        """

        # Render with Streamlit
        if collapsible:
            with st.expander(title, expanded=default_expanded):
                st.markdown(content, unsafe_allow_html=True)
                if actions:
                    self._render_action_buttons(actions, key)
        else:
            st.markdown(card_html, unsafe_allow_html=True)

    def _render_card_actions(self, actions: List[Dict[str, Any]]) -> str:
        """Render action buttons for card."""
        actions_html = """
        <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #e0e0e0;">
        """

        for action in actions:
            button = ButtonComponent()
            if button.render(
                action['label'],
                f"{action.get('key', 'action')}_btn",
                on_click=action.get('on_click'),
                button_type=action.get('type', 'primary'),
                size=action.get('size', 'medium'),
                icon=action.get('icon'),
                help_text=action.get('help')
            ):
                if action.get('on_click'):
                    action['on_click']()

        actions_html += "</div>"
        return actions_html

    def _render_action_buttons(self, actions: List[Dict[str, Any]], key_prefix: str) -> None:
        """Render action buttons using Streamlit."""
        cols = st.columns(len(actions))

        for i, action in enumerate(actions):
            with cols[i]:
                if st.button(
                    action['label'],
                    key=f"{key_prefix}_{action.get('key', f'action_{i}')}",
                    help=action.get('help')
                ):
                    if action.get('on_click'):
                        action['on_click']()


class FormComponent(BaseComponent):
    """Form component with validation and consistent styling."""

    def render(
        self,
        fields: List[Dict[str, Any]],
        submit_label: str = "Submit",
        key: str = "form",
        on_submit: Optional[Callable] = None
    ) -> Optional[Dict[str, Any]]:
        """Render form component.

        Args:
            fields: List of field configurations
            submit_label: Submit button label
            key: Form key
            on_submit: Submit handler

        Returns:
            Form data if submitted, None otherwise
        """
        # Apply base styles
        self.apply_base_styles()

        # Form styling
        form_style = f"""
        background-color: {self.config.background_color};
        border: 1px solid #e0e0e0;
        border-radius: {self.config.border_radius};
        padding: 1.5rem;
        margin: 1rem 0;
        """

        st.markdown(f"""
        <style>
        .form-field {{
            margin-bottom: 1rem;
        }}
        .form-field label {{
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
            color: {self.config.text_color};
        }}
        .form-field input, .form-field select, .form-field textarea {{
            width: 100%;
            padding: 0.5rem;
            border: 1px solid #ddd;
            border-radius: {self.config.border_radius};
            font-family: {self.config.font_family};
            font-size: {self.config.font_size_base};
        }}
        .form-field input:focus, .form-field select:focus, .form-field textarea:focus {{
            outline: none;
            border-color: {self.config.primary_color};
            box-shadow: 0 0 0 2px rgba(31, 119, 180, 0.2);
        }}
        .error-message {{
            color: {self.config.danger_color};
            font-size: 0.875rem;
            margin-top: 0.25rem;
        }}
        </style>
        """, unsafe_allow_html=True)

        # Render form with Streamlit
        with st.form(key=key):
            form_data = {}

            for field in fields:
                field_name = field['name']
                field_type = field['type']
                field_label = field['label']
                required = field.get('required', False)

                # Render different field types
                if field_type == 'text':
                    value = st.text_input(
                        field_label,
                        value=field.get('default', ''),
                        key=f"{key}_{field_name}",
                        help=field.get('help')
                    )
                elif field_type == 'password':
                    value = st.text_input(
                        field_label,
                        type='password',
                        key=f"{key}_{field_name}",
                        help=field.get('help')
                    )
                elif field_type == 'email':
                    value = st.text_input(
                        field_label,
                        value=field.get('default', ''),
                        key=f"{key}_{field_name}",
                        help=field.get('help')
                    )
                elif field_type == 'number':
                    value = st.number_input(
                        field_label,
                        value=field.get('default', 0),
                        key=f"{key}_{field_name}",
                        help=field.get('help')
                    )
                elif field_type == 'select':
                    value = st.selectbox(
                        field_label,
                        options=field['options'],
                        index=field.get('default_index', 0),
                        key=f"{key}_{field_name}",
                        help=field.get('help')
                    )
                elif field_type == 'multiselect':
                    default = field.get('default', [])
                    if isinstance(default, str):
                        default = [default]
                    value = st.multiselect(
                        field_label,
                        options=field['options'],
                        default=default,
                        key=f"{key}_{field_name}",
                        help=field.get('help')
                    )
                elif field_type == 'textarea':
                    value = st.text_area(
                        field_label,
                        value=field.get('default', ''),
                        height=field.get('height', 100),
                        key=f"{key}_{field_name}",
                        help=field.get('help')
                    )
                elif field_type == 'checkbox':
                    value = st.checkbox(
                        field_label,
                        value=field.get('default', False),
                        key=f"{key}_{field_name}",
                        help=field.get('help')
                    )
                elif field_type == 'date':
                    value = st.date_input(
                        field_label,
                        value=field.get('default'),
                        key=f"{key}_{field_name}",
                        help=field.get('help')
                    )
                elif field_type == 'file':
                    value = st.file_uploader(
                        field_label,
                        type=field.get('accepted_types', None),
                        key=f"{key}_{field_name}",
                        help=field.get('help')
                    )
                else:
                    st.error(f"Unsupported field type: {field_type}")
                    continue

                form_data[field_name] = value

                # Show validation errors
                if required and not value:
                    st.error(f"{field_label} is required")

            # Submit button
            submitted = st.form_submit_button(
                submit_label,
                type="primary"
            )

            if submitted:
                # Validate required fields
                is_valid = True
                for field in fields:
                    field_name = field['name']
                    required = field.get('required', False)

                    if required and not form_data.get(field_name):
                        is_valid = False
                        break

                if is_valid:
                    if on_submit:
                        on_submit(form_data)
                    return form_data

        return None


class AlertComponent(BaseComponent):
    """Alert component for notifications and messages."""

    def render(
        self,
        message: str,
        alert_type: str = "info",
        key: str = "alert",
        dismissible: bool = False,
        icon: Optional[str] = None
    ) -> None:
        """Render alert component.

        Args:
            message: Alert message
            alert_type: Type of alert (info, success, warning, error)
            key: Unique key
            dismissible: Whether alert can be dismissed
            icon: Icon to display
        """
        # Alert styling based on type
        alert_styles = {
            'info': f"""
                background-color: #e3f2fd;
                border-left: 4px solid {self.config.primary_color};
                color: #1565c0;
            """,
            'success': f"""
                background-color: #e8f5e8;
                border-left: 4px solid {self.config.success_color};
                color: #2e7d32;
            """,
            'warning': f"""
                background-color: #fff3e0;
                border-left: 4px solid #ff9800;
                color: #ef6c00;
            """,
            'error': f"""
                background-color: #ffebee;
                border-left: 4px solid {self.config.danger_color};
                color: #c62828;
            """
        }

        style = alert_styles.get(alert_type, alert_styles['info'])

        # Create alert HTML
        icon_html = f'<span style="margin-right: 0.5rem;">{icon}</span>' if icon else ''

        alert_html = f"""
        <div style="
            padding: 1rem;
            margin: 1rem 0;
            border-radius: {self.config.border_radius};
            {style}
        ">
            {icon_html}{message}
        </div>
        """

        st.markdown(alert_html, unsafe_allow_html=True)

        # Add dismiss button if dismissible
        if dismissible:
            if st.button("✕", key=f"{key}_dismiss", help="Dismiss alert"):
                st.rerun()


class ProgressComponent(BaseComponent):
    """Progress component for showing loading states."""

    def render(
        self,
        progress: float,
        message: str = "Processing...",
        key: str = "progress",
        show_percentage: bool = True
    ) -> None:
        """Render progress component.

        Args:
            progress: Progress value (0.0 to 1.0)
            message: Progress message
            key: Unique key
            show_percentage: Whether to show percentage
        """
        # Progress bar styling
        progress_style = f"""
        .progress-bar {{
            width: 100%;
            height: 20px;
            background-color: #f0f0f0;
            border-radius: {self.config.border_radius};
            overflow: hidden;
        }}
        .progress-fill {{
            height: 100%;
            background-color: {self.config.primary_color};
            width: {progress * 100}%;
            transition: width 0.3s ease;
        }}
        """

        st.markdown(f"<style>{progress_style}</style>", unsafe_allow_html=True)

        # Progress bar HTML
        progress_html = f"""
        <div class="progress-bar">
            <div class="progress-fill"></div>
        </div>
        """

        st.markdown(progress_html, unsafe_allow_html=True)

        # Progress text
        percentage_text = f" ({progress * 100".1f"}%)" if show_percentage else ""
        st.caption(f"{message}{percentage_text}")


class TableComponent(BaseComponent):
    """Table component with sorting and filtering."""

    def render(
        self,
        data: List[Dict[str, Any]],
        columns: List[Dict[str, Any]],
        key: str = "table",
        sortable: bool = True,
        filterable: bool = False,
        pagination: bool = True,
        page_size: int = 20
    ) -> None:
        """Render table component.

        Args:
            data: Table data
            columns: Column configurations
            key: Unique key
            sortable: Whether table is sortable
            filterable: Whether table is filterable
            pagination: Whether to use pagination
            page_size: Items per page
        """
        if not data:
            st.info("No data to display")
            return

        # Convert to DataFrame for easier manipulation
        import pandas as pd

        df = pd.DataFrame(data)

        # Apply filters if enabled
        if filterable:
            df = self._apply_table_filters(df, columns, key)

        # Apply sorting if enabled
        if sortable:
            df = self._apply_table_sorting(df, columns, key)

        # Apply pagination if enabled
        if pagination:
            df = self._apply_table_pagination(df, page_size, key)
        else:
            # Show all data
            st.dataframe(df, use_container_width=True)
            return

        # Render table
        st.dataframe(df, use_container_width=True)

    def _apply_table_filters(self, df: pd.DataFrame, columns: List[Dict[str, Any]], key: str) -> pd.DataFrame:
        """Apply filters to table data."""
        # Create filter inputs for each column
        filters = {}

        with st.expander("🔍 Filters", expanded=False):
            filter_cols = st.columns(len(columns))

            for i, column in enumerate(columns):
                with filter_cols[i]:
                    col_name = column['name']
                    col_type = column.get('type', 'text')

                    if col_type == 'text':
                        filter_value = st.text_input(
                            f"Filter {col_name}",
                            key=f"{key}_filter_{col_name}",
                            placeholder=f"Search {col_name}..."
                        )
                    elif col_type == 'select':
                        options = column.get('filter_options', df[col_name].unique())
                        filter_value = st.selectbox(
                            f"Filter {col_name}",
                            ['All'] + list(options),
                            key=f"{key}_filter_{col_name}"
                        )
                    else:
                        filter_value = None

                    filters[col_name] = filter_value

        # Apply filters
        filtered_df = df.copy()
        for col_name, filter_value in filters.items():
            if filter_value and filter_value != 'All':
                if isinstance(filter_value, str):
                    filtered_df = filtered_df[
                        filtered_df[col_name].astype(str).str.contains(filter_value, case=False, na=False)
                    ]
                else:
                    filtered_df = filtered_df[filtered_df[col_name] == filter_value]

        return filtered_df

    def _apply_table_sorting(self, df: pd.DataFrame, columns: List[Dict[str, Any]], key: str) -> pd.DataFrame:
        """Apply sorting to table data."""
        # Sort options
        sort_column = st.selectbox(
            "Sort by",
            [col['name'] for col in columns],
            key=f"{key}_sort_column"
        )

        sort_order = st.radio(
            "Order",
            ['Ascending', 'Descending'],
            key=f"{key}_sort_order",
            horizontal=True
        )

        if sort_column:
            ascending = sort_order == 'Ascending'
            df = df.sort_values(sort_column, ascending=ascending)

        return df

    def _apply_table_pagination(self, df: pd.DataFrame, page_size: int, key: str) -> pd.DataFrame:
        """Apply pagination to table data."""
        total_rows = len(df)
        total_pages = (total_rows + page_size - 1) // page_size

        if total_pages <= 1:
            return df

        # Page selector
        page = st.selectbox(
            "Page",
            range(1, total_pages + 1),
            key=f"{key}_page",
            format_func=lambda x: f"Page {x} of {total_pages}"
        )

        # Calculate slice indices
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_rows)

        return df.iloc[start_idx:end_idx]


class ModalComponent(BaseComponent):
    """Modal dialog component."""

    def __init__(self, config: Optional[ComponentConfig] = None):
        """Initialize modal component."""
        super().__init__(config)
        self._modals: Dict[str, Dict[str, Any]] = {}

    def show_modal(
        self,
        title: str,
        content: str,
        key: str,
        size: str = "medium",
        confirm_button: Optional[str] = None,
        cancel_button: Optional[str] = None,
        on_confirm: Optional[Callable] = None,
        on_cancel: Optional[Callable] = None
    ) -> Optional[bool]:
        """Show modal dialog.

        Args:
            title: Modal title
            content: Modal content
            key: Unique key
            size: Modal size (small, medium, large)
            confirm_button: Confirm button label
            cancel_button: Cancel button label
            on_confirm: Confirm handler
            on_cancel: Cancel handler

        Returns:
            True if confirmed, False if cancelled, None if still open
        """
        # Modal sizing
        size_styles = {
            'small': 'width: 400px;',
            'medium': 'width: 600px;',
            'large': 'width: 800px;'
        }

        modal_style = f"""
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        padding: 2rem;
        border-radius: {self.config.border_radius};
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        z-index: 1000;
        {size_styles.get(size, size_styles['medium'])}
        """

        # Backdrop style
        backdrop_style = """
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        z-index: 999;
        """

        # Show modal if triggered
        if st.session_state.get(f"{key}_show_modal", False):
            # Create backdrop
            st.markdown(
                f'<div style="{backdrop_style}"></div>',
                unsafe_allow_html=True
            )

            # Create modal content
            with st.container():
                st.markdown(
                    f'<div style="{modal_style}">',
                    unsafe_allow_html=True
                )

                # Modal header
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.subheader(title)
                with col2:
                    if st.button("✕", key=f"{key}_close"):
                        st.session_state[f"{key}_show_modal"] = False
                        st.rerun()

                st.markdown("---")

                # Modal content
                st.markdown(content)

                # Modal footer with buttons
                if confirm_button or cancel_button:
                    st.markdown("---")
                    cols = st.columns(2)

                    result = None

                    with cols[0]:
                        if cancel_button and st.button(
                            cancel_button,
                            key=f"{key}_cancel",
                            type="secondary"
                        ):
                            st.session_state[f"{key}_show_modal"] = False
                            if on_cancel:
                                on_cancel()
                            result = False
                            st.rerun()

                    with cols[1]:
                        if confirm_button and st.button(
                            confirm_button,
                            key=f"{key}_confirm",
                            type="primary"
                        ):
                            st.session_state[f"{key}_show_modal"] = False
                            if on_confirm:
                                on_confirm()
                            result = True
                            st.rerun()

                    return result

                st.markdown('</div>', unsafe_allow_html=True)

        return None

    def open_modal(self, key: str) -> None:
        """Open modal dialog."""
        st.session_state[f"{key}_show_modal"] = True

    def close_modal(self, key: str) -> None:
        """Close modal dialog."""
        st.session_state[f"{key}_show_modal"] = False


class NavigationComponent(BaseComponent):
    """Navigation component for consistent navigation."""

    def render_sidebar(self, items: List[Dict[str, Any]], key: str = "sidebar") -> Optional[str]:
        """Render navigation sidebar.

        Args:
            items: Navigation items
            key: Sidebar key

        Returns:
            Selected navigation item
        """
        st.sidebar.title("🧭 Navigation")

        selected_item = None

        for item in items:
            if st.sidebar.button(
                item['label'],
                key=f"{key}_{item['id']}",
                help=item.get('help'),
                type="primary" if item.get('active', False) else "secondary"
            ):
                selected_item = item['id']

        return selected_item

    def render_breadcrumbs(self, breadcrumbs: List[Dict[str, Any]]) -> None:
        """Render breadcrumb navigation.

        Args:
            breadcrumbs: List of breadcrumb items
        """
        if not breadcrumbs:
            return

        breadcrumb_html = """
        <div style="
            display: flex;
            align-items: center;
            margin-bottom: 1rem;
            font-size: 0.875rem;
        ">
        """

        for i, crumb in enumerate(breadcrumbs):
            if i > 0:
                breadcrumb_html += """
                <span style="margin: 0 0.5rem; color: #666;">›</span>
                """

            if i == len(breadcrumbs) - 1:
                # Last item - not clickable
                breadcrumb_html += f"""
                <span style="color: {self.config.text_color}; font-weight: 500;">
                    {crumb['label']}
                </span>
                """
            else:
                # Clickable items
                breadcrumb_html += f"""
                <a href="#" style="
                    color: {self.config.primary_color};
                    text-decoration: none;
                " onclick="window.parent.postMessage({{'type': 'navigate', 'path': '{crumb['path']}'}}, '*')">
                    {crumb['label']}
                </a>
                """

        breadcrumb_html += "</div>"

        st.markdown(breadcrumb_html, unsafe_allow_html=True)


class LoadingComponent(BaseComponent):
    """Loading component for async operations."""

    def render_spinner(self, message: str = "Loading...", key: str = "spinner") -> None:
        """Render loading spinner.

        Args:
            message: Loading message
            key: Unique key
        """
        st.spinner(message)

    def render_skeleton(self, rows: int = 3, key: str = "skeleton") -> None:
        """Render skeleton loading placeholder.

        Args:
            rows: Number of skeleton rows
            key: Unique key
        """
        skeleton_style = f"""
        .skeleton {{
            background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
            background-size: 200% 100%;
            animation: loading 1.5s infinite;
            border-radius: {self.config.border_radius};
            height: 20px;
            margin: 0.5rem 0;
        }}
        @keyframes loading {{
            0% {{ background-position: 200% 0; }}
            100% {{ background-position: -200% 0; }}
        }}
        """

        st.markdown(f"<style>{skeleton_style}</style>", unsafe_allow_html=True)

        for i in range(rows):
            st.markdown(
                f'<div class="skeleton" style="width: {80 + (i * 10)}%;"></div>',
                unsafe_allow_html=True
            )


class NotificationComponent(BaseComponent):
    """Notification component for user feedback."""

    def __init__(self, config: Optional[ComponentConfig] = None):
        """Initialize notification component."""
        super().__init__(config)
        self.notifications: List[Dict[str, Any]] = []

    def show_success(self, message: str, duration: int = 3) -> None:
        """Show success notification."""
        self.notifications.append({
            'type': 'success',
            'message': message,
            'duration': duration,
            'timestamp': st.session_state.get('timestamp', 0)
        })
        st.success(message)

    def show_error(self, message: str, duration: int = 5) -> None:
        """Show error notification."""
        self.notifications.append({
            'type': 'error',
            'message': message,
            'duration': duration,
            'timestamp': st.session_state.get('timestamp', 0)
        })
        st.error(message)

    def show_warning(self, message: str, duration: int = 4) -> None:
        """Show warning notification."""
        self.notifications.append({
            'type': 'warning',
            'message': message,
            'duration': duration,
            'timestamp': st.session_state.get('timestamp', 0)
        })
        st.warning(message)

    def show_info(self, message: str, duration: int = 3) -> None:
        """Show info notification."""
        self.notifications.append({
            'type': 'info',
            'message': message,
            'duration': duration,
            'timestamp': st.session_state.get('timestamp', 0)
        })
        st.info(message)

    def render_toast(self, message: str, type: str = "info", duration: int = 3) -> None:
        """Render toast notification.

        Args:
            message: Toast message
            type: Toast type (info, success, warning, error)
            duration: Display duration in seconds
        """
        # Toast styling
        toast_styles = {
            'info': f'background-color: #e3f2fd; color: #1565c0; border-left: 4px solid {self.config.primary_color};',
            'success': f'background-color: #e8f5e8; color: #2e7d32; border-left: 4px solid {self.config.success_color};',
            'warning': f'background-color: #fff3e0; color: #ef6c00; border-left: 4px solid #ff9800;',
            'error': f'background-color: #ffebee; color: #c62828; border-left: 4px solid {self.config.danger_color};'
        }

        style = toast_styles.get(type, toast_styles['info'])

        toast_html = f"""
        <div style="
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            border-radius: {self.config.border_radius};
            {style}
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1001;
            max-width: 400px;
            animation: slideIn 0.3s ease-out;
        " id="toast">
            <div style="display: flex; align-items: center;">
                <span>{message}</span>
                <button onclick="this.parentElement.parentElement.style.display='none'"
                        style="
                            background: none;
                            border: none;
                            color: inherit;
                            cursor: pointer;
                            margin-left: auto;
                            font-size: 1.2rem;
                        ">✕</button>
            </div>
        </div>

        <style>
        @keyframes slideIn {{
            from {{
                transform: translateX(100%);
                opacity: 0;
            }}
            to {{
                transform: translateX(0);
                opacity: 1;
            }}
        }}
        </style>
        """

        # Use Streamlit's toast for now (can be enhanced with custom HTML)
        if type == 'success':
            st.success(message)
        elif type == 'error':
            st.error(message)
        elif type == 'warning':
            st.warning(message)
        else:
            st.info(message)


# Component factory for easy access

class ComponentFactory:
    """Factory for creating UI components."""

    @staticmethod
    def get_button(config: Optional[ComponentConfig] = None) -> ButtonComponent:
        """Get button component instance."""
        return ButtonComponent(config)

    @staticmethod
    def get_card(config: Optional[ComponentConfig] = None) -> CardComponent:
        """Get card component instance."""
        return CardComponent(config)

    @staticmethod
    def get_form(config: Optional[ComponentConfig] = None) -> FormComponent:
        """Get form component instance."""
        return FormComponent(config)

    @staticmethod
    def get_alert(config: Optional[ComponentConfig] = None) -> AlertComponent:
        """Get alert component instance."""
        return AlertComponent(config)

    @staticmethod
    def get_table(config: Optional[ComponentConfig] = None) -> TableComponent:
        """Get table component instance."""
        return TableComponent(config)

    @staticmethod
    def get_modal(config: Optional[ComponentConfig] = None) -> ModalComponent:
        """Get modal component instance."""
        return ModalComponent(config)

    @staticmethod
    def get_navigation(config: Optional[ComponentConfig] = None) -> NavigationComponent:
        """Get navigation component instance."""
        return NavigationComponent(config)

    @staticmethod
    def get_loading(config: Optional[ComponentConfig] = None) -> LoadingComponent:
        """Get loading component instance."""
        return LoadingComponent(config)

    @staticmethod
    def get_notification(config: Optional[ComponentConfig] = None) -> NotificationComponent:
        """Get notification component instance."""
        return NotificationComponent(config)
