"""
Service layer for knowledge base management.
"""

import logging
import os
import tempfile
from datetime import UTC, datetime
from uuid import UUID

from fastapi import UploadFile
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_postgres import PGVectorStore
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.models.knowledge_base import KnowledgeBase
from app.models.user import User, UserRole
from app.repositories.destination import DestinationRepository
from app.repositories.knowledge_base import KnowledgeBaseRepository
from app.schemas.knowledge_base import KnowledgeBaseItemCreate, KnowledgeBaseItemUpdate

logger = logging.getLogger(__name__)


class KnowledgeService:
    """Service class for knowledge base business logic."""

    def __init__(self, db: AsyncSession):
        self.knowledge_repo = KnowledgeBaseRepository(db)
        self.destination_repo = DestinationRepository(db)

    async def get_all_knowledge_entries(
        self, user_id: UUID, org_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[KnowledgeBase]:
        """Get all knowledge entries with their destinations."""
        return await self.knowledge_repo.get_all_with_destinations(
            user_id=user_id, org_id=org_id, skip=skip, limit=limit
        )

    async def get_knowledge_by_destination(
        self, user_id: UUID, org_id: UUID, destination_id: UUID, skip: int = 0, limit: int = 100
    ) -> list[KnowledgeBase]:
        """Get knowledge entries for a specific destination."""
        # Business logic: Validate destination exists
        if not await self.destination_repo.exists_by_id(
            user_id=user_id, org_id=org_id, destination_id=destination_id
        ):
            raise NotFoundError(f"Destination with id {destination_id} not found")

        return await self.knowledge_repo.get_by_destination_id(
            user_id=user_id, org_id=org_id, destination_id=destination_id, skip=skip, limit=limit
        )

    async def get_knowledge_by_id(
        self, user_id: UUID, org_id: UUID, knowledge_id: UUID
    ) -> KnowledgeBase | None:
        """Get a knowledge entry by its ID."""
        return await self.knowledge_repo.get_by_id(
            user_id=user_id, org_id=org_id, knowledge_id=knowledge_id
        )

    async def create_knowledge_entry(
        self, user_id: UUID, org_id: UUID, knowledge_data: KnowledgeBaseItemCreate
    ) -> KnowledgeBase:
        """Create a new knowledge base entry."""
        # Business logic: Validate destination exists
        if not await self.destination_repo.exists_by_id(
            user_id=user_id, org_id=org_id, destination_id=knowledge_data.destination_id
        ):
            raise NotFoundError(f"Destination with id {knowledge_data.destination_id} not found")

        return await self.knowledge_repo.create(
            user_id=user_id,
            org_id=org_id,
            knowledge_data=knowledge_data.model_dump(),
        )

    async def update_knowledge_entry(
        self, user: User, org_id: UUID, knowledge_id: UUID, knowledge_data: KnowledgeBaseItemUpdate
    ) -> KnowledgeBase | None:
        """Update an existing knowledge entry."""
        knowledge = await self.knowledge_repo.get_by_id(
            user_id=user.id, org_id=org_id, knowledge_id=knowledge_id
        )
        if not knowledge:
            return None

        if knowledge.user_id != user.id or user.role != UserRole.ADMIN.value:
            raise ForbiddenError(
                "Only the creator of the knowledge entry or an organization admin can update it"
            )

        update_data = knowledge_data.model_dump(exclude_unset=True)
        return await self.knowledge_repo.update(
            user_id=user.id, org_id=org_id, knowledge=knowledge, update_data=update_data
        )

    async def soft_delete_knowledge_entry(
        self, user: User, org_id: UUID, knowledge_id: UUID
    ) -> bool:
        """Soft delete a knowledge entry."""
        knowledge = await self.knowledge_repo.get_by_id(
            user_id=user.id, org_id=org_id, knowledge_id=knowledge_id
        )
        if not knowledge:
            raise NotFoundError(f"Knowledge entry with id {knowledge_id} not found")

        if knowledge.user_id != user.id or user.role != UserRole.ADMIN.value:
            raise ForbiddenError(
                "Only the creator of the knowledge entry or an organization admin can delete it"
            )

        return await self.knowledge_repo.soft_delete(
            user_id=user.id, org_id=org_id, knowledge_id=knowledge_id
        )

    async def delete_knowledge_entry(self, user: User, org_id: UUID, knowledge_id: UUID) -> bool:
        """Delete a knowledge entry."""
        knowledge = await self.knowledge_repo.get_by_id(
            user_id=user.id, org_id=org_id, knowledge_id=knowledge_id
        )
        if not knowledge:
            raise NotFoundError(f"Knowledge entry with id {knowledge_id} not found")

        if knowledge.user_id != user.id or user.role != UserRole.ADMIN.value:
            raise ForbiddenError(
                "Only the creator of the knowledge entry or an organization admin can delete it"
            )

        return await self.knowledge_repo.purge(user_id=user.id, org_id=org_id, knowledge=knowledge)

    # async def search_knowledge_by_content(
    #     self, search_term: str, user_id: UUID, org_id: UUID, destination_id: UUID | None = None
    # ) -> list[KnowledgeBase]:
    #     """Search knowledge entries by content."""
    #     # Business logic: Validate destination if provided
    #     if destination_id and not await self.destination_repo.exists_by_id(
    #         user_id=user_id, org_id=org_id, destination_id=destination_id
    #     ):
    #         raise NotFoundError(f"Destination with id {destination_id} not found")

    #     return await self.knowledge_repo.search_by_content(
    #         user_id=user_id, org_id=org_id, search_term=search_term, destination_id=destination_id
    #     )

    # async def get_destination_knowledge_content(
    #     self, user_id: UUID, org_id: UUID, destination_id: UUID
    # ) -> list[str]:
    #     """Get all knowledge content for a destination (for RAG processing)."""
    #     # Business logic: Validate destination exists
    #     if not await self.destination_repo.exists_by_id(
    #         user_id=user_id, org_id=org_id, destination_id=destination_id
    #     ):
    #         raise NotFoundError(f"Destination with id {destination_id} not found")

    #     return await self.knowledge_repo.get_content_by_destination_id(
    #         user_id=user_id, org_id=org_id, destination_id=destination_id
    #     )

    async def knowledge_exists(self, user_id: UUID, org_id: UUID, knowledge_id: UUID) -> bool:
        """Check if a knowledge entry exists."""
        return await self.knowledge_repo.exists_by_id(
            user_id=user_id, org_id=org_id, knowledge_id=knowledge_id
        )

    async def ingest_knowledge_file(
        self, knowledge_id: UUID, file: UploadFile, pgvector_db_store: PGVectorStore
    ) -> int:
        """Ingest a new knowledge base entry."""
        # Business logic: Validate file
        if not file:
            raise BadRequestError("File is required")

        # Business logic: Validate file size
        if file.size > 10 * 1024 * 1024:  # 10MB
            raise BadRequestError("File size must be less than 10MB")

        # validate file extension
        if file.filename.split(".")[-1] not in ["pdf", "md", "txt"]:
            raise BadRequestError("File must be a PDF or Markdown")

        # # Business logic: Validate file type
        # if file.content_type not in ["application/pdf", "text/markdown", "text/plain"]:
        #     raise BadRequestError("File must be a PDF, Markdown, or TXT file")

        try:

            with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp_file:
                tmp_file.write(await file.read())
                tmp_file_path = tmp_file.name

            if file.content_type == "application/pdf":
                loader = PyPDFLoader(tmp_file_path)
                documents = loader.load()
            else:
                with open(tmp_file_path, encoding="utf-8") as f:
                    text_content = f.read()
                documents = [Document(page_content=text_content)]

            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            chunks = text_splitter.split_documents(documents)

            # Add knowledge_id to metadata
            for i, chunk in enumerate(chunks):
                chunk.metadata["knowledge_item_id"] = str(knowledge_id)
                chunk.metadata["chunk_idx"] = i
                chunk.metadata["created_at"] = datetime.now(UTC)
                chunk.metadata["title"] = file.filename
            await pgvector_db_store.aadd_documents(chunks)
            return len(chunks)

        finally:
            if "tmp_file_path" in locals():
                os.unlink(tmp_file_path)

    async def similarity_search(
        self,
        pgvector_db_store: PGVectorStore,
        query: str,
        knowledge_id: UUID | None = None,
        k: int = 5,
    ) -> list[Document]:
        """Perform similarity search on the vector store."""
        filter_metadata = {}
        if knowledge_id:
            filter_metadata["knowledge_item_id"] = str(knowledge_id)

        return await pgvector_db_store.asimilarity_search(query, k=k, filter=filter_metadata)
