import streamlit as st
import sqlite3
import os
import pandas as pd
import json
from knowledge_structure import KNOWLEDGE_BASE_STRUCTURE

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
    # Create directory if it doesn't exist
    os.makedirs(DB_STORAGE_DIR, exist_ok=True)

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
            print("✅ Database verificato e tabella 'papers' pronta.")
    except sqlite3.Error as e:
        print(f"❌ Errore nella creazione della tabella database: {e}")
        raise

@st.cache_data(ttl=10)
def get_papers_dataframe():
    """Recupera i dati dei paper dal DB e li restituisce come DataFrame."""
    if not os.path.exists(METADATA_DB_FILE):
        return pd.DataFrame()  # Return empty DataFrame if no database exists
    
    try:
        with db_connect() as conn:
            df = pd.read_sql_query("SELECT * FROM papers ORDER BY category_id, title", conn)
            return df
    except Exception as e:
        print(f"Errore nel recupero dei paper: {e}")
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

def get_archive_tree():
    """
    Scans the categorized archive directory and builds a hierarchical tree structure
    with file metadata from the database. This serves as the single source of truth
    for the file explorer interface.

    Returns:
        dict: Nested structure representing the archive tree with the following format:
        {
            "P1_IL_PALCOSCENICO_COSMICO_E_BIOLOGICO": {
                "name": "Parte I: Il Palcoscenico Cosmico e Biologico",
                "path": "P1_IL_PALCOSCENICO_COSMICO_E_BIOLOGICO",
                "type": "category",
                "children": {
                    "C01": {
                        "name": "L'Universo e la Terra - La Nascita del Contesto",
                        "path": "P1_IL_PALCOSCENICO_COSMICO_E_BIOLOGICO/C01",
                        "type": "category",
                        "files": [...],
                        "subdirectories": {...}
                    }
                }
            }
        }
    """
    try:
        # First, get all papers from database for efficient lookup
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM papers")
            papers = cursor.fetchall()

        # Create a lookup dictionary for papers by file_name
        papers_dict = {paper['file_name']: paper for paper in papers}

        # Initialize the tree structure
        archive_tree = {}

        # Check if archive directory exists
        if not os.path.exists(CATEGORIZED_ARCHIVE_DIR):
            print(f"⚠️ Archive directory '{CATEGORIZED_ARCHIVE_DIR}' not found. Returning empty tree.")
            return archive_tree

        # Walk through the directory structure
        for root, dirs, files in os.walk(CATEGORIZED_ARCHIVE_DIR):
            # Calculate relative path from archive directory
            rel_path = os.path.relpath(root, CATEGORIZED_ARCHIVE_DIR)
            if rel_path == '.':
                rel_path = ''

            # Split path into parts for tree navigation
            path_parts = rel_path.split(os.sep) if rel_path else []

            # Navigate to the correct position in the tree
            current_node = archive_tree

            # Build the path through the tree
            for i, part in enumerate(path_parts):
                if part not in current_node:
                    # Determine if this is a part (P1-P5) or chapter (C01-C27)
                    if part.startswith('P') and len(part) > 10:  # Part identifier
                        # Find matching part in knowledge structure
                        for part_key, part_data in KNOWLEDGE_BASE_STRUCTURE.items():
                            if part_key == part:
                                current_node[part] = {
                                    "name": part_data["name"],
                                    "path": part,
                                    "type": "part",
                                    "children": {}
                                }
                                break
                    else:  # Chapter identifier
                        # Find the parent part and chapter info
                        if path_parts and path_parts[0] in KNOWLEDGE_BASE_STRUCTURE:
                            parent_part = KNOWLEDGE_BASE_STRUCTURE[path_parts[0]]
                            if part in parent_part["chapters"]:
                                current_node[part] = {
                                    "name": parent_part["chapters"][part],
                                    "path": f"{path_parts[0]}/{part}",
                                    "type": "chapter",
                                    "files": [],
                                    "subdirectories": {}
                                }

                current_node = current_node[part]
                if current_node["type"] in ["part", "chapter"]:
                    if "children" not in current_node:
                        current_node["children"] = {}
                    current_node = current_node["children"]

            # Process files in current directory
            for file_name in files:
                file_path = os.path.join(root, file_name)

                # Get file metadata
                file_stat = os.stat(file_path)
                file_size = file_stat.st_size
                file_mtime = file_stat.st_mtime

                # Get metadata from database
                paper_metadata = papers_dict.get(file_name, {})

                # Create file object
                file_obj = {
                    "name": file_name,
                    "path": os.path.relpath(file_path, CATEGORIZED_ARCHIVE_DIR),
                    "type": "file",
                    "size": file_size,
                    "modified_time": file_mtime,
                    "extension": os.path.splitext(file_name)[1].lower(),
                    # Database metadata
                    "title": paper_metadata.get('title', file_name),
                    "authors": paper_metadata.get('authors', ''),
                    "publication_year": paper_metadata.get('publication_year'),
                    "category_id": paper_metadata.get('category_id', ''),
                    "category_name": paper_metadata.get('category_name', ''),
                    "formatted_preview": paper_metadata.get('formatted_preview', ''),
                    "processed_at": paper_metadata.get('processed_at', ''),
                    # Processing status
                    "status": "indexed" if paper_metadata else "unindexed"
                }

                # Add file to current directory's files list
                if "files" not in current_node:
                    current_node["files"] = []
                current_node["files"].append(file_obj)

        return archive_tree

    except Exception as e:
        print(f"❌ Errore nella creazione dell'albero dell'archivio: {e}")
        return {}
