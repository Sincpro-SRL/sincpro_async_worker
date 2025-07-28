"""
Dispatcher component that executes async tasks.

This module provides the concrete implementation of the DispatcherInterface,
coordinating the execution of async coroutines in separate threads with
dedicated event loops for parallel subtask execution.
"""

import asyncio
import concurrent.futures
import logging
from typing import Optional, TypeVar

from sincpro_async_worker.domain.dispatcher import AsyncCoroutine, DispatcherInterface
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

    def execute(self, task: AsyncCoroutine[T], timeout: Optional[float] = None) -> T:
        """
        Execute an async coroutine and wait for its completion.

        Executes the coroutine in a separate thread with its own event loop,
        enabling parallel execution of async subtasks within the coroutine.

        Args:
            task: The async coroutine to execute
            timeout: Optional timeout in seconds

        Returns:
            The result of the coroutine execution

        Raises:
            TimeoutError: If the task takes longer than timeout seconds
            RuntimeError: If the worker is not available
            Exception: Any exception raised by the coroutine
        """
        future = self._worker.run_coroutine(task)
        if future is None:
            raise RuntimeError("Worker is not available to execute task")

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

    def execute_async(self, task: AsyncCoroutine[T]) -> concurrent.futures.Future[T]:
        """
        Execute an async coroutine in fire-and-forget mode (non-blocking).

        Starts the coroutine execution in a separate thread and returns immediately
        with a Future. The coroutine can contain parallel async subtasks.

        Args:
            task: The async coroutine to execute

        Returns:
            A concurrent.futures.Future representing the eventual result

        Raises:
            RuntimeError: If the worker is not available
        """
        logger.debug("Executing task in fire-and-forget mode")
        future = self._worker.run_coroutine(task)
        if future is None:
            raise RuntimeError("Worker is not available to execute task")
        return future

    def __del__(self) -> None:
        """Cleanup when the dispatcher is destroyed."""
        self._worker.shutdown()
        logger.debug("Dispatcher cleaned up")
