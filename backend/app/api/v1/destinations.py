"""
API routes for destination management.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.dependencies import destination_service, get_current_active_user
from app.core.limiter import limiter

# from app.decorators.idempotency import idempotent
from app.models.user import User
from app.schemas import destination as schemas
from app.services.destination import DestinationService

router = APIRouter(prefix="/destinations", tags=["destinations"])


@router.get("/", response_model=list[schemas.Destination])
@limiter.limit("60/minute")
async def get_destinations(
    request: Request,  # noqa: ARG001
    skip: int = 0,
    limit: int = 100,
    dest_service: DestinationService = Depends(destination_service),
    user: User = Depends(get_current_active_user),
):
    """Get all destinations with pagination."""
    destinations = await dest_service.get_destinations(
        user_id=user.id, org_id=user.org_id, skip=skip, limit=limit
    )
    return destinations


@router.get(
    "/{destination_id}",
    response_model=schemas.DestinationWithKnowledge,
)
@limiter.limit("60/minute")
async def get_destination(
    request: Request,  # noqa: ARG001
    destination_id: str,
    dest_service: DestinationService = Depends(destination_service),
    user: User = Depends(get_current_active_user),
):
    """Get a specific destination by ID with its knowledge entries."""
    destination = await dest_service.get_destination_by_id(
        user_id=user.id, org_id=user.org_id, destination_id=destination_id
    )
    if not destination:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Destination with id {destination_id} not found",
        )
    return destination


@router.post("/", response_model=schemas.Destination, status_code=status.HTTP_201_CREATED)
@limiter.limit("60/minute")
async def create_destination(
    request: Request,  # noqa: ARG001
    destination_data: schemas.DestinationCreate,
    dest_service: DestinationService = Depends(destination_service),
    user: User = Depends(get_current_active_user),
):
    """
    Create a new destination.
    """

    try:
        destination = await dest_service.create_destination(
            user_id=user.id, org_id=user.org_id, destination_data=destination_data
        )
        return destination
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{destination_id}", response_model=schemas.Destination)
@limiter.limit("60/minute")
async def update_destination(
    request: Request,  # noqa: ARG001
    destination_id: str,
    destination_data: schemas.DestinationUpdate,
    dest_service: DestinationService = Depends(destination_service),
    user: User = Depends(get_current_active_user),
):
    """Update a destination."""

    try:
        updated_destination = await dest_service.update_destination(
            user_id=user.id,
            org_id=user.org_id,
            destination_id=destination_id,
            destination_data=destination_data,
        )
        if not updated_destination:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Destination with id {destination_id} not found",
            )
        return updated_destination
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{destination_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("60/minute")
async def delete_destination(
    request: Request,  # noqa: ARG001
    destination_id: str,
    dest_service: DestinationService = Depends(destination_service),
    user: User = Depends(get_current_active_user),
):
    """Delete a destination."""

    destination = await dest_service.get_destination_by_id(
        user_id=user.id, org_id=user.org_id, destination_id=destination_id
    )
    if not destination:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Destination with id {destination_id} not found",
        )

    await dest_service.soft_delete_destination(
        user_id=user.id, org_id=user.org_id, destination_id=destination_id
    )
