# 🎯 UX Components for Archivista AI
"""
Reusable UX components to improve user experience across the application.

This module provides:
- Tooltip system for better icon labeling
- Onboarding components for new users
- Contextual help and guidance
- Progress indicators and feedback
- Smart suggestions based on user state
"""

import streamlit as st
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# --- TOOLTIP SYSTEM ---

def add_tooltip_icon(text: str, icon: str = "❓") -> str:
    """Create a tooltip icon with help text."""
    return f"""
    <div title="{text}" style="display: inline-block; cursor: help; margin-left: 5px;">
        {icon}
    </div>
    """

def create_labeled_icon(icon: str, label: str, tooltip: str = "") -> str:
    """Create an icon with label and optional tooltip."""
    tooltip_html = f' title="{tooltip}"' if tooltip else ""
    return f"""
    <div{tooltip_html} style="display: inline-flex; align-items: center; gap: 5px; cursor: help;">
        {icon} {label}
    </div>
    """

# --- ONBOARDING SYSTEM ---

class OnboardingManager:
    """Manages user onboarding and progress tracking."""

    def __init__(self):
        self.user_progress_key = "user_onboarding_progress"
        self.completed_steps_key = "completed_onboarding_steps"

    def get_user_progress(self, user_id: str) -> Dict[str, Any]:
        """Get user's onboarding progress."""
        if user_id not in st.session_state:
            return {"is_new_user": True, "completed_steps": [], "last_seen": None}

        return st.session_state.get(self.user_progress_key, {
            "is_new_user": True,
            "completed_steps": [],
            "last_seen": None
        })

    def mark_step_completed(self, user_id: str, step_name: str):
        """Mark an onboarding step as completed."""
        progress = self.get_user_progress(user_id)

        if step_name not in progress["completed_steps"]:
            progress["completed_steps"].append(step_name)
            progress["last_seen"] = datetime.now().isoformat()
            progress["is_new_user"] = False

            st.session_state[self.user_progress_key] = progress

    def is_step_completed(self, user_id: str, step_name: str) -> bool:
        """Check if a step is completed."""
        progress = self.get_user_progress(user_id)
        return step_name in progress["completed_steps"]

    def should_show_onboarding(self, user_id: str) -> bool:
        """Determine if onboarding should be shown."""
        progress = self.get_user_progress(user_id)
        return progress.get("is_new_user", True)

# Global onboarding manager instance
onboarding = OnboardingManager()

def show_welcome_modal():
    """Display welcome modal for new users."""
    if "show_welcome" not in st.session_state:
        st.session_state.show_welcome = True

    if st.session_state.show_welcome:
        @st.dialog("🎉 Benvenuto in Archivista AI!")
        def welcome_dialog():
            st.markdown("""
            ### 🚀 Iniziamo il tuo viaggio!

            Archivista AI è il tuo assistente intelligente per la gestione della conoscenza.
            Ecco cosa puoi fare:

            #### 📚 **Gestisci Documenti**
            - Carica e organizza i tuoi documenti
            - L'AI crea automaticamente anteprime intelligenti
            - Cerca e trova informazioni rapidamente

            #### 💬 **Chatta con l'Archivio**
            - Fai domande sui tuoi documenti
            - Ottieni risposte contestuali e accurate
            - Esplora relazioni tra documenti

            #### 📝 **Crea Contenuto**
            - Scrivi documenti direttamente nell'app
            - Usa template per iniziare velocemente
            - Modifica anteprime generate dall'AI
            """)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🚀 Inizia Subito", type="primary", use_container_width=True):
                    st.session_state.show_welcome = False
                    st.session_state.completed_onboarding_steps = ["welcome_shown"]
                    st.rerun()

            with col2:
                if st.button("📖 Fammi Vedere", use_container_width=True):
                    st.session_state.show_welcome = False
                    st.session_state.show_guided_tour = True
                    st.rerun()

        welcome_dialog()

def show_guided_tour():
    """Display interactive guided tour."""
    if "show_guided_tour" not in st.session_state or not st.session_state.show_guided_tour:
        return

    @st.dialog("🎯 Tour Guidato Rapido")
    def tour_dialog():
        st.markdown("### 📋 Guida Rapida - 5 Passi")

        steps = [
            {
                "title": "1. 📚 Carica Documenti",
                "description": "Inizia caricando i tuoi documenti nella cartella 'documenti_da_processare'"
            },
            {
                "title": "2. 🔍 Esplora l'Archivio",
                "description": "Vai nella pagina Archivio per vedere i documenti processati"
            },
            {
                "title": "3. 💬 Fai Domande",
                "description": "Nella pagina Chat, chiedi informazioni sui tuoi documenti"
            },
            {
                "title": "4. 📝 Crea Contenuto",
                "description": "Usa la pagina Nuovo per creare documenti direttamente nell'app"
            },
            {
                "title": "5. 🎨 Personalizza",
                "description": "Modifica le anteprime e organizza la tua conoscenza"
            }
        ]

        for i, step in enumerate(steps, 1):
            with st.expander(f"{step['title']}", expanded=(i == 1)):
                st.markdown(step['description'])

        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Ho Capito!", type="primary", use_container_width=True):
                st.session_state.show_guided_tour = False
                st.session_state.completed_onboarding_steps = ["tour_completed"]
                st.rerun()

        with col2:
            if st.button("⏭️ Salta per Ora", use_container_width=True):
                st.session_state.show_guided_tour = False
                st.rerun()

    tour_dialog()

