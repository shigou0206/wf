from typing import Callable, Awaitable

CloseFunction = Callable[[], Awaitable[None]]
