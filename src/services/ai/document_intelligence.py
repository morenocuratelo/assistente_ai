"""
Document Intelligence System for Archivista AI.
Implements entity extraction, topic modeling, sentiment analysis, and similarity detection.
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import Counter, defaultdict
import logging
import math

from ...database.models.base import Document, ConceptEntity, ConceptRelationship
from ...core.errors.error_handler import handle_errors


@dataclass
class Entity:
    """Extracted entity with metadata."""
    text: str
    type: str
    confidence: float
    start_pos: int
    end_pos: int
    context: str
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Topic:
    """Document topic with relevance score."""
    name: str
    keywords: List[str]
    relevance_score: float
    document_sections: List[str]


@dataclass
class SentimentResult:
    """Sentiment analysis result."""
    polarity: float  # -1.0 (negative) to 1.0 (positive)
    subjectivity: float  # 0.0 (objective) to 1.0 (subjective)
    confidence: float
    dominant_emotion: Optional[str] = None
    emotion_scores: Dict[str, float] = field(default_factory=dict)


@dataclass
class DocumentSimilarity:
    """Document similarity result."""
    source_document: Document
    target_document: Document
    similarity_score: float
    similarity_type: str  # 'semantic', 'keyword', 'structural'
    matching_sections: List[Dict[str, Any]] = field(default_factory=list)


class EntityExtractor:
    """Advanced entity extraction system."""

    def __init__(self):
        """Initialize entity extractor."""
        self.logger = logging.getLogger(__name__)

        # Entity patterns
        self.entity_patterns = {
            'person': re.compile(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'),  # Simple person names
            'organization': re.compile(r'\b[A-Z][a-zA-Z\s&]+\b'),  # Organizations
            'location': re.compile(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'),  # Locations
            'date': re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b'),
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'url': re.compile(r'https?://[^\s]+'),
            'phone': re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
            'academic_term': re.compile(r'\b[A-Z][a-z]+(?:ology|ics|ment|tion|sis|ing)\b'),
            'technical_term': re.compile(r'\b[A-Za-z]+[0-9]+[A-Za-z]*\b|\b[A-Z]{2,}\b'),
        }

        # Stop words for filtering
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'
        }

    @handle_errors(operation="extract_entities", component="entity_extractor")
    def extract_entities(self, document: Document) -> List[Entity]:
        """Extract entities from document content.

        Args:
            document: Document to analyze

        Returns:
            List of extracted entities
        """
        entities = []
        text = document.formatted_preview or ""

        if not text:
            return entities

        # Extract entities by type
        for entity_type, pattern in self.entity_patterns.items():
            matches = pattern.finditer(text)

            for match in matches:
                entity_text = match.group().strip()

                # Skip if too short or in stop words
                if len(entity_text) < 3 or entity_text.lower() in self.stop_words:
                    continue

                # Calculate confidence based on context
                confidence = self._calculate_entity_confidence(
                    entity_text, match.span(), text, entity_type
                )

                if confidence > 0.3:  # Minimum confidence threshold
                    entity = Entity(
                        text=entity_text,
                        type=entity_type,
                        confidence=confidence,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        context=self._extract_context(text, match.span())
                    )
                    entities.append(entity)

        # Remove duplicates and sort by confidence
        unique_entities = self._deduplicate_entities(entities)
        return sorted(unique_entities, key=lambda x: x.confidence, reverse=True)

    def _calculate_entity_confidence(
        self,
        entity_text: str,
        span: Tuple[int, int],
        text: str,
        entity_type: str
    ) -> float:
        """Calculate confidence for extracted entity."""
        confidence = 0.5  # Base confidence

        # Boost confidence based on entity type
        type_boosts = {
            'email': 0.9,
            'url': 0.8,
            'date': 0.7,
            'phone': 0.8,
            'person': 0.6,
            'organization': 0.5,
            'location': 0.5,
            'academic_term': 0.4,
            'technical_term': 0.4
        }

        confidence += type_boosts.get(entity_type, 0.0)

        # Boost for entities in title
        title = getattr(Document, 'title', None) or ""
        if title and entity_text.lower() in title.lower():
            confidence += 0.2

        # Boost for capitalized entities (likely proper nouns)
        if entity_text[0].isupper():
            confidence += 0.1

        # Boost for longer entities
        if len(entity_text) > 5:
            confidence += 0.1

        return min(confidence, 1.0)

    def _extract_context(self, text: str, span: Tuple[int, int]) -> str:
        """Extract context around entity."""
        start, end = span
        context_start = max(0, start - 50)
        context_end = min(len(text), end + 50)

        context = text[context_start:context_end].strip()

        # Highlight the entity in context
        entity_text = text[start:end]
        if entity_text in context:
            context = context.replace(
                entity_text,
                f"**{entity_text}**"
            )

        return context

    def _deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """Remove duplicate entities."""
        seen = set()
        unique_entities = []

        for entity in entities:
            # Create unique key
            key = (entity.text.lower(), entity.type)

            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)

        return unique_entities


class TopicModeler:
    """Topic modeling and clustering system."""

    def __init__(self):
        """Initialize topic modeler."""
        self.logger = logging.getLogger(__name__)

        # Academic topic keywords
        self.topic_keywords = {
            'machine_learning': [
                'algorithm', 'neural network', 'deep learning', 'classification',
                'regression', 'clustering', 'supervised', 'unsupervised', 'training',
                'validation', 'accuracy', 'precision', 'recall', 'model'
            ],
            'statistics': [
                'probability', 'distribution', 'hypothesis', 'significance',
                'correlation', 'regression', 'anova', 'chi-square', 'p-value',
                'confidence interval', 'sample', 'population', 'mean', 'median'
            ],
            'programming': [
                'function', 'variable', 'class', 'object', 'method', 'loop',
                'condition', 'array', 'string', 'integer', 'boolean', 'syntax',
                'compile', 'debug', 'algorithm', 'data structure'
            ],
            'research': [
                'study', 'experiment', 'analysis', 'methodology', 'conclusion',
                'finding', 'result', 'evidence', 'theory', 'hypothesis', 'data',
                'sample', 'population', 'variable', 'control', 'treatment'
            ],
            'mathematics': [
                'equation', 'function', 'variable', 'constant', 'theorem', 'proof',
                'geometry', 'algebra', 'calculus', 'matrix', 'vector', 'set',
                'number', 'operation', 'solve', 'calculate', 'formula'
            ]
        }

    @handle_errors(operation="extract_topics", component="topic_modeler")
    def extract_topics(self, document: Document, max_topics: int = 5) -> List[Topic]:
        """Extract topics from document.

        Args:
            document: Document to analyze
            max_topics: Maximum number of topics to extract

        Returns:
            List of extracted topics
        """
        text = document.formatted_preview or ""
        title = document.title or ""

        if not text and not title:
            return []

        # Combine title and content for analysis
        full_text = f"{title} {text}".lower()

        # Calculate topic relevance
        topic_scores = {}

        for topic_name, keywords in self.topic_keywords.items():
            score = self._calculate_topic_score(full_text, keywords, title)
            if score > 0.1:  # Minimum relevance threshold
                topic_scores[topic_name] = score

        # Sort topics by relevance
        sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)

        # Create topic objects
        topics = []
        for topic_name, score in sorted_topics[:max_topics]:
            topic = Topic(
                name=topic_name,
                keywords=self.topic_keywords[topic_name],
                relevance_score=score,
                document_sections=self._identify_relevant_sections(full_text, topic_name)
            )
            topics.append(topic)

        return topics

    def _calculate_topic_score(self, text: str, keywords: List[str], title: str) -> float:
        """Calculate relevance score for topic."""
        score = 0.0
        text_words = set(text.split())

        # Count keyword matches
        keyword_matches = 0
        for keyword in keywords:
            if keyword in text:
                keyword_matches += 1

        # Normalize by total keywords
        keyword_score = keyword_matches / len(keywords)

        # Boost for title matches
        title_matches = 0
        for keyword in keywords:
            if keyword in title.lower():
                title_matches += 1

        title_boost = title_matches / len(keywords) * 0.3

        score = keyword_score * 0.7 + title_boost

        return min(score, 1.0)

    def _identify_relevant_sections(self, text: str, topic_name: str) -> List[str]:
        """Identify relevant sections for topic."""
        sections = []
        sentences = text.split('.')

        for sentence in sentences:
            if any(keyword in sentence for keyword in self.topic_keywords[topic_name]):
                sections.append(sentence.strip())

        return sections[:3]  # Return top 3 relevant sections


class SentimentAnalyzer:
    """Sentiment analysis for document content."""

    def __init__(self):
        """Initialize sentiment analyzer."""
        self.logger = logging.getLogger(__name__)

        # Sentiment word lists
        self.positive_words = {
            'good', 'excellent', 'amazing', 'wonderful', 'fantastic', 'great',
            'outstanding', 'superb', 'brilliant', 'positive', 'successful',
            'effective', 'efficient', 'valuable', 'important', 'significant'
        }

        self.negative_words = {
            'bad', 'terrible', 'awful', 'horrible', 'worst', 'poor', 'negative',
            'failure', 'problem', 'issue', 'error', 'flaw', 'defect', 'weak',
            'inadequate', 'insufficient', 'unsatisfactory', 'disappointing'
        }

        self.emotion_words = {
            'happy': ['joy', 'happiness', 'pleasure', 'delight', 'excited'],
            'sad': ['sorrow', 'grief', 'sadness', 'depression', 'unhappy'],
            'angry': ['anger', 'rage', 'fury', 'irritation', 'annoyance'],
            'fear': ['fear', 'terror', 'anxiety', 'worry', 'panic'],
            'surprise': ['surprise', 'shock', 'amazement', 'astonishment']
        }

    @handle_errors(operation="analyze_sentiment", component="sentiment_analyzer")
    def analyze_sentiment(self, document: Document) -> SentimentResult:
        """Analyze sentiment of document content.

        Args:
            document: Document to analyze

        Returns:
            Sentiment analysis result
        """
        text = document.formatted_preview or ""

        if not text:
            return SentimentResult(
                polarity=0.0,
                subjectivity=0.0,
                confidence=0.0
            )

        text_lower = text.lower()
        words = text_lower.split()

        # Count sentiment words
        positive_count = sum(1 for word in words if word in self.positive_words)
        negative_count = sum(1 for word in words if word in self.negative_words)

        # Calculate polarity
        total_sentiment_words = positive_count + negative_count
        if total_sentiment_words == 0:
            polarity = 0.0
        else:
            polarity = (positive_count - negative_count) / total_sentiment_words

        # Calculate subjectivity (presence of opinion words)
        opinion_words = self.positive_words | self.negative_words
        opinion_count = sum(1 for word in words if word in opinion_words)
        subjectivity = min(opinion_count / len(words), 1.0) if words else 0.0

        # Calculate confidence based on sentiment word density
        confidence = min(total_sentiment_words / len(words) * 5, 1.0) if words else 0.0

        # Determine dominant emotion
        dominant_emotion = self._determine_dominant_emotion(text_lower)

        # Calculate emotion scores
        emotion_scores = self._calculate_emotion_scores(text_lower)

        return SentimentResult(
            polarity=polarity,
            subjectivity=subjectivity,
            confidence=confidence,
            dominant_emotion=dominant_emotion,
            emotion_scores=emotion_scores
        )

    def _determine_dominant_emotion(self, text: str) -> Optional[str]:
        """Determine dominant emotion in text."""
        emotion_scores = {}

        for emotion, keywords in self.emotion_words.items():
            matches = sum(1 for keyword in keywords if keyword in text)
            if matches > 0:
                emotion_scores[emotion] = matches

        if emotion_scores:
            return max(emotion_scores.items(), key=lambda x: x[1])[0]

        return None

    def _calculate_emotion_scores(self, text: str) -> Dict[str, float]:
        """Calculate emotion scores."""
        emotion_scores = {}

        for emotion, keywords in self.emotion_words.items():
            matches = sum(1 for keyword in keywords if keyword in text)
            if matches > 0:
                # Normalize by text length
                emotion_scores[emotion] = min(matches / len(text.split()) * 10, 1.0)

        return emotion_scores


class DocumentSimilarityEngine:
    """Engine for detecting document similarity."""

    def __init__(self):
        """Initialize similarity engine."""
        self.logger = logging.getLogger(__name__)

    @handle_errors(operation="calculate_similarity", component="similarity_engine")
    def calculate_similarity(
        self,
        source_doc: Document,
        target_doc: Document,
        similarity_type: str = "comprehensive"
    ) -> DocumentSimilarity:
        """Calculate similarity between two documents.

        Args:
            source_doc: Source document
            target_doc: Target document
            similarity_type: Type of similarity to calculate

        Returns:
            Similarity result
        """
        # Calculate different types of similarity
        semantic_score = self._calculate_semantic_similarity(source_doc, target_doc)
        keyword_score = self._calculate_keyword_similarity(source_doc, target_doc)
        structural_score = self._calculate_structural_similarity(source_doc, target_doc)

        # Combine scores based on type
        if similarity_type == "semantic":
            overall_score = semantic_score
        elif similarity_type == "keyword":
            overall_score = keyword_score
        elif similarity_type == "structural":
            overall_score = structural_score
        else:  # comprehensive
            overall_score = (semantic_score * 0.4 + keyword_score * 0.4 + structural_score * 0.2)

        # Find matching sections
        matching_sections = self._find_matching_sections(source_doc, target_doc)

        return DocumentSimilarity(
            source_document=source_doc,
            target_document=target_doc,
            similarity_score=overall_score,
            similarity_type=similarity_type,
            matching_sections=matching_sections
        )

    def _calculate_semantic_similarity(self, doc1: Document, doc2: Document) -> float:
        """Calculate semantic similarity between documents."""
        text1 = (doc1.formatted_preview or "").lower()
        text2 = (doc2.formatted_preview or "").lower()

        if not text1 or not text2:
            return 0.0

        # Simple semantic similarity based on word overlap
        words1 = set(text1.split())
        words2 = set(text2.split())

        # Remove stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words1 = words1 - stop_words
        words2 = words2 - stop_words

        if not words1 or not words2:
            return 0.0

        # Calculate Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def _calculate_keyword_similarity(self, doc1: Document, doc2: Document) -> float:
        """Calculate keyword-based similarity."""
        keywords1 = set(doc1.keywords) if doc1.keywords else set()
        keywords2 = set(doc2.keywords) if doc2.keywords else set()

        if not keywords1 or not keywords2:
            return 0.0

        # Calculate keyword overlap
        intersection = len(keywords1 & keywords2)
        union = len(keywords1 | keywords2)

        return intersection / union if union > 0 else 0.0

    def _calculate_structural_similarity(self, doc1: Document, doc2: Document) -> float:
        """Calculate structural similarity."""
        # Compare document structure (length, title presence, etc.)
        score = 0.0

        # Length similarity
        len1 = len(doc1.formatted_preview or "")
        len2 = len(doc2.formatted_preview or "")

        if len1 > 0 and len2 > 0:
            length_ratio = min(len1, len2) / max(len1, len2)
            score += length_ratio * 0.3

        # Title presence similarity
        title1 = 1 if doc1.title else 0
        title2 = 1 if doc2.title else 0
        title_similarity = 1 - abs(title1 - title2)
        score += title_similarity * 0.3

        # File type similarity
        ext1 = doc1.file_name.split('.')[-1].lower() if '.' in doc1.file_name else 'unknown'
        ext2 = doc2.file_name.split('.')[-1].lower() if '.' in doc2.file_name else 'unknown'
        type_similarity = 1 if ext1 == ext2 else 0
        score += type_similarity * 0.4

        return score

    def _find_matching_sections(self, doc1: Document, doc2: Document) -> List[Dict[str, Any]]:
        """Find matching sections between documents."""
        matching_sections = []

        text1 = doc1.formatted_preview or ""
        text2 = doc2.formatted_preview or ""

        if not text1 or not text2:
            return matching_sections

        # Simple section matching based on sentence similarity
        sentences1 = [s.strip() for s in text1.split('.') if s.strip()]
        sentences2 = [s.strip() for s in text2.split('.') if s.strip()]

        for sent1 in sentences1:
            for sent2 in sentences2:
                similarity = self._calculate_sentence_similarity(sent1, sent2)
                if similarity > 0.7:  # High similarity threshold
                    matching_sections.append({
                        'source_section': sent1,
                        'target_section': sent2,
                        'similarity': similarity,
                        'type': 'sentence_match'
                    })

        return matching_sections[:10]  # Limit results

    def _calculate_sentence_similarity(self, sent1: str, sent2: str) -> float:
        """Calculate similarity between two sentences."""
        words1 = set(sent1.lower().split())
        words2 = set(sent2.lower().split())

        if not words1 or not words2:
            return 0.0

        # Remove stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words1 = words1 - stop_words
        words2 = words2 - stop_words

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def find_similar_documents(
        self,
        target_document: Document,
        document_list: List[Document],
        min_similarity: float = 0.3,
        max_results: int = 10
    ) -> List[DocumentSimilarity]:
        """Find documents similar to target document.

        Args:
            target_document: Document to find similarities for
            document_list: List of documents to compare against
            min_similarity: Minimum similarity threshold
            max_results: Maximum number of results

        Returns:
            List of similar documents
        """
        similarities = []

        for doc in document_list:
            if doc.id == target_document.id:
                continue  # Skip self-comparison

            similarity = self.calculate_similarity(target_document, doc)

            if similarity.similarity_score >= min_similarity:
                similarities.append(similarity)

        # Sort by similarity score
        similarities.sort(key=lambda x: x.similarity_score, reverse=True)

        return similarities[:max_results]


class DocumentIntelligenceEngine:
    """Main document intelligence engine."""

    def __init__(self):
        """Initialize document intelligence engine."""
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.entity_extractor = EntityExtractor()
        self.topic_modeler = TopicModeler()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.similarity_engine = DocumentSimilarityEngine()

    @handle_errors(operation="analyze_document", component="document_intelligence")
    def analyze_document(self, document: Document) -> Dict[str, Any]:
        """Perform comprehensive document analysis.

        Args:
            document: Document to analyze

        Returns:
            Comprehensive analysis results
        """
        analysis_results = {
            'document_id': document.id,
            'analysis_timestamp': datetime.utcnow().isoformat(),
            'entities': [],
            'topics': [],
            'sentiment': None,
            'similarity_candidates': [],
            'quality_score': 0.0,
            'analysis_metadata': {}
        }

        try:
            # Extract entities
            entities = self.entity_extractor.extract_entities(document)
            analysis_results['entities'] = [
                {
                    'text': entity.text,
                    'type': entity.type,
                    'confidence': entity.confidence,
                    'context': entity.context
                }
                for entity in entities
            ]

            # Extract topics
            topics = self.topic_modeler.extract_topics(document)
            analysis_results['topics'] = [
                {
                    'name': topic.name,
                    'keywords': topic.keywords,
                    'relevance_score': topic.relevance_score,
                    'sections': topic.document_sections
                }
                for topic in topics
            ]

            # Analyze sentiment
            sentiment = self.sentiment_analyzer.analyze_sentiment(document)
            analysis_results['sentiment'] = {
                'polarity': sentiment.polarity,
                'subjectivity': sentiment.subjectivity,
                'confidence': sentiment.confidence,
                'dominant_emotion': sentiment.dominant_emotion,
                'emotion_scores': sentiment.emotion_scores
            }

            # Calculate overall quality score
            analysis_results['quality_score'] = self._calculate_document_quality(
                entities, topics, sentiment
            )

            # Add analysis metadata
            analysis_results['analysis_metadata'] = {
                'entities_count': len(entities),
                'topics_count': len(topics),
                'text_length': len(document.formatted_preview or ""),
                'processing_time_ms': 0  # Would be measured
            }

            return analysis_results

        except Exception as e:
            self.logger.error(f"Error analyzing document {document.id}: {e}")
            raise

    def _calculate_document_quality(
        self,
        entities: List[Entity],
        topics: List[Topic],
        sentiment: SentimentResult
    ) -> float:
        """Calculate overall document quality score."""
        quality = 0.5  # Base quality

        # Entity quality (more entities = richer content)
        if entities:
            entity_score = min(len(entities) / 10, 1.0)  # Up to 10 entities
            quality += entity_score * 0.2

        # Topic quality (relevant topics = better structure)
        if topics:
            topic_score = sum(topic.relevance_score for topic in topics) / len(topics)
            quality += topic_score * 0.3

        # Sentiment quality (balanced sentiment = more objective)
        if sentiment:
            # Prefer moderate subjectivity (not too objective, not too subjective)
            subjectivity_score = 1 - abs(sentiment.subjectivity - 0.5) * 2
            quality += subjectivity_score * 0.2

            # Prefer neutral to positive polarity for academic content
            polarity_score = (sentiment.polarity + 1) / 2  # Convert -1,1 to 0,1
            quality += polarity_score * 0.1

        return min(quality, 1.0)

    def find_related_documents(
        self,
        document: Document,
        document_list: List[Document],
        min_similarity: float = 0.3
    ) -> List[DocumentSimilarity]:
        """Find documents related to target document.

        Args:
            document: Target document
            document_list: List of documents to search in
            min_similarity: Minimum similarity threshold

        Returns:
            List of related documents
        """
        return self.similarity_engine.find_similar_documents(
            document, document_list, min_similarity
        )

    def extract_document_insights(self, document: Document) -> Dict[str, Any]:
        """Extract key insights from document.

        Args:
            document: Document to analyze

        Returns:
            Key insights and summary
        """
        try:
            # Get full analysis
            analysis = self.analyze_document(document)

            # Generate insights
            insights = {
                'document_id': document.id,
                'key_entities': [e['text'] for e in analysis['entities'][:5]],
                'main_topics': [t['name'] for t in analysis['topics'][:3]],
                'sentiment_summary': self._summarize_sentiment(analysis['sentiment']),
                'content_quality': self._assess_content_quality(analysis),
                'readability_score': self._calculate_readability_score(document),
                'key_findings': self._extract_key_findings(document, analysis)
            }

            return insights

        except Exception as e:
            self.logger.error(f"Error extracting insights from document {document.id}: {e}")
            return {}

    def _summarize_sentiment(self, sentiment: Dict[str, Any]) -> str:
        """Summarize sentiment analysis."""
        if not sentiment:
            return "Sentiment analysis not available"

        polarity = sentiment.get('polarity', 0)
        subjectivity = sentiment.get('subjectivity', 0)
        dominant_emotion = sentiment.get('dominant_emotion')

        # Determine sentiment description
        if polarity > 0.3:
            sentiment_desc = "Positive"
        elif polarity < -0.3:
            sentiment_desc = "Negative"
        else:
            sentiment_desc = "Neutral"

        # Determine subjectivity description
        if subjectivity > 0.7:
            subjectivity_desc = "Highly subjective"
        elif subjectivity > 0.4:
            subjectivity_desc = "Moderately subjective"
        else:
            subjectivity_desc = "Objective"

        summary = f"{sentiment_desc}, {subjectivity_desc}"
        if dominant_emotion:
            summary += f", primarily {dominant_emotion}"

        return summary

    def _assess_content_quality(self, analysis: Dict[str, Any]) -> str:
        """Assess overall content quality."""
        quality_score = analysis.get('quality_score', 0)

        if quality_score >= 0.8:
            return "Excellent"
        elif quality_score >= 0.6:
            return "Good"
        elif quality_score >= 0.4:
            return "Fair"
        else:
            return "Poor"

    def _calculate_readability_score(self, document: Document) -> float:
        """Calculate document readability score."""
        text = document.formatted_preview or ""

        if not text:
            return 0.0

        # Simple readability metrics
        sentences = text.split('.')
        words = text.split()

        if not sentences or not words:
            return 0.0

        # Average sentence length
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)

        # Average word length
        avg_word_length = sum(len(word) for word in words) / len(words)

        # Simple readability score (lower is more readable)
        readability = (avg_sentence_length * 0.4) + (avg_word_length * 0.6)

        # Convert to 0-1 scale (lower readability score = higher readability)
        return max(0, 1 - (readability / 20))

    def _extract_key_findings(self, document: Document, analysis: Dict[str, Any]) -> List[str]:
        """Extract key findings from document analysis."""
        findings = []

        # Key entities
        entities = analysis.get('entities', [])
        if entities:
            top_entities = [e['text'] for e in entities[:3]]
            findings.append(f"Key entities: {', '.join(top_entities)}")

        # Main topics
        topics = analysis.get('topics', [])
        if topics:
            top_topics = [t['name'] for t in topics[:2]]
            findings.append(f"Main topics: {', '.join(top_topics)}")

        # Sentiment insight
        sentiment = analysis.get('sentiment', {})
        if sentiment:
            sentiment_summary = self._summarize_sentiment(sentiment)
            findings.append(f"Content tone: {sentiment_summary}")

        return findings

    def batch_analyze_documents(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """Analyze multiple documents in batch.

        Args:
            documents: List of documents to analyze

        Returns:
            List of analysis results
        """
        results = []

        for document in documents:
            try:
                analysis = self.analyze_document(document)
                results.append(analysis)
            except Exception as e:
                self.logger.error(f"Error analyzing document {document.id}: {e}")
                results.append({
                    'document_id': document.id,
                    'error': str(e),
                    'analysis_timestamp': datetime.utcnow().isoformat()
                })

        return results

    def get_intelligence_summary(self, documents: List[Document]) -> Dict[str, Any]:
        """Get intelligence summary for document collection.

        Args:
            documents: List of documents to summarize

        Returns:
            Intelligence summary
        """
        try:
            # Analyze all documents
            analyses = self.batch_analyze_documents(documents)

            # Aggregate results
            summary = {
                'total_documents': len(documents),
                'analyzed_documents': len([a for a in analyses if 'error' not in a]),
                'entity_frequency': self._aggregate_entity_frequency(analyses),
                'topic_distribution': self._aggregate_topic_distribution(analyses),
                'sentiment_overview': self._aggregate_sentiment_overview(analyses),
                'quality_distribution': self._aggregate_quality_distribution(analyses),
                'summary_timestamp': datetime.utcnow().isoformat()
            }

            return summary

        except Exception as e:
            self.logger.error(f"Error creating intelligence summary: {e}")
            return {}

    def _aggregate_entity_frequency(self, analyses: List[Dict[str, Any]]) -> Dict[str, int]:
        """Aggregate entity frequency across analyses."""
        entity_counts = Counter()

        for analysis in analyses:
            if 'entities' in analysis:
                for entity in analysis['entities']:
                    entity_counts[entity['text']] += 1

        return dict(entity_counts.most_common(20))

    def _aggregate_topic_distribution(self, analyses: List[Dict[str, Any]]) -> Dict[str, int]:
        """Aggregate topic distribution across analyses."""
        topic_counts = Counter()

        for analysis in analyses:
            if 'topics' in analysis:
                for topic in analysis['topics']:
                    topic_counts[topic['name']] += 1

        return dict(topic_counts.most_common(10))

    def _aggregate_sentiment_overview(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate sentiment overview."""
        sentiments = []

        for analysis in analyses:
            if 'sentiment' in analysis:
                sentiment = analysis['sentiment']
                sentiments.append({
                    'polarity': sentiment.get('polarity', 0),
                    'subjectivity': sentiment.get('subjectivity', 0)
                })

        if not sentiments:
            return {}

        # Calculate averages
        avg_polarity = sum(s['polarity'] for s in sentiments) / len(sentiments)
        avg_subjectivity = sum(s['subjectivity'] for s in sentiments) / len(sentiments)

        # Determine overall sentiment
        if avg_polarity > 0.2:
            overall_sentiment = "Positive"
        elif avg_polarity < -0.2:
            overall_sentiment = "Negative"
        else:
            overall_sentiment = "Neutral"

        return {
            'overall_sentiment': overall_sentiment,
            'average_polarity': avg_polarity,
            'average_subjectivity': avg_subjectivity,
            'sentiment_count': len(sentiments)
        }

    def _aggregate_quality_distribution(self, analyses: List[Dict[str, Any]]) -> Dict[str, int]:
        """Aggregate quality distribution."""
        quality_ranges = {
            'excellent': 0,  # 0.8-1.0
            'good': 0,       # 0.6-0.8
            'fair': 0,       # 0.4-0.6
            'poor': 0        # 0.0-0.4
        }

        for analysis in analyses:
            quality_score = analysis.get('quality_score', 0)

            if quality_score >= 0.8:
                quality_ranges['excellent'] += 1
            elif quality_score >= 0.6:
                quality_ranges['good'] += 1
            elif quality_score >= 0.4:
                quality_ranges['fair'] += 1
            else:
                quality_ranges['poor'] += 1

        return quality_ranges


