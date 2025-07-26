"""
Base test module for the async worker.
"""

import asyncio
import concurrent.futures
import time
from typing import List

import pytest

from sincpro_async_worker.core import run_async_task


async def async_task(delay: float) -> str:
    """Simple async task that sleeps for a given delay."""
    await asyncio.sleep(delay)
    return f"Task completed after {delay} seconds"


def test_async_task_execution() -> None:
    """Test that async tasks can be executed."""
    result = run_async_task(async_task(0.1))
    assert result == "Task completed after 0.1 seconds"


def test_async_task_timeout() -> None:
    """Test that async tasks respect timeouts."""
    with pytest.raises(TimeoutError):
        run_async_task(async_task(0.2), timeout=0.1)


async def concurrent_tasks() -> List[str]:
    """Run multiple tasks concurrently."""
    tasks = [async_task(0.1) for _ in range(3)]
    return await asyncio.gather(*tasks)


def test_concurrent_task_execution() -> None:
    """Test that multiple tasks can run concurrently."""
    start_time = time.time()

    # Run three tasks concurrently
    results = run_async_task(concurrent_tasks())

    end_time = time.time()
    total_time = end_time - start_time

    # All tasks should complete in roughly the same time
    assert total_time < 0.2  # Should be close to 0.1 seconds
    assert len(results) == 3
    assert all(r == "Task completed after 0.1 seconds" for r in results)


def test_fire_and_forget_execution() -> None:
    """Test that fire-and-forget mode returns a Future immediately."""
    # Execute task in fire-and-forget mode
    future = run_async_task(async_task(0.1), fire_and_forget=True)

    # Should return a Future object (concurrent.futures.Future from asyncio.run_coroutine_threadsafe)
    assert isinstance(future, concurrent.futures.Future)

    # Should not be done immediately
    assert not future.done()

    # Wait for the task to complete and verify result
    result = future.result(timeout=1.0)
    assert result == "Task completed after 0.1 seconds"


def test_fire_and_forget_multiple_tasks() -> None:
    """Test multiple fire-and-forget tasks can run concurrently."""
    start_time = time.time()

    # Start multiple tasks in fire-and-forget mode
    futures = []
    for i in range(3):
        future = run_async_task(async_task(0.1), fire_and_forget=True)
        futures.append(future)

    # All futures should be created quickly
    creation_time = time.time() - start_time
    assert creation_time < 0.05  # Should be very fast

    # Wait for all tasks to complete
    results = []
    for future in futures:
        result = future.result(timeout=1.0)
        results.append(result)

    total_time = time.time() - start_time

    # All tasks should complete in roughly the same time
    assert total_time < 0.2  # Should be close to 0.1 seconds
    assert len(results) == 3
    assert all(r == "Task completed after 0.1 seconds" for r in results)


def test_fire_and_forget_exception_handling() -> None:
    """Test that exceptions in fire-and-forget tasks are captured in the Future."""

    async def failing_task() -> str:
        await asyncio.sleep(0.05)
        raise ValueError("Test exception")

    # Execute failing task in fire-and-forget mode
    future = run_async_task(failing_task(), fire_and_forget=True)

    # Should return a Future object
    assert isinstance(future, concurrent.futures.Future)

    # Exception should be captured in the Future
    with pytest.raises(ValueError, match="Test exception"):
        future.result(timeout=1.0)


def test_fire_and_forget_vs_blocking_mode() -> None:
    """Test the difference between fire-and-forget and blocking mode."""
    start_time = time.time()

    # Fire-and-forget should return immediately
    future = run_async_task(async_task(0.1), fire_and_forget=True)
    fire_and_forget_time = time.time() - start_time

    # Should return almost immediately
    assert fire_and_forget_time < 0.05
    assert isinstance(future, concurrent.futures.Future)

    # Blocking mode should wait for completion
    start_time = time.time()
    result = run_async_task(async_task(0.1), fire_and_forget=False)
    blocking_time = time.time() - start_time

    # Should take at least the task duration
    assert blocking_time >= 0.1
    assert isinstance(result, str)
    assert result == "Task completed after 0.1 seconds"
