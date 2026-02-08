#!/usr/bin/env python3
"""
Genera un único PNG del grafo global de orquestación (triage → quote / contract / support).
Uso (desde la raíz del proyecto, con venv activado):
  python scripts/export_graph_png.py
El PNG se guarda como agents/global_graph.png.
"""
import os
import sys
from typing import Literal, TypedDict

# Raíz del proyecto (parent de scripts/)
_project_dir = os.path.abspath(os.path.dirname(__file__))
project_root = os.path.dirname(_project_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, ".env"))

from langgraph.graph import StateGraph, END


class GlobalState(TypedDict, total=False):
    next_agent: str


def _build_global_graph():
    """Grafo global: entrada en triage, enrutado a quote, contract o support."""
    workflow = StateGraph(GlobalState)

    def noop(state: GlobalState) -> dict:
        return {}

    # Nodos (uno por agente a nivel orquestación)
    workflow.add_node("triage_agent", noop)
    workflow.add_node("quote_agent", noop)
    workflow.add_node("contract_agent", noop)
    workflow.add_node("support_agent", noop)

    # Entrada: siempre triage
    workflow.set_entry_point("triage_agent")

    # Triage enruta a uno de los tres agentes (según next_agent en estado)
    def route_after_triage(state: GlobalState) -> Literal["quote_agent", "contract_agent", "support_agent"]:
        next_agent = (state or {}).get("next_agent") or "quote_agent"
        if next_agent not in ("quote_agent", "contract_agent", "support_agent"):
            return "quote_agent"
        return next_agent

    workflow.add_conditional_edges(
        "triage_agent",
        route_after_triage,
        {
            "quote_agent": "quote_agent",
            "contract_agent": "contract_agent",
            "support_agent": "support_agent",
        },
    )

    workflow.add_edge("quote_agent", END)
    workflow.add_edge("contract_agent", END)
    workflow.add_edge("support_agent", END)

    return workflow.compile()


def main():
    output_dir = os.path.join(project_root, "agents")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "global_graph.png")

    graph = _build_global_graph()
    graph.get_graph().draw_mermaid_png(output_file_path=output_path)
    print(f"--- Grafo global guardado: {output_path} ---")


if __name__ == "__main__":
    main()
