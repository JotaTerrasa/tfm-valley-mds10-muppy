import os
import logging

# Cargar .env lo primero (raíz del proyecto + fallbacks)
import app.env_loader as _env  # noqa: E402

import uuid
import json

# Arize AX (Tracing Projects): registrar e instrumentar LangChain antes de importar LangChain.
_arize_tracer = None
try:
    _arize_key = os.getenv("ARIZE_API_KEY") or os.getenv("PHOENIX_API_KEY")
    _arize_space = os.getenv("ARIZE_SPACE_ID", "U3BhY2U6OTMyOk1tZm8=")
    if _arize_key and _arize_space:
        from arize.otel import register as arize_register
        # Endpoint: ARIZE_COLLECTOR_ENDPOINT en .env (EU: https://otlp.eu-west-1a.arize.com/v1)
        _arize_tracer = arize_register(
            space_id=_arize_space,
            api_key=_arize_key,
            project_name=os.getenv("ARIZE_PROJECT_NAME") or os.getenv("PHOENIX_PROJECT_NAME") or "mapfre-muppy",
        )
        from openinference.instrumentation.langchain import LangChainInstrumentor
        LangChainInstrumentor().instrument(tracer_provider=_arize_tracer)
except Exception as e:
    import warnings
    warnings.warn(f"Arize AX tracing no inicializado: {e}", UserWarning)

from fastapi import Request, FastAPI, HTTPException, BackgroundTasks, Depends, Header
from fastapi.responses import PlainTextResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import messages_to_dict
from langchain_core.chat_history import BaseChatMessageHistory

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
from app.logging_config import set_request_id, clear_request_id, setup_correlation_logging
from app.channels import (
    build_whatsapp_session_id,
    extract_whatsapp_messages,
    send_whatsapp_text,
    verify_whatsapp_signature,
)

app = FastAPI(title="Plataforma de Agentes de IA - Mapfre Seguros")

logger = logging.getLogger(__name__)

# Estado de sesión en memoria (sin Redis)
session_store: Dict[str, dict] = {}

@app.on_event("startup")
def startup_event():
    # Forzar carga de .env al arranque (por si el proceso se inició con otro cwd)
    _env.load_env()
    setup_correlation_logging()  # request_id, trace_id, span_id en logs
    load_all_agent_configs("agents")
    logger.info("--- [Startup] Configuraciones de agentes cargadas. ---")
    if is_login_required():
        if _ENV_LOGIN_USER:
            logger.info("--- [Startup] Login activo. Usuario env: '%s' (y/o data/users.json). ---", _ENV_LOGIN_USER)
        else:
            logger.info("--- [Startup] Login activo (usuarios en data/users.json). ---")
    else:
        logger.info("--- [Startup] Login no configurado: /invoke es público. ---")
    key = os.getenv("GOOGLE_API_KEY")
    env_path = _env.ENV_PATH
    env_exists = env_path.is_file()
    if not key:
        print(f"--- [Startup] GOOGLE_API_KEY NO configurada. .env buscado en: {env_path} (existe: {env_exists}). ---")
        logger.warning("--- [Startup] GOOGLE_API_KEY no está configurada. Añádela al .env o /invoke fallará. ---")
    else:
        print("--- [Startup] GOOGLE_API_KEY cargada correctamente. ---")
        logger.info("--- [Startup] GOOGLE_API_KEY cargada correctamente. ---")

# Request ID: trazabilidad de peticiones (headers + OpenTelemetry)
REQUEST_ID_HEADER = "X-Request-ID"

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        request.state.request_id = request_id
        set_request_id(request_id)  # Para que todos los logs de la petición lleven request_id/trace_id
        # Añadir al span actual de OpenTelemetry para verlo en Arize
        try:
            from opentelemetry import trace
            span = trace.get_current_span()
            if span.is_recording():
                span.set_attribute("request_id", request_id)
        except Exception:
            pass
        try:
            response = await call_next(request)
            response.headers[REQUEST_ID_HEADER] = request_id
            return response
        finally:
            clear_request_id()

app.add_middleware(RequestIDMiddleware)
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


