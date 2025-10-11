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
    Crea le tabelle del database se non esistono,
    garantendo la struttura completa per l'applicazione.
    """
    # Create directory if it doesn't exist
    os.makedirs(DB_STORAGE_DIR, exist_ok=True)

    try:
        with db_connect() as conn:
            cursor = conn.cursor()

            # Tabella documenti esistente
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

            # Aggiungi colonne accademiche se non esistono
            cursor.execute("PRAGMA table_info(papers)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'keywords' not in columns:
                cursor.execute("ALTER TABLE papers ADD COLUMN keywords TEXT")  # JSON array
            if 'ai_tasks' not in columns:
                cursor.execute("ALTER TABLE papers ADD COLUMN ai_tasks TEXT")  # JSON object

            # Tabelle per il sistema utenti e memoria chat
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_updated TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    message_type TEXT NOT NULL CHECK (message_type IN ('user', 'ai')),
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions (id) ON DELETE CASCADE
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    query TEXT NOT NULL,
                    context_used TEXT,
                    response TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)

            # Tabelle per il sistema accademico universitario
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS courses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    course_name TEXT NOT NULL,
                    course_code TEXT UNIQUE,
                    description TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lectures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_id INTEGER NOT NULL,
                    lecture_title TEXT NOT NULL,
                    lecture_date TEXT,
                    description TEXT,
                    keywords TEXT,  -- JSON array of keywords
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS materials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lecture_id INTEGER NULL,  -- Can be uncategorized
                    course_id INTEGER NULL,
                    file_name TEXT NOT NULL,
                    material_type TEXT CHECK (material_type IN ('lecture_notes', 'handout', 'assignment', 'reading', 'other')),
                    description TEXT,
                    processed_at TEXT,
                    FOREIGN KEY (lecture_id) REFERENCES lectures (id) ON DELETE SET NULL,
                    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE SET NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    course_id INTEGER NULL,
                    lecture_id INTEGER NULL,
                    task_title TEXT NOT NULL,
                    task_description TEXT,
                    priority TEXT CHECK (priority IN ('low', 'medium', 'high')),
                    task_type TEXT CHECK (task_type IN ('short_term', 'medium_term', 'long_term')),
                    due_date TEXT,
                    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled')),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE SET NULL,
                    FOREIGN KEY (lecture_id) REFERENCES lectures (id) ON DELETE SET NULL
                )
            """)

            # Tabelle per il grafo della conoscenza (Phase 3)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS concept_entities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    entity_type TEXT NOT NULL, -- 'concept', 'theory', 'author', 'formula', 'technique', 'method'
                    entity_name TEXT NOT NULL,
                    entity_description TEXT,
                    source_file_name TEXT NOT NULL,
                    confidence_score REAL DEFAULT 0.5,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS concept_relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    source_entity_id INTEGER NOT NULL,
                    target_entity_id INTEGER NOT NULL,
                    relationship_type TEXT NOT NULL, -- 'proposed_by', 'related_to', 'part_of', 'prerequisite_for', 'example_of', 'contradicts', 'extends'
                    relationship_description TEXT,
                    confidence_score REAL DEFAULT 0.5,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                    FOREIGN KEY (source_entity_id) REFERENCES concept_entities (id) ON DELETE CASCADE,
                    FOREIGN KEY (target_entity_id) REFERENCES concept_entities (id) ON DELETE CASCADE
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_xp (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    xp_amount INTEGER NOT NULL,
                    xp_source TEXT NOT NULL, -- 'task_completed', 'document_uploaded', 'quiz_passed', 'study_session', 'achievement_unlocked'
                    xp_description TEXT,
                    source_id INTEGER, -- ID of the source (task_id, quiz_id, etc.)
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_achievements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    achievement_type TEXT NOT NULL, -- 'early_bird', 'stakhanovist', 'marathon_runner', 'knowledge_builder', etc.
                    achievement_title TEXT NOT NULL,
                    achievement_description TEXT,
                    earned_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                    UNIQUE(user_id, achievement_type) -- One achievement type per user
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS study_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_start TEXT NOT NULL,
                    session_end TEXT,
                    duration_minutes INTEGER,
                    course_id INTEGER NULL,
                    topics_covered TEXT, -- JSON array of topic strings
                    notes TEXT,
                    productivity_rating INTEGER CHECK (productivity_rating >= 1 AND productivity_rating <= 5),
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE SET NULL
                )
            """)

            conn.commit()
            print("✅ Database verificato: tutte le tabelle sono pronte.")
    except sqlite3.Error as e:
        print(f"❌ Errore nella creazione delle tabelle database: {e}")
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

# --- FUNZIONI PER LA GESTIONE UTENTI ---

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    try:
        import bcrypt
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    except ImportError:
        # Fallback to hashlib if bcrypt is not available
        import hashlib
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    try:
        import bcrypt
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except ImportError:
        # Fallback to hashlib if bcrypt is not available
        import hashlib
        return hashlib.sha256(password.encode('utf-8')).hexdigest() == hashed

def create_user(username: str, password: str) -> int:
    """
    Crea un nuovo utente nel database.
    Returns user ID if successful, raises exception if username exists.
    """
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            from datetime import datetime
            created_at = datetime.now().isoformat()
            password_hash = hash_password(password)
            cursor.execute(
                "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                (username, password_hash, created_at)
            )
            conn.commit()
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        raise ValueError(f"Username '{username}' già esistente")

def authenticate_user(username: str, password: str) -> dict:
    """
    Autentica un utente.
    Returns user dict with id and username if successful, None if failed.
    """
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, username, password_hash FROM users WHERE username = ?",
                (username,)
            )
            user = cursor.fetchone()
            if user and verify_password(password, user['password_hash']):
                return {'id': user['id'], 'username': user['username']}
            return None
    except Exception as e:
        print(f"Errore durante l'autenticazione: {e}")
        return None

def get_user_by_id(user_id: int) -> dict:
    """Recupera informazioni utente per ID."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, created_at FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            return dict(user) if user else None
    except Exception as e:
        print(f"Errore nel recupero utente: {e}")
        return None

