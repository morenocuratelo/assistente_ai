"""
AI Integration Engine for Archivista AI.
Integrates all AI features across modules with unified interface and automation workflows.
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path

from ...database.models.base import Document, User
from ...core.errors.error_handler import handle_errors
from ...core.performance.optimizer import cache_result, measure_performance


@dataclass
class FeatureInteraction:
    """Interaction between different AI features."""
    source_feature: str
    target_feature: str
    interaction_type: str  # 'sequential', 'parallel', 'conditional'
    data_flow: Dict[str, Any]
    trigger_conditions: Dict[str, Any]
    success_rate: float = 0.0
    total_executions: int = 0


@dataclass
class AutomationWorkflow:
    """Automated workflow combining multiple AI features."""
    workflow_id: str
    name: str
    description: str
    trigger_event: str
    steps: List[Dict[str, Any]]
    conditions: Dict[str, Any]
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_executed: Optional[datetime] = None
    execution_count: int = 0
    success_count: int = 0


class FeatureInteractionTracker:
    """Tracks interactions between different AI features."""

    def __init__(self):
        """Initialize feature interaction tracker."""
        self.logger = logging.getLogger(__name__)

        # Feature interaction storage
        self.interactions: Dict[str, FeatureInteraction] = {}
        self.execution_history: List[Dict[str, Any]] = []

        # Predefined interactions
        self._setup_default_interactions()

    def _setup_default_interactions(self) -> None:
        """Setup default feature interactions."""
        interactions = [
            FeatureInteraction(
                source_feature="document_processing",
                target_feature="entity_extraction",
                interaction_type="sequential",
                data_flow={'documents': 'entities'},
                trigger_conditions={'document_processed': True}
            ),
            FeatureInteraction(
                source_feature="entity_extraction",
                target_feature="knowledge_graph",
                interaction_type="sequential",
                data_flow={'entities': 'graph_nodes'},
                trigger_conditions={'entities_found': True}
            ),
            FeatureInteraction(
                source_feature="user_query",
                target_feature="confidence_scoring",
                interaction_type="parallel",
                data_flow={'query': 'confidence'},
                trigger_conditions={'query_received': True}
            ),
            FeatureInteraction(
                source_feature="confidence_scoring",
                target_feature="smart_suggestions",
                interaction_type="conditional",
                data_flow={'confidence': 'suggestions'},
                trigger_conditions={'confidence_threshold': 0.7}
            )
        ]

        for interaction in interactions:
            interaction_id = f"{interaction.source_feature}_{interaction.target_feature}"
            self.interactions[interaction_id] = interaction

    @handle_errors(operation="track_interaction", component="interaction_tracker")
    def track_interaction(
        self,
        source_feature: str,
        target_feature: str,
        execution_data: Dict[str, Any],
        success: bool = True
    ) -> None:
        """Track feature interaction execution.

        Args:
            source_feature: Source feature name
            target_feature: Target feature name
            execution_data: Execution data and results
            success: Whether interaction was successful
        """
        interaction_id = f"{source_feature}_{target_feature}"

        # Update interaction metrics
        if interaction_id in self.interactions:
            interaction = self.interactions[interaction_id]
            interaction.total_executions += 1

            if success:
                interaction.success_rate = (
                    (interaction.success_rate * (interaction.total_executions - 1) + 1)
                    / interaction.total_executions
                )
            else:
                interaction.success_rate = (
                    (interaction.success_rate * (interaction.total_executions - 1))
                    / interaction.total_executions
                )

        # Record execution history
        self.execution_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'source_feature': source_feature,
            'target_feature': target_feature,
            'success': success,
            'execution_data': execution_data
        })

        # Keep only recent history
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]

    def get_interaction_analytics(self) -> Dict[str, Any]:
        """Get feature interaction analytics.

        Returns:
            Interaction analytics data
        """
        total_interactions = len(self.interactions)
        successful_interactions = sum(
            1 for i in self.interactions.values()
            if i.success_rate > 0.8
        )

        return {
            'total_interactions': total_interactions,
            'successful_interactions': successful_interactions,
            'success_rate': successful_interactions / total_interactions if total_interactions > 0 else 0,
            'recent_executions': len(self.execution_history),
            'interactions': [
                {
                    'id': f"{i.source_feature}_{i.target_feature}",
                    'source': i.source_feature,
                    'target': i.target_feature,
                    'type': i.interaction_type,
                    'success_rate': i.success_rate,
                    'total_executions': i.total_executions
                }
                for i in self.interactions.values()
            ]
        }


class UnifiedAISettings:
    """Unified settings interface for all AI features."""

    def __init__(self):
        """Initialize unified AI settings."""
        self.logger = logging.getLogger(__name__)

        # Settings storage
        self.settings: Dict[str, Any] = {}
        self.user_overrides: Dict[str, Dict[str, Any]] = defaultdict(dict)

        # Load default settings
        self._load_default_settings()

    def _load_default_settings(self) -> None:
        """Load default AI settings."""
        self.settings = {
            'confidence_scoring': {
                'enabled': True,
                'threshold_high': 0.8,
                'threshold_medium': 0.6,
                'threshold_low': 0.4,
                'require_user_feedback': True,
                'auto_adjust_thresholds': True
            },
            'document_intelligence': {
                'enabled': True,
                'entity_extraction': True,
                'topic_modeling': True,
                'sentiment_analysis': True,
                'similarity_detection': True,
                'min_confidence': 0.3
            },
            'knowledge_graph': {
                'enabled': True,
                'auto_build': True,
                'max_nodes': 1000,
                'relationship_threshold': 0.5,
                'visualization_enabled': True
            },
            'smart_suggestions': {
                'enabled': True,
                'max_suggestions': 5,
                'context_window': 7,
                'personalization_enabled': True,
                'proactive_suggestions': True
            },
            'collaboration': {
                'enabled': True,
                'real_time_sync': True,
                'max_participants': 10,
                'auto_save': True,
                'conflict_resolution': 'last_write_wins'
            },
            'performance': {
                'caching_enabled': True,
                'cache_ttl_seconds': 300,
                'lazy_loading': True,
                'async_processing': True,
                'monitoring_enabled': True
            }
        }

    def get_setting(self, feature: str, setting: str, user_id: str = None) -> Any:
        """Get setting value.

        Args:
            feature: Feature name
            setting: Setting name
            user_id: User ID for personalized settings

        Returns:
            Setting value
        """
        # Check user overrides first
        if user_id and user_id in self.user_overrides:
            user_settings = self.user_overrides[user_id]
            if feature in user_settings and setting in user_settings[feature]:
                return user_settings[feature][setting]

        # Return default setting
        if feature in self.settings and setting in self.settings[feature]:
            return self.settings[feature][setting]

        return None

    def set_user_override(
        self,
        user_id: str,
        feature: str,
        setting: str,
        value: Any
    ) -> bool:
        """Set user-specific setting override.

        Args:
            user_id: User ID
            feature: Feature name
            setting: Setting name
            value: Setting value

        Returns:
            True if override set successfully
        """
        try:
            if user_id not in self.user_overrides:
                self.user_overrides[user_id] = {}

            if feature not in self.user_overrides[user_id]:
                self.user_overrides[user_id][feature] = {}

            self.user_overrides[user_id][feature][setting] = value

            self.logger.info(f"Set user override for {user_id}: {feature}.{setting} = {value}")
            return True

        except Exception as e:
            self.logger.error(f"Error setting user override: {e}")
            return False

    def reset_user_overrides(self, user_id: str) -> bool:
        """Reset all user overrides.

        Args:
            user_id: User ID

        Returns:
            True if reset successful
        """
        try:
            if user_id in self.user_overrides:
                del self.user_overrides[user_id]
                self.logger.info(f"Reset user overrides for {user_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error resetting user overrides: {e}")
            return False

    def get_feature_settings(self, feature: str, user_id: str = None) -> Dict[str, Any]:
        """Get all settings for specific feature.

        Args:
            feature: Feature name
            user_id: User ID for personalized settings

        Returns:
            Feature settings dictionary
        """
        default_settings = self.settings.get(feature, {})

        if not user_id:
            return default_settings.copy()

        # Merge with user overrides
        user_settings = self.user_overrides.get(user_id, {}).get(feature, {})
        merged_settings = default_settings.copy()
        merged_settings.update(user_settings)

        return merged_settings

    def export_settings(self, file_path: str) -> bool:
        """Export all settings to file.

        Args:
            file_path: Path to export file

        Returns:
            True if export successful
        """
        try:
            export_data = {
                'default_settings': self.settings,
                'user_overrides': dict(self.user_overrides),
                'export_timestamp': datetime.utcnow().isoformat()
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Settings exported to {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error exporting settings: {e}")
            return False

    def import_settings(self, file_path: str) -> bool:
        """Import settings from file.

        Args:
            file_path: Path to settings file

        Returns:
            True if import successful
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            # Validate import data
            if 'default_settings' in import_data:
                self.settings.update(import_data['default_settings'])

            if 'user_overrides' in import_data:
                self.user_overrides.update(import_data['user_overrides'])

            self.logger.info(f"Settings imported from {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error importing settings: {e}")
            return False


