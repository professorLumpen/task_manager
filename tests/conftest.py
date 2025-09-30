from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.schemas.common import TaskWithUsers, UserWithTasks
from app.api.schemas.task import TaskFromDB
from app.api.schemas.user import UserFromDB
from app.core.config import settings
from app.core.dependencies import get_current_user
from app.db.database import Base
from app.services.task_service import TaskService, get_task_service
from app.services.user_service import UserService, get_user_service
from app.utils.unit_of_work import UnitOfWork
from main import app


@pytest.fixture
async def test_engine():
    engine = create_async_engine(settings.TEST_DATABASE_URL)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def test_session(test_engine):
    test_session_maker = async_sessionmaker(test_engine, class_=AsyncSession)

    async with test_session_maker() as session:
        yield session


@pytest.fixture
async def test_uow(test_engine):
    test_session_maker = async_sessionmaker(test_engine)
    uow = UnitOfWork(test_session_maker)
    yield uow


@pytest.fixture
def task_data():
    return {"title": "task1", "description": "descr", "status": "created"}


@pytest.fixture
def task_from_db(task_data):
    db_data = task_data.copy()
    db_data.update({"id": 1, "completed_at": None, "created_at": datetime.now()})
    task = TaskFromDB(**db_data)
    return task


@pytest.fixture
def task_with_users(task_data):
    db_data = task_data.copy()
    db_data.update({"id": 1, "completed_at": None, "created_at": datetime.now(), "users": []})
    task = TaskWithUsers(**db_data)
    return task


@pytest.fixture
def user_data():
    return {"username": "user1", "password": "password", "roles": ["user"]}


@pytest.fixture
def user_from_db(user_data):
    db_data = user_data.copy()
    db_data.update({"id": 1})
    user = UserFromDB(**db_data)
    return user


@pytest.fixture
def user_with_tasks(user_data):
    db_data = user_data.copy()
    db_data.update({"id": 1, "tasks": []})
    user = UserWithTasks(**db_data)
    return user


@pytest.fixture
def user_with_password(user_data):
    db_data = user_data.copy()
    db_data.update({"id": 1, "tasks": []})

    user = MagicMock()
    [setattr(user, key, val) for key, val in user_data.items()]
    return user


@pytest.fixture
def mock_task_repo():
    repo = AsyncMock()
    repo.add_one = AsyncMock()
    repo.find_one = AsyncMock()
    repo.find_all = AsyncMock()
    repo.update_one = AsyncMock()
    repo.remove_one = AsyncMock()
    return repo


@pytest.fixture
def mock_user_repo():
    repo = AsyncMock()
    repo.add_one = AsyncMock()
    repo.find_one = AsyncMock()
    repo.find_all = AsyncMock()
    repo.update_one = AsyncMock()
    repo.remove_one = AsyncMock()
    return repo


class AsyncContextManagerMock:
    def __init__(self, uow):
        self.uow = uow

    async def __aenter__(self):
        return self.uow

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False


@pytest.fixture
def mock_uow(mock_task_repo, mock_user_repo):
    uow = AsyncMock()
    uow.task_repo = mock_task_repo
    uow.user_repo = mock_user_repo
    uow.commit = AsyncMock()
    return AsyncContextManagerMock(uow)


@pytest.fixture
def mock_ws_manager():
    ws_manager = AsyncMock()
    ws_manager.broadcast = AsyncMock()
    return ws_manager


@pytest.fixture
def task_service(mock_uow, mock_ws_manager):
    return TaskService(mock_uow, mock_ws_manager)


@pytest.fixture
def user_service(mock_uow):
    return UserService(mock_uow)


@pytest.fixture
def mock_task_service():
    task_service = AsyncMock()
    task_service.get_tasks = AsyncMock(return_value=[])
    task_service.get_task = AsyncMock()
    task_service.create_task = AsyncMock()
    task_service.delete_task = AsyncMock()
    task_service.update_task = AsyncMock()
    task_service.assign_task = AsyncMock()
    task_service.unassign_task = AsyncMock()
    return task_service


@pytest.fixture
def mock_user_service():
    user_service = AsyncMock()
    user_service.get_users = AsyncMock(return_value=[])
    user_service.get_user = AsyncMock()
    user_service.create_user = AsyncMock()
    user_service.delete_user = AsyncMock()
    user_service.update_user = AsyncMock()
    user_service.login_user = AsyncMock()
    return user_service


@pytest.fixture
async def mock_app(mock_user_service, mock_task_service, user_with_password):
    async def get_test_user_service():
        yield mock_user_service

    async def get_test_task_service():
        yield mock_task_service

    async def get_test_admin():
        user_with_password.roles.append("admin")
        yield user_with_password

    app.dependency_overrides[get_user_service] = get_test_user_service
    app.dependency_overrides[get_task_service] = get_test_task_service
    app.dependency_overrides[get_current_user] = get_test_admin
    yield app


@pytest.fixture
async def async_mock_client(mock_app):
    transport = ASGITransport(app=mock_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
