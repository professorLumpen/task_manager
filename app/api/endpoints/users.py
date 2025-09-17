from typing import List

from fastapi import APIRouter, Depends, Request

from app.api.schemas.common import UserWithTasks
from app.api.schemas.user import UserAuth, UserCreate, UserFromDB
from app.core.dependencies import get_current_user
from app.services.user_service import UserService, get_user_service
from app.utils.rbac import PermissionChecker


users_router = APIRouter(tags=["users"], prefix="/users")


@users_router.post("/login/")
async def login_user(user: UserAuth, user_service: UserService = Depends(get_user_service)):
    token = await user_service.login_user(user)
    return token


@users_router.get("/", response_model=List[UserFromDB])
@PermissionChecker(["admin"])
async def get_users(
    request: Request,
    current_user: UserWithTasks = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    return await user_service.get_users()


@users_router.get("/{user_id}/", response_model=UserWithTasks)
@PermissionChecker(["admin"])
async def get_user(
    request: Request,
    user_id: int,
    current_user: UserWithTasks = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    return await user_service.get_user(id=user_id)


@users_router.post("/", response_model=UserFromDB)
async def create_user(user: UserCreate, user_service: UserService = Depends(get_user_service)):
    return await user_service.create_user(user)


@users_router.put("/{user_id}/", response_model=UserFromDB)
@PermissionChecker(["admin"])
async def update_user(
    request: Request,
    user_id: int,
    user: UserCreate,
    current_user: UserWithTasks = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    return await user_service.update_user(user_id, user)


@users_router.delete("/{user_id}/", response_model=UserFromDB)
@PermissionChecker(["admin"])
async def delete_user(
    request: Request,
    user_id: int,
    current_user: UserWithTasks = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    return await user_service.delete_user(user_id)
