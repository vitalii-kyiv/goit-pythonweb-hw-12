import logging
from datetime import datetime
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import RefreshToken
from src.repository.base import BaseRepository
from src.schemas.user import UserCreate

logger = logging.getLogger("uvicorn.error")


class RefreshTokenRepository(BaseRepository):
    """
    Repository for managing refresh token records in the database.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize the repository with the current database session.

        :param session: Async SQLAlchemy session
        """
        super().__init__(session, RefreshToken)

    async def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        """
        Retrieve a refresh token record by its hash.

        :param token_hash: Hashed refresh token
        :return: RefreshToken instance or None if not found
        """
        stmt = select(self.model).where(RefreshToken.token_hash == token_hash)
        token = await self.db.execute(stmt)
        return token.scalars().first()

    async def get_active_token(
        self, token_hash: str, current_time: datetime
    ) -> RefreshToken | None:
        """
        Retrieve an active (non-expired and non-revoked) refresh token.

        :param token_hash: Hashed refresh token
        :param current_time: Current timestamp for expiration comparison
        :return: Active RefreshToken or None
        """
        stmt = select(self.model).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.expired_at > current_time,
            RefreshToken.revoked_at.is_(None),
        )
        token = await self.db.execute(stmt)
        return token.scalars().first()

    async def save_token(
        self,
        user_id: int,
        token_hash: str,
        expired_at: datetime,
        ip_address: str,
        user_agent: str,
    ) -> RefreshToken:
        """
        Save a new refresh token in the database.

        :param user_id: ID of the user
        :param token_hash: Hashed token string
        :param expired_at: Expiration datetime
        :param ip_address: IP address from which the token was issued
        :param user_agent: User agent string of the client
        :return: Created RefreshToken instance
        """
        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expired_at=expired_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return await self.create(refresh_token)

    async def revoke_token(self, refresh_token: RefreshToken) -> None:
        """
        Revoke a refresh token by setting the revoked_at field.

        :param refresh_token: RefreshToken instance to revoke
        """
        refresh_token.revoked_at = datetime.now()
        await self.db.commit()
