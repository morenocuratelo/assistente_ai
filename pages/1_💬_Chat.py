# Pagina Chat - Interfaccia principale con memoria utente persistente
import streamlit as st
import time
from datetime import datetime

# Import delle funzionalità necessarie
from config import get_chat_llm
from file_utils import (
    get_papers_dataframe,
    get_user_chat_sessions,
    create_chat_session,
    get_chat_messages,
    save_chat_message,
    save_chat_history_entry,
    get_user_chat_history,
    get_user_memory_summary
)
from file_utils import get_archive_tree  # Aggiunto per la navigazione dei documenti
import knowledge_structure

# --- CONFIGURAZIONE CHAT ---
CHAT_MODEL = get_chat_llm()

def main():
    """Main function for the chat page with user sessions."""
    st.set_page_config(page_title="💬 Chat - Archivista AI", page_icon="💬", layout="wide")

    # VERIFICA AUTENTICAZIONE
    if 'user_id' not in st.session_state or not st.session_state['user_id']:
        st.error("**Accesso Negato** 🔒")
        st.markdown("Devi essere loggato per accedere alla chat. Clicca il pulsante **Login** nella sidebar.")
        if st.button("🔐 Vai al Login", type="primary"):
            st.switch_page("pages/login.py")
        return

    user_id = st.session_state['user_id']
    username = st.session_state.get('username', 'Utente')

    # Inizializzazione sessione chat se necessario
    if 'current_session_id' not in st.session_state:
        st.session_state['current_session_id'] = None
    if 'chat_messages' not in st.session_state:
        st.session_state['chat_messages'] = []

    # Header con informazioni utente
    col_title, col_user = st.columns([0.7, 0.3])
    with col_title:
        st.title("💬 Chat con l'Archivio")
        st.caption(f" Benvenuto {username}! Fai domande sui tuoi documenti e ottieni risposte intelligenti.")
    with col_user:
        if st.button("🚪 Logout", help="Disconnetti dal sistema"):
            for key in ['user_id', 'username', 'current_session_id', 'chat_messages']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

    # Layout 3 colonne
    col_left, col_center, col_right = st.columns([0.25, 0.5, 0.25])

    with col_left:
        show_chat_controls(user_id, username)

    with col_center:
        show_chat_interface(user_id)

    with col_right:
        show_document_previews()

def show_chat_controls(user_id, username):
    """Controlli per la gestione delle sessioni chat."""
    st.markdown("### 🎭 Sessioni Chat")

    # Lista delle sessioni esistenti
    try:
        sessions = get_user_chat_sessions(user_id)
    except Exception as e:
        st.error(f"Errore nel caricamento delle sessioni: {e}")
        sessions = []

    if sessions:
        st.markdown("##### Sessioni Recenti")
        session_names = ["Nuova Sessione..."] + [f"{s['session_name']} ({s['last_updated'][:10]})" for s in sessions]

        selected_session = st.selectbox(
            "Seleziona Sessione:",
            session_names,
            key="session_selector"
        )

        # Gestione cambio sessione
        if selected_session == "Nuova Sessione...":
            if st.session_state.get('current_session_id') is not None:
                st.session_state['current_session_id'] = None
                st.session_state['chat_messages'] = []
        else:
            # Trova la sessione selezionata
            for session in sessions:
                if f"{session['session_name']} ({session['last_updated'][:10]})" == selected_session:
                    if st.session_state.get('current_session_id') != session['id']:
                        st.session_state['current_session_id'] = session['id']
                        # Carica messaggi della sessione
                        load_session_messages(session['id'])
                    break
    else:
        st.info("Nessuna sessione trovata. Inizia da una **Nuova Sessione**.")

    st.divider()

    # Controlli sessione
    current_session_id = st.session_state.get('current_session_id')

    if current_session_id:
        if st.button("🗑️ Cancella Messaggi", help="Cancella tutti i messaggi di questa sessione"):
            # Cancella messaggi dalla UI (non dal DB per ora)
            st.session_state['chat_messages'] = []
            st.rerun()
    else:
        # Form per creare nuova sessione
        st.markdown("##### Nuova Sessione")
        with st.form("new_session_form"):
            session_name = st.text_input("Nome Sessione", value=f"Sessione del {datetime.now().strftime('%d/%m/%Y')}")
            create_button = st.form_submit_button("➕ Crea Sessione")

            if create_button and session_name:
                try:
                    new_session_id = create_chat_session(user_id, session_name)
                    st.session_state['current_session_id'] = new_session_id
                    st.session_state['chat_messages'] = []
                    st.success(f"Sessione '{session_name}' creata!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Errore nella creazione della sessione: {e}")

    st.divider()

    # Statistiche
    st.markdown("### 📊 Statistiche")
    total_sessions = len(get_user_chat_sessions(user_id))
    st.metric("Sessioni Totali", total_sessions)

