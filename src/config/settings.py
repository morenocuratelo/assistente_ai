"""
Configuration management module.
Centralized configuration with validation and hot-reloading capabilities.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

from .validation import ConfigValidator


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    url: str = "sqlite:///db_memoria/metadata.sqlite"
    pool_size: int = 5
    timeout: int = 30
    retry_attempts: int = 3
    connection_max_age: int = 3600  # 1 hour
    enable_metrics: bool = True


@dataclass
class AIConfig:
    """AI service configuration settings."""
    model_name: str = "llama3"
    temperature: float = 0.7
    max_tokens: int = 1000
    api_key: str = ""
    base_url: str = "http://localhost:11434"
    request_timeout: int = 60
    max_retries: int = 3
    enable_streaming: bool = True
    confidence_threshold: float = 0.5


@dataclass
class UIConfig:
    """UI configuration settings."""
    theme: str = "light"
    language: str = "it"
    items_per_page: int = 20
    max_file_size_mb: int = 100
    enable_animations: bool = True
    enable_tooltips: bool = True
    session_timeout_minutes: int = 60


@dataclass
class LoggingConfig:
    """Logging configuration settings."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size_mb: int = 100
    backup_count: int = 5
    enable_cloud_logging: bool = False


@dataclass
class SecurityConfig:
    """Security configuration settings."""
    secret_key: str = ""
    token_expiration_hours: int = 24
    password_min_length: int = 8
    enable_rate_limiting: bool = True
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30
    enable_audit_logging: bool = True


@dataclass
class PerformanceConfig:
    """Performance configuration settings."""
    enable_caching: bool = True
    cache_ttl_seconds: int = 300
    enable_async_processing: bool = True
    max_workers: int = 4
    batch_size: int = 10
    enable_metrics: bool = True


@dataclass
class AppConfig:
    """Main application configuration."""
    # Core settings
    app_name: str = "Archivista AI"
    version: str = "2.5"
    environment: str = "development"
    debug: bool = True

    # Component configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)

    # Additional settings
    data_dir: str = "db_memoria"
    upload_dir: str = "documenti_da_processare"
    temp_dir: str = "temp"
    backup_dir: str = "backups"

    # Feature flags
    enable_knowledge_graph: bool = True
    enable_bayesian_inference: bool = True
    enable_real_time_collaboration: bool = False
    enable_advanced_analytics: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'app_name': self.app_name,
            'version': self.version,
            'environment': self.environment,
            'debug': self.debug,
            'database': {
                'url': self.database.url,
                'pool_size': self.database.pool_size,
                'timeout': self.database.timeout,
                'retry_attempts': self.database.retry_attempts,
                'connection_max_age': self.database.connection_max_age,
                'enable_metrics': self.database.enable_metrics,
            },
            'ai': {
                'model_name': self.ai.model_name,
                'temperature': self.ai.temperature,
                'max_tokens': self.ai.max_tokens,
                'api_key': self.ai.api_key,
                'base_url': self.ai.base_url,
                'request_timeout': self.ai.request_timeout,
                'max_retries': self.ai.max_retries,
                'enable_streaming': self.ai.enable_streaming,
                'confidence_threshold': self.ai.confidence_threshold,
            },
            'ui': {
                'theme': self.ui.theme,
                'language': self.ui.language,
                'items_per_page': self.ui.items_per_page,
                'max_file_size_mb': self.ui.max_file_size_mb,
                'enable_animations': self.ui.enable_animations,
                'enable_tooltips': self.ui.enable_tooltips,
                'session_timeout_minutes': self.ui.session_timeout_minutes,
            },
            'logging': {
                'level': self.logging.level,
                'format': self.logging.format,
                'file_path': self.logging.file_path,
                'max_file_size_mb': self.logging.max_file_size_mb,
                'backup_count': self.logging.backup_count,
                'enable_cloud_logging': self.logging.enable_cloud_logging,
            },
            'security': {
                'secret_key': self.security.secret_key,
                'token_expiration_hours': self.security.token_expiration_hours,
                'password_min_length': self.security.password_min_length,
                'enable_rate_limiting': self.security.enable_rate_limiting,
                'max_login_attempts': self.security.max_login_attempts,
                'lockout_duration_minutes': self.security.lockout_duration_minutes,
                'enable_audit_logging': self.security.enable_audit_logging,
            },
            'performance': {
                'enable_caching': self.performance.enable_caching,
                'cache_ttl_seconds': self.performance.cache_ttl_seconds,
                'enable_async_processing': self.performance.enable_async_processing,
                'max_workers': self.performance.max_workers,
                'batch_size': self.performance.batch_size,
                'enable_metrics': self.performance.enable_metrics,
            },
            'data_dir': self.data_dir,
            'upload_dir': self.upload_dir,
            'temp_dir': self.temp_dir,
            'backup_dir': self.backup_dir,
            'enable_knowledge_graph': self.enable_knowledge_graph,
            'enable_bayesian_inference': self.enable_bayesian_inference,
            'enable_real_time_collaboration': self.enable_real_time_collaboration,
            'enable_advanced_analytics': self.enable_advanced_analytics,
        }


