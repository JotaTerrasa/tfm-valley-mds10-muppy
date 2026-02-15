import json
import re
import os
import uuid
import copy
from typing import Dict, Any, Optional, TypedDict, Annotated
import operator
from langchain_core.language_models.base import BaseLanguageModel
from langgraph.graph import StateGraph, END
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import ValidationError
from app.utils.file_loader import load_file_content
from langdetect import detect

from app.schemas.structured_outputs import AgentState as PydanticAgentState
from app.tools.registry import get_tool_by_name

class GraphState(TypedDict):
    user_input: str
    chat_history: Annotated[list[BaseMessage], operator.add]
    structured_data: dict
    token_usage: dict
    metadata: dict

class StateMachineStrategy():
    def __init__(self, llm: Optional[BaseLanguageModel], tool_names: list, config: dict):
        self.config = config
        self.llm = llm
        
        print("--- [Estrategia State Machine] Inicializando... ---")

        self.tools_by_name = {}
        for name in tool_names:
            try:
                self.tools_by_name[name] = get_tool_by_name(name)
            except Exception as e:
                print(f"--- [Estrategia] ADVERTENCIA: No se pudo cargar la herramienta '{name}': {e} ---")
        
        self.agent_base_path = self.config.get('__agent_base_path__')
        if not self.agent_base_path:
            raise ValueError("La configuración del agente no contiene la clave '__agent_base_path__'.")

        self.sm_config = self.config.get("state_machine", {})
        self.nodes_config = self.sm_config.get("nodes", {})
        self.router_config = self.sm_config.get("router", {})
        self.initial_state_template = self.sm_config.get("initial_state", {})

        self.prompts = {}
        self.node_handlers = {}
        for node_name, node_config in self.nodes_config.items():
            self.prompts[node_name] = self._create_prompt_template(node_config["prompt_path"])
            self.node_handlers[node_name] = self._create_node_handler(node_name, node_config)
            print(f"--- [Estrategia] Nodo '{node_name}' configurado. ---")

        self.graph = self._build_graph()
        print("--- [Estrategia] Grafo construido y compilado con éxito. ---")

    def _create_prompt_template(self, prompt_path: str):
        full_prompt_path = os.path.join(self.agent_base_path, prompt_path)
        template = load_file_content(full_prompt_path)
        # Escape literal braces so .format() does not treat JSON in prompts as placeholders
        template = template.replace("{", "{{").replace("}", "}}")
        return ChatPromptTemplate.from_messages([("system", template), ("human", "{input}")])

    @staticmethod
    def _message_content_to_str(content) -> str:
        """Normalize LLM message content (str or list of blocks) to a single string for parsing."""
        if content is None:
            return ""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for block in content:
                if isinstance(block, str):
                    parts.append(block)
                elif isinstance(block, dict) and block.get("text"):
                    parts.append(block["text"])
                else:
                    parts.append(str(block))
            return "\n".join(parts) if parts else ""
        return str(content)

    def _parse_llm_output(self, raw_response_text: str) -> dict:
        raw_response_text = self._message_content_to_str(raw_response_text)
        # Nunca exponer pseudo-código interno de herramientas al usuario final.
        raw_response_text = re.sub(r"<tool_code>.*?</tool_code>", "", raw_response_text, flags=re.DOTALL | re.IGNORECASE).strip()
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', raw_response_text, re.DOTALL)
        user_facing_message = raw_response_text
        structured_data = {}
        if json_match:
            json_string = json_match.group(1)
            user_facing_message = raw_response_text[:json_match.start()].strip()
            try:
                structured_data = json.loads(json_string)
            except json.JSONDecodeError:
                print(f"--- ERROR: Bloque JSON inválido. ---")
        else:
            # Fallback: algunos modelos devuelven JSON en crudo al final (sin ```json).
            # Si encontramos un objeto JSON válido al final del texto, lo extraemos y no lo mostramos al usuario.
            decoder = json.JSONDecoder()
            text = raw_response_text.strip()
            for idx in range(len(text) - 1, -1, -1):
                if text[idx] != "{":
                    continue
                candidate = text[idx:]
                try:
                    parsed_obj, end = decoder.raw_decode(candidate)
                    if idx + end == len(text) and isinstance(parsed_obj, dict):
                        structured_data = parsed_obj
                        user_facing_message = text[:idx].strip()
                        break
                except json.JSONDecodeError:
                    continue
        return {"user_facing_message": user_facing_message or " ", "structured_data": structured_data}

    def _run_llm_and_update_state(self, state: GraphState, prompt_template: ChatPromptTemplate, node_tools: list) -> dict:
        print(f"--- [LLM Call] Usando prompt para el nodo actual con {len(node_tools)} herramientas específicas. ---")

        llm_with_tools = self.llm.bind_tools(node_tools) if node_tools else self.llm

        def json_converter(o):
            import datetime
            if isinstance(o, (datetime.date, datetime.datetime)):
                return o.isoformat()
            return str(o)

        history_str = "\n".join([f"{msg.type}: {self._message_content_to_str(msg.content)}" for msg in state['chat_history']])
        lang_lock = (state.get('structured_data') or {}).get('lang_lock') or 'es'
        language_instruction = (
            "Instrucción de idioma: Responde SIEMPRE en español. No cambies de idioma."
            if lang_lock == 'es' else
            "Language instruction: Always respond in English. Do not switch languages."
        )
        input_for_llm = (
            f"Historial:\n{history_str}\n\n"
            f"Input del Usuario: \"{state['user_input']}\"\n\n"
            f"Estado JSON actual:\n{json.dumps(state['structured_data'], indent=2, default=json_converter)}"
        )
        
        system_prompt = prompt_template.format_messages(input=input_for_llm)
        language_system_message = SystemMessage(content=language_instruction)
        final_messages_for_llm = [language_system_message] + system_prompt + [HumanMessage(content=state['user_input'])]
        
        try:
            raw_response = llm_with_tools.invoke(final_messages_for_llm)
        except Exception as e:
            # Algunos proveedores fallan en validación de schema de tools (p.ej. argumentos null).
            # Fallback robusto: reintentar sin tools para no romper la petición del usuario.
            print(f"--- [LLM Call] Error con tools ({e}). Reintentando sin tools. ---")
            raw_response = self.llm.invoke(final_messages_for_llm)

        tool_messages = []
        if node_tools and raw_response.tool_calls:
            print(f"--- [Agente] El LLM ha decidido usar una herramienta: {raw_response.tool_calls} ---")
            tools_by_name = {t.name: t for t in node_tools}
            for tc in raw_response.tool_calls:
                _name = tc.get("name", None) if isinstance(tc, dict) else getattr(tc, "name", None)
                _args = tc.get("args", {}) if isinstance(tc, dict) else getattr(tc, "args", {}) or {}
                _id = tc.get("id", "") if isinstance(tc, dict) else getattr(tc, "id", "")
                name = _name
                if not name or name not in tools_by_name:
                    tool_messages.append(
                        ToolMessage(content=f"Error: herramienta '{name}' no encontrada.", tool_call_id=_id, name=name or "unknown")
                    )
                    continue
                tool = tools_by_name[name]
                try:
                    result = tool.invoke(_args)
                    content = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False, default=str)
                except Exception as e:
                    content = json.dumps({"error": str(e)}, ensure_ascii=False)
                tool_messages.append(ToolMessage(content=content, tool_call_id=_id, name=name))
            print("--- [Agente] Re-invocando LLM con el resultado de la herramienta... ---")
            try:
                final_response = llm_with_tools.invoke(final_messages_for_llm + [raw_response] + tool_messages)
            except Exception as e:
                print(f"--- [LLM Call] Error al re-invocar con tools ({e}). Usando fallback sin tools. ---")
                final_response = self.llm.invoke(final_messages_for_llm + [raw_response] + tool_messages)
            response_content = final_response.content
            final_raw_response_for_parsing = final_response
        else:
            response_content = raw_response.content
            final_raw_response_for_parsing = raw_response

        response_content = self._message_content_to_str(response_content)
        parsed_output = self._parse_llm_output(response_content)
        # Si el LLM devolvió vacío tras una herramienta (p. ej. calculate_quote), formatear fallback desde el resultado
        if tool_messages and (not parsed_output["user_facing_message"] or not parsed_output["user_facing_message"].strip()):
            last_tool = tool_messages[-1]
            content = getattr(last_tool, "content", None) or ""
            if isinstance(content, str) and content.strip():
                try:
                    tool_result = json.loads(content)
                    if isinstance(tool_result, dict) and "annual_premium" in tool_result and "error" not in tool_result:
                        msg = f"Tu cotización: **{tool_result.get('annual_premium')}** {tool_result.get('currency', 'EUR')} anuales"
                        if tool_result.get("monthly_premium"):
                            msg += f" ({tool_result['monthly_premium']} EUR/mes)."
                        else:
                            msg += "."
                        # Preferir coberturas del RAG (base de conocimientos) si están presentes
                        coberturas_rag = tool_result.get("coberturas_rag")
                        if coberturas_rag and isinstance(coberturas_rag, str) and coberturas_rag.strip() and "No se encontró" not in coberturas_rag:
                            msg += " " + coberturas_rag.strip()[:600]
                            if len(coberturas_rag) > 600:
                                msg += "..."
                        elif tool_result.get("coberturas_incluidas"):
                            msg += " Coberturas: " + ", ".join(tool_result["coberturas_incluidas"][:6]) + "."
                        parsed_output["user_facing_message"] = msg
                except (json.JSONDecodeError, TypeError):
                    pass
        print(f'--- [Traza Agente] Respuesta para el usuario: {parsed_output["user_facing_message"]} ---')

        token_usage = {}
        if hasattr(final_raw_response_for_parsing, 'usage_metadata') and final_raw_response_for_parsing.usage_metadata:
            token_usage = {
                "input_tokens": final_raw_response_for_parsing.usage_metadata.get("input_tokens", 0),
                "output_tokens": final_raw_response_for_parsing.usage_metadata.get("output_tokens", 0),
            }
        
        new_structured_data = self._merge_structured_data(state.get("structured_data", {}), parsed_output.get("structured_data", {}))
        try:
            PydanticAgentState.model_validate(new_structured_data)
        except ValidationError as e:
            new_structured_data["validation_error"] = str(e)

        return {
            "structured_data": new_structured_data, 
            "chat_history": [AIMessage(content=parsed_output["user_facing_message"])],
            "token_usage": token_usage
        }

    @staticmethod
    def _deep_merge_dict(base: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
        """Merge nested dictionaries without dropping existing subkeys."""
        result = copy.deepcopy(base)
        for key, value in (incoming or {}).items():
            if isinstance(value, dict) and isinstance(result.get(key), dict):
                result[key] = StateMachineStrategy._deep_merge_dict(result[key], value)
            else:
                result[key] = value
        return result

    def _merge_structured_data(self, current: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
        if not incoming:
            return copy.deepcopy(current or {})
        return self._deep_merge_dict(current or {}, incoming)

    @staticmethod
    def _reset_for_triage(structured_data: Dict[str, Any]) -> None:
        """Reset transient flow fields when forcing a return to triage."""
        structured_data["next_agent"] = None
        structured_data["route"] = "triage"
        structured_data["datos_completos"] = False
        structured_data["pending_field"] = None
        structured_data["invalid_reason"] = None
        structured_data["ready_for_commit"] = False
        structured_data["missing_fields"] = []
        structured_data["payment_link"] = None
        structured_data["payment_status"] = "pending"
    
    def _create_node_handler(self, node_name: str, node_config: dict):
        """Crea una función handler para un nodo específico usando clausuras."""
        def handler(state: GraphState) -> dict:
            print(f"--- [Estado] Ejecutando nodo dinámico: {node_name} ---")
            tool_names = node_config.get("available_tools", [])
            node_tools = [self.tools_by_name[name] for name in tool_names if name in self.tools_by_name]
            prompt = self.prompts[node_name]
            return self._run_llm_and_update_state(state, prompt, node_tools)
        return handler

    def entry_point_router(self, state: GraphState) -> str:
        """Enrutador genérico con guardrail inteligente para validación según tipo de flujo."""
        routing_field = self.router_config.get("field", "route")
        routing_map = self.router_config.get("map", {})
        default_node = self.router_config.get("default_node")

        if not default_node:
            raise ValueError("El campo 'default_node' es obligatorio en la configuración del router.")

        structured_data = state.get("structured_data", {})
        current_value = structured_data.get(routing_field)
        user_input = (state.get("user_input") or "").lower()
        history_text = " ".join(
            self._message_content_to_str(msg.content).lower()
            for msg in (state.get("chat_history") or [])
            if getattr(msg, "type", "") == "human"
        )
        combined_text = f"{history_text} {user_input}"
        has_claim_id = re.search(r"\bclm[-_ ]?\d", combined_text, flags=re.IGNORECASE) is not None
        has_policy_number = re.search(r"\bmap-[a-z]+-\w+-\d+\b", combined_text, flags=re.IGNORECASE) is not None

        # Clasificador determinista de tópico para soporte (evita bucles de handoff).
        claims_markers = ("siniestro", "claim", "parte", "golpe", "accidente", "avería", "averia", "incidente")
        billing_markers = ("factur", "recibo", "pago", "cargo", "cuota")
        policy_change_markers = ("renovar", "cancelar")
        update_markers = ("actualizar", "modificar", "cambiar")
        update_fields = ("email", "correo", "telefono", "teléfono", "dirección", "direccion", "contacto")
        policy_markers = ("póliza", "poliza", "cobertura")

        if current_value == "soporte":
            structured_data["route"] = "support"
            current_value = "support"

        if current_value in ("support", "soporte", "human_handoff"):
            if has_claim_id or any(k in combined_text for k in claims_markers):
                structured_data["route"] = "claims"
            elif any(k in combined_text for k in billing_markers):
                structured_data["route"] = "billing"
            elif (
                any(k in combined_text for k in policy_change_markers)
                or (
                    any(k in combined_text for k in ("cambiar", "modificar", "ampliar"))
                    and any(k in combined_text for k in ("póliza", "poliza", "cobertura", "coberturas"))
                )
            ):
                structured_data["route"] = "policy_change"
            elif any(k in combined_text for k in update_markers) and any(k in combined_text for k in update_fields):
                structured_data["route"] = "update_data"
            elif has_policy_number or any(k in combined_text for k in policy_markers):
                structured_data["route"] = "policy_lookup"
            current_value = structured_data.get(routing_field)

        # Escape hatch para soporte: si está en soporte/human_handoff y el usuario trae
        # una petición operativa, re-enrutar al subflujo adecuado.
        if current_value in ("support", "soporte", "human_handoff") and "support" in routing_map:
            if any(k in user_input for k in ("siniestro", "claim", "parte", "golpe", "accidente", "avería", "averia")):
                structured_data["route"] = "claims"
            elif any(k in user_input for k in ("factur", "recibo", "pago")):
                structured_data["route"] = "billing"
            elif any(k in user_input for k in ("cambiar póliza", "cambiar poliza", "renovar", "cancelar")):
                structured_data["route"] = "policy_change"
            elif ("actualizar" in user_input or "modificar" in user_input) and any(
                k in user_input for k in ("email", "correo", "telefono", "teléfono", "dirección", "direccion", "contacto")
            ):
                structured_data["route"] = "update_data"
            elif any(k in user_input for k in ("póliza", "poliza", "cobertura")):
                structured_data["route"] = "policy_lookup"
            current_value = structured_data.get(routing_field)

        # Retroceso explícito del usuario: forzar vuelta a triage sin romper el contexto útil.
        backtrack_markers = ("volver", "atrás", "atras", "cambiar", "corregir", "me equivoqué", "me equivoque")
        if current_value != "triage" and any(marker in user_input for marker in backtrack_markers):
            print("--- [Router] Detección de retroceso/corrección. Volviendo a triage. ---")
            self._reset_for_triage(structured_data)
            return default_node
        
        # GUARDRAIL INTELIGENTE: Validación según tipo de flujo
        next_agent = structured_data.get("next_agent")
        intent = structured_data.get("intent")
        cliente_id = structured_data.get("cliente_id")
        tipo_seguro = structured_data.get("tipo_seguro")
        datos_completos = structured_data.get("datos_completos", False)
        requiere_cliente_id = structured_data.get("requiere_cliente_id", False)
        
        # Si el LLM intenta derivar a otro agente, validar según el flujo
        if next_agent and next_agent != "null" and next_agent != default_node:
            
            # FLUJO 1: Cotizar/Contratar - Solo requiere tipo_seguro
            if intent in ["cotizar", "contratar"]:
                if not tipo_seguro:
                    print(f"--- [GUARDRAIL] BLOQUEO: Intento de derivar a '{next_agent}' sin tipo_seguro. ---")
                    print(f"    Intent: {intent}, tipo_seguro: {tipo_seguro}")
                    self._reset_for_triage(state["structured_data"])
                    return default_node
            
            # FLUJO 2: Soporte - Requiere cliente_id + tipo_seguro
            elif intent == "soporte" or requiere_cliente_id:
                if not cliente_id or not tipo_seguro:
                    print(f"--- [GUARDRAIL] BLOQUEO: Intento de derivar a soporte sin datos completos. ---")
                    print(f"    cliente_id: {cliente_id}, tipo_seguro: {tipo_seguro}, requiere_cliente_id: {requiere_cliente_id}")
                    self._reset_for_triage(state["structured_data"])
                    return default_node

        if current_value and current_value not in routing_map:
            print(f"--- [Router] ADVERTENCIA: ruta inválida '{current_value}'. Usando nodo por defecto '{default_node}'. ---")
        destination = routing_map.get(current_value, default_node)
        print(f"--- [Router] Campo: '{routing_field}', Valor: '{current_value}', Intent: '{intent}'. Próximo nodo: '{destination}' ---")
        
        # Validación adicional: solo permitir salir de triage si datos_completos es true
        if destination != default_node and current_value == "triage":
            if not datos_completos:
                print(f"--- [GUARDRAIL] Datos incompletos (datos_completos=False). Forzando permanencia en triage. ---")
                destination = default_node
        
        return destination

    def _build_graph(self) -> StateGraph:
        """Construye el grafo de LangGraph de forma dinámica."""
        workflow = StateGraph(GraphState)
        
        for node_name, handler_func in self.node_handlers.items():
            workflow.add_node(node_name, handler_func)
            workflow.add_edge(node_name, END)
            
        all_nodes = list(self.nodes_config.keys())
        workflow.set_conditional_entry_point(
            self.entry_point_router,
            {node_name: node_name for node_name in all_nodes}
        )
        
        return workflow.compile()

    async def invoke(self, user_input: str, memory, metadata: Optional[Dict[str, Any]] = None):
        metadata = metadata or {}
        current_structured_data = metadata.get("current_state", {})

        if not current_structured_data:
            print("--- [Estado] No se encontró estado previo. Inicializando desde plantilla de configuración. ---")
            current_structured_data = self.initial_state_template.copy()
            current_structured_data["id"] = metadata.get("session_id") or getattr(memory.chat_memory, "session_id", None) or str(uuid.uuid4())

        # Detección de idioma
        try:
            if not current_structured_data.get("lang_lock"):
                detected = 'es'
                try:
                    detected = detect(user_input or "") or 'es'
                except Exception:
                    detected = 'es'
                normalized = 'en' if detected.startswith('en') else 'es'
                current_structured_data.setdefault("ISO", normalized)
                current_structured_data.setdefault("lang_lock", normalized)
        except Exception:
            pass

        initial_graph_state = {
            "user_input": user_input,
            "chat_history": memory.chat_memory.messages,
            "structured_data": current_structured_data,
            "token_usage": {},
            "metadata": metadata
        }
        
        final_state = await self.graph.ainvoke(initial_graph_state)

        final_ai_message = final_state["chat_history"][-1]
        memory.chat_memory.add_user_message(user_input)
        memory.chat_memory.add_ai_message(final_ai_message.content)

        return {
            "output": final_ai_message.content,
            "chat_history": memory.chat_memory.messages,
            "structured_data": final_state["structured_data"],
            "token_usage": final_state.get("token_usage", {}),
            "raw_agent_response": (f"{final_ai_message.content}\n\n```json\n"
                               f"{json.dumps(final_state['structured_data'], indent=2)}\n```")
        }