def show_chat_interface(user_id):
    """Interfaccia principale della chat."""
    st.markdown("### 💭 Conversazione")

    # Mostra nome sessione corrente
    current_session_id = st.session_state.get('current_session_id')
    if current_session_id:
        st.caption(f"Sessione attiva: {get_session_name(current_session_id)}")
    else:
        st.caption("Nessuna sessione attiva - crea una nuova sessione per iniziare")

    # Area messaggi
    chat_container = st.container(height=400)

    with chat_container:
        if st.session_state['chat_messages']:
            for msg in st.session_state['chat_messages']:
                if msg['type'] == 'user':
                    st.markdown(f"**👤 Tu:** {msg['content']}")
                else:
                    st.markdown(f"**🤖 AI:** {msg['content']}")
                st.markdown("---")
        else:
            st.markdown("*Nessun messaggio ancora. Inizia la conversazione!* 💬")
            st.markdown("**Suggerimenti:**")
            st.markdown("- Chiedi informazioni su documenti specifici")
            st.markdown("- Richiedi riassunti di argomenti")
            st.markdown("- Fai domande comparative tra documenti")

    # Input utente
    if current_session_id or st.session_state.get('current_session_id') is None:
        st.markdown("#### 💬 Nuovo Messaggio")
        user_input = st.text_area(
            "Scrivi la tua domanda:",
            height=80,
            placeholder="Fai una domanda sui tuoi documenti...",
            label_visibility="collapsed"
        )

        col_send, col_clear = st.columns([0.8, 0.2])
        with col_send:
            send_button = st.button("📤 Invia", type="primary", use_container_width=True)
        with col_clear:
            if st.button("🗑️ Cancella", help="Cancella il testo inserito"):
                user_input = ""

        if send_button and user_input.strip():
            process_user_message(user_id, current_session_id, user_input.strip())

def process_user_message(user_id, session_id, user_input):
    """Processa il messaggio dell'utente e genera risposta AI."""
    try:
        # Assicurati che ci sia una sessione attiva
        if session_id is None:
            # Crea automaticamente una nuova sessione
            session_name = f"Autogenerata {datetime.now().strftime('%H:%M')}"
            session_id = create_chat_session(user_id, session_name)
            st.session_state['current_session_id'] = session_id

        # Aggiungi messaggio utente
        timestamp = datetime.now().isoformat()
        user_msg = {
            'type': 'user',
            'content': user_input,
            'timestamp': timestamp
        }
        st.session_state['chat_messages'].append(user_msg)

        # Salva messaggio utente nel DB
        save_chat_message(session_id, 'user', user_input)

        # Mostra messaggio utente
        with st.spinner("🤖 Elaborando risposta..."):
            # Ottieni contesto dai documenti
            context = get_chat_context(user_input)

            # Ottieni memoria conversazionale dell'utente
            memory_summary = get_user_memory_summary(user_id)

            # Combina contesto documenti con memoria utente
            full_context = f"{context}\\n\\n{memory_summary}"

            # Genera risposta AI
            from prompt_manager import get_prompt
            prompt_template = get_prompt("CHAT_ASSISTANT_PROMPT")
            response = CHAT_MODEL.complete(
                prompt_template.format(context_str=full_context, query_str=user_input)
            )
            ai_response = str(response).strip()

        # Aggiungi risposta AI
        ai_msg = {
            'type': 'ai',
            'content': ai_response,
            'timestamp': datetime.now().isoformat()
        }
        st.session_state['chat_messages'].append(ai_msg)

        # Salva risposta AI nel DB
        save_chat_message(session_id, 'ai', ai_response)

        # Salva nella cronologia generale (opzionale - disabilitato per ora)
        # save_chat_history_entry(user_id, user_input, context, ai_response)

        st.success("Risposta ricevuta!")
        st.rerun()

    except Exception as e:
        st.error(f"Errore nella elaborazione del messaggio: {e}")
        print(f"Debug - Errore chat: {e}")

