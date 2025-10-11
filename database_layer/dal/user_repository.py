# User Repository - Gestione utenti e autenticazione
"""
Repository specializzato per la gestione degli utenti.

Gestisce la tabella 'users' che contiene:
- Informazioni account utente
- Hash password sicure
- Stato utente (nuovo, attivo, etc.)
- Metadati creazione e aggiornamento
"""

import bcrypt
import hashlib
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from .base_repository import BaseRepository, DatabaseOperationError

logger = logging.getLogger('UserRepository')

class UserRepository(BaseRepository):
    """
    Repository per gestione utenti e autenticazione.

    Fornisce operazioni sicure per gestione account utente
    con supporto password hashing e validazione.
    """

    def _get_table_name(self) -> str:
        """Restituisce nome tabella utenti"""
        return 'users'

    def _validate_create_data(self, data: Dict[str, Any]):
        """Validazione dati creazione utente"""
        super()._validate_create_data(data)

        required_fields = ['username', 'password_hash']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Campo obbligatorio mancante: {field}")

        # Validazione username
        if not data['username'] or not data['username'].strip():
            raise ValueError("Username non può essere vuoto")

        if len(data['username']) < 3:
            raise ValueError("Username deve essere almeno 3 caratteri")

        # Validazione password hash
        if not data['password_hash'] or not data['password_hash'].strip():
            raise ValueError("Password hash non può essere vuoto")

    def create_user(self, username: str, password: str) -> int:
        """
        Crea nuovo utente con password hashing sicuro.

        Args:
            username: Nome utente
            password: Password in chiaro

        Returns:
            ID utente creato

        Raises:
            DatabaseOperationError: Se username esiste già
        """
        try:
            # Verifica unicità username
            if self.find_by_username(username):
                raise DatabaseOperationError(f"Username '{username}' già esistente")

            # Hash password
            password_hash = self._hash_password(password)

            # Crea utente
            user_data = {
                'username': username.strip(),
                'password_hash': password_hash,
                'created_at': datetime.now().isoformat(),
                'is_new_user': 1
            }

            user_id = self.create(user_data)
            logger.info(f"Utente creato: {username} (ID: {user_id})")
            return user_id

        except Exception as e:
            logger.error(f"Errore creazione utente {username}: {e}")
            raise DatabaseOperationError(f"Errore creazione utente: {e}")

    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """
        Autentica utente con verifica password.

        Args:
            username: Nome utente
            password: Password in chiaro

        Returns:
            Dati utente se autenticazione successful, None altrimenti
        """
        try:
            user = self.find_by_username(username)
            if not user:
                logger.warning(f"Tentativo accesso username inesistente: {username}")
                return None

            # Verifica password
            if self._verify_password(password, user['password_hash']):
                logger.info(f"Autenticazione successful: {username}")
                return {
                    'id': user['id'],
                    'username': user['username'],
                    'created_at': user['created_at'],
                    'is_new_user': user.get('is_new_user', 1)
                }
            else:
                logger.warning(f"Password errata per utente: {username}")
                return None

        except Exception as e:
            logger.error(f"Errore autenticazione utente {username}: {e}")
            return None

    def find_by_username(self, username: str) -> Optional[Dict]:
        """
        Trova utente per username.

        Args:
            username: Username da cercare

        Returns:
            Utente trovato o None
        """
        query = "SELECT * FROM users WHERE username = ?"
        return self.execute_query(query, (username,), fetch='one')

    def find_by_id(self, user_id: int) -> Optional[Dict]:
        """
        Trova utente per ID.

        Args:
            user_id: ID utente da cercare

        Returns:
            Utente trovato o None
        """
        query = "SELECT id, username, created_at, is_new_user FROM users WHERE id = ?"
        return self.execute_query(query, (user_id,), fetch='one')

    def update_password(self, user_id: int, new_password: str) -> bool:
        """
        Aggiorna password utente.

        Args:
            user_id: ID utente
            new_password: Nuova password in chiaro

        Returns:
            True se aggiornata con successo
        """
        try:
            password_hash = self._hash_password(new_password)

            success = self.update(user_id, {
                'password_hash': password_hash
            })

            if success:
                logger.info(f"Password aggiornata per utente ID: {user_id}")

            return success

        except Exception as e:
            logger.error(f"Errore aggiornamento password utente {user_id}: {e}")
            raise DatabaseOperationError(f"Errore aggiornamento password: {e}")

    def mark_user_not_new(self, user_id: int) -> bool:
        """
        Marca utente come non più nuovo.

        Args:
            user_id: ID utente

        Returns:
            True se aggiornato con successo
        """
        try:
            success = self.update(user_id, {
                'is_new_user': 0
            })

            if success:
                logger.info(f"Utente {user_id} marcato come non nuovo")

            return success

        except Exception as e:
            logger.error(f"Errore marcatura utente non nuovo {user_id}: {e}")
            return False

    def is_new_user(self, user_id: int) -> bool:
        """
        Verifica se utente è nuovo.

        Args:
            user_id: ID utente

        Returns:
            True se utente è nuovo
        """
        try:
            user = self.find_by_id(user_id)
            return user and user.get('is_new_user', 1) == 1

        except Exception as e:
            logger.error(f"Errore verifica utente nuovo {user_id}: {e}")
            return True  # Default a True per sicurezza

    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Statistiche utente.

        Args:
            user_id: ID utente

        Returns:
            Dizionario statistiche
        """
        try:
            # Questa query richiede accesso ad altre tabelle
            # Per ora restituiamo statistiche base
            user = self.find_by_id(user_id)
            if not user:
                return {}

            return {
                'user_id': user_id,
                'username': user['username'],
                'created_at': user['created_at'],
                'is_new_user': user.get('is_new_user', 1),
                'account_age_days': (datetime.now() - datetime.fromisoformat(user['created_at'])).days
            }

        except Exception as e:
            logger.error(f"Errore statistiche utente {user_id}: {e}")
            return {}

    def delete_user(self, user_id: int) -> bool:
        """
        Elimina utente (operazione pericolosa).

        Args:
            user_id: ID utente da eliminare

        Returns:
            True se eliminato con successo
        """
        try:
            # Verifica esistenza
            if not self.exists(user_id):
                logger.warning(f"Tentativo eliminazione utente inesistente: {user_id}")
                return False

            # Elimina utente (cascade dovrebbe eliminare dati correlati)
            success = self.delete(user_id)

            if success:
                logger.info(f"Utente eliminato: {user_id}")

            return success

        except Exception as e:
            logger.error(f"Errore eliminazione utente {user_id}: {e}")
            raise DatabaseOperationError(f"Errore eliminazione utente: {e}")

    def list_users(self, limit: int = 100) -> List[Dict]:
        """
        Lista utenti (admin function).

        Args:
            limit: Limite risultati

        Returns:
            Lista utenti
        """
        query = "SELECT id, username, created_at, is_new_user FROM users ORDER BY created_at DESC"
        if limit:
            query += f" LIMIT {limit}"

        return self.execute_query(query, fetch='all')

    def _hash_password(self, password: str) -> str:
        """
        Hash password usando bcrypt.

        Args:
            password: Password in chiaro

        Returns:
            Hash password sicuro
        """
        try:
            # Usa bcrypt se disponibile
            return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        except (ImportError, AttributeError):
            # Fallback a hashlib se bcrypt non disponibile
            logger.warning("bcrypt non disponibile, uso hashlib (meno sicuro)")
            return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """
        Verifica password contro hash.

        Args:
            password: Password in chiaro
            password_hash: Hash da verificare

        Returns:
            True se password corretta
        """
        try:
            # Prova bcrypt prima
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except (ImportError, AttributeError):
            # Fallback a hashlib
            return hashlib.sha256(password.encode('utf-8')).hexdigest() == password_hash

    def change_username(self, user_id: int, new_username: str) -> bool:
        """
        Cambia username utente.

        Args:
            user_id: ID utente
            new_username: Nuovo username

        Returns:
            True se cambiato con successo
        """
        try:
            # Verifica unicità nuovo username
            existing_user = self.find_by_username(new_username)
            if existing_user and existing_user['id'] != user_id:
                raise DatabaseOperationError(f"Username '{new_username}' già esistente")

            success = self.update(user_id, {
                'username': new_username.strip()
            })

            if success:
                logger.info(f"Username cambiato per utente {user_id}: {new_username}")

            return success

        except Exception as e:
            logger.error(f"Errore cambio username utente {user_id}: {e}")
            raise DatabaseOperationError(f"Errore cambio username: {e}")

    def get_user_count(self) -> int:
        """
        Conta totale utenti.

        Returns:
            Numero totale utenti
        """
        return self.count()

    def get_new_users_count(self) -> int:
        """
        Conta utenti nuovi.

        Returns:
            Numero utenti nuovi
        """
        return self.count({'is_new_user': 1})
