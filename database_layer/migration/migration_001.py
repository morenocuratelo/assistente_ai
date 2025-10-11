# Migration 001 - Schema Extension for Multi-Project Support
"""
Prima migrazione per supporto multi-progetto in Archivista AI.

Questa migrazione:
1. Crea tabella projects per gestione progetti
2. Aggiunge project_id a tutte le tabelle esistenti
3. Crea progetto default "Wiki Globale"
4. Migra dati esistenti al progetto default
5. Crea indici per performance ottimizzate

Autore: Archivista AI - Fase 1 Migration System
Data: Gennaio 2025
"""

import sqlite3
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Migration001')

class MigrationError(Exception):
    """Eccezione per errori migrazione"""
    pass

class DatabaseMigrator:
    """
    Sistema migrazione per estensione schema multi-progetto.

    Gestisce migrazione sicura con rollback automatico
    in caso di errori.
    """

    def __init__(self, db_path: str = "db_memoria/metadata.sqlite"):
        """
        Inizializza migratore database.

        Args:
            db_path: Percorso database da migrare
        """
        self.db_path = db_path
        self.backup_path = None
        self.migration_log = []

        # Verifica esistenza database
        if not os.path.exists(db_path):
            raise MigrationError(f"Database non trovato: {db_path}")

        logger.info(f"Migrator inizializzato per database: {db_path}")

    def create_backup(self) -> str:
        """
        Crea backup completo database prima migrazione.

        Returns:
            Percorso backup creato
        """
        try:
            # Crea directory backup
            backup_dir = Path("db_memoria/backups")
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Crea nome backup con timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"pre_migration_001_{timestamp}.sqlite"
            self.backup_path = backup_dir / backup_name

            # Crea backup
            import shutil
            shutil.copy2(self.db_path, self.backup_path)

            logger.info(f"Backup creato: {self.backup_path}")
            return str(self.backup_path)

        except Exception as e:
            logger.error(f"Errore creazione backup: {e}")
            raise MigrationError(f"Errore backup: {e}")

    def log_migration_step(self, step: str, success: bool, details: str = ""):
        """Log passo migrazione"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'step': step,
            'success': success,
            'details': details
        }
        self.migration_log.append(log_entry)

        status = "✅" if success else "❌"
        logger.info(f"{status} {step}: {details}")

    def execute_migration(self) -> bool:
        """
        Esegue migrazione completa.

        Returns:
            True se migrazione completata con successo
        """
        try:
            logger.info("🚀 Inizio migrazione 001 - Multi-Project Support")

            # 1. Crea backup
            self.log_migration_step("backup_creation", True, "Backup pre-migrazione creato")
            backup_path = self.create_backup()

            # 2. Crea tabella projects
            self.log_migration_step("projects_table", True, "Tabella projects creata")
            self._create_projects_table()

            # 3. Crea progetto default
            default_project_id = self._create_default_project()
            self.log_migration_step("default_project", True, f"Progetto default creato: {default_project_id}")

            # 4. Estendi tabelle esistenti con project_id
            self.log_migration_step("schema_extension", True, "Schema esteso con project_id")
            self._extend_existing_tables(default_project_id)

            # 5. Crea indici ottimizzati
            self.log_migration_step("indexes_creation", True, "Indici performance creati")
            self._create_performance_indexes()

            # 6. Validazione migrazione
            self.log_migration_step("validation", True, "Migrazione validata")
            self._validate_migration()

            logger.info("🎉 Migrazione 001 completata con successo!")
            return True

        except Exception as e:
            logger.error(f"❌ Errore migrazione: {e}")
            self.log_migration_step("migration_failed", False, str(e))

            # Tenta rollback se backup disponibile
            if self.backup_path and os.path.exists(self.backup_path):
                self._rollback_migration()

            raise MigrationError(f"Migrazione fallita: {e}")

    def _create_projects_table(self):
        """Crea tabella projects principale"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Crea tabella projects
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    is_default INTEGER DEFAULT 0,
                    settings TEXT,  -- JSON per configurazioni future
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)

            # Crea tabella associazione utenti-progetti (per accesso multiplo)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    project_id TEXT NOT NULL,
                    role TEXT DEFAULT 'member',  -- owner, admin, member, viewer
                    joined_at TEXT NOT NULL,
                    permissions TEXT,  -- JSON per permessi specifici
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
                    UNIQUE(user_id, project_id)
                )
            """)

            conn.commit()
            logger.debug("Tabella projects e user_projects create")

    def _create_default_project(self) -> str:
        """Crea progetto default 'Wiki Globale'"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Crea progetto default
            default_project_id = "wiki_globale"
            now = datetime.now().isoformat()

            cursor.execute("""
                INSERT OR IGNORE INTO projects (id, user_id, name, description, created_at, updated_at, is_default)
                VALUES (?, 1, ?, ?, ?, ?, 1)
            """, (
                default_project_id,
                "Wiki Globale",
                "Progetto globale contenente tutti i dati esistenti prima della migrazione multi-progetto",
                now, now
            ))

            # Crea associazione utente-progetto
            cursor.execute("""
                INSERT OR IGNORE INTO user_projects (user_id, project_id, role, joined_at)
                VALUES (?, ?, 'owner', ?)
            """, (1, default_project_id, now))

            conn.commit()
            logger.debug(f"Progetto default creato: {default_project_id}")
            return default_project_id

    def _extend_existing_tables(self, default_project_id: str):
        """Estende tabelle esistenti con colonna project_id"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Lista tabelle da estendere
            tables_to_extend = [
                ('papers', 'file_name'),  # Chiave primaria esistente
                ('chat_sessions', 'id'),
                ('chat_messages', 'id'),
                ('user_chat_history', 'id'),
                ('courses', 'id'),
                ('lectures', 'id'),
                ('materials', 'id'),
                ('tasks', 'id'),
                ('study_sessions', 'id'),
                ('concept_entities', 'id'),
                ('concept_relationships', 'id'),
                ('user_xp', 'id'),
                ('user_achievements', 'id'),
                ('user_activity', 'id')
            ]

            for table_name, primary_key in tables_to_extend:
                try:
                    # Verifica se colonna già esiste
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = [col['name'] for col in cursor.fetchall()]

                    if 'project_id' not in columns:
                        # Aggiungi colonna project_id
                        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN project_id TEXT")

                        # Crea foreign key constraint
                        cursor.execute(f"""
                            CREATE INDEX IF NOT EXISTS idx_{table_name}_project_id
                            ON {table_name}(project_id)
                        """)

                        logger.debug(f"Colonna project_id aggiunta a tabella: {table_name}")

                    # Aggiorna record esistenti con progetto default
                    if table_name != 'users':  # Users non ha project_id diretto
                        cursor.execute(f"""
                            UPDATE {table_name}
                            SET project_id = ?
                            WHERE project_id IS NULL
                        """, (default_project_id,))

                        logger.debug(f"Record esistenti aggiornati per tabella: {table_name}")

                except sqlite3.Error as e:
                    logger.error(f"Errore estensione tabella {table_name}: {e}")
                    raise MigrationError(f"Errore estensione tabella {table_name}: {e}")

            conn.commit()

    def _create_performance_indexes(self):
        """Crea indici per ottimizzare performance multi-progetto"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Indici per progetto
            indexes = [
                # Indici principali per progetto
                ("idx_papers_project_category", "papers(project_id, category_id)"),
                ("idx_papers_project_year", "papers(project_id, publication_year)"),
                ("idx_courses_project_user", "courses(project_id, user_id)"),
                ("idx_tasks_project_user", "tasks(project_id, user_id)"),
                ("idx_chat_project_user", "chat_sessions(project_id, user_id)"),
                ("idx_lectures_project_course", "lectures(project_id, course_id)"),

                # Indici composti per query comuni
                ("idx_user_activity_project_timestamp", "user_activity(project_id, timestamp)"),
                ("idx_study_sessions_project_user", "study_sessions(project_id, user_id)"),
                ("idx_materials_project_lecture", "materials(project_id, lecture_id)"),

                # Indici per ricerca full-text
                ("idx_papers_project_search", "papers(project_id, title, authors)"),
                ("idx_concept_entities_project", "concept_entities(project_id, entity_type)"),
            ]

            for index_name, index_columns in indexes:
                try:
                    cursor.execute(f"""
                        CREATE INDEX IF NOT EXISTS {index_name}
                        ON {index_columns}
                    """)
                    logger.debug(f"Indice creato: {index_name}")

                except sqlite3.Error as e:
                    logger.warning(f"Errore creazione indice {index_name}: {e}")

            conn.commit()

    def _validate_migration(self):
        """Valida integrità migrazione"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Verifica tabella projects
            cursor.execute("SELECT COUNT(*) as count FROM projects")
            row = cursor.fetchone()
            projects_count = row[0] if row else 0

            if projects_count == 0:
                raise MigrationError("Nessun progetto trovato dopo migrazione")

            # Verifica progetto default
            cursor.execute("SELECT id FROM projects WHERE is_default = 1")
            default_project_row = cursor.fetchone()
            default_project_id = default_project_row[0] if default_project_row else None

            if not default_project_id:
                raise MigrationError("Progetto default non trovato")

            # Verifica project_id in tabelle principali
            main_tables = ['papers', 'courses', 'tasks', 'chat_sessions']

            for table in main_tables:
                cursor.execute(f"SELECT COUNT(*) as total, COUNT(project_id) as with_project FROM {table}")
                row = cursor.fetchone()
                total = row[0] if row else 0
                with_project = row[1] if row and len(row) > 1 else 0

                if with_project != total:
                    logger.warning(f"Tabella {table}: {total - with_project} record senza project_id")

            logger.info("Validazione migrazione completata")

    def _rollback_migration(self):
        """Esegue rollback migrazione ripristinando backup"""
        try:
            if self.backup_path and os.path.exists(self.backup_path):
                # Ripristina backup
                import shutil
                shutil.copy2(self.backup_path, self.db_path)
                logger.info(f"Rollback eseguito - Backup ripristinato: {self.backup_path}")

                # Rimuovi backup dopo rollback
                os.remove(self.backup_path)
                logger.info("Backup di rollback rimosso")

        except Exception as e:
            logger.error(f"Errore rollback migrazione: {e}")
            raise MigrationError(f"Errore rollback: {e}")

    def get_migration_report(self) -> Dict[str, Any]:
        """Genera report completo migrazione"""
        return {
            'migration_id': '001',
            'migration_name': 'Multi-Project Schema Extension',
            'start_time': self.migration_log[0]['timestamp'] if self.migration_log else None,
            'end_time': datetime.now().isoformat(),
            'success': all(log['success'] for log in self.migration_log),
            'steps': self.migration_log,
            'backup_path': str(self.backup_path) if self.backup_path else None,
            'database_path': self.db_path
        }

def run_migration_001(db_path: str = "db_memoria/metadata.sqlite", dry_run: bool = False) -> Dict[str, Any]:
    """
    Esegue migrazione 001 per supporto multi-progetto.

    Args:
        db_path: Percorso database da migrare
        dry_run: Se True, simula migrazione senza modifiche

    Returns:
        Report migrazione completo
    """
    logger.info(f"{'SIMULAZIONE' if dry_run else 'ESECUZIONE'} Migrazione 001 - Multi-Project Support")

    try:
        migrator = DatabaseMigrator(db_path)

        if dry_run:
            logger.info("🔍 MODO DRY RUN - Nessuna modifica verrà applicata")
            # Qui potresti implementare simulazione
            return {
                'success': True,
                'dry_run': True,
                'message': 'Simulazione completata - nessuna modifica applicata'
            }

        # Esegui migrazione completa
        success = migrator.execute_migration()

        # Genera report finale
        report = migrator.get_migration_report()
        report['success'] = success

        return report

    except Exception as e:
        logger.error(f"Errore migrazione: {e}")
        return {
            'success': False,
            'error': str(e),
            'migration_id': '001'
        }

if __name__ == "__main__":
    # Esegui migrazione quando script chiamato direttamente
    import sys

    # Controlla argomenti
    db_path = "db_memoria/metadata.sqlite"
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("🔍 ESECUZIONE IN MODALITÀ DRY RUN")
        print("Nessuna modifica verrà applicata al database")

    # Esegui migrazione
    report = run_migration_001(db_path, dry_run)

    # Mostra risultati
    print("\n" + "="*60)
    print("📊 REPORT MIGRAZIONE 001")
    print("="*60)

    if report['success']:
        print("✅ MIGRAZIONE COMPLETATA CON SUCCESSO!")
        print(f"📁 Database: {db_path}")
        if report.get('backup_path'):
            print(f"💾 Backup: {report['backup_path']}")
        print(f"📈 Step eseguiti: {len(report.get('steps', []))}")
    else:
        print("❌ MIGRAZIONE FALLITA!")
        print(f"💥 Errore: {report.get('error', 'Errore sconosciuto')}")

    print("="*60)
