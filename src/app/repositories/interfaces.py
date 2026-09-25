from typing import Protocol

from app.db.models import Person

class PersonRepository(Protocol):
    async def get_all_persons(self) -> list[Person]:
        ...

    async def get_person_by_id(self, person_id: int) -> Person | None:
        ...

    async def create_person(self, person_data: dict) -> Person:
        ...

    async def update_person(self, person_id: int, updated_data: dict) -> Person | None:
        ...

    async def delete_person(self, person_id: int) -> bool:
        ... 