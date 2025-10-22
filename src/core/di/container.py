"""Minimal service container for dependency injection used in tests."""
from typing import Any, Dict


class ServiceContainer:
    def __init__(self):
        # store either {'name': ('singleton', instance)} or {'name': ('factory', callable)}
        self._services: Dict[str, tuple] = {}

    def register(self, name: str, svc: Any):
        # Register as singleton by default
        self._services[name] = ('singleton', svc)

    def register_singleton(self, name: str, instance: Any) -> None:
        """Register a singleton instance under `name`. Tests expect this method."""
        self._services[name] = ('singleton', instance)

    def register_factory(self, name: str, factory_callable) -> None:
        """Register a factory callable that returns a new instance when resolved."""
        self._services[name] = ('factory', factory_callable)

    def resolve(self, name: str) -> Any:
        entry = self._services.get(name)
        if not entry:
            return None
        kind, value = entry
        if kind == 'singleton':
            return value
        if kind == 'factory':
            return value()
        return value
