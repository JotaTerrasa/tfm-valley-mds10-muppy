import os
import logging

# Cargar .env lo primero (raíz del proyecto + fallbacks)
import app.env_loader as _env  # noqa: E402

import uuid
import json
import re
from urllib.parse import urlparse

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


def _extract_stripe_checkout_session_id(payment_link: Optional[str]) -> Optional[str]:
    if not payment_link:
        return None
    try:
        path = urlparse(payment_link).path or ""
    except Exception:
        path = payment_link
    # Checkout links suelen llevar .../c/pay/cs_test_xxx o .../pay/cs_test_xxx
    match = re.search(r"(cs_(?:test|live)_[A-Za-z0-9]+)", path)
    if match:
        return match.group(1)
    # Fallback por si el enlace llega sin parseo de URL
    match = re.search(r"(cs_(?:test|live)_[A-Za-z0-9]+)", payment_link)
    return match.group(1) if match else None


def _sanitize_stripe_link_for_whatsapp(payment_link: Optional[str]) -> Optional[str]:
    """
    Devuelve el enlace de checkout en texto plano (sin markdown),
    conservando la URL completa original de Stripe.
    """
    if not payment_link:
        return None
    raw = str(payment_link).strip()
    # Si por cualquier motivo llega en markdown [url](url), extraemos la URL.
    md_match = re.match(r"^\[[^\]]+\]\((https?://[^\s)]+)\)$", raw)
    if md_match:
        return md_match.group(1)
    return raw


def _sanitize_contract_state(structured_data: Dict[str, Any]) -> None:
    """Evita rutas inválidas en contract_agent que rompen el grafo."""
    if not structured_data:
        return
    if structured_data.get("active_agent_key") != "contract_agent":
        return
    allowed_routes = {"data_capture", "verification", "payment", "final_summary"}
    current_route = structured_data.get("route")
    if current_route not in allowed_routes:
        structured_data["route"] = "data_capture"
        structured_data["status"] = structured_data.get("status") or "incomplete"
        structured_data["payment_status"] = structured_data.get("payment_status") or "pending"


def _candidate_session_ids(internal_session_id: Optional[str]) -> List[str]:
    """Genera posibles claves de sesión para mapear webhooks de Stripe."""
    if not internal_session_id:
        return []
    base = str(internal_session_id).strip()
    if not base:
        return []
    candidates = [base]
    if base.startswith("wa:"):
        plain = base.replace("wa:", "", 1).strip()
        if plain:
            candidates.append(plain)
    else:
        candidates.append(f"wa:{base}")
    # Deduplicar preservando orden
    deduped: List[str] = []
    for key in candidates:
        if key and key not in deduped:
            deduped.append(key)
    return deduped


def _find_sessions_by_checkout_id(checkout_session_id: Optional[str]) -> List[str]:
    if not checkout_session_id:
        return []
    matches: List[str] = []
    for sid, state in session_store.items():
        if (state or {}).get("stripe_checkout_session_id") == checkout_session_id:
            matches.append(sid)
    return matches


def _mark_payment_success_for_session(session_id: str, checkout_session_id: Optional[str], stripe_payment_status: Optional[str]) -> bool:
    state = session_store.get(session_id, {})
    # Idempotencia: si ya estaba confirmado para este mismo checkout, no repetir acciones.
    if (
        state.get("payment_status") == "successful"
        and checkout_session_id
        and state.get("stripe_checkout_session_id") == checkout_session_id
    ):
        return False
    state["payment_status"] = "successful"
    state["payment_link"] = None
    state["route"] = "final_summary"
    state["status"] = "new"
    state["active_agent_key"] = state.get("active_agent_key") or "contract_agent"
    state["stripe_checkout_session_id"] = checkout_session_id
    state["stripe_payment_status"] = stripe_payment_status
    session_store[session_id] = state
    return True


