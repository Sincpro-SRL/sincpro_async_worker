"""
Tests for the Dispatcher component following TDD principles.

The Dispatcher component should:
1. Act as the primary entry point for executing async tasks
2. Handle task execution lifecycle (timeouts, errors, cancellation)
3. Manage underlying worker resources
4. Follow dependency inversion principle
"""

import asyncio
import concurrent.futures
import time

import pytest

from sincpro_async_worker.domain.dispatcher import DispatcherInterface
from sincpro_async_worker.infrastructure import Dispatcher


@pytest.fixture
def dispatcher_fixture():
    """
    Fixture that provides a clean Dispatcher instance and ensures proper cleanup.
    """
    dispatcher = Dispatcher()
    yield dispatcher
    # Cleanup will happen automatically in __del__


def test_dispatcher_should_implement_interface():
    """Test that Dispatcher implements the DispatcherInterface."""
    dispatcher = Dispatcher()
    assert isinstance(dispatcher, DispatcherInterface)


def test_dispatcher_should_execute_simple_task(dispatcher_fixture):
    """Test that dispatcher can execute a simple async task."""

    async def simple_task():
        return "success"

    result = dispatcher_fixture.execute(simple_task())
    assert result == "success"


def test_dispatcher_should_handle_task_with_parameters(dispatcher_fixture):
    """Test that dispatcher can execute tasks with parameters."""

    async def parameterized_task(x: int, y: str) -> str:
        return f"{y}{x}"

    result = dispatcher_fixture.execute(parameterized_task(42, "answer"))
    assert result == "answer42"


def test_dispatcher_should_handle_timeout(dispatcher_fixture):
    """Test that dispatcher respects timeout constraints."""

    async def slow_task():
        await asyncio.sleep(0.2)
        return "completed"

    with pytest.raises(TimeoutError):
        dispatcher_fixture.execute(slow_task(), timeout=0.1)


def test_dispatcher_should_propagate_exceptions(dispatcher_fixture):
    """Test that dispatcher properly propagates exceptions from tasks."""

    async def failing_task():
        raise ValueError("Task failed")

    with pytest.raises(ValueError, match="Task failed"):
        dispatcher_fixture.execute(failing_task())


def test_dispatcher_execute_async_should_return_future(dispatcher_fixture):
    """Test that execute_async returns a Future immediately."""

    async def async_task():
        await asyncio.sleep(0.1)
        return "async_result"

    future = dispatcher_fixture.execute_async(async_task())

    # Should return a concurrent.futures.Future object
    assert isinstance(future, concurrent.futures.Future)

    # Should not be done immediately
    assert not future.done()

    # Wait for completion and verify result
    result = future.result(timeout=1.0)
    assert result == "async_result"


def test_dispatcher_execute_async_multiple_tasks(dispatcher_fixture):
    """Test that multiple execute_async calls work concurrently."""

    async def numbered_task(number: int):
        await asyncio.sleep(0.1)
        return f"task_{number}"

    start_time = time.time()

    # Start multiple async tasks
    futures = []
    for i in range(3):
        future = dispatcher_fixture.execute_async(numbered_task(i))
        futures.append(future)

    # All futures should be created quickly
    creation_time = time.time() - start_time
    assert creation_time < 0.05

    # Wait for all to complete
    results = []
    for future in futures:
        result = future.result(timeout=1.0)
        results.append(result)

    total_time = time.time() - start_time

    # Should complete concurrently (roughly 0.1 seconds, not 0.3)
    assert total_time < 0.2
    assert set(results) == {"task_0", "task_1", "task_2"}


def test_dispatcher_execute_async_exception_handling(dispatcher_fixture):
    """Test that execute_async properly captures exceptions in Future."""

    async def failing_async_task():
        await asyncio.sleep(0.05)
        raise RuntimeError("Async task failed")

    future = dispatcher_fixture.execute_async(failing_async_task())

    # Should return a concurrent.futures.Future object
    assert isinstance(future, concurrent.futures.Future)

    # Exception should be captured in the Future
    with pytest.raises(RuntimeError, match="Async task failed"):
        future.result(timeout=1.0)


