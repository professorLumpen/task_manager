import pytest
from fastapi import status
from fastapi.exceptions import ResponseValidationError

from app.api.schemas.user import UserAuth, UserCreate


@pytest.mark.asyncio
async def test_get_users(async_mock_client, user_from_db, mock_user_service):
    mock_user_service.get_users.return_value = [user_from_db]

    response = await async_mock_client.get("/users/")

    response_data = response.json()
    user = response_data[0]
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response_data, list)
    assert user == user_from_db.model_dump()
    assert not hasattr(user, "password")
    mock_user_service.get_users.assert_called_once()


@pytest.mark.asyncio
async def test_get_user(async_mock_client, user_with_tasks, mock_user_service):
    user_id = user_with_tasks.id
    mock_user_service.get_user.return_value = user_with_tasks

    response = await async_mock_client.get(f"/users/{user_id}/")

    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data == user_with_tasks.model_dump()
    mock_user_service.get_user.assert_called_once_with(id=user_id)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "id, username, roles, tasks, message",
    (
        [None, "user1", ["user"], [], "Field required"],
        [1, None, ["user"], [], "Field required"],
        [1, "user1", ["user"], None, "Field required"],
        ["one", "user1", ["user"], [], "should be a valid"],
        [1, 2, ["user"], [], "should be a valid"],
        [1, "user1", "user", [], "should be a valid"],
        [1, "user1", ["user"], 13, "should be a valid"],
    ),
)
async def test_get_user_wrong_output(async_mock_client, mock_user_service, id, username, roles, tasks, message):
    exc_type = ResponseValidationError
    user_from_db = {
        key: val
        for key, val in [
            ("id", id),
            ("username", username),
            ("roles", roles),
            ("tasks", tasks),
        ]
        if val is not None
    }

    mock_user_service.get_user.return_value = user_from_db

    with pytest.raises(exc_type) as exc_info:
        await async_mock_client.get("/users/1/")

    assert exc_info.type == exc_type
    assert message in exc_info.value.errors()[0]["msg"]


@pytest.mark.asyncio
async def test_create_user(async_mock_client, user_data, user_from_db, mock_user_service):
    user_to_create = UserCreate(**user_data)
    mock_user_service.create_user.return_value = user_from_db

    response = await async_mock_client.post("/users/", json=user_data)

    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data == user_from_db.model_dump()
    mock_user_service.create_user.assert_called_once_with(user_to_create)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "username, password, roles, message",
    (
        ["user1", None, ["user"], "Field required"],
        [None, "password", ["user"], "Field required"],
        [2, "password", ["user"], "should be a valid"],
        ["user1", 2, ["user"], "should be a valid"],
        ["user1", "password", "user", "should be a valid"],
    ),
)
async def test_create_user_wrong_input(
    async_mock_client, user_from_db, mock_user_service, username, password, roles, message
):
    user_data = {
        key: val
        for key, val in [
            ("username", username),
            ("password", password),
            ("roles", roles),
        ]
        if val is not None
    }
    mock_user_service.create_user.return_value = user_from_db

    response = await async_mock_client.post("/users/", json=user_data)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert message in response.json()["detail"][0]["msg"]
    mock_user_service.create_user.assert_not_called()


@pytest.mark.asyncio
async def test_update_user(async_mock_client, user_data, user_from_db, mock_user_service):
    user_id = user_from_db.id
    user_to_update = UserCreate(**user_data)
    mock_user_service.update_user.return_value = user_from_db

    response = await async_mock_client.put(f"/users/{user_id}/", json=user_data)

    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data == user_from_db.model_dump()
    mock_user_service.update_user.assert_called_once_with(user_id, user_to_update)


@pytest.mark.asyncio
async def test_delete_user(async_mock_client, user_from_db, mock_user_service):
    user_id = user_from_db.id
    mock_user_service.delete_user.return_value = user_from_db

    response = await async_mock_client.delete(f"/users/{user_id}/")

    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data == user_from_db.model_dump()
    mock_user_service.delete_user.assert_called_once_with(user_id)


@pytest.mark.asyncio
async def test_login_user(async_mock_client, user_data, mock_user_service):
    token_data = {"access_token": "1111", "token_type": "Bearer"}
    user_to_auth = UserAuth(**user_data)
    mock_user_service.login_user.return_value = token_data

    response = await async_mock_client.post("/users/login/", json=user_data)

    response_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert response_data == token_data
    mock_user_service.login_user.assert_called_once_with(user_to_auth)
