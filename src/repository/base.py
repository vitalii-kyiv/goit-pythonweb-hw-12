from typing import TypeVar, Type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository:
    """
    A generic repository providing basic CRUD operations for SQLAlchemy models.
    """

    def __init__(self, session: AsyncSession, model: Type[ModelType]):
        """
        Initialize the repository with a database session and model.

        :param session: Async SQLAlchemy session
        :param model: SQLAlchemy model class
        """
        self.db = session
        self.model = model

    async def get_all(self) -> list[ModelType]:
        """
        Retrieve all instances of the model from the database.

        :return: List of model instances
        """
        stmt = select(self.model)
        todos = await self.db.execute(stmt)
        return list(todos.scalars().all())

    async def get_by_id(self, _id: int) -> ModelType | None:
        """
        Retrieve a single instance by its ID.

        :param _id: ID of the instance
        :return: Model instance or None if not found
        """
        result = await self.db.execute(select(self.model).where(self.model.id == _id))
        return result.scalars().first()

    async def create(self, instance: ModelType) -> ModelType:
        """
        Create a new instance in the database.

        :param instance: Model instance to create
        :return: Created model instance
        """
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def update(self, instance: ModelType) -> ModelType:
        """
        Update an existing instance in the database.

        :param instance: Model instance to update
        :return: Updated model instance
        """
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    async def delete(self, instance: ModelType) -> None:
        """
        Delete an instance from the database.

        :param instance: Model instance to delete
        """
        await self.db.delete(instance)
        await self.db.commit()
