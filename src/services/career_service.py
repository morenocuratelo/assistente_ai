"""
Career Service.

Service layer per gestione carriera accademica con business logic
e integrazione con repository pattern.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta

from .base_service import BaseService
from ..database.repositories.base_repository import BaseRepository
from ..database.models.base import DatabaseResponse

logger = logging.getLogger(__name__)


class CareerService(BaseService):
    """Service per gestione carriera accademica."""

    def __init__(self, repository: BaseRepository):
        """Inizializza CareerService.

        Args:
            repository: Repository per accesso dati carriera
        """
        super().__init__(repository)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def get_by_id(self, course_id: Any) -> DatabaseResponse:
        """Recupera corso per ID."""
        try:
            course = self.repository.find_by_id(course_id)
            if course:
                return self._create_response(True, "Corso recuperato", course)
            else:
                return self._create_response(False, f"Corso non trovato: {course_id}")
        except Exception as e:
            return self._handle_error(e, f"recupero corso {course_id}")

    def get_all(self, filters: Dict[str, Any] = None) -> DatabaseResponse:
        """Recupera tutti i corsi."""
        try:
            courses = self.repository.get_all(filters)
            return self._create_response(True, f"Recuperati {len(courses)} corsi", courses)
        except Exception as e:
            return self._handle_error(e, "recupero corsi")

    def create(self, data: Any) -> DatabaseResponse:
        """Crea nuovo corso."""
        try:
            # Validazione dati corso
            if not data.get('name') or not data['name'].strip():
                return self._create_response(False, "Nome corso obbligatorio")

            # Crea corso
            course = self.repository.create(data)
            if course:
                logger.info(f"Corso creato: {data.get('name')}")
                return self._create_response(True, "Corso creato", course)
            else:
                return self._create_response(False, "Errore creazione corso")
        except Exception as e:
            return self._handle_error(e, "creazione corso")

    def update(self, course_id: Any, data: Any) -> DatabaseResponse:
        """Aggiorna corso."""
        try:
            course = self.repository.update(course_id, data)
            if course:
                logger.info(f"Corso aggiornato: {course_id}")
                return self._create_response(True, "Corso aggiornato", course)
            else:
                return self._create_response(False, f"Errore aggiornamento corso: {course_id}")
        except Exception as e:
            return self._handle_error(e, f"aggiornamento corso {course_id}")

    def delete(self, course_id: Any) -> DatabaseResponse:
        """Elimina corso."""
        try:
            success = self.repository.delete(course_id)
            if success:
                logger.info(f"Corso eliminato: {course_id}")
                return self._create_response(True, "Corso eliminato")
            else:
                return self._create_response(False, f"Errore eliminazione corso: {course_id}")
        except Exception as e:
            return self._handle_error(e, f"eliminazione corso {course_id}")

    def get_courses_for_user(self, user_id: int) -> DatabaseResponse:
        """Recupera tutti i corsi per un utente."""
        try:
            filters = {'user_id': user_id}
            return self.get_all(filters)
        except Exception as e:
            return self._handle_error(e, f"recupero corsi utente {user_id}")

    def create_course(self, course_data: Dict[str, Any]) -> DatabaseResponse:
        """Crea corso con validazione."""
        try:
            # Validazione business
            validation_result = self._validate_course_data(course_data)
            if not validation_result['valid']:
                return self._create_response(False, "Validazione fallita", error=validation_result['errors'])

            # Crea corso
            course_data['created_at'] = datetime.now().isoformat()
            course_data['updated_at'] = datetime.now().isoformat()

            return self.create(course_data)

        except Exception as e:
            return self._handle_error(e, "creazione corso con validazione")

    def delete_course(self, course_id: Any) -> DatabaseResponse:
        """Elimina corso con cleanup."""
        try:
            # Verifica corso esiste
            course_result = self.get_by_id(course_id)
            if not course_result.success:
                return course_result

            # Elimina corso
            return self.delete(course_id)

        except Exception as e:
            return self._handle_error(e, f"eliminazione corso {course_id}")

    def _validate_course_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida dati corso."""
        errors = []

        # Validazione nome
        name = data.get('name', '').strip()
        if not name:
            errors.append("Nome corso obbligatorio")
        elif len(name) > 100:
            errors.append("Nome corso troppo lungo (max 100 caratteri)")

        # Validazione codice corso
        code = data.get('code', '')
        if code and len(code) > 20:
            errors.append("Codice corso troppo lungo (max 20 caratteri)")

        # Validazione descrizione
        description = data.get('description', '')
        if description and len(description) > 500:
            errors.append("Descrizione troppo lunga (max 500 caratteri)")

        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

    def get_course_lectures(self, course_id: Any) -> DatabaseResponse:
        """Recupera lezioni per un corso."""
        try:
            # Placeholder - in implementazione completa useresti query specifiche
            lectures = self.repository.get_course_lectures(course_id)
            return self._create_response(True, f"Lezioni recuperate: {len(lectures)}", lectures)
        except Exception as e:
            return self._handle_error(e, f"recupero lezioni corso {course_id}")

    def get_course_tasks(self, course_id: Any) -> DatabaseResponse:
        """Recupera attività per un corso."""
        try:
            # Placeholder - in implementazione completa useresti query specifiche
            tasks = self.repository.get_course_tasks(course_id)
            return self._create_response(True, f"Attività recuperate: {len(tasks)}", tasks)
        except Exception as e:
            return self._handle_error(e, f"recupero attività corso {course_id}")

    def get_course_stats(self, course_id: Any) -> DatabaseResponse:
        """Ottieni statistiche corso."""
        try:
            # Placeholder per statistiche corso
            stats = {
                'total_lectures': 0,
                'total_tasks': 0,
                'completed_tasks': 0,
                'total_materials': 0,
                'last_activity': None,
                'created_at': datetime.now().isoformat()
            }
            return self._create_response(True, "Statistiche corso recuperate", stats)
        except Exception as e:
            return self._handle_error(e, f"recupero statistiche corso {course_id}")

    def get_user_career_stats(self, user_id: int) -> DatabaseResponse:
        """Ottieni statistiche carriera utente."""
        try:
            # Recupera tutti i corsi utente
            courses_result = self.get_courses_for_user(user_id)
            if not courses_result.success:
                return courses_result

            courses = courses_result.data
            total_courses = len(courses)

            # Calcola statistiche aggregate
            total_lectures = 0
            total_tasks = 0
            completed_tasks = 0
            total_materials = 0

            for course in courses:
                course_id = course.get('id')

                # Statistiche corso
                stats_result = self.get_course_stats(course_id)
                if stats_result.success:
                    stats = stats_result.data
                    total_lectures += stats.get('total_lectures', 0)
                    total_tasks += stats.get('total_tasks', 0)
                    completed_tasks += stats.get('completed_tasks', 0)
                    total_materials += stats.get('total_materials', 0)

            career_stats = {
                'total_courses': total_courses,
                'total_lectures': total_lectures,
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'total_materials': total_materials,
                'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
                'last_updated': datetime.now().isoformat()
            }

            return self._create_response(True, "Statistiche carriera recuperate", career_stats)

        except Exception as e:
            return self._handle_error(e, f"recupero statistiche carriera utente {user_id}")

    def _generate_ai_tasks(self, document_text: str) -> Dict[str, Any]:
        """Genera task AI da testo documento."""
        try:
            # Analizza il contenuto per generare task rilevanti
            doc_lower = document_text.lower()

            # Determina tipo di task basandosi sul contenuto
            tasks = []

            # Task per contenuti accademici con teoremi
            if 'teorema' in doc_lower or 'theorem' in doc_lower:
                tasks.append({
                    'title': 'Ripasso teoremi fondamentali',
                    'description': 'Rivedere i teoremi principali del capitolo',
                    'priority': 'high',
                    'task_type': 'short_term'
                })

            # Task per contenuti con esercizi
            if 'eserciz' in doc_lower or 'exercise' in doc_lower:
                tasks.append({
                    'title': 'Esercizi pratici',
                    'description': 'Completare gli esercizi del capitolo',
                    'priority': 'medium',
                    'task_type': 'medium_term'
                })

            # Task generico se non trova pattern specifici
            if not tasks:
                tasks.append({
                    'title': 'Revisione documento',
                    'description': 'Rivedere il documento caricato',
                    'priority': 'medium',
                    'task_type': 'short_term'
                })

            return {
                'tasks': tasks,
                'summary': f'Task generati da AI: {len(tasks)}'
            }
        except Exception as e:
            self.logger.error(f"Errore generazione task AI: {e}")
            return {'tasks': [], 'summary': 'Errore generazione task'}

    def _validate_ai_tasks(self, ai_tasks: Dict[str, Any]) -> Dict[str, Any]:
        """Valida task AI generati."""
        try:
            errors = []

            if 'tasks' not in ai_tasks:
                errors.append("Campo 'tasks' mancante")
                return {'valid': False, 'errors': errors}

            tasks = ai_tasks['tasks']

            for i, task in enumerate(tasks):
                if not task.get('title'):
                    errors.append(f"Task {i}: titolo mancante")
                if not task.get('priority'):
                    errors.append(f"Task {i}: priorità mancante")

            return {
                'valid': len(errors) == 0,
                'errors': errors
            }
        except Exception as e:
            return {'valid': False, 'errors': [str(e)]}

    def _enrich_ai_tasks(self, ai_tasks: Dict[str, Any], user_id: str) -> List[Dict[str, Any]]:
        """Arricchisci task AI con metadati."""
        try:
            enriched_tasks = []

            for task in ai_tasks.get('tasks', []):
                enriched_task = {
                    **task,
                    'id': f"ai_task_{len(enriched_tasks) + 1}",
                    'user_id': user_id,
                    'status': 'pending',
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                enriched_tasks.append(enriched_task)

            return enriched_tasks
        except Exception as e:
            self.logger.error(f"Errore arricchimento task AI: {e}")
            return []

    def _map_task_priority(self, priority: str) -> str:
        """Mappa priorità task a valori standard."""
        priority_map = {
            'high': 'high',
            'medium': 'medium',
            'low': 'low',
            'urgent': 'high',
            'normal': 'medium'
        }
        return priority_map.get(priority.lower(), 'medium')

    def _map_task_type(self, task_type: str) -> str:
        """Mappa tipo task a valori standard."""
        type_map = {
            'short_term': 'short_term',
            'medium_term': 'medium_term',
            'long_term': 'long_term',
            'esame': 'long_term',
            'progetto': 'long_term'
        }
        return type_map.get(task_type.lower(), 'short_term')

    def _calculate_task_due_date(self, task_type: str, base_date: datetime = None) -> datetime:
        """Calcola data scadenza task basata sul tipo."""
        if base_date is None:
            base_date = datetime.now()

        if task_type == 'short_term':
            return base_date + timedelta(days=3)
        elif task_type == 'medium_term':
            return base_date + timedelta(days=14)
        else:  # long_term
            return base_date + timedelta(days=30)

    def _calculate_task_relevance(self, task: Dict[str, Any], document_text: str) -> float:
        """Calcola score rilevanza task rispetto al documento."""
        try:
            # Implementazione base - in produzione useresti algoritmi più sofisticati
            task_text = f"{task.get('title', '')} {task.get('description', '')}".lower()
            doc_text_lower = document_text.lower()

            # Conta parole chiave comuni
            keywords = ['studio', 'eserciz', 'ripass', 'teorem', 'capitol', 'lezione']
            matches = sum(1 for keyword in keywords if keyword in task_text and keyword in doc_text_lower)

            return min(matches / len(keywords), 1.0)
        except Exception:
            return 0.5  # Score neutro in caso di errore

    def _deduplicate_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rimuovi task duplicati."""
        try:
            seen = set()
            unique_tasks = []

            for task in tasks:
                task_key = f"{task.get('title', '')}_{task.get('description', '')}".lower()

                if task_key not in seen:
                    seen.add(task_key)
                    unique_tasks.append(task)

            return unique_tasks
        except Exception:
            return tasks

    def _optimize_task_priorities(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Ottimizza priorità task basata su contenuto."""
        try:
            optimized_tasks = []

            for task in tasks:
                optimized_task = task.copy()

                # Aumenta priorità per task accademici
                if any(keyword in task.get('description', '').lower()
                      for keyword in ['esame', 'urgente', 'importante', 'scadenza']):
                    optimized_task['priority'] = 'high'
                elif any(keyword in task.get('description', '').lower()
                        for keyword in ['progetto', 'tesi', 'ricerca']):
                    optimized_task['priority'] = 'medium'

                optimized_tasks.append(optimized_task)

            return optimized_tasks
        except Exception:
            return tasks

    # === METODI LEGACY DA FILE_UTILS.PY (MANTENUTI) ===

    def get_user_courses(self, user_id: int) -> List[Dict[str, Any]]:
        """Recupera tutti i corsi dell'utente (metodo legacy mantenuto)."""
        try:
            return self.repository.get_user_courses(user_id)
        except Exception as e:
            self.logger.error(f"Errore recupero corsi utente {user_id}: {e}")
            return []

    def create_course(self, user_id: int, course_name: str, course_code: str = None, description: str = None) -> int:
        """Crea un nuovo corso per l'utente (metodo legacy mantenuto)."""
        try:
            course_data = {
                'name': course_name,
                'code': course_code,
                'description': description,
                'user_id': user_id
            }

            result = self.create_course(course_data)
            if result.success:
                return result.data.get('id', 0)
            else:
                raise Exception(result.message)
        except Exception as e:
            self.logger.error(f"Errore creazione corso: {e}")
            return 0

    def update_course(self, course_id: int, course_name: str = None, course_code: str = None, description: str = None):
        """Aggiorna un corso (metodo legacy mantenuto)."""
        try:
            update_data = {}
            if course_name:
                update_data['name'] = course_name
            if course_code:
                update_data['code'] = course_code
            if description:
                update_data['description'] = description

            if update_data:
                result = self.update(course_id, update_data)
                return result.success
            return True
        except Exception as e:
            self.logger.error(f"Errore aggiornamento corso {course_id}: {e}")
            return False

    def delete_course(self, course_id: int):
        """Elimina un corso (metodo legacy mantenuto)."""
        try:
            result = self.delete_course(course_id)
            return result.success
        except Exception as e:
            self.logger.error(f"Errore eliminazione corso {course_id}: {e}")
            return False

    def get_course_lectures(self, course_id: int) -> List[Dict[str, Any]]:
        """Recupera tutte le lezioni di un corso (metodo legacy mantenuto)."""
        try:
            result = self.get_course_lectures(course_id)
            if result.success:
                return result.data
            return []
        except Exception as e:
            self.logger.error(f"Errore recupero lezioni corso {course_id}: {e}")
            return []

    def create_lecture(self, course_id: int, lecture_title: str, lecture_date: str = None, description: str = None) -> int:
        """Crea una nuova lezione per un corso (metodo legacy mantenuto)."""
        try:
            lecture_data = {
                'course_id': course_id,
                'title': lecture_title,
                'lecture_date': lecture_date,
                'description': description
            }

            result = self.repository.create_lecture(lecture_data)
            if result:
                return result.get('id', 0)
            return 0
        except Exception as e:
            self.logger.error(f"Errore creazione lezione: {e}")
            return 0

    def get_user_tasks(self, user_id: int) -> List[Dict[str, Any]]:
        """Recupera tutte le attività dell'utente (metodo legacy mantenuto)."""
        try:
            return self.repository.get_user_tasks(user_id)
        except Exception as e:
            self.logger.error(f"Errore recupero attività utente {user_id}: {e}")
            return []

    def create_task(self, user_id: int, course_id: int = None, lecture_id: int = None,
                   task_title: str = None, task_description: str = None,
                   priority: str = 'medium', task_type: str = 'medium_term',
                   due_date: str = None, status: str = 'pending') -> int:
        """Crea una nuova attività (metodo legacy mantenuto)."""
        try:
            task_data = {
                'user_id': user_id,
                'course_id': course_id,
                'lecture_id': lecture_id,
                'title': task_title,
                'description': task_description,
                'priority': priority,
                'task_type': task_type,
                'due_date': due_date,
                'status': status
            }

            result = self.repository.create_task(task_data)
            if result:
                return result.get('id', 0)
            return 0
        except Exception as e:
            self.logger.error(f"Errore creazione attività: {e}")
            return 0

    def update_task(self, task_id: int, **kwargs):
        """Aggiorna un'attività (metodo legacy mantenuto)."""
        try:
            result = self.repository.update_task(task_id, kwargs)
            return result
        except Exception as e:
            self.logger.error(f"Errore aggiornamento attività {task_id}: {e}")
            return False

    def delete_task(self, task_id: int):
        """Elimina un'attività (metodo legacy mantenuto)."""
        try:
            result = self.repository.delete_task(task_id)
            return result
        except Exception as e:
            self.logger.error(f"Errore eliminazione attività {task_id}: {e}")
            return False


def create_career_service(db_path: str = "db_memoria/metadata.sqlite") -> CareerService:
    """Factory function per creare CareerService."""
    from ..database.repositories.career_repository import CareerRepository
    return CareerService(CareerRepository(db_path))
