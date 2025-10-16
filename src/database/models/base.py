"""
Base models and common structures for the database layer.
Pydantic models for data validation and serialization.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator, root_validator
import uuid


class ProcessingStatus(str, Enum):
    """Status di processamento documenti."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    QUARANTINED = "quarantined"


class MaterialType(str, Enum):
    """Tipi di materiale didattico."""
    LECTURE_NOTES = "lecture_notes"
    HANDOUT = "handout"
    ASSIGNMENT = "assignment"
    READING = "reading"
    OTHER = "other"


class TaskPriority(str, Enum):
    """Priorità task."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskStatus(str, Enum):
    """Status task."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EntityType(str, Enum):
    """Tipi di entità conoscenza."""
    CONCEPT = "concept"
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    EVENT = "event"
    TERM = "term"


class RelationshipType(str, Enum):
    """Tipi di relazioni conoscenza."""
    RELATED_TO = "related_to"
    IS_A = "is_a"
    PART_OF = "part_of"
    CAUSES = "causes"
    REQUIRES = "requires"
    EXAMPLE_OF = "example_of"


class BaseEntity(BaseModel):
    """Entità base con campi comuni."""
    id: Optional[Union[int, str]] = Field(default=None, description="ID univoco entità")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Data creazione")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Data ultimo aggiornamento")

    class Config:
        """Configurazione Pydantic."""
        validate_assignment = True
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Project(BaseEntity):
    """Modello progetto."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="ID progetto")
    name: str = Field(..., min_length=1, max_length=255, description="Nome progetto")
    description: Optional[str] = Field(None, description="Descrizione progetto")
    owner_id: int = Field(..., description="ID proprietario progetto")
    is_default: bool = Field(default=False, description="Flag progetto default")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Impostazioni progetto")

    @validator('name')
    def validate_name(cls, v: str) -> str:
        """Valida nome progetto."""
        if not v.strip():
            raise ValueError("Nome progetto non può essere vuoto")
        return v.strip()


class User(BaseEntity):
    """Modello utente."""
    id: Optional[int] = Field(default=None, description="ID utente")
    username: str = Field(..., min_length=3, max_length=100, description="Nome utente")
    email: Optional[str] = Field(None, description="Email utente")
    password_hash: str = Field(..., description="Hash password")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="Preferenze utente")
    is_active: bool = Field(default=True, description="Flag utente attivo")
    is_new_user: bool = Field(default=True, description="Flag nuovo utente")

    @validator('username')
    def validate_username(cls, v: str) -> str:
        """Valida username."""
        if not v or len(v) < 3:
            raise ValueError("Username deve essere almeno 3 caratteri")
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Username può contenere solo lettere, numeri, _ e -")
        return v.lower()

    @validator('email')
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Valida email."""
        if v is None:
            return v
        if '@' not in v or '.' not in v:
            raise ValueError("Email non valida")
        return v.lower()


class Document(BaseEntity):
    """Modello documento."""
    id: Optional[int] = Field(default=None, description="ID documento")
    project_id: str = Field(..., description="ID progetto proprietario")
    file_name: str = Field(..., min_length=1, max_length=255, description="Nome file originale")
    title: Optional[str] = Field(None, max_length=500, description="Titolo documento")
    content_hash: Optional[str] = Field(None, max_length=64, description="Hash contenuto per deduplica")
    file_size: Optional[int] = Field(None, description="Dimensione file in byte")
    mime_type: Optional[str] = Field(None, max_length=100, description="Tipo MIME")
    processing_status: ProcessingStatus = Field(default=ProcessingStatus.PENDING, description="Status processamento")
    formatted_preview: Optional[str] = Field(None, description="Preview formattato AI")
    keywords: List[str] = Field(default_factory=list, description="Parole chiave estratte")
    ai_tasks: Dict[str, Any] = Field(default_factory=dict, description="Task AI associati")
    created_by: Optional[int] = Field(None, description="ID utente creatore")

    @validator('file_name')
    def validate_file_name(cls, v: str) -> str:
        """Valida nome file."""
        if not v or len(v) > 255:
            raise ValueError("Nome file non valido")
        # Controlli sicurezza
        dangerous_patterns = ['../', '..\\', '<script', 'javascript:']
        for pattern in dangerous_patterns:
            if pattern.lower() in v.lower():
                raise ValueError("Nome file contiene caratteri non sicuri")
        return v


