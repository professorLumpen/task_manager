from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    username: str


class UserAuth(UserBase):
    password: str


class UserCreate(UserAuth):
    roles: list = ["user"]


class UserFromDB(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    roles: list = ["user"]
