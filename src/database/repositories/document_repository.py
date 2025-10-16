"""
Document repository implementation.
Handles document-specific database operations with advanced querying.
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from .base_repository import BaseRepository, DatabaseOperationError
from ..models.base import Document, ProcessingStatus


class DocumentRepository(BaseRepository[Document]):
    """Repository per operazioni documenti."""

    def __init__(self, db_path: str):
        """Inizializza document repository."""
        super().__init__(db_path, "documents")

    @property
    def table_fields(self) -> List[str]:
        """Campi tabella documenti."""
        return [
            'id', 'project_id', 'file_name', 'title', 'content_hash',
            'file_size', 'mime_type', 'processing_status', 'formatted_preview',
            'keywords', 'ai_tasks', 'created_by', 'created_at', 'updated_at'
        ]

    @property
    def primary_key(self) -> str:
        """Chiave primaria documenti."""
        return 'id'

    def to_dict(self, entity: Document) -> Dict[str, Any]:
        """Converte documento in dizionario."""
        return {
            'id': entity.id,
            'project_id': entity.project_id,
            'file_name': entity.file_name,
            'title': entity.title,
            'content_hash': entity.content_hash,
            'file_size': entity.file_size,
            'mime_type': entity.mime_type,
            'processing_status': entity.processing_status.value if hasattr(entity.processing_status, 'value') else entity.processing_status,
            'formatted_preview': entity.formatted_preview,
            'keywords': json.dumps(entity.keywords) if entity.keywords else None,
            'ai_tasks': json.dumps(entity.ai_tasks) if entity.ai_tasks else None,
            'created_by': entity.created_by,
            'created_at': entity.created_at,
            'updated_at': entity.updated_at
        }

    def from_dict(self, data: Dict[str, Any]) -> Document:
        """Converte dizionario in documento."""
        return Document(
            id=data.get('id'),
            project_id=data.get('project_id', ''),
            file_name=data.get('file_name', ''),
            title=data.get('title'),
            content_hash=data.get('content_hash'),
            file_size=data.get('file_size'),
            mime_type=data.get('mime_type'),
            processing_status=self._parse_processing_status(data.get('processing_status')),
            formatted_preview=data.get('formatted_preview'),
            keywords=json.loads(data.get('keywords', '[]') or '[]'),
            ai_tasks=json.loads(data.get('ai_tasks', '{}') or '{}'),
            created_by=data.get('created_by'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

    def _parse_processing_status(self, status: Any) -> ProcessingStatus:
        """Converte valore status in enum."""
        if isinstance(status, str):
            try:
                return ProcessingStatus(status)
            except ValueError:
                return ProcessingStatus.PENDING
        return ProcessingStatus.PENDING

    def get_by_file_name(self, file_name: str) -> Optional[Document]:
        """Recupera documento per nome file.

        Args:
            file_name: Nome file da cercare

        Returns:
            Documento se trovato
        """
        return self.find_by_field('file_name', file_name)[0] if self.find_by_field('file_name', file_name) else None

    def get_by_content_hash(self, content_hash: str) -> List[Document]:
        """Recupera documenti per hash contenuto (deduplica).

        Args:
            content_hash: Hash contenuto da cercare

        Returns:
            Lista documenti con stesso hash
        """
        return self.find_by_field('content_hash', content_hash)

    def get_by_processing_status(self, status: ProcessingStatus) -> List[Document]:
        """Recupera documenti per status processamento.

        Args:
            status: Status da cercare

        Returns:
            Lista documenti con status specificato
        """
        status_value = status.value if hasattr(status, 'value') else status
        return self.find_by_field('processing_status', status_value)

    def get_pending_processing(self, limit: int = 100) -> List[Document]:
        """Recupera documenti in attesa di processamento.

        Args:
            limit: Numero massimo documenti

        Returns:
            Lista documenti pending
        """
        try:
            with self.get_connection() as conn:
                placeholders = ', '.join(['?' for _ in self.table_fields])
                query = f"""
                    SELECT {placeholders} FROM {self.table_name}
                    WHERE processing_status = ?
                    ORDER BY created_at ASC
                    LIMIT ?
                """
                params = self.table_fields + [ProcessingStatus.PENDING.value, limit]

                cursor = conn.execute(query, params)
                rows = cursor.fetchall()

                return [self.from_dict(dict(row)) for row in rows]

        except Exception as e:
            self.logger.error(f"Errore recupero documenti pending: {e}")
            raise DatabaseOperationError(
                "Errore recupero documenti pending",
                "get_pending_processing",
                self.table_name
            )

    def get_by_user(self, user_id: int, project_id: str = None) -> List[Document]:
        """Recupera documenti per utente.

        Args:
            user_id: ID utente
            project_id: ID progetto (opzionale)

        Returns:
            Lista documenti utente
        """
        filters = {'created_by': user_id}
        if project_id:
            filters['project_id'] = project_id

        return self.get_all(filters)

    def get_by_project(self, project_id: str) -> List[Document]:
        """Recupera documenti per progetto.

        Args:
            project_id: ID progetto

        Returns:
            Lista documenti progetto
        """
        return self.get_all({'project_id': project_id})

    def search_by_content(self, query: str, project_id: str = None) -> List[Document]:
        """Cerca documenti per contenuto.

        Args:
            query: Testo da cercare
            project_id: ID progetto (opzionale)

        Returns:
            Lista documenti corrispondenti
        """
        try:
            with self.get_connection() as conn:
                base_query = """
                    SELECT * FROM documents
                    WHERE (title LIKE ? OR formatted_preview LIKE ?)
                """
                params = [f'%{query}%', f'%{query}%']

                if project_id:
                    base_query += " AND project_id = ?"
                    params.append(project_id)

                base_query += " ORDER BY updated_at DESC"

                cursor = conn.execute(base_query, params)
                rows = cursor.fetchall()

                return [self.from_dict(dict(row)) for row in rows]

        except Exception as e:
            self.logger.error(f"Errore ricerca contenuto: {e}")
            raise DatabaseOperationError(
                "Errore ricerca documenti",
                "search_by_content",
                self.table_name
            )

    def search_by_keywords(self, keywords: List[str], project_id: str = None) -> List[Document]:
        """Cerca documenti per parole chiave.

        Args:
            keywords: Lista parole chiave
            project_id: ID progetto (opzionale)

        Returns:
            Lista documenti corrispondenti
        """
        try:
            if not keywords:
                return []

            with self.get_connection() as conn:
                # Crea placeholders per keywords
                placeholders = ', '.join(['?' for _ in keywords])

                base_query = f"""
                    SELECT * FROM documents
                    WHERE keywords LIKE ?
                """
                params = [f'%{keywords[0]}%']

                # Aggiungi condizioni OR per altre keywords
                for keyword in keywords[1:]:
                    base_query += " OR keywords LIKE ?"
                    params.append(f'%{keyword}%')

                if project_id:
                    base_query += " AND project_id = ?"
                    params.append(project_id)

                base_query += " ORDER BY updated_at DESC"

                cursor = conn.execute(base_query, params)
                rows = cursor.fetchall()

                return [self.from_dict(dict(row)) for row in rows]

        except Exception as e:
            self.logger.error(f"Errore ricerca keywords: {e}")
            raise DatabaseOperationError(
                "Errore ricerca per keywords",
                "search_by_keywords",
                self.table_name
            )

    def get_recent_documents(self, project_id: str = None, limit: int = 10) -> List[Document]:
        """Recupera documenti recenti.

        Args:
            project_id: ID progetto (opzionale)
            limit: Numero massimo documenti

        Returns:
            Lista documenti recenti
        """
        try:
            with self.get_connection() as conn:
                placeholders = ', '.join(['?' for _ in self.table_fields])
                query = f"""
                    SELECT {placeholders} FROM {self.table_name}
                    WHERE processing_status = ?
                """
                params = self.table_fields + [ProcessingStatus.COMPLETED.value]

                if project_id:
                    query += " AND project_id = ?"
                    params.append(project_id)

                query += " ORDER BY updated_at DESC LIMIT ?"
                params.append(limit)

                cursor = conn.execute(query, params)
                rows = cursor.fetchall()

                return [self.from_dict(dict(row)) for row in rows]

        except Exception as e:
            self.logger.error(f"Errore recupero documenti recenti: {e}")
            raise DatabaseOperationError(
                "Errore recupero documenti recenti",
                "get_recent_documents",
                self.table_name
            )

    def get_documents_by_size_range(self, min_size: int, max_size: int, project_id: str = None) -> List[Document]:
        """Recupera documenti per range dimensione.

        Args:
            min_size: Dimensione minima (byte)
            max_size: Dimensione massima (byte)
            project_id: ID progetto (opzionale)

        Returns:
            Lista documenti nel range
        """
        filters = {
            'file_size': {
                'gte': min_size,
                'lte': max_size
            }
        }

        if project_id:
            filters['project_id'] = project_id

        return self.get_all(filters)

    def get_documents_by_date_range(self, start_date: str, end_date: str, project_id: str = None) -> List[Document]:
        """Recupera documenti per range date.

        Args:
            start_date: Data inizio (YYYY-MM-DD)
            end_date: Data fine (YYYY-MM-DD)
            project_id: ID progetto (opzionale)

        Returns:
            Lista documenti nel range date
        """
        filters = {
            'created_at': {
                'gte': start_date,
                'lte': end_date
            }
        }

        if project_id:
            filters['project_id'] = project_id

        return self.get_all(filters)

    def update_processing_status(self, document_id: int, status: ProcessingStatus, error_message: str = None) -> bool:
        """Aggiorna status processamento documento.

        Args:
            document_id: ID documento
            status: Nuovo status
            error_message: Messaggio errore (opzionale)

        Returns:
            True se aggiornamento riuscito
        """
        try:
            update_data = {
                'processing_status': status.value if hasattr(status, 'value') else status,
                'updated_at': datetime.utcnow()
            }

            if error_message:
                update_data['error_message'] = error_message

            # Crea entità temporanea per update
            temp_entity = Document(**update_data)
            return self.update(document_id, temp_entity)

        except Exception as e:
            self.logger.error(f"Errore aggiornamento status documento {document_id}: {e}")
            return False

    def bulk_update_status(self, document_ids: List[int], status: ProcessingStatus) -> int:
        """Aggiornamento bulk status documenti.

        Args:
            document_ids: Lista ID documenti
            status: Nuovo status

        Returns:
            Numero documenti aggiornati
        """
        if not document_ids:
            return 0

        try:
            status_value = status.value if hasattr(status, 'value') else status
            current_time = datetime.utcnow().isoformat()

            placeholders = ', '.join(['?' for _ in document_ids])
            query = f"""
                UPDATE {self.table_name}
                SET processing_status = ?, updated_at = ?
                WHERE id IN ({placeholders})
            """

            params = [status_value, current_time] + document_ids

            with self.get_connection() as conn:
                cursor = conn.execute(query, params)
                conn.commit()

                return cursor.rowcount

        except Exception as e:
            self.logger.error(f"Errore bulk update status: {e}")
            return 0

    def get_processing_stats(self, project_id: str = None) -> Dict[str, Any]:
        """Recupera statistiche processamento.

        Args:
            project_id: ID progetto (opzionale)

        Returns:
            Dizionario statistiche
        """
        try:
            with self.get_connection() as conn:
                base_query = """
                    SELECT
                        processing_status,
                        COUNT(*) as count,
                        AVG(file_size) as avg_size,
                        MIN(created_at) as first_created,
                        MAX(created_at) as last_created
                    FROM documents
                """
                params = []

                if project_id:
                    base_query += " WHERE project_id = ?"
                    params.append(project_id)

                base_query += " GROUP BY processing_status"

                cursor = conn.execute(base_query, params)
                rows = cursor.fetchall()

                stats = {
                    'total_documents': 0,
                    'by_status': {},
                    'total_size_bytes': 0,
                    'avg_size_bytes': 0,
                    'oldest_document': None,
                    'newest_document': None
                }

                for row in rows:
                    status = row['processing_status']
                    count = row['count']

                    stats['total_documents'] += count
                    stats['by_status'][status] = count

                    if row['first_created']:
                        if not stats['oldest_document'] or row['first_created'] < stats['oldest_document']:
                            stats['oldest_document'] = row['first_created']

                    if row['last_created']:
                        if not stats['newest_document'] or row['last_created'] > stats['newest_document']:
                            stats['newest_document'] = row['last_created']

                # Calcola dimensione totale e media
                if project_id:
                    size_query = "SELECT SUM(file_size), AVG(file_size) FROM documents WHERE project_id = ?"
                else:
                    size_query = "SELECT SUM(file_size), AVG(file_size) FROM documents"

                cursor = conn.execute(size_query, params)
                size_row = cursor.fetchone()

                stats['total_size_bytes'] = size_row[0] or 0
                stats['avg_size_bytes'] = size_row[1] or 0

                return stats

        except Exception as e:
            self.logger.error(f"Errore statistiche processamento: {e}")
            return {}

    def find_duplicates(self, project_id: str = None) -> List[Dict[str, Any]]:
        """Trova documenti duplicati per hash contenuto.

        Args:
            project_id: ID progetto (opzionale)

        Returns:
            Lista gruppi documenti duplicati
        """
        try:
            with self.get_connection() as conn:
                base_query = """
                    SELECT content_hash, COUNT(*) as duplicate_count, GROUP_CONCAT(file_name) as files
                    FROM documents
                    WHERE content_hash IS NOT NULL
                """
                params = []

                if project_id:
                    base_query += " AND project_id = ?"
                    params.append(project_id)

                base_query += """
                    GROUP BY content_hash
                    HAVING duplicate_count > 1
                    ORDER BY duplicate_count DESC
                """

                cursor = conn.execute(base_query, params)
                rows = cursor.fetchall()

                duplicates = []
                for row in rows:
                    files = row['files'].split(',')
                    duplicates.append({
                        'content_hash': row['content_hash'],
                        'duplicate_count': row['duplicate_count'],
                        'files': files
                    })

                return duplicates

        except Exception as e:
            self.logger.error(f"Errore ricerca duplicati: {e}")
            return []

    def get_documents_needing_reprocessing(self, max_retries: int = 3) -> List[Document]:
        """Recupera documenti che necessitano reprocessing.

        Args:
            max_retries: Numero massimo tentativi falliti

        Returns:
            Lista documenti da riprocessare
        """
        try:
            with self.get_connection() as conn:
                placeholders = ', '.join(['?' for _ in self.table_fields])
                query = f"""
                    SELECT {placeholders} FROM {self.table_name}
                    WHERE processing_status IN (?, ?)
                    AND retry_count < ?
                    ORDER BY updated_at ASC
                """
                params = self.table_fields + [
                    ProcessingStatus.FAILED.value,
                    ProcessingStatus.PENDING.value,
                    max_retries
                ]

                cursor = conn.execute(query, params)
                rows = cursor.fetchall()

                return [self.from_dict(dict(row)) for row in rows]

        except Exception as e:
            self.logger.error(f"Errore documenti da riprocessare: {e}")
            return []

    def cleanup_old_processing_logs(self, days_old: int = 30) -> int:
        """Pulisce log processamento vecchi.

        Args:
            days_old: Giorni dopo cui considerare vecchi

        Returns:
            Numero record eliminati
        """
        try:
            cutoff_date = datetime.utcnow().replace(
                day=datetime.utcnow().day - days_old
            ).isoformat()

            query = """
                DELETE FROM document_processing_status
                WHERE updated_at < ?
                AND processing_state IN ('completed', 'failed')
            """

            with self.get_connection() as conn:
                cursor = conn.execute(query, (cutoff_date,))
                deleted_count = cursor.rowcount
                conn.commit()

                self.logger.info(f"Puliti {deleted_count} log processamento vecchi")
                return deleted_count

        except Exception as e:
            self.logger.error(f"Errore pulizia log vecchi: {e}")
            return 0

    def get_storage_summary(self, project_id: str = None) -> Dict[str, Any]:
        """Recupera summary utilizzo storage.

        Args:
            project_id: ID progetto (opzionale)

        Returns:
            Dizionario summary storage
        """
        try:
            with self.get_connection() as conn:
                base_query = """
                    SELECT
                        COUNT(*) as total_files,
                        SUM(file_size) as total_bytes,
                        AVG(file_size) as avg_file_size,
                        MIN(file_size) as min_file_size,
                        MAX(file_size) as max_file_size,
                        COUNT(DISTINCT mime_type) as unique_types,
                        COUNT(CASE WHEN processing_status = 'completed' THEN 1 END) as processed_files
                    FROM documents
                """
                params = []

                if project_id:
                    base_query += " WHERE project_id = ?"
                    params.append(project_id)

                cursor = conn.execute(base_query, params)
                row = cursor.fetchone()

                if not row:
                    return {}

                return {
                    'total_files': row['total_files'] or 0,
                    'total_bytes': row['total_bytes'] or 0,
                    'total_mb': (row['total_bytes'] or 0) / (1024 * 1024),
                    'avg_file_size_bytes': row['avg_file_size'] or 0,
                    'min_file_size_bytes': row['min_file_size'] or 0,
                    'max_file_size_bytes': row['max_file_size'] or 0,
                    'unique_mime_types': row['unique_types'] or 0,
                    'processed_files': row['processed_files'] or 0,
                    'processing_ratio': (row['processed_files'] or 0) / (row['total_files'] or 1)
                }

        except Exception as e:
            self.logger.error(f"Errore summary storage: {e}")
            return {}

    def get_advanced_search(
        self,
        query: str = None,
        project_id: str = None,
        status: ProcessingStatus = None,
        mime_types: List[str] = None,
        date_from: str = None,
        date_to: str = None,
        size_min: int = None,
        size_max: int = None,
        has_keywords: bool = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Ricerca avanzata documenti con filtri multipli.

        Args:
            query: Testo da cercare
            project_id: ID progetto
            status: Status processamento
            mime_types: Lista tipi MIME
            date_from: Data inizio (YYYY-MM-DD)
            date_to: Data fine (YYYY-MM-DD)
            size_min: Dimensione minima (byte)
            size_max: Dimensione massima (byte)
            has_keywords: Flag presenza keywords
            limit: Limite risultati
            offset: Offset risultati

        Returns:
            Dizionario risultati ricerca
        """
        try:
            with self.get_connection() as conn:
                # Query base
                query_parts = ["SELECT * FROM documents WHERE 1=1"]
                params = []

                # Filtro testo
                if query:
                    query_parts.append("(title LIKE ? OR formatted_preview LIKE ?)")
                    params.extend([f'%{query}%', f'%{query}%'])

                # Filtro progetto
                if project_id:
                    query_parts.append("project_id = ?")
                    params.append(project_id)

                # Filtro status
                if status:
                    status_value = status.value if hasattr(status, 'value') else status
                    query_parts.append("processing_status = ?")
                    params.append(status_value)

                # Filtro tipi MIME
                if mime_types:
                    placeholders = ', '.join(['?' for _ in mime_types])
                    query_parts.append(f"mime_type IN ({placeholders})")
                    params.extend(mime_types)

                # Filtro date
                if date_from:
                    query_parts.append("created_at >= ?")
                    params.append(date_from)

                if date_to:
                    query_parts.append("created_at <= ?")
                    params.append(date_to)

                # Filtro dimensione
                if size_min is not None:
                    query_parts.append("file_size >= ?")
                    params.append(size_min)

                if size_max is not None:
                    query_parts.append("file_size <= ?")
                    params.append(size_max)

                # Filtro keywords
                if has_keywords:
                    query_parts.append("keywords IS NOT NULL AND keywords != '[]'")

                # Ordinamento e paginazione
                query_parts.append("ORDER BY updated_at DESC LIMIT ? OFFSET ?")
                params.extend([limit, offset])

                # Conta totale
                count_query = "SELECT COUNT(*) FROM documents WHERE 1=1"
                count_conditions = query_parts[1:-2]  # Escludi ORDER BY e LIMIT/OFFSET
                if count_conditions:
                    count_query += " AND " + " AND ".join(count_conditions)

                cursor = conn.execute(count_query, params[:-2])  # Escludi limit/offset
                total_count = cursor.fetchone()[0]

                # Esegui query principale
                full_query = " ".join(query_parts)
                cursor = conn.execute(full_query, params)
                rows = cursor.fetchall()

                documents = [self.from_dict(dict(row)) for row in rows]

                return {
                    'documents': documents,
                    'total_count': total_count,
                    'returned_count': len(documents),
                    'has_more': offset + limit < total_count,
                    'query_time_ms': 0  # Potrebbe essere misurato
                }

        except Exception as e:
            self.logger.error(f"Errore ricerca avanzata: {e}")
            raise DatabaseOperationError(
                "Errore ricerca avanzata documenti",
                "get_advanced_search",
                self.table_name
            )

    def increment_retry_count(self, document_id: int) -> bool:
        """Incrementa contatore retry documento.

        Args:
            document_id: ID documento

        Returns:
            True se incremento riuscito
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    UPDATE documents
                    SET retry_count = COALESCE(retry_count, 0) + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (document_id,))

                conn.commit()
                return cursor.rowcount > 0

        except Exception as e:
            self.logger.error(f"Errore incremento retry documento {document_id}: {e}")
            return False

    def get_documents_by_similarity(self, content_hash: str, threshold: float = 0.8) -> List[Document]:
        """Recupera documenti simili per hash contenuto.

        Args:
            content_hash: Hash contenuto di riferimento
            threshold: Soglia similarità

        Returns:
            Lista documenti simili
        """
        # Questa è una implementazione semplificata
        # In produzione potresti voler usare algoritmi più sofisticati
        return self.get_by_content_hash(content_hash)

    def archive_old_documents(self, days_old: int = 365, project_id: str = None) -> int:
        """Archivia documenti vecchi cambiando status.

        Args:
            days_old: Giorni dopo cui considerare vecchi
            project_id: ID progetto (opzionale)

        Returns:
            Numero documenti archiviati
        """
        try:
            cutoff_date = datetime.utcnow().replace(
                day=datetime.utcnow().day - days_old
            ).isoformat()

            query = """
                UPDATE documents
                SET processing_status = 'archived', updated_at = CURRENT_TIMESTAMP
                WHERE created_at < ?
                AND processing_status = 'completed'
            """
            params = [cutoff_date]

            if project_id:
                query += " AND project_id = ?"
                params.append(project_id)

            with self.get_connection() as conn:
                cursor = conn.execute(query, params)
                archived_count = cursor.rowcount
                conn.commit()

                self.logger.info(f"Archiviati {archived_count} documenti vecchi")
                return archived_count

        except Exception as e:
            self.logger.error(f"Errore archiviazione documenti vecchi: {e}")
            return 0
