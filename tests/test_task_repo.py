import datetime

import pytest
from fastapi import HTTPException
from fastapi import status as http_status
from sqlalchemy.exc import DBAPIError, IntegrityError, ProgrammingError

from app.repositories.task_repository import TaskRepository


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "id, title, description, status",
    (
        [None, "task1", "descr", "status"],
        [1, "task1", "descr", "status"],
    ),
)
async def test_task_repo_add_one(test_session, id, title, description, status):
    test_task_repo = TaskRepository(test_session)
    task_data = {
        k: v
        for k, v in [("id", id), ("title", title), ("description", description), ("status", status)]
        if v is not None
    }

    task = await test_task_repo.add_one(task_data)

    assert task.id == 1
    assert task.completed_at is None
    assert (datetime.datetime.now() - task.created_at) < datetime.timedelta(seconds=1)
    assert all(getattr(task, field) == value for field, value in task_data.items())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "id, title, description, status, wrong_field",
    (
        [None, None, "descr", "created", None],
        [None, "task1", None, "created", None],
        [None, "task1", "descr", None, None],
        [None, "task1", "descr", "created", "wrong_val"],
        [None, 1, "descr", "created", None],
        [None, "task1", 1, "created", None],
        [None, "task1", "descr", 1, None],
        ["23", "task1", "descr", "created", None],
    ),
)
async def test_task_repo_add_one_wrong_data(test_uow, id, title, description, status, wrong_field):
    task_data = {
        k: v
        for k, v in (
            ("id", id),
            ("title", title),
            ("description", description),
            ("status", status),
            ("wrong_field", wrong_field),
        )
        if v is not None
    }
    db_exceptions = (IntegrityError, ProgrammingError, AttributeError)

    async with test_uow as uow:
        with pytest.raises(db_exceptions) as exc_info:
            await uow.task_repo.add_one(task_data)
            await uow.commit()

    assert exc_info.type in db_exceptions


@pytest.mark.asyncio
async def test_task_repo_already_exists(test_uow):
    task_data = {"title": "task1", "description": "descr", "status": "created"}

    async with test_uow as uow:
        await uow.task_repo.add_one(task_data)
        await uow.commit()

    async with test_uow as uow:
        with pytest.raises(HTTPException) as exc_info:
            await uow.task_repo.add_one(task_data)

    assert exc_info.value.status_code == http_status.HTTP_409_CONFLICT
    assert exc_info.value.detail == "Already exists"


@pytest.mark.asyncio
async def test_task_repo_find_all(test_uow):
    task_data = {"title": "task1", "description": "descr", "status": "created"}
    async with test_uow as uow:
        empty_tasks = await uow.task_repo.find_all()
        await uow.task_repo.add_one(task_data)
        await uow.commit()
        tasks = await uow.task_repo.find_all()

        assert empty_tasks == []
        assert len(tasks) == 1
        assert all(getattr(tasks[0], field) == value for field, value in task_data.items())


@pytest.mark.asyncio
async def test_task_repo_find_one(test_uow):
    task_data = {"title": "task1", "description": "descr", "status": "created"}

    async with test_uow as uow:
        await uow.task_repo.add_one(task_data)
        await uow.commit()

    async with test_uow as uow:
        found_task = await uow.task_repo.find_one(id=1)
        assert found_task.id == 1
        assert all(getattr(found_task, field) == value for field, value in task_data.items())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "id, title, description, status",
    (
        [1, None, None, None],
        [None, "task1", None, None],
        [None, None, "descr", None],
        [None, None, None, "created"],
        [1, None, None, "created"],
        [1, "task1", "descr", None],
        [1, "task1", "descr", "created"],
    ),
)
async def test_task_repo_find_one_parameters(test_uow, id, title, description, status):
    task_data = {"title": "task1", "description": "descr", "status": "created"}
    search_data = {
        k: v
        for k, v in (("id", id), ("title", title), ("description", description), ("status", status))
        if v is not None
    }

    async with test_uow as uow:
        await uow.task_repo.add_one(task_data)
        await uow.commit()

        found_task = await uow.task_repo.find_one(**search_data)

        assert found_task.id == 1
        assert all(getattr(found_task, field) == value for field, value in task_data.items())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "id, title, description, status",
    (
        [2, None, None, None],
        [None, "task2", None, None],
        [None, None, "description", None],
        [None, None, None, "assigned"],
        [1, None, None, "assigned"],
        [1, "task1", "", None],
        [1, "task1", "descr", "updated"],
    ),
)
async def test_task_repo_not_found(test_uow, id, title, description, status):
    task_data = {"title": "task1", "description": "descr", "status": "created"}
    search_data = {
        k: v
        for k, v in (("id", id), ("title", title), ("description", description), ("status", status))
        if v is not None
    }

    async with test_uow as uow:
        await uow.task_repo.add_one(task_data)
        await uow.commit()
        found_task = await uow.task_repo.find_one(**task_data)
        assert found_task.id == 1

    async with test_uow as uow:
        with pytest.raises(HTTPException) as exc_info:
            await uow.task_repo.find_one(**search_data)

    assert exc_info.value.status_code == http_status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "Not Found"


