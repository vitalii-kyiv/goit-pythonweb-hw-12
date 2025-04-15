import asyncio

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from main import app
from src.entity.models import Base, User, Role  # Додано імпорт Role
from src.database.db import get_db
from src.services.auth import AuthService

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, expire_on_commit=False, bind=engine
)

test_user = {
    "username": "deadpool",
    "email": "deadpool@example.com",
    "password": "12345678",
}

@pytest.fixture(scope="module", autouse=True)
def init_models_wrap():
    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        async with TestingSessionLocal() as session:
            auth_service = AuthService(session)
            hash_password = auth_service._hash_password(test_user["password"])  # noqa
            current_user = User(
                username=test_user["username"],
                email=test_user["email"],
                hash_password=hash_password,
                confirmed=True,
                avatar="https://twitter.com/gravatar",
                role=Role.admin,  # Змінено з UserRole.ADMIN на Role.admin
            )
            session.add(current_user)
            await session.commit()

    asyncio.run(init_models())

# Решта коду без змін
@pytest.fixture(scope="module")
def client():
    async def override_get_db():
        async with TestingSessionLocal() as session:
            try:
                yield session
            except Exception as err:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)

@pytest_asyncio.fixture()
async def get_token():
    async with TestingSessionLocal() as session:
        auth_service = AuthService(session)
        token = auth_service.create_access_token(test_user["username"])
    return token