# --- FUNZIONI PER LA GESTIONE DELLE SESSIONI CHAT ---

def create_chat_session(user_id: int, session_name: str) -> int:
    """Crea una nuova sessione di chat per l'utente."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            from datetime import datetime
            now = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO chat_sessions (user_id, session_name, created_at, last_updated) VALUES (?, ?, ?, ?)",
                (user_id, session_name, now, now)
            )
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        print(f"Errore nella creazione della sessione: {e}")
        raise

def get_user_chat_sessions(user_id: int) -> list:
    """Recupera tutte le sessioni chat dell'utente."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM chat_sessions WHERE user_id = ? ORDER BY last_updated DESC",
                (user_id,)
            )
            sessions = cursor.fetchall()
            return [dict(session) for session in sessions]
    except Exception as e:
        print(f"Errore nel recupero delle sessioni: {e}")
        return []

def save_chat_message(session_id: int, message_type: str, content: str):
    """Salva un messaggio nella sessione chat."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            from datetime import datetime
            timestamp = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO chat_messages (session_id, message_type, content, timestamp) VALUES (?, ?, ?, ?)",
                (session_id, message_type, content, timestamp)
            )
            cursor.execute(
                "UPDATE chat_sessions SET last_updated = ? WHERE id = ?",
                (timestamp, session_id)
            )
            conn.commit()
    except Exception as e:
        print(f"Errore nel salvataggio messaggio: {e}")

def get_chat_messages(session_id: int) -> list:
    """Recupera tutti i messaggi di una sessione chat."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY timestamp",
                (session_id,)
            )
            messages = cursor.fetchall()
            return [dict(msg) for msg in messages]
    except Exception as e:
        print(f"Errore nel recupero messaggi: {e}")
        return []

def save_chat_history_entry(user_id: int, query: str, context_used: str, response: str):
    """Salva una voce nella cronologia chat dell'utente."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            from datetime import datetime
            timestamp = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO user_chat_history (user_id, query, context_used, response, timestamp) VALUES (?, ?, ?, ?, ?)",
                (user_id, query, context_used, response, timestamp)
            )
            conn.commit()
    except Exception as e:
        print(f"Errore nel salvataggio cronologia: {e}")

def get_user_chat_history(user_id: int, limit: int = 50) -> list:
    """Recupera la cronologia delle chat dell'utente (più recenti prima)."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM user_chat_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
                (user_id, limit)
            )
            history = cursor.fetchall()
            return [dict(entry) for entry in history]
    except Exception as e:
        print(f"Errore nel recupero cronologia: {e}")
        return []

