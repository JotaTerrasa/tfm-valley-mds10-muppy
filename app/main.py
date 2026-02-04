import uuid
import json
import time
import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Arize Phoenix (LangGraph exporter): registrar antes de importar LangChain/LangGraph.
try:
    if os.getenv("PHOENIX_PROJECT_NAME") or os.getenv("PHOENIX_ENABLED", "").lower() in ("1", "true", "yes"):
        from phoenix.otel import register
        register(
            project_name=os.getenv("PHOENIX_PROJECT_NAME", "tfm-muppy-multiagent"),
            auto_instrument=True,
            batch=os.getenv("PHOENIX_BATCH", "true").lower() in ("1", "true", "yes"),
        )
except Exception as e:
    import warnings
    warnings.warn(f"Phoenix tracing no inicializado: {e}", UserWarning)

from fastapi import Request, FastAPI, HTTPException, BackgroundTasks, Depends, Header
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import messages_to_dict
from langchain.memory.chat_memory import BaseChatMemory

from app.core.agent_orchestrator import AgentOrchestrator
from app.core.config_manager import load_all_agent_configs, get_agent_config
from app.core.agent_factory import get_agent_orchestrator, memory_cache
from app.components.memory.memory_factory import get_memory_for_agent
from app.core.config_manager import DEFAULT_AGENT_KEY
from app.auth import (
    is_login_required,
    verify_user,
    create_access_token,
    get_current_user_optional,
    register_user,
)
from app.auth import LOGIN_USER as _ENV_LOGIN_USER

app = FastAPI(title="Plataforma de Agentes de IA - Mapfre Seguros")

logger = logging.getLogger(__name__)

# Estado de sesión en memoria (sin Redis)
session_store: Dict[str, dict] = {}

@app.on_event("startup")
def startup_event():
    load_all_agent_configs("agents")
    logger.info("--- [Startup] Configuraciones de agentes cargadas. ---")
    if is_login_required():
        if _ENV_LOGIN_USER:
            logger.info("--- [Startup] Login activo. Usuario env: '%s' (y/o data/users.json). ---", _ENV_LOGIN_USER)
        else:
            logger.info("--- [Startup] Login activo (usuarios en data/users.json). ---")
    else:
        logger.info("--- [Startup] Login no configurado: /invoke es público. ---")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

API_KEY_SECRET = os.getenv("API_KEY_SECRET")
REGISTER_SECRET = os.getenv("REGISTER_SECRET", API_KEY_SECRET)


class RegisterRequest(BaseModel):
    username: str
    password: str


def require_admin_key(x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    """Exige cabecera X-Admin-Key para registrar usuarios."""
    if not REGISTER_SECRET:
        raise HTTPException(status_code=503, detail="Registro no configurado (REGISTER_SECRET o API_KEY_SECRET)")
    if x_admin_key != REGISTER_SECRET:
        raise HTTPException(status_code=403, detail="Clave de administrador incorrecta")


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


@app.get("/auth/required")
async def auth_required():
    """Indica si el backend exige login para usar el chat. El frontend lo usa para mostrar o no la pantalla de login."""
    return {"login_required": is_login_required()}


@app.post("/auth/login")
async def login(form: OAuth2PasswordRequestForm = Depends()):
    """Login con usuario y contraseña. Devuelve un token JWT."""
    if not verify_user(form.username, form.password):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    token = create_access_token(subject=form.username)
    return {"access_token": token, "token_type": "bearer"}


@app.post("/auth/register")
async def register(
    body: RegisterRequest,
    _: None = Depends(require_admin_key),
):
    """
    Registra un nuevo usuario (solo con clave de admin).
    Cabecera: X-Admin-Key: <API_KEY_SECRET o REGISTER_SECRET>
    """
    try:
        register_user(body.username, body.password)
        return {"message": f"Usuario '{body.username}' registrado correctamente"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/invoke")
async def invoke_agent(
    request: InvokeRequest,
    background_tasks: BackgroundTasks,
    _user: Optional[str] = Depends(get_current_user_optional),
):
    start_time = time.time()
    
    try:
        session_id = request.session_id or str(uuid.uuid4())
        
        current_state = session_store.get(session_id, {})
        
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
        metadata["session_id"] = session_id

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
            session_store[session_id] = new_structured_data
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
