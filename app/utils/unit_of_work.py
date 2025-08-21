from abc import ABC, abstractmethod

from app.db.database import async_session_maker
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository


class IUnitOfWork(ABC):
    task_repo: TaskRepository
    user_repo: UserRepository

    @abstractmethod
    async def __aenter__(self):
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    @abstractmethod
    async def commit(self):
        pass

    @abstractmethod
    async def rollback(self):
        pass


class UnitOfWork(IUnitOfWork):
    def __init__(self, session_maker):
        self.session_maker = session_maker

    async def __aenter__(self):
        self.session = self.session_maker()
        self.user_repo = UserRepository(self.session)
        self.task_repo = TaskRepository(self.session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.rollback()
        await self.session.close()
        self.session = None

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()


async def get_unit_of_work():
    return UnitOfWork(async_session_maker)