# --- CONTEXTUAL HELP SYSTEM ---

def show_contextual_help(context: str, suggestions: List[str] = None):
    """Show contextual help based on current page/context."""
    help_content = {
        "empty_archive": {
            "title": "📭 Archivio Vuoto - Da Dove Iniziare?",
            "content": """
            Il tuo archivio è vuoto! Ecco cosa puoi fare per iniziare:

            **🚀 Passo 1: Carica Documenti**
            - Metti i tuoi PDF, Word, o TXT nella cartella `documenti_da_processare/`
            - L'AI li processerà automaticamente

            **📝 Passo 2: Crea Contenuto**
            - Usa la pagina "Nuovo" per creare documenti direttamente nell'app
            - Scegli da template predefiniti per iniziare velocemente

            **💡 Suggerimenti:**
            - Inizia con pochi documenti per vedere come funziona
            - I documenti vengono organizzati automaticamente per categoria
            """,
            "actions": [
                {"label": "📤 Vai a 'Nuovo Documento'", "page": "pages/4_Nuovo.py"},
                {"label": "📚 Vedi Documenti da Processare", "action": "show_processing_folder"}
            ]
        },
        "empty_chat": {
            "title": "💬 Chat Vuota - Cosa Chiedere?",
            "content": """
            La chat è il tuo assistente intelligente per l'archivio.
            Ecco alcuni esempi di cosa puoi chiedere:

            **🔍 Domande sui Documenti:**
            - "Riassumi il documento principale sull'intelligenza artificiale"
            - "Quali sono i temi trattati nel capitolo sulla cosmologia?"
            - "Confronta le diverse teorie sull'origine della vita"

            **📊 Richieste di Analisi:**
            - "Quanti documenti ho sull'argomento X?"
            - "Quali sono gli autori più citati?"
            - "Mostrami i documenti più recenti"

            **💡 Suggerimenti:**
            - Sii specifico sui documenti o argomenti che ti interessano
            - Chiedi relazioni tra documenti diversi
            - Usa la chat per esplorare connessioni nascoste
            """,
            "actions": [
                {"label": "📚 Vai all'Archivio", "page": "pages/2_Archivio.py"},
                {"label": "📖 Vedi Esempi Domande", "action": "show_sample_questions"}
            ]
        },
        "document_creation": {
            "title": "📝 Creazione Documento - Guida",
            "content": """
            Stai creando un nuovo documento. Ecco alcuni consigli:

            **🎯 Scegli il Template Giusto:**
            - **Documento vuoto**: Per contenuti generici o appunti veloci
            - **Appunti riunione**: Per verbali e discussioni di gruppo
            - **Riassunto libro**: Per recensioni e sintesi di letture
            - **Idea progetto**: Per pianificare nuovi progetti
            - **Nota ricerca**: Per appunti di ricerca e metodologia

            **📋 Metadati Importanti:**
            - **Titolo chiaro**: Aiuta l'AI a categorizzare correttamente
            - **Autori**: Chi ha creato il documento
            - **Anno**: Per organizzazione cronologica
            - **Categoria**: Dove verrà archiviato automaticamente

            **💡 Best Practices:**
            - Usa titoli descrittivi e specifici
            - Struttura il contenuto con sezioni (## Titolo Sezione)
            - Includi parole chiave importanti per la ricerca futura
            """,
            "actions": [
                {"label": "📚 Vedi Archivio", "page": "pages/2_Archivio.py"},
                {"label": "💬 Prova la Chat", "page": "pages/1_Chat.py"}
            ]
        },
        "archive_overview": {
            "title": "🗂️ Guida all'Archivio - Come Usarlo",
            "content": """
            L'Archivio è il cuore della tua knowledge base. Ecco come sfruttarlo al meglio:

            **🗂️ Navigazione:**
            - Usa la colonna sinistra per esplorare le categorie
            - Clicca su una categoria per vedere i documenti contenuti
            - Le categorie sono organizzate gerarchicamente (Parti → Capitoli)

            **📋 Tabs Principali:**
            - **Esplora**: Vista principale dei documenti con ricerca e filtri
            - **Dashboard**: Statistiche e analisi dell'archivio
            - **Operazioni Batch**: Modifiche massive a più documenti
            - **Esporta**: Scarica i dati in vari formati

            **👆 Azioni sui Documenti:**
            - Clicca su un documento per selezionarlo
            - Usa i pulsanti per visualizzare o modificare
            - Il menu ⋮ offre azioni avanzate e AI

            **💡 Suggerimenti:**
            - Inizia dalla categoria che ti interessa
            - Usa la ricerca per trovare documenti specifici
            - Seleziona più documenti per operazioni batch
            """,
            "actions": [
                {"label": "📤 Crea Nuovo Documento", "page": "pages/4_Nuovo.py"},
                {"label": "💬 Vai alla Chat", "page": "pages/1_Chat.py"}
            ]
        }
    }

    if context in help_content:
        content = help_content[context]

        with st.expander(f"💡 {content['title']}", expanded=True):
            st.markdown(content["content"])

            if suggestions:
                st.markdown("**🎯 Suggerimenti Personalizzati:**")
                for suggestion in suggestions:
                    st.markdown(f"• {suggestion}")

            if "actions" in content:
                st.markdown("**🚀 Azioni Consigliate:**")
                cols = st.columns(len(content["actions"]))
                for i, action in enumerate(content["actions"]):
                    with cols[i]:
                        if st.button(action["label"], key=f"action_{context}_{i}", use_container_width=True):
                            if "page" in action:
                                st.switch_page(action["page"])
                            elif "action" in action:
                                st.session_state[f"trigger_{action['action']}"] = True
                                st.rerun()

