# 🎯 Enhanced Feedback & Communication System for Archivista AI
"""
Comprehensive feedback system providing:
- Real-time status indicators for all operations
- Actionable success/error messaging
- Progress tracking for long-running operations
- Contextual help integration
- User-friendly notifications and alerts
"""

import streamlit as st
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import threading
import queue

# --- STATUS INDICATOR SYSTEM ---

class StatusIndicator:
    """Enhanced status indicator with visual feedback."""

    def __init__(self, operation_name: str, operation_type: str = "process"):
        self.operation_name = operation_name
        self.operation_type = operation_type
        self.start_time = datetime.now()
        self.status_key = f"status_{operation_name}_{int(time.time())}"

    def show(self, status: str, message: str, progress: float = None, details: str = None):
        """Display enhanced status with visual indicators."""
        status_config = {
            "processing": {"icon": "🔄", "color": "#007bff", "spinner": True},
            "success": {"icon": "✅", "color": "#28a745", "spinner": False},
            "error": {"icon": "❌", "color": "#dc3545", "spinner": False},
            "warning": {"icon": "⚠️", "color": "#ffc107", "spinner": False},
            "info": {"icon": "ℹ️", "color": "#17a2b8", "spinner": False}
        }

        config = status_config.get(status, status_config["info"])

        # Create status container
        with st.container():
            col1, col2 = st.columns([0.1, 0.9])

            with col1:
                if config["spinner"]:
                    st.spinner()
                else:
                    st.markdown(f"**{config['icon']}**")

            with col2:
                st.markdown(f"**{message}**")

                if progress is not None:
                    st.progress(progress, text=f"Completamento: {progress:.1%}")

                if details:
                    with st.expander("🔍 Dettagli"):
                        st.info(details)

                # Show elapsed time for long operations
                elapsed = datetime.now() - self.start_time
                if elapsed.seconds > 2:
                    st.caption(f"⏱️ Tempo trascorso: {elapsed.seconds}s")

# --- OPERATION TRACKER ---

class OperationTracker:
    """Tracks multiple operations with progress monitoring."""

    def __init__(self):
        self.operations = {}
        self.completed_operations = []

    def start_operation(self, operation_id: str, operation_name: str, total_steps: int = None):
        """Start tracking a new operation."""
        self.operations[operation_id] = {
            'name': operation_name,
            'start_time': datetime.now(),
            'current_step': 0,
            'total_steps': total_steps,
            'status': 'running',
            'messages': []
        }

        # Store in session state for persistence
        if 'operation_tracker' not in st.session_state:
            st.session_state.operation_tracker = {}

        st.session_state.operation_tracker[operation_id] = self.operations[operation_id]

    def update_operation(self, operation_id: str, step: int = None, message: str = None, status: str = None):
        """Update operation progress."""
        if operation_id in self.operations:
            if step is not None:
                self.operations[operation_id]['current_step'] = step
            if message:
                self.operations[operation_id]['messages'].append({
                    'timestamp': datetime.now(),
                    'message': message
                })
            if status:
                self.operations[operation_id]['status'] = status

            # Update session state
            st.session_state.operation_tracker[operation_id] = self.operations[operation_id]

    def complete_operation(self, operation_id: str, success: bool = True, final_message: str = None):
        """Mark operation as completed."""
        if operation_id in self.operations:
            self.operations[operation_id]['status'] = 'completed' if success else 'failed'
            self.operations[operation_id]['end_time'] = datetime.now()

            if final_message:
                self.operations[operation_id]['messages'].append({
                    'timestamp': datetime.now(),
                    'message': final_message
                })

            # Move to completed list
            self.completed_operations.append(self.operations[operation_id])
            del self.operations[operation_id]

            # Update session state
            st.session_state.operation_tracker[operation_id] = self.operations.get(operation_id, {})

    def get_operation_status(self, operation_id: str) -> Dict[str, Any]:
        """Get current status of an operation."""
        return self.operations.get(operation_id, {})

    def show_active_operations(self):
        """Display all active operations."""
        if not self.operations:
            return

        st.markdown("### 🔄 Operazioni in Corso")

        for op_id, op_data in self.operations.items():
            with st.expander(f"🔄 {op_data['name']}", expanded=False):
                elapsed = datetime.now() - op_data['start_time']

                st.info(f"**Stato:** In esecuzione da {elapsed.seconds} secondi")

                if op_data['total_steps']:
                    progress = op_data['current_step'] / op_data['total_steps']
                    st.progress(progress, text=f"Passo {op_data['current_step']}/{op_data['total_steps']}")

                # Show recent messages
                if op_data['messages']:
                    recent_messages = op_data['messages'][-3:]  # Last 3 messages
                    for msg in recent_messages:
                        st.caption(f"• {msg['message']}")

