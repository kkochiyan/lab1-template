from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


Int32 = Annotated[
    int,
    Field(ge=-(2**31), le=2**31 - 1, json_schema_extra={"format": "int32"}),
]


class PersonResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Int32
    name: str
    age: Int32 | None = None
    address: str | None = None
    work: str | None = None


class PersonRequestSchema(BaseModel):
    """POST and PATCH payload; name is required by the API contract.

    For PATCH, pass model_dump(exclude_unset=True) to the service so that
    omitted fields are preserved and explicitly provided nulls are retained.
    """

    name: str
    age: Int32 | None = None
    address: str | None = None
    work: str | None = None
