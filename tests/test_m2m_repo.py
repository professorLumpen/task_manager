import pytest
from sqlalchemy.exc import IntegrityError


async def create_task_and_user(uow, task_data, user_data):
    async with uow as u:
        await u.task_repo.add_one(task_data)
        await u.user_repo.add_one(user_data)
        await u.commit()


async def add_task_to_user(uow, task_id=1, user_id=1):
    async with uow as u:
        task = await u.task_repo.find_one(id=task_id)
        user = await u.user_repo.find_one(id=user_id)
        user.tasks.append(task)
        await u.commit()


async def add_user_to_task(uow, task_id=1, user_id=1):
    async with uow as u:
        task = await u.task_repo.find_one(id=task_id)
        user = await u.user_repo.find_one(id=user_id)
        task.users.append(user)
        await u.commit()


@pytest.mark.asyncio
async def test_repos_user_add_task(test_uow, task_data, user_data):
    await create_task_and_user(test_uow, task_data, user_data)
    await add_task_to_user(test_uow)

    async with test_uow as uow:
        task = await uow.task_repo.find_one(id=1)
        user = await uow.user_repo.find_one(id=1)

        assert task in user.tasks
        assert user in task.users


@pytest.mark.asyncio
async def test_repos_user_add_task_already_assigned(test_uow, task_data, user_data):
    exc_type = IntegrityError

    await create_task_and_user(test_uow, task_data, user_data)

    async with test_uow as uow:
        task = await uow.task_repo.find_one(id=1)
        user = await uow.user_repo.find_one(id=1)
        with pytest.raises(exc_type) as exc_info:
            user.tasks.extend([task, task])
            await uow.commit()

    assert exc_info.type is exc_type
    assert "уже существует" in exc_info.value.args[0]


@pytest.mark.asyncio
async def test_repos_user_delete_task(test_uow, task_data, user_data):
    await create_task_and_user(test_uow, task_data, user_data)
    await add_task_to_user(test_uow)

    async with test_uow as uow:
        task = await uow.task_repo.find_one(id=1)
        user = await uow.user_repo.find_one(id=1)
        user.tasks.remove(task)
        await uow.commit()

    async with test_uow as uow:
        task = await uow.task_repo.find_one(id=1)
        user = await uow.user_repo.find_one(id=1)

        assert task not in user.tasks
        assert user not in task.users


@pytest.mark.asyncio
async def test_repos_user_delete_task_not_assigned(test_uow, task_data, user_data):
    exc_type = ValueError

    await create_task_and_user(test_uow, task_data, user_data)

    async with test_uow as uow:
        task = await uow.task_repo.find_one(id=1)
        user = await uow.user_repo.find_one(id=1)
        with pytest.raises(exc_type) as exc_info:
            user.tasks.remove(task)
            await uow.commit()

    assert exc_info.type is exc_type
    assert "not in" in exc_info.value.args[0]


@pytest.mark.asyncio
async def test_repos_task_add_user(test_uow, task_data, user_data):
    await create_task_and_user(test_uow, task_data, user_data)
    await add_user_to_task(test_uow)

    async with test_uow as uow:
        task = await uow.task_repo.find_one(id=1)
        user = await uow.user_repo.find_one(id=1)

        assert task in user.tasks
        assert user in task.users


@pytest.mark.asyncio
async def test_repos_task_add_user_already_assigned(test_uow, task_data, user_data):
    exc_type = IntegrityError

    await create_task_and_user(test_uow, task_data, user_data)

    async with test_uow as uow:
        task = await uow.task_repo.find_one(id=1)
        user = await uow.user_repo.find_one(id=1)
        with pytest.raises(exc_type) as exc_info:
            task.users.extend([user, user])
            await uow.commit()

    assert exc_info.type is exc_type
    assert "уже существует" in exc_info.value.args[0]


@pytest.mark.asyncio
async def test_repos_task_delete_user(test_uow, task_data, user_data):
    await create_task_and_user(test_uow, task_data, user_data)
    await add_user_to_task(test_uow)

    async with test_uow as uow:
        task = await uow.task_repo.find_one(id=1)
        user = await uow.user_repo.find_one(id=1)
        task.users.remove(user)
        await uow.commit()

    async with test_uow as uow:
        task = await uow.task_repo.find_one(id=1)
        user = await uow.user_repo.find_one(id=1)

        assert task not in user.tasks
        assert user not in task.users


@pytest.mark.asyncio
async def test_repos_task_delete_user_not_assigned(test_uow, task_data, user_data):
    exc_type = ValueError

    await create_task_and_user(test_uow, task_data, user_data)

    async with test_uow as uow:
        task = await uow.task_repo.find_one(id=1)
        user = await uow.user_repo.find_one(id=1)
        with pytest.raises(exc_type) as exc_info:
            task.users.remove(user)
            await uow.commit()

    assert exc_info.type is exc_type
    assert "not in" in exc_info.value.args[0]
