# Sincpro Async Worker

Asynchronous component for sincpro_framework that enables executing asynchronous tasks (e.g., sending logs or HTTP requests) in a primarily synchronous environment.

## Features

- **Single worker per process**: Manages a single asynchronous event loop in a dedicated thread.
- **Simple API**: Minimalist "fire-and-forget" interface for executing asynchronous tasks.
- **Multitasking**: Executes multiple asynchronous tasks without blocking the main thread.
- **Result handling**: Optional retrieval of results when needed.
- **Robust error handling**: Proper handling of exceptions and errors in asynchronous tasks.
- **Graceful shutdown**: Ensures all pending tasks complete or are properly cancelled at termination.

## Installation

```bash
pip install sincpro-async-worker
```

Or using poetry:

```bash
poetry add sincpro-async-worker
```

## Basic Usage

The component API is designed to be as simple as possible:

```python
import asyncio
from sincpro_async_worker import start, run_async_task, run_async_tasks

# Start the worker (do this once at the beginning of your application)
start()

# Define an asynchronous task
async def my_task():
    await asyncio.sleep(1)  # I/O operation
    return "Result"

# Execute task without waiting for result (fire-and-forget)
run_async_task(my_task())

# Or execute and wait for the result
result = run_async_task(my_task(), wait_for_result=True)
print(f"Result: {result}")

# Or execute multiple tasks
tasks = [my_task() for _ in range(5)]
results = run_async_tasks(tasks, wait_all=True)
```

## API Reference

### `start()`

Starts the asynchronous worker. Must be called once at the beginning of your application.

```python
from sincpro_async_worker import start

start()  # Starts the asynchronous worker
```

### `run_async_task(coro, *, wait_for_result=False, timeout=None)`

Executes an asynchronous task.

- `coro`: The coroutine to execute.
- `wait_for_result`: If `True`, waits and returns the task result. If `False` (default), executes the task in "fire-and-forget" mode.
- `timeout`: Optional timeout in seconds to wait for the result (if `wait_for_result=True`).

```python
# Execute without waiting for result (fire-and-forget)
run_async_task(my_task())

# Execute and wait for result with timeout
result = run_async_task(my_task(), wait_for_result=True, timeout=5.0)
```

### `run_async_tasks(coros, *, wait_all=False, timeout=None)`

Executes multiple asynchronous tasks.

- `coros`: List of coroutines to execute.
- `wait_all`: If `True`, waits and returns the results of all tasks. If `False` (default), executes the tasks in "fire-and-forget" mode.
- `timeout`: Optional timeout in seconds to wait for the results (if `wait_all=True`).

```python
# Execute multiple tasks without waiting
tasks = [task1(), task2(), task3()]
run_async_tasks(tasks)

# Execute and wait for results of all tasks
results = run_async_tasks([task1(), task2(), task3()], wait_all=True)
```

### `shutdown()`

Stops the asynchronous worker in an orderly manner. Normally, you don't need to call this function as it's automatically registered with `atexit`.

```python
from sincpro_async_worker import shutdown

# At termination (optional, as it's registered with atexit)
shutdown()
```

### `get_stats()`

Gets statistics from the asynchronous worker.

```python
from sincpro_async_worker import get_stats

# Get statistics
stats = get_stats()
print(f"Pending tasks: {stats['pending_tasks_count']}")
```

## Integration Examples with sincpro_framework

### Example with sincpro_logger

```python
import asyncio
from sincpro_async_worker import start, run_async_task
from sincpro_logger import Logger

# Start the worker
start()

async def send_log_async(log_data):
    # Simulate a costly operation like sending to a remote server
    await asyncio.sleep(0.1)
    print(f"Log sent: {log_data}")

class AsyncLogger(Logger):
    def log(self, level, message, **context):
        # Asynchronous version of the log method
        log_data = self._format_log(level, message, **context)
        run_async_task(send_log_async(log_data))
        
# Usage
logger = AsyncLogger()
logger.info("Operation completed", user_id=123)  # Doesn't block the main thread
```

### Example with sincpro_siat_soap (electronic billing)

```python
import asyncio
from sincpro_async_worker import start, run_async_task
from sincpro_siat_soap import SiatClient

# Start the worker
start()

async def send_invoice_async(invoice_data):
    await asyncio.sleep(0.5)  # Simulates invoice sending
    return {"status": "ACCEPTED", "invoice_number": "123456"}

class AsyncSiatClient(SiatClient):        
    def send_invoice_async(self, invoice_data):
        """Sends invoice asynchronously without waiting for response"""
        run_async_task(send_invoice_async(invoice_data))
        
    def send_invoice(self, invoice_data):
        """Sends invoice and waits for response (synchronous method)"""
        return run_async_task(send_invoice_async(invoice_data), wait_for_result=True)

# Usage
client = AsyncSiatClient()
client.send_invoice_async({"id": "F001", "amount": 100})  # Doesn't block
response = client.send_invoice({"id": "F002", "amount": 200})  # Blocks until response received
```

## Performance Considerations

- **uvloop**: On Unix/Linux systems, the component uses uvloop to improve event loop performance if available.
- **Timeouts**: All operations can be configured with timeouts to avoid indefinite blocking.
- **Error handling**: Errors in "fire-and-forget" tasks don't stop the application but are logged for debugging.

## Running Tests

To run the tests, use pytest:

```bash
pytest
```

Or with coverage:

```bash
pytest --cov=sincpro_async_worker
```

## License

This component is subject to the business license of Sincpro S.R.L., and its use is governed by the terms and conditions established in the LICENSE.md file.