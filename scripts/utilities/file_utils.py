import streamlit as st
import sqlite3
import os
import pandas as pd
import json
from knowledge_structure import (
    KNOWLEDGE_BASE_STRUCTURE,
    BayesianKnowledgeEntity,
    BayesianKnowledgeRelationship,
    EvidenceRecord,
    ConfidenceUpdateRequest,
    get_default_confidence_score,
    get_evidence_strength,
    calculate_confidence_update,
    validate_confidence_score
)
from datetime import datetime

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
                    updated_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)

            # Tabella per il tracciamento dello stato di processamento documenti
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS document_processing_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_name TEXT NOT NULL,
                    processing_state TEXT NOT NULL CHECK (processing_state IN (
                        'PENDING', 'QUEUED', 'PROCESSING', 'FAILED_PARSING',
                        'FAILED_EXTRACTION_API', 'FAILED_EXTRACTION_FORMAT',
                        'FAILED_INDEXING', 'FAILED_ARCHIVING', 'COMPLETED',
                        'MANUAL_INTERVENTION_REQUIRED'
                    )),
                    current_phase TEXT NOT NULL DEFAULT 'phase_1',
                    phase_started_at TEXT,
                    phase_completed_at TEXT,
                    error_message TEXT,
                    error_details TEXT, -- JSON con dettagli tecnici dell'errore
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    celery_task_id TEXT,
                    worker_node TEXT,
                    processing_metadata TEXT, -- JSON con metadati del processamento
                    quarantine_path TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(file_name)
                )
            """)

            # Tabella per il log strutturato degli errori
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processing_error_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_name TEXT NOT NULL,
                    processing_state TEXT NOT NULL,
                    error_category TEXT NOT NULL, -- 'IOError', 'ConnectionError', 'APIError', 'FormatError', 'IndexingError', 'ArchivingError'
                    error_type TEXT NOT NULL, -- 'critical', 'error', 'warning', 'info'
                    error_message TEXT NOT NULL,
                    error_details TEXT, -- JSON con stack trace e contesto
                    celery_task_id TEXT,
                    worker_node TEXT,
                    resolution_status TEXT DEFAULT 'open' CHECK (resolution_status IN ('open', 'investigating', 'resolved', 'ignored')),
                    resolution_notes TEXT,
                    created_at TEXT NOT NULL,
                    resolved_at TEXT,
                    FOREIGN KEY (file_name) REFERENCES document_processing_status(file_name) ON DELETE CASCADE
                )
            """)

            # Tabella per le metriche di processamento
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processing_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date_period TEXT NOT NULL, -- 'YYYY-MM-DD' o 'YYYY-MM-DD HH' per aggregazione oraria
                    total_files INTEGER DEFAULT 0,
                    files_pending INTEGER DEFAULT 0,
                    files_processing INTEGER DEFAULT 0,
                    files_completed INTEGER DEFAULT 0,
                    files_failed INTEGER DEFAULT 0,
                    avg_processing_time REAL, -- secondi
                    error_rate REAL, -- percentuale
                    quarantine_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    UNIQUE(date_period)
                )
            """)

            # Tabella per i file in quarantena
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quarantine_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_name TEXT NOT NULL,
                    original_path TEXT NOT NULL,
                    quarantine_path TEXT NOT NULL,
                    failure_reason TEXT NOT NULL,
                    failure_category TEXT NOT NULL,
                    error_details TEXT, -- JSON dettagliato
                    retry_eligible INTEGER DEFAULT 1, -- 1=può essere ritentato, 0=no
                    manual_review_required INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    reviewed_at TEXT,
                    review_notes TEXT,
                    review_decision TEXT CHECK (review_decision IN ('retry', 'delete', 'manual_fix', 'ignore')),
                    UNIQUE(file_name)
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
                    is_planned INTEGER DEFAULT 0, -- 0=storico, 1=pianificato
                    planned_date TEXT, -- Data pianificata per sessioni future
                    planned_duration INTEGER, -- Durata pianificata in minuti
                    priority_score REAL DEFAULT 0.5, -- Importanza calcolata (0-1)
                    ai_recommendation TEXT, -- Suggerimento IA per questa sessione
                    completed_at TEXT, -- Quando completata (per sessioni pianificate)
                    created_at TEXT NOT NULL,
                    updated_at TEXT, -- Ultima modifica
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE SET NULL
                )
            """)

            # Tabella per tracciamento attività utente (per dashboard intelligente)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    action_type TEXT NOT NULL, -- 'view_doc', 'edit_doc', 'create_doc', 'start_chat', 'complete_task', etc.
                    target_type TEXT, -- 'document', 'chat', 'task', 'course', etc.
                    target_id TEXT, -- ID del target (document_id, chat_session_id, task_id, etc.)
                    metadata TEXT, -- JSON con informazioni aggiuntive
                    timestamp TEXT NOT NULL,
                    session_id TEXT, -- Per raggruppare azioni per sessione
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)

            # Aggiungi campo is_new_user alla tabella users se non esiste
            cursor.execute("PRAGMA table_info(users)")
            user_columns = [col[1] for col in cursor.fetchall()]
            if 'is_new_user' not in user_columns:
                cursor.execute("ALTER TABLE users ADD COLUMN is_new_user INTEGER DEFAULT 1")

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
                        if part in KNOWLEDGE_BASE_STRUCTURE:
                            part_data = KNOWLEDGE_BASE_STRUCTURE[part]
                            current_node[part] = {
                                "name": part_data["name"],
                                "path": part,
                                "type": "part",
                                "children": {}
                            }
                        else:
                            # Handle unknown parts gracefully
                            current_node[part] = {
                                "name": f"Parte {part}",
                                "path": part,
                                "type": "part",
                                "children": {}
                            }
                    elif part == "UNCATEGORIZED":  # Special case for uncategorized content
                        current_node[part] = {
                            "name": "Contenuto Non Categorizzato",
                            "path": part,
                            "type": "part",
                            "children": {}
                        }
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
                            else:
                                # Handle unknown chapters gracefully
                                current_node[part] = {
                                    "name": f"Capitolo {part}",
                                    "path": f"{path_parts[0]}/{part}",
                                    "type": "chapter",
                                    "files": [],
                                    "subdirectories": {}
                                }
                        else:
                            # Handle cases where parent part is not in knowledge structure
                            current_node[part] = {
                                "name": f"Capitolo {part}",
                                "path": f"{path_parts[0]}/{part}" if path_parts else part,
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

                # Handle both sqlite3.Row objects and dictionaries
                if hasattr(paper_metadata, 'get'):
                    # It's already a dictionary-like object
                    title = paper_metadata.get('title', file_name)
                    authors = paper_metadata.get('authors', '')
                    publication_year = paper_metadata.get('publication_year')
                    category_id = paper_metadata.get('category_id', '')
                    category_name = paper_metadata.get('category_name', '')
                    formatted_preview = paper_metadata.get('formatted_preview', '')
                    processed_at = paper_metadata.get('processed_at', '')
                else:
                    # It's a sqlite3.Row object, convert to dict or access directly
                    title = getattr(paper_metadata, 'title', file_name)
                    authors = getattr(paper_metadata, 'authors', '')
                    publication_year = getattr(paper_metadata, 'publication_year', None)
                    category_id = getattr(paper_metadata, 'category_id', '')
                    category_name = getattr(paper_metadata, 'category_name', '')
                    formatted_preview = getattr(paper_metadata, 'formatted_preview', '')
                    processed_at = getattr(paper_metadata, 'processed_at', '')

                # Create file object
                file_obj = {
                    "name": file_name,
                    "path": os.path.relpath(file_path, CATEGORIZED_ARCHIVE_DIR),
                    "type": "file",
                    "size": file_size,
                    "modified_time": file_mtime,
                    "extension": os.path.splitext(file_name)[1].lower(),
                    # Database metadata
                    "title": title,
                    "authors": authors,
                    "publication_year": publication_year,
                    "category_id": category_id,
                    "category_name": category_name,
                    "formatted_preview": formatted_preview,
                    "processed_at": processed_at,
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

# --- ASSISTENTE CALENDARIZZATORE IA ---

def create_planned_study_session(user_id: int, planned_date: str, planned_duration: int,
                               course_id: int = None, topics: list = None,
                               priority_score: float = 0.5, ai_recommendation: str = None) -> int:
    """
    Crea una nuova sessione di studio pianificata per il futuro.
    """
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            from datetime import datetime
            now = datetime.now().isoformat()

            cursor.execute("""
                INSERT INTO study_sessions (
                    user_id, planned_date, planned_duration, course_id,
                    topics_covered, priority_score, ai_recommendation,
                    is_planned, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            """, (
                user_id, planned_date, planned_duration, course_id,
                json.dumps(topics) if topics else None, priority_score,
                ai_recommendation, now, now
            ))

            session_id = cursor.lastrowid
            conn.commit()
            return session_id
    except Exception as e:
        print(f"Errore nella creazione della sessione pianificata: {e}")
        raise

def get_today_planned_sessions(user_id: int) -> list:
    """Recupera le sessioni pianificate per oggi."""
    try:
        from datetime import datetime
        today = datetime.now().date().isoformat()

        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ss.*, c.course_name, c.course_code
                FROM study_sessions ss
                LEFT JOIN courses c ON ss.course_id = c.id
                WHERE ss.user_id = ? AND ss.planned_date = ? AND ss.is_planned = 1
                AND (ss.completed_at IS NULL OR ss.completed_at > ?)
                ORDER BY ss.priority_score DESC, ss.planned_date ASC
            """, (user_id, today, datetime.now().isoformat()))

            sessions = cursor.fetchall()
            result = []
            for session in sessions:
                session_dict = dict(session)
                if session_dict['topics_covered']:
                    session_dict['topics_covered'] = json.loads(session_dict['topics_covered'])
                result.append(session_dict)
            return result
    except Exception as e:
        print(f"Errore nel recupero sessioni pianificate per oggi: {e}")
        return []

def generate_study_schedule(user_id: int, days_ahead: int = 7) -> dict:
    """
    Genera un piano di studio intelligente basato sull'analisi dei dati disponibili.
    """
    try:
        from datetime import datetime, timedelta
        from config import get_chat_llm

        # Analizza dati attuali
        courses = get_user_courses(user_id)
        all_tasks = get_user_tasks(user_id)

        # Filtra task attivi (non completati)
        active_tasks = [t for t in all_tasks if t['status'] in ['pending', 'in_progress']]

        # Recupera lezioni future (nei prossimi giorni)
        future_lectures = []
        for course in courses:
            lectures = get_course_lectures(course['id'])
            for lecture in lectures:
                if lecture['lecture_date']:
                    lecture_date = datetime.fromisoformat(lecture['lecture_date']).date()
                    today = datetime.now().date()
                    days_until = (lecture_date - today).days
                    if 0 <= days_until <= days_ahead:
                        future_lectures.append({
                            'id': lecture['id'],
                            'title': lecture['lecture_title'],
                            'course_name': course['course_name'],
                            'date': lecture['lecture_date'],
                            'days_until': days_until,
                            'course_id': course['id']
                        })

        # Recupera storico prestazioni
        study_sessions = get_user_study_sessions(user_id, limit=20)
        avg_session_length = sum([s['duration_minutes'] or 0 for s in study_sessions]) / len(study_sessions) if study_sessions else 60
        avg_productivity = sum([s['productivity_rating'] or 3 for s in study_sessions]) / len(study_sessions) if study_sessions else 3

        # Genera priorità per ogni giorno
        schedule = {}
        base_date = datetime.now().date()

        for day_offset in range(days_ahead + 1):
            current_date = base_date + timedelta(days=day_offset)

            # Trova lezioni di questo giorno
            day_lectures = [l for l in future_lectures if l['date'].startswith(str(current_date))]
            # Trova task in scadenza entro questa settimana
            urgent_tasks = [
                t for t in active_tasks
                if t.get('due_date') and
                (datetime.fromisoformat(t['due_date']).date() - base_date).days <= 7
            ]

            schedule[str(current_date)] = {
                'lectures': day_lectures,
                'urgent_tasks': urgent_tasks[:3],  # Max 3 per giorno
                'suggested_sessions': []
            }

        # Usa AI per generare suggerimenti intelligenti
        context_prompt = f"""
Sei un assistente di calendarizzazione intelligente per studenti universitari.
Basandoti sui dati forniti, genera suggerimenti di studio personalizzati.

CONTESTO STUDENTE:
- Sessioni medie: {avg_session_length:.0f} minuti
- Produttività media: {avg_productivity:.1f}/5
- Corsi attivi: {len(courses)}
- Task attivi: {len(active_tasks)}
- Lezioni future nei prossimi {days_ahead} giorni: {len(future_lectures)}

CALENDARIO LEZIONI FUTURE:
{future_lectures[:10]}  # Mostra max 10

TASK URGENTI:
{[(t['task_title'], t.get('priority', 'medium'), t.get('due_date')[:10] if t.get('due_date') else None) for t in active_tasks[:15] if t.get('due_date')][:10]}

Genera un JSON con suggerimenti di studio per i prossimi {days_ahead} giorni.
Ogni giorno dovrebbe avere al massimo 2 sessioni da 45-90 minuti.
Priorità: lezioni tomorrow > task in scadenza > ripasso argomenti trattati recentemente > nuovi contenuti.

Formato JSON:
{{
  "schedule": {{
    "2025-10-15": [
      {{
        "topic": "Preparazione esame Algebra Lineare",
        "duration_minutes": 90,
        "priority": 0.9,
        "reasoning": "Esame tra 2 settimane, focati sui concetti fondamentali"
      }}
    ]
  }},
  "weekly_insights": ["Stringhe di insight sulla settimana"]
}}
"""

        try:
            llm = get_chat_llm()
            ai_response = str(llm.complete(context_prompt))

            # Estrai JSON dalla risposta
            start_idx = ai_response.find('{')
            end_idx = ai_response.rfind('}') + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = ai_response[start_idx:end_idx]
                ai_schedule = json.loads(json_str)

                # Integra i suggerimenti AI nel calendario
                if 'schedule' in ai_schedule:
                    for date_str, suggestions in ai_schedule['schedule'].items():
                        if date_str in schedule:
                            schedule[date_str]['ai_suggestions'] = suggestions
                            schedule[date_str]['weekly_insights'] = ai_schedule.get('weekly_insights', [])

        except Exception as e:
            print(f"Errore generazione AI schedule: {e}")
            # Procedi senza suggerimenti AI

        return schedule

    except Exception as e:
        print(f"Errore generazione piano di studio: {e}")
        return {}

def implement_generated_schedule(user_id: int, schedule: dict) -> int:
    """
    Crea effettivamente le sessioni pianificate dal piano generato.
    """
    sessions_created = 0
    try:
        for date_str, day_data in schedule.items():
            if 'ai_suggestions' in day_data:
                for suggestion in day_data['ai_suggestions']:
                    try:
                        session_id = create_planned_study_session(
                            user_id=user_id,
                            planned_date=date_str,
                            planned_duration=suggestion.get('duration_minutes', 60),
                            course_id=None,  # Da determinare meglio
                            topics=[suggestion.get('topic', 'Studio generale')],
                            priority_score=suggestion.get('priority', 0.5),
                            ai_recommendation=suggestion.get('reasoning', '')
                        )
                        sessions_created += 1
                    except Exception as e:
                        print(f"Errore creazione sessione pianificata {date_str}: {e}")

        return sessions_created

    except Exception as e:
        print(f"Errore implementazione piano: {e}")
        return 0

def get_materials_for_lecture(lecture_id: int) -> list:
    """Recupera tutti i materiali associati a una lezione."""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.*, p.title, p.authors, p.category_name
                FROM materials m
                LEFT JOIN papers p ON m.file_name = p.file_name
                WHERE m.lecture_id = ?
                ORDER BY m.processed_at DESC
            """, (lecture_id,))

            materials = cursor.fetchall()
            return [dict(material) for material in materials]
    except Exception as e:
        print(f"Errore nel recupero materiali per lezione {lecture_id}: {e}")
        return []

def get_study_insights(user_id: int) -> dict:
    """
    Fornisce insight sul pattern di studio dello studente.
    """
    try:
        from datetime import datetime
        sessions = get_user_study_sessions(user_id, limit=50)

        if not sessions:
            return {"insight": "Inizia a registrare le tue sessioni di studio per ricevere insight personalizzati!"}

        # Calcola statistiche base
        total_sessions = len(sessions)
        completed_sessions = len([s for s in sessions if s.get('session_end')])
        avg_duration = sum([s.get('duration_minutes', 0) for s in sessions if s.get('session_end')]) / completed_sessions if completed_sessions > 0 else 0
        avg_productivity = sum([s.get('productivity_rating', 3) for s in sessions if s.get('session_end')]) / completed_sessions if completed_sessions > 0 else 3

        # Pattern giornaliero
        weekday_counts = {}
        for session in sessions:
            if session.get('session_start'):
                start_datetime = datetime.fromisoformat(session['session_start'])
                weekday = start_datetime.strftime('%A')
                weekday_counts[weekday] = weekday_counts.get(weekday, 0) + 1

        most_productive_day = max(weekday_counts.items(), key=lambda x: x[1])[0] if weekday_counts else "N/A"

        # Performance trend
        recent_sessions = sessions[:10]  # Ultime 10
        recent_avg_prod = sum([s.get('productivity_rating', 3) for s in recent_sessions]) / len(recent_sessions)

        trend = "costante"
        if recent_avg_prod > avg_productivity + 0.3:
            trend = "migliorativo 📈"
        elif recent_avg_prod < avg_productivity - 0.3:
            trend = "peggiorativo 📉"

        return {
            "total_sessions": total_sessions,
            "completed_sessions": completed_sessions,
            "avg_duration_minutes": round(avg_duration, 1),
            "avg_productivity": round(avg_productivity, 1),
            "most_productive_day": most_productive_day,
            "productivity_trend": trend,
            "insight": f"Le tue sessioni sono in media di {avg_duration:.0f} minuti con produttività {avg_productivity:.1f}/5. "
                      f"Giorno più produttivo: {most_productive_day}. Trend recente: {trend}"
        }

    except Exception as e:
        print(f"Errore generazione insight: {e}")
        return {"insight": "Impossibile generare insight al momento"}

# --- FUNZIONI PER TRACCIAMENTO ATTIVITÀ UTENTE (DASHBOARD INTELLIGENTE) ---

def record_user_activity(user_id: int, action_type: str, target_type: str = None, target_id: str = None, metadata: dict = None):
    """
    Registra un'attività dell'utente per l'analisi comportamentale e la dashboard.

    Args:
        user_id: ID dell'utente
        action_type: Tipo di azione ('view_doc', 'edit_doc', 'create_doc', 'start_chat', etc.)
        target_type: Tipo di target ('document', 'chat', 'task', 'course', etc.)
        target_id: ID specifico del target
        metadata: Informazioni aggiuntive in formato JSON
    """
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            from datetime import datetime
            now = datetime.now().isoformat()
            session_id = st.session_state.get('current_session_id', 'unknown')

            cursor.execute("""
                INSERT INTO user_activity (user_id, action_type, target_type, target_id, metadata, timestamp, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, action_type, target_type, target_id,
                json.dumps(metadata) if metadata else None,
                now, session_id
            ))
            conn.commit()
    except Exception as e:
        print(f"Errore nel tracciamento attività: {e}")
        # Non bloccare l'app se il tracciamento fallisce

def get_recent_documents(user_id: int, limit: int = 5) -> list:
    """
    Recupera gli ultimi documenti visualizzati o modificati dall'utente.

    Returns:
        list: Lista di documenti con metadati di accesso
    """
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT p.*, ua.timestamp as last_accessed, ua.action_type as last_action
                FROM papers p
                JOIN user_activity ua ON (
                    (ua.target_type = 'document' AND ua.target_id = p.file_name) OR
                    (ua.action_type IN ('view_doc', 'edit_doc') AND ua.metadata LIKE '%' || p.file_name || '%')
                )
                WHERE ua.user_id = ?
                ORDER BY ua.timestamp DESC
                LIMIT ?
            """, (user_id, limit))

            documents = cursor.fetchall()
            result = []
            for doc in documents:
                doc_dict = dict(doc)
                if doc_dict.get('metadata'):
                    try:
                        doc_dict['metadata'] = json.loads(doc_dict['metadata'])
                    except:
                        doc_dict['metadata'] = {}
                result.append(doc_dict)
            return result
    except Exception as e:
        print(f"Errore nel recupero documenti recenti: {e}")
        return []

def get_recent_uploads(user_id: int, limit: int = 5) -> list:
    """
    Recupera gli ultimi file caricati dall'utente.

    Returns:
        list: Lista di upload recenti con metadati
    """
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.*, ua.timestamp as upload_date, ua.metadata as upload_metadata
                FROM papers p
                JOIN user_activity ua ON ua.target_id = p.file_name
                WHERE ua.user_id = ? AND ua.action_type = 'create_doc'
                ORDER BY ua.timestamp DESC
                LIMIT ?
            """, (user_id, limit))

            uploads = cursor.fetchall()
            result = []
            for upload in uploads:
                upload_dict = dict(upload)
                if upload_dict.get('upload_metadata'):
                    try:
                        upload_dict['upload_metadata'] = json.loads(upload_dict['upload_metadata'])
                    except:
                        upload_dict['upload_metadata'] = {}
                result.append(upload_dict)
            return result
    except Exception as e:
        print(f"Errore nel recupero upload recenti: {e}")
        return []

def get_user_activity_summary(user_id: int, days: int = 7) -> dict:
    """
    Fornisce un riassunto delle attività dell'utente negli ultimi giorni.

    Returns:
        dict: Statistiche di attività con breakdown per tipo
    """
    try:
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=days)

        with db_connect() as conn:
            cursor = conn.cursor()

            # Statistiche generali
            cursor.execute("""
                SELECT COUNT(*) as total_actions,
                       COUNT(DISTINCT DATE(timestamp)) as active_days,
                       COUNT(DISTINCT target_type) as different_targets
                FROM user_activity
                WHERE user_id = ? AND timestamp > ?
            """, (user_id, cutoff_date.isoformat()))

            general_stats = dict(cursor.fetchone())

            # Breakdown per tipo di azione
            cursor.execute("""
                SELECT action_type, COUNT(*) as count
                FROM user_activity
                WHERE user_id = ? AND timestamp > ?
                GROUP BY action_type
                ORDER BY count DESC
            """, (user_id, cutoff_date.isoformat()))

            action_breakdown = [dict(row) for row in cursor.fetchall()]

            # Documenti più accessati
            cursor.execute("""
                SELECT p.title, p.file_name, COUNT(*) as access_count,
                       MAX(ua.timestamp) as last_accessed
                FROM papers p
                JOIN user_activity ua ON (
                    ua.target_type = 'document' AND ua.target_id = p.file_name
                )
                WHERE ua.user_id = ? AND ua.timestamp > ?
                GROUP BY p.file_name
                ORDER BY access_count DESC
                LIMIT 5
            """, (user_id, cutoff_date.isoformat()))

            top_documents = [dict(row) for row in cursor.fetchall()]

            return {
                'general_stats': general_stats,
                'action_breakdown': action_breakdown,
                'top_documents': top_documents,
                'period_days': days
            }
    except Exception as e:
        print(f"Errore nel recupero riassunto attività: {e}")
        return {'general_stats': {}, 'action_breakdown': [], 'top_documents': []}

def get_most_accessed_documents(user_id: int, limit: int = 10) -> list:
    """
    Recupera i documenti più accessati dall'utente.

    Returns:
        list: Documenti ordinati per numero di accessi
    """
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.*, COUNT(ua.id) as access_count, MAX(ua.timestamp) as last_accessed
                FROM papers p
                JOIN user_activity ua ON (
                    ua.target_type = 'document' AND ua.target_id = p.file_name
                )
                WHERE ua.user_id = ?
                GROUP BY p.file_name
                ORDER BY access_count DESC, last_accessed DESC
                LIMIT ?
            """, (user_id, limit))

            documents = cursor.fetchall()
            result = []
            for doc in documents:
                doc_dict = dict(doc)
                doc_dict['last_accessed'] = doc_dict['last_accessed'][:10] if doc_dict['last_accessed'] else 'N/A'
                result.append(doc_dict)
            return result
    except Exception as e:
        print(f"Errore nel recupero documenti più accessati: {e}")
        return []

