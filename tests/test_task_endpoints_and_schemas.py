import datetime

import pytest
from fastapi import status as http_status
from fastapi.exceptions import ResponseValidationError

from app.api.schemas.task import TaskCreate


@pytest.mark.asyncio
async def test_get_tasks(async_mock_client, task_from_db, mock_task_service):
    mock_task_service.get_tasks.return_value = [task_from_db]

    response = await async_mock_client.get("/tasks/")

    response_data = response.json()
    task = response_data[0]
    task["created_at"] = datetime.datetime.fromisoformat(task["created_at"])

    assert response.status_code == http_status.HTTP_200_OK
    assert isinstance(response_data, list)
    assert task == task_from_db.model_dump()
    mock_task_service.get_tasks.assert_called_once()


@pytest.mark.asyncio
async def test_get_task(async_mock_client, task_with_users, mock_task_service):
    task_id = task_with_users.id
    mock_task_service.get_task.return_value = task_with_users

    response = await async_mock_client.get(f"/tasks/{task_id}/")

    response_data = response.json()
    response_data["created_at"] = datetime.datetime.fromisoformat(response_data["created_at"])

    assert response.status_code == http_status.HTTP_200_OK
    assert response_data == task_with_users.model_dump()
    mock_task_service.get_task.assert_called_once_with(id=task_id)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "id, title, description, status, users, created_at, completed_at, message",
    (
        [None, "task1", "descr", "created", [], datetime.datetime.now(), datetime.datetime.now(), "Field required"],
        [1, None, "descr", "created", [], datetime.datetime.now(), datetime.datetime.now(), "Field required"],
        [1, "task1", None, "created", [], datetime.datetime.now(), datetime.datetime.now(), "Field required"],
        [1, "task1", "descr", "created", None, datetime.datetime.now(), datetime.datetime.now(), "Field required"],
        [1, "task1", "descr", "created", [], None, datetime.datetime.now(), "Field required"],
        [1, "task1", "descr", "created", [], datetime.datetime.now(), None, "Field required"],
        ["one", "task1", "descr", "created", [], datetime.datetime.now(), None, "should be a valid"],
        [1, 2, "descr", "created", [], datetime.datetime.now(), None, "should be a valid"],
        [1, "task1", 2, "created", [], datetime.datetime.now(), datetime.datetime.now(), "should be a valid"],
        [1, "task1", "descr", 2, [], datetime.datetime.now(), datetime.datetime.now(), "should be a valid"],
        [
            1,
            "task1",
            "descr",
            "created",
            "tasks",
            datetime.datetime.now(),
            datetime.datetime.now(),
            "should be a valid",
        ],
        [1, "task1", "descr", "created", [], datetime.datetime.now(), "12:30", "should be a valid"],
    ),
)
async def test_get_task_wrong_output(
    async_mock_client, mock_task_service, id, title, description, status, users, created_at, completed_at, message
):
    exc_type = ResponseValidationError
    task_from_db = {
        key: val
        for key, val in [
            ("id", id),
            ("title", title),
            ("status", status),
            ("users", users),
            ("description", description),
            ("created_at", created_at),
            ("completed_at", completed_at),
        ]
        if val is not None
    }

    mock_task_service.get_task.return_value = task_from_db

    with pytest.raises(exc_type) as exc_info:
        await async_mock_client.get("/tasks/1/")

    assert exc_info.type == exc_type
    assert message in exc_info.value.errors()[0]["msg"]


