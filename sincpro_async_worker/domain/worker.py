"""
Domain interface for the Worker component.
"""

from typing import Awaitable, Optional, Protocol, TypeVar

T = TypeVar("T")


class WorkerInterface(Protocol):
    """
    Interface for the Worker component.
    Defines the contract that all Worker implementations must follow.
    """

    def start(self) -> None:
        """
        Start the worker.
        """
        ...

    def run_coroutine(self, coro: Awaitable[T]) -> Optional[Awaitable[T]]:
        """
        Run a coroutine in the worker's event loop.

        Args:
            coro: The coroutine to run

        Returns:
            An awaitable representing the result of the coroutine, or None if failed
        """
        ...

    def shutdown(self) -> None:
        """
        Shutdown the worker.
        """
        ...

    def is_running(self) -> bool:
        """
        Check if the worker is running.
        """
        ...
