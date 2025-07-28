"""
EventLoop component that manages async execution using dedicated thread strategy.
"""

import asyncio
import concurrent.futures
import logging
import threading
from typing import Awaitable, Coroutine, Optional, TypeVar

logger = logging.getLogger(__name__)
T = TypeVar("T")


class EventLoop:
    """
    EventLoop that always creates a dedicated thread with isolated event loop.

    This ensures:
    - Type Safety: Always returns concurrent.futures.Future
    - Simplicity: One strategy, simple code
    - Universality: Works in scripts, Jupyter, FastAPI
    - Isolation: Zero interference with external contexts
    """

    def __init__(self) -> None:
        """Initialize the EventLoop."""
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._is_running = False
        logger.debug("EventLoop initialized with dedicated thread strategy")

    def start(self) -> None:
        """Start the event loop in a dedicated thread."""
        if self._is_running:
            logger.debug("EventLoop is already running")
            return

        try:
            self._loop = asyncio.new_event_loop()
            self._thread = threading.Thread(
                target=self._run_loop_forever, daemon=True, name="AsyncWorkerThread"
            )
            self._thread.start()
            self._is_running = True
            logger.info("Created dedicated worker thread with isolated event loop")

        except Exception as e:
            logger.error(f"Failed to start event loop: {e}")
            self._is_running = False

    def _run_loop_forever(self) -> None:
        """Internal method to run the event loop in the dedicated thread."""
        asyncio.set_event_loop(self._loop)
        if self._loop:
            self._loop.run_forever()

    def run_coroutine(self, coro: Awaitable[T]) -> Optional[concurrent.futures.Future[T]]:
        """
        Run a coroutine in the dedicated event loop thread.

        Args:
            coro: The coroutine to execute

        Returns:
            A concurrent.futures.Future representing the result, or None if failed
        """
        if not self._is_running:
            self.start()

        if not self._is_running or self._loop is None:
            logger.error("No event loop available")
            return None

        try:
            # Convert Awaitable to Coroutine if needed
            if not isinstance(coro, Coroutine):

                async def wrapper():
                    return await coro

                coro_to_run = wrapper()
            else:
                coro_to_run = coro

            return asyncio.run_coroutine_threadsafe(coro_to_run, self._loop)
        except Exception as e:
            logger.error(f"Failed to run coroutine: {e}")
            return None

    def shutdown(self) -> None:
        """Shutdown the dedicated event loop and thread."""
        if not self._is_running:
            return

        try:
            if self._loop and not self._loop.is_closed():
                logger.info("Shutting down dedicated event loop")
                self._loop.call_soon_threadsafe(self._loop.stop)

                if self._thread and self._thread.is_alive():
                    self._thread.join(timeout=2.0)

                if not self._loop.is_closed():

                    def close_loop():
                        if self._loop and not self._loop.is_closed():
                            self._loop.close()

                    close_thread = threading.Thread(target=close_loop, daemon=True)
                    close_thread.start()
                    close_thread.join(timeout=1.0)

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        finally:
            self._loop = None
            self._thread = None
            self._is_running = False

    def is_running(self) -> bool:
        """Check if the event loop is running."""
        return self._is_running and self._loop is not None and not self._loop.is_closed()
