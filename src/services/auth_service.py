"""
Servizio per la gestione dell'autenticazione.

Questo servizio estrae e centralizza la logica di autenticazione
da file_utils.py per sostituire gradualmente le 12 pagine sparse.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..database.repositories.user_repository import UserRepository
from ..database.models.user import User
from ..core.errors.error_handler import handle_errors

logger = logging.getLogger(__name__)

class AuthService:
    """Servizio centralizzato per autenticazione."""

    def __init__(self):
        """Inizializza il servizio autenticazione."""
        self.repository = UserRepository()

    @handle_errors(operation="authenticate_user", component="auth_service")
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Autentica utente."""
        try:
            return self.repository.authenticate_user(username, password)
        except Exception as e:
            logger.error(f"Errore autenticazione utente {username}: {e}")
            return None

    @handle_errors(operation="create_user", component="auth_service")
    def create_user(self, username: str, password: str, email: str = None) -> Optional[User]:
        """Crea nuovo utente."""
        try:
            user = User(
                username=username,
                password_hash=self._hash_password(password),
                email=email,
                created_at=datetime.now(),
                is_active=True
            )
            return self.repository.create_user(user)
        except Exception as e:
            logger.error(f"Errore creazione utente {username}: {e}")
            return None

    @handle_errors(operation="get_user_by_id", component="auth_service")
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Recupera utente per ID."""
        try:
            return self.repository.get_user_by_id(user_id)
        except Exception as e:
            logger.error(f"Errore recupero utente {user_id}: {e}")
            return None

    @handle_errors(operation="update_user_preferences", component="auth_service")
    def update_user_preferences(self, user_id: int, preferences: Dict[str, Any]) -> bool:
        """Aggiorna preferenze utente."""
        try:
            return self.repository.update_user_preferences(user_id, preferences)
        except Exception as e:
            logger.error(f"Errore aggiornamento preferenze utente {user_id}: {e}")
            return False

    def _hash_password(self, password: str) -> str:
        """Hash password (placeholder per implementazione completa)."""
        # Questa logica verrà estratta da file_utils.py
        import hashlib
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def get_user_statistics(self) -> Dict[str, Any]:
        """Restituisce statistiche utenti."""
        try:
            total_users = self.repository.count_users()
            active_users = self.repository.count_active_users()

            return {
                "total_users": total_users,
                "active_users": active_users,
                "new_users_today": 0,  # Da implementare
                "last_registration": None  # Da implementare
            }
        except Exception as e:
            logger.error(f"Errore calcolo statistiche utenti: {e}")
            return {"total_users": 0, "active_users": 0}
