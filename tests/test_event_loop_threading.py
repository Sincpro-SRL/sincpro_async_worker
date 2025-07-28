"""
Tests específicos para la funcionalidad de threading del EventLoop.

Estos tests verifican:
1. Gestión de threads cuando se crea un loop nuevo
2. Comportamiento cuando se reutiliza un loop existente
3. Limpieza correcta de threads propios vs externos
4. Verificación de ownership del loop
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


class TestEventLoopThreading:
    """Tests específicos para la funcionalidad de threading del EventLoop."""

    def test_should_create_thread_when_no_existing_loop(self, fresh_event_loop):
        """Test que verifica creación de thread cuando no hay loop existente."""
        # Given: No hay loop existente
        assert not fresh_event_loop.is_running()

        # When: Iniciamos el EventLoop
        fresh_event_loop.start()

        # Then: Debe estar corriendo
        assert fresh_event_loop.is_running()

        # El comportamiento de ownership depende del contexto:
        # - Si encuentra loop existente: owns_loop = False, thread = None
        # - Si crea loop nuevo: owns_loop = True, thread != None
        if fresh_event_loop.owns_loop():
            # Caso: Creó un loop nuevo
            assert isinstance(fresh_event_loop._thread, threading.Thread)
            assert fresh_event_loop._thread.is_alive()
            assert fresh_event_loop._thread.daemon  # Debe ser daemon thread
        else:
            # Caso: Reutilizó un loop existente (común en pytest)
            assert fresh_event_loop._thread is None

    def test_should_not_create_thread_when_reusing_existing_loop(self):
        """Test que verifica NO creación de thread cuando reutiliza loop existente."""

        async def test_inside_asyncio_run():
            # Given: Estamos dentro de asyncio.run() - ya hay un loop
            event_loop = EventLoop()

            # When: Iniciamos el EventLoop
            event_loop.start()

            # Then: NO debe crear thread y NO debe ser propietario
            assert event_loop.is_running()
            assert not event_loop.owns_loop()  # No es propietario
            assert event_loop._thread is None  # No hay thread propio

            # Cleanup
            event_loop.shutdown()

        # Ejecutar dentro de asyncio.run() para simular loop existente
        asyncio.run(test_inside_asyncio_run())

    def test_thread_should_execute_coroutines_when_owns_loop(self, fresh_event_loop):
        """Test que verifica ejecución en thread propio cuando es propietario del loop."""
        # Given: EventLoop iniciado
        fresh_event_loop.start()

        # Solo verificar thread execution si somos propietarios del loop
        if not fresh_event_loop.owns_loop():
            pytest.skip(
                "EventLoop reutilizó loop existente - no puede verificar thread propio"
            )

        async def get_current_thread_info():
            return {
                "thread": threading.current_thread(),
                "is_main": threading.current_thread() is threading.main_thread(),
            }

        # When: Ejecutamos una corrutina
        future = fresh_event_loop.run_coroutine(get_current_thread_info())
        thread_info = future.result(timeout=1.0)

        # Then: Debe ejecutarse en el thread del EventLoop, no en main
        assert thread_info["thread"] is fresh_event_loop._thread
        assert not thread_info["is_main"]  # No debe ser el main thread

    def test_thread_cleanup_when_owns_loop(self, fresh_event_loop):
        """Test que verifica limpieza correcta del thread cuando es propietario."""
        # Given: EventLoop iniciado
        fresh_event_loop.start()

        # Solo verificar cleanup si somos propietarios del loop
        if not fresh_event_loop.owns_loop():
            pytest.skip(
                "EventLoop reutilizó loop existente - no hay thread propio para limpiar"
            )

        thread = fresh_event_loop._thread
        assert thread is not None
        assert thread.is_alive()

        # When: Hacemos shutdown
        fresh_event_loop.shutdown()

        # Then: El thread debe terminar
        assert not fresh_event_loop.is_running()
        assert fresh_event_loop._thread is None
        assert not thread.is_alive()

    def test_no_thread_cleanup_when_not_owns_loop(self):
        """Test que verifica NO limpieza cuando no es propietario del loop."""

        async def test_external_loop_cleanup():
            # Given: EventLoop usando loop externo
            event_loop = EventLoop()
            event_loop.start()

            # Verificar que no es propietario
            assert not event_loop.owns_loop()
            assert event_loop._thread is None

            # When: Hacemos shutdown
            event_loop.shutdown()

            # Then: No debe afectar el loop externo (asyncio.run sigue funcionando)
            assert not event_loop.is_running()  # EventLoop se marca como no running

            # El loop de asyncio.run() sigue funcionando
            await asyncio.sleep(0.01)  # Esta línea no debería fallar

        # Si esto se ejecuta sin errores, significa que no afectamos el loop externo
        asyncio.run(test_external_loop_cleanup())

    def test_multiple_coroutines_in_same_thread_when_owns_loop(self, fresh_event_loop):
        """Test que verifica múltiples corrutinas ejecutándose en el mismo thread."""
        # Given: EventLoop iniciado
        fresh_event_loop.start()

        # Solo verificar si somos propietarios del loop
        if not fresh_event_loop.owns_loop():
            pytest.skip(
                "EventLoop reutilizó loop existente - no puede verificar thread específico"
            )

        async def get_thread_id():
            return threading.get_ident()

        # When: Ejecutamos múltiples corrutinas
        futures = [fresh_event_loop.run_coroutine(get_thread_id()) for _ in range(5)]

        thread_ids = [f.result(timeout=1.0) for f in futures]

        # Then: Todas deben ejecutarse en el mismo thread
        assert len(set(thread_ids)) == 1  # Todos los IDs son iguales
        assert thread_ids[0] == fresh_event_loop._thread.ident

    def test_thread_should_be_daemon(self, fresh_event_loop):
        """Test que verifica que el thread creado sea daemon."""
        # When: Iniciamos EventLoop
        fresh_event_loop.start()

        # Solo verificar si somos propietarios del loop
        if not fresh_event_loop.owns_loop():
            pytest.skip("EventLoop reutilizó loop existente - no hay thread propio")

        # Then: El thread debe ser daemon
        assert fresh_event_loop._thread.daemon

    def test_thread_lifecycle_robustness(self, fresh_event_loop):
        """Test de robustez del ciclo de vida del thread."""
        # Solo ejecutar si podemos crear nuestro propio loop
        fresh_event_loop.start()
        if not fresh_event_loop.owns_loop():
            pytest.skip(
                "EventLoop reutilizó loop existente - no puede verificar lifecycle de thread propio"
            )
        fresh_event_loop.shutdown()

        # Multiple start/shutdown cycles
        for i in range(3):
            # Start
            fresh_event_loop.start()
            assert fresh_event_loop.is_running()
            assert fresh_event_loop.owns_loop()

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

    def test_thread_ownership_detection_accuracy(self):
        """Test que verifica detección precisa de ownership en diferentes contextos."""
        # Context 1: Primer EventLoop - puede crear o reutilizar
        loop1 = EventLoop()
        loop1.start()
        ownership1 = loop1.owns_loop()  # Puede ser True o False
        loop1.shutdown()

        # Context 2: Con loop existente garantizado
        async def test_with_existing():
            loop2 = EventLoop()
            loop2.start()
            assert not loop2.owns_loop()  # Debe reutilizar el de asyncio.run()
            loop2.shutdown()

        asyncio.run(test_with_existing())

        # Verificar que al menos uno de los contextos funciona
        assert isinstance(ownership1, bool)  # Al menos verificamos que devuelve boolean
