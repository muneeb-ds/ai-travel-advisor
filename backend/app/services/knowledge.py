"""
Service layer for knowledge base management.
"""
import logging
import tempfile
from typing import List
from uuid import UUID

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai.embeddings import OpenAIEmbeddings
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile

from app.core.settings import settings
from app.models.knowledge_base import KnowledgeBase
from app.repositories.destination import DestinationRepository
from app.repositories.knowledge_base import KnowledgeBaseRepository
from app.schemas.knowledge_base import KnowledgeBaseItemCreate, KnowledgeBaseItemUpdate
from app.models.user import User, UserRole
from app.core.exceptions import NotFoundError, ForbiddenError, BadRequestError


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
        return await self.knowledge_repo.get_by_id(user_id=user_id, org_id=org_id, knowledge_id=knowledge_id)

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
        knowledge = await self.knowledge_repo.get_by_id(user_id=user.id, org_id=org_id, knowledge_id=knowledge_id)
        if not knowledge:
            return None

        if (knowledge.user_id != user.id or user.role != UserRole.ADMIN.value):
            raise ForbiddenError("Only the creator of the knowledge entry or an organization admin can update it")

        update_data = knowledge_data.model_dump(exclude_unset=True)
        return await self.knowledge_repo.update(
            user_id=user.id, org_id=org_id, knowledge=knowledge, update_data=update_data
        )

    async def soft_delete_knowledge_entry(self, user: User, org_id: UUID, knowledge_id: UUID) -> bool:
        """Soft delete a knowledge entry."""
        knowledge = await self.knowledge_repo.get_by_id(user_id=user.id, org_id=org_id, knowledge_id=knowledge_id)
        if not knowledge:
            raise NotFoundError(f"Knowledge entry with id {knowledge_id} not found")

        if (knowledge.user_id != user.id or user.role != UserRole.ADMIN.value):
            raise ForbiddenError("Only the creator of the knowledge entry or an organization admin can delete it")

        return await self.knowledge_repo.soft_delete(user_id=user.id, org_id=org_id, knowledge_id=knowledge_id)

    async def delete_knowledge_entry(self, user: User, org_id: UUID, knowledge_id: UUID) -> bool:
        """Delete a knowledge entry."""
        knowledge = await self.knowledge_repo.get_by_id(user_id=user.id, org_id=org_id, knowledge_id=knowledge_id)
        if not knowledge:
            raise NotFoundError(f"Knowledge entry with id {knowledge_id} not found")

        if (knowledge.user_id != user.id or user.role != UserRole.ADMIN.value):
            raise ForbiddenError("Only the creator of the knowledge entry or an organization admin can delete it")

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
        return await self.knowledge_repo.exists_by_id(user_id=user_id, org_id=org_id, knowledge_id=knowledge_id)

    async def ingest_knowledge_file(self, knowledge_id: UUID, file: UploadFile) -> KnowledgeBase:
        """Ingest a new knowledge base entry."""
        # Business logic: Validate file
        if not file:
            raise BadRequestError("File is required")

        # Business logic: Validate file size
        if file.size > 10 * 1024 * 1024:  # 10MB
            raise BadRequestError("File size must be less than 10MB")

        # Business logic: Validate file type
        if file.content_type not in ["application/pdf", "text/markdown"]:
            raise BadRequestError("File must be a PDF or Markdown")

        # create embedding in embeddings table
        # return await self.knowledge_repo.ingest_knowledge_file(user_id=user_id, org_id=org_id, file=file)

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp_file:
                tmp_file.write(await file.read())
                tmp_file_path = tmp_file.name
            

            if file.content_type == "application/pdf":
                loader = PyPDFLoader(tmp_file_path)
                documents: List[Document] = loader.load()
            else:
                with open(tmp_file_path, "r") as f:
                    documents = f.read()
            
            # convert documents to text
            if isinstance(documents, list):
                document_text = ""
                for doc in documents:
                    document_text += f"{doc.page_content}\n"

            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            chunks = text_splitter.split_text(document_text)
            embeddings_model = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
            embeddings = embeddings_model.embed_documents(chunks)


            logger.critical(f"Documents items: {documents}")
            logger.critical(f"Documents items: {document_text}")
            logger.critical(f"Chunks items: {chunks}")
            logger.critical(f"Embedding items: {embeddings}")

            embedding_items = await self.knowledge_repo.ingest_knowledge_file(
                knowledge_id=knowledge_id, chunks=chunks, embeddings=embeddings
            )

            return embedding_items
        finally:
            if "tmp_file_path" in locals():
                import os

                os.unlink(tmp_file_path)