"""
Modelli base per il sistema.

Definisce modelli e utility comuni per tutti i modelli dati.
"""

from pydantic import BaseModel
from typing import Any, Dict, Optional
from datetime import datetime
from typing import List, Optional as _Optional

# Backwards compatibility imports: some tests import Document/User/ProcessingStatus
# from this module. Import lazily to avoid circular imports.
try:
    from .document import Document  # type: ignore
except Exception:
    Document = None  # type: ignore
try:
    from .user import User  # type: ignore
except Exception:
    User = None  # type: ignore

try:
    from .document import ProcessingStatus, DocumentResponse  # type: ignore
except Exception:
    ProcessingStatus = None  # type: ignore
    DocumentResponse = None  # type: ignore
try:
    from .user import UserResponse  # type: ignore
except Exception:
    UserResponse = None  # type: ignore


class BaseDBModel(BaseModel):
    """Modello base per tutti i modelli database."""

    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class DatabaseResponse(BaseModel):
    """Risposta standard operazioni database."""
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None

    # Allow dict-like access used in tests, e.g., result['success']
    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)

    def keys(self):
        return ('success', 'message', 'data', 'error')

class PaginationParams(BaseModel):
    """Parametri paginazione."""
    page: int = 1
    size: int = 20
    sort_by: Optional[str] = None
    sort_order: str = "asc"  # asc, desc

class PaginatedResponse(BaseModel):
    """Risposta paginata."""
    items: list
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool


# Lightweight knowledge-graph related models used across AI services.
from pydantic import Field
from typing import List

class ConceptEntity(BaseModel):
    id: Optional[int] = None
    name: str = Field(...)
    type: Optional[str] = None
    confidence: Optional[float] = 0.0

class ConceptRelationship(BaseModel):
    source: str
    target: str
    relation: Optional[str] = None
    strength: Optional[float] = 0.0

class BayesianEvidence(BaseModel):
    evidence_id: Optional[str] = None
    entity: Optional[ConceptEntity] = None
    likelihood: Optional[float] = 0.0
    details: Optional[dict] = None
