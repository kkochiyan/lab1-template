from copy import deepcopy

import pytest

from app.db.models import Person
from app.services.persons import PersonService


class FakePersonRepository:
    def __init__(self, persons):
        self.persons = persons

    async def get_all_persons(self):
        return [self.persons[key] for key in sorted(self.persons)]

    async def get_person_by_id(self, person_id):
        return self.persons.get(person_id)

    async def create_person(self, person_data):
        person = Person(id=max(self.persons, default=0) + 1, **person_data)
        self.persons[person.id] = person
        return person

    async def update_person(self, person_id, updated_data):
        person = self.persons.get(person_id)
        if person is not None:
            for key, value in updated_data.items():
                setattr(person, key, value)
        return person

    async def delete_person(self, person_id):
        return self.persons.pop(person_id, None) is not None


class FakeUnitOfWork:
    def __init__(self, storage):
        self.storage = storage
        self.committed = False
        self.closed = False

    async def __aenter__(self):
        self.persons = FakePersonRepository(deepcopy(self.storage))
        return self

    async def __aexit__(self, *args):
        await self.rollback()
        self.closed = True

    async def commit(self):
        self.storage.clear()
        self.storage.update(deepcopy(self.persons.persons))
        self.committed = True

    async def rollback(self):
        self.persons.persons = deepcopy(self.storage)


@pytest.fixture
def service():
    storage = {}
    units = []

    def factory():
        uow = FakeUnitOfWork(storage)
        units.append(uow)
        return uow

    return PersonService(factory), storage, units


async def test_create_persists_person_and_returns_independent_snapshot(service):
    service, storage, units = service
    result = await service.create_person({"name": "Karen", "age": 25})

    assert storage[result.id].name == "Karen"
    assert units[0].committed and units[0].closed
    storage[result.id].name = "Changed"
    assert result.name == "Karen"
    assert result.age == 25


async def test_list_and_get_use_separate_units_without_commit(service):
    service, storage, units = service
    assert await service.get_all_persons() == []
    storage[1] = Person(id=1, name="Karen")

    persons = await service.get_all_persons()
    person = await service.get_person_by_id(1)

    assert persons == [person]
    assert len(units) == 3
    assert all(unit.closed and not unit.committed for unit in units)


async def test_update_preserves_omitted_fields_and_accepts_explicit_none(service):
    service, storage, units = service
    storage[1] = Person(id=1, name="Karen", age=25, address="Moscow", work="Developer")

    result = await service.update_person(1, {"name": "New name", "work": None})

    assert result.name == storage[1].name == "New name"
    assert result.age == storage[1].age == 25
    assert result.address == "Moscow"
    assert result.work is None and storage[1].work is None
    assert units[0].committed


async def test_delete_persists_removal(service):
    service, storage, units = service
    storage[1] = Person(id=1, name="Karen")

    assert await service.delete_person(1) is None
    assert storage == {}
    assert units[0].committed and units[0].closed
