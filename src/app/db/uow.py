from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.repositories.interfaces import PersonRepository
from app.repositories.persons import SQLAlchemyPersonRepository


class SqlAlchemyUnitOfWork:
    """Own a session and require explicit commit to persist changes.

    Create a separate unit of work for each operation; do not share it
    between concurrent tasks or nested contexts.
    """

    persons: PersonRepository
    _session: AsyncSession

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def __aenter__(self) -> Self:
        self._session = self._session_factory()
        self.persons = SQLAlchemyPersonRepository(self._session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        try:
            await self.rollback()
        finally:
            await self._session.close()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
