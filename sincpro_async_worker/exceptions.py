"""
Exception module for sincpro_async_worker.

This module defines specific exceptions that may be raised by the component.
"""


class AsyncWorkerError(Exception):
    """Base exception for errors in the AsyncWorker."""


class TaskExecutionError(AsyncWorkerError):
    """Raised when an error occurs during asynchronous task execution."""


class WorkerNotRunningError(AsyncWorkerError):
    """Raised when trying to use the worker when it's not running."""
