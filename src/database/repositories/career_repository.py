"""
Career Repository.

Repository per gestione carriera accademica nel database.
Implementa operazioni CRUD per corsi, lezioni e attività.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class CareerRepository(BaseRepository):
    """Repository per gestione carriera accademica."""

    def __init__(self, db_path: str = "db_memoria/metadata.sqlite"):
        """Inizializza repository carriera."""
        super().__init__(db_path)
        self._ensure_tables_exist()

    def _ensure_tables_exist(self) -> None:
        """Crea tabelle carriera se non esistono."""
        try:
            # Controlla se tabella courses esiste
            check_query = """
            SELECT sql FROM sqlite_master
            WHERE type='table' AND name='courses'
            """
            results = self.execute_query(check_query)

            if not results:
                # Crea tabella courses
                query = """
                CREATE TABLE courses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    code TEXT,
                    description TEXT,
                    user_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1
                )
                """
                self.execute_update(query)
                logger.info("Created courses table")

                # Crea tabella lectures
                lectures_query = """
                CREATE TABLE lectures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    lecture_date TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    FOREIGN KEY (course_id) REFERENCES courses (id)
                )
                """
                self.execute_update(lectures_query)
                logger.info("Created lectures table")

                # Crea tabella tasks
                tasks_query = """
                CREATE TABLE tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    course_id INTEGER,
                    lecture_id INTEGER,
                    title TEXT NOT NULL,
                    description TEXT,
                    priority TEXT DEFAULT 'medium',
                    status TEXT DEFAULT 'pending',
                    task_type TEXT DEFAULT 'short_term',
                    due_date TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    FOREIGN KEY (course_id) REFERENCES courses (id),
                    FOREIGN KEY (lecture_id) REFERENCES lectures (id)
                )
                """
                self.execute_update(tasks_query)
                logger.info("Created tasks table")

        except Exception as e:
            logger.error(f"Errore creazione tabelle carriera: {e}")
            raise

    def get_by_id(self, course_id: Any) -> Optional[Dict[str, Any]]:
        """Recupera corso per ID."""
        try:
            query = "SELECT * FROM courses WHERE id = ? AND is_active = 1"
            results = self.execute_query(query, (course_id,))

            if results:
                return dict(results[0])
            return None
        except Exception as e:
            logger.error(f"Errore recupero corso {course_id}: {e}")
            return None

    def find_by_id(self, course_id: Any) -> Optional[Dict[str, Any]]:
        """Alias per get_by_id (compatibilità)."""
        return self.get_by_id(course_id)

    def get_all(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Recupera tutti i corsi."""
        try:
            query = "SELECT * FROM courses WHERE is_active = 1"
            params = []

            if filters:
                for key, value in filters.items():
                    if value is not None:
                        query += f" AND {key} = ?"
                        params.append(value)

            query += " ORDER BY created_at DESC"

            results = self.execute_query(query, tuple(params))
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Errore recupero corsi: {e}")
            return []

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea nuovo corso."""
        try:
            # Prepara dati per inserimento
            course_data = {
                'name': data.get('name'),
                'code': data.get('code'),
                'description': data.get('description'),
                'user_id': data.get('user_id'),
                'created_at': data.get('created_at', datetime.now().isoformat()),
                'updated_at': data.get('updated_at', datetime.now().isoformat()),
                'is_active': 1
            }

            # Costruisci query INSERT
            columns = ', '.join(course_data.keys())
            placeholders = ', '.join(['?' for _ in course_data.values()])
            values = list(course_data.values())

            query = f"""
            INSERT INTO courses ({columns})
            VALUES ({placeholders})
            """

            success = self.execute_update(query, tuple(values))

            if success:
                # Recupera ID corso creato
                course_id = self.execute_query("SELECT last_insert_rowid() as id")[0]['id']

                # Recupera corso creato
                created_course = self.get_by_id(course_id)
                logger.info(f"Corso creato: {created_course.get('name')}")
                return created_course

            return None

        except Exception as e:
            logger.error(f"Errore creazione corso: {e}")
            return None

    def update(self, course_id: Any, data: Dict[str, Any]) -> bool:
        """Aggiorna corso."""
        try:
            # Prepara dati per update
            update_data = {
                'name': data.get('name'),
                'code': data.get('code'),
                'description': data.get('description'),
                'updated_at': datetime.now().isoformat()
            }

            # Costruisci query UPDATE
            update_fields = []
            params = []

            for field, value in update_data.items():
                if value is not None:
                    update_fields.append(f"{field} = ?")
                    params.append(value)

            if not update_fields:
                return True

            params.append(course_id)

            query = f"""
            UPDATE courses SET {', '.join(update_fields)}
            WHERE id = ?
            """

            return self.execute_update(query, tuple(params))

        except Exception as e:
            logger.error(f"Errore aggiornamento corso {course_id}: {e}")
            return False

    def delete(self, course_id: Any) -> bool:
        """Elimina corso (soft delete)."""
        try:
            query = "UPDATE courses SET is_active = 0, updated_at = ? WHERE id = ?"
            return self.execute_update(query, (datetime.now().isoformat(), course_id))
        except Exception as e:
            logger.error(f"Errore eliminazione corso {course_id}: {e}")
            return False

    def get_course_lectures(self, course_id: Any) -> List[Dict[str, Any]]:
        """Recupera lezioni per un corso."""
        try:
            query = """
            SELECT * FROM lectures
            WHERE course_id = ? AND is_active = 1
            ORDER BY lecture_date DESC
            """
            results = self.execute_query(query, (course_id,))
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Errore recupero lezioni corso {course_id}: {e}")
            return []

    def get_course_tasks(self, course_id: Any) -> List[Dict[str, Any]]:
        """Recupera attività per un corso."""
        try:
            query = """
            SELECT * FROM tasks
            WHERE course_id = ? AND is_active = 1
            ORDER BY due_date ASC, priority DESC
            """
            results = self.execute_query(query, (course_id,))
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Errore recupero attività corso {course_id}: {e}")
            return []

    def get_user_tasks(self, user_id: int) -> List[Dict[str, Any]]:
        """Recupera tutte le attività per un utente."""
        try:
            query = """
            SELECT * FROM tasks
            WHERE user_id = ? AND is_active = 1
            ORDER BY due_date ASC, priority DESC
            """
            results = self.execute_query(query, (user_id,))
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Errore recupero attività utente {user_id}: {e}")
            return []

    def create_lecture(self, lecture_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea nuova lezione."""
        try:
            # Prepara dati per inserimento
            lecture_data_db = {
                'course_id': lecture_data.get('course_id'),
                'title': lecture_data.get('title'),
                'description': lecture_data.get('description'),
                'lecture_date': lecture_data.get('lecture_date'),
                'created_at': lecture_data.get('created_at', datetime.now().isoformat()),
                'updated_at': lecture_data.get('updated_at', datetime.now().isoformat()),
                'is_active': 1
            }

            # Costruisci query INSERT
            columns = ', '.join(lecture_data_db.keys())
            placeholders = ', '.join(['?' for _ in lecture_data_db.values()])
            values = list(lecture_data_db.values())

            query = f"""
            INSERT INTO lectures ({columns})
            VALUES ({placeholders})
            """

            success = self.execute_update(query, tuple(values))

            if success:
                # Recupera ID lezione creata
                lecture_id = self.execute_query("SELECT last_insert_rowid() as id")[0]['id']

                # Recupera lezione creata
                created_lecture = self.get_lecture_by_id(lecture_id)
                logger.info(f"Lezione creata: {created_lecture.get('title')}")
                return created_lecture

            return None

        except Exception as e:
            logger.error(f"Errore creazione lezione: {e}")
            return None

    def get_lecture_by_id(self, lecture_id: Any) -> Optional[Dict[str, Any]]:
        """Recupera lezione per ID."""
        try:
            query = "SELECT * FROM lectures WHERE id = ? AND is_active = 1"
            results = self.execute_query(query, (lecture_id,))

            if results:
                return dict(results[0])
            return None
        except Exception as e:
            logger.error(f"Errore recupero lezione {lecture_id}: {e}")
            return None

    def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea nuova attività."""
        try:
            # Prepara dati per inserimento
            task_data_db = {
                'user_id': task_data.get('user_id'),
                'course_id': task_data.get('course_id'),
                'lecture_id': task_data.get('lecture_id'),
                'title': task_data.get('title'),
                'description': task_data.get('description'),
                'priority': task_data.get('priority', 'medium'),
                'status': task_data.get('status', 'pending'),
                'task_type': task_data.get('task_type', 'short_term'),
                'due_date': task_data.get('due_date'),
                'created_at': task_data.get('created_at', datetime.now().isoformat()),
                'updated_at': task_data.get('updated_at', datetime.now().isoformat()),
                'is_active': 1
            }

            # Costruisci query INSERT
            columns = ', '.join(task_data_db.keys())
            placeholders = ', '.join(['?' for _ in task_data_db.values()])
            values = list(task_data_db.values())

            query = f"""
            INSERT INTO tasks ({columns})
            VALUES ({placeholders})
            """

            success = self.execute_update(query, tuple(values))

            if success:
                # Recupera ID attività creata
                task_id = self.execute_query("SELECT last_insert_rowid() as id")[0]['id']

                # Recupera attività creata
                created_task = self.get_task_by_id(task_id)
                logger.info(f"Attività creata: {created_task.get('title')}")
                return created_task

            return None

        except Exception as e:
            logger.error(f"Errore creazione attività: {e}")
            return None

    def get_task_by_id(self, task_id: Any) -> Optional[Dict[str, Any]]:
        """Recupera attività per ID."""
        try:
            query = "SELECT * FROM tasks WHERE id = ? AND is_active = 1"
            results = self.execute_query(query, (task_id,))

            if results:
                return dict(results[0])
            return None
        except Exception as e:
            logger.error(f"Errore recupero attività {task_id}: {e}")
            return None

    def update_task(self, task_id: Any, data: Dict[str, Any]) -> bool:
        """Aggiorna attività."""
        try:
            # Prepara dati per update
            update_data = {
                'title': data.get('title'),
                'description': data.get('description'),
                'priority': data.get('priority'),
                'status': data.get('status'),
                'task_type': data.get('task_type'),
                'due_date': data.get('due_date'),
                'updated_at': datetime.now().isoformat()
            }

            # Costruisci query UPDATE
            update_fields = []
            params = []

            for field, value in update_data.items():
                if value is not None:
                    update_fields.append(f"{field} = ?")
                    params.append(value)

            if not update_fields:
                return True

            params.append(task_id)

            query = f"""
            UPDATE tasks SET {', '.join(update_fields)}
            WHERE id = ?
            """

            return self.execute_update(query, tuple(params))

        except Exception as e:
            logger.error(f"Errore aggiornamento attività {task_id}: {e}")
            return False

    def delete_task(self, task_id: Any) -> bool:
        """Elimina attività (soft delete)."""
        try:
            query = "UPDATE tasks SET is_active = 0, updated_at = ? WHERE id = ?"
            return self.execute_update(query, (datetime.now().isoformat(), task_id))
        except Exception as e:
            logger.error(f"Errore eliminazione attività {task_id}: {e}")
            return False


def create_career_repository(db_path: str = "db_memoria/metadata.sqlite") -> CareerRepository:
    """Factory function per creare CareerRepository."""
    return CareerRepository(db_path)
