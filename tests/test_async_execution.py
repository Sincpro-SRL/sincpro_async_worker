"""
Test suite for async execution scenarios.
Focus on testing the worker's ability to handle async tasks properly.
"""

import asyncio
import pytest
from sincpro_async_worker.infrastructure import Worker
from sincpro_async_worker.domain.worker import ExecutionMode


@pytest.fixture
def worker():
    """Fixture that provides a clean Worker instance for each test."""
    worker = Worker()
    yield worker
    if worker.is_running:
        worker.shutdown()
        # Wait for worker to fully shutdown
        if worker.thread_id:
            worker.thread.join(timeout=1.0)
        if worker.process_id:
            worker.process.join(timeout=1.0)


@pytest.mark.asyncio
async def test_async_task_execution(worker):
    """Test basic async task execution."""
    worker.start()
    
    try:
        async def simple_task():
            await asyncio.sleep(0.1)
            return "success"
        
        result = await worker.run(simple_task())
        assert result == "success"
    finally:
        worker.shutdown()


@pytest.mark.asyncio
async def test_concurrent_async_tasks(worker):
    """Test concurrent execution of multiple async tasks."""
    worker.start()
    
    try:
        async def task(i: int):
            await asyncio.sleep(0.1)
            return i
        
        # Create and run multiple tasks concurrently
        tasks = [worker.run(task(i)) for i in range(3)]
        results = await asyncio.gather(*tasks)
        
        assert sorted(results) == list(range(3))
    finally:
        worker.shutdown()


@pytest.mark.asyncio
async def test_async_task_with_exception(worker):
    """Test handling of exceptions in async tasks."""
    worker.start()
    
    try:
        async def failing_task():
            await asyncio.sleep(0.1)
            raise ValueError("Task failed")
        
        with pytest.raises(ValueError, match="Task failed"):
            await worker.run(failing_task())
    finally:
        worker.shutdown()


@pytest.mark.asyncio
async def test_async_task_timeout(worker):
    """Test timeout handling in async tasks."""
    worker.start()
    
    try:
        async def long_running_task():
            await asyncio.sleep(1.0)  # Task that takes longer than timeout
            return "success"
        
        with pytest.raises(asyncio.TimeoutError):
            await worker.run(long_running_task(), timeout=0.1)
    finally:
        worker.shutdown() 