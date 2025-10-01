# Pagina Chat - Interfaccia principale con layout 3 colonne
import streamlit as st

def main():
    st.set_page_config(page_title="💬 Chat - Archivista AI", page_icon="💬", layout="wide")
    st.title("💬 Chat con l'Archivio")
    st.caption("Fai domande sui tuoi documenti e ottieni risposte intelligenti")

    # Layout 3 colonne
    col_left, col_center, col_right = st.columns([0.25, 0.5, 0.25])

    with col_left:
        st.markdown("### 📚 Selezione Documenti")
        st.info("Seleziona i documenti da usare come contesto per la chat")

        # Qui integreremo display_chat_archive_view() dal main.py originale

    with col_center:
        st.markdown("### 💭 Conversazione")

        # Filtri chat posizionati sopra i messaggi
        st.markdown("#### 🔧 Filtri Chat")
        filter_col1, filter_col2, filter_col3 = st.columns([0.3, 0.3, 0.4])

        with filter_col1:
            # Filtro categoria
            st.selectbox("Categoria", ["Tutte", "Categoria 1", "Categoria 2"], key="chat_category_filter")

        with filter_col2:
            # Filtro documento
            st.selectbox("Documento", ["Tutti", "Documento 1", "Documento 2"], key="chat_document_filter")

        with filter_col3:
            if st.button("🗑️ Cancella Filtri"):
                pass

        st.divider()

        # Area messaggi chat
        st.markdown("**Messaggi Chat:**")
        st.info("💬 Area chat principale - sarà implementata nel prossimo step")

    with col_right:
        st.markdown("### 📖 Anteprime")

        # Qui mostreremo le anteprime dei documenti selezionati
        st.info("📋 Anteprime documenti selezionati appariranno qui")

        # Esempio di struttura anteprima
        with st.expander("📄 Documento Selezionato", expanded=True):
            st.markdown("**Titolo:** Documento di esempio")
            st.markdown("**Categoria:** Categoria esempio")
            st.info("Anteprima generata dall'AI apparirà qui...")

            # Pulsante modifica anteprima
            if st.button("✏️ Modifica Anteprima", key="chat_edit_preview"):
                st.session_state.edit_paper = "documento_selezionato.pdf"  # Qui andrebbe il file selezionato
                st.switch_page("pages/3_📝_Editor.py")

if __name__ == "__main__":
    main()