# Global operation tracker
operation_tracker = OperationTracker()

# --- ENHANCED MESSAGING SYSTEM ---

def show_enhanced_message(message_type: str, title: str, message: str, actions: List[Dict] = None, duration: int = None):
    """Show enhanced messages with actions and auto-dismiss."""

    message_config = {
        "success": {"icon": "✅", "color": "success", "default_duration": 3},
        "error": {"icon": "❌", "color": "error", "default_duration": 0},  # No auto-dismiss for errors
        "warning": {"icon": "⚠️", "color": "warning", "default_duration": 5},
        "info": {"icon": "ℹ️", "color": "info", "default_duration": 4}
    }

    config = message_config.get(message_type, message_config["info"])

    # Create message container
    message_container = st.container()

    with message_container:
        # Main message
        if message_type == "error":
            st.error(f"**{config['icon']} {title}**")
            st.error(message)
        elif message_type == "warning":
            st.warning(f"**{config['icon']} {title}**")
            st.warning(message)
        elif message_type == "success":
            st.success(f"**{config['icon']} {title}**")
            st.success(message)
        else:
            st.info(f"**{config['icon']} {title}**")
            st.info(message)

        # Action buttons if provided
        if actions:
            cols = st.columns(len(actions))
            for i, action in enumerate(actions):
                with cols[i]:
                    if st.button(
                        action['label'],
                        key=f"action_{message_type}_{i}",
                        use_container_width=True,
                        type="secondary"
                    ):
                        if action.get('page'):
                            st.switch_page(action['page'])
                        elif action.get('action'):
                            st.session_state[f"trigger_{action['action']}"] = True
                            st.rerun()

# --- PROGRESS TRACKING FOR LONG OPERATIONS ---

def track_long_operation(operation_name: str, operation_func: Callable, *args, **kwargs):
    """Track a long-running operation with progress updates."""

    operation_id = f"op_{int(time.time())}"

    # Start operation
    operation_tracker.start_operation(operation_id, operation_name)

    try:
        # Show initial status
        status_indicator = StatusIndicator(operation_name)
        status_indicator.show("processing", f"Avvio {operation_name}...")

        # Execute operation in steps if possible
        if hasattr(operation_func, '__code__') and operation_func.__code__.co_argcount > 1:
            # Function accepts progress callback
            def progress_callback(step, total, message):
                progress = step / total if total > 0 else 0
                operation_tracker.update_operation(operation_id, step, message)
                status_indicator.show("processing", message, progress)

            result = operation_func(progress_callback, *args, **kwargs)
        else:
            # Simple operation
            result = operation_func(*args, **kwargs)

        # Complete successfully
        operation_tracker.complete_operation(operation_id, True, f"{operation_name} completato con successo")
        status_indicator.show("success", f"{operation_name} completato!")

        return result

    except Exception as e:
        # Handle errors
        operation_tracker.complete_operation(operation_id, False, f"Errore in {operation_name}: {str(e)}")
        status_indicator.show("error", f"Errore in {operation_name}", details=str(e))

        # Show enhanced error message
        show_enhanced_message("error",
                            f"Errore in {operation_name}",
                            str(e),
                            actions=[{"label": "🔄 Riprova", "action": "retry_operation"}])
        raise

