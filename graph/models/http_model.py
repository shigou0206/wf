from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Union, Callable, List, Literal, TypedDict, Awaitable
from enum import Enum
import asyncio
import threading


class HttpRequestMethods(str, Enum):
    DELETE = "DELETE"
    GET = "GET"
    HEAD = "HEAD"
    PATCH = "PATCH"
    POST = "POST"
    PUT = "PUT"

    @classmethod
    def from_string(cls, value: str) -> "HttpRequestMethods":
        try:
            return cls(value.upper())
        except ValueError:
            raise ValueError(f"Invalid HTTP request method: {value}")


@dataclass
class BaseAbortSignal:
    aborted: bool = False
    onabort: Optional[Callable[..., None]] = None
    _listeners: List[Callable[..., None]] = field(default_factory=list, init=False)

    def add_event_listener(self, listener: Callable[..., None]):
        if listener not in self._listeners:
            self._listeners.append(listener)

    def remove_event_listener(self, listener: Callable[..., None]):
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _trigger_abort(self):
        """同步触发 `abort` 事件"""
        self.aborted = True
        if self.onabort:
            self.onabort()
        for listener in self._listeners:
            listener()


@dataclass
class ThreadedAbortSignal(BaseAbortSignal):
    _abort_event: threading.Event = field(default_factory=threading.Event, init=False)

    def abort(self):
        if not self.aborted:
            self._abort_event.set()
            self._trigger_abort()


@dataclass
class AsyncAbortSignal(BaseAbortSignal):
    _abort_event: asyncio.Event = field(default_factory=asyncio.Event, init=False)

    async def abort(self):
        if not self.aborted:
            self._abort_event.set()
            self.aborted = True
            if self.onabort:
                await self.onabort()
            for listener in self._listeners:
                if asyncio.iscoroutinefunction(listener):
                    await listener()
                else:
                    listener()


def get_abort_signal() -> Union[ThreadedAbortSignal, AsyncAbortSignal]:
    try:
        asyncio.get_running_loop()
        return AsyncAbortSignal()
    except RuntimeError:
        return ThreadedAbortSignal()


@dataclass
class HttpRequestAuth:
    username: str
    password: str
    send_immediately: Optional[bool] = True


@dataclass
class HttpRequestProxy:
    host: str
    port: int
    auth: Optional[HttpRequestAuth] = None
    protocol: Optional[str] = None  # HTTP / HTTPS


@dataclass
class HttpRequestOptions:
    url: str
    base_url: Optional[str] = None
    headers: Optional[Dict[str, Any]] = None
    method: Optional[HttpRequestMethods] = HttpRequestMethods.GET
    body: Optional[Union[bytes, str, Dict[str, Any], list]] = None
    qs: Optional[Dict[str, Any]] = None
    array_format: Optional[Literal["indices", "brackets", "repeat", "comma"]] = None
    auth: Optional[HttpRequestAuth] = None
    disable_follow_redirect: Optional[bool] = False
    encoding: Optional[Literal["arraybuffer", "blob", "document", "json", "text", "stream"]] = "json"
    skip_ssl_certificate_validation: Optional[bool] = False
    return_full_response: Optional[bool] = False
    ignore_http_status_errors: Optional[bool] = False
    proxy: Optional[HttpRequestProxy] = None
    timeout: Optional[float] = 30.0
    json: Optional[bool] = False
    abort_signal: Optional[Union[ThreadedAbortSignal, AsyncAbortSignal]] = None

class PostReceiveType(str, Enum):
    BINARY_DATA = "binaryData"
    FILTER = "filter"
    LIMIT = "limit"
    ROOT_PROPERTY = "rootProperty"
    SET = "set"
    SET_KEY_VALUE = "setKeyValue"
    SORT = "sort"

class PostReceiveBase(TypedDict):
    type: PostReceiveType
    properties: Dict[str, Union[str, int, bool, Dict[str, Any]]]
    enabled: Optional[Union[bool, str]]
    error_message: Optional[str]

class PostReceiveBinaryData(PostReceiveBase):
    type: PostReceiveType.BINARY_DATA
    properties: Dict[str, str] 

class PostReceiveFilter(PostReceiveBase):
    type: PostReceiveType.FILTER
    properties: Dict[str, Union[bool, str]]

class PostReceiveLimit(PostReceiveBase):
    type: PostReceiveType.LIMIT
    properties: Dict[str, Union[int, str]]

class PostReceiveRootProperty(PostReceiveBase):
    type: PostReceiveType.ROOT_PROPERTY
    properties: Dict[str, str]

class PostReceiveSet(PostReceiveBase):
    type: PostReceiveType.SET
    properties: Dict[str, str] 

class PostReceiveSetKeyValue(PostReceiveBase):
    type: PostReceiveType.SET_KEY_VALUE
    properties: Dict[str, Union[str, int]]

class PostReceiveSort(PostReceiveBase):
    type: PostReceiveType.SORT
    properties: Dict[str, str]

PostReceiveAction = Union[
    Callable[[List[Dict[str, Any]], Dict[str, Any]], List[Dict[str, Any]]], 
    Callable[[List[Dict[str, Any]], Dict[str, Any]], Awaitable[List[Dict[str, Any]]]],
    PostReceiveBinaryData,
    PostReceiveFilter,
    PostReceiveLimit,
    PostReceiveRootProperty,
    PostReceiveSet,
    PostReceiveSetKeyValue,
    PostReceiveSort
]

@dataclass
class NodeRequestOutput:
    max_results: Optional[Union[int, str]] = None
    post_receive: Optional[List[PostReceiveAction]] = field(default_factory=list)