import pytest
from fastapi import HTTPException, status

from app.api.schemas.common import TaskWithUsers, UserWithTasks
from app.api.schemas.task import TaskCreate, TaskFromDB


@pytest.mark.asyncio
async def test_task_service_get_tasks(task_from_db, mock_task_repo, task_service, mock_ws_manager, mock_uow):
    mock_task_repo.find_all.return_value = [task_from_db]

    tasks = await task_service.get_tasks()

    task = tasks[0]
    assert all(getattr(task, key) == val for key, val in task_from_db.model_dump().items())
    assert isinstance(task, TaskFromDB)
    assert not hasattr(task, "users")
    mock_task_repo.find_all.assert_called_once()
    mock_ws_manager.broadcast.assert_not_called()
    mock_uow.uow.commit.assert_not_called()


@pytest.mark.asyncio
async def test_task_service_get_task(
    task_data, task_with_users, mock_task_repo, task_service, mock_ws_manager, mock_uow
):
    mock_task_repo.find_one.return_value = task_with_users

    task = await task_service.get_task(**task_data)

    assert all(getattr(task, key) == val for key, val in task_with_users.model_dump().items())
    assert isinstance(task, TaskWithUsers)
    mock_task_repo.find_one.assert_called_once_with(**task_data)
    mock_ws_manager.broadcast.assert_not_called()
    mock_uow.uow.commit.assert_not_called()


@pytest.mark.asyncio
async def test_task_service_create_task(
    task_data, task_from_db, mock_task_repo, task_service, mock_ws_manager, mock_uow
):
    mock_task_repo.add_one.return_value = task_from_db
    task_in = TaskCreate(**task_data)

    task = await task_service.create_task(task_in)

    assert all(getattr(task, key) == val for key, val in task_from_db.model_dump().items())
    assert isinstance(task, TaskFromDB)
    mock_task_repo.add_one.assert_called_once_with(task_data)
    mock_ws_manager.broadcast.assert_called_once()
    mock_uow.uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_task_service_delete_task(
    task_data, task_from_db, mock_task_repo, task_service, mock_ws_manager, mock_uow
):
    mock_task_repo.remove_one.return_value = task_from_db
    task_id = task_from_db.id

    task = await task_service.delete_task(task_id)

    assert all(getattr(task, key) == val for key, val in task_from_db.model_dump().items())
    assert isinstance(task, TaskFromDB)
    mock_task_repo.remove_one.assert_called_once_with(task_id)
    mock_ws_manager.broadcast.assert_called_once()
    mock_uow.uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_task_service_update_task(
    task_data, task_from_db, mock_task_repo, task_service, mock_ws_manager, mock_uow
):
    mock_task_repo.update_one.return_value = task_from_db
    task_in = TaskCreate(**task_data)
    task_id = task_from_db.id

    task = await task_service.update_task(task_id, task_in)

    assert all(getattr(task, key) == val for key, val in task_from_db.model_dump().items())
    assert isinstance(task, TaskFromDB)
    mock_task_repo.update_one.assert_called_once_with(task_id, task_data)
    mock_ws_manager.broadcast.assert_called_once()
    mock_uow.uow.commit.assert_called_once()


async def test_task_service_assign_task(
    task_with_users, user_with_tasks, mock_task_repo, mock_user_repo, task_service, mock_ws_manager, mock_uow
):
    mock_task_repo.find_one.return_value = task_with_users
    mock_user_repo.find_one.return_value = user_with_tasks
    task_id = task_with_users.id
    user_id = user_with_tasks.id

    task = await task_service.assign_task(task_id, user_id)
    user = task.users[0]

    assert all(getattr(task, key) == val for key, val in task_with_users.model_dump().items() if key != "users")
    assert isinstance(task, TaskWithUsers)
    assert all(getattr(user, key) == val for key, val in user_with_tasks.model_dump().items())
    assert isinstance(user, UserWithTasks)
    mock_task_repo.find_one.assert_called_once_with(id=task_id)
    mock_user_repo.find_one.assert_called_once_with(id=user_id)
    mock_ws_manager.broadcast.assert_called_once()
    mock_uow.uow.commit.assert_called_once()


async def test_task_service_already_assigned(
    task_with_users, user_with_tasks, mock_task_repo, mock_user_repo, task_service, mock_ws_manager, mock_uow
):
    task_with_users.users.append(user_with_tasks)
    mock_task_repo.find_one.return_value = task_with_users
    mock_user_repo.find_one.return_value = user_with_tasks
    task_id = task_with_users.id
    user_id = user_with_tasks.id

    with pytest.raises(HTTPException) as exc_info:
        await task_service.assign_task(task_id, user_id)

    assert exc_info.value.status_code == status.HTTP_409_CONFLICT
    assert exc_info.value.detail == "User is already assigned"
    mock_task_repo.find_one.assert_called_once_with(id=task_id)
    mock_user_repo.find_one.assert_called_once_with(id=user_id)
    mock_ws_manager.broadcast.assert_not_called()
    mock_uow.uow.commit.assert_not_called()


async def test_task_service_unassign_task(
    task_with_users, user_with_tasks, mock_task_repo, mock_user_repo, task_service, mock_ws_manager, mock_uow
):
    task_with_users.users.append(user_with_tasks)
    mock_task_repo.find_one.return_value = task_with_users
    mock_user_repo.find_one.return_value = user_with_tasks
    task_id = task_with_users.id
    user_id = user_with_tasks.id

    task = await task_service.unassign_task(task_id, user_id)

    assert all(getattr(task, key) == val for key, val in task_with_users.model_dump().items())
    assert isinstance(task, TaskWithUsers)
    mock_task_repo.find_one.assert_called_once_with(id=task_id)
    mock_user_repo.find_one.assert_called_once_with(id=user_id)
    mock_ws_manager.broadcast.assert_called_once()
    mock_uow.uow.commit.assert_called_once()


async def test_task_service_already_not_assigned(
    task_with_users, user_with_tasks, mock_task_repo, mock_user_repo, task_service, mock_ws_manager, mock_uow
):
    mock_task_repo.find_one.return_value = task_with_users
    mock_user_repo.find_one.return_value = user_with_tasks
    task_id = task_with_users.id
    user_id = user_with_tasks.id

    with pytest.raises(HTTPException) as exc_info:
        await task_service.unassign_task(task_id, user_id)

    assert exc_info.value.status_code == status.HTTP_409_CONFLICT
    assert exc_info.value.detail == "User is not assigned"
    mock_task_repo.find_one.assert_called_once_with(id=task_id)
    mock_user_repo.find_one.assert_called_once_with(id=user_id)
    mock_ws_manager.broadcast.assert_not_called()
    mock_uow.uow.commit.assert_not_called()
