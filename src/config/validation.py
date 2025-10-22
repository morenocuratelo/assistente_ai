"""
Configuration validation module.
Validates configuration values and provides detailed error reporting.
"""

import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass
class ValidationError:
    """Rappresenta un errore di validazione configurazione."""
    field: str
    value: Any
    message: str
    severity: str = "error"  # error, warning, info


class ConfigValidator:
    """Validatore configurazione applicazione."""

    def __init__(self):
        """Inizializza validatore configurazione."""
        self.validation_rules = {
            'app_name': self._validate_app_name,
            'version': self._validate_version,
            'environment': self._validate_environment,
            'debug': self._validate_debug,
            'database': self._validate_database_config,
            'ai': self._validate_ai_config,
            'ui': self._validate_ui_config,
            'logging': self._validate_logging_config,
            'security': self._validate_security_config,
            'performance': self._validate_performance_config,
        }

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Valida configurazione completa.

        Args:
            config: Dizionario configurazione da validare

        Returns:
            Lista messaggi errore validazione
        """
        errors = []

        # Valida campi principali
        for field, validator in self.validation_rules.items():
            if field in config:
                field_errors = validator(config[field])
                errors.extend([f"{field}: {error}" for error in field_errors])

        # Valida campi custom
        if 'data_dir' in config:
            data_dir_errors = self._validate_data_dir(config['data_dir'])
            errors.extend([f"data_dir: {error}" for error in data_dir_errors])

        if 'upload_dir' in config:
            upload_dir_errors = self._validate_upload_dir(config['upload_dir'])
            errors.extend([f"upload_dir: {error}" for error in upload_dir_errors])

        if 'temp_dir' in config:
            temp_dir_errors = self._validate_temp_dir(config['temp_dir'])
            errors.extend([f"temp_dir: {error}" for error in temp_dir_errors])

        if 'backup_dir' in config:
            backup_dir_errors = self._validate_backup_dir(config['backup_dir'])
            errors.extend([f"backup_dir: {error}" for error in backup_dir_errors])

        # Valida feature flags
        feature_flags = [
            'enable_knowledge_graph', 'enable_bayesian_inference',
            'enable_real_time_collaboration', 'enable_advanced_analytics'
        ]

        for flag in feature_flags:
            if flag in config:
                flag_errors = self._validate_feature_flag(config[flag])
                errors.extend([f"{flag}: {error}" for error in flag_errors])

        return errors

    def _validate_app_name(self, value: Any) -> List[str]:
        """Valida nome applicazione."""
        errors = []

        if not isinstance(value, str):
            errors.append("Deve essere una stringa")
            return errors

        if not value.strip():
            errors.append("Non può essere vuoto")
            return errors

        if len(value) > 100:
            errors.append("Non può essere più lungo di 100 caratteri")

        return errors

    def _validate_version(self, value: Any) -> List[str]:
        """Valida versione applicazione."""
        errors = []

        if not isinstance(value, str):
            errors.append("Deve essere una stringa")
            return errors

        # Pattern versione semantica (x.y.z)
        version_pattern = r'^\d+\.\d+\.\d+$'
        if not re.match(version_pattern, value):
            errors.append("Deve seguire formato semantico x.y.z")

        return errors

    def _validate_environment(self, value: Any) -> List[str]:
        """Valida ambiente esecuzione."""
        errors = []

        if not isinstance(value, str):
            errors.append("Deve essere una stringa")
            return errors

        valid_environments = ['development', 'test', 'staging', 'production']
        if value not in valid_environments:
            errors.append(f"Deve essere uno di: {', '.join(valid_environments)}")

        return errors

    def _validate_debug(self, value: Any) -> List[str]:
        """Valida flag debug."""
        errors = []

        if not isinstance(value, bool):
            errors.append("Deve essere un booleano")

        return errors

    def _validate_database_config(self, config: Dict[str, Any]) -> List[str]:
        """Valida configurazione database."""
        errors = []

        if not isinstance(config, dict):
            errors.append("Deve essere un dizionario")
            return errors

        # Valida URL database
        if 'url' in config:
            url_errors = self._validate_database_url(config['url'])
            errors.extend([f"url: {error}" for error in url_errors])

        # Valida pool size
        if 'pool_size' in config:
            pool_errors = self._validate_pool_size(config['pool_size'])
            errors.extend([f"pool_size: {error}" for error in pool_errors])

        # Valida timeout
        if 'timeout' in config:
            timeout_errors = self._validate_timeout(config['timeout'])
            errors.extend([f"timeout: {error}" for error in timeout_errors])

        # Valida retry attempts
        if 'retry_attempts' in config:
            retry_errors = self._validate_retry_attempts(config['retry_attempts'])
            errors.extend([f"retry_attempts: {error}" for error in retry_errors])

        return errors

    def _validate_ai_config(self, config: Dict[str, Any]) -> List[str]:
        """Valida configurazione AI."""
        errors = []

        if not isinstance(config, dict):
            errors.append("Deve essere un dizionario")
            return errors

        # Valida model name
        if 'model_name' in config:
            model_errors = self._validate_model_name(config['model_name'])
            errors.extend([f"model_name: {error}" for error in model_errors])

        # Valida temperature
        if 'temperature' in config:
            temp_errors = self._validate_temperature(config['temperature'])
            errors.extend([f"temperature: {error}" for error in temp_errors])

        # Valida max tokens
        if 'max_tokens' in config:
            token_errors = self._validate_max_tokens(config['max_tokens'])
            errors.extend([f"max_tokens: {error}" for error in token_errors])

        # Valida base URL
        if 'base_url' in config:
            url_errors = self._validate_ai_base_url(config['base_url'])
            errors.extend([f"base_url: {error}" for error in url_errors])

        # Valida timeout
        if 'request_timeout' in config:
            timeout_errors = self._validate_ai_timeout(config['request_timeout'])
            errors.extend([f"request_timeout: {error}" for error in timeout_errors])

        return errors

    def _validate_ui_config(self, config: Dict[str, Any]) -> List[str]:
        """Valida configurazione UI."""
        errors = []

        if not isinstance(config, dict):
            errors.append("Deve essere un dizionario")
            return errors

        # Valida theme
        if 'theme' in config:
            theme_errors = self._validate_theme(config['theme'])
            errors.extend([f"theme: {error}" for error in theme_errors])

        # Valida language
        if 'language' in config:
            lang_errors = self._validate_language(config['language'])
            errors.extend([f"language: {error}" for error in lang_errors])

        # Valida items per page
        if 'items_per_page' in config:
            page_errors = self._validate_items_per_page(config['items_per_page'])
            errors.extend([f"items_per_page: {error}" for error in page_errors])

        # Valida max file size
        if 'max_file_size_mb' in config:
            size_errors = self._validate_max_file_size(config['max_file_size_mb'])
            errors.extend([f"max_file_size_mb: {error}" for error in size_errors])

        return errors

    def _validate_logging_config(self, config: Dict[str, Any]) -> List[str]:
        """Valida configurazione logging."""
        errors = []

        if not isinstance(config, dict):
            errors.append("Deve essere un dizionario")
            return errors

        # Valida level
        if 'level' in config:
            level_errors = self._validate_log_level(config['level'])
            errors.extend([f"level: {error}" for error in level_errors])

        # Valida max file size
        if 'max_file_size_mb' in config:
            size_errors = self._validate_log_file_size(config['max_file_size_mb'])
            errors.extend([f"max_file_size_mb: {error}" for error in size_errors])

        return errors

    def _validate_security_config(self, config: Dict[str, Any]) -> List[str]:
        """Valida configurazione sicurezza."""
        errors = []

        if not isinstance(config, dict):
            errors.append("Deve essere un dizionario")
            return errors

        # Valida secret key
        if 'secret_key' in config:
            key_errors = self._validate_secret_key(config['secret_key'])
            errors.extend([f"secret_key: {error}" for error in key_errors])

        # Valida token expiration
        if 'token_expiration_hours' in config:
            exp_errors = self._validate_token_expiration(config['token_expiration_hours'])
            errors.extend([f"token_expiration_hours: {error}" for error in exp_errors])

        # Valida password min length
        if 'password_min_length' in config:
            pwd_errors = self._validate_password_min_length(config['password_min_length'])
            errors.extend([f"password_min_length: {error}" for error in pwd_errors])

        return errors

    def _validate_performance_config(self, config: Dict[str, Any]) -> List[str]:
        """Valida configurazione performance."""
        errors = []

        if not isinstance(config, dict):
            errors.append("Deve essere un dizionario")
            return errors

        # Valida max workers
        if 'max_workers' in config:
            worker_errors = self._validate_max_workers(config['max_workers'])
            errors.extend([f"max_workers: {error}" for error in worker_errors])

        # Valida batch size
        if 'batch_size' in config:
            batch_errors = self._validate_batch_size(config['batch_size'])
            errors.extend([f"batch_size: {error}" for error in batch_errors])

        # Valida cache TTL
        if 'cache_ttl_seconds' in config:
            ttl_errors = self._validate_cache_ttl(config['cache_ttl_seconds'])
            errors.extend([f"cache_ttl_seconds: {error}" for error in ttl_errors])

        return errors

    def _validate_database_url(self, url: str) -> List[str]:
        """Valida URL database."""
        errors = []

        if not isinstance(url, str):
            errors.append("Deve essere una stringa")
            return errors

        if not url.strip():
            errors.append("Non può essere vuoto")
            return errors

        # Supporta SQLite, PostgreSQL, MySQL
        valid_schemes = ['sqlite', 'postgresql', 'mysql']
        parsed = urlparse(url)

        if parsed.scheme not in valid_schemes:
            errors.append(f"Schema non supportato. Usa: {', '.join(valid_schemes)}")

        return errors

    def _validate_pool_size(self, value: Any) -> List[str]:
        """Valida dimensione pool connessioni."""
        errors = []

        if not isinstance(value, int):
            errors.append("Deve essere un intero")
            return errors

        if value < 1:
            errors.append("Deve essere almeno 1")

        if value > 100:
            errors.append("Non dovrebbe essere maggiore di 100")

        return errors

    def _validate_timeout(self, value: Any) -> List[str]:
        """Valida timeout database."""
        errors = []

        if not isinstance(value, int):
            errors.append("Deve essere un intero")
            return errors

        if value < 1:
            errors.append("Deve essere almeno 1 secondo")

        if value > 300:
            errors.append("Non dovrebbe essere maggiore di 300 secondi")

        return errors

    def _validate_retry_attempts(self, value: Any) -> List[str]:
        """Valida numero tentativi retry."""
        errors = []

        if not isinstance(value, int):
            errors.append("Deve essere un intero")
            return errors

        if value < 0:
            errors.append("Non può essere negativo")

        if value > 10:
            errors.append("Non dovrebbe essere maggiore di 10")

        return errors

    def _validate_model_name(self, value: Any) -> List[str]:
        """Valida nome modello AI."""
        errors = []

        if not isinstance(value, str):
            errors.append("Deve essere una stringa")
            return errors

        if not value.strip():
            errors.append("Non può essere vuoto")

        # Pattern nomi modelli comuni
        valid_pattern = r'^[a-zA-Z0-9_-]+$'
        if not re.match(valid_pattern, value):
            errors.append("Può contenere solo lettere, numeri, _ e -")

        return errors

    def _validate_temperature(self, value: Any) -> List[str]:
        """Valida temperatura AI."""
        errors = []

        if not isinstance(value, (int, float)):
            errors.append("Deve essere un numero")
            return errors

        if value < 0.0:
            errors.append("Non può essere negativo")

        if value > 2.0:
            errors.append("Non dovrebbe essere maggiore di 2.0")

        return errors

    def _validate_max_tokens(self, value: Any) -> List[str]:
        """Valida numero massimo token."""
        errors = []

        if not isinstance(value, int):
            errors.append("Deve essere un intero")
            return errors

        if value < 1:
            errors.append("Deve essere almeno 1")

        if value > 10000:
            errors.append("Non dovrebbe essere maggiore di 10000")

        return errors

    def _validate_ai_base_url(self, value: Any) -> List[str]:
        """Valida base URL AI service."""
        errors = []

        if not isinstance(value, str):
            errors.append("Deve essere una stringa")
            return errors

        if not value.strip():
            errors.append("Non può essere vuoto")
            return errors

        try:
            parsed = urlparse(value)
            if not parsed.scheme or not parsed.netloc:
                errors.append("URL non valido")
        except Exception:
            errors.append("URL non valido")

        return errors

    def _validate_ai_timeout(self, value: Any) -> List[str]:
        """Valida timeout AI requests."""
        errors = []

        if not isinstance(value, int):
            errors.append("Deve essere un intero")
            return errors

        if value < 1:
            errors.append("Deve essere almeno 1 secondo")

        if value > 300:
            errors.append("Non dovrebbe essere maggiore di 300 secondi")

        return errors

    def _validate_theme(self, value: Any) -> List[str]:
        """Valida tema UI."""
        errors = []

        if not isinstance(value, str):
            errors.append("Deve essere una stringa")
            return errors

        valid_themes = ['light', 'dark', 'auto']
        if value not in valid_themes:
            errors.append(f"Deve essere uno di: {', '.join(valid_themes)}")

        return errors

    def _validate_language(self, value: Any) -> List[str]:
        """Valida lingua UI."""
        errors = []

        if not isinstance(value, str):
            errors.append("Deve essere una stringa")
            return errors

        # Lista lingue supportate (può essere estesa)
        valid_languages = ['it', 'en', 'es', 'fr', 'de']
        if value not in valid_languages:
            errors.append(f"Lingua non supportata. Usa: {', '.join(valid_languages)}")

        return errors

    def _validate_items_per_page(self, value: Any) -> List[str]:
        """Valida elementi per pagina."""
        errors = []

        if not isinstance(value, int):
            errors.append("Deve essere un intero")
            return errors

        if value < 1:
            errors.append("Deve essere almeno 1")

        if value > 1000:
            errors.append("Non dovrebbe essere maggiore di 1000")

        return errors

    def _validate_max_file_size(self, value: Any) -> List[str]:
        """Valida dimensione massima file."""
        errors = []

        if not isinstance(value, int):
            errors.append("Deve essere un intero")
            return errors

        if value < 1:
            errors.append("Deve essere almeno 1 MB")

        if value > 1000:
            errors.append("Non dovrebbe essere maggiore di 1000 MB")

        return errors

    def _validate_log_level(self, value: Any) -> List[str]:
        """Valida livello logging."""
        errors = []

        if not isinstance(value, str):
            errors.append("Deve essere una stringa")
            return errors

        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if value.upper() not in valid_levels:
            errors.append(f"Deve essere uno di: {', '.join(valid_levels)}")

        return errors

    def _validate_log_file_size(self, value: Any) -> List[str]:
        """Valida dimensione massima file log."""
        errors = []

        if not isinstance(value, int):
            errors.append("Deve essere un intero")
            return errors

        if value < 1:
            errors.append("Deve essere almeno 1 MB")

        if value > 1000:
            errors.append("Non dovrebbe essere maggiore di 1000 MB")

        return errors

    def _validate_secret_key(self, value: Any) -> List[str]:
        """Valida secret key sicurezza."""
        errors = []

        if not isinstance(value, str):
            errors.append("Deve essere una stringa")
            return errors

        if len(value) < 32:
            errors.append(f"Dovrebbe essere almeno 32 caratteri per sicurezza (attuale: {len(value)})")

        if len(value) > 256:
            errors.append("Non dovrebbe essere maggiore di 256 caratteri")

        return errors

    def _validate_token_expiration(self, value: Any) -> List[str]:
        """Valida scadenza token."""
        errors = []

        if not isinstance(value, int):
            errors.append("Deve essere un intero")
            return errors

        if value < 1:
            errors.append("Deve essere almeno 1 ora")

        if value > 168:
            errors.append("Non dovrebbe essere maggiore di 168 ore (1 settimana)")

        return errors

    def _validate_password_min_length(self, value: Any) -> List[str]:
        """Valida lunghezza minima password."""
        errors = []

        if not isinstance(value, int):
            errors.append("Deve essere un intero")
            return errors

        if value < 6:
            errors.append("Dovrebbe essere almeno 6 caratteri per sicurezza")

        if value > 50:
            errors.append("Non dovrebbe essere maggiore di 50 caratteri")

        return errors

    def _validate_max_workers(self, value: Any) -> List[str]:
        """Valida numero massimo worker."""
        errors = []

        if not isinstance(value, int):
            errors.append("Deve essere un intero")
            return errors

        if value < 1:
            errors.append("Deve essere almeno 1")

        if value > 32:
            errors.append("Non dovrebbe essere maggiore di 32")

        return errors

    def _validate_batch_size(self, value: Any) -> List[str]:
        """Valida dimensione batch."""
        errors = []

        if not isinstance(value, int):
            errors.append("Deve essere un intero")
            return errors

        if value < 1:
            errors.append("Deve essere almeno 1")

        if value > 1000:
            errors.append("Non dovrebbe essere maggiore di 1000")

        return errors

    def _validate_cache_ttl(self, value: Any) -> List[str]:
        """Valida TTL cache."""
        errors = []

        if not isinstance(value, int):
            errors.append("Deve essere un intero")
            return errors

        if value < 0:
            errors.append("Non può essere negativo")

        if value > 86400:
            errors.append("Non dovrebbe essere maggiore di 86400 secondi (24 ore)")

        return errors

    def _validate_data_dir(self, value: Any) -> List[str]:
        """Valida directory dati."""
        errors = []

        if not isinstance(value, str):
            errors.append("Deve essere una stringa")
            return errors

        if not value.strip():
            errors.append("Non può essere vuoto")

        # Controlla caratteri pericolosi
        dangerous_chars = ['<', '>', '|', '"', '*', '?']
        for char in dangerous_chars:
            if char in value:
                errors.append(f"Non può contenere caratteri speciali: {char}")

        return errors

    def _validate_upload_dir(self, value: Any) -> List[str]:
        """Valida directory upload."""
        return self._validate_data_dir(value)

    def _validate_temp_dir(self, value: Any) -> List[str]:
        """Valida directory temporanea."""
        return self._validate_data_dir(value)

    def _validate_backup_dir(self, value: Any) -> List[str]:
        """Valida directory backup."""
        return self._validate_data_dir(value)

    def _validate_feature_flag(self, value: Any) -> List[str]:
        """Valida feature flag."""
        errors = []

        if not isinstance(value, bool):
            errors.append("Deve essere un booleano")

        return errors

    def get_validation_summary(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Recupera summary validazione configurazione.

        Args:
            config: Configurazione da validare

        Returns:
            Dizionario con summary validazione
        """
        errors = self.validate_config(config)

        return {
            'is_valid': len(errors) == 0,
            'total_errors': len(errors),
            'errors': errors,
            'validation_timestamp': None,  # Potrebbe essere aggiunto
        }

    def validate_field(self, field_name: str, value: Any) -> List[str]:
        """Valida singolo campo configurazione.

        Args:
            field_name: Nome campo da validare
            value: Valore da validare

        Returns:
            Lista errori validazione
        """
        if field_name in self.validation_rules:
            return self.validation_rules[field_name](value)

        # Valida campi speciali
        if field_name == 'data_dir':
            return self._validate_data_dir(value)
        elif field_name == 'upload_dir':
            return self._validate_upload_dir(value)
        elif field_name == 'temp_dir':
            return self._validate_temp_dir(value)
        elif field_name == 'backup_dir':
            return self._validate_backup_dir(value)
        elif field_name.startswith('enable_'):
            return self._validate_feature_flag(value)

        return [f"Campo sconosciuto: {field_name}"]

    def suggest_fixes(self, errors: List[str]) -> Dict[str, str]:
        """Suggerisce correzioni per errori configurazione.

        Args:
            errors: Lista errori da correggere

        Returns:
            Dizionario suggerimenti correzione
        """
        suggestions = {}

        for error in errors:
            if 'database url' in error.lower():
                suggestions[error] = "Usa formato: sqlite:///path/to/db.sqlite"
            elif 'temperature' in error.lower():
                suggestions[error] = "Usa valore tra 0.0 e 2.0"
            elif 'max_tokens' in error.lower():
                suggestions[error] = "Usa valore tra 1 e 10000"
            elif 'pool_size' in error.lower():
                suggestions[error] = "Usa valore tra 1 e 100"
            elif 'theme' in error.lower():
                suggestions[error] = "Usa: light, dark, o auto"
            elif 'language' in error.lower():
                suggestions[error] = "Usa codice lingua ISO: it, en, es, fr, de"

        return suggestions
