from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import OneTimeToken, RefreshSession, User


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, user_id: str) -> User | None:
        return self.session.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self.session.scalar(select(User).where(User.email == email))

    def add(self, user: User) -> User:
        self.session.add(user)
        self.session.flush()
        return user


class RefreshSessionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_for_update(self, session_id: str) -> RefreshSession | None:
        query = select(RefreshSession).where(RefreshSession.id == session_id).with_for_update()
        return self.session.scalar(query)

    def add(self, refresh_session: RefreshSession) -> RefreshSession:
        self.session.add(refresh_session)
        self.session.flush()
        return refresh_session

    def revoke(self, refresh_session: RefreshSession, at: datetime) -> None:
        refresh_session.revoked_at = at
        refresh_session.last_used_at = at

    def revoke_family(self, family_id: str, at: datetime) -> None:
        query = (
            select(RefreshSession).where(RefreshSession.family_id == family_id).with_for_update()
        )
        for refresh_session in self.session.scalars(query):
            if refresh_session.revoked_at is None:
                self.revoke(refresh_session, at)

    def revoke_all_for_user(self, user_id: str, at: datetime) -> None:
        query = select(RefreshSession).where(RefreshSession.user_id == user_id).with_for_update()
        for refresh_session in self.session.scalars(query):
            if refresh_session.revoked_at is None:
                self.revoke(refresh_session, at)


class OneTimeTokenRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_active_for_update(
        self, token_hash: str, purpose: str, now: datetime
    ) -> OneTimeToken | None:
        query = (
            select(OneTimeToken)
            .where(
                OneTimeToken.token_hash == token_hash,
                OneTimeToken.purpose == purpose,
                OneTimeToken.used_at.is_(None),
                OneTimeToken.expires_at > now,
            )
            .with_for_update()
        )
        return self.session.scalar(query)

    def add(self, token: OneTimeToken) -> OneTimeToken:
        self.session.add(token)
        self.session.flush()
        return token

    def invalidate_active(self, user_id: str, purpose: str, at: datetime) -> None:
        query = (
            select(OneTimeToken)
            .where(
                OneTimeToken.user_id == user_id,
                OneTimeToken.purpose == purpose,
                OneTimeToken.used_at.is_(None),
            )
            .with_for_update()
        )
        for token in self.session.scalars(query):
            token.used_at = at
