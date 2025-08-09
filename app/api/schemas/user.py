from pydantic import BaseModel


class UserIn(BaseModel):
    username: str
    password: str
    roles: list = ["user"]
