"""
In-process and REST domain event bus.
"""

from collections.abc import Callable
from typing import Any
from src.schemas.workflow import DomainEventPayload

EventHandler = Callable[[DomainEventPayload], None]


class EventBus:
    """Pub/Sub event dispatcher for cross-service events."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler]] = {}
        self._history: list[DomainEventPayload] = []

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def publish(self, event: DomainEventPayload) -> None:
        self._history.append(event)
        handlers = self._subscribers.get(event.event_type, [])
        for h in handlers:
            try:
                h(event)
            except Exception:
                pass

    def get_recent_events(self, limit: int = 50) -> list[DomainEventPayload]:
        return list(reversed(self._history[-limit:]))


GLOBAL_BUS = EventBus()
