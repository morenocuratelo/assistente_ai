"""
Service per gestione utenti.

Implementa logica business per operazioni sugli utenti.
"""

import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base_service import BaseService
from ..database.repositories.user_repository import UserRepository
from ..database.models.user import User, UserCreate, UserUpdate

class UserService(BaseService):
    """Service per utenti."""

    def __init__(self, repository: UserRepository = None):
        """Inizializza service utenti."""
        if repository is None:
            repository = UserRepository()
        super().__init__(repository)

    def get_by_id(self, id: int) -> Dict[str, Any]:
        """Recupera utente per ID."""
        try:
            user = self.repository.get_by_id(id)
            if user:
                return self._create_response(True, "Utente recuperato", data=user.dict())
            return self._create_response(False, "Utente non trovato")
        except Exception as e:
            return self._handle_error(e, "recupero utente")

    def get_by_username(self, username: str) -> Dict[str, Any]:
        """Recupera utente per username."""
        try:
            user = self.repository.get_by_username(username)
            if user:
                return self._create_response(True, "Utente recuperato", data=user.dict())
            return self._create_response(False, "Utente non trovato")
        except Exception as e:
            return self._handle_error(e, "recupero utente per username")

    def get_by_email(self, email: str) -> Dict[str, Any]:
        """Recupera utente per email."""
        try:
            user = self.repository.get_by_email(email)
            if user:
                return self._create_response(True, "Utente recuperato", data=user.dict())
            return self._create_response(False, "Utente non trovato")
        except Exception as e:
            return self._handle_error(e, "recupero utente per email")

    def get_all(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Recupera tutti gli utenti."""
        try:
            users = self.repository.get_all(filters)
            return self._create_response(
                True,
                f"Recuperati {len(users)} utenti",
                data=[user.dict() for user in users]
            )
        except Exception as e:
            return self._handle_error(e, "recupero utenti")

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea nuovo utente."""
        try:
            # Hash della password se presente
            if 'password' in data:
                data['password_hash'] = self._hash_password(data.pop('password'))

            # Crea oggetto UserCreate
            user_create = UserCreate(**data)
            user = self.repository.create(user_create)
            return self._create_response(True, "Utente creato", data=user.dict())
        except Exception as e:
            return self._handle_error(e, "creazione utente")

    def update(self, id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Aggiorna utente."""
        try:
            # Hash della password se presente
            if 'password' in data:
                data['password_hash'] = self._hash_password(data.pop('password'))

            # Crea oggetto UserUpdate
            user_update = UserUpdate(**data)
            success = self.repository.update(id, user_update)
            if success:
                return self._create_response(True, "Utente aggiornato")
            return self._create_response(False, "Utente non trovato")
        except Exception as e:
            return self._handle_error(e, "aggiornamento utente")

    def delete(self, id: int) -> Dict[str, Any]:
        """Elimina utente."""
        try:
            success = self.repository.delete(id)
            if success:
                return self._create_response(True, "Utente eliminato")
            return self._create_response(False, "Utente non trovato")
        except Exception as e:
            return self._handle_error(e, "eliminazione utente")

    def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """Autentica utente."""
        try:
            password_hash = self._hash_password(password)
            user = self.repository.authenticate_user(username, password_hash)

            if user:
                return self._create_response(
                    True,
                    "Autenticazione riuscita",
                    data=user.dict()
                )
            return self._create_response(False, "Credenziali non valide")
        except Exception as e:
            return self._handle_error(e, "autenticazione utente")

    def update_last_login(self, user_id: int) -> Dict[str, Any]:
        """Aggiorna ultimo accesso utente."""
        try:
            success = self.repository.update_last_login(user_id)
            if success:
                return self._create_response(True, "Ultimo accesso aggiornato")
            return self._create_response(False, "Utente non trovato")
        except Exception as e:
            return self._handle_error(e, "aggiornamento ultimo accesso")

    def get_active_users(self) -> Dict[str, Any]:
        """Recupera utenti attivi."""
        try:
            users = self.repository.get_active_users()
            return self._create_response(
                True,
                f"Recuperati {len(users)} utenti attivi",
                data=[user.dict() for user in users]
            )
        except Exception as e:
            return self._handle_error(e, "recupero utenti attivi")

    def get_admin_users(self) -> Dict[str, Any]:
        """Recupera utenti amministratori."""
        try:
            users = self.repository.get_admin_users()
            return self._create_response(
                True,
                f"Recuperati {len(users)} utenti amministratori",
                data=[user.dict() for user in users]
            )
        except Exception as e:
            return self._handle_error(e, "recupero utenti amministratori")

    def change_password(self, user_id: int, old_password: str, new_password: str) -> Dict[str, Any]:
        """Cambia password utente."""
        try:
            # Verifica vecchia password
            user = self.repository.get_by_id(user_id)
            if not user:
                return self._create_response(False, "Utente non trovato")

            old_hash = self._hash_password(old_password)
            if user.password_hash != old_hash:
                return self._create_response(False, "Password attuale non corretta")

            # Aggiorna password
            new_hash = self._hash_password(new_password)
            user_update = UserUpdate(password_hash=new_hash)
            success = self.repository.update(user_id, user_update)

            if success:
                return self._create_response(True, "Password cambiata con successo")
            return self._create_response(False, "Errore aggiornamento password")
        except Exception as e:
            return self._handle_error(e, "cambio password")

    def _hash_password(self, password: str) -> str:
        """Hash password con SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def create_user_session(self, username: str, password: str) -> Dict[str, Any]:
        """Crea sessione utente dopo autenticazione."""
        try:
            auth_result = self.authenticate(username, password)
            if not auth_result['success']:
                return auth_result

            user_data = auth_result['data']
            user_id = user_data['id']

            # Aggiorna ultimo accesso
            self.update_last_login(user_id)

            # Crea dati sessione (senza password)
            session_data = {
                'user_id': user_id,
                'username': user_data['username'],
                'email': user_data['email'],
                'first_name': user_data.get('first_name'),
                'last_name': user_data.get('last_name'),
                'is_admin': user_data.get('is_admin', False),
                'login_time': datetime.now().isoformat()
            }

            return self._create_response(
                True,
                "Sessione creata",
                data=session_data
            )
        except Exception as e:
            return self._handle_error(e, "creazione sessione utente")
