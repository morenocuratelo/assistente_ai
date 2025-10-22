"""
Main application per dashboard unificata.

Punto di ingresso principale per testare la dashboard unificata
con integrazione completa dei servizi della Fase 2.
"""

import streamlit as st
import logging
from pathlib import Path
import sys

# Aggiungi path principale per import
sys.path.append(str(Path(__file__).parent.parent.parent))

# Configurazione pagina
st.set_page_config(
    page_title="🎯 Archivista AI - Dashboard Unificata",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def initialize_session_state():
    """Inizializza stato sessione."""
    defaults = {
        'user': None,
        'context_files': [],
        'chat_messages': [],
        'active_tab': 'chat',
        'show_login': False,
        'show_file_manager': False,
        'sidebar_collapsed': False
    }

    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

def main():
    """Funzione principale applicazione."""
    logger.info("🚀 Avvio dashboard unificata")

    # Inizializza stato sessione
    initialize_session_state()

    try:
        # Import e crea dashboard unificata
        from src.ui.components.unified_dashboard import create_unified_dashboard

        dashboard = create_unified_dashboard()

        # Render dashboard principale
        dashboard.render()

        # Gestisci cambiamenti di stato
        dashboard.handle_state_changes()

        logger.info("✅ Dashboard unificata renderizzata con successo")

    except Exception as e:
        logger.error(f"❌ Errore dashboard unificata: {e}")
        st.error(f"Errore applicazione: {e}")
        st.error("Verifica che tutti i servizi siano configurati correttamente.")

        # Debug info
        with st.expander("🔧 Debug Information"):
            st.write(f"**Errore:** {str(e)}")
            st.write(f"**Tipo errore:** {type(e).__name__}")

            try:
                from src.services import DocumentService, UserService, ChatService
                st.success("✅ Import servizi OK")
            except ImportError as ie:
                st.error(f"❌ Errore import servizi: {ie}")

            try:
                from src.database.repositories import DocumentRepository, UserRepository, ChatRepository
                st.success("✅ Import repository OK")
            except ImportError as ie:
                st.error(f"❌ Errore import repository: {ie}")

if __name__ == "__main__":
    main()
