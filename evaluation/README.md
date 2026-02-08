# Golden Set – Evaluación automática de respuestas

Script para detectar **regresiones** en el asistente: se envían inputs fijos al backend y se comprueba que la respuesta cumple unos criterios (keywords, substring o texto exacto).

## Requisitos

- Backend en marcha (por ejemplo `.\scripts\run\start-backend.ps1`).
- Python con `requests` (ya está en `requirements.txt` del proyecto).

## Uso

Desde la **raíz del proyecto**:

```bash
python evaluation/run_golden.py
```

Opciones:

- `--golden evaluation/golden_set.json` – ruta al JSON del golden set (por defecto: el que está junto al script).
- `--base-url http://localhost:8000` – URL del backend (por defecto: `GOLDEN_BASE_URL` o `http://localhost:8000`).
- `--timeout 60` – timeout por petición en segundos.
- `-v` / `--verbose` – mostrar la respuesta completa en cada caso.

Ejemplo con otra URL:

```bash
GOLDEN_BASE_URL=http://localhost:8000 python evaluation/run_golden.py
```

El script devuelve **código de salida 0** si todos los casos pasan y **1** si alguno falla (útil para CI).

## Formato del golden set (`golden_set.json`)

```json
{
  "description": "Opcional",
  "base_url": "http://localhost:8000",
  "cases": [
    {
      "id": "identificador_caso",
      "input": "Texto que envía el usuario",
      "expected_keywords": ["palabra1", "palabra2"],
      "description": "Opcional: qué se espera"
    }
  ]
}
```

Por cada caso se usa **solo uno** de estos criterios:

| Criterio | Comportamiento |
|----------|----------------|
| `expected_keywords` | La respuesta debe contener **todas** las palabras (insensible a mayúsculas). |
| `expected_substring` | La respuesta debe contener esta cadena (insensible a mayúsculas). |
| `expected_exact` | La respuesta debe coincidir exactamente con este texto. |

Cada caso llama a `/invoke` **sin** `session_id`, es decir, cada uno es una conversación nueva (triage desde el inicio).

## Añadir casos

1. Edita `evaluation/golden_set.json`.
2. Añade un objeto en `cases` con `id`, `input` y uno de: `expected_keywords`, `expected_substring` o `expected_exact`.
3. Vuelve a ejecutar `python evaluation/run_golden.py`.

## Integración con CI

Ejemplo (GitHub Actions u otro):

```yaml
- name: Start backend
  run: .\scripts\run\start-backend.ps1 &
- name: Wait for backend
  run: timeout 10 bash -c 'until curl -s http://localhost:8000/health; do sleep 1; done'
- name: Run Golden Set
  run: python evaluation/run_golden.py
```

(En Windows usar el equivalente para arrancar el backend en segundo plano y esperar al health.)

## LLM as a Judge

Para evaluar “calidad” o criterios más abiertos (cortesía, no revelar datos sensibles, etc.) añade en un caso el campo `judge_criteria` (name, min_score 1-5, description opcional) y ejecuta `python evaluation/run_golden.py --judge`. Requiere GOOGLE_API_KEY. Ver `evaluation/judge.py` para uso standalone.

## Catálogo de prompts y muestras (run_evaluation.py)

Script para listar todos los prompts por agente y nodo del grafo, y opcionalmente invocar muestras (trazas a Phoenix/Arize):

- `python evaluation/run_evaluation.py` — solo catálogo por consola
- `python evaluation/run_evaluation.py --catalog-json` — catálogo en JSON
- `python evaluation/run_evaluation.py --run-samples --samples 5` — con backend en marcha, invoca casos de prueba (para ver trazas)

Variables opcionales: `EVAL_API_URL` (URL del backend), `PHOENIX_PROJECT_NAME` / `PHOENIX_ENABLED` para tracing.
