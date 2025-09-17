from fastapi import HTTPException
from fastapi.params import Depends

from app.api.schemas.common import UserWithTasks
from app.api.schemas.user import UserAuth, UserCreate, UserFromDB
from app.core.security import create_access_token, get_password_hash, verify_password
from app.utils.unit_of_work import IUnitOfWork, get_unit_of_work


class UserService:
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    async def get_users(self) -> list[UserFromDB]:
        async with self.uow as uow:
            users = await uow.user_repo.find_all()
            return [UserFromDB.model_validate(user) for user in users]

    async def get_user(self, **filters) -> UserWithTasks:
        filters.pop("password", None)
        async with self.uow as uow:
            user = await uow.user_repo.find_one(**filters)
            return UserWithTasks.model_validate(user)

    async def create_user(self, user: UserCreate) -> UserFromDB:
        user_data = user.model_dump()
        user_data["password"] = get_password_hash(user_data["password"])
        async with self.uow as uow:
            new_user = await uow.user_repo.add_one(user_data)
            user_to_return = UserFromDB.model_validate(new_user)
            await uow.commit()
            return user_to_return

    async def delete_user(self, user_id: int) -> UserFromDB:
        async with self.uow as uow:
            deleted_user = await uow.user_repo.remove_one(user_id)
            user_to_return = UserFromDB.model_validate(deleted_user)
            await uow.commit()
            return user_to_return

    async def update_user(self, user_id: int, user: UserCreate) -> UserFromDB:
        user_data = user.model_dump()
        user_data["password"] = get_password_hash(user_data["password"])
        async with self.uow as uow:
            updated_user = await uow.user_repo.update_one(user_id, user_data)
            user_to_return = UserFromDB.model_validate(updated_user)
            await uow.commit()
            return user_to_return

    async def login_user(self, user: UserAuth) -> dict[str, str]:
        user_data = user.model_dump()
        async with self.uow as uow:
            found_user = await uow.user_repo.find_one(**user_data)
            if not verify_password(user_data["password"], found_user.password):
                raise HTTPException(status_code=401, detail="Incorrect password")
            payload = {"sub": str(found_user.id)}
            return {"token": create_access_token(payload)}


async def get_user_service(uow: IUnitOfWork = Depends(get_unit_of_work)) -> UserService:
    return UserService(uow)
