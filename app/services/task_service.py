from fastapi import Depends

from app.api.schemas.task import TaskCreate, TaskFromDB
from app.utils.unit_of_work import IUnitOfWork, get_unit_of_work
from app.utils.websocket import ConnectionManager, get_ws_manager


class TaskService:
    def __init__(self, uow: IUnitOfWork, ws_manager: ConnectionManager):
        self.uow = uow
        self.ws_manager = ws_manager

    async def get_tasks(self) -> list[TaskFromDB]:
        async with self.uow as uow:
            tasks = await uow.task_repo.find_all()
            return [TaskFromDB.model_validate(task) for task in tasks]

    async def get_task(self, **filters) -> TaskFromDB:
        async with self.uow as uow:
            task = await uow.task_repo.find_one(**filters)
            return TaskFromDB.model_validate(task)

    async def create_task(self, task: TaskCreate) -> TaskFromDB:
        task_data = task.model_dump()
        async with self.uow as uow:
            new_task = await uow.task_repo.add_one(task_data)
            task_to_return = TaskFromDB.model_validate(new_task)
            await uow.commit()

            await self.ws_manager.broadcast({"event": "task_created", "task": task_to_return.model_dump(mode="json")})

            return task_to_return

    async def delete_task(self, task_id: int) -> TaskFromDB:
        async with self.uow as uow:
            deleted_task = await uow.task_repo.remove_one(task_id)
            task_to_return = TaskFromDB.model_validate(deleted_task)
            await uow.commit()

            await self.ws_manager.broadcast({"event": "task_deleted", "task": task_to_return.model_dump(mode="json")})

            return task_to_return

    async def update_task(self, task_id: int, task: TaskCreate) -> TaskFromDB:
        task_data = task.model_dump()
        async with self.uow as uow:
            updated_task = await uow.task_repo.update_one(task_id, task_data)
            task_to_return = TaskFromDB.model_validate(updated_task)
            await uow.commit()

            await self.ws_manager.broadcast({"event": "task_updated", "task": task_to_return.model_dump(mode="json")})

            return task_to_return


async def get_task_service(
    uow: IUnitOfWork = Depends(get_unit_of_work), ws_manager: ConnectionManager = Depends(get_ws_manager)
) -> TaskService:
    return TaskService(uow, ws_manager)
