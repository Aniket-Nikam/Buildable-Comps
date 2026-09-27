from collections.abc import Generator
from typing import Annotated

from buildable_core.errors import AppError
from buildable_core.security import TokenDecodeError, TokenService
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .models import User
from .repositories import UserRepository

bearer = HTTPBearer(auto_error=False)


def get_db(request: Request) -> Generator[Session, None, None]:
    session = request.app.state.session_factory()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    session: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None:
        raise AppError("authentication_required", "Authentication is required.", status_code=401)
    try:
        payload = TokenService(request.app.state.settings).decode(credentials.credentials, "access")
    except TokenDecodeError as error:
        raise AppError(
            "authentication_required", "Authentication is required.", status_code=401
        ) from error
    user = UserRepository(session).get_by_id(payload.subject)
    if user is None or user.status != "active":
        raise AppError("authentication_required", "Authentication is required.", status_code=401)
    if payload.auth_version != user.auth_version:
        raise AppError("authentication_required", "Authentication is required.", status_code=401)
    if request.app.state.settings.require_verified_email and not user.email_verified:
        raise AppError(
            "email_verification_required",
            "Verify your email before continuing.",
            status_code=403,
        )
    return user


DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