async def _process_invoke_request(
    request: InvokeRequest,
    background_tasks: BackgroundTasks,
) -> InvokeResponse:
    try:
        session_id = request.session_id or str(uuid.uuid4())
        
        current_state = session_store.get(session_id, {})
        user_input_lc = (request.input or "").lower()
        backtrack_markers = ("volver", "atrás", "atras", "cambiar", "corregir", "me equivoqué", "me equivoque")
        if current_state.get("active_agent_key") and current_state.get("active_agent_key") != "triage_agent":
            if any(marker in user_input_lc for marker in backtrack_markers):
                logger.info("--- [Main] Solicitud de retroceso detectada. Forzando vuelta a triage. ---")
                current_state["route"] = "triage"
                current_state["next_agent"] = None
                current_state["active_agent_key"] = "triage_agent"
                current_state["pending_field"] = None
                current_state["invalid_reason"] = None
                current_state["ready_for_commit"] = False
                current_state["missing_fields"] = []
                current_state["payment_link"] = None
                current_state["payment_status"] = "pending"
        
        # Determinar qué agente usar (fallback robusto a triage)
        route = current_state.get("route")
        active_agent_key = current_state.get("active_agent_key")
        if route == "triage" or not active_agent_key:
            active_agent_key = "triage_agent"
        elif not get_agent_config(active_agent_key):
            logger.warning("--- [Main] Agente '%s' no válido en estado. Volviendo a triage. ---", active_agent_key)
            active_agent_key = "triage_agent"
            current_state["route"] = "triage"

        agent_config = get_agent_config(active_agent_key)
        if not agent_config:
            raise HTTPException(status_code=404, detail=f"Agente '{active_agent_key}' no encontrado.")
        
        orchestrator = get_agent_orchestrator(active_agent_key, agent_config)
        llm_instance = orchestrator.get_llm_for_request(request.model_id)
        
        memory = memory_cache.get(session_id) or get_memory_for_agent(agent_config, llm_instance, session_id)
        memory_cache[session_id] = memory
        
        logger.info(f"--- Agente: {active_agent_key} | Sesión: {session_id} ---")
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


@app.post("/invoke")
async def invoke_agent(
    request: InvokeRequest,
    background_tasks: BackgroundTasks,
    _user: Optional[str] = Depends(get_current_user_optional),
):
    return await _process_invoke_request(request, background_tasks)


async def _process_whatsapp_message(inbound_message: Dict[str, Any]) -> None:
    from_number = inbound_message.get("from", "")
    user_text = (inbound_message.get("text") or "").strip()
    if not from_number or not user_text:
        return

    session_id = build_whatsapp_session_id(from_number)
    invoke_request = InvokeRequest(
        input=user_text,
        session_id=session_id,
        metadata={
            "source": "whatsapp",
            "whatsapp": {
                "from": from_number,
                "message_id": inbound_message.get("message_id"),
                "timestamp": inbound_message.get("timestamp"),
                "phone_number_id": inbound_message.get("phone_number_id"),
            },
        },
    )

    try:
        response = await _process_invoke_request(invoke_request, BackgroundTasks())
        await send_whatsapp_text(from_number, response.response or "Ahora mismo no tengo una respuesta.")
        logger.info("--- [WhatsApp] Respuesta enviada a %s (session_id=%s). ---", from_number, session_id)
    except Exception as e:
        logger.error("--- [WhatsApp] Fallo procesando mensaje entrante: %s ---", e, exc_info=True)


@app.get("/webhooks/whatsapp")
async def whatsapp_webhook_verify(request: Request):
    mode = request.query_params.get("hub.mode")
    verify_token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    expected_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "").strip()

    if mode == "subscribe" and expected_token and verify_token == expected_token and challenge:
        return PlainTextResponse(content=challenge, status_code=200)
    raise HTTPException(status_code=403, detail="Webhook verify token inválido")


@app.post("/webhooks/whatsapp")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    raw_body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    if not verify_whatsapp_signature(raw_body, signature):
        raise HTTPException(status_code=401, detail="Firma de webhook inválida")

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Payload JSON inválido")

    messages = extract_whatsapp_messages(payload)
    if not messages:
        return {"status": "ignored", "reason": "no_text_messages"}

    for inbound_message in messages:
        background_tasks.add_task(_process_whatsapp_message, inbound_message)

    return {"status": "accepted", "messages": len(messages)}

@app.get("/")
async def root():
    return {"message": "Plataforma de Agentes de IA - Mapfre Seguros", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
