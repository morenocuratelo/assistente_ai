import streamlit as st
import sqlite3
import os
import pandas as pd
import json

# --- CONFIGURAZIONE ---
DB_STORAGE_DIR = "db_memoria"
CATEGORIZED_ARCHIVE_DIR = "Dall_Origine_alla_Complessita"
METADATA_DB_FILE = os.path.join(DB_STORAGE_DIR, "metadata.sqlite")

def db_connect():
    """Stabilisce una connessione al database SQLite."""
    os.makedirs(DB_STORAGE_DIR, exist_ok=True)
    conn = sqlite3.connect(METADATA_DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def setup_database():
    """
    Crea la tabella 'papers' nel database se non esiste,
    garantendo che abbia tutte le colonne necessarie.
    """
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS papers (
                    file_name TEXT PRIMARY KEY,
                    title TEXT,
                    authors TEXT,
                    publication_year INTEGER,
                    category_id TEXT,
                    category_name TEXT,
                    formatted_preview TEXT,
                    processed_at TEXT
                )
            """)
            conn.commit()
            print("✅ Database verificato e pronto.")
    except sqlite3.Error as e:
        print(f"❌ Errore durante la configurazione del database: {e}")
        st.error(f"Errore critico del database: {e}")

@st.cache_data(ttl=10)
def get_papers_dataframe():
    """Recupera i dati dei paper dal DB e li restituisce come DataFrame."""
    try:
        with db_connect() as conn:
            df = pd.read_sql_query("SELECT * FROM papers ORDER BY category_id, title", conn)
            return df
    except (sqlite3.OperationalError, pd.io.sql.DatabaseError):
        # La tabella potrebbe non esistere ancora o essere vuota
        return pd.DataFrame()

def delete_paper(file_name: str):
    """
    Elimina un documento dal database e dal disco.
    """
    try:
        # 1. Recupera la categoria dal DB per trovare il file
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT category_id FROM papers WHERE file_name = ?", (file_name,))
            result = cursor.fetchone()
            if not result or not result['category_id']:
                st.error(f"Impossibile trovare la categoria per '{file_name}' nel database.")
                return False
            category_id = result['category_id']

        # 2. Elimina dal database
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM papers WHERE file_name = ?", (file_name,))
            conn.commit()

        # 3. Elimina il file fisico dalla sua cartella categorizzata
        file_path = os.path.join(CATEGORIZED_ARCHIVE_DIR, *category_id.split('/'), file_name)
        if os.path.exists(file_path):
            os.remove(file_path)
            st.success(f"'{file_name}' è stato eliminato con successo!")
            return True
        else:
            st.warning(f"File '{file_name}' non trovato nel percorso previsto: {file_path}. Rimosso solo dal DB.")
            return True
            
    except Exception as e:
        st.error(f"Errore durante l'eliminazione di '{file_name}': {e}")
        return False

# La funzione update_paper_metadata rimane invariata
def update_paper_metadata(file_name: str, new_data: dict):
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            set_clause = ", ".join([f"{key} = ?" for key in new_data.keys()])
            values = list(new_data.values()) + [file_name]
            query = f"UPDATE papers SET {set_clause} WHERE file_name = ?"
            cursor.execute(query, tuple(values))
            conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Errore database in update_paper_metadata: {e}")
        return False

def cleanup_missing_files():
    """
    Rimuove dal database i riferimenti a file che non esistono più fisicamente.
    Restituisce il numero di record eliminati.
    """
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT file_name, category_id FROM papers")
            papers = cursor.fetchall()

        removed_count = 0
        for paper in papers:
            file_name = paper['file_name']
            category_id = paper['category_id']

            # Verifica se il file esiste nella cartella categorizzata
            file_path = os.path.join(CATEGORIZED_ARCHIVE_DIR, *category_id.split('/'), file_name)

            if not os.path.exists(file_path):
                # Il file non esiste, rimuovilo dal database
                cursor.execute("DELETE FROM papers WHERE file_name = ?", (file_name,))
                removed_count += 1
                print(f"🗑️ Rimosso dal database: {file_name} (file non trovato: {file_path})")

        if removed_count > 0:
            conn.commit()
            print(f"✅ Pulizia completata: rimossi {removed_count} riferimenti a file inesistenti.")

        return removed_count

    except Exception as e:
        print(f"❌ Errore durante la pulizia del database: {e}")
        return 0
