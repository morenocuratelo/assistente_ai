"""
Repository per gestione chat.

Implementa operazioni CRUD per le chat nel database.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

from .base_repository import BaseRepository
from ..models.chat import Chat, ChatCreate, ChatUpdate, Message, MessageCreate, MessageUpdate

class ChatRepository(BaseRepository):
    """Repository per chat."""

    def __init__(self, db_path: str = "db_memoria/metadata.sqlite"):
        """Inizializza repository chat."""
        super().__init__(db_path)
        self._ensure_tables_exist()

    def _ensure_tables_exist(self) -> None:
        """Crea tabelle chat e messaggi se non esistono."""
        # Tabella chat
        chat_query = """
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            user_id INTEGER,
            is_active BOOLEAN DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            metadata TEXT
        )
        """
        self.execute_update(chat_query)

        # Tabella messaggi
        message_query = """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            role TEXT NOT NULL,  -- user, assistant, system
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            metadata TEXT,
            tokens INTEGER,
            model TEXT,
            temperature REAL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (chat_id) REFERENCES chats (id) ON DELETE CASCADE
        )
        """
        self.execute_update(message_query)

    def get_by_id(self, id: int) -> Optional[Chat]:
        """Recupera chat per ID."""
        try:
            query = "SELECT * FROM chats WHERE id = ?"
            results = self.execute_query(query, (id,))

            if results:
                data = results[0]
                chat = Chat(**data)
                # Carica messaggi
                chat.messages = self.get_messages_by_chat_id(id)
                return chat
            return None
        except Exception as e:
            self.logger.error(f"Errore recupero chat {id}: {e}")
            return None

    def get_all(self, filters: Dict[str, Any] = None) -> List[Chat]:
        """Recupera tutte le chat."""
        try:
            query = "SELECT * FROM chats"
            params = []

            if filters:
                conditions = []
                for key, value in filters.items():
                    if value is not None:
                        conditions.append(f"{key} = ?")
                        params.append(value)

                if conditions:
                    query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY updated_at DESC"

            results = self.execute_query(query, tuple(params))
            chats = []
            for data in results:
                chat = Chat(**data)
                # Carica messaggi
                chat.messages = self.get_messages_by_chat_id(chat.id)
                chats.append(chat)

            return chats
        except Exception as e:
            self.logger.error(f"Errore recupero chat: {e}")
            return []

    def create(self, entity: ChatCreate) -> Chat:
        """Crea nuova chat."""
        try:
            query = """
            INSERT INTO chats (title, user_id, is_active, created_at, metadata)
            VALUES (?, ?, ?, ?, ?)
            """

            params = (
                entity.title,
                entity.user_id,
                entity.is_active,
                datetime.now().isoformat(),
                entity.metadata
            )

            if self.execute_update(query, params):
                # Recupera la chat appena creata
                chat_id = self._get_last_insert_id()
                return self.get_by_id(chat_id)
            raise Exception("Errore creazione chat")
        except Exception as e:
            self.logger.error(f"Errore creazione chat: {e}")
            raise

    def update(self, id: int, entity: ChatUpdate) -> bool:
        """Aggiorna chat."""
        try:
            # Costruisci query dinamica
            update_fields = []
            params = []

            for field, value in entity.dict(exclude_unset=True).items():
                update_fields.append(f"{field} = ?")
                params.append(value)

            if not update_fields:
                return True

            params.append(datetime.now().isoformat())  # updated_at
            params.append(id)

            query = f"""
            UPDATE chats SET {', '.join(update_fields)}, updated_at = ?
            WHERE id = ?
            """

            return self.execute_update(query, tuple(params))
        except Exception as e:
            self.logger.error(f"Errore aggiornamento chat {id}: {e}")
            return False

    def delete(self, id: int) -> bool:
        """Elimina chat."""
        try:
            query = "DELETE FROM chats WHERE id = ?"
            return self.execute_update(query, (id,))
        except Exception as e:
            self.logger.error(f"Errore eliminazione chat {id}: {e}")
            return False

    def get_messages_by_chat_id(self, chat_id: int) -> List[Message]:
        """Recupera messaggi per chat ID."""
        try:
            query = """
            SELECT * FROM messages
            WHERE chat_id = ?
            ORDER BY timestamp ASC
            """
            results = self.execute_query(query, (chat_id,))

            messages = []
            for data in results:
                message = Message(**data)
                messages.append(message)

            return messages
        except Exception as e:
            self.logger.error(f"Errore recupero messaggi chat {chat_id}: {e}")
            return []

    def add_message(self, chat_id: int, message: MessageCreate) -> Message:
        """Aggiunge messaggio a chat."""
        try:
            query = """
            INSERT INTO messages (chat_id, role, content, timestamp, metadata,
                               tokens, model, temperature, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            params = (
                chat_id,
                message.role,
                message.content,
                message.timestamp,
                message.metadata,
                message.tokens,
                message.model,
                message.temperature,
                datetime.now().isoformat()
            )

            if self.execute_update(query, params):
                # Recupera il messaggio appena creato
                message_id = self._get_last_insert_id()
                return self.get_message_by_id(message_id)
            raise Exception("Errore aggiunta messaggio")
        except Exception as e:
            self.logger.error(f"Errore aggiunta messaggio a chat {chat_id}: {e}")
            raise

    def get_message_by_id(self, message_id: int) -> Optional[Message]:
        """Recupera messaggio per ID."""
        try:
            query = "SELECT * FROM messages WHERE id = ?"
            results = self.execute_query(query, (message_id,))

            if results:
                data = results[0]
                return Message(**data)
            return None
        except Exception as e:
            self.logger.error(f"Errore recupero messaggio {message_id}: {e}")
            return None

    def update_message(self, message_id: int, message: MessageUpdate) -> bool:
        """Aggiorna messaggio."""
        try:
            # Costruisci query dinamica
            update_fields = []
            params = []

            for field, value in message.dict(exclude_unset=True).items():
                update_fields.append(f"{field} = ?")
                params.append(value)

            if not update_fields:
                return True

            params.append(message_id)

            query = f"""
            UPDATE messages SET {', '.join(update_fields)}
            WHERE id = ?
            """

            return self.execute_update(query, tuple(params))
        except Exception as e:
            self.logger.error(f"Errore aggiornamento messaggio {message_id}: {e}")
            return False

    def delete_message(self, message_id: int) -> bool:
        """Elimina messaggio."""
        try:
            query = "DELETE FROM messages WHERE id = ?"
            return self.execute_update(query, (message_id,))
        except Exception as e:
            self.logger.error(f"Errore eliminazione messaggio {message_id}: {e}")
            return False

    def get_chats_by_user(self, user_id: int) -> List[Chat]:
        """Recupera chat per utente."""
        return self.get_all({"user_id": user_id})

    def get_recent_chats(self, limit: int = 10) -> List[Chat]:
        """Recupera chat più recenti."""
        try:
            query = """
            SELECT * FROM chats
            WHERE is_active = 1
            ORDER BY updated_at DESC
            LIMIT ?
            """
            results = self.execute_query(query, (limit,))

            chats = []
            for data in results:
                chat = Chat(**data)
                # Carica messaggi recenti (ultimi 10)
                chat.messages = self.get_recent_messages_by_chat(chat.id, 10)
                chats.append(chat)

            return chats
        except Exception as e:
            self.logger.error(f"Errore recupero chat recenti: {e}")
            return []

    def get_recent_messages_by_chat(self, chat_id: int, limit: int = 10) -> List[Message]:
        """Recupera messaggi più recenti per chat."""
        try:
            query = """
            SELECT * FROM messages
            WHERE chat_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """
            results = self.execute_query(query, (chat_id, limit))

            # Inverti ordine per avere dal più vecchio al più nuovo
            messages = []
            for data in reversed(results):
                message = Message(**data)
                messages.append(message)

            return messages
        except Exception as e:
            self.logger.error(f"Errore recupero messaggi recenti chat {chat_id}: {e}")
            return []

    def _get_last_insert_id(self) -> int:
        """Recupera ultimo ID inserito."""
        try:
            # Usa connessione diretta per ottenere l'ultimo ID
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT last_insert_rowid()")
            result = cursor.fetchone()
            return result[0] if result else 0
        except Exception as e:
            self.logger.error(f"Errore recupero ultimo ID: {e}")
            return 0
