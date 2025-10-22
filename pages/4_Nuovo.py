# Pagina Nuovo Documento - Creazione documenti direttamente nell'app
"""
Pagina Nuovo Documento: Interfaccia per creare nuova conoscenza direttamente nell'applicazione.

Questa pagina permette di creare documenti Markdown che vengono automaticamente
processati dalla pipeline esistente e integrati nell'archivio.

Funzionalità:
- Editor WYSIWYG professionale con streamlit-quill
- Creazione documenti Markdown con metadati
- Salvataggio automatico in documenti_da_processare/
- Integrazione seamless con pipeline esistente
- Template predefiniti per diversi tipi di contenuto
"""

import streamlit as st
import os
import time
from datetime import datetime

# Import UX components for improved user experience
from scripts.operations.ux_components import show_contextual_help, show_success_message, show_error_message
# Import feedback system for enhanced messaging
from scripts.operations.feedback_system import show_enhanced_message, show_success_with_actions, handle_operation_error, notification_manager
# Import smart suggestions for behavior tracking
from scripts.operations.smart_suggestions import record_user_action, doc_type_detector

# --- CONFIGURAZIONE ---
DOCS_TO_PROCESS_DIR = "documenti_da_processare"

def main():
    st.set_page_config(page_title="✨ Nuovo Documento - Archivista AI", page_icon="✨", layout="wide")
    st.title("✨ Crea Nuovo Documento")
    st.caption("Crea nuova conoscenza direttamente nell'applicazione")

    # Add help button for document creation
    if st.button("❓ Guida Creazione", help="Mostra guida per creare documenti"):
        show_contextual_help("document_creation")

    # Layout 2 colonne per creazione documento
    col_left, col_right = st.columns([0.6, 0.4])

    with col_left:
        render_creation_form()

    with col_right:
        render_creation_sidebar()

def render_creation_form():
    """Form principale per creazione documento"""
    st.markdown("### 📝 Crea Nuovo Documento")

    # Enhanced template selection with descriptions
    st.markdown("#### 🎯 Scegli Template")

    # Template options with detailed descriptions
    template_options = {
        "Documento vuoto": {
            "description": "📄 Documento generico per appunti veloci e contenuti vari",
            "use_case": "Ideale per: note rapide, bozze, contenuti generici"
        },
        "Appunti riunione": {
            "description": "🗣️ Struttura per verbali e discussioni di gruppo",
            "use_case": "Ideale per: riunioni, meeting, discussioni collaborative"
        },
        "Riassunto libro": {
            "description": "📖 Template per recensioni e sintesi di letture",
            "use_case": "Ideale per: recensioni libri, sintesi letture, analisi testi"
        },
        "Idea progetto": {
            "description": "💡 Struttura per pianificare nuovi progetti",
            "use_case": "Ideale per: pianificazione, proposte, sviluppo idee"
        },
        "Nota ricerca": {
            "description": "🔬 Template per appunti di ricerca e metodologia",
            "use_case": "Ideale per: ricerca accademica, studi, indagini"
        }
    }

    # Create radio buttons for better template selection
    template = st.radio(
        "Tipo di documento:",
        options=list(template_options.keys()),
        key="document_template",
        help="Scegli il template più adatto al tuo contenuto"
    )

    # Show template description and use case
    if template in template_options:
        template_info = template_options[template]
        st.info(f"**{template_info['description']}**")
        st.caption(f"💡 {template_info['use_case']}")

    # Metadati documento
    st.markdown("#### 📋 Metadati")

    col1, col2 = st.columns(2)

    with col1:
        document_title = st.text_input(
            "Titolo documento:",
            value=get_template_title(template),
            key="document_title",
            placeholder="Inserisci il titolo del documento..."
        )

        document_authors = st.text_input(
            "Autori (separati da virgola):",
            value="Utente",
            key="document_authors",
            placeholder="Nome autore, Secondo autore..."
        )

    with col2:
        document_year = st.number_input(
            "Anno pubblicazione:",
            min_value=1900,
            max_value=datetime.now().year + 1,
            value=datetime.now().year,
            key="document_year"
        )

        document_category = st.selectbox(
            "Categoria:",
            options=["Seleziona categoria...", "P1_IL_PALCOSCENICO_COSMICO_E_BIOLOGICO/C01",
                    "P2_L_ASCESA_DEL_GENERE_HOMO/C04", "UNCATEGORIZED/C00"],
            key="document_category"
        )

    # Editor contenuto con tecnologia avanzata
    st.markdown("#### 📝 Contenuto Documento")

    # Contenuto iniziale basato su template
    initial_content = get_template_content(template)

    # Editor avanzato con fallback
    try:
        from streamlit_quill import st_quill

        document_content = st_quill(
            value=initial_content,
            html=True,
            key="new_document_editor",
            placeholder="Inizia a scrivere il tuo documento...",
            toolbar=[
                ['bold', 'italic', 'underline', 'strike'],
                ['blockquote', 'code-block'],
                [{'header': 1}, {'header': 2}, {'header': 3}],
                [{'list': 'ordered'}, {'list': 'bullet'}],
                [{'script': 'sub'}, {'script': 'super'}],
                [{'indent': '-1'}, {'indent': '+1'}],
                [{'direction': 'rtl'}],
                ['link', 'image'],
                ['clean']
            ]
        )

    except ImportError:
        # Fallback a text_area
        st.warning("⚠️ Editor avanzato non disponibile, utilizzo editor base")
        document_content = st.text_area(
            "Contenuto del documento:",
            value=initial_content,
            height=400,
            key="new_document_content",
            help="Scrivi il contenuto del tuo documento in formato Markdown"
        )

    # Azioni documento
    st.markdown("#### 💾 Azioni")

    col_save, col_preview, col_clear = st.columns([0.33, 0.33, 0.34])

    with col_save:
        if st.button(
            "💾 Salva e Processa",
            key="save_new_document",
            use_container_width=True,
            type="primary",
            help="Salva il documento e avviane il processamento automatico"
        ):
            if save_new_document(document_title, document_authors, document_year, document_category, document_content):
                # Enhanced success feedback with actions
                show_success_with_actions(
                    "Documento Creato!",
                    f"Il documento '{document_title}' è stato creato e inviato per processamento automatico.",
                    actions=[
                        {"label": "📚 Vedi Archivio", "page": "pages/2_Archivio.py"},
                        {"label": "💬 Vai alla Chat", "page": "pages/1_Chat.py"},
                        {"label": "📊 Monitoraggio", "page": "pages/8_Feedback_Dashboard.py"}
                    ],
                    notification=True
                )
            else:
                st.error("❌ Errore nella creazione del documento")

    with col_preview:
        if st.button(
            "👁️ Anteprima",
            key="preview_document",
            use_container_width=True,
            help="Visualizza anteprima del documento"
        ):
            st.session_state.show_preview = not st.session_state.get('show_preview', False)

    with col_clear:
        if st.button(
            "🗑️ Cancella Tutto",
            key="clear_document",
            use_container_width=True,
            help="Cancella tutto e ricomincia"
        ):
            # Pulisce tutti i campi
            keys_to_clear = ['document_title', 'document_authors', 'document_year', 'document_category', 'new_document_editor', 'new_document_content']
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

    # Mostra anteprima se richiesta
    if st.session_state.get('show_preview', False):
        st.markdown("---")
        st.markdown("### 👁️ Anteprima Documento")
        with st.expander("Visualizza anteprima", expanded=True):
            st.markdown(f"**📄 Titolo:** {document_title}")
            st.markdown(f"**👥 Autori:** {document_authors}")
            st.markdown(f"**📅 Anno:** {document_year}")
            st.markdown(f"**📂 Categoria:** {document_category}")

            st.markdown("**📝 Contenuto:**")
            if document_content:
                st.info(document_content)
            else:
                st.warning("Il documento è vuoto")

