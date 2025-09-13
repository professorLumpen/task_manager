from app.api.schemas.task import TaskFromDB
from app.api.schemas.user import UserFromDB


class UserWithTasks(UserFromDB):
    tasks: list[TaskFromDB]


class TaskWithUsers(TaskFromDB):
    users: list[UserFromDB]
