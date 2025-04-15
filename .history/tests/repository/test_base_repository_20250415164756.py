import pytest
import pytest_asyncio
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from src.repository.base import BaseRepository

Base = declarative_base()

class DummyModel(Base):
    __tablename__ = "dummy"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

# Fixtures for data preparation
@pytest.fixture
def dummy_instance():
    return DummyModel(name="Test")

# Fixture for session creation
@pytest_asyncio.fixture()
async def async_session(async_engine):
    async_session = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    async with async_session() as session:
        yield session

# Fixture for repository
@pytest_asyncio.fixture
async def repo(async_session: AsyncSession):
    return BaseRepository(async_session, DummyModel)

# Create async_engine directly in tests
@pytest_asyncio.fixture()
async def async_engine():
    # Create async database connection
    engine = create_async_engine(
        "sqlite+aiosqlite:///./test.db",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool  # StaticPool is now properly imported
    )
    yield engine
    await engine.dispose()

# Database preparation
@pytest_asyncio.fixture(autouse=True)
async def prepare_database(async_engine):
    # Create tables
    async with async_engine.begin() as conn:
        await conn.run_sync(DummyModel.metadata.create_all)

@pytest.mark.asyncio
async def test_create(repo, dummy_instance):
    created = await repo.create(dummy_instance)
    assert created.id is not None
    assert created.name == "Test"

@pytest.mark.asyncio
async def test_get_all(repo, dummy_instance):
    await repo.create(dummy_instance)
    results = await repo.get_all()
    assert any(obj.name == "Test" for obj in results)

@pytest.mark.asyncio
async def test_get_by_id(repo, dummy_instance):
    created = await repo.create(dummy_instance)
    found = await repo.get_by_id(created.id)
    assert found is not None
    assert found.name == "Test"

@pytest.mark.asyncio
async def test_update(repo, dummy_instance):
    created = await repo.create(dummy_instance)
    created.name = "Updated"
    updated = await repo.update(created)
    assert updated.name == "Updated"

@pytest.mark.asyncio
async def test_delete(repo, dummy_instance):
    created = await repo.create(dummy_instance)
    await repo.delete(created)
    found = await repo.get_by_id(created.id)
    assert found is None

# Run this test with:
# pytest tests/repository/test_base_repository.py
