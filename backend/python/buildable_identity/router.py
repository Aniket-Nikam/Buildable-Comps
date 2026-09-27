from buildable_core.config import Settings
from fastapi import APIRouter, Request, Response, status
from sqlalchemy.orm import Session

from .dependencies import CurrentUser, DbSession
from .schemas import (
    AuthData,
    EmailRequest,
    LoginRequest,
    PasswordResetRequest,
    RegisterRequest,
    SuccessEnvelope,
    TokenRequest,
    UpdateProfileRequest,
    UserPublic,
)
from .service import AuthenticationService, AuthResult, UserProfileService

REFRESH_COOKIE = "buildable_refresh"
router = APIRouter()


def _service(request: Request, session: Session) -> AuthenticationService:
    return AuthenticationService(
        session,
        request.app.state.settings,
        request.app.state.events,
        request.app.state.identity_notifier,
    )


def _rate_limit(request: Request, action: str) -> None:
    client_host = request.client.host if request.client else "unknown"
    request.app.state.auth_rate_limiter.check(f"{action}:{client_host}")


def _auth_data(result: AuthResult) -> AuthData:
    return AuthData(
        access_token=result.access_token,
        expires_in=result.expires_in,
        user=UserPublic.model_validate(result.user),
    )


def _set_refresh_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(
        REFRESH_COOKIE,
        token,
        max_age=settings.refresh_token_ttl_days * 86400,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path=f"{settings.api_prefix}/auth",
    )


@router.post("/auth/register", response_model=SuccessEnvelope, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    session: DbSession,
) -> SuccessEnvelope:
    _rate_limit(request, "register")
    result = _service(request, session).register(
        str(payload.email), payload.password, payload.display_name
    )
    _set_refresh_cookie(response, result.refresh_token, request.app.state.settings)
    return SuccessEnvelope(data=_auth_data(result))


@router.post("/auth/login", response_model=SuccessEnvelope)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    session: DbSession,
) -> SuccessEnvelope:
    _rate_limit(request, "login")
    result = _service(request, session).login(str(payload.email), payload.password)
    _set_refresh_cookie(response, result.refresh_token, request.app.state.settings)
    return SuccessEnvelope(data=_auth_data(result))


@router.post("/auth/refresh", response_model=SuccessEnvelope)
def refresh(request: Request, response: Response, session: DbSession) -> SuccessEnvelope:
    token = request.cookies.get(REFRESH_COOKIE, "")
    result = _service(request, session).refresh(token)
    _set_refresh_cookie(response, result.refresh_token, request.app.state.settings)
    return SuccessEnvelope(data=_auth_data(result))


@router.post("/auth/logout", response_model=SuccessEnvelope)
def logout(request: Request, response: Response, session: DbSession) -> SuccessEnvelope:
    _service(request, session).logout(request.cookies.get(REFRESH_COOKIE))
    response.delete_cookie(REFRESH_COOKIE, path=f"{request.app.state.settings.api_prefix}/auth")
    return SuccessEnvelope(data={"loggedOut": True})


@router.post("/auth/email-verification/request", response_model=SuccessEnvelope)
def request_email_verification(
    payload: EmailRequest, request: Request, session: DbSession
) -> SuccessEnvelope:
    _rate_limit(request, "email-verification-request")
    _service(request, session).request_email_verification(str(payload.email))
    return SuccessEnvelope(data={"accepted": True})


@router.post("/auth/email-verification/confirm", response_model=SuccessEnvelope)
def confirm_email_verification(
    payload: TokenRequest, request: Request, session: DbSession
) -> SuccessEnvelope:
    _rate_limit(request, "email-verification-confirm")
    user = _service(request, session).verify_email(payload.token)
    return SuccessEnvelope(data=UserPublic.model_validate(user))


@router.post("/auth/password/forgot", response_model=SuccessEnvelope)
def forgot_password(payload: EmailRequest, request: Request, session: DbSession) -> SuccessEnvelope:
    _rate_limit(request, "password-forgot")
    _service(request, session).request_password_reset(str(payload.email))
    return SuccessEnvelope(data={"accepted": True})


@router.post("/auth/password/reset", response_model=SuccessEnvelope)
def reset_password(
    payload: PasswordResetRequest, request: Request, session: DbSession
) -> SuccessEnvelope:
    _rate_limit(request, "password-reset")
    _service(request, session).reset_password(payload.token, payload.new_password)
    return SuccessEnvelope(data={"passwordReset": True})


@router.get("/users/me", response_model=SuccessEnvelope)
def get_me(user: CurrentUser) -> SuccessEnvelope:
    return SuccessEnvelope(data=UserPublic.model_validate(user))


@router.patch("/users/me", response_model=SuccessEnvelope)
def update_me(
    payload: UpdateProfileRequest,
    session: DbSession,
    user: CurrentUser,
) -> SuccessEnvelope:
    updated_user = UserProfileService(session).update_display_name(user, payload.display_name)
    return SuccessEnvelope(data=UserPublic.model_validate(updated_user))
