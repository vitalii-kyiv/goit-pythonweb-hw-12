import logging

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.depend_service import get_user_service
from src.core.email_token import get_email_from_token
from src.database.db import get_db
from src.services.auth import AuthService, oauth2_scheme
from src.schemas.token import TokenResponse, RefreshTokenRequest
from src.schemas.user import UserResponse, UserCreate
from src.schemas.email import RequestEmail, ResetPasswordRequest
from src.services.email import send_email
from src.services.user import UserService

router = APIRouter(tags=["auth"])
logger = logging.getLogger("uvicorn.error")


def get_auth_service(db: AsyncSession = Depends(get_db)):
    """
    Dependency function to get an instance of AuthService with a database session.
    """
    return AuthService(db)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Register a new user and send confirmation email.

    :param user_data: UserCreate schema with registration info
    :param background_tasks: FastAPI background task manager
    :param request: Request object for host URL
    :param auth_service: AuthService instance
    :return: Created user data
    """
    user = await auth_service.register_user(user_data)
    background_tasks.add_task(
        send_email, user_data.email, user_data.username, str(request.base_url)
    )
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Authenticate user and generate access and refresh tokens.

    :param form_data: OAuth2PasswordRequestForm with login credentials
    :param request: Request object to get client IP and User-Agent
    :param auth_service: AuthService instance
    :return: Access and refresh tokens
    """
    user = await auth_service.authenticate(form_data.username, form_data.password)
    access_token = auth_service.create_access_token(user.username)
    refresh_token = await auth_service.create_refresh_token(
        user.id,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )
    return TokenResponse(
        access_token=access_token, token_type="bearer", refresh_token=refresh_token
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    refresh_token: RefreshTokenRequest,
    request: Request = None,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Refresh access and refresh tokens using a valid refresh token.

    :param refresh_token: RefreshTokenRequest containing refresh token
    :param request: Request object to get client IP and User-Agent
    :param auth_service: AuthService instance
    :return: New access and refresh tokens
    """
    user = await auth_service.validate_refresh_token(refresh_token.refresh_token)

    new_access_token = auth_service.create_access_token(user.username)
    new_refresh_token = await auth_service.create_refresh_token(
        user.id,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )

    await auth_service.revoke_refresh_token(refresh_token.refresh_token)

    return TokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        refresh_token=new_refresh_token,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    refresh_token: RefreshTokenRequest,
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Logout user by revoking access and refresh tokens.

    :param refresh_token: RefreshTokenRequest schema
    :param token: Bearer token from authorization header
    :param auth_service: AuthService instance
    """
    await auth_service.revoke_access_token(token)
    await auth_service.revoke_refresh_token(refresh_token.refresh_token)
    return None


@router.post("/request-reset-password")
async def request_reset_password(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service),
):
    """
    Request a password reset link via email.

    :param body: RequestEmail schema with user's email
    :param background_tasks: FastAPI background task manager
    :param request: Request object for base URL
    :param auth_service: AuthService instance
    :param user_service: UserService instance
    :return: Message about the reset process
    """
    user = await user_service.get_user_by_email(str(body.email))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    background_tasks.add_task(
        auth_service.send_password_reset_email,
        user.email,
        str(request.base_url),
    )
    return {"message": "Check your email for instructions to reset your password."}


@router.post("/reset-password")
async def reset_password(
    body: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Reset user password using a valid token.

    :param body: ResetPasswordRequest containing token and new password
    :param auth_service: AuthService instance
    :return: Confirmation message
    """
    await auth_service.reset_password(body.token, body.new_password)
    return {"message": "Password successfully changed."}


@router.get("/reset_password/{token}")
async def verify_reset_password_token(token: str):
    """
    Validate a password reset token.

    :param token: Token string to verify
    :return: Email and success message if valid
    """
    try:
        email = get_email_from_token(token)
        return {"message": "Token is valid", "email": email}
    except HTTPException:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
