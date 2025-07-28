"""
Worker component that manages the execution of async tasks in a separate thread.

This module provides the concrete implementation of worker components that
execute async coroutines in dedicated threads with their own event loops,
enabling parallel execution of async subtasks.
"""

import concurrent.futures
import logging
from typing import Awaitable, Optional, TypeVar

from sincpro_async_worker.infrastructure.event_loop import EventLoop

logger = logging.getLogger(__name__)
T = TypeVar("T")


class Worker:
    """
    Worker that manages the execution of async coroutines in a separate thread.

    Provides a dedicated thread with its own event loop for executing async
    coroutines that may contain parallel async subtasks.
    """

    def __init__(self) -> None:
        """Initialize the Worker component with a dedicated event loop."""
        self._event_loop = EventLoop()
        logger.debug("Worker initialized with dedicated event loop")

    def start(self) -> None:
        """Start the worker thread and its event loop."""
        self._event_loop.start()
        logger.debug("Worker started with event loop running")

    def run_coroutine(self, coro: Awaitable[T]) -> Optional[concurrent.futures.Future[T]]:
        """
        Execute an async coroutine in the worker's dedicated event loop.

        The coroutine runs in a separate thread with its own event loop,
        allowing async subtasks within the coroutine to execute in parallel.

        Args:
            coro: The async coroutine to execute

        Returns:
            A Future representing the eventual result, or None if execution failed
        """
        return self._event_loop.run_coroutine(coro)

    def shutdown(self) -> None:
        """Shutdown the worker and clean up resources."""
        self._event_loop.shutdown()
        logger.debug("Worker shutdown completed")

    def is_running(self) -> bool:
        """Check if the worker and its event loop are running."""
        return self._event_loop.is_running()
