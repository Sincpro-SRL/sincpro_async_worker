"""
Base test module for the async worker.
"""

import asyncio
import time
from typing import List

import pytest

from sincpro_async_worker.core import run_async_task

async def async_task(delay: float) -> str:
    """Simple async task that sleeps for a given delay."""
    await asyncio.sleep(delay)
    return f"Task completed after {delay} seconds"

def test_async_task_execution() -> None:
    """Test that async tasks can be executed."""
    result = run_async_task(async_task(0.1))
    assert result == "Task completed after 0.1 seconds"

def test_async_task_timeout() -> None:
    """Test that async tasks respect timeouts."""
    with pytest.raises(TimeoutError):
        run_async_task(async_task(0.2), timeout=0.1)

async def concurrent_tasks() -> List[str]:
    """Run multiple tasks concurrently."""
    tasks = [async_task(0.1) for _ in range(3)]
    return await asyncio.gather(*tasks)

def test_concurrent_task_execution() -> None:
    """Test that multiple tasks can run concurrently."""
    start_time = time.time()
    
    # Run three tasks concurrently
    results = run_async_task(concurrent_tasks())
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # All tasks should complete in roughly the same time
    assert total_time < 0.2  # Should be close to 0.1 seconds
    assert len(results) == 3
    assert all(r == "Task completed after 0.1 seconds" for r in results) 