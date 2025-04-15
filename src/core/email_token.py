from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, status

from src.conf.config import settings


def create_email_token(data: dict) -> str:
    """
    Create a JWT token for email verification.

    Args:
        data (dict): Data to include in the token payload.

    Returns:
        str: Encoded JWT token.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({"iat": datetime.now(timezone.utc), "exp": expire})
    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token


def get_email_from_token(token: str) -> str:
    """
    Decode the JWT token and extract the email from the 'sub' claim.

    Args:
        token (str): JWT token.

    Returns:
        str: Email address extracted from the token.

    Raises:
        HTTPException: If the token is invalid or expired.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        email = payload["sub"]
        return email
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid email verification token",
        )
