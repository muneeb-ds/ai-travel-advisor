from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.models.user import User


class UserRepository:
    """Repository class for user and organization data access operations."""

    def __init__(self, db: AsyncSession):
        """Initialize the repository with a database session."""
        self.db = db

    # --- User Operations ---
    async def get_user_by_id(self, user_id: UUID) -> User | None:
        """Get a user by their ID."""
        return await self.db.get(User, user_id)

    async def get_user_by_email(self, email: str) -> User | None:
        """Get a user by their email address."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create_user(self, user_data: dict) -> User:
        """Create a new user."""
        user = User(**user_data)
        self.db.add(user)
        await self.db.flush()
        return user

    # --- Organization Operations ---
    async def create_organization(self, name: str) -> Organization:
        """Create a new organization."""
        organization = Organization(name=name)
        self.db.add(organization)
        await self.db.flush()
        return organization
