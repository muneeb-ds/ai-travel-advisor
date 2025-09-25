"""
API routes for knowledge base management.
"""

from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException,status, UploadFile, File, Request

from app.api.dependencies import get_current_user, knowledge_service
from app.core.limiter import limiter
from app.models.user import User
from app.schemas import knowledge_base as schemas
from app.services.knowledge import KnowledgeService
from app.core.exceptions import NotFoundError, ForbiddenError, BadRequestError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/",
    response_model=list[schemas.KnowledgeBaseResponse],
)
@limiter.limit("60/minute")
async def get_knowledge_entries(
    request: Request,
    destination_id: str = None,
    skip: int = 0,
    limit: int = 100,
    knowledge_service: KnowledgeService = Depends(knowledge_service),
    user: User = Depends(get_current_user),
):
    """Get knowledge base entries with optional destination filter."""

    try:
        if destination_id:
            entries = await knowledge_service.get_knowledge_by_destination(
                user_id=user.id, org_id=user.org_id, destination_id=destination_id, skip=skip, limit=limit
            )
        else:
            entries = await knowledge_service.get_all_knowledge_entries(
                user_id=user.id, org_id=user.org_id, skip=skip, limit=limit
            )
        return entries
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except BadRequestError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{knowledge_id}", response_model=schemas.KnowledgeBaseResponse)
@limiter.limit("60/minute")
async def get_knowledge_entry(
    request: Request,
    knowledge_id: str,
    knowledge_service: KnowledgeService = Depends(knowledge_service),
    user: User = Depends(get_current_user),
):
    """Get a specific knowledge entry by ID."""
    try:
        entry = await knowledge_service.get_knowledge_by_id(user_id=user.id, org_id=user.org_id, knowledge_id=knowledge_id)
        return entry
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except BadRequestError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/", response_model=schemas.KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("60/minute")
async def create_knowledge_entry(
    request: Request,
    knowledge_data: schemas.KnowledgeBaseItemCreate,
    # destination_id: UUID,
    knowledge_service: KnowledgeService = Depends(knowledge_service),
    user: User = Depends(get_current_user),
):
    """
    Create a new knowledge base entry.

    Supports idempotency via the Idempotency-Key header to prevent duplicate entries.
    """

    try:
        entry = await knowledge_service.create_knowledge_entry(
            user_id=user.id, org_id=user.org_id, knowledge_data=knowledge_data
        )
        return entry
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except BadRequestError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/{knowledge_id}/ingest-file")
@limiter.limit("60/minute")
async def ingest_knowledge_file(
    request: Request,
    knowledge_id: str,
    file: UploadFile = File(...),
    knowledge_service: KnowledgeService = Depends(knowledge_service),
    _user: User = Depends(get_current_user),
):
    """Ingest a new knowledge base entry."""
    try:
        entry = await knowledge_service.ingest_knowledge_file(knowledge_id=knowledge_id, file=file)
        return entry
    except NotFoundError as e:
        logger.exception(e)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except BadRequestError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.patch("/{knowledge_id}", response_model=schemas.KnowledgeBaseResponse)
@limiter.limit("60/minute")
async def update_knowledge_entry(
    request: Request,
    knowledge_id: str,
    knowledge_data: schemas.KnowledgeBaseItemUpdate,
    knowledge_service: KnowledgeService = Depends(knowledge_service),
    user: User = Depends(get_current_user),
):
    """Update a knowledge base entry."""

    try:
        updated_entry = await knowledge_service.update_knowledge_entry(
            user=user, org_id=user.org_id, knowledge_id=knowledge_id, knowledge_data=knowledge_data
        )
        return updated_entry
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except BadRequestError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{knowledge_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("60/minute")
async def delete_knowledge_entry(
    request: Request,
    knowledge_id: str,
    knowledge_service: KnowledgeService = Depends(knowledge_service),
    user: User = Depends(get_current_user),
):
    """Delete a knowledge base entry."""

    try:
        await knowledge_service.soft_delete_knowledge_entry(user=user, org_id=user.org_id, knowledge_id=knowledge_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
