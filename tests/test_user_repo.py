import pytest
from fastapi import HTTPException, status
from sqlalchemy.exc import DBAPIError, IntegrityError, ProgrammingError

from app.repositories.user_repository import UserRepository


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "id, username, password, roles",
    (
        [None, "user1", "password", ["user"]],
        [1, "user1", "password", ["user"]],
    ),
)
async def test_user_repo_add_one(test_session, id, username, password, roles):
    test_user_repo = UserRepository(test_session)
    user_data = {
        k: v for k, v in [("id", id), ("username", username), ("password", password), ("roles", roles)] if v is not None
    }

    user = await test_user_repo.add_one(user_data)

    assert user.id == 1
    assert all(getattr(user, field) == value for field, value in user_data.items())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "id, username, password, roles, wrong_field",
    (
        [None, None, "password", ["user"], None],
        [None, "user1", None, ["user"], None],
        [None, "user1", "password", None, None],
        [None, "user1", "password", ["user"], "wrong_val"],
        [None, 1, "password", ["user"], None],
        [None, "user1", 1, ["user"], None],
        [None, "user1", "password", 1, None],
        ["23", "user1", "password", ["user"], None],
    ),
)
async def test_user_repo_add_one_wrong_data(test_uow, id, username, password, roles, wrong_field):
    user_data = {
        k: v
        for k, v in (
            ("id", id),
            ("username", username),
            ("password", password),
            ("roles", roles),
            ("wrong_field", wrong_field),
        )
        if v is not None
    }
    db_exceptions = (IntegrityError, ProgrammingError, AttributeError, DBAPIError)

    async with test_uow as uow:
        with pytest.raises(db_exceptions) as exc_info:
            await uow.user_repo.add_one(user_data)
            await uow.commit()

    assert exc_info.type in db_exceptions


@pytest.mark.asyncio
async def test_user_repo_already_exists(test_uow, user_data):
    async with test_uow as uow:
        await uow.user_repo.add_one(user_data)
        await uow.commit()

    async with test_uow as uow:
        with pytest.raises(HTTPException) as exc_info:
            await uow.user_repo.add_one(user_data)

    assert exc_info.value.status_code == status.HTTP_409_CONFLICT
    assert exc_info.value.detail == "Already exists"


@pytest.mark.asyncio
async def test_user_repo_find_all(test_uow, user_data):
    async with test_uow as uow:
        empty_users = await uow.user_repo.find_all()
        await uow.user_repo.add_one(user_data)
        await uow.commit()
        users = await uow.user_repo.find_all()

        assert empty_users == []
        assert len(users) == 1
        assert all(getattr(users[0], field) == value for field, value in user_data.items())


@pytest.mark.asyncio
async def test_user_repo_find_one(test_uow, user_data):
    async with test_uow as uow:
        await uow.user_repo.add_one(user_data)
        await uow.commit()

    async with test_uow as uow:
        found_user = await uow.user_repo.find_one(id=1)
        assert found_user.id == 1
        assert all(getattr(found_user, field) == value for field, value in user_data.items())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "id, username, password, roles",
    (
        [1, None, None, None],
        [None, "user1", None, None],
        [None, None, None, ["user"]],
        [1, None, 1, None],
        [1, None, None, ["user"]],
        [1, "user1", "password", None],
        [1, "user1", "password", ["user"]],
    ),
)
async def test_user_repo_find_one_parameters(test_uow, user_data, id, username, password, roles):
    search_data = {
        k: v for k, v in (("id", id), ("username", username), ("password", password), ("roles", roles)) if v is not None
    }

    async with test_uow as uow:
        await uow.user_repo.add_one(user_data)
        await uow.commit()

        found_user = await uow.user_repo.find_one(**search_data)

        assert found_user.id == 1
        assert all(getattr(found_user, field) == value for field, value in user_data.items())


