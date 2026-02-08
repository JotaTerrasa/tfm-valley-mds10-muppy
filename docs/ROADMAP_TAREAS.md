# Roadmap de tareas – Mapfre Backend

Seguimiento de las tareas pendientes con prioridad, dependencias y pasos concretos.

---

## 1. Configurar exportación de logs (Arize)

**Objetivo:** Conectar el sistema para ver qué pasa dentro (logs en Arize).

**Estado:** [x] Hecho (logs con correlación; listos para agregador o Arize si soporta logs)

**Contexto:** Ya tienes **trazas** (OpenTelemetry) en Arize AX → Tracing Projects. Los **logs** de aplicación incluyen request_id, trace_id y span_id para correlacionar con las trazas.

**Opciones:**
- **A)** Enviar logs a Arize si el producto soporta ingesta de logs (revisar docs Arize AX / Observe).
- **B)** Centralizar logs en un sistema externo y correlacionar con `trace_id` (implementado: ver abajo).

**Implementado:** Módulo `app/logging_config.py` (TraceCorrelationFilter, JsonLogFormatter con `LOG_FORMAT=json`), set_request_id/clear_request_id en middleware, setup_correlation_logging() al arranque. Ver `docs/LOGGING.md`. Los logs ya incluyen request_id/trace_id/span_id; para JSON pon en .env `LOG_FORMAT=json`.

---

## 2. Trazabilidad (Ingeniería de SW) – Rastreo de peticiones

**Objetivo:** Implementar el rastreo de peticiones (request → respuesta, correlación entre servicios/agentes).

**Estado:** [x] Hecho (Request ID en middleware + OpenTelemetry + logs)  

**Contexto:** OpenTelemetry + Arize ya dan **trazas por invocación** (LLM, chains). La “trazabilidad” de ingeniería suele ser: ID de petición único, propagación por capas y registro en logs/trazas.

**Implementado:**
1. **Request ID:** Middleware `RequestIDMiddleware` en `app/main.py`: genera (o acepta si el cliente envía) `X-Request-ID` y lo guarda en `request.state.request_id`.
2. **Propagación:** Se inyecta en el span actual de OpenTelemetry como atributo `request_id` (visible en Arize en cada trace).
3. **Respuesta:** Todas las respuestas incluyen el header `X-Request-ID`.
4. **Logs:** Los logs de `/invoke` incluyen `[request_id]` para correlacionar con trazas.

**Uso:** El cliente puede enviar `X-Request-ID` en la petición (opcional); si no lo envía, el servidor genera uno. La respuesta siempre trae `X-Request-ID` en los headers. En Arize AX, al abrir un trace verás el atributo `request_id` en el span para localizar la petición.

---

## 3. Script "Golden Set" – Evaluación automática de respuestas

**Objetivo:** Automatizar la evaluación de respuestas correctas tras cambios (regresión en comportamiento del asistente).

**Estado:** [x] Hecho

**Implementado:** Carpeta `evaluation/`: `golden_set.json` (casos con expected_keywords, expected_substring o expected_exact), `run_golden.py` (llama a `/invoke` por caso y comprueba criterios), `README.md` con uso y formato. Ejecutar con el backend en marcha: `python evaluation/run_golden.py`. Código de salida 1 si algún caso falla (para CI).

---

## 4. Selección de Métricas Core

**Objetivo:** Definir las 5–6 métricas clave del sistema (calidad, rendimiento, negocio).

**Estado:** [x] Hecho  

**Implementado:** Documento `docs/METRICAS_CORE.md` con 6 métricas: Latencia P50, P95, Tasa de error, Coste por petición, Tokens por petición, Throughput (RPS). Para cada una: definición, dónde se obtiene (Arize, API, load test, logs) y objetivo típico a validar con negocio.

---

## 5. Generación de Escenarios (Stress Test) – 500 usuarios

**Objetivo:** Simular 500 usuarios para pruebas de carga.

**Estado:** [x] Hecho

**Implementado:** Carpeta `load_tests/`: `locustfile.py` (usuarios que hacen GET /health y POST /invoke con mensajes cortos de triage), `README.md` con uso. Locust está en `requirements.txt`. Ejecución: `locust -f load_tests/locustfile.py --host=http://localhost:8000` (UI en :8089) o `.\scripts\run\run-stress.ps1` (headless: 500 usuarios, rampa 50/s, 5 min). Los resultados dan P50, P95, tasa de error y RPS (métricas core 1, 2, 3, 6).

---

## 6. Formación sobre trazas

**Objetivo:** Entender cómo leer los logs/trazas (Arize AX, OpenTelemetry).

**Estado:** [ ] Pendiente  

**Contenido sugerido:**
- Qué es un **trace** y un **span** (una petición = un trace; cada LLM/chain = span).
- Cómo abrir una traza en Arize AX (Tracing Projects → proyecto → trace).
- Cómo interpretar: latencia por span, tokens, coste, errores.
- Cómo correlacionar con **request_id** o con logs si se implementa el punto 1–2.
- Documento interno corto o sesión de 1h con el equipo.

---

## 7. Evaluación: LLM as a Judge

**Objetivo:** Configurar un LLM para que evalúe respuestas de otros (calidad, adecuación, seguridad).

**Estado:** [x] Hecho  

**Pasos sugeridos:**
1. Definir **criterios de evaluación** (ej. “¿Responde a la pregunta?”, “¿Es cortés?”, “¿Evita datos sensibles?”).
2. Elegir **modelo juez** (ej. Gemini Flash o Pro) y **prompt** tipo: “Dado input X y respuesta Y, puntúa 1–5 en criterio Z”.
3. Implementar módulo de evaluación (Python): input + respuesta del agente → llamada al LLM juez → score o etiquetas.
4. Integrar con el **Golden Set** (punto 3): el script puede usar el juez en lugar de (o además de) comparación por texto/keywords.
5. Opcional: enviar scores a Arize (Span Evaluations) si el formato es compatible.

---

## Orden sugerido (dependencias)

| Orden | Tarea                    | Motivo |
|-------|--------------------------|--------|
| 1     | **Trazabilidad** (2)     | Request ID + propagación ayuda en todo lo demás (logs, stress, evaluación). |
| 2     | **Logs (Arize)** (1)     | Ver qué pasa dentro; complementa trazas. |
| 3     | **Métricas Core** (4)   | Definir qué medir antes de automatizar. |
| 4     | **Golden Set** (3)       | Base para regresión y para el juez. |
| 5     | **LLM as a Judge** (7)   | Evaluación automática de calidad. |
| 6     | **Stress Test** (5)     | Cuando el sistema sea estable y medible. |
| 7     | **Formación trazas** (6)| En paralelo o cuando ya haya trazas y logs claros. |

---

## Dónde guardar artefactos

- **Trazabilidad / Request ID:** `app/main.py` (middleware), `app/` donde se propague contexto.
- **Golden Set:** `evaluation/golden_set.json` + `evaluation/run_golden.py` (o `tests/golden/`).
- **LLM Judge:** `evaluation/judge.py` (o `app/evaluation/`).
- **Stress test:** `load_tests/` con script Locust/k6/Artillery.
- **Docs formación:** `docs/TRAZAS_ARIZE.md` o similar.

Si quieres, el siguiente paso puede ser implementar **Trazabilidad (Request ID)** en el backend y, en paralelo, el esqueleto del **Golden Set** y del **LLM as a Judge**.
