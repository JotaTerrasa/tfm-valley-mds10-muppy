# Dashboards de Arize AX para observabilidad

Recomendación de plantillas de dashboard según el valor que aportan a tu backend (agentes LLM, trazas en Tracing Projects, métricas de latencia/tokens/coste/errores).

---

## Prioridad alta (añadir primero)

### 1. **Token Tracking and Latency** (Model Overview)

- **Qué aporta:** Tokens y latencia de las peticiones LLM a lo largo del tiempo. Encaja con tus **métricas core** (Latencia P50/P95, Tokens por petición).
- **Por qué:** Ya envías trazas a Arize; este dashboard muestra tendencias, picos y patrones de uso del modelo (Gemini). Sirve para detectar subidas de coste, lentitud o picos de tráfico.
- **Acción:** Pulsa el **+** en "Token Tracking and Latency" para crear el dashboard.

### 2. **Monitor Summary** (Model Overview)

- **Qué aporta:** Vista global de todos los **monitors** que tengas (alertas/reglas de salud del modelo).
- **Por qué:** Cuando definas monitors (ej. latencia > X segundos, tasa de error > Y %), aquí verás el estado de todos en un solo sitio.
- **Acción:** Añade "Monitor Summary". Después puedes crear monitors en **Monitors** y ver su resumen aquí.

### 3. **Blank Template** (Custom Template)

- **Qué aporta:** Dashboard a medida con las métricas que tú elijas (latencia, RPS, coste, errores, por agente si Arize lo permite por atributos).
- **Por qué:** Puedes alinear el dashboard con tu doc **Métricas core** (P50, P95, errores, coste, throughput) y con request_id/trace_id si lo expones en trazas.
- **Acción:** Crea un "Blank Template" y añade widgets según los datos que Arize exponga para tu proyecto de Tracing (métricas derivadas de trazas).

---

## Prioridad media (útil más adelante)

### 4. **Compare Model A with Model B**

- **Qué aporta:** Comparar dos variantes (A/B) en un mismo dashboard (p. ej. dos modelos o dos versiones de prompt).
- **Cuándo:** Cuando quieras probar un nuevo modelo o un cambio de prompt y comparar latencia, tokens o calidad frente al actual.

### 5. **Compare Production vs Training**

- **Qué aporta:** Comparar comportamiento en “entrenamiento” (o preproducción) frente a producción.
- **Cuándo:** Si más adelante tienes entornos distintos o datos de evaluación (golden set / LLM as a Judge) que quieras contrastar con producción.

---

## Prioridad baja (menos alineados con tu caso ahora)

- **Regression / Classification / Ranking / MultiClass**: Orientados a modelos clásicos (métricas de accuracy, precisión, etc.). No son los principales para observabilidad de un asistente LLM conversacional.
- **Explore your model's training/validation data**: Útil cuando tengas datasets de entrenamiento/validación en Arize; no es lo primero para observabilidad en tiempo real.
- **Feature Analysis / Feature Drift**: Pensados para modelos con muchas features (tabla de datos). Tu flujo es sobre todo texto y trazas LLM; pueden esperar.

---

## Resumen rápido

| Dashboard                    | Aporta para observabilidad                    | Añadir |
|-----------------------------|-----------------------------------------------|--------|
| Token Tracking and Latency  | Tokens y latencia en el tiempo (LLM)          | Sí     |
| Monitor Summary             | Resumen de todos los monitors                 | Sí     |
| Blank Template              | Dashboard a medida (tus métricas core)        | Sí     |
| Compare Model A with Model B| A/B de modelos o prompts                      | Más adelante |
| Compare Prod vs Training    | Prod vs preprod/entrenamiento                 | Más adelante |
| Resto (Regression, Feature…) | Más específicos de ML tradicional / features | No prioritario |

---

## Siguiente paso

1. En **Arize AX → Dashboards**, añade con **+** estos tres: **Token Tracking and Latency**, **Monitor Summary** y **Blank Template**.
2. En **Monitors**, define al menos un monitor (ej. latencia P95 > 10 s o tasa de error > 1 %) para sacar partido al Monitor Summary.
3. En el **Blank Template**, configura widgets con las métricas que Arize te ofrezca para tu proyecto de Tracing (latencia, tokens, coste, número de requests, etc.) para tener una vista alineada con `docs/METRICAS_CORE.md`.
