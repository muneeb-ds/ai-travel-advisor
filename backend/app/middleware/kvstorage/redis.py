import json

from typing import Any, Dict, Union, cast
from redis.asyncio import Redis, from_url
from .base import BaseKVStorage


AnyDict = Dict[str, Any]
AnyData = Union[str, AnyDict]
REDIS_URL: str = ""


class RedisStorage(BaseKVStorage):
    def __init__(self, prefix: str, redis_url: str) -> None:
        super().__init__(prefix)
        global REDIS_URL
        REDIS_URL = redis_url

    def _format_key(self, key: str) -> str:
        return "%s:%s" % (self.prefix, key)

    @staticmethod
    async def _get_pool() -> Redis:
        pool = from_url(REDIS_URL, decode_responses=True)
        if not pool:
            raise ValueError("Unable to get connection pool")
        return pool

    async def get(self, key: str, deserialize: bool = True) -> Union[str, AnyDict, None]:
        pool = await self._get_pool()
        value = await pool.get(self._format_key(key))
        if value is None:
            return None
        if isinstance(value, bytes):
            value = value.decode("utf8")
        if deserialize and ("{" in value or "[" in value):
            try:
                return cast(AnyDict, json.loads(value))
            except json.JSONDecodeError:
                pass
        await pool.close()
        return cast(str, value)

    async def set(self, key: str, data: AnyData, expired: int = 0, **kwargs: Any) -> Union[str, None]:
        if isinstance(data, dict):
            data = json.dumps(data)
        pool = await self._get_pool()
        await pool.set(self._format_key(key), data, ex=expired, **kwargs)
        await pool.close()
        return key

    async def delete(self, key: str) -> None:
        pool = await self._get_pool()
        await pool.delete(self._format_key(key))
        await pool.close()