# --- CONTEXTUAL HELP BUTTONS ---

def add_contextual_help_button(context: str, label: str = "❓ Aiuto", size: str = "small"):
    """Add a contextual help button that shows relevant guidance."""

    button_cols = st.columns([0.3, 0.7]) if size == "large" else st.columns([0.15, 0.85])

    with button_cols[0]:
        if st.button(label, key=f"help_{context}", help=f"Mostra guida per: {context}"):
            st.session_state[f"show_help_{context}"] = not st.session_state.get(f"show_help_{context}", False)

    with button_cols[1]:
        if st.session_state.get(f"show_help_{context}", False):
            from ux_components import show_contextual_help
            show_contextual_help(context)

# --- NOTIFICATION SYSTEM ---

class NotificationManager:
    """Manages user notifications and alerts."""

    def __init__(self):
        self.notifications_key = "user_notifications"

    def add_notification(self, type: str, title: str, message: str, priority: str = "normal"):
        """Add a new notification."""
        if self.notifications_key not in st.session_state:
            st.session_state[self.notifications_key] = []

        notification = {
            'id': f"notif_{int(time.time())}_{len(st.session_state[self.notifications_key])}",
            'type': type,
            'title': title,
            'message': message,
            'priority': priority,
            'timestamp': datetime.now(),
            'read': False
        }

        st.session_state[self.notifications_key].insert(0, notification)

        # Keep only last 50 notifications
        if len(st.session_state[self.notifications_key]) > 50:
            st.session_state[self.notifications_key] = st.session_state[self.notifications_key][:50]

    def show_notifications(self):
        """Display user notifications."""
        if self.notifications_key not in st.session_state:
            return

        notifications = st.session_state[self.notifications_key]

        if not notifications:
            return

        # Show unread count
        unread_count = sum(1 for n in notifications if not n['read'])

        if unread_count > 0:
            st.markdown(f"### 🔔 Notifiche ({unread_count} non lette)")

            for notification in notifications[:5]:  # Show last 5
                with st.expander(
                    f"{'🆕' if not notification['read'] else '📖'} {notification['title']}",
                    expanded=not notification['read']
                ):
                    st.markdown(f"**{notification['message']}**")
                    st.caption(f"📅 {notification['timestamp'].strftime('%d/%m/%Y %H:%M')}")

                    if not notification['read']:
                        if st.button("✅ Marca come letta", key=f"read_{notification['id']}"):
                            notification['read'] = True
                            st.rerun()

# Global notification manager
notification_manager = NotificationManager()

# --- OPERATION STATUS DASHBOARD ---

def show_operation_status_dashboard():
    """Show a dashboard of all operations and their status."""
    st.markdown("### 📊 Stato Operazioni")

    # Active operations
    operation_tracker.show_active_operations()

    # Recent completed operations
    if operation_tracker.completed_operations:
        with st.expander("📋 Operazioni Recenti", expanded=False):
            for op in operation_tracker.completed_operations[-5:]:  # Last 5
                status_icon = "✅" if op['status'] == 'completed' else "❌"
                elapsed = op.get('end_time', datetime.now()) - op['start_time']

                st.markdown(f"**{status_icon} {op['name']}**")
                st.caption(f"⏱️ Durata: {elapsed.seconds}s | 📅 {op['start_time'].strftime('%H:%M:%S')}")

                if op['messages']:
                    for msg in op['messages'][-2:]:  # Last 2 messages
                        st.caption(f"• {msg['message']}")

# --- ENHANCED ERROR HANDLING ---

