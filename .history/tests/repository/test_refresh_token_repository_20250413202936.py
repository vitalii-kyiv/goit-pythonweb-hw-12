import pytest
from datetime import datetime, timedelta
from uuid import uuid4

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from src.entity.models import RefreshToken
from src.repository.refresh_token_repository import RefreshTokenRepository

# Фікстура для створення асинхронної сесії
@pytest_asyncio.fixture()
async def async_session(async_engine):
    async_session = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    async with async_session() as session:
        yield session

# Створення async_engine
@pytest_asyncio.fixture()
async def async_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///./test.db",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    yield engine
    await engine.dispose()

# Підготовка бази даних
@pytest_asyncio.fixture(autouse=True)
async def prepare_database(async_engine):
    async with async_engine.begin() as conn:
        await conn.run_sync(RefreshToken.metadata.create_all)

# Тести
@pytest.mark.asyncio
async def test_save_and_get_token(async_session):
    repo = RefreshTokenRepository(async_session)
    now = datetime.utcnow()
    token_hash = f"hash-{uuid4()}"  # Унікальний хеш токена

    token = await repo.save_token(
        user_id=1,
        token_hash=token_hash,
        expired_at=now + timedelta(days=7),
        ip_address="127.0.0.1",
        user_agent="pytest-agent"
    )

    assert token.id is not None
    assert token.token_hash == token_hash


@pytest.mark.asyncio
async def test_get_by_token_hash(async_session):
    repo = RefreshTokenRepository(async_session)
    token_hash = f"hash-{uuid4()}"
    now = datetime.utcnow()

    await repo.save_token(
        user_id=1,
        token_hash=token_hash,
        expired_at=now + timedelta(days=7),
        ip_address="127.0.0.1",
        user_agent="pytest-agent"
    )

    token = await repo.get_by_token_hash(token_hash)
    assert token is not None
    assert token.token_hash == token_hash


@pytest.mark.asyncio
async def test_get_active_token(async_session):
    repo = RefreshTokenRepository(async_session)
    token_hash = f"hash-{uuid4()}"
    now = datetime.utcnow()

    await repo.save_token(
        user_id=1,
        token_hash=token_hash,
        expired_at=now + timedelta(days=7),
        ip_address="127.0.0.1",
        user_agent="pytest-agent"
    )

    token = await repo.get_active_token(token_hash, now)
    assert token is not None
    assert token.token_hash == token_hash


@pytest.mark.asyncio
async def test_revoke_token(async_session):
    repo = RefreshTokenRepository(async_session)
    token_hash = f"hash-{uuid4()}"
    now = datetime.utcnow()

    token = await repo.save_token(
        user_id=1,
        token_hash=token_hash,
        expired_at=now + timedelta(days=7),
        ip_address="127.0.0.1",
        user_agent="pytest-agent"
    )

    await repo.revoke_token(token)

    revoked = await repo.get_by_token_hash(token_hash)
    assert revoked.revoked_at is not None


# Run this test with:
# pytest tests/repository/test_refresh_token_repository.py
