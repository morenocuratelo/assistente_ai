"""
Smart Suggestions System for Archivista AI.
Implements context-aware suggestions, user behavior learning, and proactive assistance.
"""

import json
import math
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import logging
import re

from ...database.models.base import Document, User, UserActivity
from ...core.errors.error_handler import handle_errors
from ...core.performance.optimizer import cache_result


@dataclass
class Suggestion:
    """Smart suggestion with metadata."""
    id: str
    type: str  # 'document', 'action', 'learning', 'organization'
    title: str
    description: str
    confidence: float
    action_data: Dict[str, Any]
    context: Dict[str, Any]
    created_at: datetime
    expires_at: Optional[datetime] = None
    user_id: Optional[str] = None
    project_id: Optional[str] = None

    def is_expired(self) -> bool:
        """Check if suggestion is expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'description': self.description,
            'confidence': self.confidence,
            'action_data': self.action_data,
            'context': self.context,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'user_id': self.user_id,
            'project_id': self.project_id
        }


@dataclass
class UserBehaviorProfile:
    """User behavior profile for personalized suggestions."""
    user_id: str
    document_preferences: Dict[str, float] = field(default_factory=dict)
    action_frequencies: Dict[str, int] = field(default_factory=dict)
    time_patterns: Dict[str, List[str]] = field(default_factory=dict)
    skill_level: str = "beginner"  # beginner, intermediate, advanced
    learning_goals: List[str] = field(default_factory=list)
    preferred_content_types: List[str] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.utcnow)


class UserBehaviorAnalyzer:
    """Analyzes user behavior to create personalized profiles."""

    def __init__(self, user_activity_repository):
        """Initialize behavior analyzer.

        Args:
            user_activity_repository: Repository for user activity data
        """
        self.user_activity_repository = user_activity_repository
        self.logger = logging.getLogger(__name__)
        self.profiles: Dict[str, UserBehaviorProfile] = {}

    @handle_errors(operation="analyze_user_behavior", component="behavior_analyzer")
    def analyze_user_behavior(self, user_id: str, days: int = 30) -> UserBehaviorProfile:
        """Analyze user behavior and create/update profile.

        Args:
            user_id: User ID to analyze
            days: Days to look back for analysis

        Returns:
            Updated user behavior profile
        """
        # Get or create profile
        if user_id not in self.profiles:
            self.profiles[user_id] = UserBehaviorProfile(user_id=user_id)

        profile = self.profiles[user_id]

        try:
            # Get user activity data
            activities = self._get_user_activities(user_id, days)

            # Analyze document preferences
            profile.document_preferences = self._analyze_document_preferences(activities)

            # Analyze action frequencies
            profile.action_frequencies = self._analyze_action_frequencies(activities)

            # Analyze time patterns
            profile.time_patterns = self._analyze_time_patterns(activities)

            # Update skill level
            profile.skill_level = self._assess_skill_level(activities)

            # Update learning goals
            profile.learning_goals = self._extract_learning_goals(activities)

            # Update preferred content types
            profile.preferred_content_types = self._get_preferred_content_types(activities)

            profile.last_updated = datetime.utcnow()

            self.logger.info(f"Updated behavior profile for user {user_id}")
            return profile

        except Exception as e:
            self.logger.error(f"Error analyzing user behavior for {user_id}: {e}")
            return profile

    def _get_user_activities(self, user_id: str, days: int) -> List[Dict[str, Any]]:
        """Get user activities for analysis."""
        # This would query the user_activity table
        # For now, return mock data
        return [
            {
                'action_type': 'document_upload',
                'target_type': 'document',
                'timestamp': datetime.utcnow() - timedelta(days=i),
                'metadata': {'file_type': 'pdf', 'category': 'academic'}
            }
            for i in range(min(days, 10))
        ]

    def _analyze_document_preferences(self, activities: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze document type preferences."""
        preferences = defaultdict(int)

        for activity in activities:
            if activity['target_type'] == 'document':
                file_type = activity.get('metadata', {}).get('file_type', 'unknown')
                preferences[file_type] += 1

        # Convert to normalized scores
        total = sum(preferences.values())
        if total > 0:
            return {k: v/total for k, v in preferences.items()}

        return {}

    def _analyze_action_frequencies(self, activities: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze action frequencies."""
        frequencies = Counter()

        for activity in activities:
            frequencies[activity['action_type']] += 1

        return dict(frequencies)

    def _analyze_time_patterns(self, activities: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Analyze time patterns."""
        patterns = {
            'active_hours': [],
            'active_days': [],
            'session_duration': []
        }

        for activity in activities:
            timestamp = activity.get('timestamp', datetime.utcnow())
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)

            # Active hours
            hour = timestamp.hour
            if hour not in patterns['active_hours']:
                patterns['active_hours'].append(hour)

            # Active days
            day = timestamp.strftime('%A')
            if day not in patterns['active_days']:
                patterns['active_days'].append(day)

        return patterns

    def _assess_skill_level(self, activities: List[Dict[str, Any]]) -> str:
        """Assess user skill level."""
        if not activities:
            return 'beginner'

        # Simple skill assessment based on activity diversity
        unique_actions = set(a['action_type'] for a in activities)

        if len(unique_actions) >= 5:
            return 'advanced'
        elif len(unique_actions) >= 3:
            return 'intermediate'
        else:
            return 'beginner'

    def _extract_learning_goals(self, activities: List[Dict[str, Any]]) -> List[str]:
        """Extract learning goals from activities."""
        # Analyze patterns to infer learning goals
        goals = []

        # Check for academic content
        academic_activities = [
            a for a in activities
            if a.get('metadata', {}).get('category') == 'academic'
        ]

        if len(academic_activities) > 5:
            goals.append('academic_research')

        # Check for document organization
        organization_activities = [
            a for a in activities
            if 'organize' in a['action_type']
        ]

        if len(organization_activities) > 3:
            goals.append('document_organization')

        return goals

    def _get_preferred_content_types(self, activities: List[Dict[str, Any]]) -> List[str]:
        """Get preferred content types."""
        content_types = []

        for activity in activities:
            file_type = activity.get('metadata', {}).get('file_type')
            if file_type and file_type not in content_types:
                content_types.append(file_type)

        return content_types


