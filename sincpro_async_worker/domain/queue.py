"""
Task queue domain abstractions and value objects.
"""

from typing import Any, Coroutine, Protocol, runtime_checkable

@runtime_checkable
class TaskQueue(Protocol):
    """Protocol defining the task queue interface."""
    
    def put(self, coro: Coroutine[Any, Any, Any]) -> None:
        """Put a coroutine in the queue."""
        ...
    
    def get(self) -> Coroutine[Any, Any, Any]:
        """Get a coroutine from the queue."""
        ...
    
    def empty(self) -> bool:
        """Check if the queue is empty."""
        ... 