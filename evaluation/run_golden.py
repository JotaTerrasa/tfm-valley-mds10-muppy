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
import subprocess
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


def _load_dotenv_if_available() -> None:
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if not env_file.is_file():
        return
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(env_file)


def _build_auth_headers(
    base_url: str,
    timeout: int,
    explicit_token: str = "",
    explicit_user: str = "",
    explicit_password: str = "",
) -> dict[str, str]:
    token = (explicit_token or os.getenv("EVAL_BEARER_TOKEN") or os.getenv("GOLDEN_BEARER_TOKEN") or "").strip()
    if token:
        return {"Authorization": f"Bearer {token}"}

    username = (explicit_user or os.getenv("LOGIN_USER") or "").strip()
    password = (explicit_password or os.getenv("LOGIN_PASSWORD") or "").strip()
    if not username or not password:
        return {}

    login_url = f"{base_url.rstrip('/')}/auth/login"
    try:
        r = requests.post(
            login_url,
            data={"username": username, "password": password},
            timeout=timeout,
        )
        r.raise_for_status()
        data = r.json()
        token = (data.get("access_token") or "").strip()
        if token:
            return {"Authorization": f"Bearer {token}"}
    except Exception:
        return {}
    return {}


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


def run_one(
    base_url: str,
    case: dict,
    timeout: int,
    use_judge: bool = False,
    headers: dict[str, str] | None = None,
) -> tuple[bool, str, str]:
    """Llama a /invoke y comprueba la respuesta. Devuelve (ok, response_text, error_msg)."""
    url = f"{base_url.rstrip('/')}/invoke"
    payload = {"input": case["input"]}
    try:
        r = requests.post(url, json=payload, headers=headers or {}, timeout=timeout)
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
    parser.add_argument(
        "--auth-token",
        default=os.getenv("EVAL_BEARER_TOKEN", ""),
        help="Bearer token para /invoke (opcional).",
    )
    parser.add_argument(
        "--auth-user",
        default=os.getenv("LOGIN_USER", ""),
        help="Usuario para /auth/login (opcional).",
    )
    parser.add_argument(
        "--auth-password",
        default=os.getenv("LOGIN_PASSWORD", ""),
        help="Password para /auth/login (opcional).",
    )
    parser.add_argument(
        "--run-ai-judge",
        action="store_true",
        help="Ejecutar tambien escenarios multi-turn de AI Judge (evaluation/run_ai_judge.py).",
    )
    parser.add_argument(
        "--ai-scenarios",
        type=Path,
        default=Path(__file__).resolve().parent / "ai_judge_scenarios.json",
        help="Ruta al JSON de escenarios para run_ai_judge.py",
    )
    parser.add_argument(
        "--ai-out",
        type=Path,
        default=Path(__file__).resolve().parent / "reports" / "ai_judge_report.json",
        help="Ruta del reporte JSON de run_ai_judge.py",
    )
    args = parser.parse_args()
    _load_dotenv_if_available()

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
    auth_headers = _build_auth_headers(
        base_url=base_url,
        timeout=args.timeout,
        explicit_token=args.auth_token,
        explicit_user=args.auth_user,
        explicit_password=args.auth_password,
    )

    failed = 0
    for i, case in enumerate(cases, 1):
        cid = case.get("id", f"case_{i}")
        ok, response_text, msg = run_one(
            base_url,
            case,
            args.timeout,
            use_judge=args.judge,
            headers=auth_headers,
        )
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
    exit_code = 1 if failed else 0

    if args.run_ai_judge:
        print("\n--- Ejecutando AI Judge multi-turn ---")
        ai_runner = Path(__file__).resolve().parent / "run_ai_judge.py"
        if not ai_runner.is_file():
            print(f"No se encuentra runner AI Judge: {ai_runner}", file=sys.stderr)
            return 2

        cmd = [
            sys.executable,
            str(ai_runner),
            "--scenarios",
            str(args.ai_scenarios),
            "--base-url",
            base_url,
            "--timeout",
            str(args.timeout),
            "--out",
            str(args.ai_out),
        ]
        if args.auth_token:
            cmd.extend(["--auth-token", args.auth_token])
        if args.auth_user:
            cmd.extend(["--auth-user", args.auth_user])
        if args.auth_password:
            cmd.extend(["--auth-password", args.auth_password])
        if args.judge:
            cmd.append("--judge")
        if args.verbose:
            cmd.append("--verbose")

        proc = subprocess.run(cmd, check=False)
        if proc.returncode != 0:
            exit_code = 1
        print(f"--- AI Judge finalizado (exit={proc.returncode}) ---")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
