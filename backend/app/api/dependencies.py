import logging

from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.security import JWT_PUBLIC_KEY, oauth2_scheme
from app.core.settings import settings
from app.models.user import User, UserRole
from app.repositories.user import UserRepository
from app.services.agent import AgentService
from app.services.auth import AuthService
from app.services.destination import DestinationService
from app.services.knowledge import KnowledgeService
from app.services.ops import OpsService

logger = logging.getLogger(__name__)


async def get_db():
    """Database session dependency - shared across all apps"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except HTTPException:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_user_repository(db: AsyncSession = Depends(get_db)):
    return UserRepository(db)


# --- Token Validation and User Retrieval ---
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_repo: UserRepository = Depends(get_user_repository),
) -> User:
    """
    Decode JWT, validate, and return the current user.
    Raises HTTPException 401 for invalid tokens or inactive users.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, JWT_PUBLIC_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        token_type = payload.get("type")

        if user_id is None or token_type != "access":
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = await user_repo.get_user_by_id(user_id)

    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get the current user and check if they are active.
    Raises HTTPException 403 if the user is inactive.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user


# --- RBAC Dependencies ---
def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Dependency to ensure the current user is an ADMIN.
    Raises HTTPException 403 if the user is not an admin.
    """
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have adequate privileges",
        )
    return current_user


# Dependency for knowledge service
async def knowledge_service(db: AsyncSession = Depends(get_db)) -> KnowledgeService:
    return KnowledgeService(db)


# Dependency for destination service
async def destination_service(db: AsyncSession = Depends(get_db)) -> DestinationService:
    return DestinationService(db)


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Dependency to get an instance of the AuthService."""
    return AuthService(db)


# Dependency for ops service
async def get_ops_service(db: AsyncSession = Depends(get_db)) -> OpsService:
    return OpsService(db)


async def get_agent_service(db: AsyncSession = Depends(get_db)) -> AgentService:
    return AgentService(db)
