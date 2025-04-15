from datetime import datetime
from typing import Optional
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, EmailStr


class RoleEnum(str, Enum):
    """
    Enum representing available user roles.
    """
    user = "user"
    admin = "admin"


class UserBase(BaseModel):
    """
    Base schema for user data.
    """
    username: str = Field(min_length=2, max_length=50, description="Username")
    email: EmailStr


class UserCreate(UserBase):
    """
    Schema for creating a new user.
    """
    password: str = Field(min_length=6, max_length=12, description="Password")


class UserResponse(UserBase):
    """
    Schema for returning user data in responses.
    """
    id: int
    avatar: Optional[str]
    role: RoleEnum
    model_config = ConfigDict(from_attributes=True)
