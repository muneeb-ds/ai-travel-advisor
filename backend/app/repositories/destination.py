"""
Repository layer for destination data access.
"""

from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.destination import Destination


class DestinationRepository:
    """Repository class for destination data access operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, user_id: UUID, org_id: UUID, skip: int = 0, limit: int = 100) -> list[Destination]:
        """Get all destinations with pagination."""
        query = select(Destination).filter(Destination.user_id == user_id, Destination.org_id == org_id).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_id(self, user_id: UUID, org_id: UUID, destination_id: UUID) -> Destination | None:
        """Get a destination by its ID, including its knowledge entries."""
        query = (
            select(Destination)
            .options(joinedload(Destination.knowledge_entries))
            .filter(Destination.id == destination_id, Destination.user_id == user_id, Destination.org_id == org_id)
        )
        result = await self.db.execute(query)
        return result.unique().scalar_one_or_none()

    async def get_by_name(self, user_id: UUID, org_id: UUID, name: str) -> Destination | None:
        """Get a destination by its name."""
        query = select(Destination).filter(Destination.name == name, Destination.user_id == user_id, Destination.org_id == org_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, user_id: UUID, org_id: UUID, destination_data: dict) -> Destination:
        """Create a new destination."""
        db_destination = Destination(**destination_data, user_id=user_id, org_id=org_id)
        self.db.add(db_destination)
        await self.db.flush()
        return db_destination

    async def update(
        self, user_id: UUID, org_id: UUID, destination: Destination, update_data: dict
    ) -> Destination:
        """Update an existing destination."""
        query = (
            update(Destination)
            .where(Destination.id == destination.id, Destination.user_id == user_id, Destination.org_id == org_id)
            .values(update_data)
        )
        await self.db.execute(query)

        # for field, value in update_data.items():
        #     if hasattr(destination, field):
        #         setattr(destination, field, value)

        await self.db.flush()
        return destination

    async def soft_delete(self, user_id: UUID, org_id: UUID, destination_id: UUID) -> bool:
        """Delete a destination."""
        query = (
            update(Destination)
            .where(Destination.id == destination_id, Destination.user_id == user_id, Destination.org_id == org_id)
            .values(is_active=False, deleted_at=func.now())
        )
        await self.db.execute(query)

    async def delete(self, user_id: UUID, org_id: UUID, destination_id: UUID) -> bool:
        """Delete a destination."""
        query = delete(Destination).where(
            Destination.id == destination_id, Destination.user_id == user_id, Destination.org_id == org_id
        )
        await self.db.execute(query)

    async def exists_by_id(self, user_id: UUID, org_id: UUID, destination_id: UUID) -> bool:
        """Check if a destination exists by ID."""
        query = select(Destination).filter(
            Destination.id == destination_id, Destination.user_id == user_id, Destination.org_id == org_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def exists_by_name(self, user_id: UUID, org_id: UUID, name: str) -> bool:
        """Check if a destination exists by name."""
        query = select(Destination).filter(Destination.name == name, Destination.user_id == user_id, Destination.org_id == org_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None