# Factory function

def create_document_intelligence_engine() -> DocumentIntelligenceEngine:
    """Create document intelligence engine with all components.

    Returns:
        Configured document intelligence engine
    """
    return DocumentIntelligenceEngine()


# Integration functions

def extract_entities_from_document(document: Document) -> List[Entity]:
    """Extract entities from document (convenience function).

    Args:
        document: Document to analyze

    Returns:
        List of extracted entities
    """
    engine = DocumentIntelligenceEngine()
    return engine.entity_extractor.extract_entities(document)


def analyze_document_sentiment(document: Document) -> SentimentResult:
    """Analyze document sentiment (convenience function).

    Args:
        document: Document to analyze

    Returns:
        Sentiment analysis result
    """
    engine = DocumentIntelligenceEngine()
    return engine.sentiment_analyzer.analyze_sentiment(document)


def find_similar_documents(
    target_document: Document,
    document_list: List[Document],
    min_similarity: float = 0.3
) -> List[DocumentSimilarity]:
    """Find similar documents (convenience function).

    Args:
        target_document: Document to find similarities for
        document_list: List of documents to compare against
        min_similarity: Minimum similarity threshold

    Returns:
        List of similar documents
    """
    engine = DocumentIntelligenceEngine()
    return engine.similarity_engine.find_similar_documents(
        target_document, document_list, min_similarity
    )
