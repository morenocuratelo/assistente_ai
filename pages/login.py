"""
 Pagina di Login e Registrazione per Archivista AI
 Gestisce l'autenticazione degli utenti con Streamlit.
"""
import streamlit as st
from file_utils import create_user, authenticate_user

def main():
    st.set_page_config(page_title="🔐 Login - Archivista AI", page_icon="🔐", layout="centered")

    # Se l'utente è già loggato, mostra la pagina di benvenuto e permetti logout
    if 'user_id' in st.session_state and st.session_state['user_id'] is not None:
        show_logged_in_page()
        return

    # Titolo principale
    st.title("🔐 Archivista AI")
    st.markdown("### Accedi al tuo archivio personale di documenti")

    # Tabs per login/registrazione
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Registrazione"])

    with tab1:
        show_login_form()

    with tab2:
        show_registration_form()

def show_logged_in_page():
    """Redirect automaticamente alla dashboard quando utente è già loggato."""
    # Reindirizamento automatico e immediato alla dashboard
    st.switch_page("main.py")

def show_login_form():
    """Mostra il form di login."""
    st.subheader("Accedi al tuo account")

    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Inserisci il tuo username")
        password = st.text_input("Password", type="password", placeholder="Inserisci la password")

        submitted = st.form_submit_button("🔑 Accedi", type="primary", use_container_width=True)

        if submitted:
            if not username or not password:
                st.error("Per favore, inserisci username e password.")
                return

            user = authenticate_user(username, password)
            if user:
                st.session_state['user_id'] = user['id']
                st.session_state['username'] = user['username']
                st.success(f"Benvenuto, {user['username']}! Reindirizzamento alla dashboard...")
                st.switch_page("main.py")  # Redirect to dashboard
            else:
                st.error("Username o password non validi.")

def show_registration_form():
    """Mostra il form di registrazione."""
    st.subheader("Crea un nuovo account")
    st.caption("Compila tutti i campi per registrarti")

    with st.form("registration_form"):
        new_username = st.text_input("Username*", placeholder="Scegli un username unico")
        new_password = st.text_input("Password*", type="password", placeholder="Scegli una password sicura")
        confirm_password = st.text_input("Conferma Password*", type="password", placeholder="Ripeti la password")

        # Note sui requisiti
        st.caption("* Campo obbligatorio")

        submitted = st.form_submit_button("📝 Registrati", type="primary", use_container_width=True)

        if submitted:
            # Validazione input
            if not new_username or not new_password or not confirm_password:
                st.error("Per favore, compila tutti i campi obbligatori.")
                return

            if len(new_username) < 3:
                st.error("L'username deve essere di almeno 3 caratteri.")
                return

            if len(new_password) < 6:
                st.error("La password deve essere di almeno 6 caratteri.")
                return

            if new_password != confirm_password:
                st.error("Le password non corrispondono.")
                return

            # Tentativo di registrazione
            try:
                create_user(new_username, new_password)
                st.success("✅ Registrazione completata con successo!")

                # Login automatico dopo registrazione
                user = authenticate_user(new_username, new_password)
                if user:
                    st.session_state['user_id'] = user['id']
                    st.session_state['username'] = user['username']
                    st.success("Benvenuto nel sistema! Sarai reindirizzato alla tua dashboard...")
                    st.rerun()
                else:
                    st.warning("Registrazione completata, ma il login automatico ha fallito. Usa il form di login.")

            except ValueError as e:
                st.error(str(e))

def logout_user():
    """Effettua il logout dell'utente."""
    if 'user_id' in st.session_state:
        del st.session_state['user_id']
    if 'username' in st.session_state:
        del st.session_state['username']
    if 'current_session_id' in st.session_state:
        del st.session_state['current_session_id']
    st.rerun()

if __name__ == "__main__":
    main()
