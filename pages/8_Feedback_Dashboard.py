# 📊 Feedback Dashboard - Operation Monitoring & Notifications
"""
Dedicated page for comprehensive feedback and operation monitoring.

This page provides:
- Real-time operation status tracking
- User notifications and alerts
- Operation history and analytics
- System health monitoring
"""

import streamlit as st
from feedback_system import (
    show_operation_status_dashboard,
    notification_manager,
    operation_tracker,
    show_enhanced_message
)

def main():
    """Main function for the Feedback Dashboard page."""
    st.set_page_config(page_title="📊 Feedback Dashboard - Archivista AI", page_icon="📊", layout="wide")

    st.title("📊 Feedback e Monitoraggio")
    st.caption("Monitora lo stato di tutte le operazioni e ricevi notifiche in tempo reale")

    # Quick stats
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        active_ops = len(operation_tracker.operations)
        st.metric("🔄 Operazioni Attive", active_ops)

    with col2:
        completed_ops = len(operation_tracker.completed_operations)
        st.metric("✅ Completate Oggi", completed_ops)

    with col3:
        if 'user_notifications' in st.session_state:
            unread = sum(1 for n in st.session_state.user_notifications if not n['read'])
            st.metric("🔔 Notifiche Non Lette", unread)
        else:
            st.metric("🔔 Notifiche Non Lette", 0)

    with col4:
        # System health indicator
        st.metric("💚 Stato Sistema", "Operativo")

    st.markdown("---")

    # Main dashboard content
    show_operation_status_dashboard()

    # Detailed notifications
    st.markdown("### 🔔 Notifiche Dettagliate")
    notification_manager.show_notifications()

    # System information
    with st.expander("ℹ️ Informazioni Sistema", expanded=False):
        st.markdown("**📊 Versione:** Archivista AI v2.4.0 (Alpha 2.4)")
        st.markdown("**🔧 Framework:** Streamlit 1.49.0+")
        st.markdown("**🤖 AI Engine:** LlamaIndex 0.14.4")
        st.markdown("**📦 Task Queue:** Celery 5.5.0 + Redis 5.2.0")

        if st.button("🔍 Diagnostica Sistema"):
            st.switch_page("pages/diagnose_app.py")

if __name__ == "__main__":
    main()
