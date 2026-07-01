import asyncio

import pytest

from app.async_task_runner import AsyncTaskRunner


async def successful_job(value: str) -> str:
    await asyncio.sleep(0)
    return f"done:{value}"


async def failing_job() -> None:
    await asyncio.sleep(0)
    raise ValueError("boom")


async def slow_job(delay: float = 0.05) -> str:
    await asyncio.sleep(delay)
    return "slow-done"


def test_async_task_runner_completes_task():
    async def scenario():
        runner = AsyncTaskRunner()

        record = runner.create_task(
            "demo",
            successful_job,
            "x",
        )
        status = await runner.await_task(record.task_id)

        assert status["task_id"] == record.task_id
        assert status["name"] == "demo"
        assert status["status"] == "completed"
        assert status["result"] == "done:x"
        assert status["error_type"] is None
        assert status["duration_ms"] >= 0

    asyncio.run(scenario())


def test_async_task_runner_records_failure_without_raising_job_error():
    async def scenario():
        runner = AsyncTaskRunner()

        record = runner.create_task("failure", failing_job)
        status = await runner.await_task(record.task_id)

        assert status["status"] == "failed"
        assert status["result"] is None
        assert status["error_type"] == "ValueError"
        assert status["error_message"] == "boom"

    asyncio.run(scenario())


def test_async_task_runner_can_cancel_running_task():
    async def scenario():
        runner = AsyncTaskRunner()

        record = runner.create_task("slow", slow_job, 1.0)
        await asyncio.sleep(0)
        status = await runner.cancel_task(record.task_id)

        assert status["status"] == "cancelled"
        assert status["error_type"] == "CancelledError"
        assert status["error_message"] == "task was cancelled"

    asyncio.run(scenario())


def test_async_task_runner_timeout_does_not_cancel_task():
    async def scenario():
        runner = AsyncTaskRunner()

        record = runner.create_task("slow", slow_job, 0.05)

        with pytest.raises(TimeoutError, match="task timed out"):
            await runner.await_task(record.task_id, timeout=0.001)

        running_status = runner.get_task_status(record.task_id)
        assert running_status["status"] in {"pending", "running"}

        final_status = await runner.await_task(record.task_id)
        assert final_status["status"] == "completed"
        assert final_status["result"] == "slow-done"

    asyncio.run(scenario())


def test_async_task_runner_runs_multiple_tasks_concurrently():
    async def scenario():
        runner = AsyncTaskRunner()

        first = runner.create_task("first", slow_job, 0.01)
        second = runner.create_task("second", slow_job, 0.01)

        first_status, second_status = await asyncio.gather(
            runner.await_task(first.task_id),
            runner.await_task(second.task_id),
        )

        assert first_status["status"] == "completed"
        assert second_status["status"] == "completed"
        assert {item["name"] for item in runner.list_task_statuses()} == {
            "first",
            "second",
        }

    asyncio.run(scenario())


def test_async_task_runner_rejects_invalid_concurrency_limit():
    with pytest.raises(ValueError, match="max_concurrent_tasks"):
        AsyncTaskRunner(max_concurrent_tasks=0)


def test_async_task_runner_limits_concurrent_tasks():
    async def scenario():
        runner = AsyncTaskRunner(max_concurrent_tasks=1)
        release = asyncio.Event()
        started = []

        async def blocking_job(name: str) -> str:
            started.append(name)
            await release.wait()
            return name

        first = runner.create_task("first", blocking_job, "first")
        second = runner.create_task("second", blocking_job, "second")

        await asyncio.sleep(0)

        first_status = runner.get_task_status(first.task_id)
        second_status = runner.get_task_status(second.task_id)

        assert first_status["status"] == "running"
        assert second_status["status"] == "pending"
        assert started == ["first"]

        release.set()

        first_final, second_final = await asyncio.gather(
            runner.await_task(first.task_id),
            runner.await_task(second.task_id),
        )

        assert first_final["status"] == "completed"
        assert second_final["status"] == "completed"
        assert second_final["result"] == "second"
        assert started == ["first", "second"]

    asyncio.run(scenario())


def test_async_task_runner_can_cancel_pending_limited_task():
    async def scenario():
        runner = AsyncTaskRunner(max_concurrent_tasks=1)
        release = asyncio.Event()

        async def blocking_job() -> str:
            await release.wait()
            return "done"

        first = runner.create_task("first", blocking_job)
        second = runner.create_task("second", blocking_job)

        await asyncio.sleep(0)

        assert runner.get_task_status(first.task_id)["status"] == "running"
        assert runner.get_task_status(second.task_id)["status"] == "pending"

        second_status = await runner.cancel_task(second.task_id)

        assert second_status["status"] == "cancelled"
        assert second_status["error_type"] == "CancelledError"

        release.set()
        first_status = await runner.await_task(first.task_id)

        assert first_status["status"] == "completed"

    asyncio.run(scenario())


def test_async_task_runner_rejects_empty_name():
    async def scenario():
        runner = AsyncTaskRunner()

        with pytest.raises(ValueError, match="task name"):
            runner.create_task(" ", successful_job, "x")

    asyncio.run(scenario())


def test_async_task_runner_rejects_non_awaitable_result():
    def not_async():
        return "not-awaitable"

    async def scenario():
        runner = AsyncTaskRunner()

        record = runner.create_task("not-async", not_async)
        status = await runner.await_task(record.task_id)

        assert status["status"] == "failed"
        assert status["error_type"] == "TypeError"
        assert "awaitable" in status["error_message"]

    asyncio.run(scenario())


def test_async_task_runner_unknown_task_id_raises_key_error():
    runner = AsyncTaskRunner()

    with pytest.raises(KeyError, match="task not found"):
        runner.get_task_status("missing")
