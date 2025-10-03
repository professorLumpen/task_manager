from fastapi import APIRouter, Depends

from app.api.schemas.common import TaskWithUsers, UserWithTasks
from app.api.schemas.task import TaskAssign, TaskCreate, TaskFromDB
from app.core.dependencies import get_current_user
from app.services.task_service import TaskService, get_task_service
from app.utils.rbac import PermissionChecker


tasks_router = APIRouter(tags=["tasks"], prefix="/tasks")


@tasks_router.get("/", response_model=list[TaskFromDB])
@PermissionChecker(["user"])
async def get_tasks(
    current_user: UserWithTasks = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
):
    return await task_service.get_tasks()


@tasks_router.post("/", response_model=TaskFromDB)
@PermissionChecker(["admin"])
async def create_task(
    task: TaskCreate,
    current_user: UserWithTasks = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
):
    return await task_service.create_task(task)


@tasks_router.post("/assign/", response_model=TaskFromDB)
@PermissionChecker(["admin"])
async def assign_task(
    assign_data: TaskAssign,
    current_user: UserWithTasks = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
):
    return await task_service.assign_task(**assign_data.model_dump())


@tasks_router.post("/unassign/", response_model=TaskFromDB)
@PermissionChecker(["admin"])
async def unassign_task(
    assign_data: TaskAssign,
    current_user: UserWithTasks = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
):
    return await task_service.unassign_task(**assign_data.model_dump())


@tasks_router.get("/{task_id}/", response_model=TaskWithUsers)
@PermissionChecker(["admin"])
async def get_task(
    task_id: int,
    current_user: UserWithTasks = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
):
    return await task_service.get_task(id=task_id)


@tasks_router.put("/{task_id}/", response_model=TaskFromDB)
@PermissionChecker(["admin"])
async def update_task(
    task_id: int,
    task: TaskCreate,
    current_user: UserWithTasks = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
):
    return await task_service.update_task(task_id, task)


@tasks_router.delete("/{task_id}/", response_model=TaskFromDB)
@PermissionChecker(["admin"])
async def delete_task(
    task_id: int,
    current_user: UserWithTasks = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
):
    return await task_service.delete_task(task_id)
