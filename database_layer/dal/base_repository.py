# Base Repository - Classe base per tutti i repository
"""
Classe base astratta che definisce il pattern repository comune
per tutte le operazioni database nell'applicazione Archivista AI.

Fornisce:
- Operazioni CRUD standardizzate
- Gestione errori centralizzata
- Logging strutturato
- Supporto contesto progetto (preparazione Fase 1)
- Validazione input
"""

import sqlite3
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import json
import os

# Configurazione logging semplificata per test
logger = logging.getLogger('BaseRepository')
logger.setLevel(logging.WARNING)  # Solo warning ed errori per test

class DatabaseConnectionError(Exception):
    """Eccezione per errori connessione database"""
    pass

class DatabaseOperationError(Exception):
    """Eccezione per errori operazioni database"""
    pass

class BaseRepository(ABC):
    """
    Classe base astratta per tutti i repository.

    Fornisce operazioni comuni e gestione errori standardizzata.
    """

    def __init__(self, db_path: str = None, project_id: str = None):
        """
        Inizializza il repository con connessione database.

        Args:
            db_path: Percorso file database (default: configurazione standard)
            project_id: ID progetto per supporto multi-progetto (Fase 1)
        """
        self.project_id = project_id
        self.db_path = db_path or self._get_default_db_path()
        self._connection = None
        self._table_name = self._get_table_name()

        logger.info(f"Inizializzato {self.__class__.__name__} per tabella '{self._table_name}'")

    def _get_default_db_path(self) -> str:
        """Restituisce percorso database di default"""
        if self.project_id:
            return f"db_memoria/project_{self.project_id}.sqlite"
        return "db_memoria/metadata.sqlite"

    @abstractmethod
    def _get_table_name(self) -> str:
        """Restituisce nome tabella gestita dal repository"""
        pass

    @property
    def connection(self) -> sqlite3.Connection:
        """Restituisce connessione database (lazy initialization)"""
        if self._connection is None:
            try:
                os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
                self._connection = sqlite3.connect(self.db_path)
                self._connection.row_factory = sqlite3.Row
                logger.debug(f"Connessione database stabilita: {self.db_path}")
            except sqlite3.Error as e:
                logger.error(f"Errore connessione database: {e}")
                raise DatabaseConnectionError(f"Impossibile connettersi al database: {e}")
        return self._connection

    def close_connection(self):
        """Chiude connessione database"""
        if self._connection:
            try:
                self._connection.close()
                logger.debug("Connessione database chiusa")
            except sqlite3.Error as e:
                logger.warning(f"Errore chiusura connessione: {e}")
            finally:
                self._connection = None

    def execute_query(self, query: str, parameters: tuple = None,
                     fetch: str = 'none') -> Union[List[Dict], Dict, None]:
        """
        Esegue query SQL con gestione errori standardizzata.

        Args:
            query: Query SQL da eseguire
            parameters: Parametri query
            fetch: Tipo fetch ('none', 'one', 'all')

        Returns:
            Risultato query basato su fetch type
        """
        try:
            with self.connection as conn:
                cursor = conn.cursor()
                logger.debug(f"Eseguo query: {query[:100]}{'...' if len(query) > 100 else ''}")

                if parameters:
                    cursor.execute(query, parameters)
                else:
                    cursor.execute(query)

                if fetch == 'all':
                    result = [dict(row) for row in cursor.fetchall()]
                    logger.debug(f"Query restituita {len(result)} righe")
                    return result
                elif fetch == 'one':
                    result = cursor.fetchone()
                    return dict(result) if result else None
                else:
                    conn.commit()
                    logger.debug("Query eseguita con successo")

        except sqlite3.Error as e:
            logger.error(f"Errore esecuzione query: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Parametri: {parameters}")
            raise DatabaseOperationError(f"Errore operazione database: {e}")

    def execute_many(self, query: str, parameters_list: List[tuple]) -> int:
        """
        Esegue multiple operazioni con stessa query.

        Args:
            query: Query SQL da eseguire
            parameters_list: Lista parametri per ogni esecuzione

        Returns:
            Numero righe inserite/aggiornate
        """
        try:
            with self.connection as conn:
                cursor = conn.cursor()
                logger.debug(f"Eseguo batch query: {query[:100]}{'...' if len(query) > 100 else ''}")
                logger.debug(f"Batch size: {len(parameters_list)}")

                cursor.executemany(query, parameters_list)
                conn.commit()

                affected_rows = cursor.rowcount
                logger.info(f"Batch eseguito con successo: {affected_rows} righe interessate")
                return affected_rows

        except sqlite3.Error as e:
            logger.error(f"Errore esecuzione batch: {e}")
            raise DatabaseOperationError(f"Errore operazione batch: {e}")

    # Operazioni CRUD standardizzate

    def create(self, data: Dict[str, Any]) -> int:
        """
        Crea nuovo record nella tabella.

        Args:
            data: Dati da inserire

        Returns:
            ID record creato
        """
        # Validazione dati
        self._validate_create_data(data)

        # Prepara query
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        values = tuple(data.values())

        query = f"INSERT INTO {self._table_name} ({columns}) VALUES ({placeholders})"

        try:
            self.execute_query(query, values)

            # Recupera ID generato
            last_id = self.execute_query(
                "SELECT last_insert_rowid() as id",
                fetch='one'
            )['id']

            logger.info(f"Record creato in {self._table_name} con ID: {last_id}")
            return last_id

        except sqlite3.IntegrityError as e:
            logger.error(f"Violazione integrità: {e}")
            raise DatabaseOperationError(f"Violazione integrità dati: {e}")

    def find_by_id(self, record_id: int) -> Optional[Dict]:
        """
        Trova record per ID.

        Args:
            record_id: ID record da cercare

        Returns:
            Record trovato o None
        """
        query = f"SELECT * FROM {self._table_name} WHERE id = ?"
        return self.execute_query(query, (record_id,), fetch='one')

    def find_by_criteria(self, criteria: Dict[str, Any],
                        order_by: str = None, limit: int = None) -> List[Dict]:
        """
        Trova record per criteri.

        Args:
            criteria: Criteri ricerca
            order_by: Ordinamento risultati
            limit: Limite risultati

        Returns:
            Lista record trovati
        """
        if not criteria:
            return self.find_all(order_by, limit)

        # Costruisci WHERE clause
        where_parts = []
        values = []
        for key, value in criteria.items():
            if isinstance(value, list):
                # Supporto IN clause
                placeholders = ','.join(['?' for _ in value])
                where_parts.append(f"{key} IN ({placeholders})")
                values.extend(value)
            else:
                where_parts.append(f"{key} = ?")
                values.append(value)

        where_clause = ' AND '.join(where_parts)
        query = f"SELECT * FROM {self._table_name} WHERE {where_clause}"

        if order_by:
            query += f" ORDER BY {order_by}"

        if limit:
            query += f" LIMIT {limit}"

        return self.execute_query(query, tuple(values), fetch='all')

    def find_all(self, order_by: str = None, limit: int = None) -> List[Dict]:
        """
        Trova tutti i record.

        Args:
            order_by: Ordinamento risultati
            limit: Limite risultati

        Returns:
            Lista tutti record
        """
        query = f"SELECT * FROM {self._table_name}"

        if order_by:
            query += f" ORDER BY {order_by}"

        if limit:
            query += f" LIMIT {limit}"

        return self.execute_query(query, fetch='all')

    def update(self, record_id: int, data: Dict[str, Any]) -> bool:
        """
        Aggiorna record esistente.

        Args:
            record_id: ID record da aggiornare
            data: Dati da aggiornare

        Returns:
            True se aggiornato con successo
        """
        # Validazione dati
        self._validate_update_data(data)

        if not data:
            logger.warning("Nessun dato da aggiornare")
            return False

        # Prepara query
        set_parts = ', '.join([f"{key} = ?" for key in data.keys()])
        values = tuple(data.values()) + (record_id,)

        query = f"UPDATE {self._table_name} SET {set_parts} WHERE id = ?"

        try:
            self.execute_query(query, values)
            logger.info(f"Record {record_id} aggiornato in {self._table_name}")
            return True
        except sqlite3.IntegrityError as e:
            logger.error(f"Violazione integrità update: {e}")
            raise DatabaseOperationError(f"Violazione integrità dati: {e}")

    def delete(self, record_id: int) -> bool:
        """
        Elimina record per ID.

        Args:
            record_id: ID record da eliminare

        Returns:
            True se eliminato con successo
        """
        query = f"DELETE FROM {self._table_name} WHERE id = ?"
        self.execute_query(query, (record_id,))
        logger.info(f"Record {record_id} eliminato da {self._table_name}")
        return True

    def count(self, criteria: Dict[str, Any] = None) -> int:
        """
        Conta record per criteri.

        Args:
            criteria: Criteri filtro

        Returns:
            Numero record
        """
        if criteria:
            where_parts = []
            values = []
            for key, value in criteria.items():
                where_parts.append(f"{key} = ?")
                values.append(value)

            where_clause = ' AND '.join(where_parts)
            query = f"SELECT COUNT(*) as count FROM {self._table_name} WHERE {where_clause}"
            result = self.execute_query(query, tuple(values), fetch='one')
        else:
            query = f"SELECT COUNT(*) as count FROM {self._table_name}"
            result = self.execute_query(query, fetch='one')

        return result['count']

    def exists(self, record_id: int) -> bool:
        """
        Verifica esistenza record.

        Args:
            record_id: ID da verificare

        Returns:
            True se esiste
        """
        query = f"SELECT 1 FROM {self._table_name} WHERE id = ? LIMIT 1"
        result = self.execute_query(query, (record_id,), fetch='one')
        return result is not None

    # Metodi validazione (da override nei repository specifici)

    def _validate_create_data(self, data: Dict[str, Any]):
        """Validazione dati creazione (da override)"""
        if not data:
            raise ValueError("Dati creazione vuoti")

    def _validate_update_data(self, data: Dict[str, Any]):
        """Validazione dati aggiornamento (da override)"""
        if not data:
            raise ValueError("Dati aggiornamento vuoti")

    # Utility methods

    def get_column_names(self) -> List[str]:
        """Restituisce nomi colonne tabella"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"PRAGMA table_info({self._table_name})")
            columns = cursor.fetchall()
            return [col['name'] for col in columns]
        except sqlite3.Error as e:
            logger.error(f"Errore recupero colonne: {e}")
            return []

    def backup_table(self, backup_suffix: str = None) -> str:
        """
        Crea backup tabella.

        Args:
            backup_suffix: Suffisso nome backup

        Returns:
            Nome tabella backup
        """
        if backup_suffix is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_suffix = f"backup_{timestamp}"

        backup_table = f"{self._table_name}_{backup_suffix}"

        try:
            query = f"CREATE TABLE {backup_table} AS SELECT * FROM {self._table_name}"
            self.execute_query(query)
            logger.info(f"Backup creato: {backup_table}")
            return backup_table
        except sqlite3.Error as e:
            logger.error(f"Errore creazione backup: {e}")
            raise DatabaseOperationError(f"Errore backup tabella: {e}")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close_connection()

    def __del__(self):
        """Destructor - cleanup connessione"""
        self.close_connection()
