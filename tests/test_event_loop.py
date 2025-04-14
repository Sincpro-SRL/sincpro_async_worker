"""
Tests for the EventLoop component following TDD principles.

The EventLoop component should:
1. Manage an asyncio event loop in a separate thread
2. Allow running coroutines safely from any thread
3. Handle the event loop lifecycle correctly
"""

import asyncio
import pytest
import threading
import time
from typing import Optional

from sincpro_async_worker.infrastructure import EventLoop


@pytest.fixture
def event_loop_fixture():
    """
    Fixture that provides a clean EventLoop instance and ensures proper cleanup.
    """
    loop = EventLoop()
    yield loop
    # Ensure cleanup
    if loop.is_running():
        loop.shutdown()


def test_event_loop_should_start_in_not_running_state(event_loop_fixture):
    """Test that EventLoop initializes in a clean state."""
    assert not event_loop_fixture.is_running()
    assert event_loop_fixture._loop is None
    assert event_loop_fixture._thread is None


def test_event_loop_should_create_new_loop_on_start(event_loop_fixture):
    """Test that start() creates a new event loop in a separate thread."""
    event_loop_fixture.start()
    
    assert event_loop_fixture.is_running()
    assert isinstance(event_loop_fixture._loop, asyncio.AbstractEventLoop)
    assert isinstance(event_loop_fixture._thread, threading.Thread)
    assert event_loop_fixture._thread.is_alive()


def test_event_loop_should_not_start_if_already_running(event_loop_fixture):
    """Test that start() is idempotent."""
    event_loop_fixture.start()
    original_loop = event_loop_fixture._loop
    original_thread = event_loop_fixture._thread
    
    # Try to start again
    event_loop_fixture.start()
    
    # Should maintain the same loop and thread
    assert event_loop_fixture._loop is original_loop
    assert event_loop_fixture._thread is original_thread


def test_get_loop_should_start_if_not_running(event_loop_fixture):
    """Test that get_loop() automatically starts the loop if needed."""
    assert not event_loop_fixture.is_running()
    
    loop = event_loop_fixture.get_loop()
    
    assert event_loop_fixture.is_running()
    assert isinstance(loop, asyncio.AbstractEventLoop)
    assert loop.is_running()


def test_run_coroutine_should_execute_in_loop_thread(event_loop_fixture):
    """Test that coroutines are executed in the event loop thread."""
    async def get_current_thread():
        return threading.current_thread()
    
    future = event_loop_fixture.run_coroutine(get_current_thread())
    thread = future.result(timeout=1)
    
    assert thread is event_loop_fixture._thread


def test_run_coroutine_should_handle_exceptions(event_loop_fixture):
    """Test that exceptions in coroutines are propagated correctly."""
    async def raise_error():
        raise ValueError("Test error")
    
    future = event_loop_fixture.run_coroutine(raise_error())
    
    with pytest.raises(ValueError, match="Test error"):
        future.result(timeout=1)


def test_shutdown_should_cleanup_resources(event_loop_fixture):
    """Test that shutdown() properly cleans up all resources."""
    event_loop_fixture.start()
    thread = event_loop_fixture._thread
    
    event_loop_fixture.shutdown()
    
    assert not event_loop_fixture.is_running()
    assert event_loop_fixture._loop is None
    assert event_loop_fixture._thread is None
    assert not thread.is_alive()


def test_shutdown_should_be_safe_to_call_multiple_times(event_loop_fixture):
    """Test that shutdown() is idempotent."""
    event_loop_fixture.start()
    event_loop_fixture.shutdown()
    # Should not raise any exceptions
    event_loop_fixture.shutdown()
    
    assert not event_loop_fixture.is_running()


def test_run_multiple_coroutines_concurrently(event_loop_fixture):
    """Test that multiple coroutines can run concurrently."""
    async def delayed_result(delay: float, value: str) -> str:
        await asyncio.sleep(delay)
        return value
    
    # Start multiple coroutines with different delays
    future1 = event_loop_fixture.run_coroutine(delayed_result(0.1, "first"))
    future2 = event_loop_fixture.run_coroutine(delayed_result(0.05, "second"))
    
    # Second should complete before first
    assert future2.result(timeout=1) == "second"
    assert future1.result(timeout=1) == "first"