def get_user_memory_summary(user_id: int, max_sessions: int = 10) -> str:
    """
    Crea un riassunto della memoria conversazionale dell'utente.
    Questo riassunto viene fornito all'AI per mantenere coerenza tra le conversazioni.
    """
    try:
        from config import get_chat_llm
        chat_model = get_chat_llm()

        # Ottieni le sessioni più recenti con i relativi messaggi
        sessions = get_user_chat_sessions(user_id)

        if not sessions:
            return "Questo è un nuovo utente senza precedenti conversazioni."

        # Prendi solo le sessioni più recenti
        recent_sessions = sessions[:max_sessions]
        memory_parts = []

        for session in recent_sessions:
            session_id = session['id']
            messages = get_chat_messages(session_id)

            if messages:
                # Costruisci la conversazione come testo
                conversation = f"\nSessione: {session['session_name']} ({session['created_at'][:10]})\n"
                for msg in messages:
                    if msg['message_type'] == 'user':
                        conversation += f"U: {msg['content'][:200]}{'...' if len(msg['content']) > 200 else ''}\n"
                    else:
                        conversation += f"A: {msg['content'][:200]}{'...' if len(msg['content']) > 200 else ''}\n"

                memory_parts.append(conversation)

        if not memory_parts:
            return "L'utente ha sessioni ma nessuna conversazione registrata."

        # Combina tutte le conversazioni
        full_memory = "\n---\n".join(memory_parts)

        # Usa l'AI per creare un riassunto conciso
        summary_prompt = """
Sei un assistente specializzato nel creare riassunti delle conversazioni passate di un utente.
Analizza le seguenti conversazioni e crea un breve riassunto che catturi:

1. I principali argomenti discussi
2. Le preferenze dell'utente
3. Il livello di conoscenza tecnica
4. Qualsiasi pattern comportamentale significativo

Mantieni il riassunto conciso (max 300 parole) e focalizzati sui dettagli rilevanti per future interazioni.

CONVERSAZIONI PASSATE:
{memory_text}

RIASSUNTO MEMORIA UTENTE:
"""

        summary_response = chat_model.complete(
            summary_prompt.format(memory_text=full_memory[:2000])  # Limita input per evitare token limit
        )

        summary = str(summary_response).strip()

        # Se il riassunto è troppo lungo, truncalo
        if len(summary) > 500:
            summary = summary[:500] + "..."

        return f"Riassunto delle interazioni passate con l'utente: {summary}"

    except Exception as e:
        print(f"Errore nella generazione del riassunto memoria: {e}")
        return "Nessuna memoria conversazionale disponibile (errore nel recupero)."

# --- FUNZIONI PER LA GESTIONE ACCADEMICA ---

def create_course(user_id: int, course_name: str, course_code: str = None, description: str = None) -> int:
    """Crea un nuovo corso per l'utente."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            from datetime import datetime
            now = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO courses (user_id, course_name, course_code, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, course_name, course_code, description, now, now)
            )
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        print(f"Errore nella creazione del corso: {e}")
        raise

def get_user_courses(user_id: int) -> list:
    """Recupera tutti i corsi dell'utente."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM courses WHERE user_id = ? ORDER BY updated_at DESC",
                (user_id,)
            )
            courses = cursor.fetchall()
            return [dict(course) for course in courses]
    except Exception as e:
        print(f"Errore nel recupero dei corsi: {e}")
        return []

def update_course(course_id: int, course_name: str = None, course_code: str = None, description: str = None):
    """Aggiorna un corso."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            from datetime import datetime
            now = datetime.now().isoformat()
            update_fields = []
            values = []
            if course_name is not None:
                update_fields.append("course_name = ?")
                values.append(course_name)
            if course_code is not None:
                update_fields.append("course_code = ?")
                values.append(course_code)
            if description is not None:
                update_fields.append("description = ?")
                values.append(description)
            update_fields.append("updated_at = ?")
            values.append(now)
            values.append(course_id)

            query = f"UPDATE courses SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, tuple(values))
            conn.commit()
    except Exception as e:
        print(f"Errore nell'aggiornamento del corso: {e}")
        raise

def delete_course(course_id: int):
    """Elimina un corso."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM courses WHERE id = ?", (course_id,))
            conn.commit()
    except Exception as e:
        print(f"Errore nell'eliminazione del corso: {e}")
        raise

