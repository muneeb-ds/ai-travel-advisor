from abc import ABC, abstractmethod
from typing import Any

AnyDict = dict[str, Any]
AnyData = str | AnyDict


class BaseKVStorage(ABC):
    prefix: str = "kv_storage"

    def __init__(self, prefix: str) -> None:
        self.prefix = prefix

    @abstractmethod
    async def get(self, key: str, deserialize: bool = True) -> str | AnyDict | None:
        """
        Get the data by key
        """

    @abstractmethod
    async def set(self, key: str, data: AnyData, expired: int = 0, **kwargs: Any) -> str | None:
        """
        Store the data to the key
        """

    @abstractmethod
    async def delete(self, key: str) -> None:
        """
        Remove the key value
        """
