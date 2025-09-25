"""
Main FastAPI application entry point.
"""

from collections.abc import AsyncGenerator, Callable
from contextlib import _AsyncGeneratorContextManager, asynccontextmanager
from typing import Any

import redis.asyncio as redis
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api import router as api_router
from app.core import cache
from app.core.limiter import limiter
from app.core.settings import RedisSettings, Settings, settings
from app.middleware import IdempotentMiddleWare
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
# from fastapi_idempotent import IdempotentMiddleWare


# -------------- cache --------------
async def create_redis_cache_pool() -> None:
    cache.pool = redis.ConnectionPool.from_url(settings.REDIS_CACHE_URL)
    cache.client = redis.Redis.from_pool(cache.pool)  # type: ignore


async def close_redis_cache_pool() -> None:
    await cache.client.aclose()  # type: ignore


def lifespan_factory(
    settings: Settings | None = None,
) -> Callable[[FastAPI], _AsyncGeneratorContextManager[Any]]:
    """Factory to create a lifespan async context manager for a FastAPI app."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator:
        from asyncio import Event

        initialization_complete = Event()
        app.state.initialization_complete = initialization_complete

        try:
            if isinstance(settings, RedisSettings):
                await create_redis_cache_pool()

            initialization_complete.set()

            yield

        finally:
            if isinstance(settings, RedisSettings):
                await close_redis_cache_pool()

    return lifespan

lifespan = lifespan_factory(settings)

app = FastAPI(
    title="AI Travel Advisor API",
    description="Backend API for the AI Travel Advisor application",
    version="0.1.0",
    default_response_class=JSONResponse,
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    IdempotentMiddleWare,
    idempotent_expired=settings.IDEMPOTENCY_TTL_SECONDS, # type: int
    redis_url=settings.REDIS_CACHE_URL,  # type: str
)
# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router)
