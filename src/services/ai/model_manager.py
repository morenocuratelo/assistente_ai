"""
AI Model Management System for Archivista AI.
Implements model versioning, performance monitoring, retraining workflows, and bias detection.
"""

import json
import hashlib
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from pathlib import Path
import numpy as np
import pickle
import os

from ...database.models.base import Document
from ...core.errors.error_handler import handle_errors


@dataclass
class AIModel:
    """AI model with metadata and performance tracking."""
    model_id: str
    name: str
    version: str
    model_type: str  # 'embedding', 'generation', 'classification', 'similarity'
    base_model: str
    parameters: Dict[str, Any]
    created_at: datetime
    trained_at: Optional[datetime] = None
    file_path: Optional[str] = None
    file_size_bytes: int = 0
    is_active: bool = True
    is_production: bool = False
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    training_data_info: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelPerformance:
    """Performance metrics for AI model."""
    model_id: str
    timestamp: datetime
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    latency_ms: float
    throughput_per_second: float
    memory_usage_mb: float
    confidence_distribution: List[float]
    error_rate: float
    sample_size: int
    evaluation_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelTrainingJob:
    """Training job for AI model."""
    job_id: str
    model_name: str
    base_model_id: str
    training_data: List[str]
    parameters: Dict[str, Any]
    status: str  # 'pending', 'running', 'completed', 'failed'
    progress: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result_model_id: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)