class Category(BaseEntity):
    """Modello categoria documenti."""
    id: Optional[int] = Field(default=None, description="ID categoria")
    project_id: str = Field(..., description="ID progetto proprietario")
    name: str = Field(..., min_length=1, max_length=255, description="Nome categoria")
    parent_id: Optional[int] = Field(None, description="ID categoria padre")
    category_type: str = Field(default="standard", description="Tipo categoria")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadati categoria")

    @validator('name')
    def validate_name(cls, v: str) -> str:
        """Valida nome categoria."""
        if not v.strip():
            raise ValueError("Nome categoria non può essere vuoto")
        return v.strip()


class Course(BaseEntity):
    """Modello corso universitario."""
    id: Optional[int] = Field(default=None, description="ID corso")
    project_id: str = Field(..., description="ID progetto proprietario")
    user_id: int = Field(..., description="ID utente proprietario")
    course_name: str = Field(..., min_length=1, max_length=255, description="Nome corso")
    course_code: Optional[str] = Field(None, max_length=50, description="Codice corso")
    description: Optional[str] = Field(None, description="Descrizione corso")

    @validator('course_name')
    def validate_course_name(cls, v: str) -> str:
        """Valida nome corso."""
        if not v.strip():
            raise ValueError("Nome corso non può essere vuoto")
        return v.strip()


class Lecture(BaseEntity):
    """Modello lezione."""
    id: Optional[int] = Field(default=None, description="ID lezione")
    course_id: int = Field(..., description="ID corso associato")
    lecture_title: str = Field(..., min_length=1, max_length=255, description="Titolo lezione")
    lecture_date: Optional[str] = Field(None, description="Data lezione (YYYY-MM-DD)")
    description: Optional[str] = Field(None, description="Descrizione lezione")
    keywords: List[str] = Field(default_factory=list, description="Parole chiave lezione")

    @validator('lecture_title')
    def validate_lecture_title(cls, v: str) -> str:
        """Valida titolo lezione."""
        if not v.strip():
            raise ValueError("Titolo lezione non può essere vuoto")
        return v.strip()


class Material(BaseEntity):
    """Modello materiale didattico."""
    id: Optional[int] = Field(default=None, description="ID materiale")
    lecture_id: Optional[int] = Field(None, description="ID lezione associata")
    course_id: Optional[int] = Field(None, description="ID corso associato")
    document_id: Optional[int] = Field(None, description="ID documento associato")
    material_type: MaterialType = Field(default=MaterialType.OTHER, description="Tipo materiale")
    description: Optional[str] = Field(None, description="Descrizione materiale")
    processed_at: Optional[datetime] = Field(None, description="Data processamento")

    @root_validator
    def validate_associations(cls, values):
        """Valida associazioni corso/lezioni."""
        lecture_id = values.get('lecture_id')
        course_id = values.get('course_id')
        document_id = values.get('document_id')

        if not any([lecture_id, course_id, document_id]):
            raise ValueError("Almeno una associazione (lecture, course, o document) richiesta")

        return values


class Task(BaseEntity):
    """Modello task/compito."""
    id: Optional[int] = Field(default=None, description="ID task")
    project_id: str = Field(..., description="ID progetto proprietario")
    user_id: int = Field(..., description="ID utente proprietario")
    course_id: Optional[int] = Field(None, description="ID corso associato")
    lecture_id: Optional[int] = Field(None, description="ID lezione associata")
    task_title: str = Field(..., min_length=1, max_length=255, description="Titolo task")
    task_description: Optional[str] = Field(None, description="Descrizione task")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Priorità task")
    task_type: str = Field(default="general", description="Tipo task")
    due_date: Optional[str] = Field(None, description="Data scadenza (YYYY-MM-DD)")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Status task")

    @validator('task_title')
    def validate_task_title(cls, v: str) -> str:
        """Valida titolo task."""
        if not v.strip():
            raise ValueError("Titolo task non può essere vuoto")
        return v.strip()


class ChatSession(BaseEntity):
    """Modello sessione chat."""
    id: Optional[int] = Field(default=None, description="ID sessione")
    project_id: str = Field(..., description="ID progetto proprietario")
    user_id: int = Field(..., description="ID utente proprietario")
    session_name: Optional[str] = Field(None, max_length=255, description="Nome sessione")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Ultimo aggiornamento")


