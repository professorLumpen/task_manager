from abc import ABC, abstractmethod

from fastapi import HTTPException
from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession


class AbstractRepository(ABC):
    @abstractmethod
    async def add_one(self, data: dict):
        pass

    @abstractmethod
    async def find_all(self):
        pass

    @abstractmethod
    async def find_one(self, obj_id: int):
        pass

    @abstractmethod
    async def update_one(self, obj_id: int, new_data: dict):
        pass

    @abstractmethod
    async def remove_one(self, obj_id: int):
        pass


class Repository(AbstractRepository):
    model = None

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_one(self, data: dict):
        query = insert(self.model).values(**data).returning(self.model)
        result = await self.session.execute(query)
        return result.scalar_one()

    async def find_all(self):
        query = select(self.model)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def find_one(self, obj_id: int):
        obj = await self.session.get(self.model, obj_id)
        if obj:
            return obj
        raise HTTPException(status_code=404, detail="Not Found")

    async def update_one(self, obj_id: int, new_data: dict):
        obj = await self.find_one(obj_id)
        for key, val in new_data.items():
            setattr(obj, key, val)
        await self.session.commit()
        return obj

    async def remove_one(self, obj_id: int):
        query = delete(self.model).where(self.model.id == obj_id)
        await self.session.execute(query)
        await self.session.commit()
        return obj_id
