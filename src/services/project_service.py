"""
Project Service.

Service layer per gestione progetti con business logic
e integrazione con repository pattern.
Mantiene e integra la logica esistente dal database_layer.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base_service import BaseService
from ..database.repositories.base_repository import BaseRepository
from ..database.models.base import DatabaseResponse

logger = logging.getLogger(__name__)


class ProjectServiceError(Exception):
    """Eccezione per errori business progetti"""
    pass


class ProjectService(BaseService):
    """Service per gestione progetti."""

    def __init__(self, repository: BaseRepository):
        """Inizializza ProjectService.

        Args:
            repository: Repository per accesso dati progetti
        """
        super().__init__(repository)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def get_by_id(self, project_id: Any) -> DatabaseResponse:
        """Recupera progetto per ID."""
        try:
            project = self.repository.find_by_id(project_id)
            if project:
                return self._create_response(True, "Progetto recuperato", project)
            else:
                return self._create_response(False, f"Progetto non trovato: {project_id}")
        except Exception as e:
            return self._handle_error(e, f"recupero progetto {project_id}")

    def get_all(self, filters: Dict[str, Any] = None) -> DatabaseResponse:
        """Recupera tutti i progetti."""
        try:
            projects = self.repository.get_all(filters)
            return self._create_response(True, f"Recuperati {len(projects)} progetti", projects)
        except Exception as e:
            return self._handle_error(e, "recupero progetti")

    def create(self, data: Any) -> DatabaseResponse:
        """Crea nuovo progetto."""
        try:
            # Validazione dati progetto
            if not data.get('name') or not data['name'].strip():
                return self._create_response(False, "Nome progetto obbligatorio")

            # Crea progetto
            project = self.repository.create(data)
            if project:
                logger.info(f"Progetto creato: {data.get('name')}")
                return self._create_response(True, "Progetto creato", project)
            else:
                return self._create_response(False, "Errore creazione progetto")
        except Exception as e:
            return self._handle_error(e, "creazione progetto")

    def update(self, project_id: Any, data: Any) -> DatabaseResponse:
        """Aggiorna progetto."""
        try:
            project = self.repository.update(project_id, data)
            if project:
                logger.info(f"Progetto aggiornato: {project_id}")
                return self._create_response(True, "Progetto aggiornato", project)
            else:
                return self._create_response(False, f"Errore aggiornamento progetto: {project_id}")
        except Exception as e:
            return self._handle_error(e, f"aggiornamento progetto {project_id}")

    def delete(self, project_id: Any) -> DatabaseResponse:
        """Elimina progetto."""
        try:
            success = self.repository.delete(project_id)
            if success:
                logger.info(f"Progetto eliminato: {project_id}")
                return self._create_response(True, "Progetto eliminato")
            else:
                return self._create_response(False, f"Errore eliminazione progetto: {project_id}")
        except Exception as e:
            return self._handle_error(e, f"eliminazione progetto {project_id}")

    def get_all_projects(self) -> DatabaseResponse:
        """Recupera tutti i progetti con statistiche."""
        try:
            projects = self.repository.get_all()

            # Arricchisci con statistiche
            enriched_projects = []
            for project in projects:
                project_id = project.get('id')

                # Ottieni statistiche progetto
                stats = self._get_project_stats(project_id)

                enriched_project = {
                    **project,
                    'stats': stats,
                    'document_count': stats.get('total_documents', 0),
                    'last_activity': stats.get('last_activity', None)
                }

                enriched_projects.append(enriched_project)

            return self._create_response(True, f"Progetti recuperati: {len(enriched_projects)}", enriched_projects)

        except Exception as e:
            return self._handle_error(e, "recupero progetti con statistiche")

    def create_project(self, project_data: Dict[str, Any]) -> DatabaseResponse:
        """Crea progetto con validazione."""
        try:
            # Validazione business
            validation_result = self._validate_project_data(project_data)
            if not validation_result['valid']:
                return self._create_response(False, "Validazione fallita", error=validation_result['errors'])

            # Crea progetto
            project_data['created_at'] = datetime.now().isoformat()
            project_data['updated_at'] = datetime.now().isoformat()

            return self.create(project_data)

        except Exception as e:
            return self._handle_error(e, "creazione progetto con validazione")

    def delete_project(self, project_id: Any) -> DatabaseResponse:
        """Elimina progetto con cleanup."""
        try:
            # Verifica progetto esiste
            project_result = self.get_by_id(project_id)
            if not project_result.success:
                return project_result

            # Elimina progetto
            return self.delete(project_id)

        except Exception as e:
            return self._handle_error(e, f"eliminazione progetto {project_id}")

    def _validate_project_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida dati progetto."""
        errors = []

        # Validazione nome
        name = data.get('name', '').strip()
        if not name:
            errors.append("Nome progetto obbligatorio")
        elif len(name) > 100:
            errors.append("Nome progetto troppo lungo (max 100 caratteri)")

        # Validazione tipo
        project_type = data.get('type', '')
        valid_types = ['Ricerca', 'Studio', 'Personale', 'Lavoro']
        if project_type and project_type not in valid_types:
            errors.append(f"Tipo progetto non valido. Usa: {', '.join(valid_types)}")

        # Validazione descrizione
        description = data.get('description', '')
        if description and len(description) > 500:
            errors.append("Descrizione troppo lunga (max 500 caratteri)")

        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

    def _get_project_stats(self, project_id: Any) -> Dict[str, Any]:
        """Ottieni statistiche progetto."""
        try:
            # Placeholder per statistiche progetto
            # In implementazione completa, useresti query specifiche
            return {
                'total_documents': 0,
                'total_tasks': 0,
                'total_courses': 0,
                'last_activity': None,
                'created_at': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Errore statistiche progetto {project_id}: {e}")
            return {}

    def get_projects_by_type(self, project_type: str) -> DatabaseResponse:
        """Recupera progetti per tipo."""
        try:
            filters = {'type': project_type}
            return self.get_all(filters)
        except Exception as e:
            return self._handle_error(e, f"recupero progetti tipo {project_type}")

    def search_projects(self, query: str) -> DatabaseResponse:
        """Cerca progetti per nome o descrizione."""
        try:
            # Implementazione base - in produzione useresti query full-text
            projects = self.repository.get_all()
            filtered_projects = [
                p for p in projects
                if query.lower() in p.get('name', '').lower() or
                   query.lower() in p.get('description', '').lower()
            ]

            return self._create_response(True, f"Trovati {len(filtered_projects)} progetti", filtered_projects)

        except Exception as e:
            return self._handle_error(e, f"ricerca progetti '{query}'")

    # === METODI AVANZATI DAL DATABASE_LAYER (MANTENUTI) ===

    def create_project_with_validation(self, project_id: str, user_id: int,
                                     name: str, description: str = None) -> Dict[str, Any]:
        """
        Crea progetto con validazione completa (metodo legacy mantenuto).

        Args:
            project_id: ID progetto
            user_id: ID utente creatore
            name: Nome progetto
            description: Descrizione progetto

        Returns:
            Dizionario risultato creazione
        """
        try:
            # Validazione business
            self._validate_project_creation(project_id, user_id, name)

            # Crea progetto usando il repository
            project_data = {
                'name': name,
                'description': description,
                'user_id': user_id
            }

            result = self.create_project(project_data)
            if result.success:
                return {
                    'success': True,
                    'project_id': project_id,
                    'project_db_id': result.data.get('id'),
                    'message': f"Progetto '{name}' creato con successo"
                }
            else:
                raise ProjectServiceError(result.message)

        except Exception as e:
            logger.error(f"Errore creazione progetto {project_id}: {e}")
            raise ProjectServiceError(f"Errore creazione progetto: {e}")

    def _validate_project_creation(self, project_id: str, user_id: int, name: str):
        """Validazione business creazione progetto (legacy)."""
        # Verifica nome progetto valido
        if not name or not name.strip():
            raise ProjectServiceError("Nome progetto obbligatorio")

        if len(name) > 100:
            raise ProjectServiceError("Nome progetto troppo lungo (max 100 caratteri)")

    def delete_project_with_cleanup(self, project_id: str, user_id: int) -> Dict[str, Any]:
        """
        Elimina progetto con cleanup completo (metodo legacy mantenuto).

        Args:
            project_id: ID progetto da eliminare
            user_id: ID utente che richiede eliminazione

        Returns:
            Dizionario risultato eliminazione
        """
        try:
            # Ottieni statistiche progetto prima eliminazione
            project_stats = self._get_project_stats(project_id)
            project_info = self.get_by_id(project_id)

            if not project_info.success:
                raise ProjectServiceError(f"Progetto non trovato: {project_id}")

            # Elimina progetto
            delete_result = self.delete_project(project_id)
            if not delete_result.success:
                raise ProjectServiceError("Eliminazione progetto fallita")

            return {
                'success': True,
                'project_id': project_id,
                'items_deleted': project_stats.get('total_items', 0),
                'message': f"Progetto '{project_info.data.get('name')}' eliminato con successo"
            }

        except Exception as e:
            logger.error(f"Errore eliminazione progetto {project_id}: {e}")
            raise ProjectServiceError(f"Errore eliminazione progetto: {e}")

    def switch_user_project(self, user_id: int, new_project_id: str) -> Dict[str, Any]:
        """
        Cambia progetto attivo utente (metodo legacy mantenuto).

        Args:
            user_id: ID utente
            new_project_id: ID nuovo progetto attivo

        Returns:
            Dizionario risultato cambio progetto
        """
        try:
            # Verifica utente ha accesso al progetto
            permissions = self.repository.get_user_permissions_in_project(user_id, new_project_id)
            if not permissions['has_access']:
                raise ProjectServiceError(f"Utente {user_id} non ha accesso al progetto {new_project_id}")

            # Aggiorna progetto default utente
            success = self.repository.set_default_project(new_project_id, user_id)
            if not success:
                raise ProjectServiceError("Impossibile impostare progetto default")

            return {
                'success': True,
                'user_id': user_id,
                'new_project_id': new_project_id,
                'message': f"Progetto attivo cambiato a: {new_project_id}"
            }

        except Exception as e:
            logger.error(f"Errore cambio progetto utente {user_id}: {e}")
            raise ProjectServiceError(f"Errore cambio progetto: {e}")

    def get_user_projects_with_stats(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Restituisce progetti utente con statistiche complete (metodo legacy mantenuto).

        Args:
            user_id: ID utente

        Returns:
            Lista progetti con statistiche dettagliate
        """
        try:
            # Usa il repository per ottenere progetti utente
            projects = self.repository.get_projects_for_user(user_id)

            enriched_projects = []
            for project in projects:
                project_id = project.get('id')

                # Ottieni statistiche progetto
                stats = self._get_project_stats(project_id)

                # Ottieni attività recente
                activity = self.repository.get_project_activity_summary(project_id, days=7)

                enriched_project = {
                    **project,
                    'stats': stats,
                    'recent_activity': activity,
                    'is_active': project.get('is_default', 0) == 1
                }

                enriched_projects.append(enriched_project)

            return enriched_projects

        except Exception as e:
            logger.error(f"Errore progetti utente con stats {user_id}: {e}")
            return []

    def get_project_recommendations(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Suggerimenti progetti per utente (metodo legacy mantenuto).

        Args:
            user_id: ID utente

        Returns:
            Lista raccomandazioni progetti
        """
        try:
            recommendations = []

            # Ottieni progetti utente
            user_projects = self.repository.get_projects_for_user(user_id)

            # Suggerisci creazione progetti per categorie documenti
            if len(user_projects) == 1:  # Solo progetto default
                recommendations.append({
                    'type': 'create_project',
                    'title': 'Crea Progetto Università',
                    'description': 'Organizza documenti accademici in progetto dedicato',
                    'action': 'create_university_project',
                    'priority': 'high'
                })

            # Suggerisci ottimizzazioni progetti esistenti
            for project in user_projects:
                if project['id'] != 'wiki_globale':  # Salta progetto default
                    stats = project.get('stats', {})

                    if stats.get('total_items', 0) > 100:
                        recommendations.append({
                            'type': 'optimize_project',
                            'title': f'Ottimizza Progetto {project["name"]}',
                            'description': f'Progetto contiene {stats["total_items"]} elementi - considera riorganizzazione',
                            'action': 'optimize_project',
                            'project_id': project['id'],
                            'priority': 'low'
                        })

            return recommendations

        except Exception as e:
            logger.error(f"Errore raccomandazioni progetti utente {user_id}: {e}")
            return []


def create_project_service(db_path: str = "db_memoria/metadata.sqlite") -> ProjectService:
    """Factory function per creare ProjectService."""
    from ..database.repositories.project_repository import ProjectRepository
    return ProjectService(ProjectRepository(db_path))
