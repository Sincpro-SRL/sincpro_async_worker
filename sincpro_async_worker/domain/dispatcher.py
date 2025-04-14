"""
Domain interface for the Dispatcher component.
"""

from typing import Protocol, TypeVar, Awaitable, Optional

T = TypeVar('T')

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
