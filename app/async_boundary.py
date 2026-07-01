import asyncio
from collections.abc import Callable
from typing import Any, TypeVar


T = TypeVar("T")


async def run_sync_in_thread(
    function: Callable[..., T],
    *args: Any,
    **kwargs: Any,
) -> T:
    if not callable(function):
        raise TypeError("function must be callable")

    return await asyncio.to_thread(
        function,
        *args,
        **kwargs,
    )