def check_first_time_user(user_id: int) -> bool:
    """
    Verifica se l'utente è al primo accesso.

    Returns:
        bool: True se è un nuovo utente
    """
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT is_new_user FROM users WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            return result and result['is_new_user'] == 1 if result else True
    except Exception as e:
        print(f"Errore nel controllo utente nuovo: {e}")
        return True

def mark_user_not_new(user_id: int):
    """
    Marca l'utente come non più nuovo (dopo la prima azione significativa).
    """
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET is_new_user = 0 WHERE id = ?", (user_id,))
            conn.commit()
    except Exception as e:
        print(f"Errore nell'aggiornamento stato utente: {e}")

# --- FUNZIONI CACHE PER DASHBOARD ---

@st.cache_data(ttl=30)  # Cache per 30 secondi
def get_dashboard_data(user_id: int) -> dict:
    """
    Recupera tutti i dati necessari per la dashboard in una sola chiamata.

    Returns:
        dict: Dati aggregati per la dashboard
    """
    try:
        return {
            'recent_documents': get_recent_documents(user_id, limit=5),
            'recent_uploads': get_recent_uploads(user_id, limit=5),
            'activity_summary': get_user_activity_summary(user_id, days=7),
            'most_accessed': get_most_accessed_documents(user_id, limit=10),
            'is_new_user': check_first_time_user(user_id)
        }
    except Exception as e:
        print(f"Errore nel recupero dati dashboard: {e}")
        return {
            'recent_documents': [],
            'recent_uploads': [],
            'activity_summary': {},
            'most_accessed': [],
            'is_new_user': True
        }

