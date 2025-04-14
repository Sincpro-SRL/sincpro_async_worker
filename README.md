# Sincpro Async Worker

Una solución simple para ejecutar tareas asíncronas desde código síncrono.

## Propósito

Esta librería está diseñada para escenarios donde necesitas ejecutar operaciones asíncronas desde código síncrono, sin la complejidad de implementar una solución completa de colas de mensajes.

## Casos de Uso Principales

1. **Ejecución de tareas asíncronas desde frameworks síncronos**
   - Ejecutar operaciones I/O asíncronas desde frameworks web síncronos
   - Manejar operaciones de red sin bloquear el hilo principal

2. **Aislamiento de operaciones asíncronas**
   - Ejecutar tareas asíncronas en un hilo separado
   - Mantener el código síncrono limpio y simple

3. **Despacho simple de tareas**
   - Para escenarios donde una cola de mensajes sería excesivo
   - Tareas que no requieren persistencia o garantías de entrega

## Cuándo NO usar esta librería

Esta librería NO está diseñada para:
- Sistemas distribuidos
- Tareas que requieren garantías de entrega
- Escenarios que necesitan persistencia de mensajes
- Sistemas que requieren alta disponibilidad

Para estos casos, considera usar soluciones más robustas como:
- RabbitMQ
- Apache Kafka
- Celery

## Instalación

```bash
pip install sincpro-async-worker
```

## Uso Básico

```python
from sincpro_async_worker import run_async_task

# Ejecutar tarea asíncrona
async def mi_tarea():
    await asyncio.sleep(1)
    return "hecho"

resultado = run_async_task(mi_tarea())

# Opcionalmente, puedes especificar un timeout
resultado = run_async_task(mi_tarea(), timeout=5.0)
```

## Características

- **Ejecución en hilo separado**: Las tareas se ejecutan en un hilo dedicado
- **Manejo de timeouts**: Soporte para timeouts en la ejecución de tareas
- **Propagación de excepciones**: Las excepciones se propagan correctamente al hilo principal
- **Limpieza automática**: Los recursos se liberan automáticamente

## Contribuciones

Las contribuciones son bienvenidas. Por favor, asegúrate de:
1. Seguir las guías de estilo del proyecto
2. Incluir tests para nuevas funcionalidades
3. Actualizar la documentación según sea necesario

## Licencia

SINCPRO S.R.L.