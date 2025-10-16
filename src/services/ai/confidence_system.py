"""
AI Confidence System for Archivista AI.
Implements confidence scoring, user feedback, and Bayesian knowledge enhancement.
"""

import math
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging
import numpy as np

from ...database.models.base import Document, ConceptEntity, ConceptRelationship, BayesianEvidence
from ...core.errors.error_handler import handle_errors


@dataclass
class ConfidenceScore:
    """Confidence score with metadata."""
    value: float  # 0.0 to 1.0
    algorithm: str
    factors: Dict[str, float]
    timestamp: datetime
    model_version: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'value': self.value,
            'algorithm': self.algorithm,
            'factors': self.factors,
            'timestamp': self.timestamp.isoformat(),
            'model_version': self.model_version,
            'metadata': self.metadata
        }


@dataclass
class UserFeedback:
    """User feedback for AI corrections."""
    user_id: str
    document_id: str
    original_response: str
    user_correction: str
    feedback_type: str  # 'accuracy', 'completeness', 'clarity', 'relevance'
    confidence_rating: int  # 1-5 stars
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)


class ConfidenceCalculator:
    """Calculates confidence scores for AI responses."""

    def __init__(self):
        """Initialize confidence calculator."""
        self.logger = logging.getLogger(__name__)

        # Confidence weights for different factors
        self.weights = {
            'text_quality': 0.25,
            'context_relevance': 0.20,
            'source_reliability': 0.15,
            'response_consistency': 0.15,
            'user_history': 0.10,
            'temporal_freshness': 0.10,
            'domain_expertise': 0.05
        }

    @handle_errors(operation="calculate_response_confidence", component="confidence_calculator")
    def calculate_response_confidence(
        self,
        response_text: str,
        context_documents: List[Document],
        user_id: str,
        query: str,
        model_version: str = "1.0"
    ) -> ConfidenceScore:
        """Calculate confidence score for AI response.

        Args:
            response_text: Generated response text
            context_documents: Documents used as context
            user_id: User ID for personalization
            query: Original user query
            model_version: AI model version used

        Returns:
            Confidence score with factors
        """
        factors = {}

        # Text quality factor
        factors['text_quality'] = self._calculate_text_quality(response_text)

        # Context relevance factor
        factors['context_relevance'] = self._calculate_context_relevance(
            response_text, context_documents, query
        )

        # Source reliability factor
        factors['source_reliability'] = self._calculate_source_reliability(context_documents)

        # Response consistency factor
        factors['response_consistency'] = self._calculate_response_consistency(
            response_text, query
        )

        # User history factor
        factors['user_history'] = self._calculate_user_history_factor(user_id)

        # Temporal freshness factor
        factors['temporal_freshness'] = self._calculate_temporal_freshness(context_documents)

        # Domain expertise factor
        factors['domain_expertise'] = self._calculate_domain_expertise(
            response_text, context_documents
        )

        # Calculate weighted confidence
        confidence_value = sum(
            factors.get(factor, 0.0) * weight
            for factor, weight in self.weights.items()
        )

        # Ensure confidence is in valid range
        confidence_value = max(0.0, min(1.0, confidence_value))

        return ConfidenceScore(
            value=confidence_value,
            algorithm="weighted_multifactor_v1",
            factors=factors,
            timestamp=datetime.utcnow(),
            model_version=model_version,
            metadata={
                'response_length': len(response_text),
                'context_docs_count': len(context_documents),
                'query_length': len(query)
            }
        )

    def _calculate_text_quality(self, text: str) -> float:
        """Calculate text quality factor."""
        if not text:
            return 0.0

        score = 0.0

        # Length factor (not too short, not too long)
        word_count = len(text.split())
        if 10 <= word_count <= 500:
            score += 0.3
        elif word_count < 10:
            score += 0.1
        else:
            score += 0.2

        # Coherence factor (sentences with proper structure)
        sentences = text.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)

        if 5 <= avg_sentence_length <= 25:
            score += 0.3
        else:
            score += 0.1

        # Grammar indicators (basic checks)
        if not text.endswith('.') and len(text) > 20:
            score += 0.1

        # Capitalization
        if text[0].isupper():
            score += 0.1

        # Punctuation balance
        punctuation_ratio = len([c for c in text if c in '.,!?']) / len(text)
        if 0.01 <= punctuation_ratio <= 0.1:
            score += 0.2

        return min(score, 1.0)

    def _calculate_context_relevance(self, response: str, documents: List[Document], query: str) -> float:
        """Calculate context relevance factor."""
        if not documents:
            return 0.3  # Base score without context

        score = 0.0
        query_terms = set(query.lower().split())

        # Check if response addresses query terms
        response_lower = response.lower()
        query_matches = sum(1 for term in query_terms if term in response_lower)
        query_coverage = query_matches / len(query_terms) if query_terms else 0
        score += query_coverage * 0.4

        # Check document content relevance
        total_relevance = 0
        for doc in documents:
            doc_relevance = 0

            # Title relevance
            if doc.title:
                title_terms = set(doc.title.lower().split())
                title_overlap = len(query_terms & title_terms) / len(query_terms) if query_terms else 0
                doc_relevance += title_overlap * 0.3

            # Content relevance
            if doc.formatted_preview:
                content_terms = set(doc.formatted_preview.lower().split())
                content_overlap = len(query_terms & content_terms) / len(query_terms) if query_terms else 0
                doc_relevance += content_overlap * 0.2

            # Keyword relevance
            if doc.keywords:
                keyword_terms = set(' '.join(doc.keywords).lower().split())
                keyword_overlap = len(query_terms & keyword_terms) / len(query_terms) if query_terms else 0
                doc_relevance += keyword_overlap * 0.5

            total_relevance += doc_relevance

        # Average relevance across documents
        if documents:
            score += (total_relevance / len(documents)) * 0.6

        return min(score, 1.0)

    def _calculate_source_reliability(self, documents: List[Document]) -> float:
        """Calculate source reliability factor."""
        if not documents:
            return 0.5  # Neutral score

        total_reliability = 0.0

        for doc in documents:
            reliability = 0.5  # Base reliability

            # Boost for processed documents
            if doc.processing_status.value == 'completed':
                reliability += 0.2

            # Boost for documents with good metadata
            if doc.title:
                reliability += 0.1
            if doc.keywords:
                reliability += 0.1
            if doc.content_hash:
                reliability += 0.1

            # Boost for recent documents
            if doc.created_at:
                days_old = (datetime.utcnow() - doc.created_at).days
                if days_old < 30:
                    reliability += 0.1
                elif days_old < 365:
                    reliability += 0.05

            total_reliability += min(reliability, 1.0)

        return total_reliability / len(documents)

    def _calculate_response_consistency(self, response: str, query: str) -> float:
        """Calculate response consistency factor."""
        # Simple consistency check
        response_words = set(response.lower().split())
        query_words = set(query.lower().split())

        # Remove stop words for better comparison
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        response_filtered = response_words - stop_words
        query_filtered = query_words - stop_words

        if not query_filtered:
            return 0.5

        # Calculate overlap
        overlap = len(response_filtered & query_filtered)
        coverage = overlap / len(query_filtered)

        return min(coverage * 2, 1.0)  # Boost the score

    def _calculate_user_history_factor(self, user_id: str) -> float:
        """Calculate user history factor."""
        # This would analyze user's interaction history
        # For now, return neutral score
        return 0.5

    def _calculate_temporal_freshness(self, documents: List[Document]) -> float:
        """Calculate temporal freshness factor."""
        if not documents:
            return 0.5

        current_time = datetime.utcnow()
        total_freshness = 0.0

        for doc in documents:
            if doc.created_at:
                days_old = (current_time - doc.created_at).days
                # Exponential decay: newer documents get higher score
                freshness = math.exp(-days_old / 365)  # Decay over a year
                total_freshness += freshness

        return total_freshness / len(documents)

    def _calculate_domain_expertise(self, response: str, documents: List[Document]) -> float:
        """Calculate domain expertise factor."""
        # Analyze if response shows domain knowledge
        expertise_indicators = [
            'research', 'study', 'analysis', 'methodology', 'conclusion',
            'evidence', 'data', 'results', 'findings', 'theory'
        ]

        response_lower = response.lower()
        matches = sum(1 for indicator in expertise_indicators if indicator in response_lower)

        return min(matches / 5, 1.0)  # Up to 5 indicators


