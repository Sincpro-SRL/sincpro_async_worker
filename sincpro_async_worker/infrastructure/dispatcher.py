"""
Dispatcher component that executes async tasks.
"""

import asyncio
import concurrent.futures
import logging
from typing import Awaitable, Optional, TypeVar

from sincpro_async_worker.domain.dispatcher import DispatcherInterface
from sincpro_async_worker.infrastructure.worker import Worker

logger = logging.getLogger(__name__)
T = TypeVar("T")


class Dispatcher(DispatcherInterface):
    """
    Dispatcher that executes async tasks.
    """

    def __init__(self) -> None:
        """Initialize the Dispatcher component."""
        self._worker = Worker()
        self._worker.start()
        logger.debug("Dispatcher initialized and worker started")

    def execute(self, task: Awaitable[T], timeout: Optional[float] = None) -> T:
        """
        Execute an async task.

        Args:
            task: The async task to execute
            timeout: Optional timeout in seconds

        Returns:
            The result of the task

        Raises:
            TimeoutError: If the task takes longer than timeout seconds
            Exception: Any exception raised by the task
        """
        future = self._worker.run_coroutine(task)
        try:
            if timeout is not None:
                return future.result(timeout=timeout)
            return future.result()
        except asyncio.TimeoutError:
            future.cancel()
            raise TimeoutError(f"Task took longer than {timeout} seconds")
        except Exception as e:
            if not future.done():
                future.cancel()
            raise e

    def execute_async(self, task: Awaitable[T]) -> concurrent.futures.Future[T]:
        """
        Execute an async task and return a Future immediately (fire-and-forget).

        Args:
            task: The async task to execute

        Returns:
            A concurrent.futures.Future representing the eventual result of the task
        """
        logger.debug("Executing task in fire-and-forget mode")
        return self._worker.run_coroutine(task)

    def __del__(self) -> None:
        """Cleanup when the dispatcher is destroyed."""
        self._worker.shutdown()
        logger.debug("Dispatcher cleaned up")