def create_lecture(course_id: int, lecture_title: str, lecture_date: str = None, description: str = None, keywords: list = None) -> int:
    """Crea una nuova lezione per un corso."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            from datetime import datetime
            now = datetime.now().isoformat()
            keywords_json = json.dumps(keywords) if keywords else None
            cursor.execute(
                "INSERT INTO lectures (course_id, lecture_title, lecture_date, description, keywords, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (course_id, lecture_title, lecture_date, description, keywords_json, now, now)
            )
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        print(f"Errore nella creazione della lezione: {e}")
        raise

def get_course_lectures(course_id: int) -> list:
    """Recupera tutte le lezioni di un corso."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM lectures WHERE course_id = ? ORDER BY lecture_date DESC, created_at DESC",
                (course_id,)
            )
            lectures = cursor.fetchall()
            result = []
            for lecture in lectures:
                lecture_dict = dict(lecture)
                if lecture_dict['keywords']:
                    lecture_dict['keywords'] = json.loads(lecture_dict['keywords'])
                result.append(lecture_dict)
            return result
    except Exception as e:
        print(f"Errore nel recupero delle lezioni: {e}")
        return []

def update_lecture(lecture_id: int, lecture_title: str = None, lecture_date: str = None, description: str = None, keywords: list = None):
    """Aggiorna una lezione."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            from datetime import datetime
            now = datetime.now().isoformat()
            update_fields = []
            values = []
            if lecture_title is not None:
                update_fields.append("lecture_title = ?")
                values.append(lecture_title)
            if lecture_date is not None:
                update_fields.append("lecture_date = ?")
                values.append(lecture_date)
            if description is not None:
                update_fields.append("description = ?")
                values.append(description)
            if keywords is not None:
                update_fields.append("keywords = ?")
                values.append(json.dumps(keywords))
            update_fields.append("updated_at = ?")
            values.append(now)
            values.append(lecture_id)

            query = f"UPDATE lectures SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, tuple(values))
            conn.commit()
    except Exception as e:
        print(f"Errore nell'aggiornamento della lezione: {e}")
        raise

def create_material(lecture_id: int = None, course_id: int = None, file_name: str = None, material_type: str = 'other', description: str = None) -> int:
    """Crea una nuova associazione materiale."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            from datetime import datetime
            now = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO materials (lecture_id, course_id, file_name, material_type, description, processed_at) VALUES (?, ?, ?, ?, ?, ?)",
                (lecture_id, course_id, file_name, material_type, description, now)
            )
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        print(f"Errore nella creazione del materiale: {e}")
        raise

def create_task(user_id: int, course_id: int = None, lecture_id: int = None, task_title: str = None, task_description: str = None, priority: str = 'medium', task_type: str = 'medium_term', due_date: str = None, status: str = 'pending') -> int:
    """Crea una nuova attività."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            from datetime import datetime
            now = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO tasks (user_id, course_id, lecture_id, task_title, task_description, priority, task_type, due_date, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (user_id, course_id, lecture_id, task_title, task_description, priority, task_type, due_date, status, now, now)
            )
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        print(f"Errore nella creazione del task: {e}")
        raise

def get_user_tasks(user_id: int) -> list:
    """Recupera tutte le attività dell'utente."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM tasks WHERE user_id = ? ORDER BY due_date ASC, created_at DESC",
                (user_id,)
            )
            tasks = cursor.fetchall()
            return [dict(task) for task in tasks]
    except Exception as e:
        print(f"Errore nel recupero delle attività: {e}")
        return []

def update_task(task_id: int, task_title: str = None, task_description: str = None, priority: str = None, task_type: str = None, due_date: str = None, status: str = None):
    """Aggiorna un'attività."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            from datetime import datetime
            now = datetime.now().isoformat()
            update_fields = []
            values = []
            if task_title is not None:
                update_fields.append("task_title = ?")
                values.append(task_title)
            if task_description is not None:
                update_fields.append("task_description = ?")
                values.append(task_description)
            if priority is not None:
                update_fields.append("priority = ?")
                values.append(priority)
            if task_type is not None:
                update_fields.append("task_type = ?")
                values.append(task_type)
            if due_date is not None:
                update_fields.append("due_date = ?")
                values.append(due_date)
            if status is not None:
                update_fields.append("status = ?")
                values.append(status)
            update_fields.append("updated_at = ?")
            values.append(now)
            values.append(task_id)

            query = f"UPDATE tasks SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, tuple(values))
            conn.commit()
    except Exception as e:
        print(f"Errore nell'aggiornamento del task: {e}")
        raise

def delete_task(task_id: int):
    """Elimina un'attività."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
    except Exception as e:
        print(f"Errore nell'eliminazione del task: {e}")
        raise

