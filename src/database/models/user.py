"""
Modelli Pydantic per utenti.

Questi modelli definiscono la struttura dati per gli utenti
nel sistema Archivista AI.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class User(BaseModel):
    """Modello utente principale."""
    id: Optional[int] = Field(None, description="ID univoco utente")
    username: str = Field(..., description="Username univoco")
    password_hash: str = Field(..., description="Hash password")
    email: Optional[str] = Field(None, description="Email utente")
    first_name: Optional[str] = Field(None, description="Nome utente")
    last_name: Optional[str] = Field(None, description="Cognome utente")
    is_active: bool = Field(True, description="Utente attivo")
    is_admin: bool = Field(False, description="Utente amministratore")
    preferences: Optional[Dict[str, Any]] = Field(None, description="Preferenze utente")
    is_new_user: bool = Field(True, description="Nuovo utente")
    created_at: Optional[str] = Field(None, description="Data creazione")
    updated_at: Optional[str] = Field(None, description="Ultimo aggiornamento")
    last_login: Optional[str] = Field(None, description="Ultimo accesso")

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    """Modello per creazione utente."""
    username: str
    password_hash: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False
    preferences: Optional[Dict[str, Any]] = None

class UserUpdate(BaseModel):
    """Modello per aggiornamento utente."""
    username: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    preferences: Optional[Dict[str, Any]] = None


class UserResponse(BaseModel):
    """Wrapper for user-related service responses."""
    user: Optional[User] = None
    message: Optional[str] = None
    success: bool = True
