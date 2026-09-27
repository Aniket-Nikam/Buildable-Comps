from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        extra="forbid",
    )


class SuccessEnvelope(ApiModel):
    success: bool = True
    data: Any
    meta: dict[str, Any] = Field(default_factory=dict)