@pytest.mark.asyncio
async def test_user_repo_find_one_password_removing(test_uow, user_data):
    new_user_data = user_data.copy()
    new_user_data["password"] = "wrong password"

    async with test_uow as uow:
        await uow.user_repo.add_one(user_data)
        await uow.commit()

    async with test_uow as uow:
        user1 = await uow.user_repo.find_one(**user_data)
        user2 = await uow.user_repo.find_one(**new_user_data)

        assert user1 == user2
        assert user2.password != new_user_data["password"]
        assert user2.password == user_data["password"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "id, username, password, roles",
    (
        [2, None, None, None],
        [None, "user2", None, None],
        [None, None, None, ["admin"]],
        [1, None, None, ["admin"]],
        [1, "user1", 1, ["admin"]],
    ),
)
async def test_user_repo_not_found(test_uow, user_data, id, username, password, roles):
    search_data = {
        k: v for k, v in (("id", id), ("username", username), ("password", password), ("roles", roles)) if v is not None
    }

    async with test_uow as uow:
        await uow.user_repo.add_one(user_data)
        await uow.commit()
        found_user = await uow.user_repo.find_one(**user_data)
        assert found_user.id == 1

    async with test_uow as uow:
        with pytest.raises(HTTPException) as exc_info:
            await uow.user_repo.find_one(**search_data)

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "Not Found"


@pytest.mark.asyncio
async def test_user_repo_commit(test_uow, user_data):
    async with test_uow as uow:
        await uow.user_repo.add_one(user_data)

    async with test_uow as uow:
        with pytest.raises(HTTPException) as exc_info:
            await uow.user_repo.find_one(id=1)

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "Not Found"


@pytest.mark.asyncio
async def test_user_repo_rollback(test_uow, user_data):
    async with test_uow as uow:
        await uow.user_repo.add_one(user_data)
        user = await uow.user_repo.find_one(id=1)
        assert user is not None

        await uow.rollback()

        with pytest.raises(HTTPException) as exc_info:
            await uow.user_repo.find_one(id=1)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Not Found"


@pytest.mark.asyncio
async def test_user_repo_update_not_found(test_uow, user_data):
    async with test_uow as uow:
        with pytest.raises(HTTPException) as exc_info:
            await uow.user_repo.update_one(1, user_data)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "id, username, password, roles",
    (
        [None, "user1", "password", ["user"]],
        [None, "user2", "password", ["user"]],
        [None, "user1", "password2", ["user"]],
        [None, "user1", "password", ["admin"]],
        [None, "user2", "password2", ["admin"]],
        [None, None, None, ["admin"]],
        [None, "user2", None, None],
        [None, None, None, None],
        [2, None, None, None],
    ),
)
async def test_user_repo_update(test_uow, user_data, id, username, password, roles):
    new_user_data = {
        k: v
        for k, v in [
            ("id", id),
            ("username", username),
            ("password", password),
            ("roles", roles),
        ]
        if v is not None
    }
    user_id = 1 if id is None else id

    async with test_uow as uow:
        await uow.user_repo.add_one(user_data)
        await uow.commit()

    async with test_uow as uow:
        await uow.user_repo.update_one(1, new_user_data)
        await uow.commit()

    async with test_uow as uow:
        updated_user = await uow.user_repo.find_one(id=user_id)

        assert all(getattr(updated_user, field) == value for field, value in new_user_data.items())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "username, password, roles, wrong_field",
    (
        [2, None, None, None],
        [None, 2, None, None],
        [None, None, 2, None],
        [None, None, None, 2],
    ),
)
async def test_user_repo_update_wrong_data(test_uow, user_data, username, password, roles, wrong_field):
    new_user_data = {
        k: v
        for k, v in [
            ("username", username),
            ("password", password),
            ("roles", roles),
            ("wrong_field", wrong_field),
        ]
        if v is not None
    }
    db_exceptions = (DBAPIError, HTTPException, ValueError)

    async with test_uow as uow:
        await uow.user_repo.add_one(user_data)
        await uow.commit()

    async with test_uow as uow:
        with pytest.raises(db_exceptions) as exc_info:
            await uow.user_repo.update_one(1, new_user_data)
            await uow.commit()

        assert exc_info.type in db_exceptions


@pytest.mark.asyncio
async def test_user_repo_remove(test_uow, user_data):
    async with test_uow as uow:
        await uow.user_repo.add_one(user_data)
        await uow.commit()
        added_user = await uow.user_repo.find_one(id=1)
        assert added_user.id == 1

    async with test_uow as uow:
        await uow.user_repo.remove_one(1)
        await uow.commit()

    async with test_uow as uow:
        with pytest.raises(HTTPException) as exc_info:
            await uow.user_repo.remove_one(1)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