def render_creation_sidebar():
    """Sidebar con informazioni e suggerimenti per creazione documento"""
    st.markdown("### 💡 Suggerimenti per Iniziare")

    # Statistiche documenti esistenti
    try:
        from scripts.utilities.file_utils import get_papers_dataframe
        papers_df = get_papers_dataframe()

        if not papers_df.empty:
            st.metric("📚 Documenti esistenti", len(papers_df))

            # Categorie più usate
            top_categories = papers_df['category_name'].value_counts().head(3)
            if not top_categories.empty:
                st.markdown("**🏆 Categorie popolari:**")
                for cat, count in top_categories.items():
                    st.markdown(f"• {cat} ({count} documenti)")

            # Quick actions for existing users
            st.markdown("**🚀 Azioni rapide:**")
            if st.button("💬 Vai alla Chat", use_container_width=True):
                st.switch_page("pages/1_Chat.py")
            if st.button("📚 Esplora Archivio", use_container_width=True):
                st.switch_page("pages/2_Archivio.py")
        else:
            st.info("📭 Questo sarà il tuo primo documento!")
            st.markdown("**🎉 Dopo averlo creato potrai:**")
            st.markdown("• 💬 Farci domande nella Chat")
            st.markdown("• 📚 Vederlo nell'Archivio")
            st.markdown("• ✏️ Modificare l'anteprima nell'Editor")

    except Exception as e:
        st.warning(f"⚠️ Impossibile caricare statistiche: {e}")

    st.markdown("---")

    # Enhanced guidance for document creation
    st.markdown("### 📖 Come Procedere")

    # Step by step guide
    st.markdown("**🎯 Passi per creare un documento perfetto:**")

    steps = [
        {
            "step": "1. 📋 Scegli Template",
            "description": "Seleziona il tipo di documento più adatto al tuo contenuto"
        },
        {
            "step": "2. ✏️ Inserisci Metadati",
            "description": "Aggiungi titolo, autori e categoria per una migliore organizzazione"
        },
        {
            "step": "3. 📝 Scrivi Contenuto",
            "description": "Usa l'editor per creare il tuo documento con formattazione Markdown"
        },
        {
            "step": "4. 💾 Salva e Processa",
            "description": "Il documento verrà automaticamente processato e aggiunto all'archivio"
        }
    ]

    for step_info in steps:
        with st.expander(step_info["step"]):
            st.caption(step_info["description"])

    st.markdown("---")

    # Tips and best practices
    st.markdown("### 💡 Best Practices")

    tips = [
        "**Titolo efficace:** Usa titoli chiari e descrittivi che spieghino il contenuto",
        "**Contenuto strutturato:** Organizza con sezioni (## Titolo) per una migliore leggibilità",
        "**Parole chiave:** Includi termini importanti per facilitare future ricerche",
        "**Metadati accurati:** Categoria e anno aiutano l'organizzazione automatica"
    ]

    for tip in tips:
        st.markdown(f"• {tip}")

    # Workflow explanation
    st.markdown("---")
    st.markdown("### 🔄 Cosa Succede Dopo?")
    st.info("""
    **🤖 Processamento Automatico:**
    1. L'AI analizza il contenuto del documento
    2. Crea un'anteprima intelligente
    3. Indicizza per la ricerca
    4. Aggiunge all'archivio categorizzato

    **⏱️ Tempistiche:**
    • Documenti brevi: pochi secondi
    • Documenti lunghi: fino a 1 minuto
    """)

