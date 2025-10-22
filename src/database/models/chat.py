"""
Modelli Pydantic per chat e conversazioni.

Questi modelli definiscono la struttura dati per le chat
nel sistema Archivista AI.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class Chat(BaseModel):
    """Modello chat principale."""
    id: Optional[int] = Field(None, description="ID chat")
    title: str = Field(..., description="Titolo chat")
    user_id: Optional[int] = Field(None, description="ID utente proprietario")
    is_active: bool = Field(True, description="Chat attiva")
    created_at: Optional[str] = Field(None, description="Data creazione")
    updated_at: Optional[str] = Field(None, description="Ultimo aggiornamento")
    metadata: Optional[str] = Field(None, description="Metadati JSON")

    # Campo virtuale per messaggi (non salvato in DB)
    messages: Optional[List['Message']] = Field(None, description="Messaggi chat")

    class Config:
        from_attributes = True

class Message(BaseModel):
    """Modello messaggio chat."""
    id: Optional[int] = Field(None, description="ID messaggio")
    chat_id: int = Field(..., description="ID chat")
    role: str = Field(..., description="Ruolo (user/assistant/system)")
    content: str = Field(..., description="Contenuto messaggio")
    timestamp: str = Field(..., description="Timestamp messaggio")
    metadata: Optional[str] = Field(None, description="Metadati JSON")
    tokens: Optional[int] = Field(None, description="Token utilizzati")
    model: Optional[str] = Field(None, description="Modello AI usato")
    temperature: Optional[float] = Field(None, description="Temperatura AI")
    created_at: Optional[str] = Field(None, description="Data creazione")

    class Config:
        from_attributes = True

class ChatCreate(BaseModel):
    """Modello per creazione chat."""
    title: str
    user_id: Optional[int] = None
    is_active: bool = True
    metadata: Optional[str] = None

class ChatUpdate(BaseModel):
    """Modello per aggiornamento chat."""
    title: Optional[str] = None
    user_id: Optional[int] = None
    is_active: Optional[bool] = None
    metadata: Optional[str] = None

class MessageCreate(BaseModel):
    """Modello per creazione messaggio."""
    chat_id: int = Field(..., description="ID chat obbligatorio")
    role: str = Field(..., description="Ruolo messaggio")
    content: str = Field(..., description="Contenuto messaggio")
    timestamp: str = Field(..., description="Timestamp messaggio")
    metadata: Optional[str] = Field(None, description="Metadati JSON")
    tokens: Optional[int] = Field(None, description="Token utilizzati")
    model: Optional[str] = Field(None, description="Modello AI usato")
    temperature: Optional[float] = Field(None, description="Temperatura AI")

class MessageUpdate(BaseModel):
    """Modello per aggiornamento messaggio."""
    role: Optional[str] = None
    content: Optional[str] = None
    timestamp: Optional[str] = None
    metadata: Optional[str] = None
    tokens: Optional[int] = None
    model: Optional[str] = None
    temperature: Optional[float] = None

# Modelli legacy per compatibilità (se necessario)
class ChatSession(BaseModel):
    """Modello sessione chat (legacy)."""
    id: Optional[int] = Field(None, description="ID sessione")
    user_id: int = Field(..., description="ID utente proprietario")
    session_name: str = Field(..., description="Nome sessione")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Data creazione")
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Ultimo aggiornamento")

    class Config:
        from_attributes = True

class ChatMessage(BaseModel):
    """Modello messaggio chat (legacy)."""
    id: Optional[int] = Field(None, description="ID messaggio")
    session_id: int = Field(..., description="ID sessione")
    message_type: str = Field(..., description="Tipo messaggio (user/ai)")
    content: str = Field(..., description="Contenuto messaggio")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Timestamp messaggio")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadati aggiuntivi")

    class Config:
        from_attributes = True

class ChatSessionCreate(BaseModel):
    """Modello per creazione sessione chat (legacy)."""
    user_id: int
    session_name: str

class ChatMessageCreate(BaseModel):
    """Modello per creazione messaggio chat (legacy)."""
    session_id: int
    message_type: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
