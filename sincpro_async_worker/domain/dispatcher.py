"""
Domain interface for the Dispatcher component.
"""

import concurrent.futures
from typing import Awaitable, Optional, Protocol, TypeVar, runtime_checkable

T = TypeVar("T")


@runtime_checkable
class DispatcherInterface(Protocol):
    """
    Interface for the Dispatcher component.
    Defines the contract that all Dispatcher implementations must follow.
    """

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
        ...

    def execute_async(self, task: Awaitable[T]) -> concurrent.futures.Future[T]:
        """
        Execute an async task and return a Future immediately (fire-and-forget).

        Args:
            task: The async task to execute

        Returns:
            A concurrent.futures.Future representing the eventual result of the task
        """
        ...
