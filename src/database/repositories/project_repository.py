"""
Project Repository.

Repository per gestione progetti nel database.
Implementa operazioni CRUD per i progetti.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class ProjectRepository(BaseRepository):
    """Repository per gestione progetti."""

    def __init__(self, db_path: str = "db_memoria/metadata.sqlite"):
        """Inizializza repository progetti."""
        super().__init__(db_path)
        self._ensure_table_exists()

    def _ensure_table_exists(self) -> None:
        """Crea tabella progetti se non esiste."""
        try:
            # Controlla se tabella esiste
            check_query = """
            SELECT sql FROM sqlite_master
            WHERE type='table' AND name='projects'
            """
            results = self.execute_query(check_query)

            if not results:
                # Crea tabella progetti
                query = """
                CREATE TABLE projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT,
                    description TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    user_id INTEGER,
                    settings TEXT
                )
                """
                self.execute_update(query)
                logger.info("Created projects table")

                # Crea tabella associazione utenti-progetti
                assoc_query = """
                CREATE TABLE user_projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    project_id INTEGER NOT NULL,
                    role TEXT DEFAULT 'member',
                    permissions TEXT,
                    joined_at TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects (id)
                )
                """
                self.execute_update(assoc_query)
                logger.info("Created user_projects table")

        except Exception as e:
            logger.error(f"Errore creazione tabella progetti: {e}")
            raise

    def get_by_id(self, project_id: Any) -> Optional[Dict[str, Any]]:
        """Recupera progetto per ID (solo attivi)."""
        try:
            query = "SELECT * FROM projects WHERE id = ? AND is_active = 1"
            results = self.execute_query(query, (project_id,))

            if results:
                return dict(results[0])
            return None
        except Exception as e:
            logger.error(f"Errore recupero progetto {project_id}: {e}")
            return None

    def find_by_id(self, project_id: Any) -> Optional[Dict[str, Any]]:
        """Alias per get_by_id (compatibilità)."""
        return self.get_by_id(project_id)

    def get_all(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Recupera tutti i progetti."""
        try:
            query = "SELECT * FROM projects WHERE is_active = 1"
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
            logger.error(f"Errore recupero progetti: {e}")
            return []

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea nuovo progetto."""
        try:
            # Prepara dati per inserimento
            project_data = {
                'name': data.get('name'),
                'type': data.get('type', 'Personale'),
                'description': data.get('description', ''),
                'created_at': data.get('created_at', datetime.now().isoformat()),
                'updated_at': data.get('updated_at', datetime.now().isoformat()),
                'is_active': 1,
                'user_id': data.get('user_id'),
                'settings': data.get('settings', '{}')
            }

            # Costruisci query INSERT
            columns = ', '.join(project_data.keys())
            placeholders = ', '.join(['?' for _ in project_data.values()])
            values = list(project_data.values())

            query = f"""
            INSERT INTO projects ({columns})
            VALUES ({placeholders})
            """

            success = self.execute_update(query, tuple(values))

            if success:
                # Recupera ID progetto creato
                project_id = self.execute_query("SELECT last_insert_rowid() as id")[0]['id']

                # Crea associazione utente-progetto se user_id specificato
                if project_data['user_id']:
                    self._create_user_project_association(project_data['user_id'], project_id)

                # Recupera progetto creato
                created_project = self.get_by_id(project_id)
                logger.info(f"Progetto creato: {created_project.get('name')}")
                return created_project

            return None

        except Exception as e:
            logger.error(f"Errore creazione progetto: {e}")
            return None

    def update(self, project_id: Any, data: Dict[str, Any]) -> bool:
        """Aggiorna progetto."""
        try:
            # Prepara dati per update
            update_data = {
                'name': data.get('name'),
                'type': data.get('type'),
                'description': data.get('description'),
                'updated_at': datetime.now().isoformat(),
                'settings': data.get('settings')
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

            params.append(project_id)

            query = f"""
            UPDATE projects SET {', '.join(update_fields)}
            WHERE id = ?
            """

            return self.execute_update(query, tuple(params))

        except Exception as e:
            logger.error(f"Errore aggiornamento progetto {project_id}: {e}")
            return False

    def delete(self, project_id: Any) -> bool:
        """Elimina progetto (soft delete)."""
        try:
            query = "UPDATE projects SET is_active = 0, updated_at = ? WHERE id = ?"
            return self.execute_update(query, (datetime.now().isoformat(), project_id))
        except Exception as e:
            logger.error(f"Errore eliminazione progetto {project_id}: {e}")
            return False

    def _create_user_project_association(self, user_id: int, project_id: int) -> bool:
        """Crea associazione utente-progetto."""
        try:
            query = """
            INSERT OR REPLACE INTO user_projects (user_id, project_id, role, permissions, joined_at)
            VALUES (?, ?, 'owner', '{"can_read": true, "can_write": true, "can_delete": true}', ?)
            """
            return self.execute_update(query, (user_id, project_id, datetime.now().isoformat()))
        except Exception as e:
            logger.error(f"Errore associazione utente-progetto: {e}")
            return False

    def get_projects_for_user(self, user_id: int) -> List[Dict[str, Any]]:
        """Recupera progetti per utente."""
        try:
            query = """
            SELECT p.* FROM projects p
            INNER JOIN user_projects up ON p.id = up.project_id
            WHERE up.user_id = ? AND p.is_active = 1
            ORDER BY p.created_at DESC
            """
            results = self.execute_query(query, (user_id,))
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Errore recupero progetti utente {user_id}: {e}")
            return []

    def get_project_stats(self, project_id: Any) -> Dict[str, Any]:
        """Ottieni statistiche progetto."""
        try:
            # Placeholder per statistiche - in implementazione completa useresti query specifiche
            return {
                'total_documents': 0,
                'total_tasks': 0,
                'total_courses': 0,
                'last_activity': None,
                'created_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Errore statistiche progetto {project_id}: {e}")
            return {}

    def get_user_permissions_in_project(self, user_id: int, project_id: Any) -> Dict[str, Any]:
        """Ottieni permessi utente in progetto."""
        try:
            query = """
            SELECT role, permissions FROM user_projects
            WHERE user_id = ? AND project_id = ?
            """
            results = self.execute_query(query, (user_id, project_id))

            if results:
                return {
                    'has_access': True,
                    'role': results[0]['role'],
                    'permissions': results[0]['permissions']
                }
            else:
                return {
                    'has_access': False,
                    'role': None,
                    'permissions': {}
                }
        except Exception as e:
            logger.error(f"Errore permessi utente {user_id} progetto {project_id}: {e}")
            return {'has_access': False, 'role': None, 'permissions': {}}

    def set_default_project(self, project_id: Any, user_id: int) -> bool:
        """Imposta progetto come default per utente."""
        try:
            # Prima rimuovi flag default da altri progetti utente
            reset_query = """
            UPDATE user_projects SET role = 'member'
            WHERE user_id = ? AND role = 'owner'
            """
            self.execute_update(reset_query, (user_id,))

            # Imposta nuovo progetto default
            update_query = """
            UPDATE user_projects SET role = 'owner'
            WHERE user_id = ? AND project_id = ?
            """
            return self.execute_update(update_query, (user_id, project_id))

        except Exception as e:
            logger.error(f"Errore impostazione progetto default: {e}")
            return False

    def get_project_activity_summary(self, project_id: Any, days: int = 7) -> Dict[str, Any]:
        """Ottieni summary attività progetto."""
        try:
            # Placeholder per attività - in implementazione completa useresti query specifiche
            return {
                'total_activity': 0,
                'documents_added': 0,
                'tasks_completed': 0,
                'last_activity_date': None
            }
        except Exception as e:
            logger.error(f"Errore activity summary progetto {project_id}: {e}")
            return {}


def create_project_repository(db_path: str = "db_memoria/metadata.sqlite") -> ProjectRepository:
    """Factory function per creare ProjectRepository."""
    return ProjectRepository(db_path)
