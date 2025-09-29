from unittest.mock import patch

import pytest
from fastapi import HTTPException, status

from app.api.schemas.common import UserWithTasks
from app.api.schemas.user import UserAuth, UserCreate, UserFromDB


@pytest.mark.asyncio
async def test_user_service_get_users(user_from_db, mock_user_repo, user_service, mock_uow):
    mock_user_repo.find_all.return_value = [user_from_db]

    users = await user_service.get_users()

    user = users[0]
    assert all(getattr(user, key) == val for key, val in user_from_db.model_dump().items())
    assert isinstance(user, UserFromDB)
    assert hasattr(user, "tasks") is False
    mock_user_repo.find_all.assert_called_once()
    mock_uow.uow.commit.assert_not_called()


@pytest.mark.asyncio
async def test_user_service_get_user(user_data, user_with_tasks, mock_user_repo, user_service, mock_uow):
    mock_user_repo.find_one.return_value = user_with_tasks

    user = await user_service.get_user(**user_data)

    assert all(getattr(user, key) == val for key, val in user_with_tasks.model_dump().items())
    assert isinstance(user, UserWithTasks)
    assert hasattr(user, "password") is False
    mock_user_repo.find_one.assert_called_once_with(**user_data)
    mock_uow.uow.commit.assert_not_called()


@pytest.mark.asyncio
async def test_user_service_create_user(user_data, user_from_db, mock_user_repo, user_service, mock_uow):
    mock_user_repo.add_one.return_value = user_from_db
    user_in = UserCreate(**user_data)

    with patch("app.services.user_service.get_password_hash", return_value="password"):
        user = await user_service.create_user(user_in)

    assert all(getattr(user, key) == val for key, val in user_from_db.model_dump().items())
    assert isinstance(user, UserFromDB)
    assert not hasattr(user, "password")
    mock_user_repo.add_one.assert_called_once_with(user_data)
    mock_uow.uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_user_service_delete_user(user_data, user_from_db, mock_user_repo, user_service, mock_uow):
    mock_user_repo.remove_one.return_value = user_from_db
    user_id = user_from_db.id

    user = await user_service.delete_user(user_id)

    assert all(getattr(user, key) == val for key, val in user_from_db.model_dump().items())
    assert isinstance(user, UserFromDB)
    mock_user_repo.remove_one.assert_called_once_with(user_id)
    mock_uow.uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_user_service_update_user(user_data, user_from_db, mock_user_repo, user_service, mock_uow):
    mock_user_repo.update_one.return_value = user_from_db
    user_in = UserCreate(**user_data)
    user_id = user_from_db.id

    with patch("app.services.user_service.get_password_hash", return_value="password"):
        user = await user_service.update_user(user_id, user_in)

    assert all(getattr(user, key) == val for key, val in user_from_db.model_dump().items())
    assert isinstance(user, UserFromDB)
    mock_user_repo.update_one.assert_called_once_with(user_id, user_data)
    mock_uow.uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_user_service_login_user(user_data, user_with_password, mock_user_repo, user_service, mock_uow):
    mock_user_repo.find_one.return_value = user_with_password
    user_auth = UserAuth(**user_data)

    with patch("app.services.user_service.verify_password", return_value=True):
        token_data = await user_service.login_user(user_auth)

    assert hasattr(token_data, "access_token")
    assert getattr(token_data, "token_type") == "Bearer"
    mock_user_repo.find_one.assert_called_once_with(**user_auth.model_dump())
    mock_uow.uow.commit.assert_not_called()


@pytest.mark.asyncio
async def test_user_service_login_user_incorrect(user_data, user_with_password, mock_user_repo, user_service, mock_uow):
    mock_user_repo.find_one.return_value = user_with_password
    user_auth = UserAuth(**user_data)

    with patch("app.services.user_service.verify_password", return_value=False):
        with pytest.raises(HTTPException) as exc_info:
            await user_service.login_user(user_auth)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Incorrect password"
    mock_user_repo.find_one.assert_called_once_with(**user_auth.model_dump())
    mock_uow.uow.commit.assert_not_called()
