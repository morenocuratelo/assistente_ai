"""Simple EventBus used in unit tests for pub/sub behavior."""
from typing import Callable, Dict, List, Any


class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Any], None]]] = {}

    def subscribe(self, event_name: str, callback: Callable[[Any], None]) -> None:
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        self._subscribers[event_name].append(callback)

    def unsubscribe(self, event_name: str, callback: Callable[[Any], None]) -> None:
        if event_name in self._subscribers:
            try:
                self._subscribers[event_name].remove(callback)
            except ValueError:
                pass

    def publish(self, event_name: str, payload: Any = None) -> None:
        # If the caller passed the whole event as a dict, extract the event_type
        if isinstance(event_name, dict):
            evt = event_name
            name = evt.get('event_type') or evt.get('type')
            payload = evt
        else:
            name = event_name

        callbacks = list(self._subscribers.get(name, []))
        for cb in callbacks:
            try:
                cb(payload)
            except Exception:
                # Swallow exceptions from subscribers to not break the bus
                pass