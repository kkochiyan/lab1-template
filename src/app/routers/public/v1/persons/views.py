from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.dependencies import get_person_service
from app.services.persons import PersonData, PersonService
from app.routers.public.v1.persons.schemas import (
    Int32,
    PersonRequestSchema,
    PersonResponseSchema,
)
from app.routers.schemas import ErrorResponseSchema, ValidationErrorResponseSchema


router = APIRouter(
    prefix="/api/v1/persons",
    tags=["Person REST API operations"],
)
ServiceDependency = Annotated[PersonService, Depends(get_person_service)]
VALIDATION_RESPONSE = {
    400: {"model": ValidationErrorResponseSchema, "description": "Invalid data"},
}
NOT_FOUND_RESPONSE = {
    404: {"model": ErrorResponseSchema, "description": "Person not found"},
}


@router.get("", response_model=list[PersonResponseSchema], summary="Get all Persons")
async def list_persons(service: ServiceDependency) -> list[PersonData]:
    return await service.get_all_persons()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_class=Response,
    summary="Create new Person",
    responses={
        **VALIDATION_RESPONSE,
        201: {
            "description": "Created new Person",
            "headers": {
                "Location": {
                    "description": "Path to new Person",
                    "schema": {"type": "string"},
                },
            },
        },
    },
)
async def create_person(
    payload: PersonRequestSchema, service: ServiceDependency
) -> Response:
    person = await service.create_person(payload.model_dump())
    return Response(
        status_code=status.HTTP_201_CREATED,
        headers={"Location": f"/api/v1/persons/{person.id}"},
    )


@router.get(
    "/{id}",
    response_model=PersonResponseSchema,
    summary="Get Person by ID",
    responses={**VALIDATION_RESPONSE, **NOT_FOUND_RESPONSE},
)
async def get_person(id: Int32, service: ServiceDependency) -> PersonData:
    return await service.get_person_by_id(id)


@router.patch(
    "/{id}",
    response_model=PersonResponseSchema,
    summary="Update Person by ID",
    responses={**VALIDATION_RESPONSE, **NOT_FOUND_RESPONSE},
)
async def update_person(
    id: Int32, payload: PersonRequestSchema, service: ServiceDependency
) -> PersonData:
    return await service.update_person(id, payload.model_dump(exclude_unset=True))


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Remove Person by ID",
    responses={**VALIDATION_RESPONSE, **NOT_FOUND_RESPONSE},
)
async def delete_person(id: Int32, service: ServiceDependency) -> Response:
    await service.delete_person(id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
