from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Person


class SQLAlchemyPersonRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_persons(self) -> list[Person]:
        result = await self.session.execute(select(Person).order_by(Person.id))
        return list(result.scalars().all())

    async def get_person_by_id(self, person_id: int) -> Person | None:
        result = await self.session.execute(
            select(Person).where(Person.id == person_id)
        )
        return result.scalar_one_or_none()

    async def create_person(self, person_data: dict) -> Person:
        new_person = Person(**person_data)
        self.session.add(new_person)
        await self.session.flush()
        return new_person

    async def update_person(self, person_id: int, updated_data: dict) -> Person | None:
        person = await self.get_person_by_id(person_id)
        if person:
            for key, value in updated_data.items():
                setattr(person, key, value)
            await self.session.flush()
            return person
        return None

    async def delete_person(self, person_id: int) -> bool:
        person = await self.get_person_by_id(person_id)
        if person:
            await self.session.delete(person)
            await self.session.flush()
            return True
        return False