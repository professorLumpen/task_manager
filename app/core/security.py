import datetime

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

from app.core.config import settings
from logger import logger


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_data: dict) -> str:
    to_encode = user_data.copy()
    cur_time = datetime.datetime.now(datetime.UTC)
    expire_delta = datetime.timedelta(seconds=settings.JWT_ACCESS_EXPIRE_SECONDS)
    to_encode.update({"exp": cur_time + expire_delta})
    token = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token


def decode_token(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Exception: expired token")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expired")
    except jwt.InvalidTokenError:
        logger.warning("Exception: invalid token")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")


def get_current_user_id(payload: dict = Depends(decode_token)) -> int:
    user_id = payload.get("sub")
    if user_id is None:
        logger.warning("Exception: no user id")
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    try:
        return int(user_id)
    except ValueError:
        logger.warning("Exception: invalid user id")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")


def mask_sensitive_repr(fields: dict) -> str:
    valid_fields = []

    for key, value in fields.items():
        if key in settings.SENSITIVE_FIELDS:
            valid_fields.append(f"{key}='***'")
        else:
            valid_fields.append(f"{key}='{value}'")

    return ", ".join(valid_fields)
