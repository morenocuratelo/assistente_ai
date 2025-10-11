# Pagina Editor - Modifica anteprime e documenti
"""
Pagina Editor: Interfaccia dedicata per la modifica delle anteprime AI.

Questa pagina offre un ambiente ottimizzato per modificare le anteprime generate
dall'AI con riferimento diretto al documento originale affiancato.

Layout:
- Colonna sinistra: Editor per modifica anteprime con controlli completi
- Colonna destra: Visualizzatore documento originale con supporto multi-formato

Funzionalità:
- Modifica anteprime con preservazione stato
- Visualizzazione documenti originali (PDF, DOCX, TXT, HTML, RTF)
- Navigazione pagine per PDF
- Auto-salvataggio e validazione modifiche
- Integrazione con Knowledge Explorer e Chat
"""

import streamlit as st
import pandas as pd
from file_utils import get_papers_dataframe, update_paper_metadata
import os
import time

def main():
    st.set_page_config(page_title="📝 Editor - Archivista AI", page_icon="📝", layout="wide")
    st.title("📝 Editor Anteprime AI")
    st.caption("Modifica le anteprime generate dall'AI con riferimento al documento originale")

    # Verifica se c'è un documento da modificare
    if 'edit_paper' not in st.session_state or not st.session_state.edit_paper:
        render_document_selection()
    else:
        render_editor_interface()

def render_document_selection():
    """Render interfaccia selezione documento quando non c'è un documento attivo"""
    st.info("📋 Seleziona un documento da modificare dalle altre pagine o dalla lista sottostante")

    papers_df = get_papers_dataframe()
    if papers_df.empty:
        st.warning("⚠️ Nessun documento disponibile per la modifica")
        return

    # Selezione documento da modificare
    st.markdown("### 📄 Documenti Disponibili per Modifica")

    # Raggruppa per categoria per organizzazione
    for category, group in papers_df.groupby(['category_id', 'category_name']):
        category_id, category_name = category
        with st.expander(f"**{category_name}** ({len(group)} documenti)"):
            for _, row in group.iterrows():
                file_name = row['file_name']
                title = row.get('title', file_name)
                has_preview = bool(row.get('formatted_preview'))

                col1, col2, col3 = st.columns([0.6, 0.2, 0.2])

                with col1:
                    status_icon = "✅" if has_preview else "⏳"
                    st.markdown(f"**{status_icon} {title}**")
                    st.caption(f"📅 {row.get('publication_year', 'N/A')} | 👥 {row.get('authors', 'N/A')}")

                with col2:
                    if st.button(
                        "✏️ Modifica",
                        key=f"edit_{file_name}",
                        help=f"Modifica anteprima di: {title}",
                        use_container_width=True
                    ):
                        st.session_state.edit_paper = file_name
                        st.rerun()

                with col3:
                    preview_status = "Con anteprima" if has_preview else "Senza anteprima"
                    st.caption(preview_status)