class ConfigurationManager:
    """Centralized configuration manager with hot-reloading."""

    def __init__(self, config_file: str = "config.json"):
        """Initialize configuration manager.

        Args:
            config_file: Path to configuration file
        """
        self.config_file = Path(config_file)
        self._config: Optional[AppConfig] = None
        self._validator = ConfigValidator()
        self._last_modified: Optional[datetime] = None
        self._listeners: List[callable] = []
        self.logger = logging.getLogger(__name__)

        # Load initial configuration
        self._load_configuration()

    def _load_configuration(self) -> None:
        """Load configuration from file and environment."""
        try:
            # Start with default configuration
            config_data = self._get_default_config()

            # Override with file configuration if exists
            if self.config_file.exists():
                file_config = self._load_from_file()
                config_data.update(file_config)

            # Override with environment variables
            env_config = self._load_from_environment()
            config_data.update(env_config)

            # Create configuration object
            self._config = self._build_config_object(config_data)

            # Validate configuration
            validation_errors = self._validator.validate_config(config_data)
            if validation_errors:
                self.logger.warning(f"Configuration validation errors: {validation_errors}")

            self._last_modified = datetime.utcnow()
            self.logger.info("Configuration loaded successfully")

        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            # Fallback to default configuration
            self._config = AppConfig()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            'app_name': 'Archivista AI',
            'version': '2.5',
            'environment': 'development',
            'debug': True,
            'database': {
                'url': 'sqlite:///db_memoria/metadata.sqlite',
                'pool_size': 5,
                'timeout': 30,
                'retry_attempts': 3,
                'connection_max_age': 3600,
                'enable_metrics': True,
            },
            'ai': {
                'model_name': 'llama3',
                'temperature': 0.7,
                'max_tokens': 1000,
                'api_key': '',
                'base_url': 'http://localhost:11434',
                'request_timeout': 60,
                'max_retries': 3,
                'enable_streaming': True,
                'confidence_threshold': 0.5,
            },
            'ui': {
                'theme': 'light',
                'language': 'it',
                'items_per_page': 20,
                'max_file_size_mb': 100,
                'enable_animations': True,
                'enable_tooltips': True,
                'session_timeout_minutes': 60,
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file_path': None,
                'max_file_size_mb': 100,
                'backup_count': 5,
                'enable_cloud_logging': False,
            },
            'security': {
                'secret_key': '',
                'token_expiration_hours': 24,
                'password_min_length': 8,
                'enable_rate_limiting': True,
                'max_login_attempts': 5,
                'lockout_duration_minutes': 30,
                'enable_audit_logging': True,
            },
            'performance': {
                'enable_caching': True,
                'cache_ttl_seconds': 300,
                'enable_async_processing': True,
                'max_workers': 4,
                'batch_size': 10,
                'enable_metrics': True,
            },
            'data_dir': 'db_memoria',
            'upload_dir': 'documenti_da_processare',
            'temp_dir': 'temp',
            'backup_dir': 'backups',
            'enable_knowledge_graph': True,
            'enable_bayesian_inference': True,
            'enable_real_time_collaboration': False,
            'enable_advanced_analytics': True,
        }

    def _load_from_file(self) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.warning(f"Could not load config file: {e}")
            return {}

    def _load_from_environment(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        config = {}

        # Database settings
        if os.getenv('DATABASE_URL'):
            config.setdefault('database', {})['url'] = os.getenv('DATABASE_URL')
        if os.getenv('DB_POOL_SIZE'):
            config.setdefault('database', {})['pool_size'] = int(os.getenv('DB_POOL_SIZE'))
        if os.getenv('DB_TIMEOUT'):
            config.setdefault('database', {})['timeout'] = int(os.getenv('DB_TIMEOUT'))

        # AI settings
        if os.getenv('AI_MODEL_NAME'):
            config.setdefault('ai', {})['model_name'] = os.getenv('AI_MODEL_NAME')
        if os.getenv('AI_API_KEY'):
            config.setdefault('ai', {})['api_key'] = os.getenv('AI_API_KEY')
        if os.getenv('AI_BASE_URL'):
            config.setdefault('ai', {})['base_url'] = os.getenv('AI_BASE_URL')
        if os.getenv('AI_TEMPERATURE'):
            config.setdefault('ai', {})['temperature'] = float(os.getenv('AI_TEMPERATURE'))

        # UI settings
        if os.getenv('UI_THEME'):
            config.setdefault('ui', {})['theme'] = os.getenv('UI_THEME')
        if os.getenv('UI_LANGUAGE'):
            config.setdefault('ui', {})['language'] = os.getenv('UI_LANGUAGE')
        if os.getenv('UI_ITEMS_PER_PAGE'):
            config.setdefault('ui', {})['items_per_page'] = int(os.getenv('UI_ITEMS_PER_PAGE'))

        # Security settings
        if os.getenv('SECRET_KEY'):
            config.setdefault('security', {})['secret_key'] = os.getenv('SECRET_KEY')
        if os.getenv('TOKEN_EXPIRATION_HOURS'):
            config.setdefault('security', {})['token_expiration_hours'] = int(os.getenv('TOKEN_EXPIRATION_HOURS'))

        # Feature flags
        if os.getenv('ENABLE_KNOWLEDGE_GRAPH'):
            config['enable_knowledge_graph'] = os.getenv('ENABLE_KNOWLEDGE_GRAPH').lower() == 'true'
        if os.getenv('ENABLE_BAYESIAN_INFERENCE'):
            config['enable_bayesian_inference'] = os.getenv('ENABLE_BAYESIAN_INFERENCE').lower() == 'true'
        if os.getenv('DEBUG'):
            config['debug'] = os.getenv('DEBUG').lower() == 'true'

        return config

    def _build_config_object(self, config_data: Dict[str, Any]) -> AppConfig:
        """Build AppConfig object from dictionary data."""
        # Database config
        db_config = DatabaseConfig(**config_data.get('database', {}))

        # AI config
        ai_config = AIConfig(**config_data.get('ai', {}))

        # UI config
        ui_config = UIConfig(**config_data.get('ui', {}))

        # Logging config
        logging_config = LoggingConfig(**config_data.get('logging', {}))

        # Security config
        security_config = SecurityConfig(**config_data.get('security', {}))

        # Performance config
        performance_config = PerformanceConfig(**config_data.get('performance', {}))

        return AppConfig(
            app_name=config_data.get('app_name', 'Archivista AI'),
            version=config_data.get('version', '2.5'),
            environment=config_data.get('environment', 'development'),
            debug=config_data.get('debug', True),
            database=db_config,
            ai=ai_config,
            ui=ui_config,
            logging=logging_config,
            security=security_config,
            performance=performance_config,
            data_dir=config_data.get('data_dir', 'db_memoria'),
            upload_dir=config_data.get('upload_dir', 'documenti_da_processare'),
            temp_dir=config_data.get('temp_dir', 'temp'),
            backup_dir=config_data.get('backup_dir', 'backups'),
            enable_knowledge_graph=config_data.get('enable_knowledge_graph', True),
            enable_bayesian_inference=config_data.get('enable_bayesian_inference', True),
            enable_real_time_collaboration=config_data.get('enable_real_time_collaboration', False),
            enable_advanced_analytics=config_data.get('enable_advanced_analytics', True),
        )

    def get_config(self) -> AppConfig:
        """Get current configuration.

        Returns:
            Current application configuration
        """
        if self._config is None:
            self._load_configuration()
        return self._config

    def reload_config(self) -> bool:
        """Reload configuration from sources.

        Returns:
            True if reload successful
        """
        try:
            old_config = self._config
            self._load_configuration()

            # Notify listeners if config changed
            if old_config != self._config:
                self._notify_listeners()

            return True

        except Exception as e:
            self.logger.error(f"Error reloading configuration: {e}")
            return False

    def save_config(self, config: AppConfig) -> bool:
        """Save configuration to file.

        Args:
            config: Configuration to save

        Returns:
            True if save successful
        """
        try:
            # Ensure config directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            # Convert to dictionary and save
            config_dict = config.to_dict()
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Configuration saved to {self.config_file}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            return False

    def update_config(self, updates: Dict[str, Any]) -> bool:
        """Update configuration with new values.

        Args:
            updates: Dictionary of configuration updates

        Returns:
            True if update successful
        """
        try:
            # Get current config as dict
            current_dict = self.get_config().to_dict()

            # Apply updates recursively
            self._deep_update(current_dict, updates)

            # Validate updated configuration
            validation_errors = self._validator.validate_config(current_dict)
            if validation_errors:
                self.logger.error(f"Configuration validation failed: {validation_errors}")
                return False

            # Create new config object
            self._config = self._build_config_object(current_dict)

            # Save to file
            self.save_config(self._config)

            # Notify listeners
            self._notify_listeners()

            return True

        except Exception as e:
            self.logger.error(f"Error updating configuration: {e}")
            return False

    def _deep_update(self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> None:
        """Recursively update dictionary."""
        for key, value in update_dict.items():
            if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value

    def add_config_listener(self, listener: callable) -> None:
        """Add configuration change listener.

        Args:
            listener: Function to call when config changes
        """
        self._listeners.append(listener)

    def remove_config_listener(self, listener: callable) -> None:
        """Remove configuration change listener.

        Args:
            listener: Function to remove
        """
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _notify_listeners(self) -> None:
        """Notify all listeners of configuration changes."""
        for listener in self._listeners:
            try:
                listener(self._config)
            except Exception as e:
                self.logger.error(f"Error notifying config listener: {e}")

    def is_config_file_modified(self) -> bool:
        """Check if configuration file has been modified.

        Returns:
            True if file has been modified since last load
        """
        if not self.config_file.exists():
            return False

        try:
            current_modified = datetime.utcfromtimestamp(self.config_file.stat().st_mtime)
            return current_modified > self._last_modified
        except Exception:
            return False

    def watch_config_file(self, callback: Optional[callable] = None) -> None:
        """Watch configuration file for changes and reload if modified.

        Args:
            callback: Optional callback to execute after reload
        """
        if self.is_config_file_modified():
            self.logger.info("Configuration file modified, reloading...")
            self.reload_config()

            if callback:
                callback(self._config)

    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary for monitoring.

        Returns:
            Dictionary with configuration summary
        """
        config = self.get_config()
        return {
            'app_name': config.app_name,
            'version': config.version,
            'environment': config.environment,
            'debug': config.debug,
            'database_url': config.database.url,
            'ai_model': config.ai.model_name,
            'ui_theme': config.ui.theme,
            'features': {
                'knowledge_graph': config.enable_knowledge_graph,
                'bayesian_inference': config.enable_bayesian_inference,
                'real_time_collaboration': config.enable_real_time_collaboration,
                'advanced_analytics': config.enable_advanced_analytics,
            },
            'last_modified': self._last_modified.isoformat() if self._last_modified else None,
            'config_file': str(self.config_file),
            'validation_errors': self._validator.validate_config(config.to_dict())
        }

    def reset_to_defaults(self) -> bool:
        """Reset configuration to defaults.

        Returns:
            True if reset successful
        """
        try:
            self._config = AppConfig()
            self.save_config(self._config)
            self._notify_listeners()
            self.logger.info("Configuration reset to defaults")
            return True

        except Exception as e:
            self.logger.error(f"Error resetting configuration: {e}")
            return False

    def export_config(self, export_path: str) -> bool:
        """Export current configuration to file.

        Args:
            export_path: Path to export configuration

        Returns:
            True if export successful
        """
        try:
            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)

            config_dict = self.get_config().to_dict()
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Configuration exported to {export_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error exporting configuration: {e}")
            return False

    def import_config(self, import_path: str) -> bool:
        """Import configuration from file.

        Args:
            import_path: Path to configuration file to import

        Returns:
            True if import successful
        """
        try:
            import_file = Path(import_path)
            if not import_file.exists():
                raise FileNotFoundError(f"Configuration file not found: {import_path}")

            with open(import_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # Validate imported configuration
            validation_errors = self._validator.validate_config(config_data)
            if validation_errors:
                self.logger.error(f"Imported configuration validation failed: {validation_errors}")
                return False

            # Apply imported configuration
            self._config = self._build_config_object(config_data)
            self.save_config(self._config)
            self._notify_listeners()

            self.logger.info(f"Configuration imported from {import_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error importing configuration: {e}")
            return False


# Global configuration instance
_config_manager: Optional[ConfigurationManager] = None


def get_config_manager() -> ConfigurationManager:
    """Get global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigurationManager()
    return _config_manager


def get_config() -> AppConfig:
    """Get current application configuration."""
    return get_config_manager().get_config()


def reload_config() -> bool:
    """Reload configuration from sources."""
    return get_config_manager().reload_config()


def update_config(updates: Dict[str, Any]) -> bool:
    """Update configuration with new values."""
    return get_config_manager().update_config(updates)


# Convenience functions for common configuration access

def get_database_config() -> DatabaseConfig:
    """Get database configuration."""
    return get_config().database


def get_ai_config() -> AIConfig:
    """Get AI configuration."""
    return get_config().ai


def get_ui_config() -> UIConfig:
    """Get UI configuration."""
    return get_config().ui


def is_debug_mode() -> bool:
    """Check if application is in debug mode."""
    return get_config().debug


def is_feature_enabled(feature: str) -> bool:
    """Check if a feature is enabled.

    Args:
        feature: Feature name to check

    Returns:
        True if feature is enabled
    """
    config = get_config()
    feature_map = {
        'knowledge_graph': config.enable_knowledge_graph,
        'bayesian_inference': config.enable_bayesian_inference,
        'real_time_collaboration': config.enable_real_time_collaboration,
        'advanced_analytics': config.enable_advanced_analytics,
    }
    return feature_map.get(feature, False)
