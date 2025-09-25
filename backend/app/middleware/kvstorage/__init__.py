"""
Key value storage class
"""
from typing import Dict
from .base import BaseKVStorage as KVStorage
from .memory import MemoryStorage
from .redis import RedisStorage

_kv_storage: Dict[str, KVStorage] = {}


def get_kv_storage(prefix: str, redis_url: str, testing: bool) -> KVStorage:
    global _kv_storage
    cls = RedisStorage if not testing else MemoryStorage

    if prefix not in _kv_storage:
        _kv_storage[prefix] = cls(prefix=prefix, redis_url=redis_url)
    return _kv_storage[prefix]
