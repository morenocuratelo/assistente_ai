"""
Advanced search engine for document archive.
Implements full-text search with highlighting, ranking, and advanced filtering.
"""

import re
import math
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from collections import Counter
import logging

from ...database.models.base import Document
from ...core.errors.error_handler import handle_errors


@dataclass
class SearchResult:
    """Risultato ricerca singolo."""
    document: Document
    score: float
    highlights: List[str]
    matched_fields: List[str]
    rank: int


@dataclass
class SearchResponse:
    """Risposta ricerca completa."""
    results: List[SearchResult]
    total_found: int
    search_time_ms: int
    query: str
    suggestions: List[str]
    facets: Dict[str, Any]


class SearchEngine:
    """Motore di ricerca avanzato per documenti."""

    def __init__(self, document_repository):
        """Inizializza search engine.

        Args:
            document_repository: Repository documenti
        """
        self.document_repository = document_repository
        self.logger = logging.getLogger(__name__)

        # Cache per performance
        self._search_cache: Dict[str, Tuple[SearchResponse, datetime]] = {}
        self._cache_ttl = 300  # 5 minutes

    @handle_errors(operation="advanced_search", component="search_engine")
    def search(
        self,
        query: str,
        project_id: str = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        offset: int = 0,
        include_highlights: bool = True,
        include_suggestions: bool = True
    ) -> SearchResponse:
        """Esegue ricerca avanzata con highlighting e ranking.

        Args:
            query: Query di ricerca
            project_id: ID progetto
            filters: Filtri aggiuntivi
            limit: Limite risultati
            offset: Offset risultati
            include_highlights: Includere highlights
            include_suggestions: Includere suggerimenti

        Returns:
            Risposta ricerca completa
        """
        start_time = datetime.utcnow()

        # Cache key
        cache_key = self._generate_cache_key(query, project_id, filters, limit, offset)

        # Check cache
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            return cached_result

        try:
            # Get documents matching criteria
            documents = self._get_searchable_documents(project_id, filters)

            # Perform search
            search_results = self._perform_search(query, documents)

            # Apply ranking
            ranked_results = self._rank_results(search_results, query)

            # Apply pagination
            paginated_results = ranked_results[offset:offset + limit]

            # Create search response
            response = SearchResponse(
                results=paginated_results,
                total_found=len(ranked_results),
                search_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
                query=query,
                suggestions=self._generate_suggestions(query, documents) if include_suggestions else [],
                facets=self._generate_facets(documents)
            )

            # Cache result
            self._cache_result(cache_key, response)

            return response

        except Exception as e:
            self.logger.error(f"Search error for query '{query}': {e}")
            raise

    def _get_searchable_documents(
        self,
        project_id: str = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """Recupera documenti ricercabili."""
        # Use repository advanced search
        search_params = filters or {}

        if project_id:
            search_params['project_id'] = project_id

        # Get all documents (in production, this would be optimized)
        all_documents = self.document_repository.get_all()

        # Apply filters
        filtered_documents = []
        for doc in all_documents:
            if self._document_matches_filters(doc, filters or {}):
                filtered_documents.append(doc)

        return filtered_documents

    def _document_matches_filters(self, document: Document, filters: Dict[str, Any]) -> bool:
        """Verifica se documento corrisponde ai filtri."""
        # Status filter
        if 'status' in filters:
            if document.processing_status.value != filters['status']:
                return False

        # Date range filters
        if 'date_from' in filters:
            doc_date = document.created_at
            if isinstance(doc_date, str):
                doc_date = datetime.fromisoformat(doc_date)
            if doc_date < datetime.fromisoformat(filters['date_from']):
                return False

        if 'date_to' in filters:
            doc_date = document.created_at
            if isinstance(doc_date, str):
                doc_date = datetime.fromisoformat(doc_date)
            if doc_date > datetime.fromisoformat(filters['date_to']):
                return False

        # Size range filters
        if 'size_min' in filters and document.file_size:
            if document.file_size < filters['size_min']:
                return False

        if 'size_max' in filters and document.file_size:
            if document.file_size > filters['size_max']:
                return False

        return True

    def _perform_search(self, query: str, documents: List[Document]) -> List[SearchResult]:
        """Esegue ricerca sui documenti."""
        if not query.strip():
            # Return all documents with score 0
            return [
                SearchResult(
                    document=doc,
                    score=0.0,
                    highlights=[],
                    matched_fields=[],
                    rank=0
                )
                for doc in documents
            ]

        results = []
        query_terms = self._tokenize_query(query)

        for document in documents:
            # Calculate relevance score
            score, highlights, matched_fields = self._calculate_document_score(
                document, query_terms
            )

            if score > 0:
                results.append(SearchResult(
                    document=document,
                    score=score,
                    highlights=highlights,
                    matched_fields=matched_fields,
                    rank=0  # Will be set during ranking
                ))

        return results

    def _tokenize_query(self, query: str) -> List[str]:
        """Tokenizza query di ricerca."""
        # Remove punctuation and split into terms
        query = re.sub(r'[^\w\s]', ' ', query.lower())
        terms = query.split()

        # Remove stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'
        }

        return [term for term in terms if len(term) > 2 and term not in stop_words]

    def _calculate_document_score(
        self,
        document: Document,
        query_terms: List[str]
    ) -> Tuple[float, List[str], List[str]]:
        """Calcola score rilevanza documento."""
        score = 0.0
        highlights = []
        matched_fields = []

        # Search in title
        title_score = self._search_in_field(document.title or '', query_terms, 'title')
        score += title_score * 3.0  # Title matches are more important
        if title_score > 0:
            matched_fields.append('title')
            highlights.extend(self._extract_highlights(document.title or '', query_terms))

        # Search in content preview
        content_score = self._search_in_field(
            document.formatted_preview or '', query_terms, 'content'
        )
        score += content_score * 1.0
        if content_score > 0:
            matched_fields.append('content')
            highlights.extend(self._extract_highlights(
                document.formatted_preview or '', query_terms
            ))

        # Search in keywords
        keywords_text = ' '.join(document.keywords) if document.keywords else ''
        keywords_score = self._search_in_field(keywords_text, query_terms, 'keywords')
        score += keywords_score * 2.0  # Keywords matches are important
        if keywords_score > 0:
            matched_fields.append('keywords')

        # Boost score for recent documents
        if document.created_at:
            days_old = (datetime.utcnow() - document.created_at).days
            recency_boost = max(0, 1.0 - (days_old / 365))  # Boost for documents < 1 year old
            score *= (1.0 + recency_boost * 0.2)

        return score, highlights, matched_fields

    def _search_in_field(self, field_text: str, query_terms: List[str], field_name: str) -> float:
        """Cerca termini query in campo specifico."""
        if not field_text:
            return 0.0

        field_lower = field_text.lower()
        score = 0.0

        for term in query_terms:
            # Exact match gets higher score
            if term in field_lower:
                score += 1.0

            # Partial matches get lower score
            if any(term in word for word in field_lower.split()):
                score += 0.5

        return score

    def _extract_highlights(self, text: str, query_terms: List[str]) -> List[str]:
        """Estrae highlights dal testo."""
        if not text:
            return []

        highlights = []
        text_lower = text.lower()

        for term in query_terms:
            # Find all occurrences of the term
            start = 0
            while True:
                pos = text_lower.find(term, start)
                if pos == -1:
                    break

                # Extract context around the match
                context_start = max(0, pos - 30)
                context_end = min(len(text), pos + len(term) + 30)

                highlight = text[context_start:context_end].strip()
                highlights.append(f"...{highlight}...")

                start = pos + 1

        return highlights[:5]  # Limit highlights

    def _rank_results(self, search_results: List[SearchResult], query: str) -> List[SearchResult]:
        """Ranka risultati ricerca per rilevanza."""
        if not search_results:
            return search_results

        # Sort by score (descending)
        ranked_results = sorted(search_results, key=lambda x: x.score, reverse=True)

        # Assign ranks
        for i, result in enumerate(ranked_results):
            result.rank = i + 1

        return ranked_results

    def _generate_suggestions(self, query: str, documents: List[Document]) -> List[str]:
        """Genera suggerimenti ricerca."""
        suggestions = []

        if not query.strip():
            return suggestions

        # Get all searchable text from documents
        all_text = []
        for doc in documents:
            if doc.title:
                all_text.append(doc.title.lower())
            if doc.formatted_preview:
                all_text.append(doc.formatted_preview.lower())
            if doc.keywords:
                all_text.extend([kw.lower() for kw in doc.keywords])

        # Find similar terms
        query_terms = self._tokenize_query(query)
        all_words = ' '.join(all_text).split()

        # Count word frequencies
        word_counts = Counter(all_words)

        # Suggest frequent words that start with query terms
        for term in query_terms:
            for word, count in word_counts.most_common(20):
                if word.startswith(term) and len(word) > len(term):
                    suggestions.append(word)

        # Remove duplicates and limit
        suggestions = list(set(suggestions))[:10]

        return suggestions

    def _generate_facets(self, documents: List[Document]) -> Dict[str, Any]:
        """Genera facets per filtri."""
        facets = {
            'status': Counter(),
            'file_type': Counter(),
            'size_range': Counter(),
            'date_range': Counter(),
            'keywords': Counter()
        }

        for doc in documents:
            # Status facet
            facets['status'][doc.processing_status.value] += 1

            # File type facet
            file_ext = doc.file_name.split('.')[-1].lower() if '.' in doc.file_name else 'unknown'
            facets['file_type'][file_ext] += 1

            # Size range facet
            if doc.file_size:
                if doc.file_size < 1024 * 1024:  # < 1MB
                    size_range = 'small'
                elif doc.file_size < 10 * 1024 * 1024:  # < 10MB
                    size_range = 'medium'
                else:
                    size_range = 'large'
                facets['size_range'][size_range] += 1

            # Date range facet
            if doc.created_at:
                days_old = (datetime.utcnow() - doc.created_at).days
                if days_old <= 7:
                    date_range = 'week'
                elif days_old <= 30:
                    date_range = 'month'
                elif days_old <= 365:
                    date_range = 'year'
                else:
                    date_range = 'older'
                facets['date_range'][date_range] += 1

            # Keywords facet (top keywords)
            if doc.keywords:
                for keyword in doc.keywords[:5]:  # Limit to top 5
                    facets['keywords'][keyword] += 1

        return {k: dict(v.most_common(10)) for k, v in facets.items()}

    def _generate_cache_key(
        self,
        query: str,
        project_id: str,
        filters: Optional[Dict[str, Any]],
        limit: int,
        offset: int
    ) -> str:
        """Genera chiave cache per parametri ricerca."""
        key_parts = [
            query.lower().strip(),
            project_id or 'all',
            str(sorted(filters.items())) if filters else 'no_filters',
            str(limit),
            str(offset)
        ]

        # Create hash of key parts
        key_string = '|'.join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    def _get_cached_result(self, cache_key: str) -> Optional[SearchResponse]:
        """Recupera risultato dalla cache se valido."""
        if cache_key in self._search_cache:
            result, timestamp = self._search_cache[cache_key]

            # Check if cache is still valid
            if (datetime.utcnow() - timestamp).seconds < self._cache_ttl:
                return result

            # Remove expired cache entry
            del self._search_cache[cache_key]

        return None

    def _cache_result(self, cache_key: str, response: SearchResponse) -> None:
        """Cache risultato ricerca."""
        self._search_cache[cache_key] = (response, datetime.utcnow())

        # Limit cache size
        if len(self._search_cache) > 100:
            # Remove oldest entries
            oldest_keys = sorted(
                self._search_cache.keys(),
                key=lambda k: self._search_cache[k][1]
            )[:50]
            for key in oldest_keys:
                del self._search_cache[key]

    def clear_search_cache(self) -> None:
        """Pulisce cache ricerca."""
        self._search_cache.clear()
        self.logger.info("Search cache cleared")

    def get_search_analytics(self) -> Dict[str, Any]:
        """Recupera analytics ricerca."""
        return {
            'cache_size': len(self._search_cache),
            'cache_ttl_seconds': self._cache_ttl,
            'oldest_cache_entry': (
                min([ts for _, ts in self._search_cache.values()]).isoformat()
                if self._search_cache else None
            ),
            'newest_cache_entry': (
                max([ts for _, ts in self._search_cache.values()]).isoformat()
                if self._search_cache else None
            )
        }