# --- FUNZIONI BAYESIANE PER LA GESTIONE DELLA CONOSCENZA DINAMICA ---

def create_bayesian_entity(entity_data: BayesianKnowledgeEntity) -> int:
    """
    Crea una nuova entità concettuale con punteggio di confidenza Bayesiano.

    Args:
        entity_data: Oggetto BayesianKnowledgeEntity con i dati dell'entità

    Returns:
        int: ID dell'entità creata
    """
    try:
        with db_connect() as conn:
            cursor = conn.cursor()

            # Usa il punteggio di default se non specificato
            confidence_score = entity_data.confidence_score
            if confidence_score is None:
                confidence_score = get_default_confidence_score()

            cursor.execute("""
                INSERT INTO concept_entities (
                    user_id, entity_type, entity_name, entity_description,
                    source_file_name, confidence_score, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                entity_data.user_id,
                entity_data.entity_type,
                entity_data.entity_name,
                entity_data.entity_description,
                entity_data.source_file_name,
                confidence_score,
                entity_data.created_at.isoformat()
            ))

            entity_id = cursor.lastrowid
            conn.commit()

            # Registra l'evento come prova iniziale
            record_evidence(
                entity_id=entity_id,
                evidence_type='document_extraction',
                evidence_source=entity_data.source_file_name,
                evidence_strength=get_evidence_strength('document_extraction'),
                evidence_description=f"Entità '{entity_data.entity_name}' estratta automaticamente dal documento"
            )

            return entity_id

    except Exception as e:
        print(f"Errore nella creazione dell'entità Bayesiana: {e}")
        raise

def create_bayesian_relationship(relationship_data: BayesianKnowledgeRelationship) -> int:
    """
    Crea una nuova relazione concettuale con punteggio di confidenza Bayesiano.

    Args:
        relationship_data: Oggetto BayesianKnowledgeRelationship con i dati della relazione

    Returns:
        int: ID della relazione creata
    """
    try:
        with db_connect() as conn:
            cursor = conn.cursor()

            # Verifica che entrambe le entità esistano
            cursor.execute("""
                SELECT id FROM concept_entities
                WHERE user_id = ? AND entity_name = ?
            """, (relationship_data.user_id, relationship_data.source_entity_id))

            source_result = cursor.fetchone()
            if not source_result:
                raise ValueError(f"Entità sorgente non trovata: {relationship_data.source_entity_id}")

            cursor.execute("""
                SELECT id FROM concept_entities
                WHERE user_id = ? AND entity_name = ?
            """, (relationship_data.user_id, relationship_data.target_entity_id))

            target_result = cursor.fetchone()
            if not target_result:
                raise ValueError(f"Entità destinazione non trovata: {relationship_data.target_entity_id}")

            source_entity_id = source_result['id']
            target_entity_id = target_result['id']

            # Usa il punteggio di default se non specificato
            confidence_score = relationship_data.confidence_score
            if confidence_score is None:
                confidence_score = get_default_confidence_score()

            cursor.execute("""
                INSERT INTO concept_relationships (
                    user_id, source_entity_id, target_entity_id, relationship_type,
                    relationship_description, confidence_score, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                relationship_data.user_id,
                source_entity_id,
                target_entity_id,
                relationship_data.relationship_type,
                relationship_data.relationship_description,
                confidence_score,
                relationship_data.created_at.isoformat()
            ))

            relationship_id = cursor.lastrowid
            conn.commit()

            # Registra l'evento come prova iniziale
            record_evidence(
                relationship_id=relationship_id,
                evidence_type='document_extraction',
                evidence_source=f"{relationship_data.source_entity_id}-{relationship_data.target_entity_id}",
                evidence_strength=get_evidence_strength('document_extraction'),
                evidence_description=f"Relazione '{relationship_data.relationship_type}' estratta automaticamente"
            )

            return relationship_id

    except Exception as e:
        print(f"Errore nella creazione della relazione Bayesiana: {e}")
        raise

