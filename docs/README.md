# Documentación del proyecto

Índice de la documentación en `docs/`.

| Documento | Contenido |
|-----------|-----------|
| [**ARIZE_TRACING.md**](ARIZE_TRACING.md) | Conectar el backend a Arize AX (Tracing Projects): variables `.env`, endpoint EU, Phoenix opcional. |
| [**ARIZE_DASHBOARDS.md**](ARIZE_DASHBOARDS.md) | Qué dashboards de Arize AX añadir para observabilidad (Token Tracking, Monitor Summary, Blank Template). |
| [**LOGGING.md**](LOGGING.md) | Logs con correlación (request_id, trace_id, span_id), formato JSON, variables de entorno. |
| [**METRICAS_CORE.md**](METRICAS_CORE.md) | Las 6 métricas clave (latencia P50/P95, tasa de error, coste, tokens, throughput) y dónde obtenerlas. |
| [**ROADMAP_TAREAS.md**](ROADMAP_TAREAS.md) | Seguimiento de tareas: trazabilidad, logs, golden set, métricas, stress test, LLM as a Judge, formación. |
| [**SETUP_MI_REPO.md**](SETUP_MI_REPO.md) | Cómo traer el repo a tu GitHub privado y sincronizar con el repo base (Sergio). |
| [**COMANDOS_RAPIDOS.md**](COMANDOS_RAPIDOS.md) | Dónde están los scripts para levantar backend y stress test (para Cursor y humanos). |

---

- **Observabilidad:** Arize (trazas) → [ARIZE_TRACING.md](ARIZE_TRACING.md) + [ARIZE_DASHBOARDS.md](ARIZE_DASHBOARDS.md). Logs → [LOGGING.md](LOGGING.md). Métricas → [METRICAS_CORE.md](METRICAS_CORE.md).
- **Evaluación:** Golden Set y LLM as a Judge → ver carpeta [../evaluation/](../evaluation/) y su [README](../evaluation/README.md).
- **Pruebas de carga:** Stress test con Locust → ver carpeta [../load_tests/](../load_tests/) y su [README](../load_tests/README.md).
- **Scripts de utilidad:** Repo (git) y datos (PDF→MD) → [../scripts/](../scripts/README.md). Estructura: `scripts/git/`, `scripts/data/`.
