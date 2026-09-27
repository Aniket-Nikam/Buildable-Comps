from datetime import datetime
from typing import Any

from buildable_core.schemas import ApiModel
from pydantic import Field

NAME_PATTERN = r"^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*$"


class RoleCreate(ApiModel):
    name: str = Field(min_length=2, max_length=80, pattern=NAME_PATTERN)
    description: str = Field(default="", max_length=240)


class PermissionCreate(ApiModel):
    name: str = Field(min_length=3, max_length=120, pattern=NAME_PATTERN)
    description: str = Field(default="", max_length=240)


class RolePublic(ApiModel):
    id: str
    name: str
    description: str
    is_system: bool
    created_at: datetime
    updated_at: datetime


class PermissionPublic(ApiModel):
    id: str
    name: str
    description: str
    created_at: datetime


class RoleDetail(RolePublic):
    permissions: list[PermissionPublic]


class AuthorizationSnapshot(ApiModel):
    roles: list[RolePublic]
    permissions: list[PermissionPublic]


class AuditLogPublic(ApiModel):
    id: str
    actor_user_id: str | None
    action: str
    target_type: str
    target_id: str
    details: dict[str, Any]
    request_id: str | None
    ip_address: str | None
    created_at: datetime
