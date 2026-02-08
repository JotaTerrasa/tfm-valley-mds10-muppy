"""
LLM as a Judge: evalúa respuestas del agente con un modelo (p. ej. Gemini).
Uso standalone o desde run_golden.py con --judge y judge_criteria en cada caso.
"""
import json
import os
import re
from pathlib import Path
from typing import Any

# Cargar .env desde la raíz del proyecto (evaluation/ está dentro del proyecto)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"


def _load_env():
    if not _ENV_FILE.is_file():
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(_ENV_FILE)
    except ImportError:
        with open(_ENV_FILE, "r", encoding="utf-8-sig", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    k, v = k.strip(), v.strip().strip("'\"")
                    if k:
                        os.environ.setdefault(k, v)


# Criterio: {"name": str, "min_score": int opcional, "description": str opcional}
# Resultado por criterio: {"name": str, "score": int, "reason": str, "passed": bool}
def evaluate(
    user_input: str,
    agent_response: str,
    criteria: list[dict[str, Any]],
    *,
    model: str = "gemini-2.0-flash",
    temperature: float = 0.1,
) -> list[dict[str, Any]]:
    """
    Evalúa la respuesta del agente con un LLM juez.
    criteria: lista de {"name": "...", "min_score": 1-5 opcional, "description": "..." opcional}
    Devuelve lista de {"name", "score", "reason", "passed"} (passed si score >= min_score cuando min_score existe).
    """
    _load_env()
    api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if not api_key:
        return [
            {
                "name": c.get("name", "?"),
                "score": 0,
                "reason": "GOOGLE_API_KEY no configurada",
                "passed": False,
            }
            for c in criteria
        ]

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError:
        return [
            {
                "name": c.get("name", "?"),
                "score": 0,
                "reason": "langchain_google_genai no instalado",
                "passed": False,
            }
            for c in criteria
        ]

    criteria_text = "\n".join(
        f"- {c.get('name', '?')}: {c.get('description', 'Puntúa 1-5 la calidad.')}"
        for c in criteria
    )
    prompt = f"""Eres un evaluador de respuestas de un asistente de Mapfre (seguros).

**Input del usuario:** {user_input!r}

**Respuesta del asistente:** {agent_response!r}

**Criterios:** Puntúa cada uno del 1 al 5 (1=muy mal, 5=muy bien).
{criteria_text}

Responde ÚNICAMENTE con un JSON válido, sin markdown ni texto extra, con esta forma:
{{"criterios": [{{"nombre": "nombre_criterio", "puntuacion": 4, "comentario": "breve razón"}}, ...]}}
Usa exactamente los nombres de criterio indicados arriba."""

    llm = ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        temperature=temperature,
    )
    try:
        msg = llm.invoke(prompt)
        text = (msg.content or "").strip()
    except Exception as e:
        return [
            {"name": c.get("name", "?"), "score": 0, "reason": str(e), "passed": False}
            for c in criteria
        ]

    # Extraer JSON (puede venir envuelto en ```json ... ```)
    json_str = text
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if m:
        json_str = m.group(1).strip()
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        json_str = m.group(0)
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        return [
            {
                "name": c.get("name", "?"),
                "score": 0,
                "reason": f"JSON inválido del juez: {text[:150]}...",
                "passed": False,
            }
            for c in criteria
        ]

    by_name = {}
    for item in data.get("criterios", data.get("criteria", [])):
        nom = item.get("nombre", item.get("name", ""))
        punt = item.get("puntuacion", item.get("score", 0))
        if isinstance(punt, (int, float)):
            punt = max(1, min(5, int(punt)))
        else:
            punt = 3
        by_name[nom] = {"score": punt, "reason": item.get("comentario", item.get("comment", ""))}

    results = []
    for c in criteria:
        name = c.get("name", "?")
        min_score = c.get("min_score")
        info = by_name.get(name, {})
        score = info.get("score", 0)
        reason = info.get("reason", "")
        passed = score >= min_score if min_score is not None else True
        results.append({"name": name, "score": score, "reason": reason, "passed": passed})
    return results


def evaluate_case(case: dict, response_text: str) -> tuple[bool, list[dict[str, Any]]]:
    """
    Evalúa un caso del golden set con judge_criteria.
    case debe tener "judge_criteria": [{"name": "...", "min_score": N, "description": "..." opcional}].
    Devuelve (todas_pasaron, lista de resultados por criterio).
    """
    criteria = case.get("judge_criteria") or []
    if not criteria:
        return True, []
    results = evaluate(case.get("input", ""), response_text or "", criteria)
    all_passed = all(r["passed"] for r in results)
    return all_passed, results
