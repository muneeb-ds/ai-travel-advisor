import hashlib
import json
from typing import Any, cast

from pydantic import BaseModel, ValidationError
from starlette import status
from starlette.middleware.base import BaseHTTPMiddleware, DispatchFunction, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response
from starlette.types import ASGIApp

from .kvstorage import KVStorage, get_kv_storage

IDEMPOTENT_EXPIRED: int = 10800
IDEMPOTENT_ENABLED: bool = True
REDIS_URL: str = ""
TESTING: bool = False

AnyDictType = dict[str, Any]
BodyType = str | AnyDictType


class DataRecord(BaseModel):
    fingerprint: str
    status_code: int
    headers: dict[str, str]
    media_type: str
    body: BodyType


class AsyncIteratorWrapper:
    def __init__(self, obj: list[Any]):
        self._it = iter(obj)

    def __aiter__(self) -> "AsyncIteratorWrapper":
        return self

    async def __anext__(self) -> Any:
        try:
            value = next(self._it)
        except StopIteration:
            raise StopAsyncIteration
        return value


class ErrorType:
    invalid_key = "invalid_key"
    too_many_request = "too_many_request"
    request_conflict = "request_conflict"
    response_conflict = "response_conflict"


ERROR_MAP = {
    ErrorType.invalid_key: "Invalid idempotent key. Minimum 32 alphabet numeric characters.",
    ErrorType.too_many_request: "Can not accept sequential requests in the short time.",
    ErrorType.request_conflict: "Request conflict.",
    ErrorType.response_conflict: "Response conflict.",
}


class IdempotentMiddleWare(BaseHTTPMiddleware):
    _PROCESSING_FLAG = "__IDEMPOTENT_PROCESSING"
    _storage = None
    _storage_key = "idempotent"
    _header_key = "X-Idempotent-Key"

    def __init__(
        self,
        app: ASGIApp,
        idempotent_expired: int = 10800,
        redis_url: str = "",
        testing: bool = False,
        dispatch: DispatchFunction = None,
    ):
        super().__init__(app, dispatch=dispatch)
        global IDEMPOTENT_EXPIRED, REDIS_URL, TESTING
        IDEMPOTENT_EXPIRED = idempotent_expired
        REDIS_URL = redis_url
        TESTING = testing

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        def supported_content_type() -> bool:
            if "content-type" in request.headers:
                return request.headers["content-type"] in [
                    "application/json",
                    "text/plain",
                    "text/html",
                ]
            return False

        def supported_method() -> bool:
            return request.method in ["POST"]

        if not IDEMPOTENT_ENABLED or not supported_method() or not supported_content_type():
            # Not apply
            return await call_next(request)

        key = self._find_idempotent_key(request)
        if not key:
            # Key not found, also skip this case
            return await call_next(request)

        if not self._is_valid_key(key):
            return self._error_response(
                ErrorType.invalid_key, status_code=status.HTTP_400_BAD_REQUEST
            )

        # Get request body and query params to generate a fingerprint
        request_data = {
            "query_params": dict(request.query_params),
            "body": (await request.body()).decode(),
        }

        # We need to reconstruct the request body stream after reading it
        request._stream = AsyncIteratorWrapper([json.dumps(request_data["body"]).encode()])

        try:
            cached_response = await self.before_call_next(key)
        except ValueError:
            return self._error_response(
                ErrorType.too_many_request, status_code=status.HTTP_429_TOO_MANY_REQUESTS
            )

        if cached_response is not None:
            return self._replay_response(request_data, cached_response)

        response: Response = await call_next(request)
        await self.after_call_next(key, request_data, response)
        return response

    @property
    def storage(self) -> KVStorage:
        if not self._storage:
            self._storage = get_kv_storage(self._storage_key, redis_url=REDIS_URL, testing=TESTING)
        return self._storage

    @classmethod
    def _find_idempotent_key(cls, request: Request) -> str | None:
        key_finders = [lambda request: request.headers.get(cls._header_key, None)]
        for func in key_finders:
            key = func(request)
            if key:
                return cast(str, key.replace("-", ""))
        return None

    @staticmethod
    def _is_valid_key(key: str) -> bool:
        return len(key) >= 32 and key.isalnum()

    @staticmethod
    def _serialize(response: AnyDictType) -> str:
        return json.dumps(response)

    @staticmethod
    def _deserialize(response: str) -> AnyDictType:
        return cast(AnyDictType, json.loads(response))

    @staticmethod
    def _create_save_data(fingerprint: str, body: BodyType, response: Response) -> AnyDictType:
        data = {
            "headers": dict(response.headers),
            "status_code": response.status_code,
            "media_type": response.media_type if response.media_type else "application/json",
            "body": body,
            "fingerprint": fingerprint,
        }
        return data

    @staticmethod
    def _error_response(error_type: str, status_code: int) -> JSONResponse:
        response = {
            "status": "error",
            "result": {"msg": ERROR_MAP[error_type], "type": "idempotent." + error_type},
        }
        return JSONResponse(response, status_code=status_code)

    def _replay_response(self, request_data: AnyDictType, cached_response: AnyDictType) -> Response:
        try:
            # Validate response data
            record = DataRecord(**cached_response)
        except ValidationError:
            return self._error_response(
                ErrorType.response_conflict, status_code=status.HTTP_409_CONFLICT
            )

        # compare fingerprint between original request body and request body
        fingerprint = self._create_fingerprint(request_data)
        if record.fingerprint != fingerprint:
            return self._error_response(
                ErrorType.request_conflict, status_code=status.HTTP_409_CONFLICT
            )

        record.headers["X-Idempotent-Replayed"] = "1"
        if record.media_type == "text/html":
            return HTMLResponse(record.body, headers=record.headers, status_code=record.status_code)
        if record.media_type == "text/plain":
            return PlainTextResponse(
                record.body, headers=record.headers, status_code=record.status_code
            )
        return JSONResponse(record.body, headers=record.headers, status_code=record.status_code)

    @staticmethod
    def _create_fingerprint(data: BodyType) -> str:
        if isinstance(data, dict):
            # Sort the dictionary to ensure consistent hash
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)

        data_bytes = data_str.encode()
        return hashlib.sha256(data_bytes).hexdigest()

    async def before_call_next(self, key: str) -> None | AnyDictType:
        cached_response = await self.storage.get(key, deserialize=False)
        if cached_response is None:
            # First request with this key
            await self.storage.set(key, self._PROCESSING_FLAG, expired=IDEMPOTENT_EXPIRED)
            return None
        if cached_response == self._PROCESSING_FLAG:
            # This request is still processing
            raise ValueError
        return self._deserialize(cast(str, cached_response))

    async def after_call_next(
        self, key: str, request_data: AnyDictType, response: Response
    ) -> Response:
        # Get response body
        resp_body = [section async for section in response.__dict__["body_iterator"]]
        # Reset body_iterator
        response.__setattr__("body_iterator", AsyncIteratorWrapper(resp_body))

        if response.headers.get("content-type") == "application/json":
            body = json.loads(resp_body[0].decode())
        else:
            body = str(resp_body)

        fingerprint = self._create_fingerprint(request_data)
        data = self._serialize(self._create_save_data(fingerprint, body, response))
        await self.storage.set(key, data, expired=IDEMPOTENT_EXPIRED)
        return response