class ConfidenceVisualizer:
    """Visualizes confidence scores and provides user feedback."""

    def __init__(self):
        """Initialize confidence visualizer."""
        self.logger = logging.getLogger(__name__)

    def create_confidence_display(self, confidence: ConfidenceScore) -> str:
        """Create HTML display for confidence score.

        Args:
            confidence: Confidence score to display

        Returns:
            HTML string for display
        """
        # Determine color based on confidence level
        if confidence.value >= 0.8:
            color = "#2ca02c"  # Green
            level = "High"
        elif confidence.value >= 0.6:
            color = "#ff7f0e"  # Orange
            level = "Medium"
        else:
            color = "#d62728"  # Red
            level = "Low"

        # Create progress bar
        progress_html = f"""
        <div style="
            background: #f0f0f0;
            border-radius: 10px;
            height: 8px;
            margin: 8px 0;
            overflow: hidden;
        ">
            <div style="
                background: {color};
                width: {confidence.value * 100}%;
                height: 100%;
                border-radius: 10px;
                transition: width 0.3s ease;
            "></div>
        </div>
        """

        # Create factors breakdown
        factors_html = ""
        for factor, value in confidence.factors.items():
            factor_color = self._get_factor_color(value)
            factors_html += f"""
            <div style="
                display: flex;
                justify-content: space-between;
                margin: 4px 0;
                font-size: 0.8rem;
            ">
                <span style="color: #666;">{factor.replace('_', ' ').title()}</span>
                <span style="color: {factor_color};">{value".2f"}</span>
            </div>
            """

        # Complete display
        display_html = f"""
        <div style="
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 12px;
            margin: 8px 0;
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        ">
            <div style="
                display: flex;
                align-items: center;
                margin-bottom: 8px;
            ">
                <span style="
                    background: {color};
                    color: white;
                    padding: 4px 8px;
                    border-radius: 12px;
                    font-size: 0.75rem;
                    font-weight: 500;
                ">{level} Confidence</span>
                <span style="
                    margin-left: auto;
                    font-size: 0.9rem;
                    font-weight: 600;
                    color: {color};
                ">{confidence.value".1%"}</span>
            </div>

            {progress_html}

            <div style="margin-top: 8px;">
                <button onclick="toggleFactors()" style="
                    background: none;
                    border: none;
                    color: #666;
                    font-size: 0.8rem;
                    cursor: pointer;
                    text-decoration: underline;
                ">View Factors</button>
            </div>

            <div id="confidenceFactors" style="display: none; margin-top: 8px;">
                {factors_html}
            </div>

            <script>
            function toggleFactors() {{
                var factors = document.getElementById('confidenceFactors');
                factors.style.display = factors.style.display === 'none' ? 'block' : 'none';
            }}
            </script>
        </div>
        """

        return display_html

    def _get_factor_color(self, value: float) -> str:
        """Get color for factor value."""
        if value >= 0.8:
            return "#2ca02c"
        elif value >= 0.6:
            return "#ff7f0e"
        else:
            return "#d62728"

    def create_confidence_badge(self, confidence: float) -> str:
        """Create simple confidence badge.

        Args:
            confidence: Confidence value (0.0 to 1.0)

        Returns:
            HTML badge string
        """
        if confidence >= 0.8:
            color = "#2ca02c"
            text = "High"
        elif confidence >= 0.6:
            color = "#ff7f0e"
            text = "Medium"
        else:
            color = "#d62728"
            text = "Low"

        return f"""
        <span style="
            background: {color};
            color: white;
            padding: 2px 6px;
            border-radius: 10px;
            font-size: 0.7rem;
            font-weight: 500;
        ">{text} ({confidence".0%"})</span>
        """


