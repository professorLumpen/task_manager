import asyncio

import pytest
from fastapi import status

from app.core.config import settings


async def create_and_login_user(async_client, user_data):
    await async_client.post("/users/", json=user_data)

    token_data = await async_client.post("/users/login/", json=user_data)

    token, token_type = token_data.json().values()
    headers = {"Authorization": f"{token_type} {token}"}

    return headers


async def get_response_with_any_method(async_client, method, uri, headers, params):
    methods_with_params = {"post", "put"}
    request = getattr(async_client, method)
    if method in methods_with_params:
        return await request(uri, headers=headers, json=params)
    return await request(uri, headers=headers)


@pytest.mark.asyncio
async def test_login(async_test_client, user_data):
    await async_test_client.post("/users/", json=user_data)
    response = await async_test_client.post("/users/login/", json=user_data)

    token_data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in token_data
    assert token_data["token_type"] == "Bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(async_test_client, user_data):
    await async_test_client.post("/users/", json=user_data)
    user_data["password"] = "wrong"

    response = await async_test_client.post("/users/login/", json=user_data)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Incorrect password"


@pytest.mark.asyncio
async def test_login_wrong_token(async_test_client, user_data):
    headers = await create_and_login_user(async_test_client, user_data)
    headers["Authorization"] = f"{headers['Authorization']}1"

    response = await async_test_client.get("/users/", headers=headers)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid token"


@pytest.mark.asyncio
async def test_login_expired_token(async_test_client, user_data, monkeypatch):
    expire_seconds = 1
    monkeypatch.setattr(settings, "JWT_ACCESS_EXPIRE_SECONDS", expire_seconds)

    headers = await create_and_login_user(async_test_client, user_data)
    await asyncio.sleep(expire_seconds)

    response = await async_test_client.get("/tasks/", headers=headers)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Token expired"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method, uri",
    (
        ["get", "/users/"],
        ["get", "/users/1/"],
        ["put", "/users/1/"],
        ["delete", "/users/1/"],
        ["get", "/tasks/"],
        ["post", "/tasks/"],
        ["get", "/tasks/1/"],
        ["put", "/tasks/1/"],
        ["delete", "/tasks/1/"],
        ["post", "/tasks/assign/"],
        ["post", "/tasks/unassign/"],
    ),
)
async def test_auth_required(async_test_client, method, uri):
    request = getattr(async_test_client, method)
    response = await request(uri)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method, uri, params, status_code",
    (
        ["post", "/users/", {"username": "user", "password": "pass"}, status.HTTP_200_OK],
        ["post", "/users/login/", {"username": "user", "password": "pass"}, status.HTTP_404_NOT_FOUND],
    ),
)
async def test_auth_not_required(async_test_client, method, uri, params, status_code):
    request = getattr(async_test_client, method)
    response = await request(uri, json=params)

    assert response.status_code == status_code


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method, uri, params",
    (
        ["get", "/users/", {}],
        ["put", "/users/1/", {"username": "user", "password": "pass"}],
        ["delete", "/users/1/", {}],
        ["post", "/tasks/", {"title": "task", "description": "descr"}],
        ["get", "/tasks/1/", {}],
        ["put", "/tasks/1/", {"title": "task", "description": "descr"}],
        ["delete", "/tasks/1/", {}],
        ["post", "/tasks/assign/", {"task_id": 1, "user_id": 1}],
        ["post", "/tasks/unassign/", {"task_id": 1, "user_id": 1}],
    ),
)
async def test_access_for_user_denied(async_test_client, user_data, method, uri, params):
    headers = await create_and_login_user(async_test_client, user_data)

    response = await get_response_with_any_method(async_test_client, method, uri, headers, params)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Access denied"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method, uri, params",
    (
        ["get", "/users/1/", {}],
        ["get", "/tasks/", {}],
        ["post", "/users/", {"username": "user2", "password": "pass"}],
        ["post", "/users/login/", {"username": "user1", "password": "password"}],
    ),
)
async def test_access_for_user(async_test_client, user_data, method, uri, params):
    headers = await create_and_login_user(async_test_client, user_data)

    response = await get_response_with_any_method(async_test_client, method, uri, headers, params)

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method, uri, params, status_code",
    (
        ["get", "/users/", {}, status.HTTP_200_OK],
        ["post", "/users/", {"username": "user2", "password": "pass"}, status.HTTP_200_OK],
        ["get", "/users/1/", {}, status.HTTP_200_OK],
        ["put", "/users/1/", {"username": "user1", "password": "password"}, status.HTTP_200_OK],
        ["delete", "/users/1/", {}, status.HTTP_200_OK],
        ["post", "/users/login/", {"username": "user1", "password": "password"}, status.HTTP_200_OK],
        ["get", "/tasks/", {}, status.HTTP_200_OK],
        ["post", "/tasks/", {"title": "task", "description": "descr"}, status.HTTP_200_OK],
        ["get", "/tasks/1/", {}, status.HTTP_404_NOT_FOUND],
        ["put", "/tasks/1/", {"title": "task", "description": "descr"}, status.HTTP_404_NOT_FOUND],
        ["delete", "/tasks/1/", {}, status.HTTP_404_NOT_FOUND],
        ["post", "/tasks/assign/", {"task_id": 1, "user_id": 1}, status.HTTP_404_NOT_FOUND],
        ["post", "/tasks/unassign/", {"task_id": 1, "user_id": 1}, status.HTTP_404_NOT_FOUND],
    ),
)
async def test_access_for_admin(async_test_client, user_data, method, uri, params, status_code):
    user_data["roles"].append("admin")
    headers = await create_and_login_user(async_test_client, user_data)

    response = await get_response_with_any_method(async_test_client, method, uri, headers, params)

    assert response.status_code == status_code
