from pydantic import BaseModel, ConfigDict

from app.core.security import mask_sensitive_repr


class SensitiveReprMixin:
    def __repr__(self):
        fields = mask_sensitive_repr(self.model_dump())
        return f"{self.__class__.__name__}({fields})"

    def __str__(self):
        fields = mask_sensitive_repr(self.model_dump())
        return f"{self.__class__.__name__}({fields})"


class UserBase(BaseModel):
    username: str


class UserAuth(SensitiveReprMixin, UserBase):
    password: str


class UserCreate(UserAuth):
    roles: list = ["user"]


class UserFromDB(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    roles: list = ["user"]


class AuthToken(SensitiveReprMixin, BaseModel):
    model_config = ConfigDict(from_attributes=True)

    access_token: str
    token_type: str = "Bearer"