class ContextAwareSuggestionEngine:
    """Engine for generating context-aware suggestions."""

    def __init__(self, document_repository, user_activity_repository):
        """Initialize suggestion engine.

        Args:
            document_repository: Document repository
            user_activity_repository: User activity repository
        """
        self.document_repository = document_repository
        self.user_activity_repository = user_activity_repository
        self.behavior_analyzer = UserBehaviorAnalyzer(user_activity_repository)
        self.logger = logging.getLogger(__name__)

        # Suggestion generators
        self.suggestion_generators = {
            'document': self._generate_document_suggestions,
            'action': self._generate_action_suggestions,
            'learning': self._generate_learning_suggestions,
            'organization': self._generate_organization_suggestions
        }

    @handle_errors(operation="generate_suggestions", component="suggestion_engine")
    def generate_suggestions(
        self,
        user_id: str,
        context: Dict[str, Any],
        limit: int = 10
    ) -> List[Suggestion]:
        """Generate personalized suggestions for user.

        Args:
            user_id: User ID
            context: Current context information
            limit: Maximum number of suggestions

        Returns:
            List of personalized suggestions
        """
        try:
            # Get user behavior profile
            profile = self.behavior_analyzer.analyze_user_behavior(user_id)

            # Get current context
            current_page = context.get('current_page', 'unknown')
            recent_actions = context.get('recent_actions', [])
            active_documents = context.get('active_documents', [])

            suggestions = []

            # Generate suggestions based on context
            if current_page == 'archive':
                suggestions.extend(self._generate_archive_suggestions(user_id, profile, context))
            elif current_page == 'chat':
                suggestions.extend(self._generate_chat_suggestions(user_id, profile, context))
            elif current_page == 'dashboard':
                suggestions.extend(self._generate_dashboard_suggestions(user_id, profile, context))

            # Generate general suggestions
            suggestions.extend(self._generate_general_suggestions(user_id, profile, context))

            # Filter and rank suggestions
            filtered_suggestions = self._filter_suggestions(suggestions, profile)
            ranked_suggestions = self._rank_suggestions(filtered_suggestions, profile)

            # Limit results
            return ranked_suggestions[:limit]

        except Exception as e:
            self.logger.error(f"Error generating suggestions for user {user_id}: {e}")
            return []

    def _generate_archive_suggestions(
        self,
        user_id: str,
        profile: UserBehaviorProfile,
        context: Dict[str, Any]
    ) -> List[Suggestion]:
        """Generate archive-specific suggestions."""
        suggestions = []

        # Suggest document organization
        if profile.action_frequencies.get('document_upload', 0) > 5:
            suggestions.append(Suggestion(
                id=f"org_{user_id}_{int(datetime.utcnow().timestamp())}",
                type="organization",
                title="Organize Your Documents",
                description="You have many documents. Consider organizing them by category or project.",
                confidence=0.8,
                action_data={'action': 'organize_documents', 'suggested_categories': ['academic', 'research']},
                context={'page': 'archive', 'trigger': 'many_documents'},
                created_at=datetime.utcnow(),
                user_id=user_id
            ))

        # Suggest search improvement
        if profile.action_frequencies.get('search', 0) > 10:
            suggestions.append(Suggestion(
                id=f"search_{user_id}_{int(datetime.utcnow().timestamp())}",
                type="action",
                title="Use Advanced Search",
                description="Try advanced search filters for better results.",
                confidence=0.7,
                action_data={'action': 'show_advanced_search'},
                context={'page': 'archive', 'trigger': 'frequent_search'},
                created_at=datetime.utcnow(),
                user_id=user_id
            ))

        return suggestions

    def _generate_chat_suggestions(
        self,
        user_id: str,
        profile: UserBehaviorProfile,
        context: Dict[str, Any]
    ) -> List[Suggestion]:
        """Generate chat-specific suggestions."""
        suggestions = []

        # Suggest document context
        if not context.get('active_documents'):
            suggestions.append(Suggestion(
                id=f"doc_context_{user_id}_{int(datetime.utcnow().timestamp())}",
                type="document",
                title="Add Document Context",
                description="Include relevant documents for more accurate AI responses.",
                confidence=0.9,
                action_data={'action': 'select_documents', 'context': 'chat'},
                context={'page': 'chat', 'trigger': 'no_context'},
                created_at=datetime.utcnow(),
                user_id=user_id
            ))

        # Suggest learning path
        if profile.skill_level == 'beginner':
            suggestions.append(Suggestion(
                id=f"learning_{user_id}_{int(datetime.utcnow().timestamp())}",
                type="learning",
                title="Explore Learning Features",
                description="Discover AI-powered learning tools and study planning.",
                confidence=0.8,
                action_data={'action': 'show_learning_features'},
                context={'page': 'chat', 'trigger': 'beginner_user'},
                created_at=datetime.utcnow(),
                user_id=user_id
            ))

        return suggestions

    def _generate_dashboard_suggestions(
        self,
        user_id: str,
        profile: UserBehaviorProfile,
        context: Dict[str, Any]
    ) -> List[Suggestion]:
        """Generate dashboard-specific suggestions."""
        suggestions = []

        # Suggest productivity features
        if profile.skill_level in ['intermediate', 'advanced']:
            suggestions.append(Suggestion(
                id=f"productivity_{user_id}_{int(datetime.utcnow().timestamp())}",
                type="action",
                title="Optimize Your Workflow",
                description="Use advanced features to optimize your document workflow.",
                confidence=0.7,
                action_data={'action': 'show_workflow_optimization'},
                context={'page': 'dashboard', 'trigger': 'advanced_user'},
                created_at=datetime.utcnow(),
                user_id=user_id
            ))

        return suggestions

    def _generate_general_suggestions(
        self,
        user_id: str,
        profile: UserBehaviorProfile,
        context: Dict[str, Any]
    ) -> List[Suggestion]:
        """Generate general suggestions."""
        suggestions = []

        # Suggest backup
        last_backup = context.get('last_backup')
        if not last_backup or (datetime.utcnow() - last_backup).days > 7:
            suggestions.append(Suggestion(
                id=f"backup_{user_id}_{int(datetime.utcnow().timestamp())}",
                type="action",
                title="Backup Your Data",
                description="It's been a while since your last backup. Consider backing up your documents.",
                confidence=0.6,
                action_data={'action': 'create_backup'},
                context={'trigger': 'backup_reminder'},
                created_at=datetime.utcnow(),
                user_id=user_id
            ))

        # Suggest feature discovery
        if profile.skill_level == 'beginner':
            suggestions.append(Suggestion(
                id=f"features_{user_id}_{int(datetime.utcnow().timestamp())}",
                type="learning",
                title="Discover New Features",
                description="Explore advanced features to enhance your productivity.",
                confidence=0.8,
                action_data={'action': 'show_feature_tour'},
                context={'trigger': 'feature_discovery'},
                created_at=datetime.utcnow(),
                user_id=user_id
            ))

        return suggestions

    def _filter_suggestions(
        self,
        suggestions: List[Suggestion],
        profile: UserBehaviorProfile
    ) -> List[Suggestion]:
        """Filter suggestions based on user profile."""
        filtered = []

        for suggestion in suggestions:
            # Skip expired suggestions
            if suggestion.is_expired():
                continue

            # Filter based on skill level
            if suggestion.type == 'learning' and profile.skill_level == 'advanced':
                # Advanced users might not need basic learning suggestions
                if 'beginner' in suggestion.context.get('trigger', ''):
                    continue

            # Filter based on user preferences
            if suggestion.type == 'document':
                preferred_types = profile.preferred_content_types
                if preferred_types and suggestion.context.get('file_type') not in preferred_types:
                    continue

            filtered.append(suggestion)

        return filtered

    def _rank_suggestions(
        self,
        suggestions: List[Suggestion],
        profile: UserBehaviorProfile
    ) -> List[Suggestion]:
        """Rank suggestions by relevance."""
        # Simple ranking based on confidence and user profile
        ranked = []

        for suggestion in suggestions:
            # Boost score based on user preferences
            score = suggestion.confidence

            # Boost for preferred action types
            if suggestion.type in profile.action_frequencies:
                score += 0.1

            # Boost for learning suggestions for beginners
            if suggestion.type == 'learning' and profile.skill_level == 'beginner':
                score += 0.2

            suggestion.confidence = min(score, 1.0)
            ranked.append(suggestion)

        # Sort by confidence
        return sorted(ranked, key=lambda x: x.confidence, reverse=True)


