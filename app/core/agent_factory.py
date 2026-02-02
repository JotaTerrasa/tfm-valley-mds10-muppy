import logging
from typing import Dict
from fastapi import HTTPException
from langchain.memory.chat_memory import BaseChatMemory
from app.core.agent_orchestrator import AgentOrchestrator

agent_cache: Dict[str, AgentOrchestrator] = {}
memory_cache: Dict[str, BaseChatMemory] = {}

logger = logging.getLogger(__name__)

def get_agent_orchestrator(config_key: str, agent_config: dict) -> AgentOrchestrator:
    """
    Crea y cachea una instancia de AgentOrchestrator a partir de una configuración.
    Esta función ahora es el único punto de verdad para obtener un agente.
    """
    if config_key not in agent_cache:
        logger.info(f"--- [Agent Factory] Creando y cacheando nuevo agente: {config_key} ---")
        try:
            agent_cache[config_key] = AgentOrchestrator(agent_config)
            logger.info(f"--- [Agent Factory] Agente '{config_key}' cargado con éxito. ---")
        except Exception as e:
            logger.error(f"Error al cargar la configuración del agente: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error al cargar la configuración del agente: {e}")
    return agent_cache[config_key]
