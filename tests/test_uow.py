from unittest.mock import MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.uow import SqlAlchemyUnitOfWork


@pytest.fixture
def session():
    return MagicMock(spec=AsyncSession)


async def test_operation_error_is_propagated_and_session_is_closed(session):
    error = ValueError("operation failed")

    with pytest.raises(ValueError) as caught:
        async with SqlAlchemyUnitOfWork(MagicMock(return_value=session)):
            raise error

    assert caught.value is error
    session.commit.assert_not_awaited()
    session.rollback.assert_awaited_once_with()
    session.close.assert_awaited_once_with()
