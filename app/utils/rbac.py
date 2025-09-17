import functools

from fastapi import HTTPException, status


class PermissionChecker:
    def __init__(self, access_roles):
        self.access_roles = access_roles

    def __call__(self, func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            user_id = kwargs.get("user_id")
            request = kwargs.get("request")

            if current_user is None:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

            if "admin" in current_user.roles:
                return await func(*args, **kwargs)

            if user_id is None and not any(role in self.access_roles for role in current_user.roles):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

            if user_id is not None:
                if request is None:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No information about request")
                if request.method != "GET" or user_id != current_user.id:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

            return await func(*args, **kwargs)

        return wrapper