# --- FUNZIONI PER LA GESTIONE DEL GRAFO DELLA CONOSCENZA ---

def create_concept_entity(user_id: int, entity_type: str, entity_name: str, source_file_name: str, entity_description: str = None, confidence_score: float = 0.5) -> int:
    """Crea una nuova entità concettuale."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            from datetime import datetime
            now = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO concept_entities (user_id, entity_type, entity_name, entity_description, source_file_name, confidence_score, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user_id, entity_type, entity_name, entity_description, source_file_name, confidence_score, now)
            )
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        print(f"Errore nella creazione dell'entità concettuale: {e}")
        raise

def create_concept_relationship(user_id: int, source_entity_name: str, target_entity_name: str, relationship_type: str, relationship_description: str = None, confidence_score: float = 0.5) -> int:
    """Crea una nuova relazione concettuale."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()

            # Trova gli ID delle entità
            cursor.execute("SELECT id FROM concept_entities WHERE user_id = ? AND entity_name = ?", (user_id, source_entity_name))
            source_result = cursor.fetchone()
            cursor.execute("SELECT id FROM concept_entities WHERE user_id = ? AND entity_name = ?", (user_id, target_entity_name))
            target_result = cursor.fetchone()

            if not source_result or not target_result:
                raise ValueError(f"Entità non trovate: {source_entity_name}, {target_entity_name}")

            source_entity_id = source_result['id']
            target_entity_id = target_result['id']

            from datetime import datetime
            now = datetime.now().isoformat()

            cursor.execute(
                "INSERT INTO concept_relationships (user_id, source_entity_id, target_entity_id, relationship_type, relationship_description, confidence_score, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user_id, source_entity_id, target_entity_id, relationship_type, relationship_description, confidence_score, now)
            )
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        print(f"Errore nella creazione della relazione concettuale: {e}")
        raise

def get_user_knowledge_graph(user_id: int) -> dict:
    """Recupera l'intero grafo della conoscenza dell'utente."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()

            # Recupera tutte le entità
            cursor.execute("SELECT * FROM concept_entities WHERE user_id = ?", (user_id,))
            entities = [dict(entity) for entity in cursor.fetchall()]

            # Recupera tutte le relazioni
            cursor.execute("""
                SELECT r.*, e1.entity_name as source_name, e1.entity_type as source_type,
                       e2.entity_name as target_name, e2.entity_type as target_type
                FROM concept_relationships r
                JOIN concept_entities e1 ON r.source_entity_id = e1.id
                JOIN concept_entities e2 ON r.target_entity_id = e2.id
                WHERE r.user_id = ?
            """, (user_id,))
            relationships = [dict(rel) for rel in cursor.fetchall()]

            return {
                "entities": entities,
                "relationships": relationships
            }
    except Exception as e:
        print(f"Errore nel recupero del grafo della conoscenza: {e}")
        return {"entities": [], "relationships": []}

def get_entity_neighbors(user_id: int, entity_name: str, max_depth: int = 2) -> dict:
    """Recupera le entità collegate a una entità specifica entro una profondità massima."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()

            # Query complessa per trovare vicini
            query = """
                WITH RECURSIVE entity_paths AS (
                    -- Prima livello: entità di partenza
                    SELECT id as entity_id, entity_name, entity_type, 0 as depth
                    FROM concept_entities
                    WHERE user_id = ? AND entity_name = ?

                    UNION ALL

                    -- Livelli successivi tramite relazioni
                    SELECT DISTINCT
                        CASE
                            WHEN ep.entity_id = r.source_entity_id THEN r.target_entity_id
                            ELSE r.source_entity_id
                        END as entity_id,
                        ce.entity_name, ce.entity_type, ep.depth + 1 as depth
                    FROM entity_paths ep
                    JOIN concept_relationships r ON (
                        r.source_entity_id = ep.entity_id OR r.target_entity_id = ep.entity_id
                    )
                    JOIN concept_entities ce ON (
                        ce.id = CASE
                            WHEN ep.entity_id = r.source_entity_id THEN r.target_entity_id
                            ELSE r.source_entity_id
                        END
                    )
                    WHERE ep.depth < ? AND ce.user_id = ?
                )
                SELECT DISTINCT entity_id, entity_name, entity_type, depth
                FROM entity_paths
                ORDER BY depth, entity_name
            """

            cursor.execute(query, (user_id, entity_name, max_depth, user_id))
            entities = cursor.fetchall()

            # Recupera le relazioni tra queste entità
            if entities:
                entity_ids = [e['entity_id'] for e in entities]
                placeholders = ','.join('?' * len(entity_ids))

                cursor.execute(f"""
                    SELECT r.*, e1.entity_name as source_name, e1.entity_type as source_type,
                           e2.entity_name as target_name, e2.entity_type as target_type
                    FROM concept_relationships r
                    JOIN concept_entities e1 ON r.source_entity_id = e1.id
                    JOIN concept_entities e2 ON r.target_entity_id = e2.id
                    WHERE r.user_id = ? AND r.source_entity_id IN ({placeholders}) AND r.target_entity_id IN ({placeholders})
                """, [user_id] + entity_ids + entity_ids)

                relationships = cursor.fetchall()
            else:
                relationships = []

            return {
                "entities": [dict(e) for e in entities],
                "relationships": [dict(r) for r in relationships]
            }
    except Exception as e:
        print(f"Errore nel recupero dei vicini dell'entità: {e}")
        return {"entities": [], "relationships": []}

