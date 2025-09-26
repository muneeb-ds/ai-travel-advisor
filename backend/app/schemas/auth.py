"""
Authentication schemas for request/response validation.
"""

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class OrgUserCreateRequest(BaseModel):
    """Schema for user creation request."""

    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Password must be at least 8 characters",
    )
    org_name: str = Field(..., description="Organization name")


class UserCreateRequest(BaseModel):
    """Schema for user creation request."""

    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Password must be at least 8 characters",
    )
    role: str = Field(default=UserRole.MEMBER.value, description="User role")


class UserLoginRequest(BaseModel):
    """Schema for user login request."""

    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


class TokenResponse(BaseModel):
    """Schema for token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserResponse(BaseModel):
    """Schema for user response data."""

    id: UUID
    email: EmailStr
    role: str
    org_id: UUID
    is_active: bool

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    """Schema for authentication response."""

    user: UserResponse
    tokens: TokenResponse


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""

    refresh_token: str


class ErrorResponse(BaseModel):
    """Schema for error responses."""

    detail: str
