import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.database import Base, get_session
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
async def test_app(test_session):
    async def get_test_session():
        yield test_session

    app.dependency_overrides[get_session] = get_test_session
    yield app


@pytest.fixture
async def async_client(test_app):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
