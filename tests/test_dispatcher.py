"""
Tests for the Dispatcher component.
"""

import asyncio
import time
from concurrent.futures import TimeoutError

import pytest

from sincpro_async_worker.dispatcher import Dispatcher
from sincpro_async_worker.exceptions import TaskExecutionError
from sincpro_async_worker.worker import Worker


@pytest.fixture
def worker():
    """Fixture that provides a Worker instance."""
    worker = Worker()
    worker.start()
    yield worker
    worker.shutdown()


@pytest.fixture
def dispatcher(worker):
    """Fixture that provides a Dispatcher instance."""
    return Dispatcher(worker)


async def successful_task(duration: float = 0.1) -> str:
    """A simple successful async task."""
    await asyncio.sleep(duration)
    return "Task completed successfully"


async def failing_task():
    """A task that raises an exception."""
    await asyncio.sleep(0.1)
    raise ValueError("Task failed")


def test_dispatcher_initialization(dispatcher, worker):
    """Test that Dispatcher initializes correctly."""
    assert dispatcher._worker is worker


def test_dispatcher_fire_and_forget(dispatcher):
    """Test fire-and-forget task execution."""
    # This should not raise any exceptions
    dispatcher.run(successful_task(), wait_for_result=False)
    time.sleep(0.2)  # Give task time to complete


def test_dispatcher_wait_for_result(dispatcher):
    """Test task execution with result waiting."""
    result = dispatcher.run(successful_task(), wait_for_result=True)
    assert result == "Task completed successfully"


def test_dispatcher_timeout(dispatcher):
    """Test task execution with timeout."""
    with pytest.raises(TimeoutError):
        dispatcher.run(successful_task(0.5), wait_for_result=True, timeout=0.1)


def test_dispatcher_error_handling(dispatcher):
    """Test error handling in task execution."""
    with pytest.raises(TaskExecutionError) as exc_info:
        dispatcher.run(failing_task(), wait_for_result=True)
    assert "Task failed" in str(exc_info.value)


def test_dispatcher_multiple_tasks(dispatcher):
    """Test execution of multiple tasks."""
    # Start multiple tasks
    results = []
    for i in range(3):
        result = dispatcher.run(successful_task(0.1 * (i + 1)), wait_for_result=True)
        results.append(result)

    assert len(results) == 3
    assert all(r == "Task completed successfully" for r in results)


def test_dispatcher_error_does_not_affect_other_tasks(dispatcher):
    """Test that one failing task doesn't affect others."""
    # Start a failing task
    with pytest.raises(TaskExecutionError):
        dispatcher.run(failing_task(), wait_for_result=True)

    # Start a successful task
    result = dispatcher.run(successful_task(), wait_for_result=True)
    assert result == "Task completed successfully"


def test_dispatcher_with_sync_function(dispatcher):
    """Test execution of a synchronous function."""

    def sync_task():
        time.sleep(0.1)
        return "Sync task completed"

    result = dispatcher.run(asyncio.to_thread(sync_task), wait_for_result=True)
    assert result == "Sync task completed"


def test_dispatcher_with_worker_not_running():
    """Test that dispatcher raises error when worker is not running."""
    worker = Worker()  # Not started
    dispatcher = Dispatcher(worker)

    with pytest.raises(TaskExecutionError):
        dispatcher.run(successful_task(), wait_for_result=True)
