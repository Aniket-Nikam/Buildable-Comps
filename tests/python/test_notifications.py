from datetime import UTC, datetime, timedelta
from email.message import EmailMessage

from buildable_identity.notifications import IdentityNotification, SmtpIdentityNotifier


class FakeSmtpConnection:
    def __init__(self) -> None:
        self.started_tls = False
        self.credentials: tuple[str, str] | None = None
        self.message: EmailMessage | None = None
        self.closed = False

    def starttls(self) -> tuple[int, bytes]:
        self.started_tls = True
        return (220, b"ready")

    def login(self, user: str, password: str) -> tuple[int, bytes]:
        self.credentials = (user, password)
        return (235, b"ok")

    def send_message(self, msg: EmailMessage) -> dict[str, tuple[int, bytes]]:
        self.message = msg
        return {}

    def quit(self) -> tuple[int, bytes]:
        self.closed = True
        return (221, b"bye")

    def close(self) -> None:
        self.closed = True


def test_smtp_notifier_hands_a_safe_recovery_link_to_provider() -> None:
    connection = FakeSmtpConnection()
    notifier = SmtpIdentityNotifier(
        host="smtp.example.com",
        port=587,
        sender="security@example.com",
        public_web_url="https://app.example.com/",
        username="smtp-user",
        password="smtp-password",
    )
    notifier._connect = lambda: connection  # type: ignore[method-assign]

    notifier.send(
        IdentityNotification(
            kind="password_reset",
            email="user@example.com",
            token="opaque token/value",
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
    )

    assert connection.started_tls is True
    assert connection.credentials == ("smtp-user", "smtp-password")
    assert connection.message is not None
    assert connection.message["Subject"] == "Reset your password"
    assert connection.message["To"] == "user@example.com"
    body = connection.message.get_body(preferencelist=("plain",)).get_content()
    assert "https://app.example.com/reset-password?token=opaque+token%2Fvalue" in body
    assert connection.closed is True
