"""
This kv storage class is for test running purpose
"""

import json
from datetime import datetime, timedelta
from typing import Any, cast

from .base import BaseKVStorage

AnyDict = dict[str, Any]
AnyData = str | AnyDict


class MemoryStorage(BaseKVStorage):
    records: AnyDict = {}

    def __init__(self, prefix: str, redis_url: str) -> None:
        super().__init__(prefix)

    def _format_key(self, key: str) -> str:
        return f"{self.prefix}_{key}"

    async def get(self, key: str, deserialize: bool = True) -> str | AnyDict | None:
        _key = self._format_key(key)
        if _key not in self.records:
            return None
        record = self.records[_key]
        if "expired_at" in record and datetime.now() > record["expired_at"]:
            self.delete(key)
            return None
        value = record["data"]
        if deserialize and ("{" in value or "[" in value):
            try:
                return cast(AnyDict, json.loads(value))
            except json.JSONDecodeError:
                pass
        return cast(str, value)

    async def set(self, key: str, data: AnyData, expired: int = 0, **kwargs: Any) -> str | None:
        if isinstance(data, dict):
            data = json.dumps(data)
        record: AnyDict = {"data": data}
        if expired != 0:
            record["expired_at"] = datetime.now() + timedelta(seconds=expired)
        self.records[self._format_key(key)] = record
        return key

    async def delete(self, key: str) -> None:
        key = self._format_key(key)
        if key in self.records:
            del self.records[key]