# --- FUNZIONI PER LA GESTIONE DEL SISTEMA XP E ACHIEVEMENTS ---

def award_xp(user_id: int, xp_amount: int, xp_source: str, xp_description: str, source_id: int = None):
    """Assegna XP all'utente."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            from datetime import datetime
            now = datetime.now().isoformat()

            cursor.execute(
                "INSERT INTO user_xp (user_id, xp_amount, xp_source, xp_description, source_id, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, xp_amount, xp_source, xp_description, source_id, now)
            )
            conn.commit()

            # Verifica se ci sono nuovi achievement da sbloccare
            check_and_award_achievements(user_id)

    except Exception as e:
        print(f"Errore nell'assegnazione dell'XP: {e}")
        raise

def get_user_total_xp(user_id: int) -> int:
    """Recupera il totale XP dell'utente."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COALESCE(SUM(xp_amount), 0) as total FROM user_xp WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            return result['total'] if result else 0
    except Exception as e:
        print(f"Errore nel recupero del totale XP: {e}")
        return 0

def get_user_xp_history(user_id: int, limit: int = 50) -> list:
    """Recupera la cronologia XP dell'utente."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM user_xp WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                (user_id, limit)
            )
            return [dict(entry) for entry in cursor.fetchall()]
    except Exception as e:
        print(f"Errore nel recupero della cronologia XP: {e}")
        return []

def check_and_award_achievements(user_id: int):
    """Verifica e assegna achievement basati sui progressi dell'utente."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()

            # Ottieni statistiche dell'utente
            total_xp = get_user_total_xp(user_id)
            courses_count = len(get_user_courses(user_id))
            tasks_completed = len([t for t in get_user_tasks(user_id) if t['status'] == 'completed'])
            documents_count = len(get_papers_dataframe())

            # Achievement disponibili con condizioni
            achievements = [
                {
                    'type': 'first_steps',
                    'title': 'Primi Passi',
                    'description': 'Hai creato il tuo primo corso!',
                    'condition': lambda: courses_count >= 1
                },
                {
                    'type': 'knowledge_builder',
                    'title': 'Costruttore di Conoscenza',
                    'description': 'Hai caricato 10 documenti!',
                    'condition': lambda: documents_count >= 10
                },
                {
                    'type': 'task_master',
                    'title': 'Maestro dei Task',
                    'description': 'Hai completato 25 attività!',
                    'condition': lambda: tasks_completed >= 25
                },
                {
                    'type': 'xp_hunter',
                    'title': 'Cacciatore di XP',
                    'description': 'Hai guadagnato 500 XP!',
                    'condition': lambda: total_xp >= 500
                },
                {
                    'type': 'scholar',
                    'title': 'Studioso',
                    'description': 'Hai creato 5 corsi diversi!',
                    'condition': lambda: courses_count >= 5
                }
            ]

            # Verifica quali achievement sono stati guadagnati
            from datetime import datetime
            now = datetime.now().isoformat()

            for achievement in achievements:
                if achievement['condition']():
                    # Verifica se già ottenuto
                    cursor.execute(
                        "SELECT id FROM user_achievements WHERE user_id = ? AND achievement_type = ?",
                        (user_id, achievement['type'])
                    )
                    if not cursor.fetchone():
                        # Assegna l'achievement
                        cursor.execute(
                            "INSERT INTO user_achievements (user_id, achievement_type, achievement_title, achievement_description, earned_at) VALUES (?, ?, ?, ?, ?)",
                            (user_id, achievement['type'], achievement['title'], achievement['description'], now)
                        )
                        # Bonus XP per achievement
                        award_xp(user_id, 50, 'achievement_unlocked', f"Achievement sbloccato: {achievement['title']}")

            conn.commit()

    except Exception as e:
        print(f"Errore nella verifica degli achievement: {e}")

