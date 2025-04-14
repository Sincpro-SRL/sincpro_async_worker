"""
Core implementation of the async worker functionality.
"""

from typing import Any, Coroutine, Optional, TypeVar

from sincpro_async_worker.dispatcher import Dispatcher
from sincpro_async_worker.domain.worker import ExecutionMode
from sincpro_async_worker.worker import Worker

T = TypeVar("T")

# Singleton worker instance
_worker: Optional[Worker] = None
_dispatcher: Optional[Dispatcher] = None


def _ensure_worker_started(mode: ExecutionMode = ExecutionMode.THREAD) -> None:
    """
    Ensure the worker is started in the specified mode.

    Args:
        mode: Execution mode, either THREAD or SUBPROCESS.
             Defaults to THREAD.
    """
    global _worker, _dispatcher

    if _worker is None:
        _worker = Worker()
        _worker.start(mode)
        _dispatcher = Dispatcher(_worker)


def run_async_task(
    coro: Coroutine[Any, Any, T],
    wait_for_result: bool = False,
    timeout: Optional[float] = None,
    mode: ExecutionMode = ExecutionMode.THREAD,
) -> Optional[T]:
    """
    Run an async task in the event loop.

    This is the main interface for executing async tasks. If the worker
    hasn't been started, it will be automatically initialized.

    Args:
        coro: Coroutine to execute.
        wait_for_result: If True, wait for and return the result.
        timeout: Maximum time to wait for the result in seconds.
        mode: Execution mode, either THREAD or SUBPROCESS.
             Defaults to THREAD.

    Returns:
        The result of the coroutine if wait_for_result is True, otherwise None.

    Raises:
        TaskExecutionError: If an error occurs during task execution.
        TimeoutError: If the operation times out.
    """
    _ensure_worker_started(mode)
    assert _dispatcher is not None  # For type checking

    return _dispatcher.run(coro, wait_for_result, timeout)


def shutdown() -> None:
    """Shutdown the worker and clean up resources."""
    global _worker, _dispatcher

    if _worker is not None:
        _worker.shutdown()
        _worker = None
        _dispatcher = None
