from dataclasses import dataclass
from typing import Any

from buildable_core.errors import AppError
from buildable_core.events import DomainEvent, EventPublisher, InProcessEventPublisher
from buildable_identity import UserRepository
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .models import AuditLog, Permission, Role, RolePermission, UserRole
from .repositories import AuthorizationRepository

SYSTEM_PERMISSIONS: tuple[tuple[str, str], ...] = (
    ("authorization.roles.read", "View roles and permissions."),
    ("authorization.roles.write", "Create roles, permissions, and permission grants."),
    ("authorization.assignments.write", "Assign and revoke user roles."),
    ("authorization.audit.read", "View authorization audit history."),
)
SYSTEM_ADMIN_ROLE = "platform-admin"


@dataclass(frozen=True, slots=True)
class AuditContext:
    request_id: str | None = None
    ip_address: str | None = None


EMPTY_AUDIT_CONTEXT = AuditContext()


class AuthorizationService:
    def __init__(
        self,
        session: Session,
        event_publisher: EventPublisher | None = None,
    ) -> None:
        self.session = session
        self.repository = AuthorizationRepository(session)
        self.users = UserRepository(session)
        self.events = event_publisher or InProcessEventPublisher()

    def snapshot(self, user_id: str) -> tuple[list[Role], list[Permission]]:
        if self.users.get_by_id(user_id) is None:
            raise AppError("user_not_found", "The requested user was not found.", status_code=404)
        return (
            self.repository.roles_for_user(user_id),
            self.repository.permissions_for_user(user_id),
        )

    def has_permission(self, user_id: str, permission_name: str) -> bool:
        return any(
            permission.name == permission_name
            for permission in self.repository.permissions_for_user(user_id)
        )

    def create_role(
        self,
        name: str,
        description: str,
        actor_user_id: str,
        context: AuditContext = EMPTY_AUDIT_CONTEXT,
    ) -> Role:
        normalized_name = name.strip().lower()
        if self.repository.get_role_by_name(normalized_name):
            raise AppError("role_exists", "A role with this name already exists.", status_code=409)
        role = Role(name=normalized_name, description=description.strip())
        try:
            self.session.add(role)
            self.session.flush()
            self._audit(actor_user_id, "role.created", "role", role.id, {}, context)
            self.session.commit()
        except IntegrityError as error:
            self.session.rollback()
            raise AppError(
                "role_exists", "A role with this name already exists.", status_code=409
            ) from error
        self.events.publish(DomainEvent.create("RoleCreated", {"roleId": role.id}))
        return role

    def create_permission(
        self,
        name: str,
        description: str,
        actor_user_id: str,
        context: AuditContext = EMPTY_AUDIT_CONTEXT,
    ) -> Permission:
        normalized_name = name.strip().lower()
        if self.repository.get_permission_by_name(normalized_name):
            raise AppError(
                "permission_exists",
                "A permission with this name already exists.",
                status_code=409,
            )
        permission = Permission(name=normalized_name, description=description.strip())
        try:
            self.session.add(permission)
            self.session.flush()
            self._audit(
                actor_user_id,
                "permission.created",
                "permission",
                permission.id,
                {"name": permission.name},
                context,
            )
            self.session.commit()
        except IntegrityError as error:
            self.session.rollback()
            raise AppError(
                "permission_exists",
                "A permission with this name already exists.",
                status_code=409,
            ) from error
        self.events.publish(
            DomainEvent.create("PermissionCreated", {"permissionId": permission.id})
        )
        return permission

    def grant_permission(
        self,
        role_id: str,
        permission_id: str,
        actor_user_id: str,
        context: AuditContext = EMPTY_AUDIT_CONTEXT,
    ) -> None:
        self._require_role(role_id)
        self._require_permission(permission_id)
        if self.repository.get_role_permission(role_id, permission_id):
            return
        self.session.add(
            RolePermission(
                role_id=role_id,
                permission_id=permission_id,
                granted_by_user_id=actor_user_id,
            )
        )
        self._audit(
            actor_user_id,
            "role.permission_granted",
            "role",
            role_id,
            {"permissionId": permission_id},
            context,
        )
        self.session.commit()
        self.events.publish(
            DomainEvent.create(
                "PermissionGranted", {"roleId": role_id, "permissionId": permission_id}
            )
        )

    def revoke_permission(
        self,
        role_id: str,
        permission_id: str,
        actor_user_id: str,
        context: AuditContext = EMPTY_AUDIT_CONTEXT,
    ) -> None:
        grant = self.repository.get_role_permission(role_id, permission_id)
        if grant is None:
            return
        role = self._require_role(role_id)
        permission = self._require_permission(permission_id)
        if role.is_system and permission.name in {name for name, _ in SYSTEM_PERMISSIONS}:
            raise AppError(
                "system_grant_protected",
                "System role permissions cannot be revoked.",
                status_code=409,
            )
        self.session.delete(grant)
        self._audit(
            actor_user_id,
            "role.permission_revoked",
            "role",
            role_id,
            {"permissionId": permission_id},
            context,
        )
        self.session.commit()
        self.events.publish(
            DomainEvent.create(
                "PermissionRevoked", {"roleId": role_id, "permissionId": permission_id}
            )
        )

    def assign_role(
        self,
        user_id: str,
        role_id: str,
        actor_user_id: str,
        context: AuditContext = EMPTY_AUDIT_CONTEXT,
    ) -> None:
        if self.users.get_by_id(user_id) is None:
            raise AppError("user_not_found", "The requested user was not found.", status_code=404)
        self._require_role(role_id)
        if self.repository.get_user_role(user_id, role_id):
            return
        self.session.add(
            UserRole(
                user_id=user_id,
                role_id=role_id,
                assigned_by_user_id=actor_user_id,
            )
        )
        self._audit(
            actor_user_id,
            "user.role_assigned",
            "user",
            user_id,
            {"roleId": role_id},
            context,
        )
        self.session.commit()
        self.events.publish(
            DomainEvent.create("RoleAssigned", {"userId": user_id, "roleId": role_id})
        )

    def revoke_role(
        self,
        user_id: str,
        role_id: str,
        actor_user_id: str,
        context: AuditContext = EMPTY_AUDIT_CONTEXT,
    ) -> None:
        assignment = self.repository.get_user_role(user_id, role_id)
        if assignment is None:
            return
        if user_id == actor_user_id and self._is_system_admin_role(role_id):
            raise AppError(
                "self_lockout_prevented",
                "You cannot remove your own platform administrator role.",
                status_code=409,
            )
        self.session.delete(assignment)
        self._audit(
            actor_user_id,
            "user.role_revoked",
            "user",
            user_id,
            {"roleId": role_id},
            context,
        )
        self.session.commit()
        self.events.publish(
            DomainEvent.create("RoleRevoked", {"userId": user_id, "roleId": role_id})
        )

    def _require_role(self, role_id: str) -> Role:
        role = self.repository.get_role(role_id)
        if role is None:
            raise AppError("role_not_found", "The requested role was not found.", status_code=404)
        return role

    def _require_permission(self, permission_id: str) -> Permission:
        permission = self.repository.get_permission(permission_id)
        if permission is None:
            raise AppError(
                "permission_not_found",
                "The requested permission was not found.",
                status_code=404,
            )
        return permission

    def _is_system_admin_role(self, role_id: str) -> bool:
        role = self.repository.get_role(role_id)
        return bool(role and role.is_system and role.name == SYSTEM_ADMIN_ROLE)

    def _audit(
        self,
        actor_user_id: str | None,
        action: str,
        target_type: str,
        target_id: str,
        details: dict[str, Any],
        context: AuditContext,
    ) -> None:
        self.session.add(
            AuditLog(
                actor_user_id=actor_user_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                details=details,
                request_id=context.request_id,
                ip_address=context.ip_address,
            )
        )