def test_dispatcher_execute_vs_execute_async_behavior(dispatcher_fixture):
    """Test the behavioral difference between execute and execute_async."""

    async def timed_task():
        await asyncio.sleep(0.1)
        return "completed"

    # execute should block and return result
    start_time = time.time()
    result = dispatcher_fixture.execute(timed_task())
    blocking_time = time.time() - start_time

    assert isinstance(result, str)
    assert result == "completed"
    assert blocking_time >= 0.1  # Should wait for task completion

    # execute_async should return immediately
    start_time = time.time()
    future = dispatcher_fixture.execute_async(timed_task())
    async_time = time.time() - start_time

    assert isinstance(future, concurrent.futures.Future)
    assert async_time < 0.05  # Should return almost immediately

    # But the future should eventually contain the result
    result = future.result(timeout=1.0)
    assert result == "completed"


def test_dispatcher_should_handle_concurrent_tasks(dispatcher_fixture):
    """Test that dispatcher can handle multiple concurrent tasks."""

    async def delayed_task(delay: float, value: str) -> str:
        await asyncio.sleep(delay)
        return value

    # Execute multiple tasks with different delays
    results = []
    results.append(dispatcher_fixture.execute(delayed_task(0.1, "first")))
    results.append(dispatcher_fixture.execute(delayed_task(0.05, "second")))

    assert results == ["first", "second"]


def test_dispatcher_should_cancel_task_on_timeout(dispatcher_fixture):
    """Test that dispatcher properly cancels tasks on timeout."""
    completion_flag = False

    async def monitored_task():
        nonlocal completion_flag
        await asyncio.sleep(0.3)
        completion_flag = True  # Should not reach this point if cancelled
        return "done"

    with pytest.raises(TimeoutError):
        dispatcher_fixture.execute(monitored_task(), timeout=0.1)

    # Give enough time for the task to complete if it wasn't cancelled
    time.sleep(0.5)
    assert not completion_flag  # Task should have been cancelled


# @pytest.mark.skip(reason="Not implemented")
def test_dispatcher_should_handle_nested_tasks(dispatcher_fixture):
    """Test that dispatcher can handle nested task execution."""

    async def inner_task():
        await asyncio.sleep(0.1)
        return "inner"

    async def outer_task():
        result = await inner_task()
        return f"outer-{result}"

    result = dispatcher_fixture.execute(outer_task())
    assert result == "outer-inner"


def test_dispatcher_should_cleanup_resources_on_deletion():
    """Test that dispatcher properly cleans up resources when deleted."""
    dispatcher = Dispatcher()
    worker = dispatcher._worker

    # Execute a task to ensure worker is running
    async def simple_task():
        return "done"

    dispatcher.execute(simple_task())
    assert worker.is_running()

    # Delete dispatcher
    del dispatcher

    # Worker should be shut down
    assert not worker.is_running()


def test_dispatcher_should_handle_long_running_tasks(dispatcher_fixture):
    """Test that dispatcher can handle long-running tasks without blocking."""

    async def long_task():
        await asyncio.sleep(0.3)
        return "long"

    async def short_task():
        await asyncio.sleep(0.1)
        return "short"

    # Start long task first
    long_result = dispatcher_fixture.execute(long_task())
    short_result = dispatcher_fixture.execute(short_task())

    # Both tasks should complete successfully
    assert long_result == "long"
    assert short_result == "short"


def test_dispatcher_should_maintain_task_order(dispatcher_fixture):
    """Test that dispatcher maintains execution order for sequential tasks."""
    results = []

    async def ordered_task(order: int):
        results.append(order)
        await asyncio.sleep(0.1)
        return order

    # Execute tasks in sequence
    for i in range(3):
        dispatcher_fixture.execute(ordered_task(i))

    # Results should maintain order
    assert results == [0, 1, 2]
