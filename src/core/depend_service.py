from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.services.auth import AuthService, oauth2_scheme
from src.services.user import UserService


def get_auth_service(db: AsyncSession = Depends(get_db)):
    """
    Dependency that provides an instance of AuthService.

    Args:
        db (AsyncSession): The database session.

    Returns:
        AuthService: An instance of the authentication service.
    """
    return AuthService(db)


def get_user_service(db: AsyncSession = Depends(get_db)):
    """
    Dependency that provides an instance of UserService.

    Args:
        db (AsyncSession): The database session.

    Returns:
        UserService: An instance of the user service.
    """
    return UserService(db)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Dependency that retrieves the currently authenticated user based on the access token.

    Args:
        token (str): Bearer access token.
        auth_service (AuthService): An instance of the authentication service.

    Returns:
        User: The currently authenticated user.
    """
    return await auth_service.get_current_user(token)
