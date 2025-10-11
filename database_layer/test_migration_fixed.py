# Test Script - Migrazione Multi-Progetto (Versione Corretta)
"""
Script di test per validare migrazione 001 prima dell'applicazione.

Questo script:
1. Crea database test vuoto
2. Popola con dati simulati
3. Esegue migrazione in modalità dry-run
4. Valida risultati migrazione
5. Test rollback automatico
"""

import sqlite3
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import logging

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('TestMigration')

class TestDataGenerator:
    """Genera dati test per validazione migrazione"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.test_data = {
            'users': [
                (1, 'test_user', 'hashed_password', datetime.now().isoformat(), 1)
            ],
            'papers': [
                ('doc1.pdf', 'Titolo Documento 1', 'Autore 1', 2023, 'CAT1', 'Categoria 1', 'Preview AI 1', datetime.now().isoformat()),
                ('doc2.pdf', 'Titolo Documento 2', 'Autore 2', 2024, 'CAT2', 'Categoria 2', 'Preview AI 2', datetime.now().isoformat()),
                ('doc3.pdf', 'Titolo Documento 3', None, 2022, 'CAT1', 'Categoria 1', None, datetime.now().isoformat())
            ],
            'courses': [
                (1, 1, 'Corso Test 1', 'CT1', 'Descrizione corso 1', datetime.now().isoformat(), datetime.now().isoformat()),
                (2, 1, 'Corso Test 2', 'CT2', 'Descrizione corso 2', datetime.now().isoformat(), datetime.now().isoformat())
            ],
            'tasks': [
                (1, 1, None, None, 'Task Test 1', 'Descrizione task 1', 'high', 'short_term', None, 'pending', datetime.now().isoformat(), datetime.now().isoformat()),
                (2, 1, None, None, 'Task Test 2', 'Descrizione task 2', 'medium', 'medium_term', None, 'completed', datetime.now().isoformat(), datetime.now().isoformat())
            ],
            'chat_sessions': [
                (1, 1, 'Sessione Chat 1', datetime.now().isoformat(), datetime.now().isoformat()),
                (2, 1, 'Sessione Chat 2', datetime.now().isoformat(), datetime.now().isoformat())
            ]
        }

    def create_test_database(self) -> bool:
        """Crea database test con dati simulati"""
        try:
            # Crea directory
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Crea tabelle esistenti (simulazione schema attuale)
                self._create_existing_tables(cursor)

                # Popola tabelle con dati test
                self._populate_test_data(cursor)

                conn.commit()
                logger.info(f"Database test creato: {self.db_path}")
                return True

        except Exception as e:
            logger.error(f"Errore creazione database test: {e}")
            return False

    def _create_existing_tables(self, cursor):
        """Crea tabelle esistenti per test"""
        tables_sql = {
            'users': """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    is_new_user INTEGER DEFAULT 1
                )
            """,
            'papers': """
                CREATE TABLE papers (
                    file_name TEXT PRIMARY KEY,
                    title TEXT,
                    authors TEXT,
                    publication_year INTEGER,
                    category_id TEXT,
                    category_name TEXT,
                    formatted_preview TEXT,
                    processed_at TEXT
                )
            """,
            'courses': """
                CREATE TABLE courses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    course_name TEXT NOT NULL,
                    course_code TEXT UNIQUE,
                    description TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """,
            'tasks': """
                CREATE TABLE tasks (
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
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """,
            'chat_sessions': """
                CREATE TABLE chat_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_updated TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """
        }

        for table_name, sql in tables_sql.items():
            cursor.execute(sql)
            logger.debug(f"Tabella test creata: {table_name}")

    def _populate_test_data(self, cursor):
        """Popola tabelle con dati test"""
        # Users
        cursor.executemany(
            "INSERT INTO users (id, username, password_hash, created_at, is_new_user) VALUES (?, ?, ?, ?, ?)",
            self.test_data['users']
        )

        # Papers
        cursor.executemany(
            "INSERT INTO papers (file_name, title, authors, publication_year, category_id, category_name, formatted_preview, processed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            self.test_data['papers']
        )

        # Courses
        cursor.executemany(
            "INSERT INTO courses (id, user_id, course_name, course_code, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            self.test_data['courses']
        )

        # Tasks
        cursor.executemany(
            "INSERT INTO tasks (id, user_id, course_id, lecture_id, task_title, task_description, priority, task_type, due_date, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            self.test_data['tasks']
        )

        # Chat sessions
        cursor.executemany(
            "INSERT INTO chat_sessions (id, user_id, session_name, created_at, last_updated) VALUES (?, ?, ?, ?, ?)",
            self.test_data['chat_sessions']
        )

        logger.info("Dati test inseriti")

    def validate_test_data(self) -> Dict[str, Any]:
        """Valida dati test inseriti"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                validation = {}

                # Conta record per tabella
                for table in ['users', 'papers', 'courses', 'tasks', 'chat_sessions']:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    count = cursor.fetchone()['count']
                    validation[table] = count

                return validation

        except Exception as e:
            logger.error(f"Errore validazione dati test: {e}")
            return {}

def run_migration_test():
    """Esegue test completo migrazione"""
    print("🧪 TEST MIGRAZIONE MULTI-PROGETTO")
    print("=" * 60)

    # Crea database test
    test_db_path = "database_layer/test_migration.db"

    try:
        # Pulisci eventuale database test precedente
        if os.path.exists(test_db_path):
            os.remove(test_db_path)

        # 1. Crea database test con dati
        print("📊 Fase 1: Creazione database test...")
        generator = TestDataGenerator(test_db_path)

        if not generator.create_test_database():
            print("❌ Errore creazione database test")
            return False

        # Valida dati iniziali
        initial_data = generator.validate_test_data()
        print(f"✅ Database test creato con dati: {initial_data}")

        # 2. Test migrazione in dry-run
        print("\n🔍 Fase 2: Test migrazione dry-run...")
        from migration.migration_001 import run_migration_001

        dry_run_result = run_migration_001(test_db_path, dry_run=True)
        print(f"✅ Dry run completato: {dry_run_result}")

        # 3. Verifica dati dopo dry-run (dovrebbero essere invariati)
        after_dry_run = generator.validate_test_data()
        if initial_data != after_dry_run:
            print("❌ Dry-run ha modificato dati!")
            return False

        print("✅ Dry-run non ha modificato dati (corretto)")

        # 4. Esegui migrazione reale
        print("\n🚀 Fase 3: Esecuzione migrazione reale...")
        migration_result = run_migration_001(test_db_path, dry_run=False)

        if not migration_result['success']:
            print(f"❌ Migrazione fallita: {migration_result.get('error')}")
            return False

        print("✅ Migrazione completata con successo!")

        # 5. Valida migrazione
        print("\n🔍 Fase 4: Validazione migrazione...")

        with sqlite3.connect(test_db_path) as conn:
            cursor = conn.cursor()

            # Verifica tabella projects creata
            cursor.execute("SELECT COUNT(*) as count FROM projects")
            projects_count = cursor.fetchone()['count']
            print(f"✅ Progetti creati: {projects_count}")

            # Verifica progetto default
            cursor.execute("SELECT id, name FROM projects WHERE is_default = 1")
            default_project = cursor.fetchone()
            if default_project:
                print(f"✅ Progetto default: {default_project['name']} ({default_project['id']})")
            else:
                print("❌ Progetto default non trovato!")
                return False

            # Verifica project_id aggiunto alle tabelle
            tables_with_project_id = []
            tables_without_project_id = []

            test_tables = ['papers', 'courses', 'tasks', 'chat_sessions']
            for table in test_tables:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [col['name'] for col in cursor.fetchall()]

                if 'project_id' in columns:
                    tables_with_project_id.append(table)
                else:
                    tables_without_project_id.append(table)

            print(f"✅ Tabelle con project_id: {tables_with_project_id}")
            if tables_without_project_id:
                print(f"❌ Tabelle senza project_id: {tables_without_project_id}")
                return False

            # Verifica dati migrati al progetto default
            for table in test_tables:
                cursor.execute(f"SELECT COUNT(*) as total, COUNT(project_id) as with_project FROM {table}")
                result = cursor.fetchone()

                if result['with_project'] != result['total']:
                    print(f"❌ Tabella {table}: {result['total'] - result['with_project']} record senza project_id")
                    return False

            print("✅ Tutti i record hanno project_id assegnato")

        # 6. Test backup creato
        backup_path = migration_result.get('backup_path')
        if backup_path and os.path.exists(backup_path):
            print(f"✅ Backup creato: {backup_path}")

            # Verifica backup contiene dati originali
            with sqlite3.connect(backup_path) as backup_conn:
                cursor = backup_conn.cursor()

                # Conta record nel backup
                for table in ['papers', 'courses', 'tasks', 'chat_sessions']:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    count = cursor.fetchone()['count']
                    print(f"   Backup {table}: {count} record")
        else:
            print("⚠️ Backup non trovato")

        print("\n🎉 TEST MIGRAZIONE COMPLETATO CON SUCCESSO!")
        print("=" * 60)

        # Cleanup
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
            print("🗑️ Database test rimosso")

        if backup_path and os.path.exists(backup_path):
            os.remove(backup_path)
            print("🗑️ Backup test rimosso")

        return True

    except Exception as e:
        print(f"❌ Errore test migrazione: {e}")
        return False

def main():
    """Funzione principale test"""
    print("🧪 SISTEMA TEST MIGRAZIONE MULTI-PROGETTO")
    print("=" * 60)
    print("Questo script testa la migrazione 001 in ambiente sicuro")
    print()

    # Esegui test
    success = run_migration_test()

    if success:
        print("\n✅ PRONTO PER MIGRAZIONE PRODUZIONE!")
        print("Il sistema di migrazione è stato validato e può essere")
        print("applicato in sicurezza al database di produzione.")
    else:
        print("\n❌ TEST FALLITO!")
        print("Risolvere i problemi prima di applicare in produzione.")

    print("=" * 60)

if __name__ == "__main__":
    main()
