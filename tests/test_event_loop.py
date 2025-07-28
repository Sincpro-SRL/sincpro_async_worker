"""
Tests para las abstracciones fundamentales del EventLoop.

Estos tests verifican:
1. Ciclo de vida básico (start, running, shutdown)
2. Ejecución de corrutinas (funcionalidad core)
3. Manejo de errores y edge cases
4. Comportamiento de la abstracción, NO detalles de implementación
"""

import asyncio

import pytest

from sincpro_async_worker.infrastructure import EventLoop


@pytest.fixture
def event_loop_fixture():
    """
    Fixture que proporciona una instancia limpia de EventLoop.
    """
    loop = EventLoop()
    yield loop
    # Ensure cleanup
    if loop.is_running():
        loop.shutdown()


class TestEventLoopAbstractions:
    """Tests para las abstracciones fundamentales del EventLoop."""

    def test_should_start_in_clean_state(self, event_loop_fixture):
        """Test que verifica estado inicial limpio."""
        assert not event_loop_fixture.is_running()

    def test_should_become_running_after_start(self, event_loop_fixture):
        """Test que verifica transición a estado 'running'."""
        # When: Iniciamos el EventLoop
        event_loop_fixture.start()

        # Then: Debe estar corriendo
        assert event_loop_fixture.is_running()

    def test_start_should_be_idempotent(self, event_loop_fixture):
        """Test que verifica que start() es idempotente."""
        # Given: EventLoop ya iniciado
        event_loop_fixture.start()
        original_loop = event_loop_fixture._loop

        # When: Llamamos start() nuevamente
        event_loop_fixture.start()

        # Then: No debe cambiar el estado
        assert event_loop_fixture.is_running()
        assert event_loop_fixture._loop is original_loop

    def test_get_loop_should_auto_start(self, event_loop_fixture):
        """Test que verifica que get_loop() inicia automáticamente."""
        # Given: EventLoop no iniciado
        assert not event_loop_fixture.is_running()

        # When: Obtenemos el loop
        loop = event_loop_fixture.get_loop()

        # Then: Debe auto-iniciar y devolver un loop válido
        assert event_loop_fixture.is_running()
        assert isinstance(loop, asyncio.AbstractEventLoop)

    def test_should_execute_coroutines_successfully(self, event_loop_fixture):
        """Test que verifica ejecución exitosa de corrutinas."""

        async def simple_coroutine():
            await asyncio.sleep(0.01)
            return "success"

        # When: Ejecutamos una corrutina
        future = event_loop_fixture.run_coroutine(simple_coroutine())
        result = future.result(timeout=1.0)

        # Then: Debe ejecutarse correctamente
        assert result == "success"

    def test_should_handle_coroutine_exceptions(self, event_loop_fixture):
        """Test que verifica manejo de excepciones en corrutinas."""

        async def failing_coroutine():
            raise ValueError("Test error")

        # When: Ejecutamos una corrutina que falla
        future = event_loop_fixture.run_coroutine(failing_coroutine())

        # Then: La excepción debe propagarse
        with pytest.raises(ValueError, match="Test error"):
            future.result(timeout=1.0)

    def test_should_execute_multiple_coroutines_concurrently(self, event_loop_fixture):
        """Test que verifica ejecución concurrente de múltiples corrutinas."""

        async def delayed_result(delay: float, value: str) -> str:
            await asyncio.sleep(delay)
            return value

        # When: Iniciamos múltiples corrutinas con diferentes delays
        future1 = event_loop_fixture.run_coroutine(delayed_result(0.1, "first"))
        future2 = event_loop_fixture.run_coroutine(delayed_result(0.05, "second"))

        # Then: La segunda debe completarse antes que la primera
        assert future2.result(timeout=1.0) == "second"
        assert future1.result(timeout=1.0) == "first"

    def test_should_transition_to_stopped_after_shutdown(self, event_loop_fixture):
        """Test que verifica transición a estado 'stopped' después de shutdown."""
        # Given: EventLoop corriendo
        event_loop_fixture.start()
        assert event_loop_fixture.is_running()

        # When: Hacemos shutdown
        event_loop_fixture.shutdown()

        # Then: No debe estar corriendo
        assert not event_loop_fixture.is_running()

    def test_shutdown_should_be_safe_to_call_multiple_times(self, event_loop_fixture):
        """Test que verifica que shutdown() es seguro de llamar múltiples veces."""
        # Given: EventLoop iniciado y luego cerrado
        event_loop_fixture.start()
        event_loop_fixture.shutdown()

        # When/Then: Múltiples llamadas a shutdown no deben fallar
        event_loop_fixture.shutdown()
        event_loop_fixture.shutdown()

        assert not event_loop_fixture.is_running()

    def test_should_handle_shutdown_when_not_running(self, event_loop_fixture):
        """Test que verifica manejo seguro de shutdown cuando no está corriendo."""
        # Given: EventLoop no iniciado
        assert not event_loop_fixture.is_running()

        # When/Then: Shutdown no debe fallar
        event_loop_fixture.shutdown()
        assert not event_loop_fixture.is_running()

    def test_run_coroutine_should_auto_start_if_not_running(self, event_loop_fixture):
        """Test que verifica auto-inicio cuando se ejecuta corrutina."""
        # Given: EventLoop no iniciado
        assert not event_loop_fixture.is_running()

        async def test_coroutine():
            return "auto_started"

        # When: Ejecutamos corrutina sin haber llamado start()
        future = event_loop_fixture.run_coroutine(test_coroutine())
        result = future.result(timeout=1.0)

        # Then: Debe auto-iniciar y ejecutar correctamente
        assert event_loop_fixture.is_running()
        assert result == "auto_started"

    def test_should_provide_ownership_information(self, event_loop_fixture):
        """Test que verifica que el EventLoop puede reportar si es propietario del loop."""
        # When: Iniciamos EventLoop
        event_loop_fixture.start()

        # Then: Debe poder reportar su estado de ownership
        owns_loop = event_loop_fixture.owns_loop()
        assert isinstance(owns_loop, bool)  # Solo verificamos que devuelve un boolean
