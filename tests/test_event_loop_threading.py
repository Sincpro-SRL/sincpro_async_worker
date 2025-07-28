"""
Tests específicos para la funcionalidad de threading del EventLoop.

Estos tests verifican que el EventLoop SIEMPRE use la estrategia "Thread Dedicado":
1. SIEMPRE crea su propio thread con event loop aislado
2. NUNCA reutiliza event loops existentes
3. SIEMPRE es propietario de su loop
4. NO interfiere con el proceso principal o loops externos
"""

import asyncio
import threading
import time

import pytest

from sincpro_async_worker.infrastructure.event_loop import EventLoop


@pytest.fixture
def fresh_event_loop():
    """Fixture que proporciona un EventLoop limpio para tests de threading."""
    loop = EventLoop()
    yield loop
    # Cleanup
    if loop.is_running():
        loop.shutdown()


def test_should_always_create_dedicated_thread():
    """Test que verifica que SIEMPRE se crea un thread dedicado."""
    # Given: EventLoop nuevo
    event_loop = EventLoop()
    assert not event_loop.is_running()

    # When: Iniciamos el EventLoop
    event_loop.start()

    # Then: SIEMPRE debe crear thread dedicado
    assert event_loop.is_running()
    assert event_loop._thread is not None
    assert event_loop._thread.daemon
    assert event_loop._thread.name == "AsyncWorkerThread"

    # Cleanup
    event_loop.shutdown()


def test_should_create_dedicated_thread_even_inside_asyncio_run():
    """Test que verifica thread dedicado incluso dentro de asyncio.run()."""

    async def test_inside_existing_loop():
        # Given: Estamos dentro de asyncio.run() - ya hay un loop corriendo
        # Verificar que hay un loop externo
        external_loop = asyncio.get_running_loop()
        assert external_loop is not None

        # When: Creamos nuestro EventLoop
        event_loop = EventLoop()
        event_loop.start()

        # Then: DEBE crear su propio thread dedicado, NO reutilizar el externo
        assert event_loop.is_running()
        assert event_loop._thread is not None
        assert event_loop._loop is not external_loop

        # Cleanup
        event_loop.shutdown()

        # El loop externo debe seguir funcionando (no se afecta)
        await asyncio.sleep(0.01)  # Esta línea confirma que el loop externo funciona

    # Ejecutar dentro de asyncio.run() para demostrar aislamiento
    asyncio.run(test_inside_existing_loop())


def test_should_execute_coroutines_in_dedicated_thread(fresh_event_loop):
    """Test que verifica ejecución en thread dedicado (no en main thread)."""
    # Given: EventLoop iniciado
    fresh_event_loop.start()

    async def get_current_thread_info():
        return {
            "thread": threading.current_thread(),
            "thread_name": threading.current_thread().name,
            "is_main": threading.current_thread() is threading.main_thread(),
        }

    # When: Ejecutamos una corrutina
    future = fresh_event_loop.run_coroutine(get_current_thread_info())
    thread_info = future.result(timeout=1.0)

    # Then: Debe ejecutarse en el thread dedicado, NO en main
    assert thread_info["thread"] is fresh_event_loop._thread
    assert thread_info["thread_name"] == "AsyncWorkerThread"
    assert not thread_info["is_main"]  # NO debe ser el main thread


def test_should_cleanup_dedicated_thread_properly(fresh_event_loop):
    """Test que verifica limpieza correcta del thread dedicado."""
    # Given: EventLoop iniciado
    fresh_event_loop.start()
    thread = fresh_event_loop._thread
    assert thread is not None
    assert thread.is_alive()

    # When: Hacemos shutdown
    fresh_event_loop.shutdown()

    # Then: El thread dedicado debe terminar correctamente
    assert not fresh_event_loop.is_running()
    assert fresh_event_loop._thread is None
    # Dar un momento para que el thread termine
    time.sleep(0.1)
    assert not thread.is_alive()


def test_should_isolate_from_external_loops():
    """Test que verifica aislamiento total de loops externos."""

    async def test_isolation():
        # Given: Loop externo corriendo (asyncio.run)
        external_loop = asyncio.get_running_loop()
        external_task_executed = False

        async def external_task():
            nonlocal external_task_executed
            await asyncio.sleep(0.05)
            external_task_executed = True
            return "external"

        # Iniciar tarea en loop externo
        external_future = asyncio.create_task(external_task())

        # When: Creamos EventLoop dedicado
        event_loop = EventLoop()
        event_loop.start()

        async def dedicated_task():
            await asyncio.sleep(0.05)
            return "dedicated"

        # Ejecutar tarea en loop dedicado
        dedicated_future = event_loop.run_coroutine(dedicated_task())
        assert dedicated_future is not None  # Verificar que se creó el future

        # Then: Ambas tareas deben ejecutarse sin interferencia
        external_result = await external_future
        dedicated_result = dedicated_future.result(timeout=1.0)

        assert external_result == "external"
        assert dedicated_result == "dedicated"
        assert external_task_executed == True

        # Los loops deben ser diferentes
        assert event_loop._loop is not external_loop

        # Cleanup
        event_loop.shutdown()

    asyncio.run(test_isolation())


def test_should_handle_multiple_coroutines_concurrently(fresh_event_loop):
    """Test que verifica múltiples corrutinas ejecutándose concurrentemente en el thread dedicado."""
    # Given: EventLoop iniciado
    fresh_event_loop.start()

    async def get_thread_id():
        return threading.get_ident()

    # When: Ejecutamos múltiples corrutinas
    futures = [fresh_event_loop.run_coroutine(get_thread_id()) for _ in range(5)]

    thread_ids = [f.result(timeout=1.0) for f in futures]

    # Then: Todas deben ejecutarse en el mismo thread dedicado
    assert len(set(thread_ids)) == 1  # Todos los IDs son iguales
    assert thread_ids[0] == fresh_event_loop._thread.ident
    # Y no debe ser el main thread
    assert thread_ids[0] != threading.main_thread().ident


def test_should_support_multiple_start_shutdown_cycles(fresh_event_loop):
    """Test de robustez: múltiples ciclos start/shutdown."""
    # Multiple start/shutdown cycles
    for i in range(3):
        # Start
        fresh_event_loop.start()
        assert fresh_event_loop.is_running()

        # Ejecutar una tarea para verificar que funciona
        async def simple_task():
            return f"iteration_{i}"

        future = fresh_event_loop.run_coroutine(simple_task())
        result = future.result(timeout=1.0)
        assert result == f"iteration_{i}"

        # Shutdown
        fresh_event_loop.shutdown()
        assert not fresh_event_loop.is_running()

        # Brief pause between cycles
        time.sleep(0.01)


def test_dedicated_thread_strategy_consistency():
    """Test que verifica que la estrategia es consistente en diferentes contextos."""

    def test_in_sync_context():
        """Test en contexto síncrono (normal)."""
        loop = EventLoop()
        loop.start()
        result = {"has_thread": loop._thread is not None, "is_running": loop.is_running()}
        loop.shutdown()
        return result

    async def test_in_async_context():
        """Test en contexto asíncrono (dentro de asyncio.run)."""
        loop = EventLoop()
        loop.start()
        result = {"has_thread": loop._thread is not None, "is_running": loop.is_running()}
        loop.shutdown()
        return result

    # Test en contexto sync
    sync_result = test_in_sync_context()

    # Test en contexto async
    async_result = asyncio.run(test_in_async_context())

    # Then: Ambos contextos deben tener el mismo comportamiento
    assert sync_result == async_result
    assert sync_result["has_thread"] == True
    assert sync_result["is_running"] == True