class UserFeedbackSystem:
    """System for collecting and processing user feedback."""

    def __init__(self, document_repository):
        """Initialize user feedback system.

        Args:
            document_repository: Document repository for context
        """
        self.document_repository = document_repository
        self.logger = logging.getLogger(__name__)

        # Feedback storage
        self.feedback_history: List[UserFeedback] = []
        self.feedback_stats = defaultdict(int)

    @handle_errors(operation="collect_feedback", component="feedback_system")
    def collect_feedback(
        self,
        user_id: str,
        document_id: str,
        original_response: str,
        user_correction: str,
        feedback_type: str,
        confidence_rating: int
    ) -> bool:
        """Collect user feedback for AI response.

        Args:
            user_id: User providing feedback
            document_id: Document context
            original_response: Original AI response
            user_correction: User's correction/suggestion
            feedback_type: Type of feedback
            confidence_rating: User's confidence rating (1-5)

        Returns:
            True if feedback collected successfully
        """
        try:
            feedback = UserFeedback(
                user_id=user_id,
                document_id=document_id,
                original_response=original_response,
                user_correction=user_correction,
                feedback_type=feedback_type,
                confidence_rating=confidence_rating,
                timestamp=datetime.utcnow()
            )

            self.feedback_history.append(feedback)

            # Update stats
            self.feedback_stats['total_feedback'] += 1
            self.feedback_stats[f'type_{feedback_type}'] += 1
            self.feedback_stats[f'rating_{confidence_rating}'] += 1

            # Keep only recent feedback (last 1000)
            if len(self.feedback_history) > 1000:
                self.feedback_history = self.feedback_history[-1000:]

            self.logger.info(f"Feedback collected from user {user_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error collecting feedback: {e}")
            return False

    def get_feedback_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get feedback summary for time period.

        Args:
            days: Days to look back

        Returns:
            Feedback summary dictionary
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        recent_feedback = [
            f for f in self.feedback_history
            if f.timestamp >= cutoff_date
        ]

        if not recent_feedback:
            return {}

        # Calculate summary statistics
        total_feedback = len(recent_feedback)
        avg_rating = sum(f.confidence_rating for f in recent_feedback) / total_feedback

        # Feedback by type
        type_counts = defaultdict(int)
        for feedback in recent_feedback:
            type_counts[feedback.feedback_type] += 1

        # Rating distribution
        rating_counts = defaultdict(int)
        for feedback in recent_feedback:
            rating_counts[feedback.confidence_rating] += 1

        return {
            'total_feedback': total_feedback,
            'average_rating': avg_rating,
            'feedback_by_type': dict(type_counts),
            'rating_distribution': dict(rating_counts),
            'time_period_days': days,
            'oldest_feedback': min(f.timestamp for f in recent_feedback).isoformat(),
            'newest_feedback': max(f.timestamp for f in recent_feedback).isoformat()
        }

    def get_feedback_for_training(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get feedback data for AI model training.

        Args:
            limit: Maximum number of feedback items

        Returns:
            List of feedback data for training
        """
        # Get recent feedback for training
        recent_feedback = self.feedback_history[-limit:]

        training_data = []
        for feedback in recent_feedback:
            training_data.append({
                'original_response': feedback.original_response,
                'user_correction': feedback.user_correction,
                'feedback_type': feedback.feedback_type,
                'confidence_rating': feedback.confidence_rating,
                'timestamp': feedback.timestamp.isoformat(),
                'context': feedback.context
            })

        return training_data


class BayesianKnowledgeEnhancer:
    """Bayesian inference system for knowledge enhancement."""

    def __init__(self, document_repository):
        """Initialize Bayesian enhancer.

        Args:
            document_repository: Document repository
        """
        self.document_repository = document_repository
        self.logger = logging.getLogger(__name__)

        # Bayesian priors
        self.priors = {
            'entity_confidence': 0.5,
            'relationship_strength': 0.3,
            'temporal_decay': 0.1
        }

        # Evidence storage
        self.evidence_cache: Dict[str, List[BayesianEvidence]] = {}

    @handle_errors(operation="update_bayesian_knowledge", component="bayesian_enhancer")
    def update_bayesian_knowledge(
        self,
        user_id: str,
        documents: List[Document],
        feedback_history: List[UserFeedback] = None
    ) -> Dict[str, Any]:
        """Update Bayesian knowledge base with new evidence.

        Args:
            user_id: User ID for personalization
            documents: Documents to process
            feedback_history: User feedback history

        Returns:
            Update results
        """
        try:
            results = {
                'entities_updated': 0,
                'relationships_updated': 0,
                'evidence_added': 0,
                'confidence_improvements': [],
                'processing_time_ms': 0
            }

            start_time = datetime.utcnow()

            # Process each document
            for document in documents:
                # Extract entities and relationships
                entities = self._extract_entities(document)
                relationships = self._extract_relationships(document, entities)

                # Update with Bayesian inference
                for entity in entities:
                    confidence_improvement = self._update_entity_confidence(
                        entity, document, user_id
                    )
                    if confidence_improvement > 0.1:  # Significant improvement
                        results['confidence_improvements'].append({
                            'entity': entity.entity_name,
                            'improvement': confidence_improvement
                        })

                results['entities_updated'] += len(entities)
                results['relationships_updated'] += len(relationships)

            # Apply temporal decay
            self._apply_temporal_decay(user_id)

            # Process user feedback for learning
            if feedback_history:
                self._process_feedback_for_learning(feedback_history, user_id)

            results['processing_time_ms'] = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )

            return results

        except Exception as e:
            self.logger.error(f"Error updating Bayesian knowledge: {e}")
            raise

    def _extract_entities(self, document: Document) -> List[ConceptEntity]:
        """Extract entities from document using simple heuristics."""
        entities = []

        # Simple entity extraction based on keywords and content
        if document.keywords:
            for keyword in document.keywords:
                entity = ConceptEntity(
                    user_id=0,  # Would be set properly
                    entity_type="concept",
                    entity_name=keyword,
                    entity_description=f"Extracted from {document.file_name}",
                    source_file_name=document.file_name,
                    confidence_score=0.7  # Base confidence
                )
                entities.append(entity)

        # Extract from title if available
        if document.title:
            title_words = document.title.split()
            for word in title_words:
                if len(word) > 5:  # Longer words might be entities
                    entity = ConceptEntity(
                        user_id=0,
                        entity_type="term",
                        entity_name=word,
                        entity_description=f"Extracted from title: {document.title}",
                        source_file_name=document.file_name,
                        confidence_score=0.6
                    )
                    entities.append(entity)

        return entities

    def _extract_relationships(
        self,
        document: Document,
        entities: List[ConceptEntity]
    ) -> List[ConceptRelationship]:
        """Extract relationships between entities."""
        relationships = []

        if len(entities) < 2:
            return relationships

        # Simple relationship extraction based on co-occurrence
        for i, entity1 in enumerate(entities):
            for entity2 in entities[i+1:]:
                # Create relationship based on document context
                relationship = ConceptRelationship(
                    user_id=0,
                    source_entity_id=entity1.id or 0,
                    target_entity_id=entity2.id or 0,
                    relationship_type="related_to",
                    relationship_description=f"Co-occur in {document.file_name}",
                    confidence_score=0.5  # Base confidence
                )
                relationships.append(relationship)

        return relationships

    def _update_entity_confidence(
        self,
        entity: ConceptEntity,
        document: Document,
        user_id: str
    ) -> float:
        """Update entity confidence using Bayesian inference."""
        # Get existing evidence for this entity
        entity_key = f"{user_id}_{entity.entity_name}"
        existing_evidence = self.evidence_cache.get(entity_key, [])

        # Calculate prior probability
        prior = self.priors['entity_confidence']

        # Calculate likelihood based on document quality
        likelihood = self._calculate_entity_likelihood(entity, document)

        # Bayesian update
        posterior = (likelihood * prior) / (likelihood * prior + (1 - likelihood) * (1 - prior))

        # Calculate improvement
        improvement = posterior - entity.confidence_score

        # Update entity confidence
        entity.confidence_score = posterior

        # Add evidence
        evidence = BayesianEvidence(
            entity_id=entity.id or 0,
            evidence_type="document_quality",
            evidence_data={
                'document_id': document.id,
                'document_quality': self._assess_document_quality(document),
                'entity_occurrence': 'title' if document.title and entity.entity_name in document.title else 'content'
            },
            confidence_weight=1.0
        )

        existing_evidence.append(evidence)
        self.evidence_cache[entity_key] = existing_evidence[-10:]  # Keep last 10

        return improvement

    def _calculate_entity_likelihood(self, entity: ConceptEntity, document: Document) -> float:
        """Calculate likelihood of entity being correct."""
        likelihood = 0.5  # Base likelihood

        # Boost likelihood based on document quality
        doc_quality = self._assess_document_quality(document)
        likelihood += doc_quality * 0.3

        # Boost if entity appears in title
        if document.title and entity.entity_name.lower() in document.title.lower():
            likelihood += 0.2

        # Boost if entity is in keywords
        if document.keywords and entity.entity_name.lower() in [k.lower() for k in document.keywords]:
            likelihood += 0.2

        return min(likelihood, 1.0)

    def _assess_document_quality(self, document: Document) -> float:
        """Assess overall document quality."""
        quality = 0.5  # Base quality

        # Processing status
        if document.processing_status.value == 'completed':
            quality += 0.2

        # Metadata completeness
        if document.title:
            quality += 0.1
        if document.keywords:
            quality += 0.1
        if document.content_hash:
            quality += 0.1

        # Content length (reasonable length is better)
        if document.formatted_preview:
            word_count = len(document.formatted_preview.split())
            if 50 <= word_count <= 2000:
                quality += 0.1

        return min(quality, 1.0)

    def _apply_temporal_decay(self, user_id: str) -> None:
        """Apply temporal decay to confidence scores."""
        decay_factor = math.exp(-self.priors['temporal_decay'])

        # This would update confidence scores in database
        # For now, just log the operation
        self.logger.info(f"Applied temporal decay (factor: {decay_factor}) for user {user_id}")

    def _process_feedback_for_learning(
        self,
        feedback_history: List[UserFeedback],
        user_id: str
    ) -> None:
        """Process user feedback for learning."""
        for feedback in feedback_history[-50:]:  # Process last 50 feedback items
            # Analyze feedback for pattern learning
            if feedback.feedback_type == 'accuracy':
                self._learn_from_accuracy_feedback(feedback)
            elif feedback.feedback_type == 'completeness':
                self._learn_from_completeness_feedback(feedback)

    def _learn_from_accuracy_feedback(self, feedback: UserFeedback) -> None:
        """Learn from accuracy feedback."""
        # Analyze difference between original response and user correction
        original_words = set(feedback.original_response.lower().split())
        correction_words = set(feedback.user_correction.lower().split())

        # Calculate similarity
        if original_words or correction_words:
            overlap = len(original_words & correction_words)
            total = len(original_words | correction_words)
            similarity = overlap / total if total > 0 else 0

            # Adjust future confidence based on feedback
            if feedback.confidence_rating <= 2:  # Low rating
                # Reduce confidence for similar responses
                pass  # Implementation would adjust model parameters

    def _learn_from_completeness_feedback(self, feedback: UserFeedback) -> None:
        """Learn from completeness feedback."""
        # Analyze if response was complete enough
        original_length = len(feedback.original_response.split())
        correction_length = len(feedback.user_correction.split())

        # If user added significant content, boost completeness requirements
        if correction_length > original_length * 1.5:
            # Adjust model parameters for more complete responses
            pass

    def get_user_knowledge_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user's personalized knowledge profile.

        Args:
            user_id: User ID

        Returns:
            Knowledge profile dictionary
        """
        try:
            # Get user's documents and interactions
            user_docs = self.document_repository.get_by_user(int(user_id))

            profile = {
                'user_id': user_id,
                'total_documents': len(user_docs),
                'preferred_categories': self._get_preferred_categories(user_docs),
                'expertise_areas': self._get_expertise_areas(user_docs),
                'learning_progression': self._get_learning_progression(user_docs),
                'confidence_preferences': self._get_confidence_preferences(user_id),
                'last_updated': datetime.utcnow().isoformat()
            }

            return profile

        except Exception as e:
            self.logger.error(f"Error getting knowledge profile for user {user_id}: {e}")
            return {}

    def _get_preferred_categories(self, documents: List[Document]) -> List[str]:
        """Get user's preferred document categories."""
        categories = []

        for doc in documents:
            if doc.file_name.lower().endswith('.pdf'):
                categories.append('academic')
            elif doc.file_name.lower().endswith(('.docx', '.doc')):
                categories.append('documents')
            else:
                categories.append('other')

        # Count frequency
        category_counts = defaultdict(int)
        for category in categories:
            category_counts[category] += 1

        # Return top categories
        return [
            category for category, count in
            sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        ]

    def _get_expertise_areas(self, documents: List[Document]) -> List[str]:
        """Get user's expertise areas based on document content."""
        expertise_keywords = defaultdict(int)

        for doc in documents:
            if doc.keywords:
                for keyword in doc.keywords:
                    expertise_keywords[keyword.lower()] += 1

        # Return top expertise areas
        return [
            keyword for keyword, count in
            sorted(expertise_keywords.items(), key=lambda x: x[1], reverse=True)[:5]
        ]

    def _get_learning_progression(self, documents: List[Document]) -> Dict[str, Any]:
        """Get user's learning progression over time."""
        if not documents:
            return {}

        # Sort documents by creation date
        sorted_docs = sorted(documents, key=lambda x: x.created_at or datetime.min)

        # Analyze progression
        progression = {
            'total_documents': len(documents),
            'date_range': {
                'first_document': sorted_docs[0].created_at.isoformat() if sorted_docs[0].created_at else None,
                'last_document': sorted_docs[-1].created_at.isoformat() if sorted_docs[-1].created_at else None
            },
            'activity_level': self._calculate_activity_level(documents)
        }

        return progression

    def _calculate_activity_level(self, documents: List[Document]) -> str:
        """Calculate user's activity level."""
        if not documents:
            return 'inactive'

        # Count documents per month
        monthly_counts = defaultdict(int)
        for doc in documents:
            if doc.created_at:
                month_key = doc.created_at.strftime('%Y-%m')
                monthly_counts[month_key] += 1

        avg_monthly = sum(monthly_counts.values()) / len(monthly_counts) if monthly_counts else 0

        if avg_monthly >= 10:
            return 'high'
        elif avg_monthly >= 5:
            return 'medium'
        else:
            return 'low'

    def _get_confidence_preferences(self, user_id: str) -> Dict[str, float]:
        """Get user's confidence preferences based on feedback."""
        # This would analyze user's feedback patterns
        # For now, return default preferences
        return {
            'preferred_confidence_threshold': 0.7,
            'tolerance_for_uncertainty': 0.3,
            'preference_for_detailed_responses': 0.6
        }


class ConfidenceThresholdManager:
    """Manages confidence thresholds for different operations."""

    def __init__(self):
        """Initialize threshold manager."""
        self.logger = logging.getLogger(__name__)

        # Default thresholds
        self.thresholds = {
            'high_confidence_response': 0.8,
            'medium_confidence_response': 0.6,
            'low_confidence_response': 0.4,
            'require_user_confirmation': 0.3,
            'block_response': 0.1
        }

        # User-specific thresholds
        self.user_thresholds: Dict[str, Dict[str, float]] = {}

    def get_threshold(self, threshold_type: str, user_id: str = None) -> float:
        """Get confidence threshold.

        Args:
            threshold_type: Type of threshold
            user_id: User ID for personalized threshold

        Returns:
            Threshold value
        """
        if user_id and user_id in self.user_thresholds:
            return self.user_thresholds[user_id].get(threshold_type, self.thresholds[threshold_type])

        return self.thresholds.get(threshold_type, 0.5)

    def set_user_threshold(self, user_id: str, threshold_type: str, value: float) -> bool:
        """Set personalized threshold for user.

        Args:
            user_id: User ID
            threshold_type: Type of threshold
            value: Threshold value

        Returns:
            True if set successfully
        """
        try:
            if user_id not in self.user_thresholds:
                self.user_thresholds[user_id] = {}

            self.user_thresholds[user_id][threshold_type] = value
            self.logger.info(f"Set threshold {threshold_type}={value} for user {user_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error setting user threshold: {e}")
            return False

    def should_require_confirmation(self, confidence: float, user_id: str = None) -> bool:
        """Check if response should require user confirmation.

        Args:
            confidence: Confidence score
            user_id: User ID

        Returns:
            True if confirmation required
        """
        threshold = self.get_threshold('require_user_confirmation', user_id)
        return confidence < threshold

    def should_block_response(self, confidence: float, user_id: str = None) -> bool:
        """Check if response should be blocked.

        Args:
            confidence: Confidence score
            user_id: User ID

        Returns:
            True if response should be blocked
        """
        threshold = self.get_threshold('block_response', user_id)
        return confidence < threshold

    def get_confidence_level(self, confidence: float, user_id: str = None) -> str:
        """Get confidence level description.

        Args:
            confidence: Confidence score
            user_id: User ID

        Returns:
            Confidence level string
        """
        if confidence >= self.get_threshold('high_confidence_response', user_id):
            return 'high'
        elif confidence >= self.get_threshold('medium_confidence_response', user_id):
            return 'medium'
        else:
            return 'low'


# Factory functions

def create_confidence_calculator() -> ConfidenceCalculator:
    """Create confidence calculator with default weights."""
    return ConfidenceCalculator()


def create_confidence_visualizer() -> ConfidenceVisualizer:
    """Create confidence visualizer."""
    return ConfidenceVisualizer()


def create_user_feedback_system(document_repository) -> UserFeedbackSystem:
    """Create user feedback system."""
    return UserFeedbackSystem(document_repository)


def create_bayesian_enhancer(document_repository) -> BayesianKnowledgeEnhancer:
    """Create Bayesian knowledge enhancer."""
    return BayesianKnowledgeEnhancer(document_repository)


def create_confidence_threshold_manager() -> ConfidenceThresholdManager:
    """Create confidence threshold manager."""
    return ConfidenceThresholdManager()


# Integration function

def create_confidence_system(document_repository) -> Dict[str, Any]:
    """Create complete confidence system.

    Args:
        document_repository: Document repository

    Returns:
        Dictionary with all confidence system components
    """
    return {
        'calculator': create_confidence_calculator(),
        'visualizer': create_confidence_visualizer(),
        'feedback_system': create_user_feedback_system(document_repository),
        'bayesian_enhancer': create_bayesian_enhancer(document_repository),
        'threshold_manager': create_confidence_threshold_manager()
    }