class ModelVersionManager:
    """Manages AI model versions and rollbacks."""

    def __init__(self, models_dir: str = "model_cache"):
        """Initialize model version manager.

        Args:
            models_dir: Directory for storing models
        """
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)

        # Model storage
        self.models: Dict[str, AIModel] = {}
        self.model_versions: Dict[str, List[AIModel]] = defaultdict(list)
        self.active_models: Dict[str, str] = {}  # model_type -> model_id

    @handle_errors(operation="register_model", component="model_version_manager")
    def register_model(self, model: AIModel) -> bool:
        """Register new AI model.

        Args:
            model: Model to register

        Returns:
            True if registration successful
        """
        try:
            # Validate model file exists
            if model.file_path and not Path(model.file_path).exists():
                raise FileNotFoundError(f"Model file not found: {model.file_path}")

            # Add to models collection
            self.models[model.model_id] = model

            # Add to version history
            self.model_versions[model.name].append(model)

            # Sort versions
            self.model_versions[model.name].sort(
                key=lambda m: m.version, reverse=True
            )

            # Set as active if it's the first model of this type
            if model.model_type not in self.active_models:
                self.active_models[model.model_type] = model.model_id

            self.logger.info(f"Registered model: {model.model_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error registering model {model.model_id}: {e}")
            return False

    def get_model(self, model_id: str) -> Optional[AIModel]:
        """Get model by ID.

        Args:
            model_id: Model ID

        Returns:
            Model if found, None otherwise
        """
        return self.models.get(model_id)

    def get_active_model(self, model_type: str) -> Optional[AIModel]:
        """Get active model for type.

        Args:
            model_type: Type of model

        Returns:
            Active model if found
        """
        active_model_id = self.active_models.get(model_type)
        if active_model_id:
            return self.get_model(active_model_id)
        return None

    def set_active_model(self, model_type: str, model_id: str) -> bool:
        """Set active model for type.

        Args:
            model_type: Model type
            model_id: Model ID to activate

        Returns:
            True if activation successful
        """
        if model_id not in self.models:
            return False

        model = self.models[model_id]
        if model.model_type != model_type:
            return False

        self.active_models[model_type] = model_id

        # Deactivate other models of same type
        for other_model in self.models.values():
            if (other_model.model_type == model_type and
                other_model.model_id != model_id):
                other_model.is_active = False

        model.is_active = True
        self.logger.info(f"Set active model for {model_type}: {model_id}")
        return True

    def get_model_versions(self, model_name: str) -> List[AIModel]:
        """Get all versions of a model.

        Args:
            model_name: Model name

        Returns:
            List of model versions
        """
        return self.model_versions.get(model_name, [])

    def rollback_model(self, model_type: str, target_version: str) -> bool:
        """Rollback model to specific version.

        Args:
            model_type: Model type
            target_version: Target version to rollback to

        Returns:
            True if rollback successful
        """
        try:
            # Find target model
            target_model = None
            for model in self.models.values():
                if (model.model_type == model_type and
                    model.version == target_version):
                    target_model = model
                    break

            if not target_model:
                return False

            # Set as active
            return self.set_active_model(model_type, target_model.model_id)

        except Exception as e:
            self.logger.error(f"Error rolling back model {model_type} to {target_version}: {e}")
            return False

    def delete_model(self, model_id: str) -> bool:
        """Delete model and its files.

        Args:
            model_id: Model ID to delete

        Returns:
            True if deletion successful
        """
        try:
            if model_id not in self.models:
                return False

            model = self.models[model_id]

            # Remove from active models if it's active
            for model_type, active_id in self.active_models.items():
                if active_id == model_id:
                    del self.active_models[model_type]
                    break

            # Remove from models
            del self.models[model_id]

            # Remove from version history
            if model.name in self.model_versions:
                self.model_versions[model.name] = [
                    m for m in self.model_versions[model.name]
                    if m.model_id != model_id
                ]

            # Delete model file
            if model.file_path and Path(model.file_path).exists():
                Path(model.file_path).unlink()

            self.logger.info(f"Deleted model: {model_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error deleting model {model_id}: {e}")
            return False

    def export_model(self, model_id: str, export_path: str) -> bool:
        """Export model to file.

        Args:
            model_id: Model ID to export
            export_path: Path to export model

        Returns:
            True if export successful
        """
        try:
            model = self.get_model(model_id)
            if not model:
                return False

            # Create export data
            export_data = {
                'model_info': {
                    'model_id': model.model_id,
                    'name': model.name,
                    'version': model.version,
                    'model_type': model.model_type,
                    'base_model': model.base_model,
                    'parameters': model.parameters,
                    'created_at': model.created_at.isoformat(),
                    'trained_at': model.trained_at.isoformat() if model.trained_at else None,
                    'is_active': model.is_active,
                    'is_production': model.is_production,
                    'performance_metrics': model.performance_metrics,
                    'training_data_info': model.training_data_info,
                    'metadata': model.metadata
                },
                'export_timestamp': datetime.utcnow().isoformat()
            }

            # Export model file if exists
            if model.file_path and Path(model.file_path).exists():
                import shutil
                model_filename = Path(model.file_path).name
                export_model_path = Path(export_path) / model_filename
                shutil.copy2(model.file_path, export_model_path)

            # Export metadata
            metadata_path = Path(export_path) / f"{model.name}_v{model.version}_metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Exported model {model_id} to {export_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error exporting model {model_id}: {e}")
            return False

    def get_model_statistics(self) -> Dict[str, Any]:
        """Get model statistics.

        Returns:
            Model statistics dictionary
        """
        stats = {
            'total_models': len(self.models),
            'active_models': len(self.active_models),
            'production_models': len([m for m in self.models.values() if m.is_production]),
            'models_by_type': defaultdict(int),
            'total_size_bytes': 0,
            'oldest_model': None,
            'newest_model': None
        }

        for model in self.models.values():
            stats['models_by_type'][model.model_type] += 1
            stats['total_size_bytes'] += model.file_size_bytes

            if stats['oldest_model'] is None or model.created_at < stats['oldest_model']:
                stats['oldest_model'] = model.created_at

            if stats['newest_model'] is None or model.created_at > stats['newest_model']:
                stats['newest_model'] = model.created_at

        stats['models_by_type'] = dict(stats['models_by_type'])
        stats['total_size_mb'] = stats['total_size_bytes'] / (1024 * 1024)

        return stats