def update_entity_confidence(entity_id: int, evidence_type: str, evidence_strength: float, evidence_description: str) -> float:
    """
    Aggiorna il punteggio di confidenza di un'entità usando inferenza Bayesiana.

    Args:
        entity_id: ID dell'entità da aggiornare
        evidence_type: Tipo di prova ('document_extraction', 'user_feedback_positive', etc.)
        evidence_strength: Forza della prova (-1.0 to 1.0)
        evidence_description: Descrizione della prova

    Returns:
        float: Nuovo punteggio di confidenza
    """
    try:
        with db_connect() as conn:
            cursor = conn.cursor()

            # Recupera il punteggio attuale
            cursor.execute("SELECT confidence_score FROM concept_entities WHERE id = ?", (entity_id,))
            result = cursor.fetchone()

            if not result:
                raise ValueError(f"Entità con ID {entity_id} non trovata")

            current_confidence = result['confidence_score']

            # Calcola il nuovo punteggio
            new_confidence = calculate_confidence_update(current_confidence, evidence_strength)

            # Aggiorna l'entità
            cursor.execute("""
                UPDATE concept_entities
                SET confidence_score = ?, updated_at = ?
                WHERE id = ?
            """, (new_confidence, datetime.now().isoformat(), entity_id))

            # Registra la prova
            record_evidence(
                entity_id=entity_id,
                evidence_type=evidence_type,
                evidence_source="system_update",
                evidence_strength=evidence_strength,
                evidence_description=evidence_description,
                previous_confidence=current_confidence,
                new_confidence=new_confidence
            )

            conn.commit()
            return new_confidence

    except Exception as e:
        print(f"Errore nell'aggiornamento confidenza entità: {e}")
        raise

