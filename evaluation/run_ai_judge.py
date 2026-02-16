#!/usr/bin/env python3
"""
Runner de AI-as-a-Judge para escenarios multi-turn del asistente.

Uso:
  python evaluation/run_ai_judge.py
  python evaluation/run_ai_judge.py --judge
  python evaluation/run_ai_judge.py --scenarios evaluation/ai_judge_scenarios.json --judge --verbose

Notas:
- Requiere backend levantado (por defecto http://localhost:8000).
- Con --judge usa evaluation.judge (LLM judge con GOOGLE_API_KEY).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, List

try:
    import requests
except ImportError:
    print("Instala requests: pip install requests", file=sys.stderr)
    sys.exit(2)

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


@dataclass
class TurnResult:
    turn_index: int
    user: str
    response: str
    passed: bool
    checks: List[str]
    judge_results: List[dict[str, Any]]


@dataclass
class ScenarioResult:
    id: str
    description: str
    passed: bool
    turns: List[TurnResult]


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _load_dotenv_if_available() -> None:
    env_file = _ROOT / ".env"
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
    explicit_token: str | None = None,
    explicit_user: str | None = None,
    explicit_password: str | None = None,
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


def _contains_any(text: str, needles: list[str]) -> bool:
    lower = (text or "").lower()
    return any(n.lower() in lower for n in needles)


def _missing_any(text: str, needles: list[str]) -> list[str]:
    lower = (text or "").lower()
    return [n for n in needles if n.lower() not in lower]


def _present_any(text: str, needles: list[str]) -> list[str]:
    lower = (text or "").lower()
    return [n for n in needles if n.lower() in lower]


def _invoke(
    base_url: str,
    user_text: str,
    session_id: str,
    timeout: int,
    headers: dict[str, str] | None = None,
) -> tuple[str, dict[str, Any]]:
    url = f"{base_url.rstrip('/')}/invoke"
    payload = {"input": user_text, "session_id": session_id}
    r = requests.post(url, json=payload, headers=headers or {}, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    response_text = (data.get("response") or data.get("raw_agent_response") or "").strip()
    return response_text, data


def _evaluate_turn(
    turn: dict[str, Any],
    response_text: str,
    use_judge: bool,
) -> tuple[bool, list[str], list[dict[str, Any]]]:
    checks: list[str] = []
    passed = True

    must_contain = turn.get("must_contain") or []
    if must_contain:
        missing = _missing_any(response_text, must_contain)
        if missing:
            passed = False
            checks.append(f"missing must_contain: {missing}")

    must_contain_any = turn.get("must_contain_any") or []
    if must_contain_any and not _contains_any(response_text, must_contain_any):
        passed = False
        checks.append(f"none matched must_contain_any: {must_contain_any}")

    must_not_contain = turn.get("must_not_contain") or []
    present = _present_any(response_text, must_not_contain)
    if present:
        passed = False
        checks.append(f"found forbidden phrases: {present}")

    judge_results: list[dict[str, Any]] = []
    if use_judge and turn.get("judge_criteria"):
        from evaluation.judge import evaluate

        judge_results = evaluate(
            user_input=turn.get("user", ""),
            agent_response=response_text,
            criteria=turn.get("judge_criteria", []),
        )
        failed = [j for j in judge_results if not j.get("passed")]
        if failed:
            passed = False
            checks.append(
                "judge failed: "
                + ", ".join(f"{j.get('name')}={j.get('score')}" for j in failed)
            )

    if not checks:
        checks.append("ok")
    return passed, checks, judge_results


def run_scenario(
    base_url: str,
    scenario: dict[str, Any],
    timeout: int,
    use_judge: bool,
    verbose: bool,
    auth_headers: dict[str, str] | None = None,
) -> ScenarioResult:
    scenario_id = scenario.get("id", f"scenario-{uuid.uuid4().hex[:8]}")
    session_id = scenario.get("session_id") or f"eval-{scenario_id}-{uuid.uuid4().hex[:8]}"
    turns = scenario.get("turns") or []

    turn_results: list[TurnResult] = []
    scenario_passed = True

    for idx, turn in enumerate(turns, start=1):
        user = (turn.get("user") or "").strip()
        if not user:
            turn_results.append(
                TurnResult(
                    turn_index=idx,
                    user="",
                    response="",
                    passed=False,
                    checks=["turn without user text"],
                    judge_results=[],
                )
            )
            scenario_passed = False
            continue

        try:
            response_text, _ = _invoke(
                base_url,
                user,
                session_id=session_id,
                timeout=timeout,
                headers=auth_headers,
            )
        except Exception as e:
            turn_results.append(
                TurnResult(
                    turn_index=idx,
                    user=user,
                    response="",
                    passed=False,
                    checks=[f"http error: {e}"],
                    judge_results=[],
                )
            )
            scenario_passed = False
            continue

        turn_passed, checks, judge_results = _evaluate_turn(
            turn=turn,
            response_text=response_text,
            use_judge=use_judge,
        )
        if not turn_passed:
            scenario_passed = False

        turn_results.append(
            TurnResult(
                turn_index=idx,
                user=user,
                response=response_text,
                passed=turn_passed,
                checks=checks,
                judge_results=judge_results,
            )
        )

        if verbose:
            print(f"    [turn {idx}] user: {user}")
            print(f"    [turn {idx}] resp: {response_text[:220]}{'...' if len(response_text) > 220 else ''}")

    return ScenarioResult(
        id=scenario_id,
        description=scenario.get("description", ""),
        passed=scenario_passed,
        turns=turn_results,
    )


def _serialize(results: list[ScenarioResult]) -> dict[str, Any]:
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_scenarios": total,
        "passed_scenarios": passed,
        "failed_scenarios": total - passed,
        "pass_rate": round((passed / total) * 100.0, 2) if total else 0.0,
        "results": [
            {
                "id": r.id,
                "description": r.description,
                "passed": r.passed,
                "turns": [asdict(t) for t in r.turns],
            }
            for r in results
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="AI-as-a-Judge runner (multi-turn scenarios)")
    parser.add_argument(
        "--scenarios",
        type=Path,
        default=Path(__file__).resolve().parent / "ai_judge_scenarios.json",
        help="Ruta al JSON de escenarios",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("GOLDEN_BASE_URL", "http://localhost:8000"),
        help="URL base del backend",
    )
    parser.add_argument("--timeout", type=int, default=60, help="Timeout por request")
    parser.add_argument("--judge", action="store_true", help="Activar LLM as a Judge")
    parser.add_argument("--verbose", "-v", action="store_true", help="Salida detallada")
    parser.add_argument(
        "--auth-token",
        default=os.getenv("EVAL_BEARER_TOKEN", ""),
        help="Bearer token para /invoke (opcional). Si no se pasa, intenta login con LOGIN_USER/LOGIN_PASSWORD.",
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
        "--out",
        type=Path,
        default=Path(__file__).resolve().parent / "reports" / "ai_judge_report.json",
        help="Ruta de salida para el reporte JSON",
    )
    args = parser.parse_args()
    _load_dotenv_if_available()

    if not args.scenarios.is_file():
        print(f"No existe archivo de escenarios: {args.scenarios}", file=sys.stderr)
        return 2

    payload = _load_json(args.scenarios)
    base_url = payload.get("base_url") or args.base_url
    scenarios = payload.get("scenarios") or []
    if not scenarios:
        print("No hay escenarios para ejecutar.", file=sys.stderr)
        return 2

    print(f"AI Judge scenarios: {args.scenarios}")
    print(f"Backend:            {base_url}")
    print(f"Judge LLM:          {'sí' if args.judge else 'no'}")
    print(f"Escenarios:         {len(scenarios)}\n")
    auth_headers = _build_auth_headers(
        base_url=base_url,
        timeout=args.timeout,
        explicit_token=args.auth_token,
        explicit_user=args.auth_user,
        explicit_password=args.auth_password,
    )

    results: list[ScenarioResult] = []
    for i, scenario in enumerate(scenarios, start=1):
        sid = scenario.get("id", f"scenario-{i}")
        print(f"[{i}/{len(scenarios)}] {sid} ...", end=" ")
        result = run_scenario(
            base_url=base_url,
            scenario=scenario,
            timeout=args.timeout,
            use_judge=args.judge,
            verbose=args.verbose,
            auth_headers=auth_headers,
        )
        results.append(result)
        print("PASS" if result.passed else "FAIL")

    report = _serialize(results)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("\nResumen:")
    print(
        f"  total={report['total_scenarios']} pass={report['passed_scenarios']} "
        f"fail={report['failed_scenarios']} rate={report['pass_rate']}%"
    )
    print(f"  reporte: {args.out}")
    return 1 if report["failed_scenarios"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

