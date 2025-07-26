"""
Core implementation of the async worker functionality.
"""

import concurrent.futures
from typing import Awaitable, Optional, TypeVar, Union

from sincpro_async_worker.infrastructure.dispatcher import Dispatcher

T = TypeVar("T")

_dispatcher: Optional[Dispatcher] = None


def run_async_task(
    task: Awaitable[T],
    timeout: Optional[float] = None,
    fire_and_forget: bool = False,
) -> Union[T, concurrent.futures.Future[T]]:
    """
    Run an async task in the event loop.

    This is the main interface for executing async tasks. If the dispatcher
    hasn't been initialized, it will be automatically created.

    Args:
        task: Async task to execute
        timeout: Maximum time to wait for the result in seconds
        fire_and_forget: If True, returns a Future without waiting for completion

    Returns:
        The result of the task (if fire_and_forget=False) or a Future (if fire_and_forget=True)

    Raises:
        TimeoutError: If the operation times out (only when fire_and_forget=False)
        Exception: Any exception raised by the task (only when fire_and_forget=False)
    """
    global _dispatcher

    if _dispatcher is None:
        _dispatcher = Dispatcher()

    if fire_and_forget:
        return _dispatcher.execute_async(task)
    else:
        return _dispatcher.execute(task, timeout)