@pytest.mark.asyncio
async def test_task_repo_commit(test_uow):
    task_data = {"title": "task1", "description": "descr", "status": "created"}
    async with test_uow as uow:
        await uow.task_repo.add_one(task_data)

    async with test_uow as uow:
        with pytest.raises(HTTPException) as exc_info:
            await uow.task_repo.find_one(id=1)

    assert exc_info.value.status_code == http_status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "Not Found"


@pytest.mark.asyncio
async def test_task_repo_update_not_found(test_uow):
    task_data = {"title": "task1", "description": "descr", "status": "created"}

    async with test_uow as uow:
        with pytest.raises(HTTPException) as exc_info:
            await uow.task_repo.update_one(1, task_data)

        assert exc_info.value.status_code == http_status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "id, title, description, status",
    (
        [None, "task1", "descr", "created"],
        [None, "task2", "descr", "created"],
        [None, "task1", "descr2", "created"],
        [None, "task1", "descr", "updated"],
        [None, "task2", "descr2", "updated"],
        [None, None, None, "assigned"],
        [None, "task2", None, None],
        [None, None, None, None],
        [2, None, None, None],
    ),
)
async def test_task_repo_update(test_uow, id, title, description, status):
    task_data = {"title": "task1", "description": "descr", "status": "created"}
    new_task_data = {
        k: v
        for k, v in [
            ("id", id),
            ("title", title),
            ("description", description),
            ("status", status),
        ]
        if v is not None
    }
    task_id = 1 if id is None else id

    async with test_uow as uow:
        await uow.task_repo.add_one(task_data)
        await uow.commit()

    async with test_uow as uow:
        await uow.task_repo.update_one(1, new_task_data)
        await uow.commit()

    async with test_uow as uow:
        updated_task = await uow.task_repo.find_one(id=task_id)

        assert all(getattr(updated_task, field) == value for field, value in new_task_data.items())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "title, description, status, wrong_field",
    (
        [2, None, None, None],
        [None, 2, None, None],
        [None, None, 2, None],
        [None, None, None, 2],
    ),
)
async def test_task_repo_update_wrong_data(test_uow, title, description, status, wrong_field):
    task_data = {"title": "task1", "description": "descr", "status": "created"}
    new_task_data = {
        k: v
        for k, v in [
            ("title", title),
            ("description", description),
            ("status", status),
            ("wrong_field", wrong_field),
        ]
        if v is not None
    }
    db_exceptions = (DBAPIError, HTTPException)

    async with test_uow as uow:
        await uow.task_repo.add_one(task_data)
        await uow.commit()

    async with test_uow as uow:
        with pytest.raises(db_exceptions) as exc_info:
            await uow.task_repo.update_one(1, new_task_data)
            await uow.commit()

        assert exc_info.type in db_exceptions


@pytest.mark.asyncio
async def test_task_repo_remove(test_uow):
    task_data = {"title": "task1", "description": "descr", "status": "created"}
    async with test_uow as uow:
        await uow.task_repo.add_one(task_data)
        await uow.commit()
        added_task = await uow.task_repo.find_one(id=1)
        assert added_task.title == "task1"

    async with test_uow as uow:
        await uow.task_repo.remove_one(1)
        await uow.commit()

    async with test_uow as uow:
        with pytest.raises(HTTPException) as exc_info:
            await uow.task_repo.remove_one(1)

        assert exc_info.value.status_code == http_status.HTTP_404_NOT_FOUND
