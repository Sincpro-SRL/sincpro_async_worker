"""
Task queue implementation for inter-process communication.
"""

import asyncio
import multiprocessing as mp
from typing import Any, Coroutine

from sincpro_async_worker.domain.queue import TaskQueue

class ThreadTaskQueue(TaskQueue):
    """Task queue implementation for thread-based execution."""
    
    def __init__(self) -> None:
        """Initialize the thread task queue."""
        self._queue: asyncio.Queue[Coroutine[Any, Any, Any]] = asyncio.Queue()
    
    def put(self, coro: Coroutine[Any, Any, Any]) -> None:
        """Put a coroutine in the queue."""
        self._queue.put_nowait(coro)
    
    async def get(self) -> Coroutine[Any, Any, Any]:
        """Get a coroutine from the queue."""
        return await self._queue.get()
    
    def empty(self) -> bool:
        """Check if the queue is empty."""
        return self._queue.empty()

class ProcessTaskQueue(TaskQueue):
    """Task queue implementation for process-based execution."""
    
    def __init__(self) -> None:
        """Initialize the process task queue."""
        self._queue: mp.Queue[Coroutine[Any, Any, Any]] = mp.Queue()
    
    def put(self, coro: Coroutine[Any, Any, Any]) -> None:
        """Put a coroutine in the queue."""
        self._queue.put(coro)
    
    def get(self) -> Coroutine[Any, Any, Any]:
        """Get a coroutine from the queue."""
        return self._queue.get()
    
    def empty(self) -> bool:
        """Check if the queue is empty."""
        return self._queue.empty() 