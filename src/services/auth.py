from datetime import datetime, timedelta, UTC, timezone
import secrets

import jwt
import bcrypt
import hashlib
import redis.asyncio as redis
from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar

from src.database.db import sessionmanager
from src.services.caсhe_user import cache_user
from src.services.email import send_reset_password_email
from src.conf.config import settings
from src.entity.models import User
from src.repository.refresh_token_repository import RefreshTokenRepository
from src.repository.user_repository import UserRepository
from src.schemas.user import UserCreate
from src.core.email_token import get_email_from_token

redis_client = redis.from_url(settings.REDIS_URL)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

class AuthService:
    """
    Service for handling user authentication, authorization, and token management.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize AuthService with a database session.
        """
        self.db = db
        self.user_repository = UserRepository(self.db)
        self.refresh_token_repository = RefreshTokenRepository(self.db)

    def _hash_password(self, password: str) -> str:
        """
        Generate a bcrypt hash of the password.
        """
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode(), salt)
        return hashed_password.decode()

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plaintext password against a hashed one.
        """
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

    def _hash_token(self, token: str):
        """
        Hash a token using SHA-256 for secure storage.
        """
        return hashlib.sha256(token.encode()).hexdigest()

    async def authenticate(self, username: str, password: str) -> User:
        """
        Authenticate a user by username and password.
        """
        user = await self.user_repository.get_by_username(username)
        if not user:
            raise HTTPException(status_code=401, detail="Incorrect username or password")

        if not user.confirmed:
            raise HTTPException(status_code=401, detail="Email address not confirmed")

        if not self._verify_password(password, user.hash_password):
            raise HTTPException(status_code=401, detail="Incorrect username or password")

        return user

    async def register_user(self, user_data: UserCreate) -> User:
        """
        Register a new user with hashed password and gravatar avatar.
        """
        if await self.user_repository.get_by_username(user_data.username):
            raise HTTPException(status_code=409, detail="User already exists")
        if await self.user_repository.get_user_by_email(str(user_data.email)):
            raise HTTPException(status_code=409, detail="Email already exists")

        avatar = None
        try:
            g = Gravatar(user_data.email)
            avatar = g.get_image()
        except Exception as e:
            print(e)

        hashed_password = self._hash_password(user_data.password)
        user = await self.user_repository.create_user(user_data, hashed_password, avatar, role="user")
        return user

    def create_access_token(self, username: str) -> str:
        """
        Create a JWT access token for the specified username.
        """
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode = {"sub": username, "exp": expire}
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    async def create_refresh_token(self, user_id: int, ip_address: str | None, user_agent: str | None) -> str:
        """
        Create and store a refresh token for a user.
        """
        token = secrets.token_urlsafe(32)
        token_hash = self._hash_token(token)
        expired_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await self.refresh_token_repository.save_token(user_id, token_hash, expired_at, ip_address, user_agent)
        return token

    def decode_and_validate_access_token(self, token: str) -> dict:
        """
        Decode a JWT access token and validate its integrity.
        """
        try:
            return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        except jwt.PyJWTError:
            raise HTTPException(status_code=401, detail="Token wrong")

    async def get_current_user(self, token: str = Depends(oauth2_scheme)) -> User:
        """
        Retrieve the current user from the JWT token, using Redis caching.
        """
        if await redis_client.exists(f"bl:{token}"):
            raise HTTPException(status_code=401, detail="Token revoked")

        cached_user = await redis_client.get(f"user:{token}")
        if cached_user:
            from json import loads
            return User(**loads(cached_user))

        payload = self.decode_and_validate_access_token(token)
        username = payload.get("sub")
        exp = payload.get("exp")

        if not username:
            raise HTTPException(status_code=401, detail="Could not validate credentials")

        user = await self.user_repository.get_by_username(username)
        if not user:
            raise HTTPException(status_code=401, detail="Could not validate credentials")

        await cache_user(user, token, exp)
        return user

    async def validate_refresh_token(self, token: str) -> User:
        """
        Validate a refresh token and return the associated user.
        """
        token_hash = self._hash_token(token)
        refresh_token = await self.refresh_token_repository.get_active_token(token_hash, datetime.now(timezone.utc))

        if not refresh_token:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        user = await self.user_repository.get_by_id(refresh_token.user_id)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        return user

    async def revoke_refresh_token(self, token: str) -> None:
        """
        Revoke a refresh token by marking it as revoked in the database.
        """
        token_hash = self._hash_token(token)
        refresh_token = await self.refresh_token_repository.get_by_token_hash(token_hash)

        if refresh_token and not refresh_token.revoked_at:
            print("Revoking refresh token")
            await self.refresh_token_repository.revoke_token(refresh_token)

    async def revoke_access_token(self, token: str) -> None:
        """
        Revoke an access token by blacklisting it in Redis.
        """
        payload = self.decode_and_validate_access_token(token)
        exp = payload.get("exp")
        if exp:
            await redis_client.setex(
                f"bl:{token}", int(exp - datetime.now(timezone.utc).timestamp()), "1"
            )

    async def send_password_reset_email(self, email: str, host: str) -> None:
        """
        Send a password reset email to the specified email address.
        """
        async with sessionmanager.session() as session:
            user_repository = UserRepository(session)
            user = await user_repository.get_user_by_email(email)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            await send_reset_password_email(email, host)

    async def reset_password(self, token: str, new_password: str) -> None:
        """
        Reset a user's password using the token from the password reset email.
        """
        try:
            payload = self.decode_and_validate_access_token(token)
            email = payload.get("sub")
            print(f"[DEBUG] Extracted email from token: {email}")
        except HTTPException as e:
            raise e

        if not email:
            raise HTTPException(status_code=400, detail="Invalid token: no email")

        user = await self.user_repository.get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        hashed_password = self._hash_password(new_password)
        await self.user_repository.update_password(user.email, hashed_password)