def _mark_payment_failed_for_session(session_id: str) -> None:
    state = session_store.get(session_id, {})
    state["payment_status"] = "failed"
    state["route"] = "payment"
    state["active_agent_key"] = state.get("active_agent_key") or "contract_agent"
    session_store[session_id] = state

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
            if next_agent_from_triage == "contract_agent":
                _sanitize_contract_state(new_structured_data)
            print(f"--- [Orquestador] Transición al agente: {next_agent_from_triage} ---")
        else:
            new_structured_data["active_agent_key"] = active_agent_key
            _sanitize_contract_state(new_structured_data)

        if new_structured_data:
            payment_link = new_structured_data.get("payment_link")
            if payment_link and not new_structured_data.get("stripe_checkout_session_id"):
                checkout_session_id = _extract_stripe_checkout_session_id(payment_link)
                if checkout_session_id:
                    new_structured_data["stripe_checkout_session_id"] = checkout_session_id
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
    current_state = session_store.get(session_id, {})

    # Si la conversación anterior terminó y el pago quedó confirmado,
    # cualquier mensaje nuevo inicia una conversación limpia desde triage.
    if (
        current_state.get("status") == "new"
        and current_state.get("route") == "final_summary"
        and current_state.get("payment_status") == "successful"
    ):
        session_store.pop(session_id, None)
        memory_cache.pop(session_id, None)
        logger.info("--- [WhatsApp] Sesión completada detectada. Reinicio de conversación para %s. ---", session_id)
        ack_markers = {"ok", "vale", "vake", "perfecto", "genial", "de acuerdo", "entendido", "listo"}
        if user_text.lower().strip() in ack_markers:
            await send_whatsapp_text(
                from_number,
                "Conversación reiniciada correctamente. ¿En qué puedo ayudarte ahora? Puedo cotizar, contratar o ayudarte con soporte.",
            )
            return

    # Fallback anti-race: si el usuario confirma pago antes de que llegue/actualice webhook,
    # consultamos Stripe por checkout_session_id y actualizamos estado al vuelo.
    paid_markers = {
        "ya lo he hecho",
        "ya pague",
        "ya pagué",
        "pagado",
        "he pagado",
        "listo pagado",
    }
    if user_text.lower().strip() in paid_markers and current_state.get("payment_status") != "successful":
        checkout_session_id = current_state.get("stripe_checkout_session_id")
        stripe_secret = (os.getenv("STRIPE_SECRET_KEY") or "").strip()
        if checkout_session_id and stripe_secret:
            try:
                import stripe

                stripe.api_key = stripe_secret
                checkout = stripe.checkout.Session.retrieve(checkout_session_id)
                if checkout and checkout.get("payment_status") == "paid":
                    _mark_payment_success_for_session(
                        session_id=session_id,
                        checkout_session_id=checkout_session_id,
                        stripe_payment_status="paid",
                    )
                    await send_whatsapp_text(
                        from_number,
                        "Pago de prueba confirmado correctamente. Tu solicitud queda registrada y pasamos al cierre final.",
                    )
                    return
            except Exception as e:
                logger.warning("--- [WhatsApp] No se pudo validar pago en Stripe en tiempo real: %s ---", e)

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
        outbound_text = response.response or "Ahora mismo no tengo una respuesta."

        # WhatsApp renderiza mejor enlaces en texto plano.
        # Si hay payment_link en estado y estamos en fase de pago, lo enviamos una sola vez.
        structured = response.structured_data or {}
        payment_link = structured.get("payment_link")
        payment_status = structured.get("payment_status")
        route = structured.get("route")
        should_force_payment_message = bool(payment_link) and payment_status != "successful" and route in {"payment", "final_summary"}
        if should_force_payment_message:
            # Eliminar links markdown repetidos que pueda generar el LLM.
            outbound_text = re.sub(r"\[[^\]]+\]\((https?://[^\s)]+)\)", r"\1", outbound_text)
            # Evitar múltiples enlaces de checkout en el mismo mensaje.
            outbound_text = re.sub(r"(https://checkout\.stripe\.com/\S+).*(https://checkout\.stripe\.com/\S+)", r"\1", outbound_text, flags=re.DOTALL)
            clean_payment_link = _sanitize_stripe_link_for_whatsapp(payment_link) or payment_link
            outbound_text = (
                "Tu solicitud está lista para pago de prueba.\n\n"
                f"Enlace de pago:\n{clean_payment_link}\n\n"
                "Cuando lo completes, responde: Ya lo he hecho."
            )

        await send_whatsapp_text(from_number, outbound_text)
        logger.info("--- [WhatsApp] Respuesta enviada a %s (session_id=%s). ---", from_number, session_id)
    except Exception as e:
        logger.error("--- [WhatsApp] Fallo procesando mensaje entrante: %s ---", e, exc_info=True)


@app.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()
    if not webhook_secret:
        raise HTTPException(status_code=503, detail="STRIPE_WEBHOOK_SECRET no configurado")

    stripe_signature = request.headers.get("Stripe-Signature")
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Falta cabecera Stripe-Signature")

    payload = await request.body()

    try:
        import stripe

        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=stripe_signature,
            secret=webhook_secret,
        )
    except Exception as e:
        logger.error("--- [Stripe] Firma de webhook inválida: %s ---", e)
        raise HTTPException(status_code=400, detail="Webhook Stripe inválido")

    event_type = event.get("type")
    event_data = ((event.get("data") or {}).get("object") or {})
    logger.info("--- [Stripe] Evento recibido: %s ---", event_type)

    if event_type in ("checkout.session.completed", "checkout.session.async_payment_succeeded"):
        metadata = event_data.get("metadata") or {}
        internal_session_id = metadata.get("session_id")
        checkout_session_id = event_data.get("id")
        stripe_payment_status = event_data.get("payment_status")
        target_sessions: List[str] = []
        target_sessions.extend(_candidate_session_ids(internal_session_id))
        target_sessions.extend(_find_sessions_by_checkout_id(checkout_session_id))
        # Deduplicar preservando orden
        deduped_targets: List[str] = []
        for sid in target_sessions:
            if sid and sid not in deduped_targets:
                deduped_targets.append(sid)

        for sid in deduped_targets:
            updated = _mark_payment_success_for_session(sid, checkout_session_id, stripe_payment_status)
            logger.info(
                "--- [Stripe] Pago confirmado para session_id=%s checkout_session_id=%s ---",
                sid,
                checkout_session_id,
            )

            if updated and sid.startswith("wa:"):
                phone = sid.replace("wa:", "", 1)
                if phone:
                    try:
                        await send_whatsapp_text(
                            phone,
                            "Pago de prueba confirmado correctamente. Tu solicitud queda registrada y pasamos al cierre final.",
                        )
                    except Exception as e:
                        logger.error("--- [Stripe] No se pudo enviar confirmación WhatsApp: %s ---", e, exc_info=True)

    if event_type in ("checkout.session.expired", "checkout.session.async_payment_failed"):
        metadata = event_data.get("metadata") or {}
        internal_session_id = metadata.get("session_id")
        checkout_session_id = event_data.get("id")
        target_sessions: List[str] = []
        target_sessions.extend(_candidate_session_ids(internal_session_id))
        target_sessions.extend(_find_sessions_by_checkout_id(checkout_session_id))
        deduped_targets: List[str] = []
        for sid in target_sessions:
            if sid and sid not in deduped_targets:
                deduped_targets.append(sid)
        for sid in deduped_targets:
            _mark_payment_failed_for_session(sid)
            logger.warning("--- [Stripe] Pago fallido/expirado para session_id=%s ---", sid)

    return {"status": "ok"}


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
