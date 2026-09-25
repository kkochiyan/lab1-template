from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.exceptions import PersonNotFoundError
from app.routers.schemas import ErrorResponseSchema, ValidationErrorResponseSchema


async def person_not_found_handler(
    request: Request, exc: PersonNotFoundError
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content=ErrorResponseSchema(message=str(exc)).model_dump(),
    )


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors: dict[str, str] = {}
    for error in exc.errors():
        location = error["loc"]
        # Use field names ("name", "id") rather than transport prefixes.
        field = ".".join(str(part) for part in location[1:])
        field = field or str(location[0] if location else "request")
        errors[field] = error["msg"]

    return JSONResponse(
        status_code=400,
        content=ValidationErrorResponseSchema(
            message="Invalid data", errors=errors
        ).model_dump(),
    )


async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponseSchema(message=str(exc.detail)).model_dump(),
        headers=exc.headers,
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(PersonNotFoundError, person_not_found_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(HTTPException, http_error_handler)
