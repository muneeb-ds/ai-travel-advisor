from fastapi import APIRouter, Depends
from httpx import get

from app.api.dependencies import get_current_active_user, get_ops_service
from app.models.user import User
from app.services.ops import OpsService

router = APIRouter(tags=["ops"])


@router.get("/metrics")
async def get_metrics(
    ops_service: OpsService = Depends(get_ops_service), user: User = Depends(get_current_active_user)
):
    return ops_service.get_metrics(user_id=user.id)


@router.get("/healthz")
async def get_healthz(ops_service: OpsService = Depends(get_ops_service)):
    return await ops_service.get_healthz()