class ProactiveAssistanceEngine:
    """Engine for proactive assistance based on user patterns."""

    def __init__(self, suggestion_engine: ContextAwareSuggestionEngine):
        """Initialize proactive assistance engine.

        Args:
            suggestion_engine: Base suggestion engine
        """
        self.suggestion_engine = suggestion_engine
        self.logger = logging.getLogger(__name__)

        # Proactive triggers
        self.triggers = {
            'new_user': self._handle_new_user,
            'inactive_user': self._handle_inactive_user,
            'power_user': self._handle_power_user,
            'study_session': self._handle_study_session,
            'document_milestone': self._handle_document_milestone
        }

    @handle_errors(operation="trigger_proactive_assistance", component="proactive_engine")
    def trigger_proactive_assistance(
        self,
        user_id: str,
        trigger_type: str,
        context: Dict[str, Any]
    ) -> List[Suggestion]:
        """Trigger proactive assistance based on user actions.

        Args:
            user_id: User ID
            trigger_type: Type of trigger
            context: Trigger context

        Returns:
            List of proactive suggestions
        """
        if trigger_type not in self.triggers:
            return []

        try:
            return self.triggers[trigger_type](user_id, context)
        except Exception as e:
            self.logger.error(f"Error in proactive assistance for {trigger_type}: {e}")
            return []

    def _handle_new_user(self, user_id: str, context: Dict[str, Any]) -> List[Suggestion]:
        """Handle new user assistance."""
        suggestions = []

        suggestions.append(Suggestion(
            id=f"welcome_{user_id}_{int(datetime.utcnow().timestamp())}",
            type="learning",
            title="Welcome to Archivista AI!",
            description="Let's get you started with your first document upload.",
            confidence=0.9,
            action_data={'action': 'show_upload_tutorial'},
            context={'trigger': 'new_user'},
            created_at=datetime.utcnow(),
            user_id=user_id
        ))

        suggestions.append(Suggestion(
            id=f"onboarding_{user_id}_{int(datetime.utcnow().timestamp())}",
            type="action",
            title="Complete Setup",
            description="Set up your preferences and explore key features.",
            confidence=0.8,
            action_data={'action': 'show_onboarding'},
            context={'trigger': 'new_user'},
            created_at=datetime.utcnow(),
            user_id=user_id
        ))

        return suggestions

    def _handle_inactive_user(self, user_id: str, context: Dict[str, Any]) -> List[Suggestion]:
        """Handle inactive user re-engagement."""
        suggestions = []

        suggestions.append(Suggestion(
            id=f"reengage_{user_id}_{int(datetime.utcnow().timestamp())}",
            type="action",
            title="Welcome Back!",
            description="Discover new features and continue your learning journey.",
            confidence=0.7,
            action_data={'action': 'show_whats_new'},
            context={'trigger': 'inactive_user'},
            created_at=datetime.utcnow(),
            user_id=user_id
        ))

        return suggestions

    def _handle_power_user(self, user_id: str, context: Dict[str, Any]) -> List[Suggestion]:
        """Handle power user optimization suggestions."""
        suggestions = []

        suggestions.append(Suggestion(
            id=f"optimize_{user_id}_{int(datetime.utcnow().timestamp())}",
            type="action",
            title="Optimize Your Workflow",
            description="Discover advanced features to enhance your productivity.",
            confidence=0.8,
            action_data={'action': 'show_advanced_features'},
            context={'trigger': 'power_user'},
            created_at=datetime.utcnow(),
            user_id=user_id
        ))

        return suggestions

    def _handle_study_session(self, user_id: str, context: Dict[str, Any]) -> List[Suggestion]:
        """Handle study session assistance."""
        suggestions = []

        suggestions.append(Suggestion(
            id=f"study_{user_id}_{int(datetime.utcnow().timestamp())}",
            type="learning",
            title="Enhance Your Study Session",
            description="Use AI-powered tools to optimize your learning.",
            confidence=0.8,
            action_data={'action': 'show_study_tools'},
            context={'trigger': 'study_session'},
            created_at=datetime.utcnow(),
            user_id=user_id
        ))

        return suggestions

    def _handle_document_milestone(self, user_id: str, context: Dict[str, Any]) -> List[Suggestion]:
        """Handle document milestone celebrations."""
        milestone = context.get('milestone', 0)

        suggestions = []

        if milestone in [10, 50, 100, 500]:
            suggestions.append(Suggestion(
                id=f"milestone_{user_id}_{int(datetime.utcnow().timestamp())}",
                type="action",
                title=f"🎉 {milestone} Documents Milestone!",
                description=f"Congratulations on reaching {milestone} documents! Consider organizing your archive.",
                confidence=0.9,
                action_data={'action': 'show_organization_tips'},
                context={'trigger': 'document_milestone', 'milestone': milestone},
                created_at=datetime.utcnow(),
                user_id=user_id
            ))

        return suggestions