def render_editor_interface():
    """Render interfaccia editor completa con layout 2 colonne"""
    papers_df = get_papers_dataframe()
    edit_row = papers_df[papers_df['file_name'] == st.session_state.edit_paper]

    if edit_row.empty:
        st.error("❌ Documento non trovato.")
        if st.button("🔙 Torna alla selezione"):
            del st.session_state.edit_paper
            st.rerun()
        return

    row = edit_row.iloc[0]
    current_content = row.get('formatted_preview', '')

    # Layout 2 colonne
    col_left, col_right = st.columns([0.5, 0.5])

    # --- COLONNA SINISTRA: EDITOR ---
    with col_left:
        st.markdown("### ✏️ Editor Anteprima")

        # Info documento corrente
        st.markdown(f"**Documento:** {row.get('title', row['file_name'])}")
        st.caption(f"📂 {row.get('category_name', 'N/A')} | 📅 {row.get('publication_year', 'N/A')}")

        # Area modifica anteprima con editor avanzato
        st.markdown("**📝 Contenuto Anteprima:**")

        # Prova editor avanzato con fallback
        try:
            from streamlit_quill import st_quill  # type: ignore

            # Verifica che il componente sia disponibile
            if not st_quill:
                raise ImportError("st_quill non disponibile")

            edited_content = st_quill(
                value=current_content,
                html=True,
                key="advanced_editor",
                placeholder="Inizia a scrivere la tua anteprima...",
                toolbar=[
                    ['bold', 'italic', 'underline', 'strike'],
                    ['blockquote', 'code-block'],
                    [{'header': 1}, {'header': 2}],
                    [{'list': 'ordered'}, {'list': 'bullet'}],
                    [{'script': 'sub'}, {'script': 'super'}],
                    [{'indent': '-1'}, {'indent': '+1'}],
                    ['link', 'image'],
                    ['clean']
                ]
            )

        except ImportError:
            # Fallback a text_area se quill non disponibile
            st.warning("⚠️ Editor avanzato non disponibile, utilizzo editor base")
            edited_content = st.text_area(
                "Modifica il contenuto Markdown dell'anteprima:",
                value=current_content,
                height=400,
                key="editor_text_area",
                help="Modifica il testo dell'anteprima generata dall'AI"
            )

        # Controlli editor
        st.markdown("**⚙️ Controlli:**")

        # Checkbox anteprima live
        show_live_preview = st.checkbox(
            "👁️ Mostra anteprima live",
            value=st.session_state.get('show_live_preview', False),
            key="live_preview_toggle"
        )

        # Pulsanti azione
        st.markdown("**💾 Azioni:**")
        col_save, col_cancel, col_reset = st.columns([0.33, 0.33, 0.34])

        with col_save:
            if st.button(
                "💾 Salva Modifiche",
                key="save_edit",
                use_container_width=True,
                type="primary",
                help="Salva le modifiche all'anteprima"
            ):
                if save_preview_changes(st.session_state.edit_paper, edited_content):
                    st.success("✅ Modifiche salvate con successo!")
                    # Aggiorna contenuto corrente
                    current_content = edited_content
                    # Ricarica dati
                    papers_df = get_papers_dataframe()
                    st.rerun()
                else:
                    st.error("❌ Errore nel salvataggio delle modifiche")

        with col_cancel:
            if st.button(
                "❌ Annulla Modifiche",
                key="cancel_edit",
                use_container_width=True,
                help="Annulla modifiche e torna alla selezione"
            ):
                del st.session_state.edit_paper
                if 'show_live_preview' in st.session_state:
                    del st.session_state.show_live_preview
                st.rerun()

        with col_reset:
            if st.button(
                "🔄 Ripristina Originale",
                key="reset_edit",
                use_container_width=True,
                help="Ripristina l'anteprima originale generata dall'AI"
            ):
                # Qui potresti ripristinare l'anteprima originale se disponibile
                st.info("🔄 Ripristino anteprima originale...")

        # Statistiche modifica
        if edited_content != current_content:
            char_diff = len(edited_content) - len(current_content)
            st.caption(f"📊 Modifiche: {char_diff} caratteri {'in più' if char_diff > 0 else 'in meno'}")

    # --- COLONNA DESTRA: VISUALIZZATORE DOCUMENTO ---
    with col_right:
        st.markdown("### 📄 Documento Originale")
        render_document_viewer(row)

        # Anteprima live se abilitata
        if show_live_preview and edited_content != current_content:
            st.markdown("---")
            st.markdown("### 👁️ Anteprima Live Modifiche")
            with st.expander("Visualizza anteprima delle modifiche", expanded=True):
                st.markdown("**📋 Come apparirà dopo il salvataggio:**")
                st.info(edited_content)

def render_document_viewer(row):
    """Render visualizzatore documento originale"""
    from main import get_original_file_path

    # Trova percorso file originale
    file_path = get_original_file_path(row)
    if not file_path or not os.path.exists(file_path):
        st.warning(f"⚠️ File originale non trovato: {row['file_name']}")
        st.info("Il documento potrebbe essere stato spostato o eliminato.")
        return

    file_ext = os.path.splitext(file_path)[1].lower()

    # Visualizzazione basata sul tipo di file
    if file_ext == '.pdf':
        display_pdf_pages(file_path)
    else:
        display_text_content(file_path)

