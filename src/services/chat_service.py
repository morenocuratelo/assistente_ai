"""
Service per gestione chat.

Implementa logica business per operazioni sulle chat.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

from .base_service import BaseService
from ..database.repositories.chat_repository import ChatRepository
from ..database.models.chat import Chat, ChatCreate, ChatUpdate, Message, MessageCreate, MessageUpdate

class ChatService(BaseService):
    """Service per chat."""

    def __init__(self, repository: ChatRepository = None):
        """Inizializza service chat."""
        if repository is None:
            repository = ChatRepository()
        super().__init__(repository)

    def get_by_id(self, id: int) -> Dict[str, Any]:
        """Recupera chat per ID."""
        try:
            chat = self.repository.get_by_id(id)
            if chat:
                return self._create_response(True, "Chat recuperata", data=chat.dict())
            return self._create_response(False, "Chat non trovata")
        except Exception as e:
            return self._handle_error(e, "recupero chat")

    def get_all(self, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Recupera tutte le chat."""
        try:
            chats = self.repository.get_all(filters)
            return self._create_response(
                True,
                f"Recuperate {len(chats)} chat",
                data=[chat.dict() for chat in chats]
            )
        except Exception as e:
            return self._handle_error(e, "recupero chat")

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea nuova chat."""
        try:
            # Crea oggetto ChatCreate
            chat_create = ChatCreate(**data)
            chat = self.repository.create(chat_create)
            return self._create_response(True, "Chat creata", data=chat.dict())
        except Exception as e:
            return self._handle_error(e, "creazione chat")

    def update(self, id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Aggiorna chat."""
        try:
            # Crea oggetto ChatUpdate
            chat_update = ChatUpdate(**data)
            success = self.repository.update(id, chat_update)
            if success:
                return self._create_response(True, "Chat aggiornata")
            return self._create_response(False, "Chat non trovata")
        except Exception as e:
            return self._handle_error(e, "aggiornamento chat")

    def delete(self, id: int) -> Dict[str, Any]:
        """Elimina chat."""
        try:
            success = self.repository.delete(id)
            if success:
                return self._create_response(True, "Chat eliminata")
            return self._create_response(False, "Chat non trovata")
        except Exception as e:
            return self._handle_error(e, "eliminazione chat")

    def get_chats_by_user(self, user_id: int) -> Dict[str, Any]:
        """Recupera chat per utente."""
        try:
            chats = self.repository.get_chats_by_user(user_id)
            return self._create_response(
                True,
                f"Recuperate {len(chats)} chat utente {user_id}",
                data=[chat.dict() for chat in chats]
            )
        except Exception as e:
            return self._handle_error(e, "recupero chat per utente")

    def get_recent_chats(self, limit: int = 10) -> Dict[str, Any]:
        """Recupera chat più recenti."""
        try:
            chats = self.repository.get_recent_chats(limit)
            return self._create_response(
                True,
                f"Recuperate {len(chats)} chat recenti",
                data=[chat.dict() for chat in chats]
            )
        except Exception as e:
            return self._handle_error(e, "recupero chat recenti")

    def add_message(self, chat_id: int, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Aggiungi messaggio alla chat."""
        try:
            # Crea messaggio dal dizionario con chat_id obbligatorio
            message_create = MessageCreate(chat_id=chat_id, **message_data)
            message = self.repository.add_message(chat_id, message_create)

            # Aggiorna timestamp chat
            self.repository.update(chat_id, ChatUpdate())

            return self._create_response(True, "Messaggio aggiunto", data=message.dict())
        except Exception as e:
            return self._handle_error(e, "aggiunta messaggio")

    def get_messages_by_chat(self, chat_id: int) -> Dict[str, Any]:
        """Recupera messaggi per chat."""
        try:
            messages = self.repository.get_messages_by_chat_id(chat_id)
            return self._create_response(
                True,
                f"Recuperati {len(messages)} messaggi",
                data=[msg.dict() for msg in messages]
            )
        except Exception as e:
            return self._handle_error(e, "recupero messaggi chat")

    def get_message_by_id(self, message_id: int) -> Dict[str, Any]:
        """Recupera messaggio per ID."""
        try:
            message = self.repository.get_message_by_id(message_id)
            if message:
                return self._create_response(True, "Messaggio recuperato", data=message.dict())
            return self._create_response(False, "Messaggio non trovato")
        except Exception as e:
            return self._handle_error(e, "recupero messaggio")

    def update_message(self, message_id: int, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Aggiorna messaggio."""
        try:
            # Crea oggetto MessageUpdate
            message_update = MessageUpdate(**message_data)
            success = self.repository.update_message(message_id, message_update)
            if success:
                return self._create_response(True, "Messaggio aggiornato")
            return self._create_response(False, "Messaggio non trovato")
        except Exception as e:
            return self._handle_error(e, "aggiornamento messaggio")

    def delete_message(self, message_id: int) -> Dict[str, Any]:
        """Elimina messaggio."""
        try:
            success = self.repository.delete_message(message_id)
            if success:
                return self._create_response(True, "Messaggio eliminato")
            return self._create_response(False, "Messaggio non trovato")
        except Exception as e:
            return self._handle_error(e, "eliminazione messaggio")

    def get_chat_with_messages(self, chat_id: int) -> Dict[str, Any]:
        """Recupera chat con tutti i messaggi."""
        try:
            chat = self.repository.get_by_id(chat_id)
            if not chat:
                return self._create_response(False, "Chat non trovata")

            # Carica tutti i messaggi
            messages = self.repository.get_messages_by_chat_id(chat_id)

            chat_data = chat.dict()
            chat_data['messages'] = [msg.dict() for msg in messages]

            return self._create_response(
                True,
                f"Chat con {len(messages)} messaggi recuperata",
                data=chat_data
            )
        except Exception as e:
            return self._handle_error(e, "recupero chat con messaggi")

    def create_chat_with_first_message(self, chat_data: Dict[str, Any], first_message: Dict[str, Any]) -> Dict[str, Any]:
        """Crea chat con primo messaggio."""
        try:
            # Crea chat
            chat_create = ChatCreate(**chat_data)
            chat = self.repository.create(chat_create)

            if not chat:
                return self._create_response(False, "Errore creazione chat")

            # Aggiungi primo messaggio
            message_result = self.add_message(chat.id, first_message)
            if not message_result['success']:
                # Se errore messaggio, elimina chat
                self.repository.delete(chat.id)
                return self._create_response(False, "Errore aggiunta primo messaggio")

            return self._create_response(
                True,
                "Chat con primo messaggio creata",
                data=chat.dict()
            )
        except Exception as e:
            return self._handle_error(e, "creazione chat con primo messaggio")

    def get_chat_stats(self, user_id: int = None) -> Dict[str, Any]:
        """Recupera statistiche chat."""
        try:
            filters = {"user_id": user_id} if user_id else None
            chats = self.repository.get_all(filters)

            total_chats = len(chats)
            total_messages = 0
            chats_with_messages = 0

            for chat in chats:
                messages = self.repository.get_messages_by_chat_id(chat.id)
                message_count = len(messages)
                total_messages += message_count
                if message_count > 0:
                    chats_with_messages += 1

            stats = {
                "total_chats": total_chats,
                "total_messages": total_messages,
                "chats_with_messages": chats_with_messages,
                "average_messages_per_chat": total_messages / total_chats if total_chats > 0 else 0
            }

            return self._create_response(True, "Statistiche chat", data=stats)
        except Exception as e:
            return self._handle_error(e, "calcolo statistiche chat")

    def search_messages(self, chat_id: int, query: str) -> Dict[str, Any]:
        """Cerca messaggi in una chat."""
        try:
            messages = self.repository.get_messages_by_chat_id(chat_id)

            # Filtro semplice per query testuale
            if query:
                filtered_messages = []
                query_lower = query.lower()
                for message in messages:
                    if query_lower in message.content.lower():
                        filtered_messages.append(message)
                messages = filtered_messages

            return self._create_response(
                True,
                f"Trovati {len(messages)} messaggi",
                data=[msg.dict() for msg in messages]
            )
        except Exception as e:
            return self._handle_error(e, "ricerca messaggi")
