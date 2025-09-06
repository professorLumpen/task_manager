from fastapi import Depends

from app.core.security import get_current_user_id
from app.services.user_service import get_user_service


async def get_current_user(user_id: int = Depends(get_current_user_id), user_service=Depends(get_user_service)):
    user = await user_service.get_user(id=user_id)
    return user
