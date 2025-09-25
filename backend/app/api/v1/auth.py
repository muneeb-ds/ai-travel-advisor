"""
Authentication API endpoints for user signup, login, logout and token refresh.
"""

import logging

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import get_auth_service, get_current_active_user
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    OrgUserCreateRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserLoginRequest,
    UserResponse,
)
from app.services.auth import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="User Registration",
)
async def signup(
    signup_data: OrgUserCreateRequest, 
    auth_service: AuthService = Depends(get_auth_service)
) -> AuthResponse:
    """
    Register a new user and create an organization for them.
    The first user in an organization becomes an ADMIN.
    """
    return await auth_service.signup(signup_data)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User Login",
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), auth_service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    """
    Authenticate a user with email and password (form data).
    """
    login_data = UserLoginRequest(email=form_data.username, password=form_data.password)
    return await auth_service.login(login_data)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh Access Token",
)
async def refresh_token(
    refresh_data: RefreshTokenRequest, auth_service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    """
    Generate a new access token using a valid refresh token.
    This process uses token rotation.
    """
    return await auth_service.refresh_access_token(refresh_data.refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="User Logout",
)
async def logout(
    refresh_data: RefreshTokenRequest, 
    _current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> None:
    """
    Logs out the user by revoking their refresh token.
    """
    await auth_service.logout(refresh_data.refresh_token)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get Current User",
)
async def get_me(current_user: User = Depends(get_current_active_user)) -> UserResponse:
    """
    Get current authenticated user's information.
    """
    return UserResponse.from_orm(current_user)
