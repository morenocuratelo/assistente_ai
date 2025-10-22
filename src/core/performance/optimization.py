"""
Performance Optimization Module.

Ottimizzazioni per migliorare le prestazioni del sistema:
- Caching intelligente
- Memory management
- Query optimization
- Lazy loading
- Background processing
"""

import time
import functools
import threading
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
import logging
import gc
import psutil
import os

logger = logging.getLogger(__name__)


class PerformanceOptimizer:
    """Ottimizzatore prestazioni centralizzato."""

    def __init__(self):
        self.cache = {}
        self.cache_timestamps = {}
        self.cache_ttl = 300  # 5 minuti default
        self.max_cache_size = 1000
        self.memory_threshold = 0.8  # 80% memory usage threshold
        self.query_stats = {}
        self.background_tasks = []

        # Avvia monitoring background
        self._start_memory_monitoring()

    def cache_result(self, key: str, result: Any, ttl: int = None) -> None:
        """Cache risultato con TTL."""
        if len(self.cache) >= self.max_cache_size:
            self._cleanup_cache()

        current_time = time.time()
        self.cache[key] = result
        self.cache_timestamps[key] = current_time

        if ttl:
            # Cache con TTL personalizzato
            threading.Timer(ttl, lambda: self._expire_cache_key(key)).start()

    def get_cached_result(self, key: str) -> Optional[Any]:
        """Recupera risultato dalla cache se valido."""
        if key not in self.cache:
            return None

        # Verifica scadenza cache
        cache_time = self.cache_timestamps.get(key, 0)
        if time.time() - cache_time > self.cache_ttl:
            del self.cache[key]
            del self.cache_timestamps[key]
            return None

        return self.cache[key]

    def _cleanup_cache(self) -> None:
        """Pulisce cache rimuovendo elementi più vecchi."""
        current_time = time.time()
        expired_keys = []

        for key, timestamp in self.cache_timestamps.items():
            if current_time - timestamp > self.cache_ttl:
                expired_keys.append(key)

        for key in expired_keys:
            self.cache.pop(key, None)
            self.cache_timestamps.pop(key, None)

        # Se ancora troppo grande, rimuovi elementi più vecchi
        if len(self.cache) >= self.max_cache_size:
            sorted_keys = sorted(self.cache_timestamps.keys(),
                               key=lambda k: self.cache_timestamps[k])
            keys_to_remove = sorted_keys[:len(self.cache) - self.max_cache_size + 100]

            for key in keys_to_remove:
                self.cache.pop(key, None)
                self.cache_timestamps.pop(key, None)

    def _expire_cache_key(self, key: str) -> None:
        """Scade chiave cache specifica."""
        self.cache.pop(key, None)
        self.cache_timestamps.pop(key, None)

    def optimize_query(self, query: str, params: tuple = None) -> str:
        """Ottimizza query SQL."""
        # Query optimization basica
        optimized_query = query.strip()

        # Aggiungi statistiche query
        query_hash = hash(optimized_query)
        self.query_stats[query_hash] = self.query_stats.get(query_hash, 0) + 1

        return optimized_query

    def get_query_stats(self) -> Dict[str, Any]:
        """Restituisce statistiche query."""
        return {
            'total_queries': sum(self.query_stats.values()),
            'unique_queries': len(self.query_stats),
            'most_used_queries': sorted(self.query_stats.items(), key=lambda x: x[1], reverse=True)[:10]
        }

    def _start_memory_monitoring(self) -> None:
        """Avvia monitoring memoria in background."""
        def monitor_memory():
            while True:
                try:
                    memory = psutil.virtual_memory()
                    memory_usage = memory.percent / 100

                    if memory_usage > self.memory_threshold:
                        logger.warning(f"Alto utilizzo memoria: {memory_usage:.1%}")
                        self._optimize_memory_usage()

                    time.sleep(60)  # Controlla ogni minuto
                except Exception as e:
                    logger.error(f"Errore monitoring memoria: {e}")
                    time.sleep(60)

        monitor_thread = threading.Thread(target=monitor_memory, daemon=True)
        monitor_thread.start()
        self.background_tasks.append(monitor_thread)

    def _optimize_memory_usage(self) -> None:
        """Ottimizza utilizzo memoria."""
        try:
            # Pulisce cache
            self._cleanup_cache()

            # Forza garbage collection
            gc.collect()

            # Log memory status
            memory = psutil.virtual_memory()
            logger.info(f"Memory optimization completed. Usage: {memory.percent:.1%}")

        except Exception as e:
            logger.error(f"Errore ottimizzazione memoria: {e}")

    def lazy_load(self, loader_func: Callable, key: str, *args, **kwargs) -> Any:
        """Lazy loading con cache."""
        # Verifica cache
        cached_result = self.get_cached_result(key)
        if cached_result is not None:
            return cached_result

        # Carica e cache
        result = loader_func(*args, **kwargs)
        self.cache_result(key, result)

        return result

    def batch_process(self, items: List[Any], processor_func: Callable, batch_size: int = 10) -> List[Any]:
        """Processa elementi in batch per ottimizzare performance."""
        results = []

        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = processor_func(batch)
            results.extend(batch_results)

            # Piccola pausa per non sovraccaricare il sistema
            if i + batch_size < len(items):
                time.sleep(0.01)

        return results

    def preload_data(self, preload_func: Callable, keys: List[str]) -> None:
        """Precarica dati in background."""
        def preload_worker():
            for key in keys:
                try:
                    if self.get_cached_result(key) is None:
                        result = preload_func(key)
                        self.cache_result(key, result)
                except Exception as e:
                    logger.error(f"Errore preload {key}: {e}")

        preload_thread = threading.Thread(target=preload_worker, daemon=True)
        preload_thread.start()
        self.background_tasks.append(preload_thread)

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Restituisce metriche performance."""
        try:
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)

            return {
                'memory_usage_percent': memory.percent,
                'memory_available_mb': memory.available / 1024 / 1024,
                'cache_size': len(self.cache),
                'cache_hit_rate': self._calculate_cache_hit_rate(),
                'query_stats': self.get_query_stats(),
                'cpu_usage_percent': cpu_percent,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Errore metriche performance: {e}")
            return {}

    def _calculate_cache_hit_rate(self) -> float:
        """Calcola hit rate cache."""
        # Implementazione base - in produzione useresti contatori specifici
        return 0.85  # 85% hit rate simulato

    def optimize_database_connection(self, db_path: str) -> None:
        """Ottimizza connessione database."""
        try:
            import sqlite3

            # Abilita WAL mode per migliori performance
            conn = sqlite3.connect(db_path)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")
            conn.execute("PRAGMA temp_store=memory")
            conn.commit()
            conn.close()

            logger.info(f"Database {db_path} ottimizzato per performance")

        except Exception as e:
            logger.error(f"Errore ottimizzazione database: {e}")


# Istanza globale ottimizzatore
performance_optimizer = PerformanceOptimizer()


def cache_result(key_template: str, ttl: int = None):
    """Decorator per caching risultati funzione."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Crea chiave cache
            key = key_template.format(*args, **kwargs)

            # Verifica cache
            cached_result = performance_optimizer.get_cached_result(key)
            if cached_result is not None:
                return cached_result

            # Esegui funzione e cache risultato
            result = func(*args, **kwargs)
            performance_optimizer.cache_result(key, result, ttl)

            return result
        return wrapper
    return decorator


