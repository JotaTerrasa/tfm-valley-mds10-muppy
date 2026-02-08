#!/usr/bin/env python3
"""
Script Golden Set: evalúa el backend contra casos (input → criterios de respuesta).
Uso: tener el backend arrancado (ej. .\start-backend.ps1) y ejecutar:
  python evaluation/run_golden.py
  python evaluation/run_golden.py --judge   # incluye LLM as a Judge en casos con judge_criteria
"""
import argparse
import json
import os
import sys
from pathlib import Path

# Raíz del proyecto para importar evaluation.judge
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

try:
    import requests
except ImportError:
    print("Instala requests: pip install requests", file=sys.stderr)
    sys.exit(2)


def load_golden(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_case(case: dict, response_text: str, use_judge: bool = False) -> tuple[bool, str]:
    """
    Comprueba la respuesta según los criterios del caso.
    Devuelve (ok, mensaje).
    Criterios: expected_keywords, expected_substring, expected_exact; si use_judge y hay judge_criteria, también LLM as a Judge.
    """
    text = (response_text or "").strip()
    case_id = case.get("id", "?")

    if "expected_exact" in case:
        exp = case["expected_exact"].strip()
        ok = text == exp
        return ok, f"Exact: expected '{exp[:50]}...' got '{text[:50]}...'" if not ok else "OK"

    if "expected_substring" in case:
        sub = case["expected_substring"].strip()
        ok = sub.lower() in text.lower()
        return ok, f"Substring '{sub}' not found in response" if not ok else "OK"

    if "expected_keywords" in case:
        keywords = [k.strip() for k in case["expected_keywords"] if k.strip()]
        missing = [k for k in keywords if k.lower() not in text.lower()]
        ok = len(missing) == 0
        if not ok:
            return False, f"Missing keywords: {missing}"
        # Si además hay judge, lo evaluamos después (en run_one)
        if use_judge and case.get("judge_criteria"):
            from evaluation.judge import evaluate_case as judge_evaluate
            judge_ok, judge_results = judge_evaluate(case, response_text)
            if not judge_ok:
                failed = [r for r in judge_results if not r["passed"]]
                msg = ", ".join(f"{r['name']}={r['score']}" for r in failed)
                return False, f"Judge: {msg}"
            return True, "OK (keywords + judge)"
        return True, "OK"

    if use_judge and case.get("judge_criteria"):
        from evaluation.judge import evaluate_case as judge_evaluate
        judge_ok, judge_results = judge_evaluate(case, response_text)
        if not judge_ok:
            failed = [r for r in judge_results if not r["passed"]]
            msg = "; ".join(f"{r['name']} score {r['score']}" for r in failed)
            return False, f"Judge: {msg}"
        return True, "OK (judge)"

    return False, "No expected_keywords, expected_substring, expected_exact or judge_criteria in case"


def run_one(base_url: str, case: dict, timeout: int, use_judge: bool = False) -> tuple[bool, str, str]:
    """Llama a /invoke y comprueba la respuesta. Devuelve (ok, response_text, error_msg)."""
    url = f"{base_url.rstrip('/')}/invoke"
    payload = {"input": case["input"]}
    try:
        r = requests.post(url, json=payload, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        response_text = data.get("response") or data.get("raw_agent_response") or ""
    except requests.RequestException as e:
        return False, "", str(e)

    ok, msg = check_case(case, response_text, use_judge=use_judge)
    return ok, response_text, msg


def main() -> int:
    parser = argparse.ArgumentParser(description="Ejecuta el Golden Set contra el backend.")
    parser.add_argument(
        "--golden",
        type=Path,
        default=Path(__file__).resolve().parent / "golden_set.json",
        help="Ruta al JSON del golden set",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("GOLDEN_BASE_URL", "http://localhost:8000"),
        help="URL base del backend (default: GOLDEN_BASE_URL o http://localhost:8000)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Timeout por petición en segundos (default: 60)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Mostrar respuesta completa en cada caso",
    )
    parser.add_argument(
        "--judge",
        action="store_true",
        help="Evaluar con LLM as a Judge los casos que tengan judge_criteria (requiere GOOGLE_API_KEY)",
    )
    args = parser.parse_args()

    if not args.golden.is_file():
        print(f"Golden set no encontrado: {args.golden}", file=sys.stderr)
        return 2

    data = load_golden(args.golden)
    base_url = data.get("base_url") or args.base_url
    cases = data.get("cases") or []
    if not cases:
        print("No hay casos en el golden set.", file=sys.stderr)
        return 0

    print(f"Golden Set: {args.golden}")
    print(f"Backend:   {base_url}")
    print(f"Judge:     {'sí' if args.judge else 'no'}")
    print(f"Casos:     {len(cases)}\n")

    failed = 0
    for i, case in enumerate(cases, 1):
        cid = case.get("id", f"case_{i}")
        ok, response_text, msg = run_one(base_url, case, args.timeout, use_judge=args.judge)
        status = "PASS" if ok else "FAIL"
        if not ok:
            failed += 1
        print(f"  [{status}] {cid}: {msg}")
        if args.verbose or not ok:
            snippet = (response_text or "(vacío)")[:200]
            if len(response_text or "") > 200:
                snippet += "..."
            print(f"           Response: {snippet}")

    print(f"\nTotal: {len(cases)} | Pass: {len(cases) - failed} | Fail: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
