"""
EventLoop component that manages the event loop configuration and state.
"""

import asyncio
from typing import Optional

import uvloop


class EventLoop:
    """
    Manages the event loop configuration and state.
    Provides a simple interface to interact with the event loop.
    """

    def __init__(self) -> None:
        """Initialize the EventLoop component."""
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._is_running = False

    def setup(self) -> None:
        """Set up the event loop with uvloop."""
        uvloop.install()
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

    def get_loop(self) -> asyncio.AbstractEventLoop:
        """Get the current event loop."""
        if not self._loop:
            raise RuntimeError("Event loop not initialized")
        return self._loop

    def is_running(self) -> bool:
        """Check if the event loop is running."""
        return self._is_running

    def set_running(self, running: bool) -> None:
        """Set the running state of the event loop."""
        self._is_running = running

    def close(self) -> None:
        """Close the event loop."""
        if self._loop:
            self._loop.close()
            self._loop = None
            self._is_running = False
