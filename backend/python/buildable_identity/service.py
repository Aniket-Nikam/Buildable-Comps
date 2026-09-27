import hmac
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from buildable_core.config import Settings
from buildable_core.errors import AppError
from buildable_core.events import DomainEvent, EventPublisher, InProcessEventPublisher
from buildable_core.security import (
    PasswordService,
    TokenDecodeError,
    TokenService,
    hash_token,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .models import OneTimeToken, RefreshSession, User
from .notifications import IdentityNotification, IdentityNotifier, InMemoryIdentityNotifier
from .repositories import OneTimeTokenRepository, RefreshSessionRepository, UserRepository

DUMMY_PASSWORD_HASH = PasswordService().hash("not-a-real-password-value")


@dataclass(frozen=True, slots=True)
class AuthResult:
    user: User
    access_token: str
    refresh_token: str
    expires_in: int
    session_id: str


class AuthenticationService:
    def __init__(
        self,
        session: Session,
        settings: Settings,
        event_publisher: EventPublisher | None = None,
        notifier: IdentityNotifier | None = None,
    ) -> None:
        self.session = session
        self.settings = settings
        self.users = UserRepository(session)
        self.refresh_sessions = RefreshSessionRepository(session)
        self.one_time_tokens = OneTimeTokenRepository(session)
        self.passwords = PasswordService()
        self.tokens = TokenService(settings)
        self.events = event_publisher or InProcessEventPublisher()
        self.notifier = notifier or InMemoryIdentityNotifier()

    def register(self, email: str, password: str, display_name: str) -> AuthResult:
        normalized_email = email.strip().lower()
        if self.users.get_by_email(normalized_email):
            raise AppError(
                "email_unavailable",
                "An account with this email already exists.",
                status_code=409,
            )
        user = User(
            email=normalized_email,
            password_hash=self.passwords.hash(password),
            display_name=display_name.strip(),
        )
        try:
            self.users.add(user)
            verification_token, verification_expiry = self._issue_one_time_token(
                user, "email_verification", self.settings.email_verification_ttl_hours
            )
            result = self._issue_session(user)
            self.session.commit()
        except IntegrityError as error:
            self.session.rollback()
            raise AppError(
                "email_unavailable",
                "An account with this email already exists.",
                status_code=409,
            ) from error
        self.events.publish(DomainEvent.create("UserRegistered", {"userId": user.id}))
        self.notifier.send(
            IdentityNotification(
                kind="email_verification",
                email=user.email,
                token=verification_token,
                expires_at=verification_expiry,
            )
        )
        return result

    def login(self, email: str, password: str) -> AuthResult:
        user = self.users.get_by_email(email.strip().lower())
        password_hash = user.password_hash if user else DUMMY_PASSWORD_HASH
        password_is_valid = self.passwords.verify(password, password_hash)
        if user is None or not password_is_valid:
            raise AppError(
                "invalid_credentials", "Email or password is incorrect.", status_code=401
            )
        if user.status != "active":
            raise AppError("account_unavailable", "This account is not active.", status_code=403)
        if self.settings.require_verified_email and not user.email_verified:
            raise AppError(
                "email_verification_required",
                "Verify your email before signing in.",
                status_code=403,
            )
        result = self._issue_session(user)
        self.session.commit()
        self.events.publish(DomainEvent.create("SessionStarted", {"userId": user.id}))
        return result

    def refresh(self, refresh_token: str) -> AuthResult:
        try:
            payload = self.tokens.decode(refresh_token, "refresh")
        except TokenDecodeError as error:
            raise self._invalid_session() from error
        if not payload.session_id:
            raise self._invalid_session()
        current = self.refresh_sessions.get_for_update(payload.session_id)
        now = datetime.now(UTC)
        if current is None or not hmac.compare_digest(
            current.token_hash, hash_token(refresh_token)
        ):
            raise self._invalid_session()
        if current.revoked_at is not None:
            if current.replaced_by_id is not None:
                current.reuse_detected_at = now
                self.refresh_sessions.revoke_family(current.family_id, now)
                self.session.commit()
                self.events.publish(
                    DomainEvent.create(
                        "RefreshTokenReuseDetected",
                        {"userId": current.user_id, "familyId": current.family_id},
                    )
                )
            raise self._invalid_session()
        if self._as_utc(current.expires_at) <= now:
            raise self._invalid_session()
        user = self.users.get_by_id(payload.subject)
        if user is None or user.id != current.user_id or user.status != "active":
            raise self._invalid_session()
        if self.settings.require_verified_email and not user.email_verified:
            raise AppError(
                "email_verification_required",
                "Verify your email before continuing.",
                status_code=403,
            )
        self.refresh_sessions.revoke(current, now)
        result = self._issue_session(user, family_id=current.family_id, parent_id=current.id)
        current.replaced_by_id = result.session_id
        self.session.commit()
        return result

    def logout(self, refresh_token: str | None) -> None:
        if not refresh_token:
            return
        try:
            payload = self.tokens.decode(refresh_token, "refresh")
        except TokenDecodeError:
            return
        if not payload.session_id:
            return
        current = self.refresh_sessions.get_for_update(payload.session_id)
        if current and hmac.compare_digest(current.token_hash, hash_token(refresh_token)):
            self.refresh_sessions.revoke(current, datetime.now(UTC))
            self.session.commit()
            self.events.publish(DomainEvent.create("SessionRevoked", {"userId": current.user_id}))

    def request_email_verification(self, email: str) -> None:
        user = self.users.get_by_email(email.strip().lower())
        if user is None or user.status != "active" or user.email_verified:
            return
        token, expires_at = self._issue_one_time_token(
            user, "email_verification", self.settings.email_verification_ttl_hours
        )
        self.session.commit()
        self.notifier.send(
            IdentityNotification(
                kind="email_verification",
                email=user.email,
                token=token,
                expires_at=expires_at,
            )
        )

    def verify_email(self, token: str) -> User:
        now = datetime.now(UTC)
        stored_token = self.one_time_tokens.get_active_for_update(
            hash_token(token), "email_verification", now
        )
        if stored_token is None:
            raise self._invalid_one_time_token()
        user = self.users.get_by_id(stored_token.user_id)
        if user is None or user.status != "active":
            raise self._invalid_one_time_token()
        user.email_verified_at = now
        stored_token.used_at = now
        self.one_time_tokens.invalidate_active(user.id, "email_verification", now)
        self.session.commit()
        self.events.publish(DomainEvent.create("EmailVerified", {"userId": user.id}))
        return user

    def request_password_reset(self, email: str) -> None:
        user = self.users.get_by_email(email.strip().lower())
        if user is None or user.status != "active":
            return
        token, expires_at = self._issue_one_time_token(
            user, "password_reset", self.settings.password_reset_ttl_hours
        )
        self.session.commit()
        self.notifier.send(
            IdentityNotification(
                kind="password_reset",
                email=user.email,
                token=token,
                expires_at=expires_at,
            )
        )

    def reset_password(self, token: str, new_password: str) -> None:
        now = datetime.now(UTC)
        stored_token = self.one_time_tokens.get_active_for_update(
            hash_token(token), "password_reset", now
        )
        if stored_token is None:
            raise self._invalid_one_time_token()
        user = self.users.get_by_id(stored_token.user_id)
        if user is None or user.status != "active":
            raise self._invalid_one_time_token()
        user.password_hash = self.passwords.hash(new_password)
        user.password_changed_at = now
        user.auth_version += 1
        stored_token.used_at = now
        self.one_time_tokens.invalidate_active(user.id, "password_reset", now)
        self.refresh_sessions.revoke_all_for_user(user.id, now)
        self.session.commit()
        self.events.publish(DomainEvent.create("PasswordReset", {"userId": user.id}))

    def _issue_session(
        self,
        user: User,
        *,
        family_id: str | None = None,
        parent_id: str | None = None,
    ) -> AuthResult:
        session_id = str(uuid.uuid4())
        resolved_family_id = family_id or session_id
        refresh_token = self.tokens.create_refresh(user.id, session_id)
        self.refresh_sessions.add(
            RefreshSession(
                id=session_id,
                user_id=user.id,
                token_hash=hash_token(refresh_token),
                family_id=resolved_family_id,
                parent_id=parent_id,
                expires_at=datetime.now(UTC) + timedelta(days=self.settings.refresh_token_ttl_days),
            )
        )
        return AuthResult(
            user=user,
            access_token=self.tokens.create_access(user.id, user.auth_version),
            refresh_token=refresh_token,
            expires_in=self.settings.access_token_ttl_minutes * 60,
            session_id=session_id,
        )

    def _issue_one_time_token(
        self, user: User, purpose: str, ttl_hours: int
    ) -> tuple[str, datetime]:
        now = datetime.now(UTC)
        self.one_time_tokens.invalidate_active(user.id, purpose, now)
        token = secrets.token_urlsafe(32)
        expires_at = now + timedelta(hours=ttl_hours)
        self.one_time_tokens.add(
            OneTimeToken(
                user_id=user.id,
                purpose=purpose,
                token_hash=hash_token(token),
                expires_at=expires_at,
            )
        )
        return token, expires_at

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)

    @staticmethod
    def _invalid_session() -> AppError:
        return AppError(
            "invalid_session", "Your session is invalid or has expired.", status_code=401
        )

    @staticmethod
    def _invalid_one_time_token() -> AppError:
        return AppError("invalid_token", "This link is invalid or has expired.", status_code=400)


class UserProfileService:
    def __init__(
        self,
        session: Session,
        event_publisher: EventPublisher | None = None,
    ) -> None:
        self.session = session
        self.events = event_publisher or InProcessEventPublisher()

    def update_display_name(self, user: User, display_name: str) -> User:
        user.display_name = display_name.strip()
        self.session.commit()
        self.events.publish(DomainEvent.create("UserUpdated", {"userId": user.id}))
        return user
