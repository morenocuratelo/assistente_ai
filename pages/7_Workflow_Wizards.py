# 🎯 Workflow Wizards Page - Interactive Guided Workflows
"""
Dedicated page for workflow wizards that guide users through complex processes.

This page provides access to interactive wizards for:
- Document upload and processing
- Advanced search building
- Document editing workflows
- Batch operations
"""

import streamlit as st
from scripts.operations.workflow_wizards import show_workflow_wizards_hub

def main():
    """Main function for the Workflow Wizards page."""
    st.set_page_config(page_title="🎯 Workflow Wizards - Archivista AI", page_icon="🎯", layout="wide")

    st.title("🎯 Workflow Wizards")
    st.caption("Guide interattive per processi complessi passo dopo passo")

    # Show brief introduction
    st.markdown("""
    ### 🚀 Cosa sono i Workflow Wizards?

    I Workflow Wizards sono guide interattive che ti accompagnano attraverso processi complessi
    in modo semplice e sicuro. Ogni wizard è progettato per aiutarti a:

    - **📤 Caricare documenti** con le impostazioni ottimali
    - **🔍 Costruire ricerche avanzate** con filtri sofisticati
    - **✏️ Modificare documenti** in modo sicuro e guidato
    - **⚡ Eseguire operazioni batch** su più documenti contemporaneamente

    ### 💡 Come Funzionano

    1. **Scegli un wizard** dalla selezione sottostante
    2. **Segui i passaggi** guidati con spiegazioni chiare
    3. **Conferma le tue scelte** prima di eseguire operazioni
    4. **Ottieni risultati** con feedback immediato
    """)

    st.markdown("---")

    # Show the workflow wizards hub
    show_workflow_wizards_hub()

if __name__ == "__main__":
    main()
