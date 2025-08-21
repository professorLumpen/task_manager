from typing import List

from fastapi import APIRouter
from fastapi.params import Depends

from app.api.schemas.user import UserCreate, UserFromDB
from app.services.user_service import UserService, get_user_service


users_router = APIRouter(tags=["users"], prefix="/users")


@users_router.get("/", response_model=List[UserFromDB])
async def get_users(user_service: UserService = Depends(get_user_service)):
    return await user_service.get_users()


@users_router.get("/{user_id}/", response_model=UserFromDB)
async def get_user(user_id: int, user_service: UserService = Depends(get_user_service)):
    return await user_service.get_user(user_id)


@users_router.post("/", response_model=UserFromDB)
async def create_user(user: UserCreate, user_service: UserService = Depends(get_user_service)):
    return await user_service.create_user(user)


@users_router.patch("/{user_id}/", response_model=UserFromDB)
async def update_user(user_id: int, user: UserCreate, user_service: UserService = Depends(get_user_service)):
    return await user_service.update_user(user_id, user)


@users_router.delete("/{user_id}/", response_model=UserFromDB)
async def delete_user(user_id: int, user_service: UserService = Depends(get_user_service)):
    return await user_service.delete_user(user_id)
