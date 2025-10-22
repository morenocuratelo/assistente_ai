"""Minimal metrics/monitoring utilities for tests."""
from typing import Dict, Any
import time


class PerformanceMonitor:
    def __init__(self):
        self.records = []
    def measure(self, name: str):
        """Decorator factory to measure function execution and store records."""
        def decorator(fn):
            def wrapper(*args, **kwargs):
                start = time.time()
                result = fn(*args, **kwargs)
                elapsed = time.time() - start
                self.records.append((name or fn.__name__, elapsed))
                return result
            return wrapper
        return decorator

    def get_performance_summary(self, hours: int = 1) -> Dict[str, Any]:
        return {"total_operations": len(self.records)}

    def get_timing(self, name: str):
        vals = [t for n, t in self.records if n == name]
        if not vals:
            return None
        return {
            'count': len(vals),
            'avg_ms': sum(vals) / len(vals) * 1000
        }


class MetricsCollector:
    def __init__(self):
        self.data = {}
    def record_counter(self, key: str, value: int = 1, tags: Dict[str, Any] = None) -> None:
        """Record a counter metric."""
        self.data.setdefault(key, 0)
        self.data[key] += value

    def record_gauge(self, key: str, value: float, tags: Dict[str, Any] = None) -> None:
        self.data[key] = value

    def record_histogram(self, key: str, value: float, tags: Dict[str, Any] = None) -> None:
        self.data.setdefault(f"hist_{key}", [])
        self.data[f"hist_{key}"].append(value)

    def get_metric(self, key: str):
        return self.data.get(key)

    def get_counter(self, key: str) -> int:
        return int(self.data.get(key, 0))

    def get_gauge(self, key: str) -> float:
        return float(self.data.get(key, 0.0))

    def get_histogram_stats(self, key: str) -> Dict[str, Any]:
        """Get histogram statistics for a key."""
        hist_key = f"hist_{key}"
        values = self.data.get(hist_key, [])

        if not values:
            return {'count': 0, 'sum': 0.0, 'avg': 0.0, 'min': 0.0, 'max': 0.0}

        return {
            'count': len(values),
            'sum': sum(values),
            'avg': sum(values) / len(values),
            'min': min(values),
            'max': max(values)
        }