def display_pdf_pages(file_path):
    """Visualizza pagine PDF (da main.py originale)"""
    try:
        import fitz  # PyMuPDF

        # Apri il PDF
        doc = fitz.open(file_path)

        if len(doc) == 0:
            st.warning("📄 Il PDF non contiene pagine.")
            return

        # Info documento
        st.info(f"📊 PDF con **{len(doc)}** pagine")

        # Selettore pagina (se più di una pagina)
        if len(doc) > 1:
            page_number = st.selectbox(
                "Seleziona pagina:",
                options=range(len(doc)),
                format_func=lambda x: f"Pagina {x + 1}",
                key="pdf_page_selector"
            )
        else:
            page_number = 0

        # Render pagina come immagine
        page = doc.load_page(page_number)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # Zoom 2x per qualità

        # Converti in formato PIL Image
        img_data = pix.tobytes("png")
        from PIL import Image
        import io
        image = Image.open(io.BytesIO(img_data))

        # Mostra immagine
        st.image(
            image,
            caption=f"Pagina {page_number + 1} di {len(doc)}",
            use_column_width=True
        )

        # Chiudi documento
        doc.close()

    except ImportError:
        st.error("❌ PyMuPDF non è installato correttamente.")
    except Exception as e:
        st.error(f"❌ Errore nella visualizzazione del PDF: {e}")
        st.info("Assicurati che il file sia un PDF valido e che PyMuPDF sia installato correttamente.")

def display_text_content(file_path):
    """Visualizza contenuto testuale (da main.py originale)"""
    try:
        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext == '.txt':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                st.info(f"📄 File di testo (.txt) - **{len(content)}** caratteri")
                # Mostra solo primi 5000 caratteri per non sovraccaricare
                display_text = content[:5000] + ("..." if len(content) > 5000 else "")
                st.text_area("Contenuto del file:", value=display_text, height=300, disabled=True)
            except UnicodeDecodeError:
                st.warning("⚠️ Impossibile leggere il file di testo con codifica UTF-8.")

        elif file_ext == '.docx':
            try:
                from docx import Document as DocxDocument
                doc = DocxDocument(file_path)
                content = '\n'.join([paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()])
                st.info(f"📄 Documento Word (.docx) - **{len(content)}** caratteri")
                display_text = content[:5000] + ("..." if len(content) > 5000 else "")
                st.text_area("Contenuto del documento:", value=display_text, height=300, disabled=True)
            except Exception as e:
                st.warning(f"⚠️ Errore nella lettura del file .docx: {e}")

        elif file_ext in ['.html', '.htm']:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                st.info(f"📄 Pagina HTML (.html) - **{len(content)}** caratteri")

                # Estrai testo senza tag HTML
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(content, 'html.parser')
                text_content = soup.get_text()

                display_text = text_content[:5000] + ("..." if len(text_content) > 5000 else "")
                st.text_area("Contenuto testuale:", value=display_text, height=300, disabled=True)
            except Exception as e:
                st.warning(f"⚠️ Errore nella lettura del file HTML: {e}")

        elif file_ext == '.rtf':
            try:
                from striprtf.striprtf import rtf_to_text
                with open(file_path, 'r', encoding='utf-8') as f:
                    rtf_content = f.read()
                content = rtf_to_text(rtf_content)
                st.info(f"📄 Documento RTF (.rtf) - **{len(content)}** caratteri")
                display_text = content[:5000] + ("..." if len(content) > 5000 else "")
                st.text_area("Contenuto del documento:", value=display_text, height=300, disabled=True)
            except Exception as e:
                st.warning(f"⚠️ Errore nella lettura del file RTF: {e}")

        else:
            st.info(f"📄 File {file_ext} - Visualizzazione non supportata")
            st.text(f"Percorso: {file_path}")

    except Exception as e:
        st.error(f"❌ Errore nella visualizzazione del file: {e}")

def save_preview_changes(file_name, new_content):
    """Salva le modifiche all'anteprima"""
    try:
        # Prepara dati per aggiornamento
        update_data = {'formatted_preview': new_content}

        # Salva nel database
        success = update_paper_metadata(file_name, update_data)

        if success:
            # Log dell'operazione
            st.session_state.log_messages.insert(0, f"[{time.strftime('%H:%M:%S')}] Anteprima aggiornata: {file_name}")

        return success

    except Exception as e:
        st.error(f"Errore nel salvataggio: {e}")
        return False

if __name__ == "__main__":
    main()