def update_relationship_confidence(relationship_id: int, evidence_type: str, evidence_strength: float, evidence_description: str) -> float:
    """
    Aggiorna il punteggio di confidenza di una relazione usando inferenza Bayesiana.

    Args:
        relationship_id: ID della relazione da aggiornare
        evidence_type: Tipo di prova
        evidence_strength: Forza della prova (-1.0 to 1.0)
        evidence_description: Descrizione della prova

    Returns:
        float: Nuovo punteggio di confidenza
    """
    try:
        with db_connect() as conn:
            cursor = conn.cursor()

            # Recupera il punteggio attuale
            cursor.execute("SELECT confidence_score FROM concept_relationships WHERE id = ?", (relationship_id,))
            result = cursor.fetchone()

            if not result:
                raise ValueError(f"Relazione con ID {relationship_id} non trovata")

            current_confidence = result['confidence_score']

            # Calcola il nuovo punteggio
            new_confidence = calculate_confidence_update(current_confidence, evidence_strength)

            # Aggiorna la relazione
            cursor.execute("""
                UPDATE concept_relationships
                SET confidence_score = ?, updated_at = ?
                WHERE id = ?
            """, (new_confidence, datetime.now().isoformat(), relationship_id))

            # Registra la prova
            record_evidence(
                relationship_id=relationship_id,
                evidence_type=evidence_type,
                evidence_source="system_update",
                evidence_strength=evidence_strength,
                evidence_description=evidence_description,
                previous_confidence=current_confidence,
                new_confidence=new_confidence
            )

            conn.commit()
            return new_confidence

    except Exception as e:
        print(f"Errore nell'aggiornamento confidenza relazione: {e}")
        raise

