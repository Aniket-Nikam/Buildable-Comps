import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import jwt
from jwt import InvalidTokenError
from pwdlib import PasswordHash

from .config import Settings

TokenType = Literal["access", "refresh"]


class TokenDecodeError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class TokenPayload:
    subject: str
    token_type: TokenType
    token_id: str
    issued_at: datetime
    expires_at: datetime
    session_id: str | None = None
    auth_version: int = 1


class PasswordService:
    def __init__(self) -> None:
        self._hasher = PasswordHash.recommended()

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)

    def verify(self, password: str, password_hash: str) -> bool:
        return self._hasher.verify(password, password_hash)


class TokenService:
    algorithm = "HS256"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def create_access(self, user_id: str, auth_version: int = 1) -> str:
        lifetime = timedelta(minutes=self.settings.access_token_ttl_minutes)
        return self._encode(user_id, "access", lifetime, auth_version=auth_version)

    def create_refresh(self, user_id: str, session_id: str) -> str:
        return self._encode(
            user_id,
            "refresh",
            timedelta(days=self.settings.refresh_token_ttl_days),
            session_id=session_id,
        )

    def _encode(
        self,
        subject: str,
        token_type: TokenType,
        lifetime: timedelta,
        *,
        session_id: str | None = None,
        auth_version: int = 1,
    ) -> str:
        now = datetime.now(UTC)
        payload: dict[str, Any] = {
            "sub": subject,
            "type": token_type,
            "jti": secrets.token_urlsafe(18),
            "iat": now,
            "exp": now + lifetime,
        }
        if session_id:
            payload["sid"] = session_id
        if token_type == "access":
            payload["ver"] = auth_version
        return jwt.encode(payload, self.settings.secret_key, algorithm=self.algorithm)

    def decode(self, token: str, expected_type: TokenType) -> TokenPayload:
        try:
            payload = jwt.decode(token, self.settings.secret_key, algorithms=[self.algorithm])
            token_type = payload["type"]
            if token_type != expected_type:
                raise TokenDecodeError("Unexpected token type")
            subject = payload["sub"]
            token_id = payload["jti"]
            issued_at = datetime.fromtimestamp(payload["iat"], tz=UTC)
            expires_at = datetime.fromtimestamp(payload["exp"], tz=UTC)
            auth_version = int(payload.get("ver", 1))
        except (InvalidTokenError, KeyError, TypeError, ValueError) as error:
            raise TokenDecodeError("Invalid or expired token") from error
        return TokenPayload(
            subject=subject,
            token_type=token_type,
            token_id=token_id,
            issued_at=issued_at,
            expires_at=expires_at,
            session_id=payload.get("sid"),
            auth_version=auth_version,
        )


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
