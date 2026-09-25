from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.dependencies import get_person_service
from app.exceptions import PersonNotFoundError
from app.services.persons import PersonData, PersonService
from app.main import create_app


@pytest.fixture
def api():
    service = AsyncMock(spec=PersonService)
    app = create_app(Settings(DATABASE_URL="postgresql+asyncpg://program:test@localhost/persons", _env_file=None))
    app.dependency_overrides[get_person_service] = lambda: service
    with TestClient(app) as client:
        yield client, service


def test_create_returns_empty_201_with_relative_location(api):
    client, service = api
    service.create_person.return_value = PersonData(7, "Karen", 25, None, None)

    response = client.post("/api/v1/persons", json={"name": "Karen", "age": 25})

    assert response.status_code == 201
    assert response.content == b""
    assert response.headers["location"] == "/api/v1/persons/7"
    service.create_person.assert_awaited_once_with(
        {"name": "Karen", "age": 25, "address": None, "work": None}
    )


def test_delete_returns_empty_204(api):
    client, service = api
    response = client.delete("/api/v1/persons/7")
    assert response.status_code == 204
    assert response.content == b""
    service.delete_person.assert_awaited_once_with(7)


def test_missing_person_returns_404(api):
    client, service = api
    service.get_person_by_id.side_effect = PersonNotFoundError(7)

    response = client.get("/api/v1/persons/7")

    assert response.status_code == 404
    assert response.json() == {"message": "Person with id 7 was not found"}


def test_invalid_payload_returns_400_without_calling_service(api):
    client, service = api
    response = client.post("/api/v1/persons", json={})

    assert response.status_code == 400
    assert response.json()["message"] == "Invalid data"
    assert isinstance(response.json()["errors"]["name"], str)
    assert service.mock_calls == []
