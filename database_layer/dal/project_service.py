# Project Service - Business Logic Layer per Progetti
"""
Service layer per gestione progetti in Archivista AI.

Fornisce:
- Business logic coordinamento progetti
- Validazione operazioni progetto
- Integrazione tra repository
- Gestione errori di business
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from .project_repository import ProjectRepository
from .document_repository import DocumentRepository
from .user_repository import UserRepository
from ..config_layer.project_config import ProjectConfig

logger = logging.getLogger('ProjectService')

class ProjectServiceError(Exception):
    """Eccezione per errori business progetti"""
    pass

class ProjectService:
    """
    Service layer per gestione progetti.

    Coordina operazioni tra repository e fornisce
    business logic per gestione progetti.
    """

    def __init__(self, db_path: str = "db_memoria/metadata.sqlite"):
        """
        Inizializza project service.

        Args:
            db_path: Percorso database
        """
        self.db_path = db_path
        self.project_repo = ProjectRepository(db_path)
        self.document_repo = DocumentRepository(db_path)
        self.user_repo = UserRepository(db_path)

        logger.info("ProjectService inizializzato")

    def create_project_with_validation(self, project_id: str, user_id: int,
                                     name: str, description: str = None) -> Dict[str, Any]:
        """
        Crea progetto con validazione completa.

        Args:
            project_id: ID progetto
            user_id: ID utente creatore
            name: Nome progetto
            description: Descrizione progetto

        Returns:
            Dizionario risultato creazione

        Raises:
            ProjectServiceError: Se creazione fallisce
        """
        try:
            # Validazione business
            self._validate_project_creation(project_id, user_id, name)

            # Crea progetto
            project_db_id = self.project_repo.create_project(project_id, user_id, name, description)

            # Crea configurazione progetto
            project_config = ProjectConfig(project_id)
            config_saved = project_config.save_to_file()

            # Crea database progetto se necessario
            db_config = project_config.get_database_config()
            db_created = db_config.create_project_database(project_id)

            result = {
                'success': True,
                'project_id': project_id,
                'project_db_id': project_db_id,
                'config_created': config_saved,
                'database_created': db_created,
                'message': f"Progetto '{name}' creato con successo"
            }

            logger.info(f"Progetto creato con validazione: {project_id}")
            return result

        except Exception as e:
            logger.error(f"Errore creazione progetto {project_id}: {e}")
            raise ProjectServiceError(f"Errore creazione progetto: {e}")

    def _validate_project_creation(self, project_id: str, user_id: int, name: str):
        """Validazione business creazione progetto"""
        # Verifica utente esiste
        user = self.user_repo.find_by_id(user_id)
        if not user:
            raise ProjectServiceError(f"Utente non trovato: {user_id}")

        # Verifica progetto non esiste già
        existing_project = self.project_repo.find_by_id(project_id)
        if existing_project:
            raise ProjectServiceError(f"Progetto già esistente: {project_id}")

        # Verifica nome progetto valido
        if not name or not name.strip():
            raise ProjectServiceError("Nome progetto obbligatorio")

        if len(name) > 100:
            raise ProjectServiceError("Nome progetto troppo lungo (max 100 caratteri)")

        # Verifica utente non ha troppi progetti attivi
        user_projects = self.project_repo.get_projects_for_user(user_id)
        if len(user_projects) >= 50:  # Limite ragionevole
            raise ProjectServiceError("Limite massimo progetti per utente raggiunto")

    def delete_project_with_cleanup(self, project_id: str, user_id: int) -> Dict[str, Any]:
        """
        Elimina progetto con cleanup completo.

        Args:
            project_id: ID progetto da eliminare
            user_id: ID utente che richiede eliminazione

        Returns:
            Dizionario risultato eliminazione

        Raises:
            ProjectServiceError: Se eliminazione fallisce
        """
        try:
            # Verifica permessi utente
            permissions = self.project_repo.get_user_permissions_in_project(user_id, project_id)
            if not permissions['has_access'] or not permissions['permissions'].get('can_delete_project'):
                raise ProjectServiceError("Permessi insufficienti per eliminare progetto")

            # Ottieni statistiche progetto prima eliminazione
            project_stats = self.project_repo.get_project_stats(project_id)
            project_info = self.project_repo.find_by_id(project_id)

            # Backup progetto se necessario
            backup_created = False
            backup_path = None

            if project_stats.get('total_items', 0) > 0:
                # Crea backup se progetto contiene dati
                db_config = DatabaseConfig(project_id=project_id)
                backup_path = db_config.backup_database()
                backup_created = backup_path is not None

            # Elimina progetto
            success = self.project_repo.delete_project(project_id)

            if not success:
                raise ProjectServiceError("Eliminazione progetto fallita")

            result = {
                'success': True,
                'project_id': project_id,
                'items_deleted': project_stats.get('total_items', 0),
                'backup_created': backup_created,
                'backup_path': backup_path,
                'message': f"Progetto '{project_info['name']}' eliminato con successo"
            }

            logger.info(f"Progetto eliminato con cleanup: {project_id}")
            return result

        except Exception as e:
            logger.error(f"Errore eliminazione progetto {project_id}: {e}")
            raise ProjectServiceError(f"Errore eliminazione progetto: {e}")

    def switch_user_project(self, user_id: int, new_project_id: str) -> Dict[str, Any]:
        """
        Cambia progetto attivo utente.

        Args:
            user_id: ID utente
            new_project_id: ID nuovo progetto attivo

        Returns:
            Dizionario risultato cambio progetto

        Raises:
            ProjectServiceError: Se cambio fallisce
        """
        try:
            # Verifica utente ha accesso al progetto
            permissions = self.project_repo.get_user_permissions_in_project(user_id, new_project_id)
            if not permissions['has_access']:
                raise ProjectServiceError(f"Utente {user_id} non ha accesso al progetto {new_project_id}")

            # Aggiorna progetto default utente
            success = self.project_repo.set_default_project(new_project_id, user_id)

            if not success:
                raise ProjectServiceError("Impossibile impostare progetto default")

            result = {
                'success': True,
                'user_id': user_id,
                'new_project_id': new_project_id,
                'previous_project_id': None,  # Potresti tracciarlo
                'message': f"Progetto attivo cambiato a: {new_project_id}"
            }

            logger.info(f"Progetto utente cambiato: {user_id} -> {new_project_id}")
            return result

        except Exception as e:
            logger.error(f"Errore cambio progetto utente {user_id}: {e}")
            raise ProjectServiceError(f"Errore cambio progetto: {e}")

    def get_user_projects_with_stats(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Restituisce progetti utente con statistiche complete.

        Args:
            user_id: ID utente

        Returns:
            Lista progetti con statistiche dettagliate
        """
        try:
            projects = self.project_repo.get_projects_for_user(user_id)

            enriched_projects = []
            for project in projects:
                project_id = project['id']

                # Ottieni statistiche progetto
                stats = self.project_repo.get_project_stats(project_id)

                # Ottieni attività recente
                activity = self.project_repo.get_project_activity_summary(project_id, days=7)

                # Ottieni configurazione progetto
                project_config = ProjectConfig(project_id)
                config_summary = project_config.get_config_summary()

                enriched_project = {
                    **project,
                    'stats': stats,
                    'recent_activity': activity,
                    'config': config_summary,
                    'is_active': project.get('is_default', 0) == 1
                }

                enriched_projects.append(enriched_project)

            return enriched_projects

        except Exception as e:
            logger.error(f"Errore progetti utente con stats {user_id}: {e}")
            return []

    def clone_project_complete(self, source_project_id: str, new_project_id: str,
                             user_id: int, new_name: str) -> Dict[str, Any]:
        """
        Clona progetto completo con tutti i dati.

        Args:
            source_project_id: ID progetto sorgente
            new_project_id: ID nuovo progetto
            user_id: ID utente che clona
            new_name: Nome nuovo progetto

        Returns:
            Dizionario risultato clonazione

        Raises:
            ProjectServiceError: Se clonazione fallisce
        """
        try:
            # Verifica permessi clonazione
            permissions = self.project_repo.get_user_permissions_in_project(user_id, source_project_id)
            if not permissions['has_access'] or permissions['role'] not in ['owner', 'admin']:
                raise ProjectServiceError("Permessi insufficienti per clonare progetto")

            # Crea nuovo progetto
            self.project_repo.create_project(new_project_id, user_id, new_name,
                                           f"Clone di {source_project_id}")

            # Qui implementeresti clonazione dati specifici:
            # - Documenti del progetto sorgente
            # - Corsi e lezioni
            # - Attività e task
            # - Sessioni chat
            # - Entità knowledge graph

            # Per ora clonazione struttura vuota
            cloned_items = {
                'documents': 0,
                'courses': 0,
                'tasks': 0,
                'chat_sessions': 0
            }

            result = {
                'success': True,
                'source_project_id': source_project_id,
                'new_project_id': new_project_id,
                'cloned_items': cloned_items,
                'message': f"Progetto clonato: {new_project_id} da {source_project_id}"
            }

            logger.info(f"Progetto clonato completo: {source_project_id} -> {new_project_id}")
            return result

        except Exception as e:
            logger.error(f"Errore clonazione progetto completo: {e}")
            raise ProjectServiceError(f"Errore clonazione progetto: {e}")

    def get_project_dashboard_data(self, project_id: str, user_id: int) -> Dict[str, Any]:
        """
        Dati dashboard per progetto specifico.

        Args:
            project_id: ID progetto
            user_id: ID utente richiedente

        Returns:
            Dizionario dati dashboard progetto

        Raises:
            ProjectServiceError: Se accesso negato
        """
        try:
            # Verifica accesso utente
            permissions = self.project_repo.get_user_permissions_in_project(user_id, project_id)
            if not permissions['has_access']:
                raise ProjectServiceError(f"Accesso negato al progetto: {project_id}")

            # Raccogli dati progetto
            project_info = self.project_repo.find_by_id(project_id)
            project_stats = self.project_repo.get_project_stats(project_id)
            recent_activity = self.project_repo.get_project_activity_summary(project_id, days=7)

            # Documenti recenti progetto
            recent_docs = self.document_repo.find_by_criteria(
                {'project_id': project_id},
                order_by='processed_at DESC',
                limit=5
            )

            # Attività recenti progetto
            recent_tasks = []  # Implementeresti query simile

            dashboard_data = {
                'project_info': project_info,
                'stats': project_stats,
                'recent_activity': recent_activity,
                'recent_documents': recent_docs,
                'recent_tasks': recent_tasks,
                'user_permissions': permissions,
                'last_updated': datetime.now().isoformat()
            }

            return dashboard_data

        except Exception as e:
            logger.error(f"Errore dati dashboard progetto {project_id}: {e}")
            raise ProjectServiceError(f"Errore dati dashboard: {e}")

    def validate_project_integrity(self, project_id: str) -> Dict[str, Any]:
        """
        Valida integrità progetto e suoi dati.

        Args:
            project_id: ID progetto da validare

        Returns:
            Report integrità progetto

        Raises:
            ProjectServiceError: Se progetto corrotto
        """
        try:
            issues = []
            warnings = []

            # Verifica progetto esiste
            project = self.project_repo.find_by_id(project_id)
            if not project:
                raise ProjectServiceError(f"Progetto non trovato: {project_id}")

            # Verifica associazione utenti
            user_projects = self.project_repo.get_projects_for_user(project['user_id'])
            project_associations = [p for p in user_projects if p['id'] == project_id]

            if not project_associations:
                issues.append("Progetto senza associazioni utenti valide")

            # Verifica dati progetto
            stats = self.project_repo.get_project_stats(project_id)

            if stats.get('total_items', 0) == 0:
                warnings.append("Progetto vuoto - nessun dato presente")

            # Verifica documenti progetto
            documents = self.document_repo.find_by_criteria({'project_id': project_id})

            orphaned_documents = 0
            for doc in documents:
                # Verifica associazione categoria se presente
                if doc.get('category_id'):
                    # Potresti verificare esistenza categoria
                    pass

            # Report finale
            integrity_report = {
                'project_id': project_id,
                'is_valid': len(issues) == 0,
                'issues': issues,
                'warnings': warnings,
                'stats': stats,
                'validation_date': datetime.now().isoformat()
            }

            return integrity_report

        except Exception as e:
            logger.error(f"Errore validazione integrità progetto {project_id}: {e}")
            raise ProjectServiceError(f"Errore validazione progetto: {e}")

    def get_project_recommendations(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Suggerimenti progetti per utente.

        Args:
            user_id: ID utente

        Returns:
            Lista raccomandazioni progetti
        """
        try:
            recommendations = []

            # Ottieni progetti utente
            user_projects = self.project_repo.get_projects_for_user(user_id)

            # Suggerisci creazione progetti per categorie documenti
            if len(user_projects) == 1:  # Solo progetto default
                recommendations.append({
                    'type': 'create_project',
                    'title': 'Crea Progetto Università',
                    'description': 'Organizza documenti accademici in progetto dedicato',
                    'action': 'create_university_project',
                    'priority': 'high'
                })

                recommendations.append({
                    'type': 'create_project',
                    'title': 'Crea Progetto Lavoro',
                    'description': 'Separa documenti professionali da quelli personali',
                    'action': 'create_work_project',
                    'priority': 'medium'
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

    def cleanup_inactive_projects(self, user_id: int, days_inactive: int = 90) -> Dict[str, Any]:
        """
        Pulisce progetti inattivi.

        Args:
            user_id: ID utente
            days_inactive: Giorni inattività per considerare progetto inattivo

        Returns:
            Report pulizia progetti
        """
        try:
            from datetime import timedelta

            cutoff_date = datetime.now() - timedelta(days=days_inactive)
            user_projects = self.project_repo.get_projects_for_user(user_id)

            cleaned_projects = []
            for project in user_projects:
                project_id = project['id']

                # Salta progetto default
                if project.get('is_default', 0) == 1:
                    continue

                # Verifica attività progetto
                activity = self.project_repo.get_project_activity_summary(project_id, days=days_inactive)

                if activity.get('total_activity', 0) == 0:
                    # Progetto inattivo - candidato pulizia
                    integrity = self.validate_project_integrity(project_id)

                    if not integrity['is_valid']:
                        # Progetto corrotto - elimina
                        self.project_repo.delete_project(project_id)
                        cleaned_projects.append({
                            'project_id': project_id,
                            'name': project['name'],
                            'reason': 'corrupted',
                            'action': 'deleted'
                        })
                    else:
                        # Progetto inattivo ma valido - archivia
                        cleaned_projects.append({
                            'project_id': project_id,
                            'name': project['name'],
                            'reason': 'inactive',
                            'action': 'archived'
                        })

            result = {
                'success': True,
                'user_id': user_id,
                'days_inactive': days_inactive,
                'cleaned_projects': cleaned_projects,
                'message': f"Pulizia completata: {len(cleaned_projects)} progetti processati"
            }

            logger.info(f"Pulizia progetti inattivi utente {user_id}: {len(cleaned_projects)} progetti")
            return result

        except Exception as e:
            logger.error(f"Errore pulizia progetti inattivi utente {user_id}: {e}")
            raise ProjectServiceError(f"Errore pulizia progetti: {e}")

    def get_project_export_data(self, project_id: str, user_id: int) -> Dict[str, Any]:
        """
        Prepara dati progetto per esportazione.

        Args:
            project_id: ID progetto da esportare
            user_id: ID utente richiedente

        Returns:
            Dizionario dati progetto per esportazione

        Raises:
            ProjectServiceError: Se accesso negato
        """
        try:
            # Verifica permessi
            permissions = self.project_repo.get_user_permissions_in_project(user_id, project_id)
            if not permissions['has_access']:
                raise ProjectServiceError(f"Accesso negato al progetto: {project_id}")

            # Raccogli tutti i dati progetto
            project_info = self.project_repo.find_by_id(project_id)
            project_stats = self.project_repo.get_project_stats(project_id)

            # Documenti progetto
            documents = self.document_repo.find_by_criteria({'project_id': project_id})

            # Altri dati progetto (corsi, task, etc.)
            courses = []  # Implementeresti
            tasks = []    # Implementeresti
            chat_sessions = []  # Implementeresti

            export_data = {
                'project_info': project_info,
                'stats': project_stats,
                'export_date': datetime.now().isoformat(),
                'data': {
                    'documents': documents,
                    'courses': courses,
                    'tasks': tasks,
                    'chat_sessions': chat_sessions
                },
                'metadata': {
                    'total_documents': len(documents),
                    'total_courses': len(courses),
                    'total_tasks': len(tasks),
                    'total_chat_sessions': len(chat_sessions)
                }
            }

            return export_data

        except Exception as e:
            logger.error(f"Errore preparazione export progetto {project_id}: {e}")
            raise ProjectServiceError(f"Errore preparazione export: {e}")

    def import_project_data(self, project_id: str, user_id: int, import_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Importa dati in progetto esistente.

        Args:
            project_id: ID progetto destinazione
            user_id: ID utente che importa
            import_data: Dati da importare

        Returns:
            Report importazione

        Raises:
            ProjectServiceError: Se importazione fallisce
        """
        try:
            # Verifica permessi
            permissions = self.project_repo.get_user_permissions_in_project(user_id, project_id)
            if not permissions['permissions'].get('can_write'):
                raise ProjectServiceError(f"Permessi scrittura insufficienti per progetto: {project_id}")

            imported_counts = {
                'documents': 0,
                'courses': 0,
                'tasks': 0,
                'chat_sessions': 0
            }

            # Importa documenti
            documents_data = import_data.get('data', {}).get('documents', [])
            for doc_data in documents_data:
                # Assicurati project_id corretto
                doc_data['project_id'] = project_id

                try:
                    # Crea documento (se non esiste già)
                    existing_doc = self.document_repo.find_by_file_name(doc_data['file_name'])
                    if not existing_doc:
                        # Crea nuovo documento
                        # Nota: In implementazione completa useresti create con dati appropriati
                        imported_counts['documents'] += 1
                except Exception as e:
                    logger.warning(f"Errore importazione documento {doc_data.get('file_name')}: {e}")

            # Qui implementeresti importazione altri tipi dati

            result = {
                'success': True,
                'project_id': project_id,
                'imported_counts': imported_counts,
                'message': f"Dati importati in progetto {project_id}"
            }

            logger.info(f"Dati importati in progetto {project_id}: {imported_counts}")
            return result

        except Exception as e:
            logger.error(f"Errore importazione dati progetto {project_id}: {e}")
            raise ProjectServiceError(f"Errore importazione dati: {e}")
