# Logging y correlación con trazas

El backend escribe logs con **request_id**, **trace_id** y **span_id** para poder cruzar lo que pasa en la aplicación con las trazas que ves en Arize AX (Tracing Projects).

## Qué se añade a cada log

- **request_id:** El mismo que va en el header `X-Request-ID` (generado o enviado por el cliente).
- **trace_id:** ID del trace de OpenTelemetry (coincide con el trace en Arize).
- **span_id:** ID del span actual (llamada LLM, chain, etc.).

Así puedes: buscar en tus logs por `request_id` o `trace_id` y abrir el mismo trace en Arize, o al revés, ver el trace en Arize y buscar en logs por ese `trace_id`.

## Formato de salida

- **Por defecto (legible):** Cada línea empieza con `[request_id] [trace=...]` y luego el mensaje.
- **JSON:** Si en `.env` pones `LOG_FORMAT=json`, cada línea es un JSON con `timestamp`, `level`, `logger`, `message`, `request_id`, `trace_id`, `span_id`. Útil para enviar a un agregador de logs (Datadog, ELK, CloudWatch, etc.) o para buscar por campos.

## Variables de entorno

| Variable     | Uso |
|-------------|-----|
| `LOG_FORMAT=json` | Activa formato JSON (una línea por evento). |
| (opcional)   | Nivel por defecto es INFO; se puede cambiar configurando el nivel del logger en código. |

## Dónde se configura

- **Filtro y formatter:** `app/logging_config.py` (TraceCorrelationFilter, JsonLogFormatter, setup_correlation_logging).
- **Activación:** En `app/main.py`, al arranque se llama a `setup_correlation_logging()` y en el middleware se usa `set_request_id` / `clear_request_id`.

## Enviar logs a Arize u otro sistema

Arize AX se centra en **trazas** (spans). Si en el futuro Arize admite ingesta de logs (OTLP Logs o API), podrías enviar las líneas JSON a ese destino. Mientras tanto, puedes:

- Redirigir stdout a un archivo y usar ese archivo en tu agregador.
- Configurar un handler en `logging_config` que envíe a un servicio (HTTP, cola, etc.) usando las mismas líneas JSON.

En todos los casos, `trace_id` y `request_id` permiten correlacionar con las trazas en Arize.
