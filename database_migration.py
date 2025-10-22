#!/usr/bin/env python3
"""
Database Migration Script for Production
Script per migrazione database da sistema legacy a unificato
"""

import os
import sys
import sqlite3
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
from pathlib import Path

class DatabaseMigrator:
    """Gestore migrazione database per produzione"""

    def __init__(self, legacy_db_path: str = "test_metadata.sqlite", new_db_path: str = "metadata.sqlite"):
        self.logger = logging.getLogger(__name__)
        self.legacy_db_path = legacy_db_path
        self.new_db_path = new_db_path

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        # Migration statistics
        self.migration_stats = {
            "documents_migrated": 0,
            "users_migrated": 0,
            "projects_migrated": 0,
            "career_data_migrated": 0,
            "errors": [],
            "warnings": []
        }

    def validate_databases(self) -> bool:
        """Valida che i database esistano e siano accessibili"""
        self.logger.info("Validating databases...")

        # Verifica database legacy
        if not os.path.exists(self.legacy_db_path):
            self.logger.error(f"Legacy database not found: {self.legacy_db_path}")
            return False

        # Verifica database nuovo
        if not os.path.exists(self.new_db_path):
            self.logger.warning(f"New database not found: {self.new_db_path}")
            self.logger.info("New database will be created during migration")

        # Test connessione
        try:
            with sqlite3.connect(self.legacy_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                self.logger.info(f"Legacy database has {len(tables)} tables")

            if os.path.exists(self.new_db_path):
                with sqlite3.connect(self.new_db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()
                    self.logger.info(f"New database has {len(tables)} tables")

            return True

        except Exception as e:
            self.logger.error(f"Database validation failed: {str(e)}")
            return False

    def create_backup(self) -> Optional[str]:
        """Crea backup del database legacy"""
        self.logger.info("Creating database backup...")

        try:
            backup_name = f"database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            backup_path = f"backups/{backup_name}"

            os.makedirs("backups", exist_ok=True)

            # Copy database file
            import shutil
            shutil.copy2(self.legacy_db_path, backup_path)

            self.logger.info(f"Database backup created: {backup_path}")
            return backup_path

        except Exception as e:
            self.logger.error(f"Backup creation failed: {str(e)}")
            return None

    def analyze_legacy_structure(self) -> Dict[str, List[str]]:
        """Analizza struttura del database legacy"""
        self.logger.info("Analyzing legacy database structure...")

        structure = {}

        try:
            with sqlite3.connect(self.legacy_db_path) as conn:
                cursor = conn.cursor()

                # Ottieni tutte le tabelle
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()

                for table in tables:
                    table_name = table[0]
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()

                    structure[table_name] = [col[1] for col in columns]

                self.logger.info(f"Found {len(tables)} tables in legacy database")
                return structure

        except Exception as e:
            self.logger.error(f"Structure analysis failed: {str(e)}")
            return {}

    def migrate_documents(self) -> bool:
        """Migra documenti dal sistema legacy"""
        self.logger.info("Migrating documents...")

        try:
            with sqlite3.connect(self.legacy_db_path) as legacy_conn:
                legacy_cursor = legacy_conn.cursor()

                with sqlite3.connect(self.new_db_path) as new_conn:
                    new_cursor = new_conn.cursor()

                    # Crea tabella documenti se non esiste
                    self._create_documents_table(new_cursor)

                    # Trova tabella documenti nel legacy
                    legacy_tables = self.analyze_legacy_structure()
                    document_table = None

                    for table_name, columns in legacy_tables.items():
                        if any('document' in col.lower() or 'file' in col.lower() or 'content' in col.lower() for col in columns):
                            document_table = table_name
                            break

                    if not document_table:
                        self.logger.warning("No document table found in legacy database")
                        return True

                    # Migra documenti
                    legacy_cursor.execute(f"SELECT * FROM {document_table}")
                    documents = legacy_cursor.fetchall()

                    for doc in documents:
                        try:
                            # Adatta schema legacy al nuovo formato
                            doc_data = self._adapt_document_schema(doc, legacy_tables[document_table])
                            self._insert_document(new_cursor, doc_data)
                            self.migration_stats["documents_migrated"] += 1

                        except Exception as e:
                            self.migration_stats["errors"].append(f"Document migration error: {str(e)}")
                            self.logger.error(f"Failed to migrate document: {str(e)}")

                    new_conn.commit()
                    self.logger.info(f"Migrated {len(documents)} documents")

            return True

        except Exception as e:
            self.logger.error(f"Document migration failed: {str(e)}")
            return False

    def _create_documents_table(self, cursor: sqlite3.Cursor):
        """Crea tabella documenti nel nuovo database"""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                file_path TEXT,
                file_type TEXT,
                file_size INTEGER,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER,
                project_id INTEGER,
                category TEXT,
                tags TEXT,
                content_hash TEXT UNIQUE,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        ''')

    def _adapt_document_schema(self, doc: Tuple, columns: List[str]) -> Dict:
        """Adatta schema documento legacy al nuovo formato"""
        doc_dict = dict(zip(columns, doc))

        # Mappatura campi legacy ai nuovi campi
        field_mapping = {
            'title': ['title', 'name', 'filename', 'document_name'],
            'content': ['content', 'text', 'body', 'data'],
            'file_path': ['file_path', 'path', 'filepath', 'location'],
            'file_type': ['file_type', 'type', 'extension', 'mime_type'],
            'file_size': ['file_size', 'size', 'length'],
            'created_at': ['created_at', 'created', 'date_created', 'timestamp'],
            'user_id': ['user_id', 'user', 'owner', 'created_by'],
            'category': ['category', 'type', 'class', 'folder'],
            'tags': ['tags', 'keywords', 'labels']
        }

        adapted = {}
        for new_field, legacy_fields in field_mapping.items():
            for legacy_field in legacy_fields:
                if legacy_field in doc_dict and doc_dict[legacy_field] is not None:
                    adapted[new_field] = doc_dict[legacy_field]
                    break

        # Genera content_hash se non presente
        if 'content_hash' not in adapted:
            import hashlib
            content = adapted.get('content', '') or adapted.get('title', '')
            adapted['content_hash'] = hashlib.md5(content.encode()).hexdigest()

        return adapted

    def _insert_document(self, cursor: sqlite3.Cursor, doc_data: Dict):
        """Inserisce documento nel nuovo database"""
        columns = ', '.join(doc_data.keys())
        placeholders = ', '.join(['?' for _ in doc_data.values()])
        values = list(doc_data.values())

        query = f"INSERT OR REPLACE INTO documents ({columns}) VALUES ({placeholders})"
        cursor.execute(query, values)

    def migrate_users(self) -> bool:
        """Migra utenti dal sistema legacy"""
        self.logger.info("Migrating users...")

        try:
            with sqlite3.connect(self.legacy_db_path) as legacy_conn:
                legacy_cursor = legacy_conn.cursor()

                with sqlite3.connect(self.new_db_path) as new_conn:
                    new_cursor = new_conn.cursor()

                    # Crea tabella utenti se non esiste
                    self._create_users_table(new_cursor)

                    # Trova tabella utenti nel legacy
                    legacy_tables = self.analyze_legacy_structure()
                    user_table = None

                    for table_name, columns in legacy_tables.items():
                        if any('user' in col.lower() or 'email' in col.lower() or 'login' in col.lower() for col in columns):
                            user_table = table_name
                            break

                    if not user_table:
                        self.logger.warning("No user table found in legacy database")
                        return True

                    # Migra utenti
                    legacy_cursor.execute(f"SELECT * FROM {user_table}")
                    users = legacy_cursor.fetchall()

                    for user in users:
                        try:
                            user_data = self._adapt_user_schema(user, legacy_tables[user_table])
                            self._insert_user(new_cursor, user_data)
                            self.migration_stats["users_migrated"] += 1

                        except Exception as e:
                            self.migration_stats["errors"].append(f"User migration error: {str(e)}")
                            self.logger.error(f"Failed to migrate user: {str(e)}")

                    new_conn.commit()
                    self.logger.info(f"Migrated {len(users)} users")

            return True

        except Exception as e:
            self.logger.error(f"User migration failed: {str(e)}")
            return False

    def _create_users_table(self, cursor: sqlite3.Cursor):
        """Crea tabella utenti nel nuovo database"""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE,
                password_hash TEXT,
                first_name TEXT,
                last_name TEXT,
                role TEXT DEFAULT 'user',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')

    def _adapt_user_schema(self, user: Tuple, columns: List[str]) -> Dict:
        """Adatta schema utente legacy al nuovo formato"""
        user_dict = dict(zip(columns, user))

        field_mapping = {
            'email': ['email', 'mail', 'email_address'],
            'username': ['username', 'user', 'login', 'name'],
            'password_hash': ['password_hash', 'password', 'hash', 'pwd'],
            'first_name': ['first_name', 'fname', 'name'],
            'last_name': ['last_name', 'lname', 'surname'],
            'role': ['role', 'type', 'level', 'access'],
            'is_active': ['is_active', 'active', 'enabled', 'status'],
            'created_at': ['created_at', 'created', 'date_created'],
            'last_login': ['last_login', 'login_date', 'last_seen']
        }

        adapted = {}
        for new_field, legacy_fields in field_mapping.items():
            for legacy_field in legacy_fields:
                if legacy_field in user_dict and user_dict[legacy_field] is not None:
                    adapted[new_field] = user_dict[legacy_field]
                    break

        return adapted

    def _insert_user(self, cursor: sqlite3.Cursor, user_data: Dict):
        """Inserisce utente nel nuovo database"""
        columns = ', '.join(user_data.keys())
        placeholders = ', '.join(['?' for _ in user_data.values()])
        values = list(user_data.values())

        query = f"INSERT OR REPLACE INTO users ({columns}) VALUES ({placeholders})"
        cursor.execute(query, values)

    def migrate_projects(self) -> bool:
        """Migra progetti dal sistema legacy"""
        self.logger.info("Migrating projects...")

        try:
            with sqlite3.connect(self.legacy_db_path) as legacy_conn:
                legacy_cursor = legacy_conn.cursor()

                with sqlite3.connect(self.new_db_path) as new_conn:
                    new_cursor = new_conn.cursor()

                    # Crea tabella progetti se non esiste
                    self._create_projects_table(new_cursor)

                    # Trova tabella progetti nel legacy
                    legacy_tables = self.analyze_legacy_structure()
                    project_table = None

                    for table_name, columns in legacy_tables.items():
                        if any('project' in col.lower() or 'proj' in col.lower() for col in columns):
                            project_table = table_name
                            break

                    if not project_table:
                        self.logger.warning("No project table found in legacy database")
                        return True

                    # Migra progetti
                    legacy_cursor.execute(f"SELECT * FROM {project_table}")
                    projects = legacy_cursor.fetchall()

                    for project in projects:
                        try:
                            project_data = self._adapt_project_schema(project, legacy_tables[project_table])
                            self._insert_project(new_cursor, project_data)
                            self.migration_stats["projects_migrated"] += 1

                        except Exception as e:
                            self.migration_stats["errors"].append(f"Project migration error: {str(e)}")
                            self.logger.error(f"Failed to migrate project: {str(e)}")

                    new_conn.commit()
                    self.logger.info(f"Migrated {len(projects)} projects")

            return True

        except Exception as e:
            self.logger.error(f"Project migration failed: {str(e)}")
            return False

    def _create_projects_table(self, cursor: sqlite3.Cursor):
        """Crea tabella progetti nel nuovo database"""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                project_type TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER,
                metadata TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

    def _adapt_project_schema(self, project: Tuple, columns: List[str]) -> Dict:
        """Adatta schema progetto legacy al nuovo formato"""
        project_dict = dict(zip(columns, project))

        field_mapping = {
            'name': ['name', 'title', 'project_name'],
            'description': ['description', 'desc', 'summary'],
            'project_type': ['project_type', 'type', 'category'],
            'status': ['status', 'state', 'active'],
            'created_at': ['created_at', 'created', 'date_created'],
            'user_id': ['user_id', 'user', 'owner', 'created_by'],
            'metadata': ['metadata', 'data', 'config']
        }

        adapted = {}
        for new_field, legacy_fields in field_mapping.items():
            for legacy_field in legacy_fields:
                if legacy_field in project_dict and project_dict[legacy_field] is not None:
                    adapted[new_field] = project_dict[legacy_field]
                    break

        return adapted

    def _insert_project(self, cursor: sqlite3.Cursor, project_data: Dict):
        """Inserisce progetto nel nuovo database"""
        columns = ', '.join(project_data.keys())
        placeholders = ', '.join(['?' for _ in project_data.values()])
        values = list(project_data.values())

        query = f"INSERT OR REPLACE INTO projects ({columns}) VALUES ({placeholders})"
        cursor.execute(query, values)

    def migrate_career_data(self) -> bool:
        """Migra dati carriera dal sistema legacy"""
        self.logger.info("Migrating career data...")

        try:
            with sqlite3.connect(self.legacy_db_path) as legacy_conn:
                legacy_cursor = legacy_conn.cursor()

                with sqlite3.connect(self.new_db_path) as new_conn:
                    new_cursor = new_conn.cursor()

                    # Crea tabelle carriera se non esistono
                    self._create_career_tables(new_cursor)

                    # Trova tabelle carriera nel legacy
                    legacy_tables = self.analyze_legacy_structure()
                    career_tables = []

                    for table_name, columns in legacy_tables.items():
                        if any('career' in col.lower() or 'course' in col.lower() or 'lesson' in col.lower() for col in columns):
                            career_tables.append(table_name)

                    if not career_tables:
                        self.logger.warning("No career tables found in legacy database")
                        return True

                    # Migra dati carriera
                    for table_name in career_tables:
                        self._migrate_career_table(new_cursor, legacy_cursor, table_name, legacy_tables[table_name])

                    new_conn.commit()
                    self.logger.info(f"Migrated career data from {len(career_tables)} tables")

            return True

        except Exception as e:
            self.logger.error(f"Career data migration failed: {str(e)}")
            return False

    def _create_career_tables(self, cursor: sqlite3.Cursor):
        """Crea tabelle carriera nel nuovo database"""
        # Tabella corsi
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                university TEXT,
                department TEXT,
                semester TEXT,
                year INTEGER,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Tabella attività
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                activity_type TEXT,
                status TEXT DEFAULT 'pending',
                priority TEXT DEFAULT 'medium',
                due_date DATE,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                course_id INTEGER,
                user_id INTEGER,
                FOREIGN KEY (course_id) REFERENCES courses (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

    def _migrate_career_table(self, new_cursor: sqlite3.Cursor, legacy_cursor: sqlite3.Cursor, table_name: str, columns: List[str]):
        """Migra singola tabella carriera"""
        try:
            legacy_cursor.execute(f"SELECT * FROM {table_name}")
            records = legacy_cursor.fetchall()

            for record in records:
                try:
                    record_data = self._adapt_career_schema(record, columns, table_name)
                    self._insert_career_record(new_cursor, record_data, table_name)
                    self.migration_stats["career_data_migrated"] += 1

                except Exception as e:
                    self.migration_stats["errors"].append(f"Career record migration error: {str(e)}")
                    self.logger.error(f"Failed to migrate career record: {str(e)}")

        except Exception as e:
            self.logger.error(f"Failed to migrate career table {table_name}: {str(e)}")

    def _adapt_career_schema(self, record: Tuple, columns: List[str], table_name: str) -> Dict:
        """Adatta schema carriera legacy al nuovo formato"""
        record_dict = dict(zip(columns, record))

        # Determina tipo di record basato sul nome tabella
        if 'course' in table_name.lower():
            return self._adapt_course_schema(record_dict)
        elif 'activity' in table_name.lower() or 'task' in table_name.lower():
            return self._adapt_activity_schema(record_dict)
        else:
            return record_dict

    def _adapt_course_schema(self, course_dict: Dict) -> Dict:
        """Adatta schema corso"""
        field_mapping = {
            'name': ['name', 'title', 'course_name'],
            'description': ['description', 'desc', 'summary'],
            'university': ['university', 'school', 'institution'],
            'department': ['department', 'faculty', 'subject'],
            'semester': ['semester', 'term', 'period'],
            'year': ['year', 'academic_year'],
            'status': ['status', 'state', 'active'],
            'user_id': ['user_id', 'user', 'student_id']
        }

        adapted = {}
        for new_field, legacy_fields in field_mapping.items():
            for legacy_field in legacy_fields:
                if legacy_field in course_dict and course_dict[legacy_field] is not None:
                    adapted[new_field] = course_dict[legacy_field]
                    break

        return adapted

    def _adapt_activity_schema(self, activity_dict: Dict) -> Dict:
        """Adatta schema attività"""
        field_mapping = {
            'title': ['title', 'name', 'activity_name'],
            'description': ['description', 'desc', 'summary'],
            'activity_type': ['activity_type', 'type', 'category'],
            'status': ['status', 'state', 'completed'],
            'priority': ['priority', 'importance'],
            'due_date': ['due_date', 'deadline', 'due'],
            'completed_at': ['completed_at', 'completed', 'finished'],
            'course_id': ['course_id', 'course', 'subject_id'],
            'user_id': ['user_id', 'user', 'student_id']
        }

        adapted = {}
        for new_field, legacy_fields in field_mapping.items():
            for legacy_field in legacy_fields:
                if legacy_field in activity_dict and activity_dict[legacy_field] is not None:
                    adapted[new_field] = activity_dict[legacy_field]
                    break

        return adapted

    def _insert_career_record(self, cursor: sqlite3.Cursor, record_data: Dict, table_name: str):
        """Inserisce record carriera nel nuovo database"""
        if 'course' in table_name.lower():
            self._insert_course(cursor, record_data)
        elif 'activity' in table_name.lower() or 'task' in table_name.lower():
            self._insert_activity(cursor, record_data)

    def _insert_course(self, cursor: sqlite3.Cursor, course_data: Dict):
        """Inserisce corso"""
        columns = ', '.join(course_data.keys())
        placeholders = ', '.join(['?' for _ in course_data.values()])
        values = list(course_data.values())

        query = f"INSERT OR REPLACE INTO courses ({columns}) VALUES ({placeholders})"
        cursor.execute(query, values)

    def _insert_activity(self, cursor: sqlite3.Cursor, activity_data: Dict):
        """Inserisce attività"""
        columns = ', '.join(activity_data.keys())
        placeholders = ', '.join(['?' for _ in activity_data.values()])
        values = list(activity_data.values())

        query = f"INSERT OR REPLACE INTO activities ({columns}) VALUES ({placeholders})"
        cursor.execute(query, values)

    def validate_migration(self) -> bool:
        """Valida che la migrazione sia stata completata correttamente"""
        self.logger.info("Validating migration...")

        try:
            with sqlite3.connect(self.new_db_path) as conn:
                cursor = conn.cursor()

                # Verifica tabelle create
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()

                required_tables = ['documents', 'users', 'projects', 'courses', 'activities']
                existing_tables = [t[0] for t in tables]

                missing_tables = [t for t in required_tables if t not in existing_tables]

                if missing_tables:
                    self.logger.error(f"Missing tables after migration: {missing_tables}")
                    return False

                # Verifica dati migrati
                for table in required_tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    self.logger.info(f"Table {table}: {count} records")

                # Verifica integrità referenziale
                if not self._check_referential_integrity(cursor):
                    return False

                self.logger.info("Migration validation passed")
                return True

        except Exception as e:
            self.logger.error(f"Migration validation failed: {str(e)}")
            return False

    def _check_referential_integrity(self, cursor: sqlite3.Cursor) -> bool:
        """Verifica integrità referenziale"""
        try:
            # Verifica foreign keys
            cursor.execute("PRAGMA foreign_key_check")
            violations = cursor.fetchall()

            if violations:
                self.logger.error(f"Foreign key violations found: {violations}")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Referential integrity check failed: {str(e)}")
            return False

    def generate_migration_report(self) -> str:
        """Genera report migrazione"""
        report = {
            "migration_summary": {
                "legacy_database": self.legacy_db_path,
                "new_database": self.new_db_path,
                "migration_date": datetime.now().isoformat(),
                "statistics": self.migration_stats,
                "legacy_structure": self.analyze_legacy_structure()
            }
        }

        report_file = f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        self.logger.info(f"Migration report generated: {report_file}")
        return report_file

    def migrate_all(self) -> bool:
        """Esegue migrazione completa"""
        self.logger.info("Starting complete database migration...")

        # Validazione database
        if not self.validate_databases():
            return False

        # Backup
        backup_path = self.create_backup()
        if not backup_path:
            self.logger.error("Backup creation failed")
            return False

        # Migrazione documenti
        if not self.migrate_documents():
            return False

        # Migrazione utenti
        if not self.migrate_users():
            return False

        # Migrazione progetti
        if not self.migrate_projects():
            return False

        # Migrazione dati carriera
        if not self.migrate_career_data():
            return False

        # Validazione migrazione
        if not self.validate_migration():
            return False

        # Report
        report_file = self.generate_migration_report()
        self.logger.info("Database migration completed successfully!")
        self.logger.info(f"Report: {report_file}")

        return True

def main():
    """Main migration function"""
    if len(sys.argv) != 3:
        print("Usage: python database_migration.py <legacy_db_path> <new_db_path>")
        sys.exit(1)

    legacy_db = sys.argv[1]
    new_db = sys.argv[2]

    migrator = DatabaseMigrator(legacy_db, new_db)

    try:
        success = migrator.migrate_all()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logging.info("Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Migration failed with error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
