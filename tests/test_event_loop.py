"""
Tests for the EventLoop component.
"""

import asyncio

import pytest

from sincpro_async_worker.event_loop import EventLoop


@pytest.fixture
def event_loop():
    """Fixture that provides a clean EventLoop instance for each test."""
    return EventLoop()


def test_event_loop_initialization(event_loop):
    """Test that EventLoop initializes correctly."""
    assert event_loop._loop is None
    assert not event_loop._is_running


def test_event_loop_setup(event_loop):
    """Test that EventLoop setup creates a new event loop."""
    event_loop.setup()
    assert event_loop._loop is not None
    assert isinstance(event_loop._loop, asyncio.AbstractEventLoop)


def test_event_loop_get_loop(event_loop):
    """Test that get_loop returns the event loop after setup."""
    event_loop.setup()
    loop = event_loop.get_loop()
    assert loop is event_loop._loop


def test_event_loop_get_loop_before_setup(event_loop):
    """Test that get_loop raises an error if called before setup."""
    with pytest.raises(RuntimeError, match="Event loop not initialized"):
        event_loop.get_loop()


def test_event_loop_running_state(event_loop):
    """Test that running state can be set and retrieved."""
    assert not event_loop.is_running()
    event_loop.set_running(True)
    assert event_loop.is_running()
    event_loop.set_running(False)
    assert not event_loop.is_running()


def test_event_loop_close(event_loop):
    """Test that close properly cleans up the event loop."""
    event_loop.setup()
    event_loop.set_running(True)

    event_loop.close()
    assert event_loop._loop is None
    assert not event_loop._is_running


def test_event_loop_close_without_setup(event_loop):
    """Test that close works even if setup hasn't been called."""
    event_loop.close()  # Should not raise any exceptions
    assert event_loop._loop is None
    assert not event_loop._is_running
