from app.db.models import Task
from app.repositories.base_repository import Repository


class TaskRepository(Repository):
    model = Task

    @property
    def second_model(self):
        return Task.users
