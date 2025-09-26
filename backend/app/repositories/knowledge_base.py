"""
Repository layer for knowledge base data access.
"""

from uuid import UUID

from sqlalchemy import delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.embedding import Embedding
from app.models.knowledge_base import KnowledgeBase


class KnowledgeBaseRepository:
    """Repository class for knowledge base data access operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_with_destinations(
        self, user_id: UUID, org_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[KnowledgeBase]:
        """Get all knowledge entries with their destinations where user is creator or scope is org_public."""
        query = (
            select(KnowledgeBase)
            .options(joinedload(KnowledgeBase.destination))
            .filter(
                KnowledgeBase.org_id == org_id,
                or_(KnowledgeBase.user_id == user_id, KnowledgeBase.scope == "org_public"),
            )
            .filter(KnowledgeBase.is_active)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.unique().scalars().all()

    async def get_by_destination_id(
        self, destination_id: UUID, user_id: UUID, org_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[KnowledgeBase]:
        """Get knowledge entries for a specific destination where user is creator or scope is org_public."""
        query = (
            select(KnowledgeBase)
            .options(joinedload(KnowledgeBase.destination))
            .filter(KnowledgeBase.destination_id == destination_id, KnowledgeBase.org_id == org_id)
            .filter(or_(KnowledgeBase.user_id == user_id, KnowledgeBase.scope == "org_public"))
            .filter(KnowledgeBase.is_active)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.unique().scalars().all()

    async def get_by_id(
        self, user_id: UUID, org_id: UUID, knowledge_id: UUID
    ) -> KnowledgeBase | None:
        """Get a knowledge entry by its ID where user is creator or scope is org_public."""
        query = (
            select(KnowledgeBase)
            .options(joinedload(KnowledgeBase.destination))
            .filter(KnowledgeBase.id == knowledge_id, KnowledgeBase.org_id == org_id)
            .filter(or_(KnowledgeBase.user_id == user_id, KnowledgeBase.scope == "org_public"))
            .filter(KnowledgeBase.is_active)
        )
        result = await self.db.execute(query)
        return result.unique().scalar_one_or_none()

    async def create(
        self, user_id: UUID, org_id: UUID, destination_id: UUID, knowledge_data: dict
    ) -> KnowledgeBase:
        """Create a new knowledge base entry."""
        db_knowledge = KnowledgeBase(destination_id=destination_id, **knowledge_data)
        self.db.add(db_knowledge)
        db_knowledge.user_id = user_id
        db_knowledge.org_id = org_id
        await self.db.flush()
        return db_knowledge

    async def update(
        self, user_id: UUID, org_id: UUID, knowledge: KnowledgeBase, update_data: dict
    ) -> KnowledgeBase:
        """Update an existing knowledge entry."""
        query = (
            update(KnowledgeBase)
            .where(
                KnowledgeBase.id == knowledge.id,
                KnowledgeBase.user_id == user_id,
                KnowledgeBase.org_id == org_id,
            )
            .filter(KnowledgeBase.is_active)
            .values(update_data)
        )
        await self.db.execute(query)

        await self.db.flush()
        return knowledge

    async def soft_delete(self, user_id: UUID, org_id: UUID, knowledge_id: UUID) -> bool:
        """Soft delete a knowledge entry."""
        query = (
            update(KnowledgeBase)
            .where(
                KnowledgeBase.id == knowledge_id,
                KnowledgeBase.user_id == user_id,
                KnowledgeBase.org_id == org_id,
            )
            .filter(KnowledgeBase.is_active)
            .values(is_active=False)
        )
        await self.db.execute(query)

    async def purge(self, user_id: UUID, org_id: UUID, knowledge: KnowledgeBase) -> bool:
        """Delete a knowledge entry."""
        query = delete(KnowledgeBase).where(
            KnowledgeBase.id == knowledge.id,
            KnowledgeBase.user_id == user_id,
            KnowledgeBase.org_id == org_id,
        )
        await self.db.execute(query)
        # return True

    # async def search_by_content(
    #     self, search_term: str, user_id: UUID, org_id: UUID, destination_id: UUID | None = None
    # ) -> list[KnowledgeBase]:
    #     """Search knowledge entries by content."""
    #     query = (
    #         select(KnowledgeBase)
    #         .options(joinedload(KnowledgeBase.destination))
    #         .filter(KnowledgeBase.content.contains(search_term), KnowledgeBase.user_id == user_id, KnowledgeBase.org_id == org_id)
    #     )

    #     if destination_id:
    #         query = query.filter(KnowledgeBase.destination_id == destination_id)

    #     result = await self.db.execute(query)
    #     return result.unique().scalars().all()

    # async def get_content_by_destination_id(self, user_id: UUID, org_id: UUID, destination_id: UUID) -> list[str]:
    #     """Get all knowledge content for a destination."""
    #     result = await self.db.execute(
    #         select(KnowledgeBase.content).filter(
    #             KnowledgeBase.destination_id == destination_id, KnowledgeBase.user_id == user_id, KnowledgeBase.org_id == org_id
    #         )
    #     )
    #     return result.scalars().all()

    # return [entry.content for entry in result.scalars().all()]

    async def exists_by_id(self, user_id: UUID, org_id: UUID, knowledge_id: UUID) -> bool:
        """Check if a knowledge entry exists by ID."""
        result = await self.db.execute(
            select(KnowledgeBase).filter(
                KnowledgeBase.id == knowledge_id,
                KnowledgeBase.user_id == user_id,
                KnowledgeBase.org_id == org_id,
                KnowledgeBase.is_active,
            )
        )
        return result.scalar_one_or_none() is not None

    async def ingest_knowledge_file(
        self, knowledge_id: UUID, chunks: list[str], embeddings: list[list[float]]
    ) -> list[Embedding]:
        """Create a new knowledge base entry and its embeddings."""
        # Create embedding entries
        embedding_items = []
        for i, (chunk, embedding_vector) in enumerate(zip(chunks, embeddings, strict=False)):
            embedding_items.append(
                Embedding(
                    knowledge_item_id=knowledge_id,
                    chunk_idx=i,
                    content=chunk,
                    embedding=embedding_vector,
                )
            )

        self.db.add_all(embedding_items)
        await self.db.flush()