def get_user_achievements(user_id: int) -> list:
    """Recupera tutti gli achievement dell'utente."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_achievements WHERE user_id = ? ORDER BY earned_at DESC", (user_id,))
            return [dict(achievement) for achievement in cursor.fetchall()]
    except Exception as e:
        print(f"Errore nel recupero degli achievement: {e}")
        return []

# --- FUNZIONI PER LA GESTIONE DELLE SESSIONI DI STUDIO ---

def start_study_session(user_id: int, course_id: int = None) -> int:
    """Avvia una nuova sessione di studio."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            from datetime import datetime
            now = datetime.now().isoformat()

            cursor.execute(
                "INSERT INTO study_sessions (user_id, session_start, course_id, created_at) VALUES (?, ?, ?, ?)",
                (user_id, now, course_id, now)
            )
            session_id = cursor.lastrowid
            conn.commit()
            return session_id
    except Exception as e:
        print(f"Errore nell'avvio della sessione di studio: {e}")
        raise

def end_study_session(session_id: int, topics_covered: list = None, notes: str = None, productivity_rating: int = 3, cursor=None):
    """Termina una sessione di studio."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            from datetime import datetime
            now = datetime.now().isoformat()

            # Calcola durata (in minuti)
            cursor.execute("SELECT session_start, user_id FROM study_sessions WHERE id = ?", (session_id,))
            result = cursor.fetchone()
            if result:
                start_time = datetime.fromisoformat(result['session_start'])
                end_time = datetime.fromisoformat(now)
                duration = int((end_time - start_time).total_seconds() / 60)
                session_user_id = result['user_id']

                topics_json = json.dumps(topics_covered) if topics_covered else None
                cursor.execute(
                    "UPDATE study_sessions SET session_end = ?, duration_minutes = ?, topics_covered = ?, notes = ?, productivity_rating = ? WHERE id = ?",
                    (now, duration, topics_json, notes, productivity_rating, session_id)
                )

                # Award XP basato sulla durata e produttività
                if duration > 0:
                    xp_amount = min(duration, 480) * productivity_rating // 10  # Max 480 minuti (8 ore)
                    if xp_amount > 0:
                        award_xp(session_user_id, xp_amount, 'study_session', f'Sessione di studio di {duration} minuti con rating {productivity_rating}', session_id)

                conn.commit()
    except Exception as e:
        print(f"Errore nella chiusura della sessione di studio: {e}")

def get_user_study_sessions(user_id: int, limit: int = 20) -> list:
    """Recupera le sessioni di studio dell'utente."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM study_sessions WHERE user_id = ? ORDER BY session_start DESC LIMIT ?",
                (user_id, limit)
            )
            sessions = cursor.fetchall()
            result = []
            for session in sessions:
                session_dict = dict(session)
                if session_dict['topics_covered']:
                    session_dict['topics_covered'] = json.loads(session_dict['topics_covered'])
                result.append(session_dict)
            return result
    except Exception as e:
        print(f"Errore nel recupero delle sessioni di studio: {e}")
        return []
