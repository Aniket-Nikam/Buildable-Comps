from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import AuditLog, Permission, Role, RolePermission, UserRole


class AuthorizationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_role(self, role_id: str) -> Role | None:
        return self.session.get(Role, role_id)

    def get_role_by_name(self, name: str) -> Role | None:
        return self.session.scalar(select(Role).where(Role.name == name))

    def list_roles(self) -> list[Role]:
        return list(self.session.scalars(select(Role).order_by(Role.name)))

    def get_permission(self, permission_id: str) -> Permission | None:
        return self.session.get(Permission, permission_id)

    def get_permission_by_name(self, name: str) -> Permission | None:
        return self.session.scalar(select(Permission).where(Permission.name == name))

    def list_permissions(self) -> list[Permission]:
        return list(self.session.scalars(select(Permission).order_by(Permission.name)))

    def roles_for_user(self, user_id: str) -> list[Role]:
        query = (
            select(Role)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user_id)
            .order_by(Role.name)
        )
        return list(self.session.scalars(query))

    def permissions_for_user(self, user_id: str) -> list[Permission]:
        query = (
            select(Permission)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(UserRole, UserRole.role_id == RolePermission.role_id)
            .where(UserRole.user_id == user_id)
            .distinct()
            .order_by(Permission.name)
        )
        return list(self.session.scalars(query))

    def permissions_for_role(self, role_id: str) -> list[Permission]:
        query = (
            select(Permission)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == role_id)
            .order_by(Permission.name)
        )
        return list(self.session.scalars(query))

    def get_user_role(self, user_id: str, role_id: str) -> UserRole | None:
        return self.session.get(UserRole, (user_id, role_id))

    def get_role_permission(self, role_id: str, permission_id: str) -> RolePermission | None:
        return self.session.get(RolePermission, (role_id, permission_id))

    def list_audit_logs(self, limit: int, offset: int) -> list[AuditLog]:
        query = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
        return list(self.session.scalars(query))
