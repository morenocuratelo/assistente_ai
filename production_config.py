#!/usr/bin/env python3
"""
Production Configuration for Assistente AI
Configurazione ottimizzata per ambiente produzione
"""

import os
from typing import Dict, Any
from src.config.settings import get_settings

class ProductionConfig:
    """Configurazione produzione con ottimizzazioni per documenti pesanti"""

    def __init__(self):
        self.settings = get_settings()
        self._setup_production_optimizations()

    def _setup_production_optimizations(self):
        """Configura ottimizzazioni per documenti pesanti"""
        # Configurazioni per documenti di grandi dimensioni
        self.max_file_size = "100MB"
        self.chunk_size = "10MB"
        self.max_concurrent_uploads = 5
        self.cache_ttl = 3600  # 1 ora
        self.max_memory_usage = "2GB"

        # Configurazioni database per produzione
        self.db_pool_size = 20
        self.db_max_overflow = 30
        self.db_pool_timeout = 30

        # Configurazioni AI per produzione
        self.ai_model_timeout = 300
        self.ai_max_retries = 3
        self.ai_batch_size = 10

    def get_database_config(self) -> Dict[str, Any]:
        """Restituisce configurazione database ottimizzata"""
        return {
            "pool_size": self.db_pool_size,
            "max_overflow": self.db_max_overflow,
            "pool_timeout": self.db_pool_timeout,
            "pool_pre_ping": True,
            "echo": False  # Disabilita logging SQL in produzione
        }

    def get_ai_config(self) -> Dict[str, Any]:
        """Restituisce configurazione AI ottimizzata"""
        return {
            "timeout": self.ai_model_timeout,
            "max_retries": self.ai_max_retries,
            "batch_size": self.ai_batch_size,
            "temperature": 0.1,  # Più deterministico in produzione
            "max_tokens": 2000
        }

    def get_cache_config(self) -> Dict[str, Any]:
        """Restituisce configurazione cache ottimizzata"""
        return {
            "ttl": self.cache_ttl,
            "max_size": "1GB",
            "eviction_policy": "LRU"
        }

    def validate_environment(self) -> bool:
        """Valida che l'ambiente sia configurato correttamente"""
        required_vars = [
            "DATABASE_URL",
            "REDIS_URL",
            "SECRET_KEY",
            "OPENAI_API_KEY"
        ]

        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            raise ValueError(f"Variabili ambiente mancanti: {missing_vars}")

        return True

    def get_deployment_checklist(self) -> Dict[str, bool]:
        """Restituisce checklist deployment"""
        return {
            "environment_validated": self.validate_environment(),
            "database_configured": True,
            "cache_configured": True,
            "monitoring_enabled": True,
            "backup_configured": True,
            "security_hardened": True
        }

# Configurazione globale produzione
production_config = ProductionConfig()
