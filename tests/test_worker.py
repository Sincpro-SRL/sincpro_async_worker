"""
Tests for the Worker component.
"""

import time

import pytest

from sincpro_async_worker.exceptions import WorkerNotRunningError
from sincpro_async_worker.worker import Worker


@pytest.fixture
def worker():
    """Fixture that provides a clean Worker instance for each test."""
    return Worker()


def test_worker_initialization(worker):
    """Test that Worker initializes correctly."""
    assert not worker._started
    assert worker._thread is None
    assert worker._event_loop is not None


def test_worker_start(worker):
    """Test that Worker starts correctly."""
    worker.start()
    assert worker._started
    assert worker._thread is not None
    assert worker._thread.is_alive()
    assert worker._event_loop.is_running()


def test_worker_double_start(worker):
    """Test that calling start twice doesn't create multiple threads."""
    worker.start()
    thread_id = worker._thread.ident
    worker.start()  # Second call should be ignored
    assert worker._thread.ident == thread_id


def test_worker_get_event_loop_before_start(worker):
    """Test that get_event_loop raises an error if called before start."""
    with pytest.raises(WorkerNotRunningError, match="Worker has not been started"):
        worker.get_event_loop()


def test_worker_get_event_loop_after_start(worker):
    """Test that get_event_loop returns the event loop after start."""
    worker.start()
    loop = worker.get_event_loop()
    assert loop is worker._event_loop.get_loop()


def test_worker_shutdown(worker):
    """Test that Worker shutdown works correctly."""
    worker.start()
    assert worker._started
    assert worker._thread.is_alive()

    worker.shutdown()
    assert not worker._started
    assert not worker._thread.is_alive()


def test_worker_shutdown_before_start(worker):
    """Test that shutdown works even if start hasn't been called."""
    worker.shutdown()  # Should not raise any exceptions
    assert not worker._started


def test_worker_thread_cleanup(worker):
    """Test that the worker thread is properly cleaned up."""
    worker.start()
    thread = worker._thread

    worker.shutdown()
    time.sleep(0.1)  # Give thread time to finish
    assert not thread.is_alive()


def test_worker_event_loop_cleanup(worker):
    """Test that the event loop is properly cleaned up on shutdown."""
    worker.start()
    worker._event_loop.get_loop()

    worker.shutdown()
    assert not worker._event_loop.is_running()
    assert worker._event_loop._loop is None


def test_worker_keyboard_interrupt_handling(worker):
    """Test that the worker handles keyboard interrupts gracefully."""
    worker.start()
    assert worker._started

    # Simulate keyboard interrupt
    worker._event_loop.get_loop().call_soon_threadsafe(
        lambda: worker._event_loop.get_loop().stop()
    )

    time.sleep(0.1)  # Give thread time to process
    assert not worker._started
    assert not worker._thread.is_alive()