class ChatMessage(BaseEntity):
    """Modello messaggio chat."""
    id: Optional[int] = Field(default=None, description="ID messaggio")
    session_id: int = Field(..., description="ID sessione chat")
    message_type: str = Field(..., regex=r'^(user|assistant|system)$', description="Tipo messaggio")
    content: str = Field(..., description="Contenuto messaggio")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadati messaggio")


class ConceptEntity(BaseEntity):
    """Modello entità conoscenza."""
    id: Optional[int] = Field(default=None, description="ID entità")
    project_id: str = Field(..., description="ID progetto proprietario")
    user_id: int = Field(..., description="ID utente proprietario")
    entity_type: EntityType = Field(..., description="Tipo entità")
    entity_name: str = Field(..., min_length=1, max_length=255, description="Nome entità")
    entity_description: Optional[str] = Field(None, description="Descrizione entità")
    source_file_name: Optional[str] = Field(None, max_length=255, description="File sorgente")
    confidence_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Punteggio confidenza")

    @validator('entity_name')
    def validate_entity_name(cls, v: str) -> str:
        """Valida nome entità."""
        if not v.strip():
            raise ValueError("Nome entità non può essere vuoto")
        return v.strip()


class ConceptRelationship(BaseEntity):
    """Modello relazione conoscenza."""
    id: Optional[int] = Field(default=None, description="ID relazione")
    user_id: int = Field(..., description="ID utente proprietario")
    source_entity_id: int = Field(..., description="ID entità sorgente")
    target_entity_id: int = Field(..., description="ID entità target")
    relationship_type: RelationshipType = Field(..., description="Tipo relazione")
    relationship_description: Optional[str] = Field(None, description="Descrizione relazione")
    confidence_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Punteggio confidenza")


class UserXP(BaseEntity):
    """Modello punti esperienza utente."""
    id: Optional[int] = Field(default=None, description="ID record XP")
    project_id: str = Field(..., description="ID progetto proprietario")
    user_id: int = Field(..., description="ID utente proprietario")
    xp_amount: int = Field(..., gt=0, description="Quantità XP")
    xp_source: str = Field(..., min_length=1, max_length=100, description="Fonte XP")
    xp_description: Optional[str] = Field(None, description="Descrizione XP")
    source_id: Optional[str] = Field(None, max_length=100, description="ID fonte")


class UserAchievement(BaseEntity):
    """Modello achievement utente."""
    id: Optional[int] = Field(default=None, description="ID achievement")
    project_id: str = Field(..., description="ID progetto proprietario")
    user_id: int = Field(..., description="ID utente proprietario")
    achievement_type: str = Field(..., min_length=1, max_length=100, description="Tipo achievement")
    achievement_title: str = Field(..., min_length=1, max_length=255, description="Titolo achievement")
    achievement_description: Optional[str] = Field(None, description="Descrizione achievement")
    earned_at: datetime = Field(default_factory=datetime.utcnow, description="Data conseguimento")


class StudySession(BaseEntity):
    """Modello sessione studio."""
    id: Optional[int] = Field(default=None, description="ID sessione")
    project_id: str = Field(..., description="ID progetto proprietario")
    user_id: int = Field(..., description="ID utente proprietario")
    session_start: datetime = Field(..., description="Inizio sessione")
    session_end: Optional[datetime] = Field(None, description="Fine sessione")
    course_id: Optional[int] = Field(None, description="ID corso associato")
    duration_minutes: Optional[int] = Field(None, description="Durata in minuti")
    topics_covered: List[str] = Field(default_factory=list, description="Argomenti trattati")
    notes: Optional[str] = Field(None, description="Note sessione")
    productivity_rating: Optional[int] = Field(None, ge=1, le=5, description="Valutazione produttività")


class UserActivity(BaseEntity):
    """Modello attività utente."""
    id: Optional[int] = Field(default=None, description="ID attività")
    project_id: str = Field(..., description="ID progetto proprietario")
    user_id: int = Field(..., description="ID utente proprietario")
    action_type: str = Field(..., min_length=1, max_length=100, description="Tipo azione")
    target_type: Optional[str] = Field(None, max_length=100, description="Tipo target")
    target_id: Optional[str] = Field(None, max_length=100, description="ID target")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadati azione")
    session_id: Optional[str] = Field(None, max_length=100, description="ID sessione")


