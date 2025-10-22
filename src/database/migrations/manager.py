"""
Database migration manager.
Handles schema migrations and data transformations safely.
"""

import sqlite3
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from contextlib import contextmanager

# Models are imported dynamically to avoid circular imports


@dataclass
class MigrationStep:
    """Rappresenta un singolo step di migrazione."""
    version: str
    description: str
    up_sql: str
    down_sql: Optional[str] = None
    pre_migration: Optional[Callable] = None
    post_migration: Optional[Callable] = None


@dataclass
class MigrationResult:
    """Risultato operazione migrazione."""
    success: bool
    version: str
    execution_time_ms: int
    error_message: Optional[str] = None
    rows_affected: int = 0


class MigrationManager:
    """Gestore migrazioni database."""

    def __init__(self, db_path: str):
        """Inizializza migration manager.

        Args:
            db_path: Percorso database SQLite
        """
        self.db_path = db_path
        self.migrations_table = "schema_migrations"
        self.logger = logging.getLogger(__name__)

        # Crea directory migrazioni se non esiste
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    def initialize_database(self) -> bool:
        """Inizializza database con schema base e tabella migrazioni."""
        try:
            with self._get_connection() as conn:
                # Crea tabella migrazioni
                conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.migrations_table} (
                        version TEXT PRIMARY KEY,
                        description TEXT NOT NULL,
                        applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        execution_time_ms INTEGER,
                        success BOOLEAN DEFAULT 1,
                        error_message TEXT
                    )
                """)

                # Crea tabella progetti (nuova architettura)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS projects (
                        id TEXT PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        description TEXT,
                        owner_id INTEGER,
                        is_default BOOLEAN DEFAULT 0,
                        settings JSON,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                conn.commit()
                self.logger.info("Database inizializzato con successo")
                return True

        except Exception as e:
            self.logger.error(f"Errore inizializzazione database: {e}")
            return False

    def get_applied_migrations(self) -> List[str]:
        """Recupera lista migrazioni applicate."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    f"SELECT version FROM {self.migrations_table} WHERE success = 1 ORDER BY version"
                )
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.OperationalError as e:
            if "no such table" in str(e):
                # Table doesn't exist yet, return empty list
                return []
            self.logger.error(f"Errore recupero migrazioni applicate: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Errore recupero migrazioni applicate: {e}")
            return []

    def get_pending_migrations(self, available_migrations: List[str]) -> List[str]:
        """Recupera migrazioni pending."""
        applied = set(self.get_applied_migrations())
        return [m for m in available_migrations if m not in applied]

    def apply_migration(self, migration: MigrationStep) -> MigrationResult:
        """Applica singola migrazione."""
        start_time = datetime.utcnow()

        try:
            # Pre-migration hook
            if migration.pre_migration:
                migration.pre_migration()

            with self._get_connection() as conn:
                # Crea tabella migrazioni se non esiste
                conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.migrations_table} (
                        version TEXT PRIMARY KEY,
                        description TEXT NOT NULL,
                        applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        execution_time_ms INTEGER,
                        success BOOLEAN DEFAULT 1,
                        error_message TEXT
                    )
                """)

                # Esegui SQL migrazione
                cursor = conn.execute(migration.up_sql)

                # Registra migrazione
                conn.execute(f"""
                    INSERT OR REPLACE INTO {self.migrations_table}
                    (version, description, execution_time_ms, success)
                    VALUES (?, ?, ?, 1)
                """, (
                    migration.version,
                    migration.description,
                    0  # Calcoleremo dopo
                ))

                rows_affected = cursor.rowcount
                conn.commit()

            # Post-migration hook
            if migration.post_migration:
                migration.post_migration()

            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            # Aggiorna tempo esecuzione
            with self._get_connection() as conn:
                conn.execute(f"""
                    UPDATE {self.migrations_table}
                    SET execution_time_ms = ? WHERE version = ?
                """, (execution_time, migration.version))
                conn.commit()

            self.logger.info(f"Migrazione {migration.version} applicata con successo")
            return MigrationResult(
                success=True,
                version=migration.version,
                execution_time_ms=execution_time,
                rows_affected=rows_affected
            )

        except Exception as e:
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            error_message = str(e)

            # Registra fallimento
            try:
                with self._get_connection() as conn:
                    # Crea tabella migrazioni se non esiste
                    conn.execute(f"""
                        CREATE TABLE IF NOT EXISTS {self.migrations_table} (
                            version TEXT PRIMARY KEY,
                            description TEXT NOT NULL,
                            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            execution_time_ms INTEGER,
                            success BOOLEAN DEFAULT 1,
                            error_message TEXT
                        )
                    """)

                    conn.execute(f"""
                        INSERT OR REPLACE INTO {self.migrations_table}
                        (version, description, execution_time_ms, success, error_message)
                        VALUES (?, ?, ?, 0, ?)
                    """, (migration.version, migration.description, execution_time, error_message))
                    conn.commit()
            except Exception as log_error:
                self.logger.error(f"Errore registrazione fallimento migrazione: {log_error}")

            self.logger.error(f"Errore applicazione migrazione {migration.version}: {e}")
            return MigrationResult(
                success=False,
                version=migration.version,
                execution_time_ms=execution_time,
                error_message=error_message
            )

    def rollback_migration(self, version: str) -> bool:
        """Esegue rollback migrazione."""
        try:
            # Trova migrazione
            migration = self._get_migration_by_version(version)
            if not migration or not migration.down_sql:
                self.logger.error(f"Migrazione {version} non trovata o senza rollback")
                return False

            with self._get_connection() as conn:
                # Esegui rollback SQL
                conn.execute(migration.down_sql)

                # Rimuovi record migrazione
                conn.execute(
                    f"DELETE FROM {self.migrations_table} WHERE version = ?",
                    (version,)
                )

                conn.commit()

            self.logger.info(f"Rollback migrazione {version} completato")
            return True

        except Exception as e:
            self.logger.error(f"Errore rollback migrazione {version}: {e}")
            return False

    def migrate_to_version(self, target_version: str) -> bool:
        """Migra database a versione specifica."""
        # Questa è una implementazione semplificata
        # In produzione, dovresti gestire dipendenze tra migrazioni
        migrations = self._get_available_migrations()
        target_index = next(
            (i for i, m in enumerate(migrations) if m.version == target_version),
            -1
        )

        if target_index == -1:
            self.logger.error(f"Versione target {target_version} non trovata")
            return False

        # Applica migrazioni fino alla target
        for migration in migrations[:target_index + 1]:
            if migration.version not in self.get_applied_migrations():
                result = self.apply_migration(migration)
                if not result.success:
                    self.logger.error(f"Errore migrazione {migration.version}")
                    return False

        return True

    def _get_connection(self) -> sqlite3.Connection:
        """Crea connessione database."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @contextmanager
    def _get_connection(self):
        """Context manager per connessione database."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _get_available_migrations(self) -> List[MigrationStep]:
        """Recupera migrazioni disponibili."""
        return [
            MigrationStep(
                version="001",
                description="Create projects table and project_id columns",
                up_sql=self._get_migration_001_up(),
                down_sql=self._get_migration_001_down(),
                pre_migration=self._pre_migration_001,
                post_migration=self._post_migration_001
            ),
            MigrationStep(
                version="002",
                description="Add password_hash column to users table",
                up_sql=self._get_migration_002_up(),
                down_sql=self._get_migration_002_down()
            ),
            MigrationStep(
                version="003",
                description="Add indexes for performance optimization",
                up_sql=self._get_migration_003_up(),
                down_sql=self._get_migration_003_down()
            ),
            MigrationStep(
                version="004",
                description="Create default project for existing users",
                up_sql=self._get_migration_004_up(),
                down_sql=self._get_migration_004_down(),
                post_migration=self._post_migration_004
            )
        ]

    def _get_migration_by_version(self, version: str) -> Optional[MigrationStep]:
        """Recupera migrazione per versione."""
        migrations = self._get_available_migrations()
        return next((m for m in migrations if m.version == version), None)

    def _get_migration_001_up(self) -> str:
        """SQL migrazione 001 - UP."""
        return """
        -- Crea tabella progetti
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            owner_id INTEGER,
            is_default BOOLEAN DEFAULT 0,
            settings JSON,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """

    def _get_migration_001_down(self) -> str:
        """SQL migrazione 001 - DOWN."""
        return """
        -- Rimuovi colonne project_id
        ALTER TABLE users DROP COLUMN IF EXISTS project_id;
        ALTER TABLE documents DROP COLUMN IF EXISTS project_id;
        ALTER TABLE courses DROP COLUMN IF EXISTS project_id;
        ALTER TABLE tasks DROP COLUMN IF EXISTS project_id;
        ALTER TABLE chat_sessions DROP COLUMN IF EXISTS project_id;
        ALTER TABLE concept_entities DROP COLUMN IF EXISTS project_id;
        ALTER TABLE user_xp DROP COLUMN IF EXISTS project_id;
        ALTER TABLE user_achievements DROP COLUMN IF EXISTS project_id;
        ALTER TABLE study_sessions DROP COLUMN IF EXISTS project_id;
        ALTER TABLE user_activity DROP COLUMN IF EXISTS project_id;
        ALTER TABLE document_processing_status DROP COLUMN IF EXISTS project_id;
        ALTER TABLE processing_error_log DROP COLUMN IF EXISTS project_id;
        ALTER TABLE processing_metrics DROP COLUMN IF EXISTS project_id;
        ALTER TABLE quarantine_files DROP COLUMN IF EXISTS project_id;
        ALTER TABLE bayesian_evidence DROP COLUMN IF EXISTS project_id;

        -- Rimuovi tabelle progetto
        DROP TABLE IF EXISTS user_projects;
        DROP TABLE IF EXISTS projects;
        """

    def _get_migration_002_up(self) -> str:
        """SQL migrazione 002 - UP (password_hash column)."""
        return """
        -- Add password_hash column to users table
        ALTER TABLE users ADD COLUMN password_hash TEXT;

        -- Create index on username for performance
        CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

        -- Create index on email for performance
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        """

    def _get_migration_002_down(self) -> str:
        """SQL migrazione 002 - DOWN (rimuovi password_hash column)."""
        return """
        -- Remove password_hash column (data loss!)
        ALTER TABLE users DROP COLUMN IF EXISTS password_hash;

        -- Remove indexes
        DROP INDEX IF EXISTS idx_users_username;
        DROP INDEX IF EXISTS idx_users_email;
        """

    def _get_migration_003_up(self) -> str:
        """SQL migrazione 003 - UP (indici performance)."""
        return """
        -- Indici per documenti
        CREATE INDEX IF NOT EXISTS idx_documents_project_id ON documents(project_id);
        CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(processing_status);
        CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(created_by);
        CREATE INDEX IF NOT EXISTS idx_documents_hash ON documents(content_hash);

        -- Indici per utenti
        CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

        -- Indici per corsi
        CREATE INDEX IF NOT EXISTS idx_courses_project_id ON courses(project_id);
        CREATE INDEX IF NOT EXISTS idx_courses_user_id ON courses(user_id);

        -- Indici per task
        CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON tasks(project_id);
        CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);
        CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);
        CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);

        -- Indici per chat
        CREATE INDEX IF NOT EXISTS idx_chat_sessions_project_id ON chat_sessions(project_id);
        CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);
        CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);

        -- Indici per conoscenza
        CREATE INDEX IF NOT EXISTS idx_concept_entities_project_id ON concept_entities(project_id);
        CREATE INDEX IF NOT EXISTS idx_concept_entities_user_id ON concept_entities(user_id);
        CREATE INDEX IF NOT EXISTS idx_concept_entities_type ON concept_entities(entity_type);
        CREATE INDEX IF NOT EXISTS idx_concept_relationships_user_id ON concept_relationships(user_id);

        -- Indici per attività utente
        CREATE INDEX IF NOT EXISTS idx_user_activity_project_id ON user_activity(project_id);
        CREATE INDEX IF NOT EXISTS idx_user_activity_user_id ON user_activity(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_activity_timestamp ON user_activity(timestamp);

        -- Indici per processamento
        CREATE INDEX IF NOT EXISTS idx_processing_status_project_id ON document_processing_status(project_id);
        CREATE INDEX IF NOT EXISTS idx_processing_status_state ON document_processing_status(processing_state);
        CREATE INDEX IF NOT EXISTS idx_processing_status_file ON document_processing_status(file_name);
        """

    def _get_migration_003_down(self) -> str:
        """SQL migrazione 003 - DOWN (rimuovi indici)."""
        return """
        -- Rimuovi tutti gli indici creati
        DROP INDEX IF EXISTS idx_documents_project_id;
        DROP INDEX IF EXISTS idx_documents_status;
        DROP INDEX IF EXISTS idx_documents_user_id;
        DROP INDEX IF EXISTS idx_documents_hash;
        DROP INDEX IF EXISTS idx_users_username;
        DROP INDEX IF EXISTS idx_users_email;
        DROP INDEX IF EXISTS idx_courses_project_id;
        DROP INDEX IF EXISTS idx_courses_user_id;
        DROP INDEX IF EXISTS idx_tasks_project_id;
        DROP INDEX IF EXISTS idx_tasks_user_id;
        DROP INDEX IF EXISTS idx_tasks_due_date;
        DROP INDEX IF EXISTS idx_tasks_status;
        DROP INDEX IF EXISTS idx_chat_sessions_project_id;
        DROP INDEX IF EXISTS idx_chat_sessions_user_id;
        DROP INDEX IF EXISTS idx_chat_messages_session_id;
        DROP INDEX IF EXISTS idx_concept_entities_project_id;
        DROP INDEX IF EXISTS idx_concept_entities_user_id;
        DROP INDEX IF EXISTS idx_concept_entities_type;
        DROP INDEX IF EXISTS idx_concept_relationships_user_id;
        DROP INDEX IF EXISTS idx_user_activity_project_id;
        DROP INDEX IF EXISTS idx_user_activity_user_id;
        DROP INDEX IF EXISTS idx_user_activity_timestamp;
        DROP INDEX IF EXISTS idx_processing_status_project_id;
        DROP INDEX IF EXISTS idx_processing_status_state;
        DROP INDEX IF EXISTS idx_processing_status_file;
        """

    def _get_migration_004_up(self) -> str:
        """SQL migrazione 004 - UP (crea progetto default)."""
        return """
        -- Crea progetto default "Wiki Globale" per tutti gli utenti esistenti
        INSERT OR IGNORE INTO projects (id, name, description, is_default)
        VALUES ('global-wiki', 'Wiki Globale', 'Progetto globale per tutti gli utenti', 1);
        """

    def _get_migration_004_down(self) -> str:
        """SQL migrazione 004 - DOWN."""
        return """
        -- Rimuovi progetto default
        DELETE FROM projects WHERE id = 'global-wiki';
        """

    def _post_migration_004(self) -> None:
        """Post-migration hook per migrazione 004."""
        self.logger.info("Migrazione 004 completata - Progetto default creato")

        # Verifica progetto default esistente
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM projects WHERE is_default = 1"
            )
            count = cursor.fetchone()[0]

            if count == 0:
                raise Exception("Progetto default non creato correttamente")

    def _pre_migration_001(self) -> None:
        """Pre-migration hook per migrazione 001."""
        self.logger.info("Iniziando migrazione 001 - Aggiunta supporto progetti")

        # Crea backup database
        backup_path = f"{self.db_path}.backup.{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        try:
            with sqlite3.connect(self.db_path) as source:
                backup = sqlite3.connect(backup_path)
                source.backup(backup)
                backup.close()
            self.logger.info(f"Backup database creato: {backup_path}")
        except Exception as e:
            self.logger.error(f"Errore creazione backup: {e}")
            raise

    def _post_migration_001(self) -> None:
        """Post-migration hook per migrazione 001."""
        self.logger.info("Migrazione 001 completata - Verifica integrità dati")

        # Verifica che tutte le tabelle esistano
        required_tables = [
            'projects', 'user_projects', 'users', 'documents',
            'courses', 'tasks', 'chat_sessions'
        ]

        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master WHERE type='table' AND name IN ({})
            """.format(','.join('?' * len(required_tables))), required_tables)

            existing_tables = {row[0] for row in cursor.fetchall()}
            missing_tables = set(required_tables) - existing_tables

            if missing_tables:
                raise Exception(f"Tabelle mancanti dopo migrazione: {missing_tables}")

    def _post_migration_003(self) -> None:
        """Post-migration hook per migrazione 003."""
        self.logger.info("Migrazione 003 completata - Progetto default creato")

        # Verifica progetto default esistente
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM projects WHERE is_default = 1"
            )
            count = cursor.fetchone()[0]

            if count == 0:
                raise Exception("Progetto default non creato correttamente")

    def run_migrations(self, target_version: Optional[str] = None) -> bool:
        """Esegue tutte le migrazioni pending."""
        try:
            # Inizializza database se necessario
            if not self._database_exists():
                self.initialize_database()

            # Recupera migrazioni disponibili
            available_migrations = self._get_available_migrations()

            if target_version:
                # Migra a versione specifica
                return self.migrate_to_version(target_version)
            else:
                # Applica tutte le migrazioni pending
                applied_migrations = self.get_applied_migrations()
                pending_migrations = self.get_pending_migrations(
                    [m.version for m in available_migrations]
                )

                if not pending_migrations:
                    self.logger.info("Nessuna migrazione pending")
                    return True

                self.logger.info(f"Applicando {len(pending_migrations)} migrazioni: {pending_migrations}")

                for migration in available_migrations:
                    if migration.version in pending_migrations:
                        result = self.apply_migration(migration)
                        if not result.success:
                            self.logger.error(f"Migrazione {migration.version} fallita")
                            return False

                self.logger.info("Tutte le migrazioni applicate con successo")
                return True

        except Exception as e:
            self.logger.error(f"Errore esecuzione migrazioni: {e}")
            return False

    def _database_exists(self) -> bool:
        """Verifica se database esiste e contiene tabelle."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
                tables = cursor.fetchall()
                return len(tables) > 0
        except Exception:
            return False

    def get_migration_status(self) -> Dict[str, Any]:
        """Recupera status migrazioni."""
        try:
            available = [m.version for m in self._get_available_migrations()]
            applied = self.get_applied_migrations()
            pending = self.get_pending_migrations(available)

            return {
                'total_migrations': len(available),
                'applied_migrations': len(applied),
                'pending_migrations': len(pending),
                'applied_versions': applied,
                'pending_versions': pending,
                'last_applied': max(applied) if applied else None
            }

        except Exception as e:
            self.logger.error(f"Errore recupero status migrazioni: {e}")
            return {
                'error': str(e)
            }

    def create_backup(self, backup_path: Optional[str] = None) -> str:
        """Crea backup database."""
        if backup_path is None:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            backup_path = f"{self.db_path}.backup.{timestamp}"

        try:
            with sqlite3.connect(self.db_path) as source:
                backup = sqlite3.connect(backup_path)
                source.backup(backup)
                backup.close()

            self.logger.info(f"Backup creato: {backup_path}")
            return backup_path

        except Exception as e:
            self.logger.error(f"Errore creazione backup: {e}")
            raise

    def restore_from_backup(self, backup_path: str) -> bool:
        """Ripristina database da backup."""
        try:
            # Crea backup corrente
            current_backup = self.create_backup()

            # Ripristina da backup
            with sqlite3.connect(backup_path) as backup:
                restore = sqlite3.connect(self.db_path)
                backup.backup(restore)
                restore.close()

            self.logger.info(f"Database ripristinato da: {backup_path}")
            return True

        except Exception as e:
            self.logger.error(f"Errore ripristino backup: {e}")
            return False
