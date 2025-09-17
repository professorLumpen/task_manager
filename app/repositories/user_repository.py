from app.db.models import User
from app.repositories.base_repository import Repository


class UserRepository(Repository):
    model = User

    @property
    def second_model(self):
        return User.tasks

    async def get_obj(self, **filters):
        filters.pop("password", None)
        return await super().get_obj(**filters)
