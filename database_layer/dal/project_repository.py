# Project Repository - Gestione progetti multi-tenant
"""
Repository specializzato per gestione progetti in Archivista AI.

Gestisce:
- Tabella projects per informazioni progetto
- Tabella user_projects per associazioni utente-progetto
- Operazioni CRUD sicure per progetti
- Gestione permessi e ruoli progetto
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from .base_repository import BaseRepository, DatabaseOperationError

logger = logging.getLogger('ProjectRepository')

class ProjectRepository(BaseRepository):
    """
    Repository per gestione progetti.

    Fornisce operazioni specializzate per gestione progetti
    con supporto ruoli e permessi.
    """

    def _get_table_name(self) -> str:
        """Restituisce nome tabella principale progetti"""
        return 'projects'

    def _validate_create_data(self, data: Dict[str, Any]):
        """Validazione dati creazione progetto"""
        super()._validate_create_data(data)

        required_fields = ['id', 'user_id', 'name']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Campo obbligatorio mancante: {field}")

        # Validazione ID progetto
        if not data['id'] or not data['id'].strip():
            raise ValueError("ID progetto non può essere vuoto")

        if not self._is_valid_project_id(data['id']):
            raise ValueError("ID progetto non valido (solo lettere, numeri, underscore)")

        # Validazione nome progetto
        if not data['name'] or not data['name'].strip():
            raise ValueError("Nome progetto non può essere vuoto")

        if len(data['name']) > 100:
            raise ValueError("Nome progetto troppo lungo (max 100 caratteri)")

    def _is_valid_project_id(self, project_id: str) -> bool:
        """Validazione formato ID progetto"""
        import re
        return bool(re.match(r'^[a-zA-Z0-9_]+$', project_id))

    def create_project(self, project_id: str, user_id: int, name: str, description: str = None) -> int:
        """
        Crea nuovo progetto.

        Args:
            project_id: ID univoco progetto
            user_id: ID utente creatore
            name: Nome progetto
            description: Descrizione progetto

        Returns:
            ID progetto creato

        Raises:
            DatabaseOperationError: Se progetto esiste già
        """
        try:
            # Verifica unicità progetto
            if self.find_by_id(project_id):
                raise DatabaseOperationError(f"Progetto '{project_id}' già esistente")

            # Crea progetto
            project_data = {
                'id': project_id,
                'user_id': user_id,
                'name': name.strip(),
                'description': description.strip() if description else None,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'is_default': 0
            }

            project_db_id = self.create(project_data)

            # Crea associazione utente-progetto come owner
            self._create_user_project_association(user_id, project_id, 'owner')

            logger.info(f"Progetto creato: {project_id} da utente {user_id}")
            return project_db_id

        except Exception as e:
            logger.error(f"Errore creazione progetto {project_id}: {e}")
            raise DatabaseOperationError(f"Errore creazione progetto: {e}")

    def _create_user_project_association(self, user_id: int, project_id: str, role: str = 'member'):
        """Crea associazione utente-progetto"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT OR IGNORE INTO user_projects (user_id, project_id, role, joined_at)
                    VALUES (?, ?, ?, ?)
                """, (user_id, project_id, role, datetime.now().isoformat()))

                conn.commit()
                logger.debug(f"Associazione utente-progetto creata: {user_id} -> {project_id} ({role})")

        except Exception as e:
            logger.error(f"Errore associazione utente-progetto: {e}")
            raise DatabaseOperationError(f"Errore associazione utente-progetto: {e}")

    def find_by_id(self, project_id: str) -> Optional[Dict]:
        """
        Trova progetto per ID.

        Args:
            project_id: ID progetto da cercare

        Returns:
            Progetto trovato o None
        """
        query = "SELECT * FROM projects WHERE id = ?"
        return self.execute_query(query, (project_id,), fetch='one')

    def find_by_user(self, user_id: int) -> List[Dict]:
        """
        Trova tutti i progetti di un utente.

        Args:
            user_id: ID utente

        Returns:
            Lista progetti utente
        """
        query = """
            SELECT p.*, up.role, up.joined_at as user_joined_at
            FROM projects p
            JOIN user_projects up ON p.id = up.project_id
            WHERE up.user_id = ?
            ORDER BY p.created_at DESC
        """
        return self.execute_query(query, (user_id,), fetch='all')

    def find_default_project(self) -> Optional[Dict]:
        """
        Trova progetto default.

        Returns:
            Progetto default o None
        """
        query = "SELECT * FROM projects WHERE is_default = 1 LIMIT 1"
        return self.execute_query(query, fetch='one')

    def get_user_role_in_project(self, user_id: int, project_id: str) -> Optional[str]:
        """
        Restituisce ruolo utente nel progetto.

        Args:
            user_id: ID utente
            project_id: ID progetto

        Returns:
            Ruolo utente o None se non associato
        """
        query = "SELECT role FROM user_projects WHERE user_id = ? AND project_id = ?"
        result = self.execute_query(query, (user_id, project_id), fetch='one')
        return result['role'] if result else None

    def add_user_to_project(self, user_id: int, project_id: str, role: str = 'member') -> bool:
        """
        Aggiunge utente a progetto.

        Args:
            user_id: ID utente da aggiungere
            project_id: ID progetto
            role: Ruolo utente nel progetto

        Returns:
            True se aggiunto con successo
        """
        try:
            # Verifica progetto esiste
            if not self.find_by_id(project_id):
                raise DatabaseOperationError(f"Progetto non trovato: {project_id}")

            # Crea associazione
            self._create_user_project_association(user_id, project_id, role)

            logger.info(f"Utente {user_id} aggiunto a progetto {project_id} con ruolo {role}")
            return True

        except Exception as e:
            logger.error(f"Errore aggiunta utente a progetto: {e}")
            raise DatabaseOperationError(f"Errore aggiunta utente: {e}")

    def remove_user_from_project(self, user_id: int, project_id: str) -> bool:
        """
        Rimuove utente da progetto.

        Args:
            user_id: ID utente da rimuovere
            project_id: ID progetto

        Returns:
            True se rimosso con successo
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Verifica associazione esiste
                cursor.execute("SELECT id FROM user_projects WHERE user_id = ? AND project_id = ?", (user_id, project_id))
                if not cursor.fetchone():
                    logger.warning(f"Associazione utente-progetto non trovata: {user_id} -> {project_id}")
                    return False

                # Rimuovi associazione
                cursor.execute("DELETE FROM user_projects WHERE user_id = ? AND project_id = ?", (user_id, project_id))
                conn.commit()

                logger.info(f"Utente {user_id} rimosso da progetto {project_id}")
                return True

        except Exception as e:
            logger.error(f"Errore rimozione utente da progetto: {e}")
            raise DatabaseOperationError(f"Errore rimozione utente: {e}")

    def update_project(self, project_id: str, name: str = None, description: str = None) -> bool:
        """
        Aggiorna informazioni progetto.

        Args:
            project_id: ID progetto da aggiornare
            name: Nuovo nome progetto
            description: Nuova descrizione progetto

        Returns:
            True se aggiornato con successo
        """
        try:
            update_data = {
                'updated_at': datetime.now().isoformat()
            }

            if name is not None:
                update_data['name'] = name.strip()

            if description is not None:
                update_data['description'] = description.strip() if description else None

            # Usa update diretto per tabella projects
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                set_parts = ', '.join([f"{key} = ?" for key in update_data.keys()])
                values = tuple(update_data.values()) + (project_id,)

                query = f"UPDATE projects SET {set_parts} WHERE id = ?"
                cursor.execute(query, values)
                conn.commit()

            logger.info(f"Progetto aggiornato: {project_id}")
            return True

        except Exception as e:
            logger.error(f"Errore aggiornamento progetto {project_id}: {e}")
            raise DatabaseOperationError(f"Errore aggiornamento progetto: {e}")

    def delete_project(self, project_id: str) -> bool:
        """
        Elimina progetto e tutti i suoi dati.

        Args:
            project_id: ID progetto da eliminare

        Returns:
            True se eliminato con successo
        """
        try:
            # Verifica progetto esiste
            if not self.find_by_id(project_id):
                logger.warning(f"Tentativo eliminazione progetto inesistente: {project_id}")
                return False

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Elimina associazioni utenti-progetto
                cursor.execute("DELETE FROM user_projects WHERE project_id = ?", (project_id,))

                # Elimina progetto (cascade eliminerà dati correlati)
                cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))

                conn.commit()

            logger.info(f"Progetto eliminato: {project_id}")
            return True

        except Exception as e:
            logger.error(f"Errore eliminazione progetto {project_id}: {e}")
            raise DatabaseOperationError(f"Errore eliminazione progetto: {e}")

    def set_default_project(self, project_id: str, user_id: int) -> bool:
        """
        Imposta progetto come default per utente.

        Args:
            project_id: ID progetto da impostare come default
            user_id: ID utente

        Returns:
            True se impostato con successo
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Rimuovi flag default da altri progetti utente
                cursor.execute("""
                    UPDATE projects
                    SET is_default = 0
                    WHERE user_id = ? AND is_default = 1
                """, (user_id,))

                # Imposta nuovo progetto default
                cursor.execute("""
                    UPDATE projects
                    SET is_default = 1, updated_at = ?
                    WHERE id = ? AND user_id = ?
                """, (datetime.now().isoformat(), project_id, user_id))

                conn.commit()

            logger.info(f"Progetto default impostato: {project_id} per utente {user_id}")
            return True

        except Exception as e:
            logger.error(f"Errore impostazione progetto default: {e}")
            raise DatabaseOperationError(f"Errore impostazione progetto default: {e}")

    def get_project_stats(self, project_id: str) -> Dict[str, Any]:
        """
        Statistiche progetto.

        Args:
            project_id: ID progetto

        Returns:
            Dizionario statistiche progetto
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Conta documenti progetto
                cursor.execute("SELECT COUNT(*) as count FROM papers WHERE project_id = ?", (project_id,))
                documents_count = cursor.fetchone()['count']

                # Conta corsi progetto
                cursor.execute("SELECT COUNT(*) as count FROM courses WHERE project_id = ?", (project_id,))
                courses_count = cursor.fetchone()['count']

                # Conta attività progetto
                cursor.execute("SELECT COUNT(*) as count FROM tasks WHERE project_id = ?", (project_id,))
                tasks_count = cursor.fetchone()['count']

                # Conta sessioni chat progetto
                cursor.execute("SELECT COUNT(*) as count FROM chat_sessions WHERE project_id = ?", (project_id,))
                chat_sessions_count = cursor.fetchone()['count']

                # Conta utenti progetto
                cursor.execute("SELECT COUNT(*) as count FROM user_projects WHERE project_id = ?", (project_id,))
                users_count = cursor.fetchone()['count']

                return {
                    'project_id': project_id,
                    'documents_count': documents_count,
                    'courses_count': courses_count,
                    'tasks_count': tasks_count,
                    'chat_sessions_count': chat_sessions_count,
                    'users_count': users_count,
                    'total_items': documents_count + courses_count + tasks_count + chat_sessions_count
                }

        except Exception as e:
            logger.error(f"Errore statistiche progetto {project_id}: {e}")
            return {}

    def list_projects(self, user_id: int = None, limit: int = 100) -> List[Dict]:
        """
        Lista progetti con informazioni complete.

        Args:
            user_id: ID utente per filtro (se None, tutti i progetti)
            limit: Limite risultati

        Returns:
            Lista progetti con statistiche
        """
        try:
            base_query = """
                SELECT p.*,
                       up.role,
                       up.joined_at as user_joined_at
                FROM projects p
                JOIN user_projects up ON p.id = up.project_id
            """

            if user_id:
                query = f"{base_query} WHERE up.user_id = ? ORDER BY p.created_at DESC LIMIT ?"
                projects = self.execute_query(query, (user_id, limit), fetch='all')
            else:
                query = f"{base_query} ORDER BY p.created_at DESC LIMIT ?"
                projects = self.execute_query(query, (limit,), fetch='all')

            # Aggiungi statistiche per ogni progetto
            for project in projects:
                project_id = project['id']
                stats = self.get_project_stats(project_id)
                project['stats'] = stats

            return projects

        except Exception as e:
            logger.error(f"Errore lista progetti: {e}")
            return []

    def get_projects_for_user(self, user_id: int) -> List[Dict]:
        """
        Restituisce tutti i progetti accessibili da utente.

        Args:
            user_id: ID utente

        Returns:
            Lista progetti utente con ruolo
        """
        query = """
            SELECT p.*, up.role, up.joined_at as user_joined_at
            FROM projects p
            JOIN user_projects up ON p.id = up.project_id
            WHERE up.user_id = ?
            ORDER BY p.is_default DESC, p.created_at DESC
        """
        return self.execute_query(query, (user_id,), fetch='all')

    def get_user_permissions_in_project(self, user_id: int, project_id: str) -> Dict[str, Any]:
        """
        Restituisce permessi utente nel progetto.

        Args:
            user_id: ID utente
            project_id: ID progetto

        Returns:
            Dizionario permessi utente
        """
        try:
            role = self.get_user_role_in_project(user_id, project_id)

            if not role:
                return {'has_access': False, 'role': None, 'permissions': {}}

            # Definisci permessi per ruolo
            role_permissions = {
                'owner': {
                    'can_read': True,
                    'can_write': True,
                    'can_delete': True,
                    'can_manage_users': True,
                    'can_manage_settings': True,
                    'can_delete_project': True
                },
                'admin': {
                    'can_read': True,
                    'can_write': True,
                    'can_delete': True,
                    'can_manage_users': True,
                    'can_manage_settings': False,
                    'can_delete_project': False
                },
                'member': {
                    'can_read': True,
                    'can_write': True,
                    'can_delete': False,
                    'can_manage_users': False,
                    'can_manage_settings': False,
                    'can_delete_project': False
                },
                'viewer': {
                    'can_read': True,
                    'can_write': False,
                    'can_delete': False,
                    'can_manage_users': False,
                    'can_manage_settings': False,
                    'can_delete_project': False
                }
            }

            permissions = role_permissions.get(role, {})

            return {
                'has_access': True,
                'role': role,
                'permissions': permissions
            }

        except Exception as e:
            logger.error(f"Errore permessi utente {user_id} in progetto {project_id}: {e}")
            return {'has_access': False, 'role': None, 'permissions': {}}

    def search_projects(self, query: str, user_id: int = None, limit: int = 20) -> List[Dict]:
        """
        Ricerca progetti per nome o descrizione.

        Args:
            query: Testo da cercare
            user_id: ID utente per filtro
            limit: Limite risultati

        Returns:
            Lista progetti matching
        """
        try:
            search_term = f'%{query}%'

            if user_id:
                sql_query = """
                    SELECT p.*, up.role
                    FROM projects p
                    JOIN user_projects up ON p.id = up.project_id
                    WHERE up.user_id = ? AND (p.name LIKE ? OR p.description LIKE ?)
                    ORDER BY p.created_at DESC
                    LIMIT ?
                """
                values = (user_id, search_term, search_term, limit)
            else:
                sql_query = """
                    SELECT p.*
                    FROM projects p
                    WHERE p.name LIKE ? OR p.description LIKE ?
                    ORDER BY p.created_at DESC
                    LIMIT ?
                """
                values = (search_term, search_term, limit)

            return self.execute_query(sql_query, values, fetch='all')

        except Exception as e:
            logger.error(f"Errore ricerca progetti: {e}")
            return []

    def get_project_activity_summary(self, project_id: str, days: int = 7) -> Dict[str, Any]:
        """
        Riassunto attività progetto negli ultimi giorni.

        Args:
            project_id: ID progetto
            days: Giorni da considerare

        Returns:
            Dizionario riassunto attività
        """
        try:
            from datetime import timedelta

            cutoff_date = datetime.now() - timedelta(days=days)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Attività documenti
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM papers
                    WHERE project_id = ? AND processed_at > ?
                """, (project_id, cutoff_date.isoformat()))
                documents_activity = cursor.fetchone()['count']

                # Attività chat
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM chat_sessions cs
                    JOIN chat_messages cm ON cs.id = cm.session_id
                    WHERE cs.project_id = ? AND cm.timestamp > ?
                """, (project_id, cutoff_date.isoformat()))
                chat_activity = cursor.fetchone()['count']

                # Attività accademica
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM tasks
                    WHERE project_id = ? AND updated_at > ?
                """, (project_id, cutoff_date.isoformat()))
                academic_activity = cursor.fetchone()['count']

                return {
                    'project_id': project_id,
                    'period_days': days,
                    'documents_activity': documents_activity,
                    'chat_activity': chat_activity,
                    'academic_activity': academic_activity,
                    'total_activity': documents_activity + chat_activity + academic_activity
                }

        except Exception as e:
            logger.error(f"Errore riassunto attività progetto {project_id}: {e}")
            return {}

    def clone_project(self, source_project_id: str, new_project_id: str, user_id: int, new_name: str) -> bool:
        """
        Clona progetto esistente.

        Args:
            source_project_id: ID progetto sorgente
            new_project_id: ID nuovo progetto
            user_id: ID utente che esegue clonazione
            new_name: Nome nuovo progetto

        Returns:
            True se clonato con successo
        """
        try:
            # Verifica progetto sorgente esiste e utente ha accesso
            source_project = self.find_by_id(source_project_id)
            if not source_project:
                raise DatabaseOperationError(f"Progetto sorgente non trovato: {source_project_id}")

            user_role = self.get_user_role_in_project(user_id, source_project_id)
            if not user_role or user_role not in ['owner', 'admin']:
                raise DatabaseOperationError("Permessi insufficienti per clonare progetto")

            # Crea nuovo progetto
            self.create_project(new_project_id, user_id, new_name, f"Clone di {source_project['name']}")

            # Qui potresti implementare clonazione dati specifici
            # Per ora creiamo solo struttura vuota

            logger.info(f"Progetto clonato: {source_project_id} -> {new_project_id}")
            return True

        except Exception as e:
            logger.error(f"Errore clonazione progetto: {e}")
            raise DatabaseOperationError(f"Errore clonazione progetto: {e}")

    def get_project_list_for_dropdown(self, user_id: int) -> List[Dict]:
        """
        Restituisce lista progetti formattata per dropdown UI.

        Args:
            user_id: ID utente

        Returns:
            Lista progetti per UI
        """
        try:
            projects = self.get_projects_for_user(user_id)

            formatted_projects = []
            for project in projects:
                formatted_projects.append({
                    'id': project['id'],
                    'name': project['name'],
                    'description': project.get('description', ''),
                    'is_default': project.get('is_default', 0) == 1,
                    'role': project.get('role', 'member'),
                    'stats': self.get_project_stats(project['id'])
                })

            return formatted_projects

        except Exception as e:
            logger.error(f"Errore lista progetti dropdown: {e}")
            return []
