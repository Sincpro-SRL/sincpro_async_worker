"""
Dispatcher component that handles task execution in the event loop.
"""

import asyncio
import logging
from concurrent.futures import TimeoutError
from typing import Any, Coroutine, Optional, TypeVar

from sincpro_async_worker.exceptions import TaskExecutionError
from sincpro_async_worker.worker import Worker

T = TypeVar("T")


class Dispatcher:
    """
    Handles task execution in the event loop.
    Provides a simple interface for running async tasks.
    """

    def __init__(self, worker: "Worker") -> None:
        """Initialize the Dispatcher with a Worker instance."""
        self._logger = logging.getLogger(__name__)
        self._worker: "Worker" = worker

    def run(
        self,
        coro: Coroutine[Any, Any, T],
        wait_for_result: bool = False,
        timeout: Optional[float] = None,
    ) -> Optional[T]:
        """
        Run an async task in the event loop.

        Args:
            coro: Coroutine to execute.
            wait_for_result: If True, wait for and return the result.
            timeout: Maximum time to wait for the result in seconds.

        Returns:
            The result of the coroutine if wait_for_result is True, otherwise None.

        Raises:
            TaskExecutionError: If an error occurs during task execution.
            TimeoutError: If the operation times out.
        """
        try:
            # Get the task queue from the worker
            task_queue = self._worker.get_task_queue()
            
            # Create a future to track the result if needed
            future: Optional[asyncio.Future[T]] = None
            if wait_for_result:
                loop = self._worker.get_event_loop()
                future = loop.create_future()
                
                # Wrap the coroutine to set the future result
                async def wrapped_coro() -> T:
                    try:
                        result = await coro
                        if future and not future.done():
                            future.set_result(result)
                        return result
                    except Exception as e:
                        if future and not future.done():
                            future.set_exception(e)
                        raise
            
            # Submit the task to the queue
            task_queue.put(wrapped_coro() if wait_for_result else coro)
            
            # If we don't need the result, return immediately
            if not wait_for_result:
                return None
            
            # Wait for the result
            try:
                return future.result(timeout=timeout)
            except TimeoutError:
                self._logger.error(f"Task timed out after {timeout} seconds")
                raise  # Re-raise the TimeoutError directly
            except Exception as e:
                self._logger.error(f"Error in task execution: {e}")
                raise TaskExecutionError(f"Error in task execution: {e}") from e

        except Exception as e:
            if not isinstance(e, TimeoutError):  # Only wrap non-TimeoutError exceptions
                self._logger.error(f"Error running task: {e}")
                raise TaskExecutionError(f"Error running task: {e}") from e
            raise  # Re-raise TimeoutError directly