def get_chat_context(query):
    """Ottieni contesto rilevante per la query."""
    try:
        # Per ora, usa una ricerca semplice sui documenti indicizzati
        papers_df = get_papers_dataframe()

        if papers_df.empty:
            return "Nessun documento disponibile nel database."

        # Ricerca semplice per parole chiave nella query
        context_parts = []
        query_lower = query.lower()

        for _, paper in papers_df.iterrows():
            if paper['formatted_preview'] and any(
                keyword in paper['formatted_preview'].lower() or
                keyword in paper.get('title', '').lower()
                for keyword in query_lower.split()
            ):
                context_parts.append(f"""
**Documento: {paper.get('title', paper['file_name'])}**
Categoria: {paper.get('category_name', 'N/A')}
{chr(10).join(paper['formatted_preview'].split('\\n')[:5])}...
                """)

                if len(context_parts) >= 3:  # Limita a 3 documenti
                    break

        if context_parts:
            return "\\n".join(context_parts)
        else:
            return "Nessun documento specifico trovato per la query. Risponderò basandomi sulla conoscenza generale."

    except Exception as e:
        print(f"Errore nel recupero contesto: {e}")
        return "Errore nel recupero del contesto. Risponderò basandomi sulla conoscenza generale."

def load_session_messages(session_id):
    """Carica i messaggi di una sessione nel session state."""
    try:
        messages = get_chat_messages(session_id)
        st.session_state['chat_messages'] = [{
            'type': msg['message_type'],
            'content': msg['content'],
            'timestamp': msg['timestamp']
        } for msg in messages]
    except Exception as e:
        st.error(f"Errore nel caricamento dei messaggi: {e}")
        st.session_state['chat_messages'] = []

def get_session_name(session_id):
    """Ottieni il nome della sessione corrente."""
    try:
        sessions = get_user_chat_sessions(st.session_state['user_id'])
        for session in sessions:
            if session['id'] == session_id:
                return session['session_name']
        return "Sessione sconosciuta"
    except:
        return "Sessione corrente"

def show_document_previews():
    """Mostra anteprime documenti selezionati."""
    st.markdown("### 📖 Anteprime Documenti")

    papers_df = get_papers_dataframe()

    if papers_df.empty:
        st.info("📋 Nessun documento disponibile")
        return

    # Selettore documenti
    doc_titles = ["Seleziona documento..."] + papers_df['title'].fillna(papers_df['file_name']).tolist()

    selected_doc = st.selectbox(
        "Documento:",
        doc_titles,
        key="selected_doc_for_preview"
    )

    if selected_doc and selected_doc != "Seleziona documento...":
        doc_row = papers_df[papers_df['title'] == selected_doc] if selected_doc in papers_df['title'].values else None
        if doc_row is None:
            doc_row = papers_df[papers_df['file_name'] == selected_doc]

        if not doc_row.empty:
            doc_data = doc_row.iloc[0]

            with st.expander(f"📄 {selected_doc}", expanded=True):
                st.markdown(f"**Titolo:** {doc_data.get('title', 'N/A')}")
                st.markdown(f"**Categoria:** {doc_data.get('category_name', 'N/A')}")
                st.markdown(f"**File:** {doc_data['file_name']}")
                st.markdown(f"**Processato:** {doc_data.get('processed_at', 'N/A')[:10] if doc_data.get('processed_at') else 'N/A'}")

                if doc_data.get('formatted_preview'):
                    st.markdown("**Anteprima:**")
                    st.info(doc_data['formatted_preview'][:500] + "..." if len(str(doc_data['formatted_preview'])) > 500 else str(doc_data['formatted_preview']))
                else:
                    st.warning("Anteprima non disponibile")

                # Pulsante modifica anteprima
                if st.button("✏️ Modifica Anteprima", key="chat_edit_preview"):
                    st.session_state.edit_paper = doc_data['file_name']
                    st.switch_page("pages/3_📝_Editor.py")

                # Link ai metadati per debug
                if st.checkbox("Mostra metadati completi", key="show_debug_info"):
                    st.json(doc_data.to_dict())

if __name__ == "__main__":
    main()
