from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization


class OrganizationRepository:
    """Repository class for organization data access operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_organization_by_name(self, name: str) -> Organization | None:
        """Get an organization by its name."""
        query = select(Organization).filter(Organization.name == name)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_organization(self, name: str) -> Organization:
        """Create a new organization."""
        organization = Organization(name=name)
        self.db.add(organization)
        await self.db.flush()
        return organization