class DocumentProcessingStatus(BaseEntity):
    """Modello status processamento documento."""
    id: Optional[int] = Field(default=None, description="ID status")
    project_id: str = Field(..., description="ID progetto proprietario")
    file_name: str = Field(..., min_length=1, max_length=255, description="Nome file")
    processing_state: ProcessingStatus = Field(default=ProcessingStatus.PENDING, description="Stato processamento")
    processing_stage: Optional[str] = Field(None, max_length=100, description="Fase processamento")
    progress_percentage: int = Field(default=0, ge=0, le=100, description="Percentuale progresso")
    error_message: Optional[str] = Field(None, description="Messaggio errore")
    retry_count: int = Field(default=0, description="Numero tentativi")
    max_retries: int = Field(default=3, description="Max tentativi")

    @validator('file_name')
    def validate_file_name(cls, v: str) -> str:
        """Valida nome file."""
        if not v or len(v) > 255:
            raise ValueError("Nome file non valido")
        return v


class ProcessingErrorLog(BaseEntity):
    """Modello log errori processamento."""
    id: Optional[int] = Field(default=None, description="ID errore")
    project_id: str = Field(..., description="ID progetto proprietario")
    file_name: Optional[str] = Field(None, max_length=255, description="Nome file errore")
    error_category: str = Field(..., min_length=1, max_length=100, description="Categoria errore")
    error_type: str = Field(..., min_length=1, max_length=100, description="Tipo errore")
    error_message: str = Field(..., description="Messaggio errore")
    error_details: Dict[str, Any] = Field(default_factory=dict, description="Dettagli errore")
    severity: str = Field(default="medium", description="Severità errore")
    resolved: bool = Field(default=False, description="Flag errore risolto")


class ProcessingMetrics(BaseEntity):
    """Modello metriche processamento."""
    id: Optional[int] = Field(default=None, description="ID metrica")
    project_id: str = Field(..., description="ID progetto proprietario")
    metric_name: str = Field(..., min_length=1, max_length=100, description="Nome metrica")
    metric_value: float = Field(..., description="Valore metrica")
    metric_unit: Optional[str] = Field(None, max_length=50, description="Unità misura")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadati metrica")


class QuarantineFile(BaseEntity):
    """Modello file in quarantena."""
    id: Optional[int] = Field(default=None, description="ID file quarantena")
    project_id: str = Field(..., description="ID progetto proprietario")
    file_name: str = Field(..., min_length=1, max_length=255, description="Nome file")
    original_path: Optional[str] = Field(None, max_length=500, description="Percorso originale")
    quarantine_reason: str = Field(..., description="Motivo quarantena")
    error_details: Dict[str, Any] = Field(default_factory=dict, description="Dettagli errore")
    resolved_at: Optional[datetime] = Field(None, description="Data risoluzione")


class BayesianEvidence(BaseEntity):
    """Modello evidenza bayesiana."""
    id: Optional[int] = Field(default=None, description="ID evidenza")
    project_id: str = Field(..., description="ID progetto proprietario")
    entity_id: int = Field(..., description="ID entità associata")
    evidence_type: str = Field(..., min_length=1, max_length=100, description="Tipo evidenza")
    evidence_data: Dict[str, Any] = Field(..., description="Dati evidenza")
    confidence_weight: float = Field(default=1.0, ge=0.0, le=2.0, description="Peso confidenza")


# Response models for API

class DocumentResponse(BaseEntity):
    """Risposta documento con dati calcolati."""
    document: Document
    category_names: List[str] = Field(default_factory=list)
    processing_time_ms: Optional[int] = Field(None)
    word_count: Optional[int] = Field(None)
    ai_confidence: Optional[float] = Field(None)

class UserResponse(BaseEntity):
    """Risposta utente con statistiche."""
    user: User
    total_documents: int = Field(default=0)
    total_xp: int = Field(default=0)
    achievements_count: int = Field(default=0)
    study_streak_days: int = Field(default=0)

class SearchResult(BaseModel):
    """Risultato ricerca documenti."""
    documents: List[DocumentResponse]
    total_count: int
    query_time_ms: int
    suggestions: List[str] = Field(default_factory=list)

class ArchiveStats(BaseModel):
    """Statistiche archivio."""
    total_documents: int
    total_size_bytes: int
    documents_by_status: Dict[str, int]
    documents_by_category: Dict[str, int]
    recent_uploads: int
    ai_processed: int