class BatchOperationManager:
    """Gestore operazioni batch sicure."""

    def __init__(self, archive_service):
        """Inizializza batch manager.

        Args:
            archive_service: Servizio archivio
        """
        self.archive_service = archive_service
        self.logger = logging.getLogger(__name__)

        # Operation templates
        self.operation_templates = {
            'cleanup_old': {
                'name': 'Cleanup Old Documents',
                'description': 'Remove documents older than specified days',
                'parameters': ['days_old'],
                'risk_level': 'medium'
            },
            'reprocess_failed': {
                'name': 'Reprocess Failed Documents',
                'description': 'Retry processing for failed documents',
                'parameters': ['max_retries'],
                'risk_level': 'low'
            },
            'export_by_category': {
                'name': 'Export by Category',
                'description': 'Export documents by category',
                'parameters': ['category', 'format'],
                'risk_level': 'low'
            },
            'bulk_tag': {
                'name': 'Bulk Tagging',
                'description': 'Apply tags to multiple documents',
                'parameters': ['tags', 'criteria'],
                'risk_level': 'low'
            }
        }

    @handle_errors(operation="execute_batch_operation", component="batch_manager")
    def execute_batch_operation(
        self,
        operation_type: str,
        document_ids: List[int],
        parameters: Dict[str, Any],
        user_id: str = None
    ) -> Dict[str, Any]:
        """Esegue operazione batch con progress tracking.

        Args:
            operation_type: Tipo operazione
            document_ids: ID documenti da processare
            parameters: Parametri operazione
            user_id: ID utente che esegue

        Returns:
            Risultati operazione batch
        """
        operation_id = f"batch_{operation_type}_{int(datetime.utcnow().timestamp())}"

        try:
            # Validate operation
            if operation_type not in self.operation_templates:
                raise ValueError(f"Unsupported operation type: {operation_type}")

            template = self.operation_templates[operation_type]

            # Validate parameters
            self._validate_operation_parameters(operation_type, parameters)

            # Execute operation with progress tracking
            results = self._execute_with_progress(
                operation_type,
                document_ids,
                parameters,
                operation_id
            )

            self.logger.info(f"Batch operation {operation_id} completed successfully")
            return results

        except Exception as e:
            self.logger.error(f"Batch operation {operation_id} failed: {e}")
            raise

    def _validate_operation_parameters(self, operation_type: str, parameters: Dict[str, Any]) -> None:
        """Valida parametri operazione."""
        template = self.operation_templates[operation_type]

        for param in template['parameters']:
            if param not in parameters:
                raise ValueError(f"Missing required parameter: {param}")

    def _execute_with_progress(
        self,
        operation_type: str,
        document_ids: List[int],
        parameters: Dict[str, Any],
        operation_id: str
    ) -> Dict[str, Any]:
        """Esegue operazione con progress tracking."""
        total_docs = len(document_ids)
        results = {
            'operation_id': operation_id,
            'operation_type': operation_type,
            'total_documents': total_docs,
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'errors': [],
            'start_time': datetime.utcnow().isoformat(),
            'end_time': None,
            'duration_ms': None
        }

        try:
            # Execute based on operation type
            if operation_type == 'cleanup_old':
                results.update(self._execute_cleanup_old(parameters))
            elif operation_type == 'reprocess_failed':
                results.update(self._execute_reprocess_failed(parameters))
            elif operation_type == 'export_by_category':
                results.update(self._execute_export_by_category(parameters))
            elif operation_type == 'bulk_tag':
                results.update(self._execute_bulk_tag(parameters))
            else:
                raise ValueError(f"Unsupported operation: {operation_type}")

        except Exception as e:
            results['errors'].append(str(e))
            self.logger.error(f"Error in batch operation {operation_id}: {e}")

        finally:
            # Finalize results
            end_time = datetime.utcnow()
            results['end_time'] = end_time.isoformat()
            results['duration_ms'] = int((end_time - datetime.fromisoformat(results['start_time'])).total_seconds() * 1000)

        return results

    def _execute_cleanup_old(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Esegue cleanup documenti vecchi."""
        days_old = parameters.get('days_old', 365)

        # This would call archive service cleanup method
        # For now, return mock results
        return {
            'processed': 10,
            'successful': 8,
            'failed': 2,
            'errors': ['Document locked', 'Permission denied']
        }

    def _execute_reprocess_failed(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Esegue reprocessing documenti falliti."""
        max_retries = parameters.get('max_retries', 3)

        # This would call archive service reprocess method
        return {
            'processed': 5,
            'successful': 4,
            'failed': 1,
            'errors': ['Processing timeout']
        }

    def _execute_export_by_category(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Esegue export per categoria."""
        category = parameters.get('category')
        export_format = parameters.get('format', 'json')

        # This would call archive service export method
        return {
            'processed': 15,
            'successful': 15,
            'failed': 0,
            'export_path': f'/exports/{category}_export.{export_format}'
        }

    def _execute_bulk_tag(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Esegue tagging bulk."""
        tags = parameters.get('tags', [])
        criteria = parameters.get('criteria', {})

        # This would call archive service tagging method
        return {
            'processed': 20,
            'successful': 18,
            'failed': 2,
            'tags_applied': tags
        }

    def get_operation_templates(self) -> Dict[str, Dict[str, Any]]:
        """Recupera templates operazioni disponibili."""
        return self.operation_templates.copy()

    def create_operation_template(
        self,
        name: str,
        description: str,
        parameters: List[str],
        risk_level: str = 'low'
    ) -> str:
        """Crea nuovo template operazione.

        Args:
            name: Nome template
            description: Descrizione template
            parameters: Lista parametri richiesti
            risk_level: Livello rischio (low, medium, high)

        Returns:
            ID template creato
        """
        template_id = f"custom_{name.lower().replace(' ', '_')}"

        self.operation_templates[template_id] = {
            'name': name,
            'description': description,
            'parameters': parameters,
            'risk_level': risk_level
        }

        self.logger.info(f"Created operation template: {template_id}")
        return template_id

    def get_batch_operation_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Recupera history operazioni batch."""
        # This would query operation history from database
        # For now, return mock data
        return [
            {
                'operation_id': f'batch_{i}',
                'operation_type': 'cleanup_old',
                'start_time': (datetime.utcnow().replace(hour=datetime.utcnow().hour - i)).isoformat(),
                'duration_ms': 1500 + i * 100,
                'total_documents': 100 - i * 5,
                'successful': 90 - i * 4,
                'failed': i + 1
            }
            for i in range(min(limit, 10))
        ]


class DocumentRelationshipMapper:
    """Mapper per relazioni tra documenti."""

    def __init__(self, document_repository):
        """Inizializza relationship mapper.

        Args:
            document_repository: Repository documenti
        """
        self.document_repository = document_repository
        self.logger = logging.getLogger(__name__)

    @handle_errors(operation="map_document_relationships", component="relationship_mapper")
    def map_relationships(
        self,
        project_id: str,
        min_confidence: float = 0.3
    ) -> Dict[str, Any]:
        """Mappa relazioni tra documenti.

        Args:
            project_id: ID progetto
            min_confidence: Confidenza minima per relazione

        Returns:
            Mappatura relazioni
        """
        try:
            # Get all documents in project
            documents = self.document_repository.get_by_project(project_id)

            relationships = {
                'nodes': [],
                'edges': [],
                'clusters': [],
                'stats': {
                    'total_documents': len(documents),
                    'total_relationships': 0,
                    'avg_confidence': 0.0
                }
            }

            # Create nodes for each document
            for doc in documents:
                relationships['nodes'].append({
                    'id': doc.id,
                    'label': doc.title or doc.file_name,
                    'type': self._get_document_type(doc.file_name),
                    'size': doc.file_size or 0,
                    'status': doc.processing_status.value,
                    'keywords': doc.keywords
                })

            # Find relationships between documents
            doc_relationships = self._find_document_relationships(documents, min_confidence)

            relationships['edges'] = doc_relationships
            relationships['stats']['total_relationships'] = len(doc_relationships)

            # Calculate average confidence
            if doc_relationships:
                confidences = [rel['confidence'] for rel in doc_relationships]
                relationships['stats']['avg_confidence'] = sum(confidences) / len(confidences)

            # Find clusters
            relationships['clusters'] = self._find_document_clusters(documents)

            return relationships

        except Exception as e:
            self.logger.error(f"Error mapping relationships: {e}")
            raise

    def _get_document_type(self, file_name: str) -> str:
        """Determina tipo documento da nome file."""
        extension = file_name.split('.')[-1].lower() if '.' in file_name else 'unknown'

        type_mapping = {
            'pdf': 'academic',
            'docx': 'document',
            'doc': 'document',
            'txt': 'note',
            'rtf': 'document',
            'html': 'web',
            'htm': 'web',
            'xlsx': 'spreadsheet',
            'xls': 'spreadsheet',
            'pptx': 'presentation',
            'ppt': 'presentation'
        }

        return type_mapping.get(extension, 'other')

    def _find_document_relationships(
        self,
        documents: List[Document],
        min_confidence: float
    ) -> List[Dict[str, Any]]:
        """Trova relazioni tra documenti."""
        relationships = []

        for i, doc1 in enumerate(documents):
            for doc2 in documents[i+1:]:
                # Calculate relationship strength
                confidence = self._calculate_relationship_confidence(doc1, doc2)

                if confidence >= min_confidence:
                    relationships.append({
                        'source': doc1.id,
                        'target': doc2.id,
                        'confidence': confidence,
                        'type': self._determine_relationship_type(doc1, doc2),
                        'strength': self._calculate_relationship_strength(confidence)
                    })

        return relationships

    def _calculate_relationship_confidence(self, doc1: Document, doc2: Document) -> float:
        """Calcola confidenza relazione tra due documenti."""
        confidence = 0.0

        # Common keywords
        if doc1.keywords and doc2.keywords:
            common_keywords = set(doc1.keywords) & set(doc2.keywords)
            if common_keywords:
                confidence += min(len(common_keywords) / 5, 1.0) * 0.4

        # Similar titles
        if doc1.title and doc2.title:
            title_similarity = self._calculate_text_similarity(doc1.title, doc2.title)
            confidence += title_similarity * 0.3

        # Similar content (if available)
        if doc1.formatted_preview and doc2.formatted_preview:
            content_similarity = self._calculate_text_similarity(
                doc1.formatted_preview, doc2.formatted_preview
            )
            confidence += content_similarity * 0.3

        return min(confidence, 1.0)

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calcola similarità tra due testi."""
        if not text1 or not text2:
            return 0.0

        # Simple similarity based on common words
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

    def _determine_relationship_type(self, doc1: Document, doc2: Document) -> str:
        """Determina tipo relazione tra documenti."""
        # Simple relationship type determination
        type1 = self._get_document_type(doc1.file_name)
        type2 = self._get_document_type(doc2.file_name)

        if type1 == type2:
            return 'similar_type'
        elif type1 == 'academic' or type2 == 'academic':
            return 'related_content'
        else:
            return 'general_relation'

    def _calculate_relationship_strength(self, confidence: float) -> str:
        """Calcola forza relazione da confidenza."""
        if confidence >= 0.8:
            return 'strong'
        elif confidence >= 0.5:
            return 'medium'
        else:
            return 'weak'

    def _find_document_clusters(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """Trova cluster di documenti correlati."""
        # Simple clustering based on keywords
        clusters = []

        # Group by common keywords
        keyword_groups = {}

        for doc in documents:
            if doc.keywords:
                for keyword in doc.keywords:
                    if keyword not in keyword_groups:
                        keyword_groups[keyword] = []
                    keyword_groups[keyword].append(doc.id)

        # Create clusters for keywords with multiple documents
        for keyword, doc_ids in keyword_groups.items():
            if len(doc_ids) >= 2:
                clusters.append({
                    'id': f'cluster_{keyword}',
                    'name': f'Documents about: {keyword}',
                    'type': 'keyword_cluster',
                    'document_ids': doc_ids,
                    'size': len(doc_ids)
                })

        return clusters

    def get_document_neighbors(
        self,
        document_id: int,
        max_neighbors: int = 10,
        min_confidence: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Recupera documenti correlati (vicini).

        Args:
            document_id: ID documento centrale
            max_neighbors: Numero massimo vicini
            min_confidence: Confidenza minima

        Returns:
            Lista documenti vicini
        """
        try:
            # Get central document
            central_doc = self.document_repository.get_by_id(document_id)
            if not central_doc:
                return []

            # Get all documents for relationship calculation
            all_docs = self.document_repository.get_all()

            # Find related documents
            neighbors = []

            for doc in all_docs:
                if doc.id == document_id:
                    continue

                confidence = self._calculate_relationship_confidence(central_doc, doc)

                if confidence >= min_confidence:
                    neighbors.append({
                        'document_id': doc.id,
                        'file_name': doc.file_name,
                        'title': doc.title,
                        'confidence': confidence,
                        'relationship_type': self._determine_relationship_type(central_doc, doc)
                    })

            # Sort by confidence and limit
            neighbors.sort(key=lambda x: x['confidence'], reverse=True)
            return neighbors[:max_neighbors]

        except Exception as e:
            self.logger.error(f"Error getting document neighbors: {e}")
            return []


class SearchResultRanker:
    """Ranker avanzato per risultati ricerca."""

    def __init__(self):
        """Inizializza ranker."""
        self.logger = logging.getLogger(__name__)

        # Ranking weights
        self.weights = {
            'title_match': 3.0,
            'content_match': 1.0,
            'keyword_match': 2.0,
            'recency_boost': 0.2,
            'file_type_boost': 0.1,
            'status_boost': 0.1
        }

    def rank_documents(
        self,
        documents: List[Document],
        query: str,
        user_context: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Document, float, str]]:
        """Ranka documenti per rilevanza.

        Args:
            documents: Lista documenti da rankare
            query: Query di ricerca
            user_context: Contesto utente per personalizzazione

        Returns:
            Lista tuple (documento, score, explanation)
        """
        ranked_documents = []

        for document in documents:
            score, explanation = self._calculate_document_score(document, query, user_context)

            if score > 0:
                ranked_documents.append((document, score, explanation))

        # Sort by score descending
        ranked_documents.sort(key=lambda x: x[1], reverse=True)

        return ranked_documents

    def _calculate_document_score(
        self,
        document: Document,
        query: str,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[float, str]:
        """Calcola score documento con spiegazione."""
        score = 0.0
        explanations = []

        query_terms = query.lower().split()

        # Title match score
        if document.title:
            title_score = self._calculate_field_score(document.title, query_terms, 'title')
            score += title_score * self.weights['title_match']
            if title_score > 0:
                explanations.append(f"Title match: {title_score".2f"}")

        # Content match score
        if document.formatted_preview:
            content_score = self._calculate_field_score(
                document.formatted_preview, query_terms, 'content'
            )
            score += content_score * self.weights['content_match']
            if content_score > 0:
                explanations.append(f"Content match: {content_score".2f"}")

        # Keyword match score
        if document.keywords:
            keyword_text = ' '.join(document.keywords)
            keyword_score = self._calculate_field_score(keyword_text, query_terms, 'keywords')
            score += keyword_score * self.weights['keyword_match']
            if keyword_score > 0:
                explanations.append(f"Keyword match: {keyword_score".2f"}")

        # Recency boost
        if document.created_at:
            days_old = (datetime.utcnow() - document.created_at).days
            recency_score = max(0, 1.0 - (days_old / 365))
            score += recency_score * self.weights['recency_boost']
            if recency_score > 0:
                explanations.append(f"Recency boost: {recency_score".2f"}")

        # File type boost (prefer PDFs for academic content)
        if document.file_name.lower().endswith('.pdf'):
            score += self.weights['file_type_boost']
            explanations.append("File type boost: PDF")

        # Status boost (prefer completed documents)
        if document.processing_status.value == 'completed':
            score += self.weights['status_boost']
            explanations.append("Status boost: Completed")

        # User context personalization
        if user_context:
            context_boost = self._calculate_context_boost(document, user_context)
            score += context_boost
            if context_boost > 0:
                explanations.append(f"Context boost: {context_boost".2f"}")

        explanation = "; ".join(explanations) if explanations else "No matches found"
        return score, explanation

    def _calculate_field_score(self, field_text: str, query_terms: List[str], field_type: str) -> float:
        """Calcola score per campo specifico."""
        if not field_text:
            return 0.0

        field_lower = field_text.lower()
        score = 0.0

        for term in query_terms:
            # Exact matches
            if term in field_lower:
                score += 1.0

            # Partial matches
            term_matches = len(re.findall(r'\b' + re.escape(term) + r'\w*', field_lower))
            score += term_matches * 0.5

        # Normalize by field length
        if len(field_lower) > 0:
            score = score / math.sqrt(len(field_lower))

        return min(score, 5.0)  # Cap score

    def _calculate_context_boost(self, document: Document, user_context: Dict[str, Any]) -> float:
        """Calcola boost basato su contesto utente."""
        boost = 0.0

        # Boost for user's preferred categories
        if 'preferred_categories' in user_context:
            doc_category = self._infer_document_category(document)
            if doc_category in user_context['preferred_categories']:
                boost += 0.2

        # Boost for recently accessed file types
        if 'recent_file_types' in user_context:
            doc_extension = document.file_name.split('.')[-1].lower()
            if doc_extension in user_context['recent_file_types']:
                boost += 0.1

        return boost

    def _infer_document_category(self, document: Document) -> str:
        """Infers document category from metadata."""
        # Simple category inference
        if document.file_name.lower().endswith('.pdf'):
            return 'academic'
        elif any(keyword in ' '.join(document.keywords).lower()
                for keyword in ['research', 'study', 'paper']):
            return 'academic'
        else:
            return 'general'

    def get_ranking_explanation(self, document: Document, query: str) -> str:
        """Genera spiegazione ranking per documento."""
        score, explanation = self._calculate_document_score(document, query)
        return f"Score: {score:.2f} - {explanation}"


# Utility functions

def create_search_engine(document_repository) -> SearchEngine:
    """Crea search engine con configurazione ottimale."""
    return SearchEngine(document_repository)


def create_batch_manager(archive_service) -> BatchOperationManager:
    """Crea batch manager con template predefiniti."""
    return BatchOperationManager(archive_service)


def create_relationship_mapper(document_repository) -> DocumentRelationshipMapper:
    """Crea relationship mapper per analisi connessioni."""
    return DocumentRelationshipMapper(document_repository)


def create_search_ranker() -> SearchResultRanker:
    """Crea search ranker con pesi ottimizzati."""
    return SearchResultRanker()
