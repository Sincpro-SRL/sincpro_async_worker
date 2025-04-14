"""
Tests for the Worker component following TDD approach.
Focus on core use cases:
1. Running async tasks from sync code
2. Task isolation in thread/subprocess
3. Simple task dispatching
"""

import os
import threading
import asyncio
import time

import pytest

from sincpro_async_worker.infrastructure import Worker


@pytest.fixture
def worker():
    """Fixture that provides a clean Worker instance for each test."""
    worker = Worker()
    yield worker
    if worker.is_running():
        worker.stop()


class TestAsyncTaskExecution:
    """Test suite for async task execution from sync code."""
    
    @pytest.mark.asyncio
    async def test_run_simple_async_task(self, worker):
        """Test running a simple async task from sync code."""
        worker.start()
        
        async def simple_task():
            await asyncio.sleep(0.1)
            return "success"
        
        try:
            future = worker.run(simple_task())
            result = await future
            assert result == "success"
        finally:
            worker.stop()
    
    @pytest.mark.asyncio
    async def test_run_async_task_with_error(self, worker):
        """Test error handling in async tasks."""
        worker.start()
        
        async def failing_task():
            raise ValueError("Task failed")
        
        try:
            future = worker.run(failing_task())
            with pytest.raises(ValueError, match="Task failed"):
                await future
        finally:
            worker.stop()


class TestTaskIsolation:
    """Test suite for task isolation in different execution modes."""
    
    @pytest.mark.asyncio
    async def test_thread_isolation(self, worker):
        """Test task isolation in thread mode."""
        worker.start(mode='thread')
        
        try:
            main_thread_id = threading.get_ident()
            
            async def get_thread_id():
                return threading.get_ident()
                
            future = worker.run(get_thread_id())
            worker_thread_id = await future
            
            assert worker_thread_id != main_thread_id
        finally:
            worker.stop()
    
    @pytest.mark.asyncio
    async def test_subprocess_isolation(self, worker):
        """Test task isolation in subprocess mode."""
        worker.start(mode='subprocess')
        
        try:
            main_process_id = os.getpid()
            
            async def get_process_id():
                return os.getpid()
                
            future = worker.run(get_process_id())
            worker_process_id = await future
            
            assert worker_process_id != main_process_id
        finally:
            worker.stop()


class TestTaskDispatching:
    """Test suite for simple task dispatching."""
    
    @pytest.mark.asyncio
    async def test_concurrent_task_execution(self, worker):
        """Test concurrent execution of multiple tasks."""
        worker.start()
        
        try:
            async def task(i: int, delay: float) -> int:
                await asyncio.sleep(delay)
                return i
            
            # Create tasks with same delay to test concurrency
            futures = [
                worker.run(task(i, 0.1))
                for i in range(3)
            ]
            
            start_time = time.time()
            results = await asyncio.gather(*futures)
            end_time = time.time()
            
            # Verify results
            assert sorted(results) == list(range(3))
            
            # Verify concurrent execution
            total_time = end_time - start_time
            assert total_time < 0.5  # Should be around 0.1s if truly concurrent
        finally:
            worker.stop()
