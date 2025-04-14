"""
Tests for the Dispatcher component.
"""

import asyncio
import time
from concurrent.futures import TimeoutError

import pytest

from sincpro_async_worker.exceptions import TaskExecutionError
from sincpro_async_worker.infrastructure import Dispatcher, Worker


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


def test_dispatcher_fire_and_forget(worker):
    """Test that dispatcher can execute tasks without waiting for result."""
    worker.start()
    dispatcher = Dispatcher(worker)
    
    future = dispatcher.run(successful_task())
    assert future is not None
    assert not future.done()
    
    worker.shutdown()


def test_dispatcher_wait_for_result(worker):
    """Test that dispatcher can wait for task result."""
    worker.start()
    dispatcher = Dispatcher(worker)
    
    result = dispatcher.run(successful_task())
    assert result == "success"
    
    worker.shutdown()


def test_dispatcher_timeout(worker):
    """Test that dispatcher respects timeout."""
    worker.start()
    dispatcher = Dispatcher(worker)
    
    with pytest.raises(asyncio.TimeoutError):
        dispatcher.run(successful_task(0.5), timeout=0.1)
    
    worker.shutdown()


def test_dispatcher_error_handling(worker):
    """Test that dispatcher properly handles task errors."""
    worker.start()
    dispatcher = Dispatcher(worker)
    
    with pytest.raises(ValueError, match="test error"):
        dispatcher.run(failing_task())
    
    worker.shutdown()


def test_dispatcher_multiple_tasks(worker):
    """Test that dispatcher can handle multiple tasks."""
    worker.start()
    dispatcher = Dispatcher(worker)
    
    futures = [dispatcher.run(successful_task()) for _ in range(5)]
    results = [future.result() for future in futures]
    
    assert all(r == "success" for r in results)
    
    worker.shutdown()


def test_dispatcher_error_does_not_affect_other_tasks(worker):
    """Test that one task's error doesn't affect other tasks."""
    worker.start()
    dispatcher = Dispatcher(worker)
    
    futures = [
        dispatcher.run(failing_task()),
        dispatcher.run(successful_task())
    ]
    
    with pytest.raises(ValueError):
        futures[0].result()
    
    assert futures[1].result() == "success"
    
    worker.shutdown()


def test_dispatcher_with_sync_function(worker):
    """Test that dispatcher can handle synchronous functions."""
    worker.start()
    dispatcher = Dispatcher(worker)
    
    def sync_func():
        return "sync result"
    
    result = dispatcher.run(sync_func)
    assert result == "sync result"
    
    worker.shutdown()


def test_dispatcher_with_worker_not_running():
    """Test that dispatcher raises error when worker is not running."""
    worker = Worker()  # Not started
    dispatcher = Dispatcher(worker)

    with pytest.raises(TaskExecutionError):
        dispatcher.run(successful_task())
