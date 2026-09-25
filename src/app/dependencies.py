from functools import partial

from fastapi import Request

from app.db.uow import SqlAlchemyUnitOfWork
from app.services.persons import PersonService


def get_person_service(request: Request) -> PersonService:
    """The application factory supplies the session factory on app.state."""
    return PersonService(
        partial(SqlAlchemyUnitOfWork, request.app.state.session_factory)
    )
