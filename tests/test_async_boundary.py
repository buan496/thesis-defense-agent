import asyncio
import threading

import pytest

from app.async_boundary import run_sync_in_thread


def test_run_sync_in_thread_returns_result():
    async def scenario():
        def sync_function(value: str) -> str:
            return f"ok:{value}"

        result = await run_sync_in_thread(
            sync_function,
            "x",
        )

        assert result == "ok:x"

    asyncio.run(scenario())


def test_run_sync_in_thread_passes_keyword_arguments():
    async def scenario():
        def sync_function(prefix: str, value: str) -> str:
            return f"{prefix}:{value}"

        result = await run_sync_in_thread(
            sync_function,
            prefix="ok",
            value="x",
        )

        assert result == "ok:x"

    asyncio.run(scenario())


def test_run_sync_in_thread_uses_worker_thread():
    async def scenario():
        event_loop_thread = threading.get_ident()

        def sync_function() -> int:
            return threading.get_ident()

        worker_thread = await run_sync_in_thread(sync_function)

        assert worker_thread != event_loop_thread

    asyncio.run(scenario())


def test_run_sync_in_thread_rejects_non_callable():
    async def scenario():
        with pytest.raises(TypeError, match="function must be callable"):
            await run_sync_in_thread("not-callable")

    asyncio.run(scenario())
