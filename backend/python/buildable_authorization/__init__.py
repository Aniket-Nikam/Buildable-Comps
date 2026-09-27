"""Public authorization exports. Route wiring and persistence details remain internal."""

from .dependencies import PermissionGuard, require_permission
from .models import AuditLog, Permission, Role, RolePermission, UserRole
from .service import AuthorizationService, bootstrap_administrator

__all__ = [
    "AuditLog",
    "AuthorizationService",
    "Permission",
    "PermissionGuard",
    "Role",
    "RolePermission",
    "UserRole",
    "bootstrap_administrator",
    "require_permission",
]