@pytest.mark.asyncio
async def test_create_task(async_mock_client, task_data, task_from_db, mock_task_service):
    task_to_update = TaskCreate(**task_data)
    mock_task_service.create_task.return_value = task_from_db

    response = await async_mock_client.post("/tasks/", json=task_data)

    response_data = response.json()
    response_data["created_at"] = datetime.datetime.fromisoformat(response_data["created_at"])

    assert response.status_code == http_status.HTTP_200_OK
    assert response_data == task_from_db.model_dump()
    mock_task_service.create_task.assert_called_once_with(task_to_update)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "title, description, status, message",
    (
        ["task1", None, "created", "Field required"],
        [None, "description", "created", "Field required"],
        [2, "description", "created", "should be a valid"],
        ["task1", 2, "created", "should be a valid"],
        ["task1", "description", 2, "should be a valid"],
    ),
)
async def test_create_task_wrong_input(async_mock_client, mock_task_service, title, description, status, message):
    task_data = {
        key: val
        for key, val in [
            ("title", title),
            ("description", description),
            ("status", status),
        ]
        if val is not None
    }

    response = await async_mock_client.post("/tasks/", json=task_data)

    assert response.status_code == http_status.HTTP_422_UNPROCESSABLE_ENTITY
    assert message in response.json()["detail"][0]["msg"]
    mock_task_service.create_task.assert_not_called()


@pytest.mark.asyncio
async def test_update_task(async_mock_client, task_data, task_from_db, mock_task_service):
    task_id = task_from_db.id
    task_to_update = TaskCreate(**task_data)
    mock_task_service.update_task.return_value = task_from_db

    response = await async_mock_client.put(f"/tasks/{task_id}/", json=task_data)

    response_data = response.json()
    response_data["created_at"] = datetime.datetime.fromisoformat(response_data["created_at"])

    assert response.status_code == http_status.HTTP_200_OK
    assert response_data == task_from_db.model_dump()
    mock_task_service.update_task.assert_called_once_with(task_id, task_to_update)


@pytest.mark.asyncio
async def test_delete_task(async_mock_client, task_from_db, mock_task_service):
    task_id = task_from_db.id
    mock_task_service.delete_task.return_value = task_from_db

    response = await async_mock_client.delete(f"/tasks/{task_id}/")

    response_data = response.json()
    response_data["created_at"] = datetime.datetime.fromisoformat(response_data["created_at"])

    assert response.status_code == http_status.HTTP_200_OK
    assert response_data == task_from_db.model_dump()
    mock_task_service.delete_task.assert_called_once_with(task_id)


@pytest.mark.asyncio
async def test_assign_task(async_mock_client, task_from_db, mock_task_service):
    assign_data = {"user_id": 1, "task_id": 1}
    mock_task_service.assign_task.return_value = task_from_db

    response = await async_mock_client.post("/tasks/assign/", json=assign_data)

    response_data = response.json()
    response_data["created_at"] = datetime.datetime.fromisoformat(response_data["created_at"])

    assert response.status_code == http_status.HTTP_200_OK
    assert response_data == task_from_db.model_dump()
    mock_task_service.assign_task.assert_called_once_with(**assign_data)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "user_id, task_id, message",
    (
        [None, 1, "Field required"],
        [1, None, "Field required"],
        ["one", 1, "should be a valid"],
        [1, "one", "should be a valid"],
    ),
)
async def test_assign_task_wrong_input(async_mock_client, task_from_db, mock_task_service, user_id, task_id, message):
    assign_data = {key: val for key, val in [("user_id", user_id), ("task_id", task_id)] if val is not None}

    response = await async_mock_client.post("/tasks/assign/", json=assign_data)

    assert response.status_code == http_status.HTTP_422_UNPROCESSABLE_ENTITY
    assert message in response.json()["detail"][0]["msg"]
    mock_task_service.create_task.assert_not_called()


@pytest.mark.asyncio
async def test_unassign_task(async_mock_client, task_from_db, mock_task_service):
    assign_data = {"user_id": 1, "task_id": 1}
    mock_task_service.unassign_task.return_value = task_from_db

    response = await async_mock_client.post("/tasks/unassign/", json=assign_data)

    response_data = response.json()
    response_data["created_at"] = datetime.datetime.fromisoformat(response_data["created_at"])

    assert response.status_code == http_status.HTTP_200_OK
    assert response_data == task_from_db.model_dump()
    mock_task_service.unassign_task.assert_called_once_with(**assign_data)
