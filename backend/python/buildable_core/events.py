from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class DomainEvent:
    name: str
    payload: dict[str, Any]
    occurred_at: datetime

    @classmethod
    def create(cls, name: str, payload: dict[str, Any]) -> "DomainEvent":
        return cls(name=name, payload=payload, occurred_at=datetime.now(UTC))

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class EventPublisher(Protocol):
    def publish(self, event: DomainEvent) -> None: ...


class InProcessEventPublisher:
    """Small synchronous adapter that can be replaced by a transactional outbox."""

    def __init__(self) -> None:
        self.events: list[DomainEvent] = []

    def publish(self, event: DomainEvent) -> None:
        self.events.append(event)
