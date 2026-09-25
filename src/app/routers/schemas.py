from pydantic import BaseModel


class ErrorResponseSchema(BaseModel):
    message: str


class ValidationErrorResponseSchema(ErrorResponseSchema):
    errors: dict[str, str]
