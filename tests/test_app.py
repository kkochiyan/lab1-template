from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.dependencies import get_person_service
from app.main import create_app


@pytest.fixture
def settings():
    return Settings(
        DATABASE_URL="postgresql+asyncpg://program:test@localhost/persons",
        _env_file=None,
    )


def test_factory_wires_dependencies_and_disposes_engine(settings):
    engine = MagicMock()
    engine.dispose = AsyncMock()
    session_factory = MagicMock()
    with (
        patch("app.main.create_engine", return_value=engine) as build_engine,
        patch("app.main.create_session_factory", return_value=session_factory),
    ):
        app = create_app(settings)
        build_engine.assert_not_called()
        with TestClient(app) as client:
            assert app.state.session_factory is session_factory
            request = MagicMock(app=app)
            service = get_person_service(request)
            assert service._uow_factory()._session_factory is session_factory
            assert client.get("/docs").status_code == 200
            engine.dispose.assert_not_awaited()
        build_engine.assert_called_once_with(settings.DATABASE_URL)
        engine.dispose.assert_awaited_once_with()
        assert not hasattr(app.state, "session_factory")
