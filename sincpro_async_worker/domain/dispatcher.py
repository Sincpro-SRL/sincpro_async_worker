"""
Domain interface for the Dispatcher component.

This module defines the core contract for dispatching async tasks.
The dispatcher coordinates the execution of async coroutines in separate threads,
enabling parallel execution of async subtasks within each coroutine.
"""

import concurrent.futures
from typing import Awaitable, Optional, Protocol, TypeVar, runtime_checkable

# Generic type for async task results
T = TypeVar("T")


@runtime_checkable
class DispatcherInterface(Protocol):
    """
    Interface for the Dispatcher component.

    Defines the contract for executing async coroutines in a separate thread
    with their own event loop. This enables parallel execution of async subtasks
    within the coroutine, similar to Promise.all() behavior in JavaScript.
    """

    def execute(self, task: Awaitable[T], timeout: Optional[float] = None) -> T:
        """
        Execute an async coroutine and wait for its completion (blocking mode).

        This method executes the coroutine in a separate thread with its own event loop,
        allowing async subtasks within the coroutine to run in parallel. The calling
        thread blocks until the coroutine completes or times out.

        Args:
            task: The async coroutine to execute. Can contain multiple async operations
                  that will be executed in parallel within the event loop.
            timeout: Optional timeout in seconds. If the coroutine doesn't complete
                    within this time, a TimeoutError is raised.

        Returns:
            The result of the async coroutine execution.

        Raises:
            TimeoutError: If the task takes longer than timeout seconds
            RuntimeError: If the worker system is not available
            Exception: Any exception raised by the coroutine

        Example:
            async def fetch_multiple():
                async with httpx.AsyncClient() as client:
                    tasks = [client.get(url) for url in urls]
                    return await asyncio.gather(*tasks)

            # All HTTP requests run in parallel within the coroutine
            results = dispatcher.execute(fetch_multiple(), timeout=30)
        """
        ...

    def execute_async(self, task: Awaitable[T]) -> concurrent.futures.Future[T]:
        """
        Execute an async coroutine in fire-and-forget mode (non-blocking).

        This method starts the coroutine execution in a separate thread and
        returns immediately with a Future. The coroutine can contain parallel
        async subtasks that run concurrently within the event loop.

        Args:
            task: The async coroutine to execute. Can contain multiple async operations
                  that will be executed in parallel within the event loop.

        Returns:
            A concurrent.futures.Future representing the eventual result of the coroutine.
            Use future.result(timeout) to retrieve the result when ready.

        Raises:
            RuntimeError: If the worker system is not available

        Example:
            async def background_processing():
                async with httpx.AsyncClient() as client:
                    tasks = [process_data(client, item) for item in items]
                    return await asyncio.gather(*tasks)

            # Start processing in background, return immediately
            future = dispatcher.execute_async(background_processing())

            # Do other work...

            # Retrieve result when ready
            results = future.result(timeout=60)
        """
        ...
