import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    """Repository class for refresh token data access operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_refresh_token(
        self, user_id: uuid.UUID, jti: str, token_hash: str, expires_at: datetime
    ) -> RefreshToken:
        """Create and store a new refresh token."""
        token = RefreshToken(
            user_id=user_id,
            jti=jti,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.db.add(token)
        await self.db.flush()
        return token

    async def get_refresh_token_by_jti(self, jti: str) -> RefreshToken | None:
        """Retrieve a refresh token by its JTI."""
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.jti == jti)
        )
        return result.scalar_one_or_none()

    async def revoke_refresh_token(self, jti: str) -> None:
        """Revoke a specific refresh token by its JTI."""
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.jti == jti)
            .values(is_revoked=True, used_at=datetime.now(UTC))
        )
        await self.db.execute(stmt)
        await self.db.flush()

    async def revoke_all_user_tokens(self, user_id: uuid.UUID) -> None:
        """Revoke all active refresh tokens for a user."""
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.is_revoked == False)
            .values(is_revoked=True, used_at=datetime.now(UTC))
        )
        await self.db.execute(stmt)
        await self.db.flush()
