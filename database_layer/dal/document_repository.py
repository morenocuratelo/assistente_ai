# Document Repository - Gestione documenti e papers
"""
Repository specializzato per la gestione dei documenti nell'archivio.

Gestisce la tabella 'papers' che contiene:
- Metadati documenti (titolo, autori, anno, categoria)
- Anteprime generate dall'AI
- Informazioni processamento
- Associazioni materiali accademici
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from .base_repository import BaseRepository, DatabaseOperationError

logger = logging.getLogger('DocumentRepository')

class DocumentRepository(BaseRepository):
    """
    Repository per gestione documenti papers.

    Fornisce operazioni specializzate per documenti con supporto
    per ricerca avanzata e gestione metadati.
    """

    def _get_table_name(self) -> str:
        """Restituisce nome tabella documenti"""
        return 'papers'

    def _validate_create_data(self, data: Dict[str, Any]):
        """Validazione dati creazione documento"""
        super()._validate_create_data(data)

        required_fields = ['file_name']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Campo obbligatorio mancante: {field}")

        # Validazione nome file
        if not data['file_name'] or not data['file_name'].strip():
            raise ValueError("Nome file non può essere vuoto")

    def _validate_update_data(self, data: Dict[str, Any]):
        """Validazione dati aggiornamento documento"""
        super()._validate_update_data(data)

        # Validazione campi specifici se presenti
        if 'file_name' in data and not data['file_name'].strip():
            raise ValueError("Nome file non può essere vuoto")

    def find_by_file_name(self, file_name: str) -> Optional[Dict]:
        """
        Trova documento per nome file.

        Args:
            file_name: Nome file da cercare

        Returns:
            Documento trovato o None
        """
        query = "SELECT * FROM papers WHERE file_name = ?"
        return self.execute_query(query, (file_name,), fetch='one')

    def find_by_category(self, category_id: str, order_by: str = 'title') -> List[Dict]:
        """
        Trova documenti per categoria.

        Args:
            category_id: ID categoria
            order_by: Ordinamento risultati

        Returns:
            Lista documenti categoria
        """
        query = f"SELECT * FROM papers WHERE category_id = ? ORDER BY {order_by}"
        return self.execute_query(query, (category_id,), fetch='all')

    def find_by_author(self, author: str, limit: int = None) -> List[Dict]:
        """
        Trova documenti per autore.

        Args:
            author: Nome autore (ricerca parziale)
            limit: Limite risultati

        Returns:
            Lista documenti autore
        """
        query = "SELECT * FROM papers WHERE authors LIKE ? ORDER BY publication_year DESC, title"
        if limit:
            query += f" LIMIT {limit}"

        return self.execute_query(query, (f'%{author}%',), fetch='all')

    def find_by_year_range(self, start_year: int, end_year: int) -> List[Dict]:
        """
        Trova documenti per range anni.

        Args:
            start_year: Anno inizio
            end_year: Anno fine

        Returns:
            Lista documenti nel range
        """
        query = "SELECT * FROM papers WHERE publication_year BETWEEN ? AND ? ORDER BY publication_year DESC, title"
        return self.execute_query(query, (start_year, end_year), fetch='all')

    def search_documents(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Ricerca full-text nei documenti.

        Args:
            query: Testo da cercare
            limit: Limite risultati

        Returns:
            Lista documenti matching
        """
        search_terms = query.split()
        if not search_terms:
            return []

        # Costruisci query ricerca complessa
        where_conditions = []
        values = []

        for term in search_terms:
            term = f'%{term}%'
            where_conditions.append("""
                (title LIKE ? OR authors LIKE ? OR formatted_preview LIKE ? OR category_name LIKE ?)
            """)
            values.extend([term, term, term, term])

        where_clause = ' AND '.join(where_conditions)
        sql_query = f"""
            SELECT *,
                   CASE
                       WHEN title LIKE ? THEN 3
                       WHEN authors LIKE ? THEN 2
                       ELSE 1
                   END as relevance_score
            FROM papers
            WHERE {where_clause}
            ORDER BY relevance_score DESC, publication_year DESC
            LIMIT ?
        """

        # Aggiungi valori per score calculation
        score_values = [f'%{query}%', f'%{query}%']
        all_values = score_values + values + [limit]

        return self.execute_query(sql_query, tuple(all_values), fetch='all')

    def get_documents_with_preview(self) -> List[Dict]:
        """
        Recupera documenti con anteprima AI generata.

        Returns:
            Lista documenti con anteprima
        """
        query = "SELECT * FROM papers WHERE formatted_preview IS NOT NULL AND formatted_preview != '' ORDER BY processed_at DESC"
        return self.execute_query(query, fetch='all')

    def get_documents_without_preview(self) -> List[Dict]:
        """
        Recupera documenti senza anteprima AI.

        Returns:
            Lista documenti senza anteprima
        """
        query = "SELECT * FROM papers WHERE formatted_preview IS NULL OR formatted_preview = '' ORDER BY created_at ASC"
        return self.execute_query(query, fetch='all')

    def update_preview(self, file_name: str, preview_content: str) -> bool:
        """
        Aggiorna anteprima documento.

        Args:
            file_name: Nome file documento
            preview_content: Contenuto anteprima

        Returns:
            True se aggiornato con successo
        """
        update_data = {
            'formatted_preview': preview_content,
            'processed_at': datetime.now().isoformat()
        }

        try:
            # Verifica esistenza documento
            if not self.find_by_file_name(file_name):
                raise DatabaseOperationError(f"Documento non trovato: {file_name}")

            # Aggiorna
            with self.connection as conn:
                cursor = conn.cursor()
                set_parts = ', '.join([f"{key} = ?" for key in update_data.keys()])
                values = tuple(update_data.values()) + (file_name,)

                query = f"UPDATE papers SET {set_parts} WHERE file_name = ?"
                cursor.execute(query, values)
                conn.commit()

            logger.info(f"Anteprima aggiornata per documento: {file_name}")
            return True

        except Exception as e:
            logger.error(f"Errore aggiornamento anteprima: {e}")
            raise DatabaseOperationError(f"Errore aggiornamento anteprima: {e}")

    def update_metadata(self, file_name: str, metadata: Dict[str, Any]) -> bool:
        """
        Aggiorna metadati documento.

        Args:
            file_name: Nome file documento
            metadata: Metadati da aggiornare

        Returns:
            True se aggiornato con successo
        """
        # Validazione metadata
        allowed_fields = {
            'title', 'authors', 'publication_year', 'category_id',
            'category_name', 'keywords', 'ai_tasks'
        }

        filtered_metadata = {k: v for k, v in metadata.items() if k in allowed_fields}
        filtered_metadata['processed_at'] = datetime.now().isoformat()

        try:
            # Verifica esistenza documento
            if not self.find_by_file_name(file_name):
                raise DatabaseOperationError(f"Documento non trovato: {file_name}")

            # Aggiorna
            with self.connection as conn:
                cursor = conn.cursor()
                set_parts = ', '.join([f"{key} = ?" for key in filtered_metadata.keys()])
                values = tuple(filtered_metadata.values()) + (file_name,)

                query = f"UPDATE papers SET {set_parts} WHERE file_name = ?"
                cursor.execute(query, values)
                conn.commit()

            logger.info(f"Metadati aggiornati per documento: {file_name}")
            return True

        except Exception as e:
            logger.error(f"Errore aggiornamento metadati: {e}")
            raise DatabaseOperationError(f"Errore aggiornamento metadati: {e}")

    def delete_by_file_name(self, file_name: str) -> bool:
        """
        Elimina documento per nome file.

        Args:
            file_name: Nome file da eliminare

        Returns:
            True se eliminato con successo
        """
        try:
            # Verifica esistenza
            if not self.find_by_file_name(file_name):
                logger.warning(f"Tentativo eliminazione documento inesistente: {file_name}")
                return False

            # Elimina
            query = "DELETE FROM papers WHERE file_name = ?"
            self.execute_query(query, (file_name,))

            logger.info(f"Documento eliminato: {file_name}")
            return True

        except Exception as e:
            logger.error(f"Errore eliminazione documento: {e}")
            raise DatabaseOperationError(f"Errore eliminazione documento: {e}")

    def get_category_stats(self) -> List[Dict]:
        """
        Statistiche documenti per categoria.

        Returns:
            Lista statistiche categorie
        """
        query = """
            SELECT
                category_id,
                category_name,
                COUNT(*) as document_count,
                COUNT(formatted_preview) as preview_count,
                AVG(CASE WHEN publication_year IS NOT NULL THEN publication_year END) as avg_year
            FROM papers
            GROUP BY category_id, category_name
            ORDER BY document_count DESC
        """
        return self.execute_query(query, fetch='all')

    def get_author_stats(self) -> List[Dict]:
        """
        Statistiche documenti per autore.

        Returns:
            Lista statistiche autori
        """
        query = """
            SELECT
                authors,
                COUNT(*) as document_count,
                COUNT(DISTINCT category_name) as category_count,
                MIN(publication_year) as first_publication,
                MAX(publication_year) as last_publication
            FROM papers
            WHERE authors IS NOT NULL AND authors != ''
            GROUP BY authors
            HAVING document_count > 1
            ORDER BY document_count DESC
        """
        return self.execute_query(query, fetch='all')

    def cleanup_missing_files(self, archive_dir: str = "Dall_Origine_alla_Complessita") -> int:
        """
        Rimuove riferimenti a file inesistenti.

        Args:
            archive_dir: Directory archivio da verificare

        Returns:
            Numero file rimossi
        """
        try:
            # Recupera tutti i documenti
            documents = self.find_all()
            removed_count = 0

            for doc in documents:
                file_name = doc['file_name']
                category_id = doc.get('category_id', '')

                # Verifica esistenza file
                if category_id:
                    file_path = os.path.join(archive_dir, *category_id.split('/'), file_name)
                else:
                    file_path = os.path.join(archive_dir, file_name)

                if not os.path.exists(file_path):
                    # File non esiste, rimuovi dal database
                    self.delete_by_file_name(file_name)
                    removed_count += 1
                    logger.info(f"Rimosso riferimento file inesistente: {file_name}")

            logger.info(f"Pulizia completata: {removed_count} riferimenti rimossi")
            return removed_count

        except Exception as e:
            logger.error(f"Errore pulizia file inesistenti: {e}")
            raise DatabaseOperationError(f"Errore pulizia: {e}")

    def get_recent_documents(self, limit: int = 10, user_id: int = None) -> List[Dict]:
        """
        Recupera documenti recenti.

        Args:
            limit: Limite risultati
            user_id: ID utente per filtro (se specificato)

        Returns:
            Lista documenti recenti
        """
        # Questa query è complessa perché coinvolge user_activity
        # Per ora restituiamo documenti ordinati per processed_at
        query = """
            SELECT p.*
            FROM papers p
            ORDER BY p.processed_at DESC
            LIMIT ?
        """
        return self.execute_query(query, (limit,), fetch='all')

    def get_dataframe(self) -> 'pd.DataFrame':
        """
        Restituisce documenti come DataFrame pandas.

        Returns:
            DataFrame con tutti i documenti
        """
        try:
            import pandas as pd

            documents = self.find_all()
            if documents:
                return pd.DataFrame(documents)
            else:
                return pd.DataFrame()

        except ImportError:
            logger.warning("Pandas non disponibile, restituisco lista")
            return self.find_all()

    def bulk_update_category(self, file_names: List[str], new_category: str) -> int:
        """
        Aggiorna categoria per multiple documenti.

        Args:
            file_names: Lista nomi file
            new_category: Nuova categoria

        Returns:
            Numero documenti aggiornati
        """
        if not file_names:
            return 0

        try:
            # Crea placeholders per IN clause
            placeholders = ','.join(['?' for _ in file_names])
            values = file_names + [new_category]

            query = f"""
                UPDATE papers
                SET category_id = ?, processed_at = ?
                WHERE file_name IN ({placeholders})
            """

            affected = self.execute_query(query, tuple(values))
            logger.info(f"Aggiornati {affected} documenti categoria: {new_category}")
            return affected

        except Exception as e:
            logger.error(f"Errore bulk update categoria: {e}")
            raise DatabaseOperationError(f"Errore bulk update: {e}")

    def get_documents_by_metadata_quality(self) -> Dict[str, List[Dict]]:
        """
        Raggruppa documenti per qualità metadati.

        Returns:
            Dizionario con documenti raggruppati per qualità
        """
        try:
            all_docs = self.find_all()

            quality_groups = {
                'complete': [],      # Tutti i metadati
                'good': [],         # Metadati principali
                'basic': [],        # Solo nome file
                'empty': []         # Nessun metadato
            }

            for doc in all_docs:
                # Valuta qualità metadati
                has_title = bool(doc.get('title'))
                has_authors = bool(doc.get('authors'))
                has_year = bool(doc.get('publication_year'))
                has_category = bool(doc.get('category_id'))
                has_preview = bool(doc.get('formatted_preview'))

                if has_title and has_authors and has_year and has_category and has_preview:
                    quality_groups['complete'].append(doc)
                elif has_title and (has_authors or has_year or has_category):
                    quality_groups['good'].append(doc)
                elif has_title or has_preview:
                    quality_groups['basic'].append(doc)
                else:
                    quality_groups['empty'].append(doc)

            return quality_groups

        except Exception as e:
            logger.error(f"Errore valutazione qualità metadati: {e}")
            return {'complete': [], 'good': [], 'basic': [], 'empty': []}
