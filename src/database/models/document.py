"""
Modelli Pydantic per documenti.

Questi modelli definiscono la struttura dati per i documenti
nel sistema Archivista AI.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import json


class ProcessingStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class DocumentResponse(BaseModel):
    """Wrapper response used by services to return processing results."""
    document: Optional['Document'] = None
    processing_time_ms: int = 0
    word_count: int = 0
    ai_confidence: float = 0.0


class Document(BaseModel):
    """Modello documento principale."""
    id: Optional[int] = Field(None, description="ID documento univoco")
    file_name: str = Field(..., description="Nome file univoco")
    title: Optional[str] = Field(None, description="Titolo documento")
    authors: Optional[str] = Field(None, description="Autori documento")
    publication_year: Optional[int] = Field(None, description="Anno pubblicazione")
    category_id: Optional[str] = Field(None, description="ID categoria")
    category_name: Optional[str] = Field(None, description="Nome categoria")
    project_id: Optional[str] = Field(None, description="ID progetto associato")
    processing_status: ProcessingStatus = Field(default=ProcessingStatus.PENDING, description="Stato processamento")
    formatted_preview: Optional[str] = Field(None, description="Anteprima generata AI")
    processed_at: Optional[str] = Field(None, description="Timestamp processamento")
    file_size: Optional[int] = Field(None, description="Dimensione file in byte")
    mime_type: Optional[str] = Field(None, description="Tipo MIME")
    keywords: Optional[List[str]] = Field(None, description="Parole chiave estratte")
    ai_tasks: Optional[Dict[str, Any]] = Field(None, description="Task AI associati")
    created_by: Optional[int] = Field(None, description="ID utente che ha creato il documento")
    created_at: Optional[str] = Field(None, description="Data creazione")
    updated_at: Optional[str] = Field(None, description="Ultimo aggiornamento")
    content_hash: Optional[str] = Field(None, description="Hash del contenuto per rilevamento duplicati")

    @field_validator('keywords', mode='before')
    @classmethod
    def convert_keywords(cls, v):
        """Convert keywords string from database to list."""
        if v is None:
            return v
        elif isinstance(v, str):
            return [keyword.strip() for keyword in v.split(',') if keyword.strip()]
        elif isinstance(v, list):
            return v
        else:
            return []

    @field_validator('ai_tasks', mode='before')
    @classmethod
    def convert_ai_tasks(cls, v):
        """Convert ai_tasks string from database to dict."""
        if v is None:
            return v
        elif isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return {}
        elif isinstance(v, dict):
            return v
        else:
            return {}

    class Config:
        from_attributes = True

class DocumentCreate(BaseModel):
    """Modello per creazione documento."""
    file_name: str
    title: Optional[str] = None
    authors: Optional[str] = None
    publication_year: Optional[int] = None
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    project_id: Optional[str] = None
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    formatted_preview: Optional[str] = None
    processed_at: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    keywords: Optional[List[str]] = None
    ai_tasks: Optional[Dict[str, Any]] = None
    created_by: Optional[int] = None
    content_hash: Optional[str] = None

class DocumentUpdate(BaseModel):
    """Modello per aggiornamento documento."""
    title: Optional[str] = None
    authors: Optional[str] = None
    publication_year: Optional[int] = None
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    project_id: Optional[str] = None
    processing_status: Optional[ProcessingStatus] = None
    formatted_preview: Optional[str] = None
    processed_at: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    keywords: Optional[List[str]] = None
    ai_tasks: Optional[Dict[str, Any]] = None
    created_by: Optional[int] = None
    content_hash: Optional[str] = None

    @field_validator('keywords', mode='before')
    @classmethod
    def convert_keywords_update(cls, v):
        """Convert keywords for update operations."""
        if v is None:
            return v
        elif isinstance(v, str):
            return [keyword.strip() for keyword in v.split(',') if keyword.strip()]
        elif isinstance(v, list):
            return v
        else:
            return []

    @field_validator('ai_tasks', mode='before')
    @classmethod
    def convert_ai_tasks_update(cls, v):
        """Convert ai_tasks for update operations."""
        if v is None:
            return v
        elif isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return {}
        elif isinstance(v, dict):
            return v
        else:
            return {}