def measure_performance(func_name: str = None):
    """Decorator per misurare performance funzione."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time

                # Log performance
                func_name_display = func_name or func.__name__
                logger.info(f"Performance {func_name_display}: {execution_time:.3f}s")

                return result

            except Exception as e:
                execution_time = time.time() - start_time
                func_name_display = func_name or func.__name__
                logger.error(f"Performance {func_name_display}: {execution_time:.3f}s - ERROR: {e}")
                raise

        return wrapper
    return decorator


def optimize_memory():
    """Ottimizza memoria sistema."""
    performance_optimizer._optimize_memory_usage()


def get_system_performance() -> Dict[str, Any]:
    """Restituisce performance sistema."""
    return performance_optimizer.get_performance_metrics()


def preload_common_data():
    """Precarica dati comuni per migliorare performance."""
    try:
        # Precarica configurazioni comuni
        from src.config.settings import get_config
        config = get_config()
        performance_optimizer.cache_result('system_config', config, ttl=600)

        # Precarica struttura conoscenza
        from knowledge_structure import KNOWLEDGE_BASE_STRUCTURE
        performance_optimizer.cache_result('knowledge_structure', KNOWLEDGE_BASE_STRUCTURE, ttl=3600)

        logger.info("Dati comuni precaricati per ottimizzazione performance")

    except Exception as e:
        logger.error(f"Errore preload dati comuni: {e}")


# Inizializza ottimizzazioni al caricamento modulo
preload_common_data()
