from fastapi import APIRouter
from app.api.v1 import (
    agent,
    auth,
    destinations,
    knowledge,
    ops,
    users,
)

router = APIRouter(prefix="/v1")
router.include_router(agent.router)
router.include_router(auth.router)
router.include_router(destinations.router)
router.include_router(knowledge.router)
router.include_router(ops.router)
router.include_router(users.router)
