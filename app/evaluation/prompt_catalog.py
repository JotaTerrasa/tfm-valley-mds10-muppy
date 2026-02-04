"""
Catálogo de prompts por agente y nodo del grafo.
Analiza las configuraciones de cada agente (state_machine) y carga el texto de cada prompt
para evaluación y envío a Arize Phoenix.
"""
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class PromptEntry:
    """Una entrada del catálogo: agente, nodo, ruta del prompt y contenido."""
    agent_key: str
    node_name: str
    prompt_path: str
    full_path: str
    prompt_text: str
    available_tools: List[str] = field(default_factory=list)


def load_prompt_text(base_path: str, relative_path: str) -> str:
    """Carga el contenido de un archivo de prompt (solo rutas locales)."""
    full = os.path.join(base_path, relative_path)
    if not os.path.isfile(full):
        return ""
    with open(full, "r", encoding="utf-8") as f:
        return f.read()


def build_prompt_catalog(agent_configs: Dict[str, Dict[str, Any]]) -> List[PromptEntry]:
    """
    Construye el catálogo de todos los prompts usados en el grafo de cada agente.
    agent_configs: dict { agent_key: config } con __agent_base_path__ y state_machine.nodes.
    """
    catalog: List[PromptEntry] = []
    for agent_key, config in agent_configs.items():
        if config.get("strategy") != "state_machine":
            continue
        base_path = config.get("__agent_base_path__")
        if not base_path or not os.path.isdir(base_path):
            continue
        nodes = config.get("state_machine", {}).get("nodes", {})
        for node_name, node_config in nodes.items():
            prompt_path = node_config.get("prompt_path")
            if not prompt_path:
                continue
            full_path = os.path.join(base_path, prompt_path)
            prompt_text = load_prompt_text(base_path, prompt_path)
            tools = node_config.get("available_tools", [])
            catalog.append(PromptEntry(
                agent_key=agent_key,
                node_name=node_name,
                prompt_path=prompt_path,
                full_path=os.path.abspath(full_path),
                prompt_text=prompt_text,
                available_tools=tools,
            ))
    return catalog


def catalog_to_dict(catalog: List[PromptEntry]) -> List[Dict[str, Any]]:
    """Convierte el catálogo a lista de dicts para serialización o envío a Arize."""
    return [
        {
            "agent_key": e.agent_key,
            "node_name": e.node_name,
            "prompt_path": e.prompt_path,
            "full_path": e.full_path,
            "prompt_text": e.prompt_text,
            "available_tools": e.available_tools,
            "prompt_length": len(e.prompt_text),
        }
        for e in catalog
    ]
