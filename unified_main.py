#!/usr/bin/env python3
"""
Archivista AI - Main Unificata (Prototipo Settimana 1)

Questa è la nuova main unificata che utilizza l'architettura modulare
per sostituire gradualmente le 12 pagine sparse esistenti.

Layout iniziale: Minimalista con chat centrale e componenti base.
"""

import streamlit as st
import logging
from datetime import datetime

# Import nuova architettura
from src.ui.components import (
    create_collapsible_sidebar,
    create_modal_login,
    create_minimal_chat,
    create_file_context_manager,
    create_header_bar
)

from src.services import initialize_services, get_service_status

# Configurazione pagina
st.set_page_config(
    page_title="📚 Archivista AI - Unificata",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"  # Sidebar collassata di default
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main application unificata."""

    # Inizializza servizi se necessario
    if not st.session_state.get('services_initialized', False):
        logger.info("Inizializzazione servizi...")
        if initialize_services():
            st.session_state.services_initialized = True
            logger.info("Servizi inizializzati con successo")
        else:
            st.error("❌ Errore inizializzazione servizi")
            return

    # Crea componenti principali
    sidebar = create_collapsible_sidebar()
    login_modal = create_modal_login()
    chat_interface = create_minimal_chat()
    file_manager = create_file_context_manager()
    header_bar = create_header_bar()

    # Layout principale minimalista
    # Header
    header_bar.render()

    # Layout principale: Sidebar + Main Content
    main_col1, main_col2 = st.columns([0.15, 0.85])

    with main_col1:
        # Sidebar collassabile
        sidebar.render()

    with main_col2:
        # Contenuto principale basato su navigazione
        current_page = sidebar.get_current_page()

        if current_page == "chat":
            # Chat centrale minimalista
            chat_interface.render()

            # File context manager (se ci sono file)
            if st.session_state.get('context_files', []):
                st.markdown("---")
                file_manager.render()

        elif current_page == "archive":
            st.info("🗂️ **Archivio** - Da implementare nella Settimana 3-4")
            st.caption("L'archivio verrà integrato come tab principale nella dashboard unificata.")

        elif current_page == "dashboard":
            st.info("📊 **Dashboard** - Da implementare nella Settimana 3-4")
            st.caption("La dashboard con statistiche verrà integrata come tab principale.")

        elif current_page == "projects":
            st.info("📚 **Projects** - Da implementare nella Settimana 5-6")
            st.caption("La gestione progetti verrà integrata nella sidebar.")

        elif current_page == "carriera":
            st.info("🎓 **Carriera** - Da implementare nella Settimana 5-6")
            st.caption("Il planner accademico verrà integrato nella sidebar.")

        elif current_page == "grafo":
            st.info("🧠 **Grafo** - Da implementare nella Settimana 5-6")
            st.caption("Il grafo della conoscenza verrà integrato nei dettagli documenti.")

        else:
            # Default: mostra chat
            chat_interface.render()

    # Footer con informazioni sviluppo
    st.markdown("---")
    col1, col2, col3 = st.columns([0.5, 0.3, 0.2])

    with col1:
        st.caption("🚀 **Architettura Unificata** - Prototipo Settimana 1")

    with col2:
        st.caption(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    with col3:
        if st.button("🔄 Debug", help="Mostra stato componenti"):
            with st.expander("🔍 Debug Info", expanded=True):
                st.json({
                    "current_page": sidebar.get_current_page(),
                    "services_status": get_service_status(),
                    "session_keys": list(st.session_state.keys()),
                    "sidebar_collapsed": sidebar.is_collapsed
                })

if __name__ == "__main__":
    main()
