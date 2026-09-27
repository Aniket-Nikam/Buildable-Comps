from collections.abc import Callable

from buildable_core.errors import AppError
from buildable_identity import CurrentUser, DbSession, User

from .service import AuthorizationService

PermissionGuard = Callable[..., User]


def require_permission(permission_name: str) -> PermissionGuard:
    def dependency(session: DbSession, user: CurrentUser) -> User:
        if not AuthorizationService(session).has_permission(user.id, permission_name):
            raise AppError(
                "permission_denied",
                "You do not have permission to perform this action.",
                status_code=403,
            )
        return user

    return dependency