def bootstrap_administrator(session: Session, user_id: str) -> Role:
    """Idempotently create management permissions and grant them to one existing user."""

    users = UserRepository(session)
    if users.get_by_id(user_id) is None:
        raise AppError("user_not_found", "The requested user was not found.", status_code=404)
    repository = AuthorizationRepository(session)
    role = repository.get_role_by_name(SYSTEM_ADMIN_ROLE)
    if role is None:
        role = Role(
            name=SYSTEM_ADMIN_ROLE,
            description="Manages roles, permissions, assignments, and authorization audit history.",
            is_system=True,
        )
        session.add(role)
        session.flush()
    for name, description in SYSTEM_PERMISSIONS:
        permission = repository.get_permission_by_name(name)
        if permission is None:
            permission = Permission(name=name, description=description)
            session.add(permission)
            session.flush()
        if repository.get_role_permission(role.id, permission.id) is None:
            session.add(RolePermission(role_id=role.id, permission_id=permission.id))
    if repository.get_user_role(user_id, role.id) is None:
        session.add(UserRole(user_id=user_id, role_id=role.id))
        session.add(
            AuditLog(
                actor_user_id=user_id,
                action="authorization.bootstrapped",
                target_type="user",
                target_id=user_id,
                details={"roleId": role.id},
            )
        )
    session.commit()
    return role
