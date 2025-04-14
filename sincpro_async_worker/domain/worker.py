"""
Worker domain abstractions and value objects.
"""

import asyncio
from enum import StrEnum
from typing import NewType, Protocol, runtime_checkable

from sincpro_async_worker.domain.queue import TaskQueue

# Value Objects
ProcessId = NewType("ProcessId", int)
ThreadId = NewType("ThreadId", int)


class ExecutionMode(StrEnum):
    """
    Execution mode for the worker.

    Attributes:
        THREAD: Run the worker in a thread (default)
        SUBPROCESS: Run the worker in a separate process
    """

    THREAD = "thread"
    SUBPROCESS = "subprocess"


@runtime_checkable
class WorkerStatus(Protocol):
    """Protocol defining the status of a worker."""

    is_running: bool
    mode: ExecutionMode
    process_id: ProcessId | None
    thread_id: ThreadId | None


@runtime_checkable
class WorkerInterface(Protocol):
    """Protocol defining the worker interface."""

    def start(self, mode: ExecutionMode = ExecutionMode.THREAD) -> None:
        """Start the worker in the specified mode."""
        ...

    def shutdown(self) -> None:
        """Stop the worker and clean up resources."""
        ...

    def get_event_loop(self) -> asyncio.AbstractEventLoop:
        """Get the event loop instance."""
        ...

    def get_task_queue(self) -> TaskQueue:
        """Get the task queue instance."""
        ...
