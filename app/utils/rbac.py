import functools

from fastapi import HTTPException, status


class PermissionChecker:
    def __init__(self, access_roles):
        self.access_roles = access_roles

    def __call__(self, func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user", None)
            if current_user is None:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")
            if not any(role in self.access_roles for role in current_user.roles):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
            return await func(*args, **kwargs)

        return wrapper
