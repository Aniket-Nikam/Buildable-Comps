from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol

NotificationKind = Literal["email_verification", "password_reset"]


@dataclass(frozen=True, slots=True)
class IdentityNotification:
    kind: NotificationKind
    email: str
    token: str
    expires_at: datetime


class IdentityNotifier(Protocol):
    """Delivery boundary for a durable email or messaging adapter."""

    def send(self, notification: IdentityNotification) -> None: ...


class InMemoryIdentityNotifier:
    """Development/test adapter. Production apps should inject a durable provider."""

    def __init__(self) -> None:
        self.outbox: list[IdentityNotification] = []

    def send(self, notification: IdentityNotification) -> None:
        self.outbox.append(notification)
