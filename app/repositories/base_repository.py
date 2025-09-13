from abc import ABC, abstractmethod

from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


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

    @property
    def second_model(self):
        return

    async def get_obj(self, **filters):
        conditions = [getattr(self.model, key) == val for key, val in filters.items()]
        query = select(self.model).where(and_(*conditions)).options(selectinload(self.second_model))
        result = await self.session.execute(query)
        obj = result.scalars().first()
        return obj

    async def add_one(self, data: dict):
        obj = await self.get_obj(**data)
        if obj:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already exists")

        new_obj = self.model(**data)
        self.session.add(new_obj)
        await self.session.flush()
        await self.session.refresh(new_obj)
        return new_obj

    async def find_all(self):
        query = select(self.model)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def find_one(self, **filters):
        obj = await self.get_obj(**filters)
        if obj:
            return obj
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")

    async def update_one(self, obj_id: int, new_data: dict):
        obj = await self.find_one(id=obj_id)
        for key, val in new_data.items():
            setattr(obj, key, val)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def remove_one(self, obj_id: int):
        obj = await self.find_one(id=obj_id)
        await self.session.delete(obj)
        return obj
