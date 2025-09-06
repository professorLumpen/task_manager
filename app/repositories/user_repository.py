from app.db.models import User
from app.repositories.base_repository import Repository


class UserRepository(Repository):
    model = User

    async def find_one(self, **filters):
        filters.pop("password", None)
        return await super().find_one(**filters)
