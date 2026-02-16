# AI-as-a-Judge (Evals)

Runner para ejecutar escenarios multi-turn contra `POST /invoke` y validar:

- Reglas deterministas (`must_contain`, `must_contain_any`, `must_not_contain`)
- Criterios con juez LLM (`judge_criteria`) opcional

## Ejecutar

Desde la raiz del proyecto, con backend levantado:

```bash
python evaluation/run_ai_judge.py
```

Con juez LLM (requiere `GOOGLE_API_KEY`):

```bash
python evaluation/run_ai_judge.py --judge
```

Desde `run_golden.py` en un solo comando (golden + AI Judge):

```bash
python evaluation/run_golden.py --judge --run-ai-judge
```

Si `/invoke` requiere autenticación, puedes pasar token:

```bash
python evaluation/run_golden.py --judge --run-ai-judge --auth-token "<tu_jwt>"
```

O credenciales para login automático contra `/auth/login`:

```bash
python evaluation/run_golden.py --judge --run-ai-judge --auth-user "<usuario>" --auth-password "<password>"
```

Verbose y salida custom:

```bash
python evaluation/run_ai_judge.py --judge -v --out evaluation/reports/ai_judge_report_demo.json
```

## Archivos

- `evaluation/ai_judge_scenarios.json`: dataset de escenarios.
- `evaluation/run_ai_judge.py`: runner principal.
- `evaluation/reports/ai_judge_report.json`: reporte generado (JSON).

## Esquema de escenario (resumen)

Cada escenario define `turns` secuenciales en la misma `session_id`.

Campos por turno:

- `user`: texto enviado a `/invoke`.
- `must_contain`: todas las frases deben aparecer.
- `must_contain_any`: al menos una frase debe aparecer.
- `must_not_contain`: ninguna frase debe aparecer.
- `judge_criteria`: lista de criterios para LLM Judge.

