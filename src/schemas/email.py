from pydantic import BaseModel, EmailStr, Field


class RequestEmail(BaseModel):
    """
    Schema for requesting an email action (e.g. password reset or verification).
    """
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """
    Schema for resetting a password using a token.
    """
    token: str
    new_password: str = Field(..., min_length=6, max_length=128, description="New password with a minimum length of 6 characters")
