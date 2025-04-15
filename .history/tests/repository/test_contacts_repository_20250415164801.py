import pytest
from uuid import uuid4
from datetime import date

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from src.entity.models import Contact
from src.repository.contacts_repository import ContactRepository
from src.schemas.contact_schema import ContactCreateSchema, ContactUpdateSchema

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

# Fixtures for creating contacts
@pytest.fixture
def unique_contact_data():
    unique = str(uuid4())
    return ContactCreateSchema(
        first_name=f"John_{unique}",
        last_name="Doe",
        email=f"john{unique}@example.com",
        phone_number="123456789",
        birthday=date(1990, 1, 1),
        additional_info="Friend"
    )


@pytest.fixture
def updated_contact_data():
    return ContactUpdateSchema(
        first_name="Jane",
        phone_number="987654321"
    )


@pytest_asyncio.fixture
async def contact_repo(async_session: AsyncSession):
    return ContactRepository(async_session)


# Create async_engine directly in tests
@pytest_asyncio.fixture()
async def async_engine():
    # Create async database connection
    engine = create_async_engine(
        "sqlite+aiosqlite:///./test.db",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    yield engine
    await engine.dispose()

# Database preparation
@pytest_asyncio.fixture(autouse=True)
async def prepare_database(async_engine):
    # Create tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Contact.metadata.create_all)

# Tests
@pytest.mark.asyncio
async def test_create_contact(contact_repo, unique_contact_data):
    contact = await contact_repo.create_contact(unique_contact_data, user_id=1)
    assert contact.id is not None
    assert contact.first_name.startswith("John_")

@pytest.mark.asyncio
async def test_get_contact_by_id(contact_repo, unique_contact_data):
    created = await contact_repo.create_contact(unique_contact_data, user_id=1)
    found = await contact_repo.get_contact_by_id(created.id)
    assert found is not None
    assert found.email == unique_contact_data.email

@pytest.mark.asyncio
async def test_update_contact(contact_repo, unique_contact_data, updated_contact_data):
    created = await contact_repo.create_contact(unique_contact_data, user_id=1)
    updated = await contact_repo.update_contact(created.id, updated_contact_data)
    assert updated.first_name == "Jane"
    assert updated.phone_number == "987654321"

@pytest.mark.asyncio
async def test_remove_contact(contact_repo, unique_contact_data):
    created = await contact_repo.create_contact(unique_contact_data, user_id=1)
    removed = await contact_repo.remove_contact(created.id)
    assert removed.id == created.id
    assert await contact_repo.get_contact_by_id(created.id) is None

# Run this test with:
# pytest tests/repository/test_contacts_repository.py
