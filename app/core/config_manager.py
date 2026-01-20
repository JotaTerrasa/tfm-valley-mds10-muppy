# app/core/config_manager.py

import os
import json
from typing import Dict

AGENT_CONFIGS: Dict[str, Dict] = {}
DEFAULT_AGENT_KEY = "triage_agent"  

def load_all_agent_configs(relative_config_dir: str = "agents"):
    """
    Escanea un directorio de agentes, carga cada config.json y le inyecta
    la ruta base de su propio directorio para que los recursos relativos
    (como los prompts) puedan ser localizados.
    """
    try:
        base_path = os.path.abspath(os.path.dirname(__file__))
        project_root = os.path.dirname(os.path.dirname(base_path))
        config_dir = os.path.join(project_root, relative_config_dir)

        print(
            f"--- [Config Manager] Buscando configuraciones en: '{config_dir}' ---")
        if not os.path.isdir(config_dir):
            print(
                f"--- [Config Manager] ADVERTENCIA: El directorio '{config_dir}' NO EXISTE. ---")
            return

        for agent_name in os.listdir(config_dir):
            if agent_name.startswith('.'):
                continue

            agent_path = os.path.join(config_dir, agent_name)
            if os.path.isdir(agent_path):
                config_file_path = os.path.join(agent_path, 'config.json')
                if os.path.isfile(config_file_path):
                    config_key = agent_name
                    try:
                        with open(config_file_path, 'r', encoding='utf-8') as f:
                            config_data = json.load(f)

                        config_data['__agent_base_path__'] = agent_path

                        AGENT_CONFIGS[config_key] = config_data
                        print(
                            f"--- [Config Manager] Configuración '{config_key}' cargada y enriquecida. ---")
                    except Exception as e:
                        print(
                            f"--- [Config Manager] ERROR al cargar '{config_key}': {e} ---")

        if not AGENT_CONFIGS:
            print(
                "--- [Config Manager] ADVERTENCIA: No se cargó ninguna configuración de agente. ---")
    except Exception as e:
        print(f"--- [Config Manager] ERROR INESPERADO: {e} ---")


def get_agent_config(config_key: str) -> Dict:
    """Obtiene una configuración de agente ya cargada."""
    return AGENT_CONFIGS.get(config_key)


