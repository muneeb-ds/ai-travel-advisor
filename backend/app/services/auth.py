"""
Authentication service for user signup, login, and token management.
"""

import hashlib
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    JWT_PRIVATE_KEY,
    JWT_PUBLIC_KEY,
    get_password_hash,
    verify_password,
)
from app.core.settings import settings
from app.core import cache
from app.models.user import User
from app.repositories.organization import OrganizationRepository
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.user import UserRepository
from app.schemas.auth import (
    AuthResponse,
    OrgUserCreateRequest,
    TokenResponse,
    UserCreateRequest,
    UserLoginRequest,
    UserResponse,
)


class AuthService:
    """Service for handling all authentication and user management operations."""

    def __init__(self, db: AsyncSession):
        """Initialize the service with database session."""
        self.db = db
        self.user_repo = UserRepository(db)
        self.org_repo = OrganizationRepository(db)
        self.refresh_token_repo = RefreshTokenRepository(db)
        self.cache = cache

    # --- Token Creation ---
    def _create_access_token(self, user: User) -> str:
        """Create a JWT access token."""
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
        to_encode = {
            "sub": str(user.id),
            "exp": expire,
            "type": "access",
            "role": user.role,
            "org_id": str(user.org_id),
        }
        return jwt.encode(
            to_encode, JWT_PRIVATE_KEY, algorithm=settings.JWT_ALGORITHM
        )

    async def _create_refresh_token(
        self, user: User, jti: str | None = None
    ) -> str:
        """Create a JWT refresh token and store its hash."""
        if jti is None:
            jti = str(uuid.uuid4())

        expire = datetime.now(UTC) + timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )
        to_encode = {"sub": str(user.id), "exp": expire, "jti": jti, "type": "refresh"}
        token = jwt.encode(
            to_encode, JWT_PRIVATE_KEY, algorithm=settings.JWT_ALGORITHM
        )

        token_hash = hashlib.sha256(token.encode()).hexdigest()
        await self.refresh_token_repo.create_refresh_token(
            user_id=user.id, jti=jti, token_hash=token_hash, expires_at=expire
        )
        return token

    async def _create_token_response(self, user: User) -> TokenResponse:
        """Create both access and refresh tokens and format response."""
        access_token = self._create_access_token(user)
        refresh_token = await self._create_refresh_token(user)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    # --- User and Auth Operations ---
    async def signup(self, signup_data: OrgUserCreateRequest) -> AuthResponse:
        """Register a new user and organization."""

        # check if user with same email already exists in another organization
        if await self.user_repo.get_user_by_email(signup_data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists in another organization",
            )

        org_name = signup_data.org_name

        organization = await self.org_repo.create_organization(name=org_name)

        hashed_password = get_password_hash(signup_data.password)
        user_data = {
            "email": signup_data.email,
            "password_hash": hashed_password,
            "org_id": organization.id,
            "role": "ADMIN",  # First user becomes admin
        }
        user = await self.user_repo.create_user(user_data)

        tokens = await self._create_token_response(user)
        return AuthResponse(user=UserResponse.model_validate(user), tokens=tokens)

    async def login(self, login_data: UserLoginRequest) -> TokenResponse:
        """Authenticate a user and return tokens."""
        user = await self.user_repo.get_user_by_email(login_data.email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive"
            )

        locked_until = await self.cache.client.get(f"locked_until:{user.id}")
        if locked_until and datetime.fromisoformat(locked_until.decode()) > datetime.now(UTC):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account locked due to too many failed login attempts.",
            )

        if not verify_password(login_data.password, user.password_hash):
            await self.increment_failed_login_attempts(user)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        await self.reset_failed_login_attempts(user)
        return await self._create_token_response(user)

    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """Verify and rotate a refresh token."""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )
        try:
            payload = jwt.decode(
                refresh_token, JWT_PUBLIC_KEY, algorithms=[settings.JWT_ALGORITHM]
            )
            user_id = payload.get("sub")
            jti = payload.get("jti")
            token_type = payload.get("type")

            if not all([user_id, jti, token_type == "refresh"]):
                raise credentials_exception

        except JWTError:
            raise credentials_exception

        stored_token = await self.refresh_token_repo.get_refresh_token_by_jti(jti)
        if not stored_token or stored_token.is_revoked:
            raise credentials_exception

        # Security: Invalidate all tokens from this user if a revoked token is used
        if stored_token.is_revoked:
            await self.refresh_token_repo.revoke_all_user_tokens(user_id)
            raise credentials_exception

        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        if token_hash != stored_token.token_hash:
            raise credentials_exception

        user = await self.user_repo.get_user_by_id(user_id)
        if not user:
            raise credentials_exception

        await self.refresh_token_repo.revoke_refresh_token(jti)
        return await self._create_token_response(user)

    async def logout(self, refresh_token: str) -> None:
        """Revoke a refresh token to log out a user."""
        try:
            payload = jwt.decode(
                refresh_token, JWT_PUBLIC_KEY, algorithms=[settings.JWT_ALGORITHM]
            )
            jti = payload.get("jti")
            if jti:
                await self.refresh_token_repo.revoke_refresh_token(jti)
        except JWTError:
            # Token is invalid anyway, so we can ignore it
            pass

    async def create_user(
        self, user_data: UserCreateRequest, admin_user: User
    ) -> UserResponse:
        """Create a new user within the admin's organization."""
        if await self.user_repo.get_user_by_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            )

        hashed_password = get_password_hash(user_data.password)
        new_user_data = {
            "email": user_data.email,
            "password_hash": hashed_password,
            "org_id": admin_user.org_id,
            "role": user_data.role,
        }
        user = await self.user_repo.create_user(new_user_data)
        return UserResponse.model_validate(user)

    # --- Login Failure and Lockout ---
    async def increment_failed_login_attempts(self, user: User) -> None:
        """Increment failed login attempts and lock account if threshold is met."""
        cache_key = f"failed_login_attempts:{user.id}"
        if await self.cache.client.get(cache_key):
            await self.cache.client.incr(cache_key, 1)
        else:
            await self.cache.client.set(cache_key, 1)

        failed_login_attempts = await self.cache.client.get(cache_key)
        if int(failed_login_attempts) >= settings.MAX_FAILED_LOGIN_ATTEMPTS:
            locked_until_cache_key = f"locked_until:{user.id}"
            await self.cache.client.set(locked_until_cache_key, datetime.isoformat(datetime.now(UTC) + timedelta(
                minutes=settings.LOCKOUT_DURATION_MINUTES
            )))

    async def reset_failed_login_attempts(self, user: User) -> None:
        """Reset failed login attempts and unlock account."""
        cache_key = f"failed_login_attempts:{user.id}"
        await self.cache.client.delete(cache_key)
        locked_until_cache_key = f"locked_until:{user.id}"
        await self.cache.client.delete(locked_until_cache_key)