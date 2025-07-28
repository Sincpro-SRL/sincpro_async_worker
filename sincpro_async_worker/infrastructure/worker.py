"""
Worker component that manages the execution of async tasks in a separate thread.
"""

import logging
from typing import Awaitable, Optional, TypeVar

from sincpro_async_worker.infrastructure.event_loop import EventLoop

logger = logging.getLogger(__name__)
T = TypeVar("T")


class Worker:
    """
    Worker that manages the execution of async tasks in a separate thread.
    """

    def __init__(self) -> None:
        """Initialize the Worker component."""
        self._event_loop = EventLoop()
        logger.debug("Worker initialized")

    def start(self) -> None:
        """Start the worker in a separate thread."""
        self._event_loop.start()
        logger.debug("Worker started")

    def run_coroutine(self, coro: Awaitable[T]) -> Optional[Awaitable[T]]:
        """
        Run a coroutine in the worker's event loop.

        Args:
            coro: The coroutine to run

        Returns:
            An awaitable representing the result of the coroutine, or None if failed
        """
        return self._event_loop.run_coroutine(coro)

    def shutdown(self) -> None:
        """Shutdown the worker."""
        self._event_loop.shutdown()
        logger.debug("Worker shutdown completed")

    def is_running(self) -> bool:
        """Check if the worker is running."""
        return self._event_loop.is_running()