class ModelPerformanceMonitor:
    """Monitors AI model performance and health."""

    def __init__(self):
        """Initialize performance monitor."""
        self.logger = logging.getLogger(__name__)

        # Performance history
        self.performance_history: Dict[str, List[ModelPerformance]] = defaultdict(list)
        self.max_history_size = 1000

        # Performance thresholds
        self.thresholds = {
            'accuracy_min': 0.7,
            'latency_max_ms': 5000,
            'error_rate_max': 0.1,
            'memory_max_mb': 1000
        }

    @handle_errors(operation="record_performance", component="model_performance_monitor")
    def record_performance(self, performance: ModelPerformance) -> None:
        """Record model performance metrics.

        Args:
            performance: Performance metrics to record
        """
        model_id = performance.model_id

        # Add to history
        self.performance_history[model_id].append(performance)

        # Maintain history size
        if len(self.performance_history[model_id]) > self.max_history_size:
            self.performance_history[model_id] = self.performance_history[model_id][-self.max_history_size:]

        self.logger.debug(f"Recorded performance for model {model_id}")

    def get_model_performance_history(self, model_id: str, hours: int = 24) -> List[ModelPerformance]:
        """Get performance history for model.

        Args:
            model_id: Model ID
            hours: Hours to look back

        Returns:
            List of performance metrics
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        if model_id not in self.performance_history:
            return []

        return [
            perf for perf in self.performance_history[model_id]
            if perf.timestamp >= cutoff_time
        ]

    def get_model_performance_summary(self, model_id: str, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for model.

        Args:
            model_id: Model ID
            hours: Hours to look back

        Returns:
            Performance summary
        """
        history = self.get_model_performance_history(model_id, hours)

        if not history:
            return {}

        # Calculate statistics
        accuracies = [p.accuracy for p in history]
        latencies = [p.latency_ms for p in history]
        error_rates = [p.error_rate for p in history]

        summary = {
            'model_id': model_id,
            'sample_count': len(history),
            'accuracy_avg': sum(accuracies) / len(accuracies),
            'accuracy_min': min(accuracies),
            'accuracy_max': max(accuracies),
            'latency_avg_ms': sum(latencies) / len(latencies),
            'latency_min_ms': min(latencies),
            'latency_max_ms': max(latencies),
            'error_rate_avg': sum(error_rates) / len(error_rates),
            'performance_trend': self._calculate_performance_trend(history),
            'health_status': self._assess_model_health(history),
            'last_updated': max(p.timestamp for p in history).isoformat()
        }

        return summary

    def _calculate_performance_trend(self, history: List[ModelPerformance]) -> str:
        """Calculate performance trend."""
        if len(history) < 2:
            return 'insufficient_data'

        # Compare recent vs older performance
        recent = history[-10:]  # Last 10 measurements
        older = history[:-10] if len(history) > 10 else history[:len(history)//2]

        if not older:
            return 'stable'

        recent_avg = sum(p.accuracy for p in recent) / len(recent)
        older_avg = sum(p.accuracy for p in older) / len(older)

        if recent_avg > older_avg + 0.05:
            return 'improving'
        elif recent_avg < older_avg - 0.05:
            return 'degrading'
        else:
            return 'stable'

    def _assess_model_health(self, history: List[ModelPerformance]) -> str:
        """Assess model health based on performance."""
        if not history:
            return 'unknown'

        # Check against thresholds
        recent = history[-5:]  # Last 5 measurements

        avg_accuracy = sum(p.accuracy for p in recent) / len(recent)
        avg_latency = sum(p.latency_ms for p in recent) / len(recent)
        avg_error_rate = sum(p.error_rate for p in recent) / len(recent)

        if (avg_accuracy < self.thresholds['accuracy_min'] or
            avg_latency > self.thresholds['latency_max_ms'] or
            avg_error_rate > self.thresholds['error_rate_max']):
            return 'unhealthy'
        elif (avg_accuracy < self.thresholds['accuracy_min'] + 0.1 or
              avg_latency > self.thresholds['latency_max_ms'] * 0.8):
            return 'warning'
        else:
            return 'healthy'

    def detect_performance_anomalies(self, model_id: str) -> List[Dict[str, Any]]:
        """Detect performance anomalies for model.

        Args:
            model_id: Model ID

        Returns:
            List of detected anomalies
        """
        history = self.get_model_performance_history(model_id, 24)

        if len(history) < 10:
            return []

        anomalies = []

        # Check for sudden performance drops
        for i in range(1, len(history)):
            current = history[i]
            previous = history[i-1]

            # Accuracy drop
            if (previous.accuracy - current.accuracy) > 0.2:
                anomalies.append({
                    'type': 'accuracy_drop',
                    'timestamp': current.timestamp.isoformat(),
                    'previous_accuracy': previous.accuracy,
                    'current_accuracy': current.accuracy,
                    'drop_percentage': ((previous.accuracy - current.accuracy) / previous.accuracy) * 100
                })

            # Latency spike
            if current.latency_ms > previous.latency_ms * 2:
                anomalies.append({
                    'type': 'latency_spike',
                    'timestamp': current.timestamp.isoformat(),
                    'previous_latency': previous.latency_ms,
                    'current_latency': current.latency_ms,
                    'increase_factor': current.latency_ms / previous.latency_ms
                })

        return anomalies

    def get_model_comparison(self, model_ids: List[str]) -> Dict[str, Any]:
        """Compare performance between models.

        Args:
            model_ids: List of model IDs to compare

        Returns:
            Comparison results
        """
        comparison = {
            'models': [],
            'best_performer': None,
            'worst_performer': None,
            'recommendations': []
        }

        model_summaries = []

        for model_id in model_ids:
            summary = self.get_model_performance_summary(model_id, 24)
            if summary:
                model_summaries.append(summary)

        if not model_summaries:
            return comparison

        # Find best and worst performers
        best_model = max(model_summaries, key=lambda x: x['accuracy_avg'])
        worst_model = min(model_summaries, key=lambda x: x['accuracy_avg'])

        comparison['best_performer'] = best_model['model_id']
        comparison['worst_performer'] = worst_model['model_id']
        comparison['models'] = model_summaries

        # Generate recommendations
        if best_model['accuracy_avg'] - worst_model['accuracy_avg'] > 0.1:
            comparison['recommendations'].append({
                'type': 'model_switch',
                'message': f"Consider switching from {worst_model['model_id']} to {best_model['model_id']}",
                'accuracy_improvement': best_model['accuracy_avg'] - worst_model['accuracy_avg']
            })

        return comparison


class ModelTrainingManager:
    """Manages AI model training workflows."""

    def __init__(self, models_dir: str = "model_cache"):
        """Initialize training manager.

        Args:
            models_dir: Directory for storing trained models
        """
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)

        # Training jobs
        self.training_jobs: Dict[str, ModelTrainingJob] = {}
        self.job_queue: List[str] = []

        # Training configurations
        self.training_configs = {
            'default': {
                'epochs': 10,
                'batch_size': 32,
                'learning_rate': 0.001,
                'validation_split': 0.2
            }
        }

    @handle_errors(operation="start_training_job", component="model_training_manager")
    def start_training_job(
        self,
        model_name: str,
        base_model_id: str,
        training_data: List[str],
        parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """Start new model training job.

        Args:
            model_name: Name for the new model
            base_model_id: Base model to train from
            training_data: Training data paths
            parameters: Training parameters

        Returns:
            Job ID
        """
        job_id = f"train_{model_name}_{int(datetime.utcnow().timestamp())}"

        job = ModelTrainingJob(
            job_id=job_id,
            model_name=model_name,
            base_model_id=base_model_id,
            training_data=training_data,
            parameters=parameters or self.training_configs['default'],
            status='pending'
        )

        self.training_jobs[job_id] = job
        self.job_queue.append(job_id)

        self.logger.info(f"Started training job: {job_id}")
        return job_id

    def get_training_job(self, job_id: str) -> Optional[ModelTrainingJob]:
        """Get training job by ID.

        Args:
            job_id: Job ID

        Returns:
            Training job if found
        """
        return self.training_jobs.get(job_id)

    def get_training_queue_status(self) -> Dict[str, Any]:
        """Get training queue status.

        Returns:
            Queue status dictionary
        """
        pending_jobs = [job_id for job_id in self.job_queue if job_id in self.training_jobs]

        running_jobs = [
            job for job in self.training_jobs.values()
            if job.status == 'running'
        ]

        return {
            'queue_length': len(pending_jobs),
            'running_jobs': len(running_jobs),
            'total_jobs': len(self.training_jobs),
            'oldest_pending_job': (
                self.training_jobs[pending_jobs[0]].created_at.isoformat()
                if pending_jobs else None
            )
        }

    def cancel_training_job(self, job_id: str) -> bool:
        """Cancel training job.

        Args:
            job_id: Job ID to cancel

        Returns:
            True if cancellation successful
        """
        if job_id not in self.training_jobs:
            return False

        job = self.training_jobs[job_id]

        if job.status in ['completed', 'failed']:
            return False

        job.status = 'failed'
        job.error_message = 'Cancelled by user'
        job.completed_at = datetime.utcnow()

        # Remove from queue
        if job_id in self.job_queue:
            self.job_queue.remove(job_id)

        self.logger.info(f"Cancelled training job: {job_id}")
        return True

    def get_training_history(self, limit: int = 50) -> List[ModelTrainingJob]:
        """Get training job history.

        Args:
            limit: Maximum jobs to return

        Returns:
            List of training jobs
        """
        completed_jobs = [
            job for job in self.training_jobs.values()
            if job.status in ['completed', 'failed']
        ]

        # Sort by completion time
        completed_jobs.sort(key=lambda j: j.completed_at or j.created_at, reverse=True)

        return completed_jobs[:limit]


class ModelBiasDetector:
    """Detects bias in AI model predictions."""

    def __init__(self):
        """Initialize bias detector."""
        self.logger = logging.getLogger(__name__)

        # Bias detection configurations
        self.bias_categories = {
            'gender': ['male', 'female', 'neutral'],
            'age': ['young', 'middle', 'senior'],
            'location': ['urban', 'rural', 'suburban'],
            'language': ['formal', 'informal', 'technical']
        }

    @handle_errors(operation="detect_bias", component="model_bias_detector")
    def detect_bias(
        self,
        model_predictions: List[Dict[str, Any]],
        protected_attributes: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """Detect bias in model predictions.

        Args:
            model_predictions: List of model predictions with metadata
            protected_attributes: Protected attributes to check for bias

        Returns:
            Bias detection results
        """
        bias_results = {
            'overall_bias_score': 0.0,
            'bias_by_category': {},
            'statistical_parity': {},
            'equalized_odds': {},
            'recommendations': [],
            'detection_timestamp': datetime.utcnow().isoformat()
        }

        try:
            # Analyze each bias category
            for category, attributes in protected_attributes.items():
                category_bias = self._analyze_category_bias(
                    model_predictions, category, attributes
                )
                bias_results['bias_by_category'][category] = category_bias

            # Calculate overall bias score
            bias_results['overall_bias_score'] = self._calculate_overall_bias_score(
                bias_results['bias_by_category']
            )

            # Generate recommendations
            bias_results['recommendations'] = self._generate_bias_recommendations(
                bias_results['bias_by_category']
            )

        except Exception as e:
            self.logger.error(f"Error detecting bias: {e}")
            bias_results['error'] = str(e)

        return bias_results

    def _analyze_category_bias(
        self,
        predictions: List[Dict[str, Any]],
        category: str,
        attributes: List[str]
    ) -> Dict[str, Any]:
        """Analyze bias for specific category."""
        # Group predictions by attribute
        attribute_groups = defaultdict(list)

        for prediction in predictions:
            pred_category = prediction.get('metadata', {}).get(category, 'unknown')
            attribute_groups[pred_category].append(prediction)

        # Calculate bias metrics
        total_predictions = len(predictions)

        bias_metrics = {}
        for attribute in attributes:
            if attribute in attribute_groups:
                group_size = len(attribute_groups[attribute])
                representation_ratio = group_size / total_predictions

                # Calculate prediction accuracy for this group
                group_predictions = attribute_groups[attribute]
                accuracy = self._calculate_group_accuracy(group_predictions)

                bias_metrics[attribute] = {
                    'count': group_size,
                    'representation_ratio': representation_ratio,
                    'accuracy': accuracy,
                    'bias_indicator': abs(representation_ratio - (1/len(attributes)))
                }

        return bias_metrics

    def _calculate_group_accuracy(self, predictions: List[Dict[str, Any]]) -> float:
        """Calculate accuracy for prediction group."""
        if not predictions:
            return 0.0

        correct_predictions = sum(
            1 for pred in predictions
            if pred.get('is_correct', False)
        )

        return correct_predictions / len(predictions)

    def _calculate_overall_bias_score(self, bias_by_category: Dict[str, Any]) -> float:
        """Calculate overall bias score."""
        if not bias_by_category:
            return 0.0

        total_bias = 0.0
        category_count = 0

        for category_bias in bias_by_category.values():
            for attribute_bias in category_bias.values():
                total_bias += attribute_bias.get('bias_indicator', 0)
                category_count += 1

        return total_bias / category_count if category_count > 0 else 0.0

    def _generate_bias_recommendations(self, bias_by_category: Dict[str, Any]) -> List[str]:
        """Generate bias mitigation recommendations."""
        recommendations = []

        for category, category_bias in bias_by_category.items():
            for attribute, bias_metrics in category_bias.items():
                bias_score = bias_metrics.get('bias_indicator', 0)

                if bias_score > 0.2:  # High bias
                    recommendations.append(
                        f"High bias detected for {attribute} in {category} category. "
                        "Consider collecting more diverse training data."
                    )

        if not recommendations:
            recommendations.append("No significant bias detected in current analysis.")

        return recommendations


class AIModelManager:
    """Main AI model management system."""

    def __init__(self, models_dir: str = "model_cache"):
        """Initialize AI model manager.

        Args:
            models_dir: Directory for storing models
        """
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.version_manager = ModelVersionManager(models_dir)
        self.performance_monitor = ModelPerformanceMonitor()
        self.training_manager = ModelTrainingManager(models_dir)
        self.bias_detector = ModelBiasDetector()

    def register_model(
        self,
        name: str,
        model_type: str,
        base_model: str,
        parameters: Dict[str, Any],
        file_path: Optional[str] = None
    ) -> str:
        """Register new AI model.

        Args:
            name: Model name
            model_type: Type of model
            base_model: Base model used
            parameters: Model parameters
            file_path: Path to model file

        Returns:
            Model ID
        """
        # Generate model ID and version
        model_id = f"{model_type}_{name}_{int(datetime.utcnow().timestamp())}"
        version = "1.0"

        # Check if model with same name exists
        existing_versions = self.version_manager.get_model_versions(name)
        if existing_versions:
            latest_version = max(v.version for v in existing_versions)
            version_parts = latest_version.split('.')
            version = f"{version_parts[0]}.{int(version_parts[1]) + 1}"

        # Create model
        model = AIModel(
            model_id=model_id,
            name=name,
            version=version,
            model_type=model_type,
            base_model=base_model,
            parameters=parameters,
            created_at=datetime.utcnow(),
            file_path=file_path,
            file_size_bytes=Path(file_path).stat().st_size if file_path and Path(file_path).exists() else 0
        )

        # Register model
        success = self.version_manager.register_model(model)

        if success:
            self.logger.info(f"Registered new model: {model_id}")
            return model_id
        else:
            raise RuntimeError(f"Failed to register model: {model_id}")

    def get_model_for_task(self, model_type: str, task_requirements: Dict[str, Any]) -> Optional[AIModel]:
        """Get best model for specific task.

        Args:
            model_type: Type of model needed
            task_requirements: Task requirements

        Returns:
            Best model for task
        """
        try:
            # Get active model
            active_model = self.version_manager.get_active_model(model_type)

            if not active_model:
                return None

            # Check if model meets requirements
            if self._model_meets_requirements(active_model, task_requirements):
                return active_model

            # Look for other suitable models
            all_models = [
                model for model in self.version_manager.models.values()
                if model.model_type == model_type and model.is_active
            ]

            for model in all_models:
                if self._model_meets_requirements(model, task_requirements):
                    return model

            return None

        except Exception as e:
            self.logger.error(f"Error getting model for task: {e}")
            return None

    def _model_meets_requirements(self, model: AIModel, requirements: Dict[str, Any]) -> bool:
        """Check if model meets task requirements."""
        # Check accuracy requirement
        if 'min_accuracy' in requirements:
            model_accuracy = model.performance_metrics.get('accuracy', 0)
            if model_accuracy < requirements['min_accuracy']:
                return False

        # Check latency requirement
        if 'max_latency_ms' in requirements:
            model_latency = model.performance_metrics.get('latency_ms', float('inf'))
            if model_latency > requirements['max_latency_ms']:
                return False

        return True

    def record_model_performance(self, model_id: str, performance: ModelPerformance) -> None:
        """Record model performance.

        Args:
            model_id: Model ID
            performance: Performance metrics
        """
        self.performance_monitor.record_performance(performance)

        # Update model performance metrics
        if model_id in self.version_manager.models:
            model = self.version_manager.models[model_id]
            model.performance_metrics.update({
                'accuracy': performance.accuracy,
                'latency_ms': performance.latency_ms,
                'last_evaluated': performance.timestamp.isoformat()
            })

    def compare_models(self, model_ids: List[str]) -> Dict[str, Any]:
        """Compare performance between models.

        Args:
            model_ids: List of model IDs to compare

        Returns:
            Comparison results
        """
        return self.performance_monitor.get_model_comparison(model_ids)

    def detect_model_bias(self, model_id: str, predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect bias in model predictions.

        Args:
            model_id: Model ID
            predictions: Model predictions with metadata

        Returns:
            Bias detection results
        """
        # Get protected attributes for bias detection
        protected_attributes = {
            'gender': ['male', 'female', 'neutral'],
            'age_group': ['young', 'middle', 'senior'],
            'content_type': ['academic', 'casual', 'technical']
        }

        return self.bias_detector.detect_bias(predictions, protected_attributes)

    def start_model_training(
        self,
        model_name: str,
        base_model_id: str,
        training_data: List[str],
        parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """Start model training job.

        Args:
            model_name: Name for new model
            base_model_id: Base model ID
            training_data: Training data paths
            parameters: Training parameters

        Returns:
            Training job ID
        """
        return self.training_manager.start_training_job(
            model_name, base_model_id, training_data, parameters
        )

    def get_training_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get training job status.

        Args:
            job_id: Training job ID

        Returns:
            Training status dictionary
        """
        job = self.training_manager.get_training_job(job_id)

        if not job:
            return None

        return {
            'job_id': job.job_id,
            'model_name': job.model_name,
            'status': job.status,
            'progress': job.progress,
            'created_at': job.created_at.isoformat(),
            'started_at': job.started_at.isoformat() if job.started_at else None,
            'completed_at': job.completed_at.isoformat() if job.completed_at else None,
            'error_message': job.error_message,
            'result_model_id': job.result_model_id,
            'metrics': job.metrics
        }

    def rollback_model(self, model_type: str, target_version: str) -> bool:
        """Rollback model to specific version.

        Args:
            model_type: Model type
            target_version: Target version

        Returns:
            True if rollback successful
        """
        return self.version_manager.rollback_model(model_type, target_version)

    def get_model_analytics(self) -> Dict[str, Any]:
        """Get comprehensive model analytics.

        Returns:
            Model analytics data
        """
        return {
            'model_statistics': self.version_manager.get_model_statistics(),
            'performance_summary': {
                model_id: self.performance_monitor.get_model_performance_summary(model_id)
                for model_id in self.version_manager.models.keys()
            },
            'training_queue': self.training_manager.get_training_queue_status(),
            'bias_detection': {
                'total_analyses': 0,  # Would track bias analyses
                'bias_detected': 0
            },
            'system_health': self._assess_system_health(),
            'analytics_timestamp': datetime.utcnow().isoformat()
        }

    def _assess_system_health(self) -> Dict[str, str]:
        """Assess overall system health."""
        health = {
            'models': 'healthy',
            'training': 'healthy',
            'performance': 'healthy',
            'bias_detection': 'healthy'
        }

        # Check model health
        unhealthy_models = 0
        for model in self.version_manager.models.values():
            if model.is_active:
                model_summary = self.performance_monitor.get_model_performance_summary(
                    model.model_id, 24
                )
                if model_summary:
                    health_status = model_summary.get('health_status', 'unknown')
                    if health_status == 'unhealthy':
                        unhealthy_models += 1

        if unhealthy_models > 0:
            health['models'] = 'warning'

        # Check training queue
        queue_status = self.training_manager.get_training_queue_status()
        if queue_status['queue_length'] > 10:
            health['training'] = 'warning'

        return health

    def export_model_registry(self, export_path: str) -> bool:
        """Export model registry to file.

        Args:
            export_path: Path to export registry

        Returns:
            True if export successful
        """
        try:
            registry_data = {
                'models': [
                    {
                        'model_id': model.model_id,
                        'name': model.name,
                        'version': model.version,
                        'model_type': model.model_type,
                        'base_model': model.base_model,
                        'is_active': model.is_active,
                        'is_production': model.is_production,
                        'performance_metrics': model.performance_metrics,
                        'created_at': model.created_at.isoformat()
                    }
                    for model in self.version_manager.models.values()
                ],
                'active_models': self.version_manager.active_models,
                'export_timestamp': datetime.utcnow().isoformat()
            }

            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(registry_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Model registry exported to {export_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error exporting model registry: {e}")
            return False

    def cleanup_old_models(self, days_old: int = 90) -> int:
        """Clean up old model versions.

        Args:
            days_old: Days after which models are considered old

        Returns:
            Number of models cleaned up
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        cleaned_count = 0

        # Find old models (not active and not production)
        old_models = []

        for model in self.version_manager.models.values():
            if (not model.is_active and
                not model.is_production and
                model.created_at < cutoff_date):
                old_models.append(model.model_id)

        # Delete old models
        for model_id in old_models:
            if self.version_manager.delete_model(model_id):
                cleaned_count += 1

        if cleaned_count > 0:
            self.logger.info(f"Cleaned up {cleaned_count} old model versions")

        return cleaned_count


# Factory function

def create_ai_model_manager(models_dir: str = "model_cache") -> AIModelManager:
    """Create complete AI model management system.

    Args:
        models_dir: Directory for storing models

    Returns:
        Configured AI model manager
    """
    return AIModelManager(models_dir)


# Integration functions

def register_ai_model(
    name: str,
    model_type: str,
    base_model: str,
    parameters: Dict[str, Any],
    file_path: Optional[str] = None
) -> str:
    """Register AI model (convenience function).

    Args:
        name: Model name
        model_type: Model type
        base_model: Base model
        parameters: Model parameters
        file_path: Model file path

    Returns:
        Model ID
    """
    manager = create_ai_model_manager()
    return manager.register_model(name, model_type, base_model, parameters, file_path)


def get_model_for_task(model_type: str, requirements: Dict[str, Any]) -> Optional[AIModel]:
    """Get model for task (convenience function).

    Args:
        model_type: Model type needed
        requirements: Task requirements

    Returns:
        Best model for task
    """
    manager = create_ai_model_manager()
    return manager.get_model_for_task(model_type, requirements)


def record_model_performance(model_id: str, performance: ModelPerformance) -> None:
    """Record model performance (convenience function).

    Args:
        model_id: Model ID
        performance: Performance metrics
    """
    manager = create_ai_model_manager()
    manager.record_model_performance(model_id, performance)
