import contextlib
import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

from src.conf.config import settings

logger = logging.getLogger("uvicorn.error")


class DatabaseSessionManager:
    """
    Manages the lifecycle of the asynchronous SQLAlchemy database session.
    """

    def __init__(self, url: str):
        """
        Initializes the database engine and session maker.

        Args:
            url (str): Database connection URL.
        """
        self._engine: AsyncEngine | None = create_async_engine(url)
        self._session_maker: async_sessionmaker = async_sessionmaker(
            autoflush=False, autocommit=False, bind=self._engine
        )

    @contextlib.asynccontextmanager
    async def session(self):
        """
        Asynchronous context manager for a database session.

        Yields:
            AsyncSession: An active SQLAlchemy async session.

        Raises:
            Exception: If the session is not initialized or any error occurs during use.
        """
        if self._session_maker is None:
            raise Exception("Database session is not initialized")
        session = self._session_maker()
        try:
            yield session
        except SQLAlchemyError as e:
            logger.error(f"Database error: {e}")
            await session.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            await session.rollback()
            raise
        finally:
            await session.close()


sessionmanager = DatabaseSessionManager(settings.DB_URL)


async def get_db():
    """
    Dependency function to get a database session.

    Yields:
        AsyncSession: An instance of a database session.
    """
    async with sessionmanager.session() as session:
        yield session
