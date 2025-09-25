import logging
from typing import Optional

from fastapi import HTTPException, Request
from jose import JWTError, jwt
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.security import JWT_PUBLIC_KEY, oauth2_scheme
from app.core.settings import settings

logger = logging.getLogger(__name__)


def key_func(request: Request) -> str:
    """
    Determine the client identifier for rate limiting.
    - If a valid JWT is present, the user ID is used.
    - Otherwise, the client's IP address is used.
    """
    try:
        # Manually extract token from header
        auth_header = request.headers.get("Authorization")
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                token = parts[1]
                payload = jwt.decode(
                    token, JWT_PUBLIC_KEY, algorithms=[settings.JWT_ALGORITHM]
                )
                user_id: Optional[str] = payload.get("sub")
                if user_id:
                    return user_id
    except JWTError as e:
        # Log JWT errors but don't raise, as we can fall back to IP.
        logger.warning(f"JWTError during token decoding for rate limit: {e}")

    # Fallback to IP address if no valid token/user_id is found
    return get_remote_address(request)


limiter = Limiter(
    key_func=key_func,
    storage_uri=settings.REDIS_CACHE_URL,
)