class SuggestionPerformanceTracker:
    """Tracks performance of suggestions and user engagement."""

    def __init__(self):
        """Initialize performance tracker."""
        self.logger = logging.getLogger(__name__)

        # Suggestion performance data
        self.suggestion_stats: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.user_engagement: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    @handle_errors(operation="track_suggestion_shown", component="performance_tracker")
    def track_suggestion_shown(self, suggestion: Suggestion) -> None:
        """Track when suggestion is shown to user."""
        suggestion_id = suggestion.id

        if suggestion_id not in self.suggestion_stats:
            self.suggestion_stats[suggestion_id] = {
                'shown_count': 0,
                'clicked_count': 0,
                'dismissed_count': 0,
                'helpful_count': 0,
                'not_helpful_count': 0,
                'first_shown': datetime.utcnow(),
                'last_shown': datetime.utcnow()
            }

        self.suggestion_stats[suggestion_id]['shown_count'] += 1
        self.suggestion_stats[suggestion_id]['last_shown'] = datetime.utcnow()

    @handle_errors(operation="track_suggestion_interaction", component="performance_tracker")
    def track_suggestion_interaction(
        self,
        suggestion_id: str,
        interaction_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Track user interaction with suggestion.

        Args:
            suggestion_id: Suggestion ID
            interaction_type: Type of interaction (click, dismiss, helpful, not_helpful)
            metadata: Additional interaction metadata
        """
        if suggestion_id not in self.suggestion_stats:
            return

        self.suggestion_stats[suggestion_id][f'{interaction_type}_count'] += 1

        # Track user engagement
        user_id = metadata.get('user_id') if metadata else 'anonymous'
        self.user_engagement[user_id].append({
            'suggestion_id': suggestion_id,
            'interaction_type': interaction_type,
            'timestamp': datetime.utcnow(),
            'metadata': metadata or {}
        })

        # Keep only recent engagement data
        if len(self.user_engagement[user_id]) > 100:
            self.user_engagement[user_id] = self.user_engagement[user_id][-100:]

    def get_suggestion_performance(self, suggestion_id: str) -> Dict[str, Any]:
        """Get performance metrics for suggestion.

        Args:
            suggestion_id: Suggestion ID

        Returns:
            Performance metrics
        """
        if suggestion_id not in self.suggestion_stats:
            return {}

        stats = self.suggestion_stats[suggestion_id]

        # Calculate engagement rates
        shown = stats.get('shown_count', 0)
        clicked = stats.get('clicked_count', 0)
        helpful = stats.get('helpful_count', 0)
        not_helpful = stats.get('not_helpful_count', 0)

        return {
            'suggestion_id': suggestion_id,
            'shown_count': shown,
            'click_rate': clicked / shown if shown > 0 else 0,
            'helpful_rate': helpful / (helpful + not_helpful) if (helpful + not_helpful) > 0 else 0,
            'engagement_score': (clicked * 0.6 + helpful * 0.4) / shown if shown > 0 else 0,
            'first_shown': stats.get('first_shown'),
            'last_shown': stats.get('last_shown')
        }

    def get_top_performing_suggestions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top performing suggestions.

        Args:
            limit: Maximum number of suggestions to return

        Returns:
            List of top performing suggestions
        """
        performances = []

        for suggestion_id, stats in self.suggestion_stats.items():
            performance = self.get_suggestion_performance(suggestion_id)
            if performance:
                performances.append(performance)

        # Sort by engagement score
        return sorted(
            performances,
            key=lambda x: x['engagement_score'],
            reverse=True
        )[:limit]

    def get_user_engagement_summary(self, user_id: str) -> Dict[str, Any]:
        """Get user engagement summary.

        Args:
            user_id: User ID

        Returns:
            Engagement summary
        """
        if user_id not in self.user_engagement:
            return {}

        engagements = self.user_engagement[user_id]

        # Analyze engagement patterns
        interaction_types = Counter(e['interaction_type'] for e in engagements)

        # Recent activity
        recent_engagements = [
            e for e in engagements
            if (datetime.utcnow() - e['timestamp']).days <= 7
        ]

        return {
            'user_id': user_id,
            'total_engagements': len(engagements),
            'interaction_breakdown': dict(interaction_types),
            'recent_engagements': len(recent_engagements),
            'engagement_rate': len(recent_engagements) / 7,  # per day
            'most_recent': max(e['timestamp'] for e in engagements).isoformat() if engagements else None
        }


class SmartSuggestionSystem:
    """Main smart suggestion system."""

    def __init__(self, document_repository, user_activity_repository):
        """Initialize smart suggestion system.

        Args:
            document_repository: Document repository
            user_activity_repository: User activity repository
        """
        self.document_repository = document_repository
        self.user_activity_repository = user_activity_repository
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.suggestion_engine = ContextAwareSuggestionEngine(
            document_repository, user_activity_repository
        )
        self.proactive_engine = ProactiveAssistanceEngine(self.suggestion_engine)
        self.performance_tracker = SuggestionPerformanceTracker()

        # Active suggestions cache
        self.active_suggestions: Dict[str, List[Suggestion]] = {}

    @handle_errors(operation="get_personalized_suggestions", component="smart_suggestions")
    def get_personalized_suggestions(
        self,
        user_id: str,
        context: Dict[str, Any],
        limit: int = 5
    ) -> List[Suggestion]:
        """Get personalized suggestions for user.

        Args:
            user_id: User ID
            context: Current context
            limit: Maximum suggestions to return

        Returns:
            List of personalized suggestions
        """
        # Check cache first
        cache_key = f"{user_id}_{context.get('current_page', 'unknown')}"
        cached_suggestions = self._get_cached_suggestions(cache_key)

        if cached_suggestions:
            return cached_suggestions[:limit]

        # Generate new suggestions
        suggestions = self.suggestion_engine.generate_suggestions(user_id, context, limit * 2)

        # Track suggestions shown
        for suggestion in suggestions:
            self.performance_tracker.track_suggestion_shown(suggestion)

        # Cache suggestions
        self.active_suggestions[cache_key] = suggestions

        return suggestions[:limit]

    def _get_cached_suggestions(self, cache_key: str) -> Optional[List[Suggestion]]:
        """Get cached suggestions if still valid."""
        if cache_key in self.active_suggestions:
            suggestions = self.active_suggestions[cache_key]

            # Check if any suggestion is expired
            valid_suggestions = [s for s in suggestions if not s.is_expired()]

            if len(valid_suggestions) == len(suggestions):
                return suggestions
            else:
                # Remove expired suggestions
                self.active_suggestions[cache_key] = valid_suggestions

        return None

    def track_suggestion_interaction(
        self,
        suggestion_id: str,
        interaction_type: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Track user interaction with suggestion.

        Args:
            suggestion_id: Suggestion ID
            interaction_type: Type of interaction
            user_id: User ID
            metadata: Additional metadata
        """
        self.performance_tracker.track_suggestion_interaction(
            suggestion_id,
            interaction_type,
            {'user_id': user_id, **(metadata or {})}
        )

    def trigger_proactive_assistance(
        self,
        user_id: str,
        trigger_type: str,
        context: Dict[str, Any]
    ) -> List[Suggestion]:
        """Trigger proactive assistance.

        Args:
            user_id: User ID
            trigger_type: Type of trigger
            context: Trigger context

        Returns:
            List of proactive suggestions
        """
        return self.proactive_engine.trigger_proactive_assistance(
            user_id, trigger_type, context
        )

    def get_suggestion_analytics(self) -> Dict[str, Any]:
        """Get suggestion system analytics.

        Returns:
            Analytics data
        """
        return {
            'performance_summary': {
                'top_performing': self.performance_tracker.get_top_performing_suggestions(5),
                'total_suggestions': len(self.suggestion_stats),
                'avg_engagement_rate': 0.0  # Would calculate from data
            },
            'user_engagement': {
                'total_users': len(self.user_engagement),
                'avg_engagements_per_user': 0.0  # Would calculate from data
            },
            'system_health': {
                'cache_size': len(self.active_suggestions),
                'last_cleanup': datetime.utcnow().isoformat()
            }
        }

    def cleanup_expired_suggestions(self) -> int:
        """Clean up expired suggestions.

        Returns:
            Number of suggestions removed
        """
        removed_count = 0

        for cache_key in list(self.active_suggestions.keys()):
            original_count = len(self.active_suggestions[cache_key])
            self.active_suggestions[cache_key] = [
                s for s in self.active_suggestions[cache_key]
                if not s.is_expired()
            ]
            new_count = len(self.active_suggestions[cache_key])
            removed_count += original_count - new_count

            # Remove empty caches
            if new_count == 0:
                del self.active_suggestions[cache_key]

        self.logger.info(f"Cleaned up {removed_count} expired suggestions")
        return removed_count


# Factory function

def create_smart_suggestion_system(document_repository, user_activity_repository) -> SmartSuggestionSystem:
    """Create complete smart suggestion system.

    Args:
        document_repository: Document repository
        user_activity_repository: User activity repository

    Returns:
        Configured smart suggestion system
    """
    return SmartSuggestionSystem(document_repository, user_activity_repository)


# Integration with existing system

def analyze_and_show_insights(user_id: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Analyze user behavior and show insights (backward compatibility).

    Args:
        user_id: User ID
        context: Current context

    Returns:
        List of insights for display
    """
    # This would integrate with the new system
    # For now, return mock insights
    return [
        {
            'type': 'info',
            'title': 'Document Organization',
            'message': 'Consider organizing your documents by category for better access.',
            'action': 'organize_documents'
        },
        {
            'type': 'tip',
            'title': 'Search Optimization',
            'message': 'Use advanced search filters for more precise results.',
            'action': 'show_advanced_search'
        }
    ]
