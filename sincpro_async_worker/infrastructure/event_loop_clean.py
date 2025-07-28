"""
EventLoop component that manages async execution without conflicts.
Detects and reuses existing event loops when possible.
"""

import asyncio
import concurrent.futures
import logging
import threading
import traceback
import warnings
from typing import Awaitable, Optional, TypeVar

logger = logging.getLogger(__name__)
T = TypeVar("T")


class EventLoopManager:
    """
    Manages async execution in a clean, conflict-free way.
    Automatically detects existing event loops and reuses them.
    """

    def __init__(self) -> None:
        """Initialize the EventLoop manager."""
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._is_active = False
        self._owns_loop = False
        logger.debug("EventLoopManager initialized")

    # Public API - New clean interface

    def start(self) -> None:
        """
        Initialize the event loop management.
        Will detect and reuse existing loops or create a new one.
        """
        if self._is_active:
            logger.warning("EventLoop is already active")
            return

        try:
            self._initialize_event_loop()
        except Exception as e:
            self._handle_initialization_error(e)

    def run_async(self, coroutine: Awaitable[T]) -> Optional[asyncio.Future[T]]:
        """
        Execute a coroutine asynchronously (non-blocking).

        Args:
            coroutine: The async function to execute

        Returns:
            Future object for the result, or None if execution failed
        """
        try:
            loop = self._ensure_loop_is_available()
            if loop is None:
                return None

            return self._submit_coroutine_to_loop(coroutine, loop)

        except Exception as e:
            self._log_execution_error("run_async", e)
            return None

    def run_sync(
        self, coroutine: Awaitable[T], timeout: Optional[float] = None
    ) -> Optional[T]:
        """
        Execute a coroutine and wait for the result (blocking).

        Args:
            coroutine: The async function to execute
            timeout: Maximum time to wait for completion

        Returns:
            The result of the coroutine, or None if failed
        """
        try:
            future = self.run_async(coroutine)
            if future is None:
                return None

            return self._wait_for_future_result(future, timeout)

        except Exception as e:
            self._log_execution_error("run_sync", e)
            return None

    def shutdown(self) -> None:
        """Clean shutdown - only closes loops we own."""
        if not self._is_active:
            return

        try:
            if self._owns_loop:
                self._shutdown_owned_loop()
            else:
                self._clear_external_loop_references()

        except Exception as e:
            self._log_shutdown_error(e)
        finally:
            self._reset_state()

    def is_active(self) -> bool:
        """Check if the event loop manager is active and functional."""
        return self._is_active and self._loop is not None and not self._loop.is_closed()

    def owns_current_loop(self) -> bool:
        """Check if this manager owns the current event loop."""
        return self._owns_loop

    # Legacy API for backward compatibility

    def is_running(self) -> bool:
        """Legacy method - use is_active() instead."""
        return self.is_active()

    def run_coroutine(self, coro: Awaitable[T]) -> Optional[asyncio.Future[T]]:
        """Legacy method - use run_async() instead."""
        return self.run_async(coro)

    def run_coroutine_sync(
        self, coro: Awaitable[T], timeout: Optional[float] = None
    ) -> Optional[T]:
        """Legacy method - use run_sync() instead."""
        return self.run_sync(coro, timeout)

    def get_loop(self) -> Optional[asyncio.AbstractEventLoop]:
        """Get the current event loop, starting if necessary."""
        return self._ensure_loop_is_available()

    def owns_loop(self) -> bool:
        """Legacy method - use owns_current_loop() instead."""
        return self.owns_current_loop()

    # Private implementation methods

    def _initialize_event_loop(self) -> None:
        """Initialize event loop - detect existing or create new."""
        if self._try_use_running_loop():
            return

        if self._try_use_thread_loop():
            return

        self._create_new_loop()

    def _try_use_running_loop(self) -> bool:
        """Attempt to use currently running event loop."""
        try:
            current_loop = asyncio.get_running_loop()
            if self._is_loop_usable(current_loop):
                self._use_existing_loop(current_loop, "running")
                return True
        except RuntimeError:
            pass
        return False

    def _try_use_thread_loop(self) -> bool:
        """Attempt to use thread's event loop."""
        try:
            thread_loop = asyncio.get_event_loop()
            if self._is_loop_usable(thread_loop):
                self._use_existing_loop(thread_loop, "thread")
                self._start_loop_if_needed(thread_loop)
                return True
        except RuntimeError:
            pass
        return False

    def _create_new_loop(self) -> None:
        """Create and start a new event loop."""
        logger.info("Creating new event loop")
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._owns_loop = True
        self._start_loop_in_thread()
        self._is_active = True
        logger.debug("New event loop created and started")

    def _is_loop_usable(self, loop: asyncio.AbstractEventLoop) -> bool:
        """Check if an event loop is usable."""
        return loop is not None and not loop.is_closed()

    def _use_existing_loop(self, loop: asyncio.AbstractEventLoop, source: str) -> None:
        """Configure to use an existing event loop."""
        logger.info(f"Using existing {source} event loop")
        self._loop = loop
        self._is_active = True
        self._owns_loop = False
        logger.debug(f"Configured to use existing {source} loop")

    def _start_loop_if_needed(self, loop: asyncio.AbstractEventLoop) -> None:
        """Start loop in thread if it's not already running."""
        if not loop.is_running():
            self._thread = threading.Thread(target=loop.run_forever, daemon=True)
            self._thread.start()
            self._owns_loop = True

    def _start_loop_in_thread(self) -> None:
        """Start the event loop in a daemon thread."""
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()

    def _ensure_loop_is_available(self) -> Optional[asyncio.AbstractEventLoop]:
        """Ensure we have an active loop, starting if necessary."""
        if not self._is_active:
            logger.info("Loop not active, starting automatically")
            self.start()

        if not self._is_active:
            self._warn_about_unavailable_loop()
            return None

        return self._loop

    def _submit_coroutine_to_loop(
        self, coroutine: Awaitable[T], loop: asyncio.AbstractEventLoop
    ) -> asyncio.Future[T]:
        """Submit coroutine to the appropriate loop context."""
        if self._is_running_in_same_loop(loop):
            return asyncio.create_task(coroutine)
        else:
            return asyncio.run_coroutine_threadsafe(coroutine, loop)

    def _is_running_in_same_loop(self, loop: asyncio.AbstractEventLoop) -> bool:
        """Check if we're running in the same event loop."""
        try:
            current_loop = asyncio.get_running_loop()
            return current_loop is loop
        except RuntimeError:
            return False

    def _wait_for_future_result(
        self, future: asyncio.Future[T], timeout: Optional[float]
    ) -> Optional[T]:
        """Wait for future result, handling different future types."""
        if isinstance(future, asyncio.Task):
            return self._wait_for_task_result(future, timeout)
        else:
            return future.result(timeout=timeout)

    def _wait_for_task_result(
        self, task: asyncio.Task[T], timeout: Optional[float]
    ) -> Optional[T]:
        """Wait for asyncio.Task result with timeout."""
        done, _ = concurrent.futures.wait([task], timeout=timeout)
        if done:
            return done.pop().result()
        else:
            task.cancel()
            return None

    def _shutdown_owned_loop(self) -> None:
        """Shutdown a loop that we own."""
        logger.info("Shutting down owned event loop")

        if self._loop and not self._loop.is_closed():
            self._loop.call_soon_threadsafe(self._loop.stop)

        self._wait_for_thread_termination()

        if self._loop and not self._loop.is_closed():
            self._loop.close()

    def _clear_external_loop_references(self) -> None:
        """Clear references to external loop without closing it."""
        logger.info("Clearing references to external event loop")

    def _wait_for_thread_termination(self) -> None:
        """Wait for the event loop thread to terminate gracefully."""
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

            if self._thread.is_alive():
                logger.warning("Event loop thread did not terminate gracefully")

    def _reset_state(self) -> None:
        """Reset all internal state."""
        self._loop = None
        self._thread = None
        self._is_active = False
        self._owns_loop = False
        logger.debug("Event loop state reset")

    def _handle_initialization_error(self, error: Exception) -> None:
        """Handle errors during initialization."""
        error_msg = f"Failed to initialize event loop: {error}"
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")
        warnings.warn(f"EventLoop initialization failed: {error_msg}", RuntimeWarning)
        self._is_active = False

    def _log_execution_error(self, operation: str, error: Exception) -> None:
        """Log errors during coroutine execution."""
        error_msg = f"Failed to execute {operation}: {error}"
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")
        warnings.warn(error_msg, RuntimeWarning)

    def _log_shutdown_error(self, error: Exception) -> None:
        """Log errors during shutdown."""
        error_msg = f"Error during shutdown: {error}"
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")
        warnings.warn(error_msg, RuntimeWarning)

    def _warn_about_unavailable_loop(self) -> None:
        """Warn when event loop is not available."""
        warning_msg = "Event loop is not available for execution"
        logger.error(warning_msg)
        warnings.warn(warning_msg, RuntimeWarning)


# Mantener retrocompatibilidad
EventLoop = EventLoopManager
