import smtplib
from dataclasses import dataclass
from datetime import datetime
from email.message import EmailMessage
from typing import Literal, Protocol, cast
from urllib.parse import urlencode

from buildable_core.config import Settings

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


class _SmtpConnection(Protocol):
    def starttls(self) -> tuple[int, bytes]: ...

    def login(self, user: str, password: str) -> tuple[int, bytes]: ...

    def send_message(self, msg: EmailMessage) -> dict[str, tuple[int, bytes]]: ...

    def quit(self) -> tuple[int, bytes]: ...

    def close(self) -> None: ...


class SmtpIdentityNotifier:
    """Provider-backed delivery adapter that hands messages to an SMTP queue."""

    def __init__(
        self,
        *,
        host: str,
        port: int,
        sender: str,
        public_web_url: str,
        username: str | None = None,
        password: str | None = None,
        security: Literal["starttls", "tls", "none"] = "starttls",
        timeout_seconds: float = 10,
    ) -> None:
        self.host = host
        self.port = port
        self.sender = sender
        self.public_web_url = public_web_url.rstrip("/")
        self.username = username
        self.password = password
        self.security = security
        self.timeout_seconds = timeout_seconds

    def send(self, notification: IdentityNotification) -> None:
        message = self._build_message(notification)
        connection = self._connect()
        try:
            if self.security == "starttls":
                connection.starttls()
            if self.username and self.password:
                connection.login(self.username, self.password)
            refused = connection.send_message(message)
            if refused:
                raise RuntimeError("The SMTP provider refused one or more recipients")
        finally:
            try:
                connection.quit()
            except (OSError, smtplib.SMTPException):
                connection.close()

    def _connect(self) -> _SmtpConnection:
        smtp_class = smtplib.SMTP_SSL if self.security == "tls" else smtplib.SMTP
        return cast(
            _SmtpConnection,
            smtp_class(self.host, self.port, timeout=self.timeout_seconds),
        )

    def _build_message(self, notification: IdentityNotification) -> EmailMessage:
        if notification.kind == "email_verification":
            subject = "Verify your email"
            route = "/verify-email"
            action = "Verify email"
        else:
            subject = "Reset your password"
            route = "/reset-password"
            action = "Reset password"
        link = f"{self.public_web_url}{route}?{urlencode({'token': notification.token})}"
        expires_at = notification.expires_at.isoformat()
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self.sender
        message["To"] = notification.email
        message.set_content(
            f"{action}: {link}\n\nThis link expires at {expires_at}. "
            "If you did not request this, you can ignore this message."
        )
        message.add_alternative(
            "<p>Use the secure link below to continue.</p>"
            f'<p><a href="{link}">{action}</a></p>'
            f"<p>This link expires at {expires_at}.</p>"
            "<p>If you did not request this, you can ignore this message.</p>",
            subtype="html",
        )
        return message


def create_identity_notifier(settings: Settings) -> IdentityNotifier:
    if settings.identity_notifier_backend == "smtp":
        if not settings.smtp_host or not settings.smtp_from_email:
            raise ValueError("SMTP settings are incomplete")
        return SmtpIdentityNotifier(
            host=settings.smtp_host,
            port=settings.smtp_port,
            sender=settings.smtp_from_email,
            public_web_url=settings.public_web_url,
            username=settings.smtp_username,
            password=settings.smtp_password,
            security=settings.smtp_security,
            timeout_seconds=settings.smtp_timeout_seconds,
        )
    if settings.identity_notifier_backend == "injected":
        raise ValueError("IDENTITY_NOTIFIER_BACKEND=injected requires an IdentityNotifier")
    return InMemoryIdentityNotifier()
