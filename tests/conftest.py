from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend import models
from backend.dependencies import get_db
from backend.routers.auth import router as auth_router
from backend.routers.projects import router as projects_router

TEST_DB_PATH = Path("tests") / "test_app.db"
TEST_DB_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH.as_posix()}"


@pytest_asyncio.fixture(scope="session")
async def engine():
    TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()

    test_engine = create_async_engine(TEST_DB_URL, future=True)
    async with test_engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    yield test_engine

    await test_engine.dispose()
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest.fixture(scope="session")
def session_maker(engine):
    return async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def clean_db(session_maker):
    async with session_maker() as session:
        await session.execute(delete(models.UserProject))
        await session.execute(delete(models.Project))
        await session.execute(delete(models.User))
        await session.commit()


@pytest.fixture(scope="session")
def app(session_maker):
    application = FastAPI()
    application.include_router(auth_router)
    application.include_router(projects_router)

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_maker() as session:
            yield session

    application.dependency_overrides[get_db] = override_get_db
    return application


@pytest.fixture()
def client(app):
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture()
def authorized_client(client):
    client.post('/api/auth/register', json={"login": "test_login", "password": "password"})
    client.post('/api/auth/login', json={"login": "test_login", "password": "password"})
    return client

@pytest.fixture()
def create_authorized_client(app):
    def _create_user(login):
        new_client = TestClient(app)
        user_data = {"login": login, "password": "password"}
        new_client.post('/api/auth/register', json = user_data)
        new_client.post('/api/auth/login', json = user_data)
        return new_client
    return _create_user

