from typing import Annotated

from buildable_core.errors import AppError
from buildable_core.schemas import SuccessEnvelope
from buildable_identity import CurrentUser, DbSession, User
from fastapi import APIRouter, Depends, Query, Request, status

from .dependencies import require_permission
from .repositories import AuthorizationRepository
from .schemas import (
    AuditLogPublic,
    AuthorizationSnapshot,
    PermissionCreate,
    PermissionPublic,
    RoleCreate,
    RoleDetail,
    RolePublic,
)
from .service import AuditContext, AuthorizationService

router = APIRouter(prefix="/authorization", tags=["authorization"])

RolesReader = Annotated[User, Depends(require_permission("authorization.roles.read"))]
RolesWriter = Annotated[User, Depends(require_permission("authorization.roles.write"))]
AssignmentsWriter = Annotated[User, Depends(require_permission("authorization.assignments.write"))]
AuditReader = Annotated[User, Depends(require_permission("authorization.audit.read"))]


def _service(request: Request, session: DbSession) -> AuthorizationService:
    return AuthorizationService(session, request.app.state.events)


def _context(request: Request) -> AuditContext:
    return AuditContext(
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
    )


@router.get("/me", response_model=SuccessEnvelope)
def get_my_authorization(session: DbSession, user: CurrentUser) -> SuccessEnvelope:
    roles, permissions = AuthorizationService(session).snapshot(user.id)
    return SuccessEnvelope(
        data=AuthorizationSnapshot(
            roles=[RolePublic.model_validate(role) for role in roles],
            permissions=[PermissionPublic.model_validate(permission) for permission in permissions],
        )
    )


@router.get("/roles", response_model=SuccessEnvelope)
def list_roles(session: DbSession, _: RolesReader) -> SuccessEnvelope:
    roles = AuthorizationRepository(session).list_roles()
    return SuccessEnvelope(data=[RolePublic.model_validate(role) for role in roles])


@router.get("/roles/{role_id}", response_model=SuccessEnvelope)
def get_role(role_id: str, session: DbSession, _: RolesReader) -> SuccessEnvelope:
    repository = AuthorizationRepository(session)
    role = repository.get_role(role_id)
    if role is None:
        raise AppError("role_not_found", "The requested role was not found.", status_code=404)
    return SuccessEnvelope(
        data=RoleDetail(
            **RolePublic.model_validate(role).model_dump(),
            permissions=[
                PermissionPublic.model_validate(permission)
                for permission in repository.permissions_for_role(role_id)
            ],
        )
    )


@router.post("/roles", response_model=SuccessEnvelope, status_code=status.HTTP_201_CREATED)
def create_role(
    payload: RoleCreate,
    request: Request,
    session: DbSession,
    actor: RolesWriter,
) -> SuccessEnvelope:
    role = _service(request, session).create_role(
        payload.name, payload.description, actor.id, _context(request)
    )
    return SuccessEnvelope(data=RolePublic.model_validate(role))


@router.get("/permissions", response_model=SuccessEnvelope)
def list_permissions(session: DbSession, _: RolesReader) -> SuccessEnvelope:
    permissions = AuthorizationRepository(session).list_permissions()
    return SuccessEnvelope(
        data=[PermissionPublic.model_validate(permission) for permission in permissions]
    )


@router.post("/permissions", response_model=SuccessEnvelope, status_code=status.HTTP_201_CREATED)
def create_permission(
    payload: PermissionCreate,
    request: Request,
    session: DbSession,
    actor: RolesWriter,
) -> SuccessEnvelope:
    permission = _service(request, session).create_permission(
        payload.name, payload.description, actor.id, _context(request)
    )
    return SuccessEnvelope(data=PermissionPublic.model_validate(permission))


@router.put("/roles/{role_id}/permissions/{permission_id}", response_model=SuccessEnvelope)
def grant_permission(
    role_id: str,
    permission_id: str,
    request: Request,
    session: DbSession,
    actor: RolesWriter,
) -> SuccessEnvelope:
    _service(request, session).grant_permission(role_id, permission_id, actor.id, _context(request))
    return SuccessEnvelope(data={"granted": True})


@router.delete("/roles/{role_id}/permissions/{permission_id}", response_model=SuccessEnvelope)
def revoke_permission(
    role_id: str,
    permission_id: str,
    request: Request,
    session: DbSession,
    actor: RolesWriter,
) -> SuccessEnvelope:
    _service(request, session).revoke_permission(
        role_id, permission_id, actor.id, _context(request)
    )
    return SuccessEnvelope(data={"revoked": True})


@router.put("/users/{user_id}/roles/{role_id}", response_model=SuccessEnvelope)
def assign_role(
    user_id: str,
    role_id: str,
    request: Request,
    session: DbSession,
    actor: AssignmentsWriter,
) -> SuccessEnvelope:
    _service(request, session).assign_role(user_id, role_id, actor.id, _context(request))
    return SuccessEnvelope(data={"assigned": True})


@router.get("/users/{user_id}", response_model=SuccessEnvelope)
def get_user_authorization(
    user_id: str,
    session: DbSession,
    _: RolesReader,
) -> SuccessEnvelope:
    roles, permissions = AuthorizationService(session).snapshot(user_id)
    return SuccessEnvelope(
        data=AuthorizationSnapshot(
            roles=[RolePublic.model_validate(role) for role in roles],
            permissions=[PermissionPublic.model_validate(permission) for permission in permissions],
        )
    )


@router.delete("/users/{user_id}/roles/{role_id}", response_model=SuccessEnvelope)
def revoke_role(
    user_id: str,
    role_id: str,
    request: Request,
    session: DbSession,
    actor: AssignmentsWriter,
) -> SuccessEnvelope:
    _service(request, session).revoke_role(user_id, role_id, actor.id, _context(request))
    return SuccessEnvelope(data={"revoked": True})


@router.get("/audit-logs", response_model=SuccessEnvelope)
def list_audit_logs(
    session: DbSession,
    _: AuditReader,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> SuccessEnvelope:
    logs = AuthorizationRepository(session).list_audit_logs(limit, offset)
    return SuccessEnvelope(data=[AuditLogPublic.model_validate(log) for log in logs])
