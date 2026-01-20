import json
from typing import Dict, Optional, Any, AsyncGenerator
from strategies.registry import get_strategy
from handlers.persistence_handler import handle_persistence
from core.llm_factory import get_llm
from utils.cost_calculation import calculate_request_cost
from tools.registry import get_tool_by_name
from fastapi import BackgroundTasks
try:
    from google.api_core.exceptions import NotFound as GoogleNotFound
except Exception: 
    GoogleNotFound = Exception

class AgentOrchestrator:
    def __init__(self, agent_config: dict):
        """
        El constructor ya no crea una instancia de LLM. Solo prepara la configuración
        y la clase de la estrategia que se usará.
        """
        self.config = agent_config
        all_tool_names = set()
        nodes_config = self.config.get("state_machine", {}).get("nodes", {})
        for node_name, node_config in nodes_config.items():
            for tool_name in node_config.get("available_tools", []):
                all_tool_names.add(tool_name)
        
        unique_tool_names = list(all_tool_names)
        print(f"--- [Orquestador] Nombres de herramientas requeridas: {unique_tool_names} ---")
        
        self.llm_instances: Dict[str, Any] = {} 
        
        strategy_name = self.config.get("strategy", "generative")
        StrategyClass = get_strategy(strategy_name)
        
        self.strategy = StrategyClass(llm=None, tool_names=unique_tool_names, config=self.config)

    def _get_llm_instance(self, model_id: str, llm_config: Dict[str, Any]):
        """
        Obtener/crear y cachear la instancia del LLM.
        """
        if model_id not in self.llm_instances:
            print(f"--- [Orquestador] Creando y cacheando nueva instancia para el modelo: {model_id} ---")
            self.llm_instances[model_id] = get_llm(llm_config)
        else:
            print(f"--- [Orquestador] Usando instancia de LLM cacheada para el modelo: {model_id} ---")
        return self.llm_instances[model_id]
    
    def get_llm_for_request(self, model_id: Optional[str] = None):
        """
        Obtiene la instancia del LLM que se usará para una petición,
        basándose en el model_id o en el por defecto.
        """
        llm_configs = self.config.get("llm_configurations", {})
        models = llm_configs.get("models", {})
        final_model_id = model_id or llm_configs.get("default_model")

        if not final_model_id or final_model_id not in models:
            raise ValueError(f"El model_id '{final_model_id}' no es válido o no se encontró una configuración por defecto en el JSON del agente.")

        selected_llm_config = models[final_model_id]
        return self._get_llm_instance(final_model_id, selected_llm_config)

    async def invoke(self, user_input: str, memory: Any, model_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None, background_tasks: Optional[BackgroundTasks] = None):

        llm_configs = self.config.get("llm_configurations", {})
        models = llm_configs.get("models", {})
        selected_model_id = model_id or llm_configs.get("default_model")
        if not selected_model_id or selected_model_id not in models:
            raise ValueError(f"El model_id '{selected_model_id}' no es válido o no se encontró una configuración por defecto en el JSON del agente.")

        llm_instance = self._get_llm_instance(selected_model_id, models[selected_model_id])
        self.strategy.llm = llm_instance

        print("--- [Orquestador] Memoria recibida. Invocando estrategia... ---")

        try:
            result = await self.strategy.invoke(user_input, memory, metadata)
            used_model_id = selected_model_id
        except GoogleNotFound as e:
            fallback_id = "gemini-2.5-flash"
            if selected_model_id != fallback_id and fallback_id in models:
                print(f"--- [Orquestador] Modelo '{selected_model_id}' no disponible. Reintentando con fallback '{fallback_id}'... ---")
                self.strategy.llm = self._get_llm_instance(fallback_id, models[fallback_id])
                result = await self.strategy.invoke(user_input, memory, metadata)
                used_model_id = fallback_id
            else:
                raise e

        # CALCULO PRECIO TOKENS
        token_usage = result.get("token_usage", {})
        pricing_info = models.get(used_model_id, {}).get("pricing", {})
        request_cost = calculate_request_cost(token_usage, pricing_info)

        result["request_cost"] = request_cost
        print(f"--- [Orquestador] Coste de la petición: ${request_cost:.6f} ---")
        # CALCULO PRECIO TOKENS

        print("--- [Orquestador] Estrategia ejecutada con éxito. ---")
        
        return result
