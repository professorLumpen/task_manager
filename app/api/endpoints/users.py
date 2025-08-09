from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.user import UserIn
from app.db.database import get_session
from app.repositories.user_repository import UserRepository


user_router = APIRouter(tags=["users"], prefix="/users")


@user_router.get("/")
async def read_users(session: AsyncSession = Depends(get_session)):
    user_repo = UserRepository(session)
    return await user_repo.find_all()


@user_router.get("/{user_id}/")
async def read_user(user_id: int, session: AsyncSession = Depends(get_session)):
    user_repo = UserRepository(session)
    return user_repo.find_one(user_id)


@user_router.post("/{user_id}/")
async def create_user(user: UserIn, session: AsyncSession = Depends(get_session)):
    user_repo = UserRepository(session)
    return await user_repo.add_one(user.model_dump())


@user_router.patch("/{user_id}/")
async def update_user(user_id: int, user: UserIn, session: AsyncSession = Depends(get_session)):
    user_repo = UserRepository(session)
    return await user_repo.update_one(user_id, user.model_dump())


@user_router.delete("/{user_id}/")
async def delete_user(user_id: int, session: AsyncSession = Depends(get_session)):
    user_repo = UserRepository(session)
    return await user_repo.remove_one(user_id)
