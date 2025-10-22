"""Small logging helpers used in unit tests."""
import logging
from typing import Dict, Any


def get_logger(name: str = __name__) -> logging.Logger:
    # For tests we return the module-level logger so that patching
    # 'src.core.utils.logging.logger' intercepts calls made by get_logger
    global logger
    return logger
    # Fallback behavior kept for completeness
    lg = logging.getLogger(name)
    if not lg.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        lg.addHandler(handler)
    return lg


# Expose a module-level logger for tests that patch `src.core.utils.logging.logger`
logger = logging.getLogger("archivista_core")


def log_performance(label: str):
    """Decorator factory for performance logging used in tests.

    Usage:
        @log_performance("operation")
        def fn(...):
            ...
    """
    def decorator(fn):
        def wrapper(*args, **kwargs):
            import time
            start = time.time()
            result = fn(*args, **kwargs)
            elapsed = time.time() - start
            logger.info(f"PERF {label}: {elapsed}s", extra={'duration_ms': int(elapsed * 1000)})
            return result
        return wrapper
    return decorator