def record_evidence(entity_id: int = None, relationship_id: int = None,
                   evidence_type: str = None, evidence_source: str = None,
                   evidence_strength: float = None, evidence_description: str = None,
                   previous_confidence: float = None, new_confidence: float = None):
    """
    Registra una prova che ha contribuito all'aggiornamento Bayesiano.

    Args:
        entity_id: ID dell'entità coinvolta (opzionale)
        relationship_id: ID della relazione coinvolta (opzionale)
        evidence_type: Tipo di prova
        evidence_source: Fonte della prova
        evidence_strength: Forza della prova
        evidence_description: Descrizione della prova
        previous_confidence: Punteggio precedente
        new_confidence: Nuovo punteggio
    """
    try:
        # Crea tabella evidence se non esiste
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bayesian_evidence (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_id INTEGER,
                    relationship_id INTEGER,
                    evidence_type TEXT NOT NULL,
                    evidence_source TEXT NOT NULL,
                    evidence_strength REAL NOT NULL,
                    evidence_description TEXT NOT NULL,
                    previous_confidence REAL,
                    new_confidence REAL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (entity_id) REFERENCES concept_entities (id) ON DELETE CASCADE,
                    FOREIGN KEY (relationship_id) REFERENCES concept_relationships (id) ON DELETE CASCADE
                )
            """)

            cursor.execute("""
                INSERT INTO bayesian_evidence (
                    entity_id, relationship_id, evidence_type, evidence_source,
                    evidence_strength, evidence_description, previous_confidence,
                    new_confidence, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entity_id,
                relationship_id,
                evidence_type,
                evidence_source,
                evidence_strength,
                evidence_description,
                previous_confidence,
                new_confidence,
                datetime.now().isoformat()
            ))

            conn.commit()

    except Exception as e:
        print(f"Errore nella registrazione della prova: {e}")
        # Non bloccare l'app se la registrazione delle prove fallisce

def get_entity_evidence_history(entity_id: int, limit: int = 10) -> list:
    """
    Recupera la cronologia delle prove per un'entità.

    Args:
        entity_id: ID dell'entità
        limit: Numero massimo di record da restituire

    Returns:
        list: Lista delle prove ordinate per data
    """
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM bayesian_evidence
                WHERE entity_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (entity_id, limit))

            evidence = cursor.fetchall()
            return [dict(e) for e in evidence]

    except Exception as e:
        print(f"Errore nel recupero cronologia prove entità: {e}")
        return []

def get_relationship_evidence_history(relationship_id: int, limit: int = 10) -> list:
    """
    Recupera la cronologia delle prove per una relazione.

    Args:
        relationship_id: ID della relazione
        limit: Numero massimo di record da restituire

    Returns:
        list: Lista delle prove ordinate per data
    """
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM bayesian_evidence
                WHERE relationship_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (relationship_id, limit))

            evidence = cursor.fetchall()
            return [dict(e) for e in evidence]

    except Exception as e:
        print(f"Errore nel recupero cronologia prove relazione: {e}")
        return []

