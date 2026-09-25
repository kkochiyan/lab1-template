from collections.abc import Callable
from dataclasses import dataclass

from app.db.models import Person
from app.exceptions import PersonNotFoundError
from app.uow.interfaces import UnitOfWork


@dataclass(frozen=True)
class PersonData:
    """A snapshot that remains usable after the database session closes."""

    id: int
    name: str
    age: int | None
    address: str | None
    work: str | None

    @classmethod
    def from_person(cls, person: Person) -> "PersonData":
        return cls(
            id=person.id,
            name=person.name,
            age=person.age,
            address=person.address,
            work=person.work,
        )


class PersonService:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]):
        self._uow_factory = uow_factory

    async def get_all_persons(self) -> list[PersonData]:
        async with self._uow_factory() as uow:
            persons = await uow.persons.get_all_persons()
            return [PersonData.from_person(person) for person in persons]

    async def get_person_by_id(self, person_id: int) -> PersonData:
        async with self._uow_factory() as uow:
            person = await uow.persons.get_person_by_id(person_id)
            if person is None:
                raise PersonNotFoundError(person_id)
            return PersonData.from_person(person)

    async def create_person(self, person_data: dict) -> PersonData:
        async with self._uow_factory() as uow:
            person = await uow.persons.create_person(person_data)
            result = PersonData.from_person(person)
            await uow.commit()
            return result

    async def update_person(self, person_id: int, updated_data: dict) -> PersonData:
        async with self._uow_factory() as uow:
            person = await uow.persons.update_person(person_id, updated_data)
            if person is None:
                raise PersonNotFoundError(person_id)
            result = PersonData.from_person(person)
            await uow.commit()
            return result

    async def delete_person(self, person_id: int) -> None:
        async with self._uow_factory() as uow:
            if not await uow.persons.delete_person(person_id):
                raise PersonNotFoundError(person_id)
            await uow.commit()
