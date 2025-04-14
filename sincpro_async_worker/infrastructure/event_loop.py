"""
EventLoop component that manages the event loop configuration and state.
"""

import asyncio
import logging
import threading
from typing import Any, Optional, TypeVar, Awaitable

logger = logging.getLogger(__name__)
T = TypeVar('T')

class EventLoop:
    """
    Custom event loop implementation.
    Provides a simple interface to interact with the event loop.
    """

    def __init__(self) -> None:
        """Initialize the EventLoop component."""
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._is_running = False
        logger.debug("EventLoop initialized")

    def start(self) -> None:
        """Start the event loop in a separate thread."""
        if self._is_running:
            logger.warning("Event loop is already running")
            return

        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        
        self._thread = threading.Thread(
            target=self._loop.run_forever,
            daemon=True
        )
        self._thread.start()
        self._is_running = True
        logger.debug("Event loop started in thread mode")

    def get_loop(self) -> asyncio.AbstractEventLoop:
        """
        Get the current event loop.
        If the loop is not running, it will be started automatically.
        """
        if not self._is_running:
            logger.info("Event loop not running, starting it automatically")
            self.start()
        return self._loop

    def run_coroutine(self, coro: Awaitable[T]) -> asyncio.Future[T]:
        """
        Run a coroutine in the event loop.
        
        Args:
            coro: The coroutine to run
            
        Returns:
            A Future representing the result of the coroutine
        """
        loop = self.get_loop()
        return asyncio.run_coroutine_threadsafe(coro, loop)

    def shutdown(self) -> None:
        """Shutdown the event loop."""
        if not self._is_running:
            return

        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._loop = None

        if self._thread:
            self._thread.join()
            self._thread = None

        self._is_running = False
        logger.debug("Event loop shutdown completed")

    def is_running(self) -> bool:
        """Check if the event loop is running."""
        return self._is_running