# --- SMART SUGGESTIONS ---

def get_smart_suggestions(user_context: Dict[str, Any]) -> List[str]:
    """Generate smart suggestions based on user context and state."""
    suggestions = []

    # Check if archive is empty
    try:
        from file_utils import get_papers_dataframe
        papers_df = get_papers_dataframe()
        has_documents = not papers_df.empty
    except:
        has_documents = False

    # Suggestions based on current state
    if not has_documents:
        suggestions.extend([
            "Carica i tuoi primi documenti nella cartella 'documenti_da_processare/'",
            "Crea il tuo primo documento usando la pagina 'Nuovo'",
            "Esplora la struttura di categorie disponibile"
        ])
    else:
        # User has documents - suggest engagement
        suggestions.extend([
            "Fai una domanda sui tuoi documenti nella pagina Chat",
            "Esplora le relazioni tra documenti nel Grafo",
            "Modifica le anteprime generate dall'AI nell'Editor"
        ])

    # Context-specific suggestions
    current_page = user_context.get("current_page", "")
    if current_page == "chat" and not has_documents:
        suggestions.append("Prima carica qualche documento per poter fare domande interessanti!")

    return suggestions[:4]  # Limit to 4 suggestions

# --- PROGRESS INDICATORS ---

def show_progress_indicator(message: str, progress: float = None):
    """Show a progress indicator with message."""
    if progress is not None:
        st.progress(progress, text=message)
    else:
        st.spinner(message)

def show_success_message(message: str, duration: int = 3):
    """Show a temporary success message."""
    placeholder = st.empty()
    placeholder.success(f"✅ {message}")
    # Note: In a real implementation, you'd use time.sleep and placeholder.empty()

def show_error_message(message: str, details: str = None):
    """Show an error message with optional details."""
    st.error(f"❌ {message}")
    if details:
        with st.expander("🔍 Dettagli errore"):
            st.code(details)

# --- STATUS BADGES ---

def create_status_badge(status: str, label: str = None) -> str:
    """Create a colored status badge."""
    status_colors = {
        "success": "#28a745",
        "warning": "#ffc107",
        "error": "#dc3545",
        "info": "#17a2b8",
        "processing": "#007bff"
    }

    color = status_colors.get(status.lower(), "#6c757d")
    display_label = label or status.upper()

    return f"""
    <span style="
        background-color: {color};
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8em;
        font-weight: bold;
    ">{display_label}</span>
    """

# --- FEATURE DISCOVERY ---

def show_feature_discovery(feature_name: str, description: str, learn_more_url: str = None):
    """Show a feature discovery card."""
    with st.expander(f"✨ Scopri: {feature_name}", expanded=False):
        st.markdown(description)
        if learn_more_url:
            st.markdown(f"📖 [Approfondisci]({learn_more_url})")

# --- UTILITY FUNCTIONS ---

def check_first_time_user(user_id: str) -> bool:
    """Check if this is a first-time user."""
    return onboarding.should_show_onboarding(user_id)

def get_completion_percentage(steps_completed: List[str], total_steps: int) -> int:
    """Calculate completion percentage."""
    if total_steps == 0:
        return 0
    return min(100, int((len(steps_completed) / total_steps) * 100))

# --- INITIALIZATION ---

def init_ux_session(user_id: str = None):
    """Initialize UX-related session state."""
    if "ux_initialized" not in st.session_state:
        st.session_state.ux_initialized = True
        st.session_state.show_welcome = check_first_time_user(user_id)
        st.session_state.show_guided_tour = False
        st.session_state.contextual_help = {}
        st.session_state.smart_suggestions = []

# Export main functions for easy importing
__all__ = [
    'add_tooltip_icon',
    'create_labeled_icon',
    'show_welcome_modal',
    'show_guided_tour',
    'show_contextual_help',
    'get_smart_suggestions',
    'show_progress_indicator',
    'show_success_message',
    'show_error_message',
    'create_status_badge',
    'show_feature_discovery',
    'check_first_time_user',
    'onboarding'
]
