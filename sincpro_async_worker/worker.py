"""
Worker component that manages the event loop thread or subprocess.
"""

import asyncio
import atexit
import logging
import multiprocessing as mp
import threading
from typing import Optional

from sincpro_async_worker.event_loop import EventLoop
from sincpro_async_worker.exceptions import WorkerNotRunningError
from sincpro_async_worker.domain.worker import (
    ExecutionMode,
    ProcessId,
    ThreadId,
    WorkerStatus,
    WorkerInterface
)
from sincpro_async_worker.task_queue import ThreadTaskQueue, ProcessTaskQueue, TaskQueue

class Worker(WorkerStatus, WorkerInterface):
    """
    Manages the event loop in either a thread or subprocess.
    Handles starting and stopping the event loop.
    """
    
    def __init__(self) -> None:
        """Initialize the Worker component."""
        self._logger = logging.getLogger(__name__)
        self._event_loop = EventLoop()
        self._thread: Optional[threading.Thread] = None
        self._process: Optional[mp.Process] = None
        self._started = False
        self._mode: ExecutionMode = ExecutionMode.THREAD
        self._task_queue: Optional[ThreadTaskQueue | ProcessTaskQueue] = None
        
        # Register cleanup at process termination
        atexit.register(self.shutdown)
    
    @property
    def process_id(self) -> Optional[ProcessId]:
        """Get the process ID if running in subprocess mode."""
        if self._process and self._process.is_alive():
            return ProcessId(self._process.pid)
        return None
    
    @property
    def thread_id(self) -> Optional[ThreadId]:
        """Get the thread ID if running in thread mode."""
        if self._thread and self._thread.is_alive():
            return ThreadId(self._thread.ident or 0)
        return None
    
        
    @property
    def is_running(self) -> bool:
        """Check if the worker is running."""
        return self._started
    
    @property
    def mode(self) -> ExecutionMode:
        """Get the current execution mode."""
        return self._mode

    
    def start(self, mode: ExecutionMode = ExecutionMode.THREAD) -> None:
        """
        Start the worker in the specified mode.
        
        Args:
            mode: Execution mode, either THREAD or SUBPROCESS.
                 Defaults to THREAD.
        """
        if self._started:
            return
            
        self._logger.info(f"Starting worker in {mode.name} mode")
        self._mode = mode
        
        # Initialize the appropriate task queue
        match mode:
            case ExecutionMode.THREAD:
                self._task_queue = ThreadTaskQueue()
            case ExecutionMode.SUBPROCESS:
                self._task_queue = ProcessTaskQueue()
        
        match mode:
            case ExecutionMode.THREAD:
                self._start_thread()
            case ExecutionMode.SUBPROCESS:
                self._start_subprocess()
        
        self._started = True
        self._logger.info("Worker started successfully")
    
    def _start_thread(self) -> None:
        """Start the event loop in a thread."""
        self._thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self._thread.start()
    
    def _start_subprocess(self) -> None:
        """Start the event loop in a subprocess."""
        self._process = mp.Process(target=self._run_event_loop, daemon=True)
        self._process.start()
    
    def _run_event_loop(self) -> None:
        """Run the event loop in the current process/thread context."""
        try:
            # Setup the event loop in the current context
            self._event_loop.setup()
            self._event_loop.set_running(True)
            
            # Get the event loop
            loop = self._event_loop.get_loop()
            
            # Run the event loop until shutdown is requested
            while self._event_loop.is_running():
                try:
                    # Process tasks from the queue
                    if not self._task_queue.empty():
                        coro = self._task_queue.get()
                        loop.create_task(coro)
                    
                    loop.run_forever()
                except KeyboardInterrupt:
                    self._logger.info("Received keyboard interrupt, shutting down...")
                    break
                except Exception as e:
                    self._logger.error(f"Error in event loop: {e}")
                    break
        except Exception as e:
            self._logger.error(f"Failed to initialize event loop: {e}")
        finally:
            # Ensure cleanup happens in all cases
            try:
                self._event_loop.set_running(False)
                self._event_loop.close()
            except Exception as e:
                self._logger.error(f"Error during event loop cleanup: {e}")
            self._started = False
    
    def shutdown(self) -> None:
        """Stop the worker and clean up resources."""
        if not self._started:
            return
            
        self._logger.info("Stopping worker")
        self._event_loop.set_running(False)
        
        # Stop the event loop
        try:
            loop = self._event_loop.get_loop()
            loop.call_soon_threadsafe(loop.stop)
        except Exception as e:
            self._logger.error(f"Error stopping event loop: {e}")
        
        # Wait for the thread/process to finish
        match self._mode:
            case ExecutionMode.THREAD if self._thread:
                self._thread.join(timeout=5.0)
            case ExecutionMode.SUBPROCESS if self._process:
                self._process.join(timeout=5.0)
                if self._process.is_alive():
                    self._process.terminate()
        
        self._started = False
        self._logger.info("Worker stopped successfully")
    
    def get_event_loop(self) -> asyncio.AbstractEventLoop:
        """Get the event loop instance."""
        if not self._started:
            raise WorkerNotRunningError("Worker has not been started")
        return self._event_loop.get_loop()
    
    def get_task_queue(self) -> TaskQueue:
        """Get the task queue instance."""
        if not self._task_queue:
            raise WorkerNotRunningError("Worker has not been started")
        return self._task_queue
