"""
Core implementation of the async worker functionality.
"""

import concurrent.futures
from typing import Awaitable, Optional, TypeVar, Union

from sincpro_async_worker.infrastructure.dispatcher import Dispatcher

# Generic type for async task results
T = TypeVar("T")

_dispatcher: Optional[Dispatcher] = None


def run_async_task(
    task: Awaitable[T],
    timeout: Optional[float] = None,
    fire_and_forget: bool = False,
) -> Union[T, concurrent.futures.Future[T]]:
    """
    Execute an async task with intelligent execution modes.

    This is the main interface for executing async tasks in a separate thread.
    The async task can contain multiple subtasks that run in parallel within
    the event loop, similar to how Promise.all() works in JavaScript.

    Key Features:
    - Executes coroutines in a dedicated thread with its own event loop
    - Supports parallel execution of async subtasks within the coroutine
    - Two execution modes: blocking (wait for result) or fire-and-forget (return Future)
    - Automatic dispatcher initialization and management
    - Thread-safe execution from any thread

    Args:
        task: The async coroutine to execute. This can contain multiple
              async operations that will run in parallel within the event loop.
        timeout: Maximum time to wait for the result in seconds.
                Only applies when fire_and_forget=False.
        fire_and_forget: Execution mode selector:
                        - False: Blocks until completion and returns the result
                        - True: Returns immediately with a Future

    Returns:
        - If fire_and_forget=False: The actual result of the async task
        - If fire_and_forget=True: A concurrent.futures.Future[T] for later retrieval

    Raises:
        TimeoutError: If the operation times out (only when fire_and_forget=False)
        RuntimeError: If the worker system is not available
        Exception: Any exception raised by the async task (only when fire_and_forget=False)

    Examples:
        # Blocking execution (like await)
        result = run_async_task(fetch_data())

        # With timeout
        result = run_async_task(fetch_data(), timeout=30.0)

        # Fire-and-forget execution
        future = run_async_task(fetch_data(), fire_and_forget=True)
        result = future.result(timeout=30)  # Retrieve when ready

        # Parallel async subtasks example
        async def multiple_operations():
            async with httpx.AsyncClient() as client:
                # These run in parallel within the event loop
                tasks = [
                    client.get("https://api1.com/data"),
                    client.get("https://api2.com/data"),
                    client.get("https://api3.com/data"),
                ]
                responses = await asyncio.gather(*tasks)
                return [r.json() for r in responses]

        # Execute all operations in parallel in a separate thread
        results = run_async_task(multiple_operations())
    """
    global _dispatcher

    if _dispatcher is None:
        _dispatcher = Dispatcher()

    if fire_and_forget:
        return _dispatcher.execute_async(task)
    else:
        return _dispatcher.execute(task, timeout)
