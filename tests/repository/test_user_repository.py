import pytest
from uuid import uuid4

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from src.repository.user_repository import UserRepository
from src.schemas.user import UserCreate
from src.entity.models import User

# Fixture for creating async session
@pytest_asyncio.fixture()
async def async_session(async_engine):
    async_session = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    async with async_session() as session:
        yield session

# Create async_engine for tests
@pytest_asyncio.fixture()
async def async_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///./test.db",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    yield engine
    await engine.dispose()

# Database preparation before tests
@pytest_asyncio.fixture(autouse=True)
async def prepare_database(async_engine):
    async with async_engine.begin() as conn:
        await conn.run_sync(User.metadata.create_all)

# Fixture for creating user
@pytest.fixture
def user_data():
    return UserCreate(
        username=f"testuser{uuid4()}",  # Generate unique username
        email=f"testuser{uuid4()}@example.com",  # Generate unique email
        password="password123",
    )

# Fixture for user repository
@pytest.fixture
def user_repo(async_session: AsyncSession):
    return UserRepository(async_session)


@pytest.mark.asyncio
async def test_create_user(user_repo, user_data):
    hashed_password = "hashedpassword"
    avatar = "http://example.com/avatar.png"
    user = await user_repo.create_user(user_data, hashed_password, avatar)

    assert user.id is not None
    assert user.username == user_data.username  # Check username uniqueness
    assert user.email == user_data.email  # Check email uniqueness
    assert user.hash_password == hashed_password
    assert user.avatar == avatar
    assert user.role.value == "user"


@pytest.mark.asyncio
async def test_get_user_by_email(user_repo, user_data):
    hashed_password = "hashedpassword"
    avatar = "http://example.com/avatar.png"
    user = await user_repo.create_user(user_data, hashed_password, avatar)

    found_user = await user_repo.get_user_by_email(user.email)

    assert found_user is not None
    assert found_user.email == user.email


@pytest.mark.asyncio
async def test_get_user_by_username(user_repo, user_data):
    hashed_password = "hashedpassword"
    avatar = "http://example.com/avatar.png"
    user = await user_repo.create_user(user_data, hashed_password, avatar)

    found_user = await user_repo.get_by_username(user.username)

    assert found_user is not None
    assert found_user.username == user.username


@pytest.mark.asyncio
async def test_update_avatar(user_repo, user_data):
    hashed_password = "hashedpassword"
    avatar = "http://example.com/avatar.png"
    user = await user_repo.create_user(user_data, hashed_password, avatar)

    new_avatar = "http://example.com/new-avatar.png"
    updated_user = await user_repo.update_avatar_url(user.email, new_avatar)

    assert updated_user.avatar == new_avatar


@pytest.mark.asyncio
async def test_update_password(user_repo, user_data):
    hashed_password = "hashedpassword"
    avatar = "http://example.com/avatar.png"
    user = await user_repo.create_user(user_data, hashed_password, avatar)

    new_hashed_password = "newhashedpassword"
    await user_repo.update_password(user.email, new_hashed_password)

    updated_user = await user_repo.get_user_by_email(user.email)
    assert updated_user.hash_password == new_hashed_password


@pytest.mark.asyncio
async def test_confirm_email(user_repo, user_data):
    hashed_password = "hashedpassword"
    avatar = "http://example.com/avatar.png"
    user = await user_repo.create_user(user_data, hashed_password, avatar)

    await user_repo.confirmed_email(user.email)

    updated_user = await user_repo.get_user_by_email(user.email)
    assert updated_user.confirmed is True

# Run this test with:
# pytest tests/repository/test_user_repository.py