def find_or_create_entity(user_id: int, entity_name: str, entity_type: str, source_file_name: str) -> int:
    """
    Trova un'entità esistente o ne crea una nuova se non esiste.

    Args:
        user_id: ID dell'utente
        entity_name: Nome dell'entità
        entity_type: Tipo di entità
        source_file_name: Documento sorgente

    Returns:
        int: ID dell'entità (esistente o appena creata)
    """
    try:
        with db_connect() as conn:
            cursor = conn.cursor()

            # Cerca entità esistente
            cursor.execute("""
                SELECT id FROM concept_entities
                WHERE user_id = ? AND entity_name = ? AND entity_type = ?
            """, (user_id, entity_name, entity_type))

            result = cursor.fetchone()

            if result:
                return result['id']
            else:
                # Crea nuova entità
                entity_data = BayesianKnowledgeEntity(
                    user_id=user_id,
                    entity_type=entity_type,
                    entity_name=entity_name,
                    source_file_name=source_file_name,
                    confidence_score=get_default_confidence_score()
                )
                return create_bayesian_entity(entity_data)

    except Exception as e:
        print(f"Errore in find_or_create_entity: {e}")
        raise

def find_or_create_relationship(user_id: int, source_entity_name: str, target_entity_name: str,
                              relationship_type: str) -> int:
    """
    Trova una relazione esistente o ne crea una nuova se non esiste.

    Args:
        user_id: ID dell'utente
        source_entity_name: Nome dell'entità sorgente
        target_entity_name: Nome dell'entità destinazione
        relationship_type: Tipo di relazione

    Returns:
        int: ID della relazione (esistente o appena creata)
    """
    try:
        with db_connect() as conn:
            cursor = conn.cursor()

            # Trova gli ID delle entità
            cursor.execute("""
                SELECT id FROM concept_entities
                WHERE user_id = ? AND entity_name = ?
            """, (user_id, source_entity_name))

            source_result = cursor.fetchone()
            if not source_result:
                raise ValueError(f"Entità sorgente non trovata: {source_entity_name}")

            cursor.execute("""
                SELECT id FROM concept_entities
                WHERE user_id = ? AND entity_name = ?
            """, (user_id, target_entity_name))

            target_result = cursor.fetchone()
            if not target_result:
                raise ValueError(f"Entità destinazione non trovata: {target_entity_name}")

            source_entity_id = source_result['id']
            target_entity_id = target_result['id']

            # Cerca relazione esistente
            cursor.execute("""
                SELECT id FROM concept_relationships
                WHERE user_id = ? AND source_entity_id = ? AND target_entity_id = ?
                AND relationship_type = ?
            """, (user_id, source_entity_id, target_entity_id, relationship_type))

            result = cursor.fetchone()

            if result:
                return result['id']
            else:
                # Crea nuova relazione
                relationship_data = BayesianKnowledgeRelationship(
                    user_id=user_id,
                    source_entity_id=source_entity_id,
                    target_entity_id=target_entity_id,
                    relationship_type=relationship_type,
                    confidence_score=get_default_confidence_score()
                )
                return create_bayesian_relationship(relationship_data)

    except Exception as e:
        print(f"Errore in find_or_create_relationship: {e}")
        raise

def get_entities_by_confidence(user_id: int, min_confidence: float = 0.0, max_confidence: float = 1.0) -> list:
    """
    Recupera entità filtrate per punteggio di confidenza.

    Args:
        user_id: ID dell'utente
        min_confidence: Confidenza minima (0.0-1.0)
        max_confidence: Confidenza massima (0.0-1.0)

    Returns:
        list: Lista di entità filtrate
    """
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM concept_entities
                WHERE user_id = ? AND confidence_score BETWEEN ? AND ?
                ORDER BY confidence_score DESC, created_at DESC
            """, (user_id, min_confidence, max_confidence))

            entities = cursor.fetchall()
            return [dict(entity) for entity in entities]

    except Exception as e:
        print(f"Errore nel recupero entità per confidenza: {e}")
        return []

def get_relationships_by_confidence(user_id: int, min_confidence: float = 0.0, max_confidence: float = 1.0) -> list:
    """
    Recupera relazioni filtrate per punteggio di confidenza.

    Args:
        user_id: ID dell'utente
        min_confidence: Confidenza minima (0.0-1.0)
        max_confidence: Confidenza massima (0.0-1.0)

    Returns:
        list: Lista di relazioni filtrate con nomi delle entità
    """
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT r.*, e1.entity_name as source_name, e1.entity_type as source_type,
                       e2.entity_name as target_name, e2.entity_type as target_type
                FROM concept_relationships r
                JOIN concept_entities e1 ON r.source_entity_id = e1.id
                JOIN concept_entities e2 ON r.target_entity_id = e2.id
                WHERE r.user_id = ? AND r.confidence_score BETWEEN ? AND ?
                ORDER BY r.confidence_score DESC, r.created_at DESC
            """, (user_id, min_confidence, max_confidence))

            relationships = cursor.fetchall()
            return [dict(rel) for rel in relationships]

    except Exception as e:
        print(f"Errore nel recupero relazioni per confidenza: {e}")
        return []

def apply_temporal_decay(user_id: int, decay_factor: float = -0.05) -> dict:
    """
    Applica decadimento temporale ai punteggi di confidenza delle entità e relazioni.

    Args:
        user_id: ID dell'utente
        decay_factor: Fattore di decadimento (negativo per riduzione)

    Returns:
        dict: Statistiche dell'operazione di decadimento
    """
    try:
        with db_connect() as conn:
            cursor = conn.cursor()

            # Applica decadimento alle entità
            cursor.execute("""
                UPDATE concept_entities
                SET confidence_score = MAX(0.1, confidence_score + ?), updated_at = ?
                WHERE user_id = ?
            """, (decay_factor, datetime.now().isoformat(), user_id))

            entities_updated = cursor.rowcount

            # Applica decadimento alle relazioni
            cursor.execute("""
                UPDATE concept_relationships
                SET confidence_score = MAX(0.1, confidence_score + ?), updated_at = ?
                WHERE user_id = ?
            """, (decay_factor, datetime.now().isoformat(), user_id))

            relationships_updated = cursor.rowcount

            # Registra l'operazione come prova di decadimento
            record_evidence(
                evidence_type='temporal_decay',
                evidence_source='system_scheduler',
                evidence_strength=decay_factor,
                evidence_description=f"Decadimento temporale applicato: {abs(decay_factor):.3f}"
            )

            conn.commit()

            return {
                'entities_updated': entities_updated,
                'relationships_updated': relationships_updated,
                'decay_factor': decay_factor
            }

    except Exception as e:
        print(f"Errore nell'applicazione decadimento temporale: {e}")
        return {'entities_updated': 0, 'relationships_updated': 0, 'decay_factor': decay_factor}

