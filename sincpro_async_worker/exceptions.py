"""
Custom exceptions for the async worker.
"""

class WorkerNotRunningError(RuntimeError):
    """Raised when trying to use a worker that is not running."""
    pass
