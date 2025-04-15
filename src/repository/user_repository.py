import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import User
from src.repository.base import BaseRepository
from src.schemas.user import UserCreate

logger = logging.getLogger("uvicorn.error")


class UserRepository(BaseRepository):
    """
    Repository for managing User entities in the database.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize the repository with a database session and bind the User model.

        :param session: Async SQLAlchemy session
        """
        super().__init__(session, User)

    async def get_by_username(self, username: str) -> User | None:
        """
        Retrieve a user by username.

        :param username: Username string
        :return: User instance or None if not found
        """
        stmt = select(self.model).where(self.model.username == username)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        """
        Retrieve a user by email address.

        :param email: Email string
        :return: User instance or None if not found
        """
        stmt = select(self.model).where(self.model.email == email)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def create_user(
        self,
        user_data: UserCreate,
        hashed_password: str,
        avatar: str,
        role: str = "user"
    ) -> User:
        """
        Create and save a new user to the database.

        :param user_data: UserCreate schema containing user input
        :param hashed_password: Hashed password string
        :param avatar: Avatar URL string
        :param role: User role ('user' or 'admin')
        :return: Created User instance
        """
        user = User(
            **user_data.model_dump(exclude_unset=True, exclude={"password"}),
            hash_password=hashed_password,
            avatar=avatar,
            role=role
        )
        return await self.create(user)

    async def confirmed_email(self, email: str) -> None:
        """
        Mark the user's email as confirmed.

        :param email: Email of the user to update
        """
        user = await self.get_user_by_email(email)
        user.confirmed = True
        await self.db.commit()

    async def update_avatar_url(self, email: str, url: str) -> User:
        """
        Update the avatar URL for a given user.

        :param email: Email of the user
        :param url: New avatar URL
        :return: Updated User instance
        """
        user = await self.get_user_by_email(email)
        user.avatar = url
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_password(self, email: str, hashed_password: str) -> None:
        """
        Update the user's password.

        :param email: Email of the user
        :param hashed_password: New hashed password
        """
        user = await self.get_user_by_email(email)
        if not user:
            return
        user.hash_password = hashed_password
        await self.db.commit()
