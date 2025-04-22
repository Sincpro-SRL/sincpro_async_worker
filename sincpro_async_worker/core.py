"""
Core implementation of the async worker functionality.
"""

from typing import Awaitable, Optional, TypeVar

from sincpro_async_worker.infrastructure.dispatcher import Dispatcher

T = TypeVar("T")

_dispatcher: Optional[Dispatcher] = None


def run_async_task(
    task: Awaitable[T],
    timeout: Optional[float] = None,
) -> T:
    """
    Run an async task in the event loop.

    This is the main interface for executing async tasks. If the dispatcher
    hasn't been initialized, it will be automatically created.

    Args:
        task: Async task to execute
        timeout: Maximum time to wait for the result in seconds

    Returns:
        The result of the task

    Raises:
        TimeoutError: If the operation times out
        Exception: Any exception raised by the task
    """
    global _dispatcher

    if _dispatcher is None:
        _dispatcher = Dispatcher()

    return _dispatcher.execute(task, timeout)