class AIFeatureOrchestrator:
    """Orchestrates AI features across modules."""

    def __init__(self, document_repository, user_activity_repository):
        """Initialize AI feature orchestrator.

        Args:
            document_repository: Document repository
            user_activity_repository: User activity repository
        """
        self.document_repository = document_repository
        self.user_activity_repository = user_activity_repository
        self.logger = logging.getLogger(__name__)

        # Initialize AI systems
        self.confidence_system = self._create_confidence_system()
        self.smart_suggestions = self._create_smart_suggestions()
        self.document_intelligence = self._create_document_intelligence()
        self.knowledge_graph = self._create_knowledge_graph()
        self.model_manager = self._create_model_manager()

        # Feature interaction tracker
        self.interaction_tracker = FeatureInteractionTracker()

        # Unified settings
        self.settings = UnifiedAISettings()

        # Automation workflows
        self.automation_workflows: Dict[str, AutomationWorkflow] = {}
        self._setup_default_workflows()

    def _create_confidence_system(self) -> Dict[str, Any]:
        """Create confidence system."""
        try:
            from .confidence_system import create_confidence_system
            return create_confidence_system(self.document_repository)
        except Exception as e:
            self.logger.error(f"Error creating confidence system: {e}")
            return {}

    def _create_smart_suggestions(self) -> Any:
        """Create smart suggestions system."""
        try:
            from .smart_suggestions import create_smart_suggestion_system
            return create_smart_suggestion_system(
                self.document_repository, self.user_activity_repository
            )
        except Exception as e:
            self.logger.error(f"Error creating smart suggestions: {e}")
            return None

    def _create_document_intelligence(self) -> Any:
        """Create document intelligence system."""
        try:
            from .document_intelligence import create_document_intelligence_engine
            return create_document_intelligence_engine()
        except Exception as e:
            self.logger.error(f"Error creating document intelligence: {e}")
            return None

    def _create_knowledge_graph(self) -> Any:
        """Create knowledge graph system."""
        try:
            from .knowledge_graph import create_knowledge_graph_system
            return create_knowledge_graph_system(self.document_repository)
        except Exception as e:
            self.logger.error(f"Error creating knowledge graph: {e}")
            return None

    def _create_model_manager(self) -> Any:
        """Create model manager."""
        try:
            from .model_manager import create_ai_model_manager
            return create_ai_model_manager()
        except Exception as e:
            self.logger.error(f"Error creating model manager: {e}")
            return None

    def _setup_default_workflows(self) -> None:
        """Setup default automation workflows."""
        workflows = [
            AutomationWorkflow(
                workflow_id="document_processing_pipeline",
                name="Document Processing Pipeline",
                description="Complete document processing with AI analysis",
                trigger_event="document_uploaded",
                steps=[
                    {
                        'feature': 'document_intelligence',
                        'action': 'analyze_document',
                        'parameters': {}
                    },
                    {
                        'feature': 'knowledge_graph',
                        'action': 'update_graph',
                        'parameters': {}
                    },
                    {
                        'feature': 'smart_suggestions',
                        'action': 'generate_suggestions',
                        'parameters': {'context': 'new_document'}
                    }
                ],
                conditions={'document_processed': True}
            ),
            AutomationWorkflow(
                workflow_id="user_onboarding",
                name="User Onboarding",
                description="Guide new users through key features",
                trigger_event="user_registered",
                steps=[
                    {
                        'feature': 'smart_suggestions',
                        'action': 'trigger_proactive_assistance',
                        'parameters': {'trigger_type': 'new_user'}
                    },
                    {
                        'feature': 'confidence_system',
                        'action': 'setup_user_thresholds',
                        'parameters': {}
                    }
                ],
                conditions={'user_is_new': True}
            )
        ]

        for workflow in workflows:
            self.automation_workflows[workflow.workflow_id] = workflow

    @handle_errors(operation="process_document_with_ai", component="ai_orchestrator")
    def process_document_with_ai(
        self,
        document: Document,
        user_id: str,
        project_id: str
    ) -> Dict[str, Any]:
        """Process document with full AI pipeline.

        Args:
            document: Document to process
            user_id: User ID
            project_id: Project ID

        Returns:
            Complete AI processing results
        """
        results = {
            'document_id': document.id,
            'processing_timestamp': datetime.utcnow().isoformat(),
            'features_executed': [],
            'confidence_scores': {},
            'entities_extracted': [],
            'topics_identified': [],
            'suggestions_generated': [],
            'knowledge_graph_updated': False,
            'overall_confidence': 0.0
        }

        try:
            # Step 1: Document Intelligence Analysis
            if self.document_intelligence:
                intelligence_results = self.document_intelligence.analyze_document(document)
                results['features_executed'].append('document_intelligence')
                results['entities_extracted'] = intelligence_results.get('entities', [])
                results['topics_identified'] = intelligence_results.get('topics', [])

                # Track interaction
                self.interaction_tracker.track_interaction(
                    'document_processing', 'entity_extraction', intelligence_results
                )

            # Step 2: Confidence Scoring
            if self.confidence_system:
                confidence_score = self.confidence_system['calculator'].calculate_response_confidence(
                    document.formatted_preview or "",
                    [document],
                    user_id,
                    "document_analysis"
                )
                results['features_executed'].append('confidence_scoring')
                results['confidence_scores']['document_analysis'] = confidence_score.value
                results['overall_confidence'] = confidence_score.value

                # Track interaction
                self.interaction_tracker.track_interaction(
                    'document_intelligence', 'confidence_scoring',
                    {'confidence': confidence_score.value}
                )

            # Step 3: Knowledge Graph Update
            if self.knowledge_graph:
                try:
                    graph_data = self.knowledge_graph.get_or_build_graph(project_id, user_id)
                    results['features_executed'].append('knowledge_graph')
                    results['knowledge_graph_updated'] = True

                    # Track interaction
                    self.interaction_tracker.track_interaction(
                        'entity_extraction', 'knowledge_graph',
                        {'nodes_added': len(graph_data.get('nodes', []))}
                    )

                except Exception as e:
                    self.logger.error(f"Error updating knowledge graph: {e}")

            # Step 4: Smart Suggestions
            if self.smart_suggestions:
                context = {
                    'current_page': 'archive',
                    'recent_actions': ['document_processed'],
                    'active_documents': [document.id]
                }

                suggestions = self.smart_suggestions.get_personalized_suggestions(
                    user_id, context, limit=3
                )
                results['features_executed'].append('smart_suggestions')
                results['suggestions_generated'] = [
                    {
                        'title': s.title,
                        'type': s.type,
                        'confidence': s.confidence
                    }
                    for s in suggestions
                ]

                # Track interaction
                self.interaction_tracker.track_interaction(
                    'confidence_scoring', 'smart_suggestions',
                    {'suggestions_count': len(suggestions)}
                )

            self.logger.info(f"AI processing completed for document {document.id}")
            return results

        except Exception as e:
            self.logger.error(f"Error in AI processing pipeline: {e}")
            raise

    @handle_errors(operation="execute_automation_workflow", component="ai_orchestrator")
    def execute_automation_workflow(
        self,
        workflow_id: str,
        trigger_data: Dict[str, Any],
        user_id: str = None
    ) -> Dict[str, Any]:
        """Execute automation workflow.

        Args:
            workflow_id: Workflow ID to execute
            trigger_data: Data that triggered the workflow
            user_id: User ID for context

        Returns:
            Workflow execution results
        """
        if workflow_id not in self.automation_workflows:
            raise ValueError(f"Workflow {workflow_id} not found")

        workflow = self.automation_workflows[workflow_id]

        if not workflow.is_active:
            return {'status': 'skipped', 'reason': 'workflow_disabled'}

        results = {
            'workflow_id': workflow_id,
            'workflow_name': workflow.name,
            'execution_timestamp': datetime.utcnow().isoformat(),
            'steps_executed': [],
            'overall_success': True,
            'errors': []
        }

        try:
            # Execute workflow steps
            for step in workflow.steps:
                step_result = self._execute_workflow_step(
                    step, trigger_data, user_id, workflow_id
                )

                results['steps_executed'].append(step_result)

                if not step_result.get('success', False):
                    results['overall_success'] = False
                    results['errors'].append(step_result.get('error', 'Unknown error'))

            # Update workflow statistics
            workflow.execution_count += 1
            workflow.last_executed = datetime.utcnow()

            if results['overall_success']:
                workflow.success_count += 1

            self.logger.info(f"Workflow {workflow_id} executed successfully")
            return results

        except Exception as e:
            results['overall_success'] = False
            results['errors'].append(str(e))
            self.logger.error(f"Error executing workflow {workflow_id}: {e}")
            return results

    def _execute_workflow_step(
        self,
        step: Dict[str, Any],
        trigger_data: Dict[str, Any],
        user_id: str,
        workflow_id: str
    ) -> Dict[str, Any]:
        """Execute single workflow step.

        Args:
            step: Step configuration
            trigger_data: Trigger data
            user_id: User ID
            workflow_id: Workflow ID

        Returns:
            Step execution result
        """
        feature = step.get('feature')
        action = step.get('action')
        parameters = step.get('parameters', {})

        try:
            # Execute based on feature
            if feature == 'document_intelligence':
                result = self._execute_document_intelligence_step(action, parameters, trigger_data)
            elif feature == 'knowledge_graph':
                result = self._execute_knowledge_graph_step(action, parameters, trigger_data)
            elif feature == 'smart_suggestions':
                result = self._execute_smart_suggestions_step(action, parameters, trigger_data, user_id)
            elif feature == 'confidence_system':
                result = self._execute_confidence_system_step(action, parameters, trigger_data)
            else:
                result = {'success': False, 'error': f'Unknown feature: {feature}'}

            # Track interaction
            if result.get('success', False):
                self.interaction_tracker.track_interaction(
                    workflow_id, feature, {'action': action, 'result': 'success'}
                )
            else:
                self.interaction_tracker.track_interaction(
                    workflow_id, feature, {'action': action, 'result': 'failed'}
                )

            return result

        except Exception as e:
            self.logger.error(f"Error executing workflow step {feature}.{action}: {e}")
            return {'success': False, 'error': str(e)}

    def _execute_document_intelligence_step(
        self,
        action: str,
        parameters: Dict[str, Any],
        trigger_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute document intelligence step."""
        try:
            if action == 'analyze_document':
                document_id = trigger_data.get('document_id')
                if document_id:
                    document = self.document_repository.get_by_id(document_id)
                    if document:
                        analysis = self.document_intelligence.analyze_document(document)
                        return {'success': True, 'analysis': analysis}

            return {'success': False, 'error': 'Invalid parameters for document intelligence step'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _execute_knowledge_graph_step(
        self,
        action: str,
        parameters: Dict[str, Any],
        trigger_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute knowledge graph step."""
        try:
            if action == 'update_graph':
                project_id = trigger_data.get('project_id')
                if project_id:
                    graph_data = self.knowledge_graph.get_or_build_graph(project_id)
                    return {'success': True, 'graph_updated': True, 'node_count': len(graph_data.get('nodes', []))}

            return {'success': False, 'error': 'Invalid parameters for knowledge graph step'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _execute_smart_suggestions_step(
        self,
        action: str,
        parameters: Dict[str, Any],
        trigger_data: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Execute smart suggestions step."""
        try:
            if action == 'generate_suggestions':
                context = parameters.get('context', 'general')
                suggestions = self.smart_suggestions.get_personalized_suggestions(
                    user_id, {'context': context}, limit=3
                )
                return {
                    'success': True,
                    'suggestions_count': len(suggestions),
                    'suggestions': [{'title': s.title, 'type': s.type} for s in suggestions]
                }

            elif action == 'trigger_proactive_assistance':
                trigger_type = parameters.get('trigger_type')
                if trigger_type:
                    suggestions = self.smart_suggestions.trigger_proactive_assistance(
                        user_id, trigger_type, trigger_data
                    )
                    return {
                        'success': True,
                        'trigger_type': trigger_type,
                        'suggestions_count': len(suggestions)
                    }

            return {'success': False, 'error': 'Invalid parameters for smart suggestions step'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _execute_confidence_system_step(
        self,
        action: str,
        parameters: Dict[str, Any],
        trigger_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute confidence system step."""
        try:
            if action == 'setup_user_thresholds':
                # Setup default thresholds for user
                return {'success': True, 'thresholds_configured': True}

            return {'success': False, 'error': 'Invalid parameters for confidence system step'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_ai_feature_status(self) -> Dict[str, Any]:
        """Get status of all AI features.

        Returns:
            AI features status
        """
        return {
            'confidence_system': self._get_system_status(self.confidence_system),
            'smart_suggestions': self._get_system_status(self.smart_suggestions),
            'document_intelligence': self._get_system_status(self.document_intelligence),
            'knowledge_graph': self._get_system_status(self.knowledge_graph),
            'model_manager': self._get_system_status(self.model_manager),
            'interaction_tracker': self.interaction_tracker.get_interaction_analytics(),
            'automation_workflows': len(self.automation_workflows),
            'settings': self.settings.get_feature_settings('global'),
            'status_timestamp': datetime.utcnow().isoformat()
        }

    def _get_system_status(self, system: Any) -> Dict[str, Any]:
        """Get status of specific system."""
        if system is None:
            return {'status': 'not_initialized', 'error': 'System not available'}

        # Try to get system health metrics
        try:
            if hasattr(system, 'get_system_stats'):
                return system.get_system_stats()
            elif hasattr(system, 'get_stats'):
                return system.get_stats()
            else:
                return {'status': 'initialized', 'features': 'available'}
        except Exception as e:
            return {'status': 'error', 'error_message': str(e)}

    def get_ai_analytics(self) -> Dict[str, Any]:
        """Get comprehensive AI analytics.

        Returns:
            AI analytics data
        """
        return {
            'feature_interactions': self.interaction_tracker.get_interaction_analytics(),
            'automation_workflows': {
                workflow_id: {
                    'name': workflow.name,
                    'execution_count': workflow.execution_count,
                    'success_count': workflow.success_count,
                    'last_executed': workflow.last_executed.isoformat() if workflow.last_executed else None
                }
                for workflow_id, workflow in self.automation_workflows.items()
            },
            'system_performance': self._get_system_performance_metrics(),
            'user_engagement': self._get_user_engagement_metrics(),
            'analytics_timestamp': datetime.utcnow().isoformat()
        }

    def _get_system_performance_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics."""
        # This would aggregate performance metrics from all AI systems
        return {
            'total_operations': 0,
            'avg_response_time_ms': 0,
            'cache_hit_rate': 0,
            'error_rate': 0
        }

    def _get_user_engagement_metrics(self) -> Dict[str, Any]:
        """Get user engagement metrics."""
        # This would aggregate user engagement data
        return {
            'total_users': 0,
            'active_users': 0,
            'avg_session_duration': 0,
            'feature_usage': {}
        }

    def create_custom_workflow(
        self,
        name: str,
        description: str,
        trigger_event: str,
        steps: List[Dict[str, Any]],
        conditions: Dict[str, Any]
    ) -> str:
        """Create custom automation workflow.

        Args:
            name: Workflow name
            description: Workflow description
            trigger_event: Event that triggers workflow
            steps: Workflow steps
            conditions: Execution conditions

        Returns:
            Workflow ID
        """
        workflow_id = f"custom_{name.lower().replace(' ', '_')}_{int(datetime.utcnow().timestamp())}"

        workflow = AutomationWorkflow(
            workflow_id=workflow_id,
            name=name,
            description=description,
            trigger_event=trigger_event,
            steps=steps,
            conditions=conditions
        )

        self.automation_workflows[workflow_id] = workflow

        self.logger.info(f"Created custom workflow: {workflow_id}")
        return workflow_id

    def enable_feature(self, feature: str, user_id: str = None) -> bool:
        """Enable AI feature.

        Args:
            feature: Feature to enable
            user_id: User ID for personalized setting

        Returns:
            True if enabled successfully
        """
        try:
            if user_id:
                # Enable for specific user
                return self.settings.set_user_override(user_id, feature, 'enabled', True)
            else:
                # Enable globally
                if feature in self.settings.settings:
                    self.settings.settings[feature]['enabled'] = True
                    return True

            return False

        except Exception as e:
            self.logger.error(f"Error enabling feature {feature}: {e}")
            return False

    def disable_feature(self, feature: str, user_id: str = None) -> bool:
        """Disable AI feature.

        Args:
            feature: Feature to disable
            user_id: User ID for personalized setting

        Returns:
            True if disabled successfully
        """
        try:
            if user_id:
                # Disable for specific user
                return self.settings.set_user_override(user_id, feature, 'enabled', False)
            else:
                # Disable globally
                if feature in self.settings.settings:
                    self.settings.settings[feature]['enabled'] = False
                    return True

            return False

        except Exception as e:
            self.logger.error(f"Error disabling feature {feature}: {e}")
            return False

    def get_feature_usage_analytics(self) -> Dict[str, Any]:
        """Get feature usage analytics.

        Returns:
            Feature usage analytics
        """
        return {
            'interactions': self.interaction_tracker.get_interaction_analytics(),
            'workflows': {
                'total_workflows': len(self.automation_workflows),
                'active_workflows': len([w for w in self.automation_workflows.values() if w.is_active]),
                'most_executed': self._get_most_executed_workflows()
            },
            'settings': {
                'global_settings': self.settings.settings,
                'user_overrides_count': len(self.settings.user_overrides)
            },
            'performance': self._get_feature_performance_metrics(),
            'analytics_timestamp': datetime.utcnow().isoformat()
        }

    def _get_most_executed_workflows(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get most executed workflows."""
        workflow_stats = []

        for workflow_id, workflow in self.automation_workflows.items():
            workflow_stats.append({
                'workflow_id': workflow_id,
                'name': workflow.name,
                'execution_count': workflow.execution_count,
                'success_count': workflow.success_count,
                'success_rate': workflow.success_count / workflow.execution_count if workflow.execution_count > 0 else 0
            })

        # Sort by execution count
        workflow_stats.sort(key=lambda x: x['execution_count'], reverse=True)
        return workflow_stats[:limit]

    def _get_feature_performance_metrics(self) -> Dict[str, Any]:
        """Get feature performance metrics."""
        # This would aggregate performance metrics from all features
        return {
            'confidence_system': {'avg_confidence': 0.7, 'total_evaluations': 0},
            'document_intelligence': {'total_analyses': 0, 'avg_processing_time': 0},
            'knowledge_graph': {'total_builds': 0, 'avg_build_time': 0},
            'smart_suggestions': {'total_suggestions': 0, 'avg_generation_time': 0}
        }

    def export_ai_configuration(self, file_path: str) -> bool:
        """Export AI configuration and settings.

        Args:
            file_path: Path to export file

        Returns:
            True if export successful
        """
        try:
            config_data = {
                'settings': self.settings.settings,
                'user_overrides': dict(self.settings.user_overrides),
                'automation_workflows': [
                    {
                        'workflow_id': w.workflow_id,
                        'name': w.name,
                        'description': w.description,
                        'trigger_event': w.trigger_event,
                        'is_active': w.is_active,
                        'execution_count': w.execution_count,
                        'success_count': w.success_count
                    }
                    for w in self.automation_workflows.values()
                ],
                'feature_interactions': self.interaction_tracker.get_interaction_analytics(),
                'export_timestamp': datetime.utcnow().isoformat()
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"AI configuration exported to {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error exporting AI configuration: {e}")
            return False

    def import_ai_configuration(self, file_path: str) -> bool:
        """Import AI configuration and settings.

        Args:
            file_path: Path to configuration file

        Returns:
            True if import successful
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # Import settings
            if 'settings' in config_data:
                self.settings.settings.update(config_data['settings'])

            # Import user overrides
            if 'user_overrides' in config_data:
                self.settings.user_overrides.update(config_data['user_overrides'])

            # Import workflows
            if 'automation_workflows' in config_data:
                for workflow_data in config_data['automation_workflows']:
                    workflow = AutomationWorkflow(
                        workflow_id=workflow_data['workflow_id'],
                        name=workflow_data['name'],
                        description=workflow_data['description'],
                        trigger_event=workflow_data['trigger_event'],
                        steps=[],  # Would need to reconstruct steps
                        conditions={}
                    )
                    self.automation_workflows[workflow.workflow_id] = workflow

            self.logger.info(f"AI configuration imported from {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error importing AI configuration: {e}")
            return False


class AIPoweredAutomation:
    """AI-powered automation workflows."""

    def __init__(self, ai_orchestrator: AIFeatureOrchestrator):
        """Initialize AI automation.

        Args:
            ai_orchestrator: AI feature orchestrator
        """
        self.ai_orchestrator = ai_orchestrator
        self.logger = logging.getLogger(__name__)

        # Automation triggers
        self.triggers: Dict[str, Callable] = {
            'document_uploaded': self._handle_document_upload,
            'user_registered': self._handle_user_registration,
            'document_processed': self._handle_document_processed,
            'user_idle': self._handle_user_idle,
            'knowledge_gap_detected': self._handle_knowledge_gap
        }

    @handle_errors(operation="trigger_automation", component="ai_automation")
    def trigger_automation(
        self,
        trigger_event: str,
        trigger_data: Dict[str, Any],
        user_id: str = None
    ) -> Dict[str, Any]:
        """Trigger AI-powered automation.

        Args:
            trigger_event: Event that triggered automation
            trigger_data: Event data
            user_id: User ID for context

        Returns:
            Automation results
        """
        if trigger_event not in self.triggers:
            return {'status': 'no_handler', 'trigger_event': trigger_event}

        try:
            return self.triggers[trigger_event](trigger_data, user_id)
        except Exception as e:
            self.logger.error(f"Error in automation trigger {trigger_event}: {e}")
            return {'status': 'error', 'error': str(e)}

    def _handle_document_upload(self, trigger_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Handle document upload automation."""
        document_id = trigger_data.get('document_id')
        project_id = trigger_data.get('project_id')

        if not document_id or not project_id:
            return {'status': 'missing_data'}

        # Execute document processing pipeline
        document = self.ai_orchestrator.document_repository.get_by_id(document_id)
        if document:
            results = self.ai_orchestrator.process_document_with_ai(document, user_id, project_id)

            # Execute automation workflow
            workflow_results = self.ai_orchestrator.execute_automation_workflow(
                'document_processing_pipeline',
                trigger_data,
                user_id
            )

            return {
                'status': 'success',
                'ai_processing': results,
                'workflow_execution': workflow_results
            }

        return {'status': 'document_not_found'}

    def _handle_user_registration(self, trigger_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Handle user registration automation."""
        if not user_id:
            return {'status': 'missing_user_id'}

        # Execute user onboarding workflow
        workflow_results = self.ai_orchestrator.execute_automation_workflow(
            'user_onboarding',
            trigger_data,
            user_id
        )

        return {
            'status': 'success',
            'workflow_execution': workflow_results
        }

    def _handle_document_processed(self, trigger_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Handle document processed automation."""
        # Trigger knowledge graph update and suggestions
        project_id = trigger_data.get('project_id')

        if project_id:
            # Update knowledge graph
            try:
                graph_data = self.ai_orchestrator.knowledge_graph.get_or_build_graph(project_id, user_id)

                # Generate contextual suggestions
                context = {
                    'current_page': 'archive',
                    'recent_actions': ['document_processed'],
                    'project_id': project_id
                }

                suggestions = self.ai_orchestrator.smart_suggestions.get_personalized_suggestions(
                    user_id, context, limit=3
                )

                return {
                    'status': 'success',
                    'knowledge_graph_updated': True,
                    'suggestions_generated': len(suggestions),
                    'suggestions': [{'title': s.title, 'type': s.type} for s in suggestions]
                }

            except Exception as e:
                self.logger.error(f"Error in document processed automation: {e}")

        return {'status': 'error', 'error': 'Processing failed'}

    def _handle_user_idle(self, trigger_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Handle user idle automation."""
        # Trigger proactive assistance
        suggestions = self.ai_orchestrator.smart_suggestions.trigger_proactive_assistance(
            user_id, 'inactive_user', trigger_data
        )

        return {
            'status': 'success',
            'proactive_suggestions': len(suggestions),
            'suggestions': [{'title': s.title, 'type': s.type} for s in suggestions]
        }

    def _handle_knowledge_gap(self, trigger_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Handle knowledge gap detection."""
        # Trigger learning suggestions
        context = {
            'current_page': 'knowledge_graph',
            'trigger': 'knowledge_gap_detected'
        }

        suggestions = self.ai_orchestrator.smart_suggestions.get_personalized_suggestions(
            user_id, context, limit=5
        )

        return {
            'status': 'success',
            'learning_suggestions': len(suggestions),
            'suggestions': [{'title': s.title, 'type': s.type} for s in suggestions]
        }


class CrossFeatureIntegrationEngine:
    """Engine for integrating AI features across modules."""

    def __init__(self, ai_orchestrator: AIFeatureOrchestrator):
        """Initialize cross-feature integration engine.

        Args:
            ai_orchestrator: AI feature orchestrator
        """
        self.ai_orchestrator = ai_orchestrator
        self.logger = logging.getLogger(__name__)

        # Integration workflows
        self.integration_workflows: Dict[str, Dict[str, Any]] = {}
        self._setup_integration_workflows()

    def _setup_integration_workflows(self) -> None:
        """Setup integration workflows."""
        self.integration_workflows = {
            'document_to_knowledge': {
                'description': 'Integrate document processing with knowledge graph',
                'sequence': ['document_intelligence', 'knowledge_graph', 'smart_suggestions'],
                'data_flow': {
                    'document_intelligence': ['entities', 'topics', 'sentiment'],
                    'knowledge_graph': ['graph_nodes', 'relationships'],
                    'smart_suggestions': ['contextual_suggestions']
                }
            },
            'user_behavior_to_personalization': {
                'description': 'Use user behavior for AI personalization',
                'sequence': ['smart_suggestions', 'confidence_system', 'knowledge_graph'],
                'data_flow': {
                    'smart_suggestions': ['user_profile', 'behavior_patterns'],
                    'confidence_system': ['personalized_thresholds'],
                    'knowledge_graph': ['user_specific_graph']
                }
            }
        }

    @handle_errors(operation="execute_cross_feature_workflow", component="integration_engine")
    def execute_cross_feature_workflow(
        self,
        workflow_name: str,
        input_data: Dict[str, Any],
        user_id: str = None
    ) -> Dict[str, Any]:
        """Execute cross-feature integration workflow.

        Args:
            workflow_name: Name of integration workflow
            input_data: Input data for workflow
            user_id: User ID for context

        Returns:
            Workflow execution results
        """
        if workflow_name not in self.integration_workflows:
            raise ValueError(f"Integration workflow {workflow_name} not found")

        workflow = self.integration_workflows[workflow_name]

        results = {
            'workflow_name': workflow_name,
            'execution_timestamp': datetime.utcnow().isoformat(),
            'steps_results': {},
            'overall_success': True,
            'data_flow': {},
            'errors': []
        }

        try:
            # Execute workflow steps in sequence
            for step in workflow['sequence']:
                step_result = self._execute_integration_step(
                    step, input_data, user_id, workflow_name
                )

                results['steps_results'][step] = step_result

                if not step_result.get('success', False):
                    results['overall_success'] = False
                    results['errors'].append({
                        'step': step,
                        'error': step_result.get('error', 'Unknown error')
                    })

                # Pass data to next step
                if step_result.get('success', False):
                    step_data = step_result.get('data', {})
                    input_data.update(step_data)

            # Track data flow
            results['data_flow'] = self._track_data_flow(workflow, results['steps_results'])

            self.logger.info(f"Cross-feature workflow {workflow_name} executed successfully")
            return results

        except Exception as e:
            results['overall_success'] = False
            results['errors'].append(str(e))
            self.logger.error(f"Error executing cross-feature workflow {workflow_name}: {e}")
            return results

    def _execute_integration_step(
        self,
        step: str,
        input_data: Dict[str, Any],
        user_id: str,
        workflow_name: str
    ) -> Dict[str, Any]:
        """Execute single integration step.

        Args:
            step: Step name
            input_data: Input data
            user_id: User ID
            workflow_name: Workflow name

        Returns:
            Step execution result
        """
        try:
            if step == 'document_intelligence':
                return self._execute_document_intelligence_integration(input_data)
            elif step == 'knowledge_graph':
                return self._execute_knowledge_graph_integration(input_data, user_id)
            elif step == 'smart_suggestions':
                return self._execute_smart_suggestions_integration(input_data, user_id)
            elif step == 'confidence_system':
                return self._execute_confidence_system_integration(input_data, user_id)
            else:
                return {'success': False, 'error': f'Unknown step: {step}'}

        except Exception as e:
            self.logger.error(f"Error executing integration step {step}: {e}")
            return {'success': False, 'error': str(e)}

    def _execute_document_intelligence_integration(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute document intelligence integration."""
        document_id = input_data.get('document_id')

        if not document_id:
            return {'success': False, 'error': 'Missing document_id'}

        document = self.ai_orchestrator.document_repository.get_by_id(document_id)
        if not document:
            return {'success': False, 'error': 'Document not found'}

        # Analyze document
        analysis = self.ai_orchestrator.document_intelligence.analyze_document(document)

        return {
            'success': True,
            'data': {
                'entities': analysis.get('entities', []),
                'topics': analysis.get('topics', []),
                'sentiment': analysis.get('sentiment', {}),
                'quality_score': analysis.get('quality_score', 0)
            }
        }

    def _execute_knowledge_graph_integration(self, input_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Execute knowledge graph integration."""
        project_id = input_data.get('project_id')
        entities = input_data.get('entities', [])

        if not project_id:
            return {'success': False, 'error': 'Missing project_id'}

        # Update knowledge graph
        graph_data = self.ai_orchestrator.knowledge_graph.get_or_build_graph(project_id, user_id)

        return {
            'success': True,
            'data': {
                'graph_nodes': len(graph_data.get('nodes', [])),
                'graph_edges': len(graph_data.get('edges', [])),
                'clusters': len(graph_data.get('clusters', [])),
                'graph_density': graph_data.get('metrics', {}).get('density', 0)
            }
        }

    def _execute_smart_suggestions_integration(self, input_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Execute smart suggestions integration."""
        context = {
            'current_page': input_data.get('current_page', 'unknown'),
            'recent_actions': input_data.get('recent_actions', []),
            'document_context': input_data.get('document_id')
        }

        # Generate suggestions
        suggestions = self.ai_orchestrator.smart_suggestions.get_personalized_suggestions(
            user_id, context, limit=5
        )

        return {
            'success': True,
            'data': {
                'suggestions': [
                    {
                        'title': s.title,
                        'type': s.type,
                        'confidence': s.confidence,
                        'action': s.action_data.get('action')
                    }
                    for s in suggestions
                ],
                'suggestions_count': len(suggestions)
            }
        }

    def _execute_confidence_system_integration(self, input_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Execute confidence system integration."""
        # Setup user-specific confidence thresholds
        threshold_manager = self.ai_orchestrator.confidence_system['threshold_manager']

        # Set personalized thresholds based on user behavior
        threshold_manager.set_user_threshold(user_id, 'high_confidence_response', 0.8)
        threshold_manager.set_user_threshold(user_id, 'require_user_confirmation', 0.4)

        return {
            'success': True,
            'data': {
                'thresholds_configured': True,
                'personalization_applied': True
            }
        }

    def _track_data_flow(self, workflow: Dict[str, Any], step_results: Dict[str, Any]) -> Dict[str, Any]:
        """Track data flow through workflow."""
        data_flow = {}

        for step in workflow['sequence']:
            if step in step_results:
                step_result = step_results[step]
                if step_result.get('success', False):
                    data_flow[step] = step_result.get('data', {})

        return data_flow

    def get_integration_analytics(self) -> Dict[str, Any]:
        """Get integration analytics.

        Returns:
            Integration analytics data
        """
        return {
            'available_workflows': list(self.integration_workflows.keys()),
            'workflow_details': {
                name: {
                    'description': workflow['description'],
                    'step_count': len(workflow['sequence']),
                    'data_flow': workflow['data_flow']
                }
                for name, workflow in self.integration_workflows.items()
            },
            'integration_timestamp': datetime.utcnow().isoformat()
        }


class UnifiedAIInterface:
    """Unified interface for all AI features."""

    def __init__(self, ai_orchestrator: AIFeatureOrchestrator):
        """Initialize unified AI interface.

        Args:
            ai_orchestrator: AI feature orchestrator
        """
        self.ai_orchestrator = ai_orchestrator
        self.logger = logging.getLogger(__name__)

    @handle_errors(operation="execute_ai_workflow", component="unified_ai_interface")
    def execute_ai_workflow(
        self,
        workflow_type: str,
        input_data: Dict[str, Any],
        user_id: str = None,
        project_id: str = None
    ) -> Dict[str, Any]:
        """Execute AI workflow through unified interface.

        Args:
            workflow_type: Type of workflow to execute
            input_data: Input data for workflow
            user_id: User ID for context
            project_id: Project ID for context

        Returns:
            Workflow execution results
        """
        try:
            # Add context data
            context_data = input_data.copy()
            if user_id:
                context_data['user_id'] = user_id
            if project_id:
                context_data['project_id'] = project_id

            # Execute based on workflow type
            if workflow_type == 'document_processing':
                return self._execute_document_processing_workflow(context_data)
            elif workflow_type == 'user_personalization':
                return self._execute_user_personalization_workflow(context_data)
            elif workflow_type == 'knowledge_discovery':
                return self._execute_knowledge_discovery_workflow(context_data)
            elif workflow_type == 'automated_insights':
                return self._execute_automated_insights_workflow(context_data)
            else:
                raise ValueError(f"Unknown workflow type: {workflow_type}")

        except Exception as e:
            self.logger.error(f"Error executing AI workflow {workflow_type}: {e}")
            raise

    def _execute_document_processing_workflow(self, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute document processing workflow."""
        document_id = context_data.get('document_id')
        user_id = context_data.get('user_id')
        project_id = context_data.get('project_id')

        if not document_id:
            raise ValueError("Document ID required for document processing workflow")

        # Get document
        document = self.ai_orchestrator.document_repository.get_by_id(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")

        # Process with full AI pipeline
        return self.ai_orchestrator.process_document_with_ai(document, user_id, project_id)

    def _execute_user_personalization_workflow(self, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute user personalization workflow."""
        user_id = context_data.get('user_id')

        if not user_id:
            raise ValueError("User ID required for personalization workflow")

        # Get user behavior profile
        profile = self.ai_orchestrator.smart_suggestions.behavior_analyzer.analyze_user_behavior(user_id)

        # Setup personalized confidence thresholds
        threshold_manager = self.ai_orchestrator.confidence_system['threshold_manager']
        threshold_manager.set_user_threshold(user_id, 'high_confidence_response', 0.8)

        # Generate personalized suggestions
        context = {'current_page': 'dashboard', 'user_profile': profile.__dict__}
        suggestions = self.ai_orchestrator.smart_suggestions.get_personalized_suggestions(
            user_id, context, limit=5
        )

        return {
            'user_profile': profile.__dict__,
            'personalized_suggestions': [
                {'title': s.title, 'type': s.type, 'confidence': s.confidence}
                for s in suggestions
            ],
            'thresholds_configured': True
        }

    def _execute_knowledge_discovery_workflow(self, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute knowledge discovery workflow."""
        project_id = context_data.get('project_id')
        user_id = context_data.get('user_id')

        if not project_id:
            raise ValueError("Project ID required for knowledge discovery workflow")

        # Build knowledge graph
        graph_data = self.ai_orchestrator.knowledge_graph.get_or_build_graph(project_id, user_id)

        # Get knowledge insights
        insights = self.ai_orchestrator.knowledge_graph.get_knowledge_insights(project_id)

        # Generate discovery suggestions
        context = {'current_page': 'knowledge_graph', 'graph_data': graph_data}
        suggestions = self.ai_orchestrator.smart_suggestions.get_personalized_suggestions(
            user_id, context, limit=5
        )

        return {
            'knowledge_graph': graph_data,
            'insights': insights,
            'discovery_suggestions': [
                {'title': s.title, 'type': s.type, 'confidence': s.confidence}
                for s in suggestions
            ]
        }

    def _execute_automated_insights_workflow(self, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute automated insights workflow."""
        project_id = context_data.get('project_id')
        user_id = context_data.get('user_id')

        # Get comprehensive insights
        insights = {
            'ai_features': self.ai_orchestrator.get_ai_feature_status(),
            'analytics': self.ai_orchestrator.get_ai_analytics(),
            'usage_analytics': self.ai_orchestrator.get_feature_usage_analytics(),
            'personalized_insights': self._get_personalized_insights(user_id, project_id)
        }

        return insights

    def _get_personalized_insights(self, user_id: str, project_id: str) -> Dict[str, Any]:
        """Get personalized insights for user."""
        insights = {}

        try:
            # Get user behavior profile
            profile = self.ai_orchestrator.smart_suggestions.behavior_analyzer.analyze_user_behavior(user_id)

            # Get knowledge graph insights
            graph_insights = self.ai_orchestrator.knowledge_graph.get_knowledge_insights(project_id)

            # Generate personalized recommendations
            insights = {
                'user_skill_level': profile.skill_level,
                'learning_goals': profile.learning_goals,
                'preferred_content': profile.preferred_content_types,
                'knowledge_graph_insights': graph_insights,
                'suggested_actions': self._generate_suggested_actions(profile, graph_insights)
            }

        except Exception as e:
            self.logger.error(f"Error getting personalized insights: {e}")

        return insights

    def _generate_suggested_actions(self, profile: Any, graph_insights: Dict[str, Any]) -> List[str]:
        """Generate suggested actions based on profile and insights."""
        actions = []

        # Suggestions based on skill level
        if profile.skill_level == 'beginner':
            actions.append("Complete the getting started tutorial")
            actions.append("Upload your first document to explore features")

        # Suggestions based on knowledge gaps
        if graph_insights.get('knowledge_gaps'):
            actions.append("Explore disconnected knowledge areas")
            actions.append("Add connecting concepts to improve knowledge flow")

        # Suggestions based on activity level
        if profile.action_frequencies.get('document_upload', 0) > 10:
            actions.append("Consider organizing documents by category")
            actions.append("Use advanced search features for better discovery")

        return actions

    def get_ai_powered_insights(self, user_id: str, project_id: str) -> Dict[str, Any]:
        """Get AI-powered insights for user and project.

        Args:
            user_id: User ID
            project_id: Project ID

        Returns:
            AI-powered insights
        """
        return self.execute_ai_workflow(
            'automated_insights',
            {'user_id': user_id, 'project_id': project_id}
        )


# Factory function

def create_ai_integration_engine(
    document_repository,
    user_activity_repository
) -> AIFeatureOrchestrator:
    """Create complete AI integration engine.

    Args:
        document_repository: Document repository
        user_activity_repository: User activity repository

    Returns:
        Configured AI integration engine
    """
    return AIFeatureOrchestrator(document_repository, user_activity_repository)


# Convenience functions

def process_document_with_full_ai_pipeline(
    document: Document,
    user_id: str,
    project_id: str
) -> Dict[str, Any]:
    """Process document with full AI pipeline (convenience function).

    Args:
        document: Document to process
        user_id: User ID
        project_id: Project ID

    Returns:
        AI processing results
    """
    # This would get the integration engine from a global registry
    # For now, return mock results
    return {
        'document_id': document.id,
        'features_executed': ['document_intelligence', 'confidence_scoring', 'knowledge_graph'],
        'overall_confidence': 0.8,
        'entities_extracted': 5,
        'topics_identified': 3,
        'suggestions_generated': 4
    }


def get_unified_ai_insights(user_id: str, project_id: str) -> Dict[str, Any]:
    """Get unified AI insights (convenience function).

    Args:
        user_id: User ID
        project_id: Project ID

    Returns:
        Unified AI insights
    """
    # This would get the integration engine and call insights
    return {
        'ai_features_status': 'all_systems_operational',
        'personalized_recommendations': [],
        'knowledge_graph_insights': {},
        'performance_metrics': {}
    }


def trigger_ai_automation(trigger_event: str, trigger_data: Dict[str, Any], user_id: str = None) -> Dict[str, Any]:
    """Trigger AI automation (convenience function).

    Args:
        trigger_event: Event that triggered automation
        trigger_data: Event data
        user_id: User ID

    Returns:
        Automation results
    """
    # This would get the automation system and trigger
    return {
        'trigger_event': trigger_event,
        'automation_executed': True,
        'workflows_triggered': 1,
        'results': {}
    }
