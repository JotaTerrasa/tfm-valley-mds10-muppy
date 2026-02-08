# Métricas core – 5-6 métricas clave

Definición de las métricas clave del sistema, dónde se obtienen y cómo interpretarlas. Validar con negocio antes de fijar umbrales (SLAs).

---

## 1. Latencia P50 de `/invoke` (rendimiento)

**Qué mide:** Tiempo que tarda en responder la mitad de las peticiones a `/invoke` (mediana).

**Dónde se obtiene:**
- **Arize AX** → Observe → Tracing Projects → proyecto `mapfre-muppy`: métricas agregadas (Latency P50 en la vista del proyecto).
- **Stress test / load test:** Locust o k6 reportan percentiles (P50, P95, P99).
- **Logs:** Si se registra tiempo por petición, se puede calcular offline.

**Objetivo típico:** &lt; 3–5 s (depende del flujo y del modelo). Definir umbral con negocio.

---

## 2. Latencia P95 de `/invoke` (rendimiento)

**Qué mide:** Tiempo por debajo del cual está el 95 % de las respuestas. Detecta colas y picos.

**Dónde se obtiene:**
- **Arize AX:** mismo proyecto, métrica Latency P99 (Arize suele mostrar P50/P99).
- **Load test:** percentil 95 en el informe de Locust/k6.

**Objetivo típico:** &lt; 8–10 s o &lt; 2× P50. Definir con negocio.

---

## 3. Tasa de error (fiabilidad)

**Qué mide:** Porcentaje de peticiones a `/invoke` que devuelven 5xx o timeout.

**Dónde se obtiene:**
- **Load test:** Locust/k6 muestran % de fallos y códigos HTTP.
- **Logs:** Contar `logger.error` o respuestas 5xx por ventana de tiempo (si se registran en logs o en un agregador).
- **Arize:** Trazas fallidas (spans con error).

**Objetivo típico:** &lt; 0,1–1 % (según SLA).

---

## 4. Coste por petición (uso / negocio)

**Qué mide:** Coste en USD (u otra moneda) por llamada a `/invoke`, basado en tokens consumidos (modelo Gemini).

**Dónde se obtiene:**
- **API:** El campo `request_cost` en la respuesta de `/invoke` (ya implementado).
- **Arize AX:** Total Cost en la vista del proyecto; por trace se ve el coste del span LLM.
- **Agregado:** Sumar `request_cost` en logs o en un proceso que consuma las respuestas.

**Objetivo típico:** Vigilar tendencia y picos; definir techo por sesión o por usuario con negocio.

---

## 5. Tokens por petición (uso / eficiencia)

**Qué mide:** Número de tokens (input + output) consumidos por cada `/invoke`. Indicador de uso de modelo y de longitud de contexto/respuesta.

**Dónde se obtiene:**
- **Arize AX:** Total Tokens en el proyecto; por trace/spans LLM se ven input/output tokens.
- **Backend:** El orquestador calcula `token_usage` (input_tokens, output_tokens); no se expone hoy en la respuesta JSON al cliente, pero se usa para `request_cost`. Si se necesita en API, se puede añadir un campo opcional.

**Objetivo típico:** Monitorear tendencia; detectar prompts o respuestas anormalmente largas.

---

## 6. Throughput (peticiones/segundo) (rendimiento)

**Qué mide:** Número de peticiones a `/invoke` (o al API) que el sistema atiende por segundo bajo carga.

**Dónde se obtiene:**
- **Load test:** Locust/k6 reportan “Requests/s” o RPS durante la prueba.
- **Arize / APM:** Si se exportan métricas de request count por intervalo (por ejemplo vía OTLP métricas en el futuro).

**Objetivo típico:** Definir con negocio según usuarios concurrentes esperados (ej. 500 usuarios con N peticiones por minuto → RPS mínimo objetivo).

---

## Resumen

| # | Métrica              | Tipo        | Origen principal        |
|---|----------------------|------------|--------------------------|
| 1 | Latencia P50         | Rendimiento| Arize, load test        |
| 2 | Latencia P95         | Rendimiento| Arize, load test        |
| 3 | Tasa de error        | Fiabilidad | Load test, logs         |
| 4 | Coste por petición   | Uso/Negocio| API `request_cost`, Arize|
| 5 | Tokens por petición  | Uso        | Arize (y backend internamente) |
| 6 | Throughput (RPS)     | Rendimiento| Load test               |

---

## Próximos pasos (opcional)

- **LLM as a Judge:** Añadir una métrica de “calidad” (score medio por petición o por golden set) cuando esté implementado.
- **Dashboard:** Centralizar P50, P95, errores, coste y RPS en un dashboard (Grafana, Arize, o similar) alimentado por load test + Arize + logs.
