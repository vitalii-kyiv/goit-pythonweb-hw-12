from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import User, Role
from src.repository.user_repository import UserRepository
from src.schemas.user import UserCreate
from src.services.auth import AuthService


class UserService:
    """
    Service class for user-related operations such as retrieving,
    creating, confirming, and updating user data.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize the UserService with a database session.

        Args:
            db (AsyncSession): Asynchronous SQLAlchemy session.
        """
        self.db = db
        self.user_repository = UserRepository(self.db)
        self.auth_service = AuthService(db)

    async def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user with registration logic handled by AuthService.

        Args:
            user_data (UserCreate): User creation data.

        Returns:
            User: The newly created user object.
        """
        user = await self.auth_service.register_user(user_data)
        return user

    async def get_user_by_username(self, username: str) -> User | None:
        """
        Retrieve a user by username.

        Args:
            username (str): Username to search for.

        Returns:
            Optional[User]: User object if found, otherwise None.
        """
        user = await self.user_repository.get_by_username(username)
        return user

    async def get_user_by_email(self, email: str) -> User | None:
        """
        Retrieve a user by email.

        Args:
            email (str): Email address to search for.

        Returns:
            Optional[User]: User object if found, otherwise None.
        """
        user = await self.user_repository.get_user_by_email(email)
        return user

    async def confirmed_email(self, email: str) -> None:
        """
        Mark a user's email as confirmed.

        Args:
            email (str): Email to confirm.
        """
        await self.user_repository.confirmed_email(email)

    async def update_avatar_url(self, email: str, url: str) -> User:
        """
        Update the avatar URL for a user. Only users with 'admin' role are allowed.

        Args:
            email (str): User's email address.
            url (str): New avatar URL.

        Returns:
            User: Updated user object.

        Raises:
            HTTPException: If user is not found or not an admin.
        """
        user = await self.user_repository.get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.role != Role.admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can change the default avatar."
            )

        return await self.user_repository.update_avatar_url(email, url)
