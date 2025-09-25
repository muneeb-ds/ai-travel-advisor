"""
Redis client configuration and management.
"""

import redis.asyncio as redis

pool: redis.ConnectionPool | None = None
client: redis.Redis | None = None