def get_template_title(template):
    """Restituisce titolo predefinito per template"""
    titles = {
        "Documento vuoto": "Nuovo Documento",
        "Appunti riunione": "Appunti Riunione",
        "Riassunto libro": "Riassunto Libro",
        "Idea progetto": "Idea Progetto",
        "Nota ricerca": "Nota Ricerca"
    }
    return titles.get(template, "Nuovo Documento")

def get_template_content(template):
    """Restituisce contenuto predefinito per template"""
    templates = {
        "Documento vuoto": """# Nuovo Documento

Inserisci qui il contenuto del tuo documento...

## Sezione 1
Contenuto della prima sezione.

## Sezione 2
Contenuto della seconda sezione.

## Conclusioni
Le tue conclusioni qui.
""",
        "Appunti riunione": """# Appunti Riunione

**Data:** [Inserisci data]
**Partecipanti:** [Elenca partecipanti]
**Moderatore:** [Nome moderatore]

## Agenda
- [ ] Punto 1
- [ ] Punto 2
- [ ] Punto 3

## Discussione
[Note sulla discussione]

## Decisioni
[Decisioni prese]

## Azioni Future
[Azioni da intraprendere]
""",
        "Riassunto libro": """# Riassunto Libro

**Titolo:** [Titolo del libro]
**Autore:** [Nome autore]
**Anno:** [Anno pubblicazione]

## Riassunto
[Breve riassunto del libro]

## Temi Principali
- Tema 1
- Tema 2
- Tema 3

## Impressioni Personali
[Tue impressioni e opinioni]
""",
        "Idea progetto": """# Idea Progetto

**Nome Progetto:** [Nome progetto]
**Proponente:** [Tuo nome]

## Descrizione
[Descrizione dell'idea di progetto]

## Obiettivi
- [ ] Obiettivo 1
- [ ] Obiettivo 2
- [ ] Obiettivo 3

## Requisiti
[Requisiti necessari per realizzarlo]

## Benefici Attesi
[Vantaggi del progetto]
""",
        "Nota ricerca": """# Nota Ricerca

**Titolo Ricerca:** [Titolo ricerca]
**Ricercatore:** [Tuo nome]

## Domanda di Ricerca
[Qual è la domanda principale che stai investigando?]

## Metodologia
[Come stai conducendo la ricerca?]

## Risultati Preliminari
[Risultati ottenuti finora]

## Conclusioni
[Conclusioni attuali]
"""
    }
    return templates.get(template, templates["Documento vuoto"])

def save_new_document(title, authors, year, category, content):
    """Salva nuovo documento nella cartella di processamento"""
    try:
        # Validazione input
        if not title or not title.strip():
            st.error("❌ Il titolo è obbligatorio")
            return False

        if not content or not content.strip():
            st.error("❌ Il contenuto è obbligatorio")
            return False

        # Crea nome file sicuro
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_name = f"{safe_title}_{timestamp}.md"

        # Crea percorso completo
        file_path = os.path.join(DOCS_TO_PROCESS_DIR, file_name)

        # Crea contenuto completo del file Markdown
        authors_list = [author.strip() for author in authors.split(',') if author.strip()]

        full_content = f"""---
title: "{title}"
authors: {authors_list}
publication_year: {year}
category_id: "{category}"
created_at: "{datetime.now().isoformat()}"
created_by: "Archivista AI - Nuovo Documento"
---

{content}
"""

        # Salva file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(full_content)

        # Log operazione
        st.session_state.log_messages.insert(0, f"[{time.strftime('%H:%M:%S')}] Nuovo documento creato: {file_name}")

        return True

    except Exception as e:
        st.error(f"❌ Errore nella creazione del documento: {e}")
        return False

if __name__ == "__main__":
    main()
