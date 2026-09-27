from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True, extra="forbid"
    )


class RegisterRequest(ApiModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    display_name: str = Field(min_length=2, max_length=80)


class LoginRequest(ApiModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UpdateProfileRequest(ApiModel):
    display_name: str = Field(min_length=2, max_length=80)


class EmailRequest(ApiModel):
    email: EmailStr


class TokenRequest(ApiModel):
    token: str = Field(min_length=32, max_length=256)


class PasswordResetRequest(TokenRequest):
    new_password: str = Field(min_length=12, max_length=128)


class UserPublic(ApiModel):
    id: str
    email: EmailStr
    display_name: str
    status: str
    email_verified: bool
    created_at: datetime
    updated_at: datetime


class AuthData(ApiModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserPublic


class SuccessEnvelope(ApiModel):
    success: bool = True
    data: Any
    meta: dict[str, Any] = Field(default_factory=dict)
