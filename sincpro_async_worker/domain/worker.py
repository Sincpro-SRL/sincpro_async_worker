"""
Domain interface for the Worker component.

This module defines the contract for worker components that execute
async coroutines in dedicated threads with their own event loops.
"""

import concurrent.futures
from typing import Awaitable, Optional, Protocol, TypeVar

# Generic type for async task results
T = TypeVar("T")


class WorkerInterface(Protocol):
    """
    Interface for the Worker component.

    Defines the contract for worker components that manage the execution
    of async coroutines in separate threads, enabling parallel execution
    of async subtasks within each coroutine.
    """

    def start(self) -> None:
        """
        Start the worker thread and its event loop.

        Initializes the worker's event loop in a separate thread,
        ready to execute async coroutines.
        """
        ...

    def run_coroutine(self, coro: Awaitable[T]) -> Optional[concurrent.futures.Future[T]]:
        """
        Execute an async coroutine in the worker's event loop.

        Submits the coroutine for execution in the worker's dedicated thread
        and event loop. The coroutine can contain multiple async operations
        that will run in parallel within that event loop.

        Args:
            coro: The async coroutine to execute. Can contain parallel async subtasks.

        Returns:
            A Future representing the eventual result of the coroutine execution,
            or None if the worker is not available or encounters an error.

        Example:
            async def parallel_tasks():
                tasks = [fetch_data(url) for url in urls]
                return await asyncio.gather(*tasks)

            future = worker.run_coroutine(parallel_tasks())
            results = future.result() if future else None
        """
        ...

    def shutdown(self) -> None:
        """
        Shutdown the worker thread and clean up resources.

        Gracefully stops the worker's event loop and joins the thread.
        Only shuts down resources that the worker owns.
        """
        ...

    def is_running(self) -> bool:
        """
        Check if the worker thread and event loop are running.

        Returns:
            True if the worker is active and ready to execute coroutines.
        """
        ...
