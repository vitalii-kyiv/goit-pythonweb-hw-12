from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict, EmailStr


class ContactCreateSchema(BaseModel):
    """
    Schema for creating a new contact.
    """
    first_name: str = Field(min_length=2, max_length=50, description="Contact's first name")
    last_name: str = Field(min_length=2, max_length=50, description="Contact's last name")
    email: EmailStr = Field(description="Contact's email address")
    phone_number: str = Field(min_length=5, max_length=20, description="Contact's phone number")
    birthday: date = Field(description="Contact's birthday")
    additional_info: Optional[str] = Field(
        default=None, max_length=255, description="Additional information"
    )


class ContactUpdateSchema(BaseModel):
    """
    Schema for updating an existing contact.
    """
    first_name: Optional[str] = Field(None, min_length=2, max_length=50)
    last_name: Optional[str] = Field(None, min_length=2, max_length=50)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, min_length=5, max_length=20)
    birthday: Optional[date] = None
    additional_info: Optional[str] = Field(None, max_length=255)


class ContactResponseSchema(BaseModel):
    """
    Schema for returning contact information in responses.
    """
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    birthday: date
    additional_info: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
