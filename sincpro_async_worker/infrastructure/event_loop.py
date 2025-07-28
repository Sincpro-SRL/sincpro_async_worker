"""
EventLoop component that manages async execution without conflicts.
Simple and direct approach.
"""

import asyncio
import logging
import threading
import warnings
from typing import Awaitable, Optional, TypeVar

logger = logging.getLogger(__name__)
T = TypeVar("T")


def get_or_create_event_loop() -> asyncio.AbstractEventLoop:
    """
    Simple function to get existing event loop or create a new one.
    Returns the loop that should be used.
    """
    try:
        # Try to get the currently running loop
        return asyncio.get_running_loop()
    except RuntimeError:
        # No running loop, try to get the thread's loop
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_closed():
                return loop
        except RuntimeError:
            pass

        # Create a new loop
        return asyncio.new_event_loop()


class EventLoop:
    """
    Simple EventLoop that detects existing loops or creates new ones.
    No magic, no hidden behavior.
    """

    def __init__(self) -> None:
        """Initialize the EventLoop."""
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._is_running = False
        self._owns_loop = False
        logger.debug("EventLoop initialized")

    def start(self) -> None:
        """Start the event loop if not already running."""
        if self._is_running:
            logger.warning("EventLoop is already running")
            return

        try:
            # Use the standalone function to get existing or create new loop
            self._loop = get_or_create_event_loop()

            # Check if we got an existing running loop
            if self._loop.is_running():
                # Existing running loop - reuse it
                self._is_running = True
                self._owns_loop = False
                logger.info("Reusing existing running event loop")
            else:
                # Got a loop but it's not running - start it ourselves
                asyncio.set_event_loop(self._loop)
                self._owns_loop = True
                self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
                self._thread.start()
                self._is_running = True
                logger.info("Started event loop in new thread")

        except Exception as e:
            error_msg = f"Failed to start event loop: {e}"
            logger.error(error_msg)
            warnings.warn(error_msg, RuntimeWarning)
            self._is_running = False

    def run_coroutine(self, coro: Awaitable[T]) -> Optional[asyncio.Future[T]]:
        """Run a coroutine in the event loop."""
        if not self._is_running:
            self.start()

        if not self._is_running or self._loop is None:
            warnings.warn("No event loop available", RuntimeWarning)
            return None

        try:
            # Check if we're in the same loop thread
            try:
                current_loop = asyncio.get_running_loop()
                if current_loop is self._loop:
                    # Same loop, create task directly
                    return asyncio.create_task(coro)
            except RuntimeError:
                pass

            # Different thread, use run_coroutine_threadsafe
            return asyncio.run_coroutine_threadsafe(coro, self._loop)

        except Exception as e:
            error_msg = f"Failed to run coroutine: {e}"
            logger.error(error_msg)
            warnings.warn(error_msg, RuntimeWarning)
            return None

    def get_loop(self) -> Optional[asyncio.AbstractEventLoop]:
        """Get the current event loop."""
        if not self._is_running:
            self.start()
        return self._loop

    def shutdown(self) -> None:
        """Shutdown the event loop only if we own it."""
        if not self._is_running:
            return

        try:
            if self._owns_loop and self._loop:
                logger.info("Shutting down owned event loop")
                self._loop.call_soon_threadsafe(self._loop.stop)

                if self._thread and self._thread.is_alive():
                    self._thread.join(timeout=2.0)

                if not self._loop.is_closed():
                    self._loop.close()
            else:
                logger.info("Not shutting down external event loop")

        except Exception as e:
            error_msg = f"Error during shutdown: {e}"
            logger.error(error_msg)
            warnings.warn(error_msg, RuntimeWarning)
        finally:
            self._loop = None
            self._thread = None
            self._is_running = False
            self._owns_loop = False

    def is_running(self) -> bool:
        """Check if the event loop is running."""
        return self._is_running and self._loop is not None and not self._loop.is_closed()

    def owns_loop(self) -> bool:
        """Check if we own the current loop."""
        return self._owns_loop
