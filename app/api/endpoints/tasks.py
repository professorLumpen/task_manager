from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.task import TaskIn
from app.db.database import get_session
from app.repositories.task_repository import TaskRepository


tasks_router = APIRouter(tags=["tasks"], prefix="/tasks")


@tasks_router.get("/")
async def get_tasks(session: AsyncSession = Depends(get_session)):
    tasks_repo = TaskRepository(session)
    return await tasks_repo.find_all()


@tasks_router.get("/{task_id}/")
async def get_task(task_id: int, session: AsyncSession = Depends(get_session)):
    tasks_repo = TaskRepository(session)
    return await tasks_repo.find_one(task_id)


@tasks_router.post("/")
async def create_task(task: TaskIn, session: AsyncSession = Depends(get_session)):
    task_repo = TaskRepository(session)
    return await task_repo.add_one(task.model_dump())


@tasks_router.patch("/{task_id}/")
async def update_task(task_id: int, task: TaskIn, session: AsyncSession = Depends(get_session)):
    task_repo = TaskRepository(session)
    return await task_repo.update_one(task_id, task.model_dump())


@tasks_router.delete("/{task_id}/")
async def delete_task(task_id: int, session: AsyncSession = Depends(get_session)):
    task_repo = TaskRepository(session)
    return await task_repo.remove_one(task_id)
