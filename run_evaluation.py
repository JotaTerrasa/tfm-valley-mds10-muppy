#!/usr/bin/env python3
"""
Sistema de evaluación del multiagente: analiza los prompts de cada parte del grafo
y opcionalmente ejecuta casos de prueba (trazas enviadas a Arize Phoenix si está configurado).

Uso (desde la raíz, con venv activado):
  python run_evaluation.py                    # solo catálogo de prompts
  python run_evaluation.py --catalog-json     # imprime catálogo en JSON
  python run_evaluation.py --run-samples       # catálogo + invoca muestras (para trazas en Phoenix)
  python run_evaluation.py --run-samples --samples 5

Variables de entorno para Phoenix (opcional):
  PHOENIX_PROJECT_NAME  o  PHOENIX_ENABLED=true  para habilitar tracing.
  PHOENIX_COLLECTOR_ENDPOINT  si Phoenix no está en localhost:4317 (gRPC).
"""
import os
import sys
import json
import argparse

project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv()

from app.core.config_manager import load_all_agent_configs, AGENT_CONFIGS
from app.evaluation.prompt_catalog import build_prompt_catalog, catalog_to_dict


# Casos de prueba por intención (para generar trazas en distintos nodos del grafo)
SAMPLE_INPUTS = [
    "Hola, buenos días",
    "Quiero cotizar un seguro de coche",
    "Quiero contratar un seguro",
    "Tengo una duda sobre mi póliza",
    "Necesito el precio de un seguro de hogar para 100m2",
]


def run_catalog():
    load_all_agent_configs("agents")
    catalog = build_prompt_catalog(AGENT_CONFIGS)
    return catalog


def run_sample_invokes(count: int):
    """Invoca el backend con muestras para generar trazas (Phoenix las captura si está activo)."""
    try:
        import httpx
    except ImportError:
        print("--- run-samples requiere httpx. pip install httpx ---")
        return
    base_url = os.getenv("EVAL_API_URL", "http://localhost:8000")
    samples = SAMPLE_INPUTS[: min(count, len(SAMPLE_INPUTS))]
    session_id = None
    for i, text in enumerate(samples, 1):
        try:
            payload = {"input": text}
            if session_id:
                payload["session_id"] = session_id
            r = httpx.post(
                f"{base_url}/invoke",
                json=payload,
                timeout=60.0,
            )
            if r.status_code == 200:
                data = r.json()
                session_id = data.get("session_id")
                print(f"  [{i}] OK: '{text[:50]}...' -> session {session_id[:8] if session_id else '-'}...")
            else:
                print(f"  [{i}] HTTP {r.status_code}: {text[:50]}...")
        except Exception as e:
            print(f"  [{i}] Error: {e}")


def main():
    parser = argparse.ArgumentParser(description="Evaluación multiagente: catálogo de prompts y muestras.")
    parser.add_argument("--catalog-json", action="store_true", help="Imprimir catálogo en JSON")
    parser.add_argument("--run-samples", action="store_true", help="Ejecutar invocaciones de muestra (trazas a Phoenix)")
    parser.add_argument("--samples", type=int, default=3, help="Número de muestras a ejecutar (default 3)")
    args = parser.parse_args()

    print("--- Catálogo de prompts por agente y nodo del grafo ---")
    catalog = run_catalog()

    if args.catalog_json:
        out = catalog_to_dict(catalog)
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return

    for e in catalog:
        print(f"  {e.agent_key} / {e.node_name}")
        print(f"    prompt: {e.prompt_path} ({len(e.prompt_text)} chars)")
        if e.available_tools:
            print(f"    tools: {e.available_tools}")
    print(f"Total: {len(catalog)} prompts en el grafo.\n")

    if args.run_samples:
        print("--- Invocando muestras (trazas a Phoenix si PHOENIX_PROJECT_NAME está configurado) ---")
        run_sample_invokes(args.samples)
        print("--- Listo. Revisa Phoenix para ver trazas por nodo y prompt. ---")


if __name__ == "__main__":
    main()
