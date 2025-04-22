"""
Tests for the Worker component following TDD approach.

The Worker component should:
1. Provide a high-level interface for running async tasks
2. Manage the lifecycle of an EventLoop
3. Handle task execution and error propagation
4. Ensure proper resource cleanup
"""

import asyncio
import threading

import pytest

from sincpro_async_worker.infrastructure import Worker


@pytest.fixture
def worker_fixture():
    """
    Fixture that provides a clean Worker instance and ensures proper cleanup.
    """
    worker = Worker()
    yield worker
    if worker.is_running():
        worker.shutdown()


def test_worker_should_start_in_not_running_state(worker_fixture):
    """Test that Worker initializes in a clean state."""
    assert not worker_fixture.is_running()


def test_worker_should_start_event_loop(worker_fixture):
    """Test that start() initializes the event loop correctly."""
    worker_fixture.start()
    assert worker_fixture.is_running()


def test_worker_should_execute_coroutine_in_separate_thread(worker_fixture):
    """Test that coroutines run in a separate thread."""
    main_thread = threading.current_thread()

    async def get_thread():
        return threading.current_thread()

    future = worker_fixture.run_coroutine(get_thread())
    worker_thread = future.result(timeout=1)

    assert worker_thread is not main_thread
    assert isinstance(worker_thread, threading.Thread)


def test_worker_should_handle_coroutine_results(worker_fixture):
    """Test that coroutine results are properly returned."""

    async def compute_value():
        await asyncio.sleep(0.1)  # Simulate some async work
        return 42

    future = worker_fixture.run_coroutine(compute_value())
    result = future.result(timeout=1)

    assert result == 42


def test_worker_should_propagate_exceptions(worker_fixture):
    """Test that exceptions in coroutines are properly propagated."""

    async def raise_error():
        await asyncio.sleep(0.1)  # Simulate some async work
        raise ValueError("Test error")

    future = worker_fixture.run_coroutine(raise_error())

    with pytest.raises(ValueError, match="Test error"):
        future.result(timeout=1)


def test_worker_should_handle_multiple_coroutines(worker_fixture):
    """Test that multiple coroutines can run concurrently."""
    results = []

    async def append_with_delay(delay: float, value: str):
        await asyncio.sleep(delay)
        results.append(value)
        return value

    # Start tasks in reverse order of completion
    future1 = worker_fixture.run_coroutine(append_with_delay(0.2, "first"))
    future2 = worker_fixture.run_coroutine(append_with_delay(0.1, "second"))

    # Wait for both to complete
    assert future2.result(timeout=1) == "second"
    assert future1.result(timeout=1) == "first"

    # Verify execution order
    assert results == ["second", "first"]


def test_worker_should_auto_start_on_first_coroutine(worker_fixture):
    """Test that worker auto-starts when running first coroutine."""
    assert not worker_fixture.is_running()

    async def simple_task():
        return "done"

    future = worker_fixture.run_coroutine(simple_task())
    assert worker_fixture.is_running()
    assert future.result(timeout=1) == "done"


def test_worker_should_cleanup_on_shutdown(worker_fixture):
    """Test that shutdown properly cleans up resources."""
    worker_fixture.start()
    assert worker_fixture.is_running()

    worker_fixture.shutdown()
    assert not worker_fixture.is_running()

    # Should be safe to call shutdown multiple times
    worker_fixture.shutdown()
    assert not worker_fixture.is_running()


def test_worker_should_handle_long_running_tasks(worker_fixture):
    """Test that long-running tasks don't block other tasks."""

    async def long_task():
        await asyncio.sleep(0.3)
        return "long done"

    async def short_task():
        await asyncio.sleep(0.1)
        return "short done"

    # Start long task first
    long_future = worker_fixture.run_coroutine(long_task())
    short_future = worker_fixture.run_coroutine(short_task())

    # Short task should complete first
    assert short_future.result(timeout=1) == "short done"
    assert long_future.result(timeout=1) == "long done"
