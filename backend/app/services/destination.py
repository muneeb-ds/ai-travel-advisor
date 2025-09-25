"""
Service layer for destination management.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.destination import Destination
from app.repositories.destination import DestinationRepository
from app.schemas.destination import DestinationCreate, DestinationUpdate


class DestinationService:
    """Service class for destination business logic."""

    def __init__(self, db: AsyncSession):
        self.destination_repo = DestinationRepository(db)

    async def get_destinations(
        self, user_id: UUID, org_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[Destination]:
        """Get all destinations with pagination."""
        return await self.destination_repo.get_all(user_id=user_id, org_id=org_id, skip=skip, limit=limit)

    async def get_destination_by_id(
        self, user_id: UUID, org_id: UUID, destination_id: UUID
    ) -> Destination | None:
        """Get a destination by its ID."""
        return await self.destination_repo.get_by_id(user_id=user_id, org_id=org_id, destination_id=destination_id)

    async def get_destination_by_name(self, user_id: UUID, org_id: UUID, name: str) -> Destination | None:
        """Get a destination by its name."""
        return await self.destination_repo.get_by_name(user_id=user_id, org_id=org_id, name=name)

    async def create_destination(
        self, user_id: UUID, org_id: UUID, destination_data: DestinationCreate
    ) -> Destination:
        """Create a new destination."""
        # Business logic: Check if destination already exists
        if await self.destination_repo.exists_by_name(user_id=user_id, org_id=org_id, name=destination_data.name):
            raise ValueError(f"Destination '{destination_data.name}' already exists")

        return await self.destination_repo.create(
            user_id=user_id, org_id=org_id, destination_data=destination_data.model_dump()
        )

    async def update_destination(
        self,
        user_id: UUID,
        org_id: UUID,
        destination_id: UUID,
        destination_data: DestinationUpdate,
    ) -> Destination | None:
        """Update an existing destination."""
        destination = await self.destination_repo.get_by_id(
            user_id=user_id, org_id=org_id, destination_id=destination_id
        )
        if not destination:
            return None

        # Business logic: Check if new name already exists (if name is being updated)
        update_data = destination_data.model_dump(exclude_unset=True)
        if "name" in update_data and update_data["name"] != destination.name:
            if await self.destination_repo.exists_by_name(
                user_id=user_id, org_id=org_id, name=update_data["name"]
            ):
                raise ValueError(f"Destination '{update_data['name']}' already exists")

        return await self.destination_repo.update(
            user_id=user_id, org_id=org_id, destination=destination, update_data=update_data
        )

    async def soft_delete_destination(self, user_id: UUID, org_id: UUID, destination_id: UUID) -> bool:
        """Delete a destination."""
        return await self.destination_repo.soft_delete(user_id=user_id, org_id=org_id, destination=destination_id)

    async def delete_destination(self, user_id: UUID, org_id: UUID, destination_id: UUID) -> bool:
        """Delete a destination."""
        destination = await self.destination_repo.get_by_id(
            user_id=user_id, org_id=org_id, destination_id=destination_id
        )
        if not destination:
            raise ValueError(f"Destination with id {destination_id} not found")
        return await self.destination_repo.delete(user_id=user_id, org_id=org_id, destination=destination)

    async def destination_exists(self, user_id: UUID, org_id: UUID, destination_id: UUID) -> bool:
        """Check if a destination exists."""
        return await self.destination_repo.exists_by_id(
            user_id=user_id, org_id=org_id, destination_id=destination_id
        )
