import uuid
import json
import redis
import time
import os
from dotenv import load_dotenv
from fastapi import Request, FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import messages_to_dict
from langchain.memory.chat_memory import BaseChatMemory
from apscheduler.schedulers.background import BackgroundScheduler

from core.agent_orchestrator import AgentOrchestrator
from core.config_manager import load_all_agent_configs, get_agent_config
import logging

from core.agent_factory import get_agent_orchestrator, memory_cache
from components.memory.memory_factory import get_memory_for_agent
from core.config_manager import DEFAULT_AGENT_KEY

load_dotenv()
app = FastAPI(title="Plataforma de Agentes de IA - Mapfre Seguros")

logger = logging.getLogger(__name__)

@app.on_event("startup")
def startup_event():
    load_all_agent_configs("agents")
    logger.info("--- [Startup] Configuraciones de agentes cargadas. ---")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

API_KEY_SECRET = os.getenv("API_KEY_SECRET")
REDIS_URL = os.getenv("REDIS_URL")
if not REDIS_URL: 
    raise RuntimeError("REDIS_URL no está configurada.")
redis_client = redis.Redis.from_url(REDIS_URL)

class InvokeRequest(BaseModel):
    input: str
    session_id: Optional[str] = None
    config_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    model_id: Optional[str] = None

class InvokeResponse(BaseModel):
    session_id: str
    response: str
    full_history: List[Dict]
    structured_data: Optional[Dict] = None
    raw_agent_response: Optional[str] = None 
    request_cost: Optional[float] = None 

@app.post("/invoke")
async def invoke_agent(request: InvokeRequest, background_tasks: BackgroundTasks):
    start_time = time.time()
    
    try:
        session_id = request.session_id or str(uuid.uuid4())
        
        state_key = f"state:{session_id}"
        current_state = {}
        state_data = redis_client.get(state_key)
        if state_data:
            current_state = json.loads(state_data)
        
        # Determinar qué agente usar
        if current_state.get("route") == "triage" or not current_state.get("active_agent_key"):
            active_agent_key = "triage_agent"
        else:
            active_agent_key = current_state.get("active_agent_key", "triage_agent")

        agent_config = get_agent_config(active_agent_key)
        if not agent_config:
            raise HTTPException(status_code=404, detail=f"Agente '{active_agent_key}' no encontrado.")
        
        orchestrator = get_agent_orchestrator(active_agent_key, agent_config)
        llm_instance = orchestrator.get_llm_for_request(request.model_id)
        
        memory = memory_cache.get(session_id) or get_memory_for_agent(agent_config, llm_instance, session_id)
        memory_cache[session_id] = memory
        
        logger.info(f"--- Petición para Agente: {active_agent_key} | Sesión ID: {session_id} ---")
        logger.info(f">>> Usuario: {request.input}")

        metadata = request.metadata or {}
        metadata["current_state"] = current_state

        final_state = await orchestrator.invoke(request.input, memory, request.model_id, metadata, background_tasks)
        
        new_structured_data = final_state.get("structured_data", {})

        # Manejar transiciones entre agentes
        next_agent_from_triage = new_structured_data.pop("next_agent", None)
        if next_agent_from_triage:
            new_structured_data["active_agent_key"] = next_agent_from_triage
            print(f"--- [Orquestador] Transición al agente: {next_agent_from_triage} ---")
        else:
            new_structured_data["active_agent_key"] = active_agent_key

        if new_structured_data:
            redis_client.set(state_key, json.dumps(new_structured_data), ex=3600)
            print(f"--- [Estado] Nuevo estado guardado. Próximo Agente: '{new_structured_data['active_agent_key']}'. Próxima Ruta: '{new_structured_data.get('route')}' ---")

        return InvokeResponse(
            session_id=session_id,
            response=final_state.get("output", ""),
            full_history=messages_to_dict(final_state.get('chat_history', [])),
            structured_data=new_structured_data,
            raw_agent_response=final_state.get("raw_agent_response", ""),
            request_cost=final_state.get("request_cost")
        )
    except Exception as e:
        logger.error(f"Error interno del servidor: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {e}")

@app.get("/")
async def root():
    return {"message": "Plataforma de Agentes de IA - Mapfre Seguros", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