def handle_operation_error(operation_name: str, error: Exception, context: str = None):
    """Handle operation errors with enhanced feedback."""

    error_message = f"Errore durante {operation_name}: {str(error)}"

    # Log error details
    print(f"Operation Error - {operation_name}: {error}")
    if context:
        print(f"Context: {context}")

    # Show enhanced error message
    show_enhanced_message("error",
                         f"Errore in {operation_name}",
                         str(error),
                         actions=[
                             {"label": "🔄 Riprova", "action": "retry_operation"},
                             {"label": "📖 Guida", "action": "show_help"}
                         ])

    # Add to notifications
    notification_manager.add_notification(
        "error",
        f"Errore in {operation_name}",
        str(error),
        priority="high"
    )

# --- SUCCESS FEEDBACK WITH ACTIONS ---

def show_success_with_actions(title: str, message: str, actions: List[Dict] = None, notification: bool = True):
    """Show success message with follow-up actions."""

    # Show enhanced success message
    show_enhanced_message("success", title, message, actions)

    # Add to notifications if requested
    if notification:
        notification_manager.add_notification(
            "success",
            title,
            message,
            priority="normal"
        )

# --- PROGRESS CONTEXT MANAGER ---

class ProgressContext:
    """Context manager for tracking operation progress."""

    def __init__(self, operation_name: str, total_steps: int = None):
        self.operation_name = operation_name
        self.total_steps = total_steps
        self.current_step = 0
        self.operation_id = None

    def __enter__(self):
        self.operation_id = f"ctx_{int(time.time())}"
        operation_tracker.start_operation(self.operation_id, self.operation_name, self.total_steps)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            operation_tracker.complete_operation(self.operation_id, False, f"Errore: {str(exc_val)}")
        else:
            operation_tracker.complete_operation(self.operation_id, True, f"{self.operation_name} completato")

    def update(self, step: int = None, message: str = None):
        """Update progress."""
        if step is not None:
            self.current_step = step
        if message:
            operation_tracker.update_operation(self.operation_id, self.current_step, message)

# --- INTEGRATION HELPERS ---

def with_progress_tracking(operation_name: str, total_steps: int = None):
    """Decorator for adding progress tracking to functions."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with ProgressContext(operation_name, total_steps) as progress:
                return func(progress, *args, **kwargs)
        return wrapper
    return decorator

def show_feedback_sidebar():
    """Show a sidebar with operation status and notifications."""
    with st.sidebar:
        st.markdown("### 📊 Stato Sistema")

        # Show active operations
        operation_tracker.show_active_operations()

        # Show notifications
        notification_manager.show_notifications()

        # Quick actions
        st.markdown("---")
        st.markdown("### 🚀 Azioni Rapide")

        if st.button("🎯 Workflow Wizards", use_container_width=True):
            st.switch_page("pages/7_Workflow_Wizards.py")

        if st.button("📚 Archivio", use_container_width=True):
            st.switch_page("pages/2_Archivio.py")

# --- MAIN INTERFACE ---

def render_feedback_dashboard():
    """Main page for feedback and operation monitoring."""
    st.set_page_config(page_title="📊 Feedback Dashboard - Archivista AI", page_icon="📊", layout="wide")

    st.title("📊 Feedback e Monitoraggio")
    st.caption("Monitora lo stato di tutte le operazioni e ricevi notifiche")

    # Show comprehensive dashboard
    show_operation_status_dashboard()

    # Show notifications
    notification_manager.show_notifications()

# Export main functions
__all__ = [
    'StatusIndicator',
    'OperationTracker',
    'operation_tracker',
    'show_enhanced_message',
    'track_long_operation',
    'add_contextual_help_button',
    'NotificationManager',
    'notification_manager',
    'show_operation_status_dashboard',
    'handle_operation_error',
    'show_success_with_actions',
    'ProgressContext',
    'with_progress_tracking',
    'show_feedback_sidebar',
    'render_feedback_dashboard'
]

if __name__ == "__main__":
    render_feedback_dashboard()