def get_knowledge_graph_with_confidence(user_id: int, min_confidence: float = 0.0) -> dict:
    """
    Recupera il grafo della conoscenza completo con filtri di confidenza.

    Args:
        user_id: ID dell'utente
        min_confidence: Confidenza minima per includere entità/relazioni

    Returns:
        dict: Grafo della conoscenza filtrato
    """
    try:
        entities = get_entities_by_confidence(user_id, min_confidence)
        relationships = get_relationships_by_confidence(user_id, min_confidence)

        return {
            'entities': entities,
            'relationships': relationships,
            'confidence_threshold': min_confidence,
            'total_entities': len(entities),
            'total_relationships': len(relationships)
        }

    except Exception as e:
        print(f"Errore nel recupero grafo con confidenza: {e}")
        return {
            'entities': [],
            'relationships': [],
            'confidence_threshold': min_confidence,
            'total_entities': 0,
            'total_relationships': 0
        }

def corroborate_entities_across_documents(user_id: int, entity_name: str, corroboration_threshold: float = 0.7) -> dict:
    """
    Trova e rafforza entità che appaiono in documenti multipli (corroborazione).

    Args:
        user_id: ID dell'utente
        entity_name: Nome dell'entità da cercare
        corroboration_threshold: Soglia di confidenza per applicare corroborazione

    Returns:
        dict: Risultati della corroborazione
    """
    try:
        with db_connect() as conn:
            cursor = conn.cursor()

            # Trova tutte le occorrenze dell'entità
            cursor.execute("""
                SELECT id, source_file_name, confidence_score
                FROM concept_entities
                WHERE user_id = ? AND entity_name = ?
            """, (user_id, entity_name))

            occurrences = cursor.fetchall()

            if len(occurrences) < 2:
                return {'corroborated': False, 'reason': 'Entità trovata in meno di 2 documenti'}

            # Calcola forza di corroborazione basata sul numero di documenti
            document_count = len(occurrences)
            corroboration_strength = min(0.3 + (document_count - 1) * 0.1, 0.8)

            # Applica rafforzamento solo se supera la soglia
            if corroboration_strength >= corroboration_threshold:
                # Aggiorna tutte le occorrenze
                entity_ids = [occ['id'] for occ in occurrences]

                for entity_id in entity_ids:
                    update_entity_confidence(
                        entity_id=entity_id,
                        evidence_type='corroboration',
                        evidence_strength=corroboration_strength,
                        evidence_description=f"Corroborazione da {document_count} documenti"
                    )

                return {
                    'corroborated': True,
                    'entity_name': entity_name,
                    'document_count': document_count,
                    'corroboration_strength': corroboration_strength,
                    'entities_updated': len(entity_ids)
                }
            else:
                return {
                    'corroborated': False,
                    'entity_name': entity_name,
                    'document_count': document_count,
                    'reason': f'Forza corroborazione {corroboration_strength:.2f} sotto la soglia {corroboration_threshold}'
                }

    except Exception as e:
        print(f"Errore nella corroborazione entità: {e}")
        return {'corroborated': False, 'error': str(e)}

def get_confidence_statistics(user_id: int) -> dict:
    """
    Calcola statistiche sui punteggi di confidenza del grafo della conoscenza.

    Args:
        user_id: ID dell'utente

    Returns:
        dict: Statistiche di confidenza
    """
    try:
        with db_connect() as conn:
            cursor = conn.cursor()

            # Statistiche entità
            cursor.execute("""
                SELECT
                    COUNT(*) as total_entities,
                    AVG(confidence_score) as avg_confidence,
                    MIN(confidence_score) as min_confidence,
                    MAX(confidence_score) as max_confidence,
                    COUNT(CASE WHEN confidence_score >= 0.8 THEN 1 END) as high_confidence,
                    COUNT(CASE WHEN confidence_score >= 0.6 AND confidence_score < 0.8 THEN 1 END) as medium_confidence,
                    COUNT(CASE WHEN confidence_score < 0.6 THEN 1 END) as low_confidence
                FROM concept_entities
                WHERE user_id = ?
            """, (user_id,))

            entity_stats = dict(cursor.fetchone())

            # Statistiche relazioni
            cursor.execute("""
                SELECT
                    COUNT(*) as total_relationships,
                    AVG(confidence_score) as avg_confidence,
                    MIN(confidence_score) as min_confidence,
                    MAX(confidence_score) as max_confidence,
                    COUNT(CASE WHEN confidence_score >= 0.8 THEN 1 END) as high_confidence,
                    COUNT(CASE WHEN confidence_score >= 0.6 AND confidence_score < 0.8 THEN 1 END) as medium_confidence,
                    COUNT(CASE WHEN confidence_score < 0.6 THEN 1 END) as low_confidence
                FROM concept_relationships
                WHERE user_id = ?
            """, (user_id,))

            relationship_stats = dict(cursor.fetchone())

            return {
                'entities': entity_stats,
                'relationships': relationship_stats,
                'summary': {
                    'total_knowledge_items': entity_stats['total_entities'] + relationship_stats['total_relationships'],
                    'avg_confidence': (entity_stats['avg_confidence'] + relationship_stats['avg_confidence']) / 2,
                    'high_confidence_ratio': (entity_stats['high_confidence'] + relationship_stats['high_confidence']) /
                                           max(1, entity_stats['total_entities'] + relationship_stats['total_relationships'])
                }
            }

    except Exception as e:
        print(f"Errore nel calcolo statistiche confidenza: {e}")
        return {
            'entities': {'total_entities': 0},
            'relationships': {'total_relationships': 0},
            'summary': {'total_knowledge_items': 0, 'avg_confidence': 0.0, 'high_confidence_ratio': 0.0}
        }
