from fastapi import APIRouter, Depends

from app.api.schemas.common import TaskWithUsers
from app.api.schemas.task import TaskAssign, TaskCreate, TaskFromDB
from app.services.task_service import TaskService, get_task_service


tasks_router = APIRouter(tags=["tasks"], prefix="/tasks")


@tasks_router.get("/", response_model=list[TaskFromDB])
async def get_tasks(task_service: TaskService = Depends(get_task_service)):
    return await task_service.get_tasks()


@tasks_router.get("/{task_id}/", response_model=TaskWithUsers)
async def get_task(task_id: int, task_service: TaskService = Depends(get_task_service)):
    return await task_service.get_task(id=task_id)


@tasks_router.post("/", response_model=TaskFromDB)
async def create_task(task: TaskCreate, task_service: TaskService = Depends(get_task_service)):
    return await task_service.create_task(task)


@tasks_router.patch("/{task_id}/", response_model=TaskFromDB)
async def update_task(task_id: int, task: TaskCreate, task_service: TaskService = Depends(get_task_service)):
    return await task_service.update_task(task_id, task)


@tasks_router.delete("/{task_id}/", response_model=TaskFromDB)
async def delete_task(task_id: int, task_service: TaskService = Depends(get_task_service)):
    return await task_service.delete_task(task_id)


@tasks_router.post("/assign/", response_model=TaskFromDB)
async def assign_task(assign_data: TaskAssign, task_service: TaskService = Depends(get_task_service)):
    return await task_service.assign_task(**assign_data.model_dump())


@tasks_router.delete("/assign/", response_model=TaskFromDB)
async def unassign_task(assign_data: TaskAssign, task_service: TaskService = Depends(get_task_service)):
    return await task_service.unassign_task(**assign_data.model_dump())
