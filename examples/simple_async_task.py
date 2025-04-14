"""
Example demonstrating the use of the simple async task interface.
"""

import asyncio
import logging
from sincpro_async_worker import run_async_task, shutdown

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def my_task(duration: float) -> str:
    """
    Example async task that simulates an I/O operation.
    
    Args:
        duration: How long to sleep in seconds.
        
    Returns:
        str: A message indicating the task completed.
    """
    logger.info(f"Starting task, will sleep for {duration} seconds")
    await asyncio.sleep(duration)
    return f"Task completed after {duration} seconds"

def main():
    try:
        # Example 1: Fire-and-forget task
        logger.info("Submitting fire-and-forget task")
        run_async_task(my_task(1.0), wait_for_result=False)
        
        # Example 2: Task with result
        logger.info("Submitting task with result")
        result = run_async_task(my_task(2.0), wait_for_result=True)
        logger.info(f"Got result: {result}")
        
        # Example 3: Task with timeout
        logger.info("Submitting task with timeout")
        try:
            result = run_async_task(my_task(3.0), wait_for_result=True, timeout=1.0)
            logger.info(f"Got result: {result}")
        except TimeoutError:
            logger.warning("Task timed out as expected")
            
    finally:
        # Clean shutdown
        shutdown()

if __name__ == "__main__":
    main() 