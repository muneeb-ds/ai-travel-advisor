"""
API endpoints for user management, accessible by administrators.
"""

import logging

from fastapi import APIRouter, Depends, Request, status

from app.api.dependencies import get_auth_service, require_admin
from app.core.limiter import limiter
from app.models.user import User
from app.schemas.auth import UserCreateRequest, UserResponse
from app.services.auth import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["User Management"])


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create User (Admin Only)",
)
@limiter.limit("60/minute")
async def create_user(
    request: Request,  # noqa: ARG001
    user_data: UserCreateRequest,
    admin_user: User = Depends(require_admin),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """
    Create a new user within the same organization as the administrator.
    Only users with the ADMIN role can access this endpoint.
    """
    return await auth_service.create_user(user_data, admin_user)
