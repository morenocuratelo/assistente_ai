"""
Base repository pattern implementation.
Provides common CRUD operations and database connection management.
"""

import sqlite3
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, TypeVar, Generic, Union
from datetime import datetime
from contextlib import contextmanager

from ..models.base import BaseEntity


T = TypeVar('T', bound=BaseEntity)


class DatabaseOperationError(Exception):
    """Eccezione per errori operazioni database."""

    def __init__(self, message: str, operation: str, table: str = None):
        super().__init__(message)
        self.operation = operation
        self.table = table


class BaseRepository(Generic[T], ABC):
    """Repository base astratto per operazioni CRUD."""

    def __init__(self, db_path: str, table_name: str):
        """Inizializza repository base.

        Args:
            db_path: Percorso database SQLite
            table_name: Nome tabella principale
        """
        self.db_path = db_path
        self.table_name = table_name
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

    @property
    @abstractmethod
    def table_fields(self) -> List[str]:
        """Campi tabella per operazioni CRUD."""
        pass

    @property
    @abstractmethod
    def primary_key(self) -> str:
        """Chiave primaria tabella."""
        pass

    @abstractmethod
    def to_dict(self, entity: T) -> Dict[str, Any]:
        """Converte entità in dizionario per database."""
        pass

    @abstractmethod
    def from_dict(self, data: Dict[str, Any]) -> T:
        """Converte dizionario database in entità."""
        pass

    @contextmanager
    def get_connection(self):
        """Context manager per connessione database."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def get_by_id(self, entity_id: Union[int, str]) -> Optional[T]:
        """Recupera entità per ID.

        Args:
            entity_id: ID entità da recuperare

        Returns:
            Entità se trovata, None altrimenti
        """
        try:
            with self.get_connection() as conn:
                placeholders = ', '.join(['?' for _ in self.table_fields])
                query = f"""
                    SELECT {placeholders} FROM {self.table_name}
                    WHERE {self.primary_key} = ?
                """

                cursor = conn.execute(query, (*self.table_fields, entity_id))
                row = cursor.fetchone()

                if row:
                    return self.from_dict(dict(row))
                return None

        except Exception as e:
            self.logger.error(f"Errore recupero per ID {entity_id}: {e}")
            raise DatabaseOperationError(
                f"Errore recupero {self.table_name}",
                "get_by_id",
                self.table_name
            )

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[T]:
        """Recupera tutte le entità con filtri opzionali.

        Args:
            filters: Filtri da applicare

        Returns:
            Lista entità
        """
        try:
            with self.get_connection() as conn:
                placeholders = ', '.join(['?' for _ in self.table_fields])
                query = f"SELECT {placeholders} FROM {self.table_name}"
                params = list(self.table_fields)

                where_clause, filter_params = self._build_where_clause(filters or {})
                if where_clause:
                    query += f" WHERE {where_clause}"
                    params.extend(filter_params)

                cursor = conn.execute(query, params)
                rows = cursor.fetchall()

                return [self.from_dict(dict(row)) for row in rows]

        except Exception as e:
            self.logger.error(f"Errore recupero tutti: {e}")
            raise DatabaseOperationError(
                f"Errore recupero {self.table_name}",
                "get_all",
                self.table_name
            )

    def create(self, entity: T) -> T:
        """Crea nuova entità.

        Args:
            entity: Entità da creare

        Returns:
            Entità creata con ID assegnato
        """
        try:
            entity_dict = self.to_dict(entity)

            # Rimuovi campi auto-generati
            fields_to_insert = [f for f in self.table_fields if f != self.primary_key and f in entity_dict]
            values = [entity_dict[f] for f in fields_to_insert]

            placeholders = ', '.join(['?' for _ in values])
            columns = ', '.join(fields_to_insert)

            query = f"""
                INSERT INTO {self.table_name} ({columns})
                VALUES ({placeholders})
            """

            with self.get_connection() as conn:
                cursor = conn.execute(query, values)
                conn.commit()

                # Recupera ID generato
                if self.primary_key == 'id':
                    generated_id = cursor.lastrowid
                    entity.id = generated_id

                return entity

        except Exception as e:
            self.logger.error(f"Errore creazione: {e}")
            raise DatabaseOperationError(
                f"Errore creazione {self.table_name}",
                "create",
                self.table_name
            )

    def update(self, entity_id: Union[int, str], entity: T) -> bool:
        """Aggiorna entità esistente.

        Args:
            entity_id: ID entità da aggiornare
            entity: Nuovi dati entità

        Returns:
            True se aggiornamento riuscito
        """
        try:
            entity_dict = self.to_dict(entity)

            # Crea clausola SET escludendo chiave primaria e campi auto
            set_fields = []
            values = []

            for field in self.table_fields:
                if field != self.primary_key and field in entity_dict:
                    set_fields.append(f"{field} = ?")
                    values.append(entity_dict[field])

            if not set_fields:
                return False

            # Aggiungi ID per WHERE
            values.append(entity_id)

            set_clause = ', '.join(set_fields)
            query = f"""
                UPDATE {self.table_name}
                SET {set_clause}
                WHERE {self.primary_key} = ?
            """

            with self.get_connection() as conn:
                cursor = conn.execute(query, values)
                conn.commit()

                return cursor.rowcount > 0

        except Exception as e:
            self.logger.error(f"Errore aggiornamento ID {entity_id}: {e}")
            raise DatabaseOperationError(
                f"Errore aggiornamento {self.table_name}",
                "update",
                self.table_name
            )

    def delete(self, entity_id: Union[int, str]) -> bool:
        """Elimina entità.

        Args:
            entity_id: ID entità da eliminare

        Returns:
            True se eliminazione riuscita
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    f"DELETE FROM {self.table_name} WHERE {self.primary_key} = ?",
                    (entity_id,)
                )
                conn.commit()

                return cursor.rowcount > 0

        except Exception as e:
            self.logger.error(f"Errore eliminazione ID {entity_id}: {e}")
            raise DatabaseOperationError(
                f"Errore eliminazione {self.table_name}",
                "delete",
                self.table_name
            )

    def exists(self, entity_id: Union[int, str]) -> bool:
        """Verifica esistenza entità.

        Args:
            entity_id: ID da verificare

        Returns:
            True se entità esiste
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    f"SELECT 1 FROM {self.table_name} WHERE {self.primary_key} = ?",
                    (entity_id,)
                )
                return cursor.fetchone() is not None

        except Exception as e:
            self.logger.error(f"Errore verifica esistenza ID {entity_id}: {e}")
            return False

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Conta entità con filtri opzionali.

        Args:
            filters: Filtri da applicare

        Returns:
            Numero entità
        """
        try:
            with self.get_connection() as conn:
                query = f"SELECT COUNT(*) FROM {self.table_name}"
                params = []

                where_clause, filter_params = self._build_where_clause(filters or {})
                if where_clause:
                    query += f" WHERE {where_clause}"
                    params.extend(filter_params)

                cursor = conn.execute(query, params)
                return cursor.fetchone()[0]

        except Exception as e:
            self.logger.error(f"Errore conteggio: {e}")
            raise DatabaseOperationError(
                f"Errore conteggio {self.table_name}",
                "count",
                self.table_name
            )

    def _build_where_clause(self, filters: Dict[str, Any]) -> tuple[str, List[Any]]:
        """Costruisce clausola WHERE da filtri.

        Args:
            filters: Dizionario filtri

        Returns:
            Tupla (where_clause, params)
        """
        if not filters:
            return "", []

        conditions = []
        params = []

        for field, value in filters.items():
            if field in self.table_fields:
                if isinstance(value, list):
                    # IN clause per liste
                    placeholders = ', '.join(['?' for _ in value])
                    conditions.append(f"{field} IN ({placeholders})")
                    params.extend(value)
                elif isinstance(value, dict):
                    # Range queries
                    if 'gte' in value:
                        conditions.append(f"{field} >= ?")
                        params.append(value['gte'])
                    if 'lte' in value:
                        conditions.append(f"{field} <= ?")
                        params.append(value['lte'])
                    if 'gt' in value:
                        conditions.append(f"{field} > ?")
                        params.append(value['gt'])
                    if 'lt' in value:
                        conditions.append(f"{field} < ?")
                        params.append(value['lt'])
                else:
                    # Simple equality
                    conditions.append(f"{field} = ?")
                    params.append(value)

        return " AND ".join(conditions), params

    def bulk_insert(self, entities: List[T]) -> int:
        """Inserimento bulk entità.

        Args:
            entities: Lista entità da inserire

        Returns:
            Numero righe inserite
        """
        if not entities:
            return 0

        try:
            with self.get_connection() as conn:
                # Prepara dati per inserimento bulk
                all_values = []
                for entity in entities:
                    entity_dict = self.to_dict(entity)
                    values = [entity_dict.get(f) for f in self.table_fields if f != self.primary_key]
                    all_values.append(values)

                # Crea query bulk
                placeholders = ', '.join(['?' for _ in self.table_fields if self.table_fields != self.primary_key])
                columns = ', '.join([f for f in self.table_fields if f != self.primary_key])

                query = f"""
                    INSERT INTO {self.table_name} ({columns})
                    VALUES ({placeholders})
                """

                cursor = conn.executemany(query, all_values)
                conn.commit()

                return cursor.rowcount

        except Exception as e:
            self.logger.error(f"Errore inserimento bulk: {e}")
            raise DatabaseOperationError(
                f"Errore inserimento bulk {self.table_name}",
                "bulk_insert",
                self.table_name
            )

    def upsert(self, entity: T, conflict_fields: List[str]) -> T:
        """Inserisci o aggiorna entità (UPSERT).

        Args:
            entity: Entità da inserire/aggiornare
            conflict_fields: Campi per conflitto

        Returns:
            Entità inserita/aggiornata
        """
        try:
            entity_dict = self.to_dict(entity)

            # Campi per INSERT
            insert_fields = [f for f in self.table_fields if f != self.primary_key and f in entity_dict]
            insert_values = [entity_dict[f] for f in insert_fields]

            # Campi per UPDATE (escludendo chiave primaria)
            update_fields = [f for f in insert_fields if f not in conflict_fields]

            # Costruisci query UPSERT
            placeholders = ', '.join(['?' for _ in insert_values])
            columns = ', '.join(insert_fields)

            set_clause = ', '.join([f"{f} = ?" for f in update_fields])
            update_values = [entity_dict[f] for f in update_fields]

            all_values = insert_values + update_values

            query = f"""
                INSERT INTO {self.table_name} ({columns})
                VALUES ({placeholders})
                ON CONFLICT ({', '.join(conflict_fields)})
                DO UPDATE SET {set_clause}
            """

            with self.get_connection() as conn:
                cursor = conn.execute(query, all_values)
                conn.commit()

                # Se è un INSERT, recupera ID generato
                if cursor.rowcount > 0 and self.primary_key == 'id':
                    entity.id = cursor.lastrowid

                return entity

        except Exception as e:
            self.logger.error(f"Errore upsert: {e}")
            raise DatabaseOperationError(
                f"Errore upsert {self.table_name}",
                "upsert",
                self.table_name
            )

    def find_by_field(self, field: str, value: Any) -> List[T]:
        """Trova entità per campo specifico.

        Args:
            field: Nome campo
            value: Valore da cercare

        Returns:
            Lista entità corrispondenti
        """
        if field not in self.table_fields:
            raise ValueError(f"Campo {field} non valido per tabella {self.table_name}")

        return self.get_all({field: value})

    def get_paginated(
        self,
        page: int = 1,
        per_page: int = 50,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Recupera entità paginate.

        Args:
            page: Numero pagina (1-based)
            per_page: Elementi per pagina
            filters: Filtri da applicare
            order_by: Campo ordinamento

        Returns:
            Dizionario con elementi e metadati paginazione
        """
        try:
            offset = (page - 1) * per_page

            with self.get_connection() as conn:
                # Conta totale
                total_count = self.count(filters)

                # Query elementi
                placeholders = ', '.join(['?' for _ in self.table_fields])
                query = f"SELECT {placeholders} FROM {self.table_name}"
                params = list(self.table_fields)

                where_clause, filter_params = self._build_where_clause(filters or {})
                if where_clause:
                    query += f" WHERE {where_clause}"
                    params.extend(filter_params)

                if order_by and order_by in self.table_fields:
                    query += f" ORDER BY {order_by}"

                query += " LIMIT ? OFFSET ?"
                params.extend([per_page, offset])

                cursor = conn.execute(query, params)
                rows = cursor.fetchall()

                entities = [self.from_dict(dict(row)) for row in rows]

                return {
                    'items': entities,
                    'total': total_count,
                    'page': page,
                    'per_page': per_page,
                    'pages': (total_count + per_page - 1) // per_page,
                    'has_next': page * per_page < total_count,
                    'has_prev': page > 1
                }

        except Exception as e:
            self.logger.error(f"Errore paginazione: {e}")
            raise DatabaseOperationError(
                f"Errore paginazione {self.table_name}",
                "get_paginated",
                self.table_name
            )

    def execute_raw_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Esegue query raw e restituisce risultati.

        Args:
            query: Query SQL
            params: Parametri query

        Returns:
            Lista risultati
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]

        except Exception as e:
            self.logger.error(f"Errore query raw: {e}")
            raise DatabaseOperationError(
                f"Errore query raw {self.table_name}",
                "execute_raw_query",
                self.table_name
            )

    def get_table_info(self) -> List[Dict[str, Any]]:
        """Recupera informazioni schema tabella.

        Returns:
            Lista informazioni colonne
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(f"PRAGMA table_info({self.table_name})")
                columns = cursor.fetchall()
                return [dict(col) for col in columns]

        except Exception as e:
            self.logger.error(f"Errore info tabella: {e}")
            return []

    def create_index(self, index_name: str, columns: List[str], unique: bool = False) -> bool:
        """Crea indice su tabella.

        Args:
            index_name: Nome indice
            columns: Colonne da indicizzare
            unique: Indice univoco

        Returns:
            True se creazione riuscita
        """
        try:
            if not all(col in self.table_fields for col in columns):
                raise ValueError("Alcune colonne non esistono nella tabella")

            unique_str = "UNIQUE" if unique else ""
            columns_str = ', '.join(columns)

            query = f"""
                CREATE {unique_str} INDEX IF NOT EXISTS {index_name}
                ON {self.table_name} ({columns_str})
            """

            with self.get_connection() as conn:
                conn.execute(query)
                conn.commit()

            self.logger.info(f"Indice {index_name} creato su {self.table_name}")
            return True

        except Exception as e:
            self.logger.error(f"Errore creazione indice {index_name}: {e}")
            return False

    def drop_index(self, index_name: str) -> bool:
        """Rimuove indice.

        Args:
            index_name: Nome indice da rimuovere

        Returns:
            True se rimozione riuscita
        """
        try:
            with self.get_connection() as conn:
                conn.execute(f"DROP INDEX IF EXISTS {index_name}")
                conn.commit()

            self.logger.info(f"Indice {index_name} rimosso")
            return True

        except Exception as e:
            self.logger.error(f"Errore rimozione indice {index_name}: {e}")
            return False

    def vacuum(self) -> bool:
        """Ottimizza database (VACUUM).

        Returns:
            True se ottimizzazione riuscita
        """
        try:
            with self.get_connection() as conn:
                conn.execute("VACUUM")
                conn.commit()

            self.logger.info("Database ottimizzato con VACUUM")
            return True

        except Exception as e:
            self.logger.error(f"Errore VACUUM: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Recupera statistiche tabella.

        Returns:
            Dizionario statistiche
        """
        try:
            with self.get_connection() as conn:
                # Conta righe
                cursor = conn.execute(f"SELECT COUNT(*) FROM {self.table_name}")
                row_count = cursor.fetchone()[0]

                # Info tabella
                table_info = self.get_table_info()

                # Ultima modifica
                cursor = conn.execute(
                    f"SELECT MAX(created_at), MAX(updated_at) FROM {self.table_name}"
                )
                timestamps = cursor.fetchone()

                return {
                    'table_name': self.table_name,
                    'row_count': row_count,
                    'columns': len(table_info),
                    'last_created': timestamps[0] if timestamps[0] else None,
                    'last_updated': timestamps[1] if timestamps[1] else None,
                    'columns_info': table_info
                }

        except Exception as e:
            self.logger.error(f"Errore statistiche tabella: {e}")
            return {}
