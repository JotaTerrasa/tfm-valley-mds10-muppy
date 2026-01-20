import json
import re
import os
import uuid
from typing import Dict, Any, Optional, TypedDict, Annotated
import operator
from langchain_core.language_models.base import BaseLanguageModel
from langgraph.graph import StateGraph, END
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import ValidationError
from utils.file_loader import load_file_content
from langgraph.prebuilt import ToolNode
from langdetect import detect

from schemas.structured_outputs import AgentState as PydanticAgentState
from tools.registry import get_tool_by_name

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
        return ChatPromptTemplate.from_messages([("system", template), ("human", "{input}")])

    def _parse_llm_output(self, raw_response_text: str) -> dict:
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
        return {"user_facing_message": user_facing_message or " ", "structured_data": structured_data}

    def _run_llm_and_update_state(self, state: GraphState, prompt_template: ChatPromptTemplate, node_tools: list) -> dict:
        print(f"--- [LLM Call] Usando prompt para el nodo actual con {len(node_tools)} herramientas específicas. ---")

        llm_with_tools = self.llm.bind_tools(node_tools) if node_tools else self.llm

        def json_converter(o):
            import datetime
            if isinstance(o, (datetime.date, datetime.datetime)):
                return o.isoformat()
            return str(o)

        history_str = "\n".join([f"{msg.type}: {msg.content}" for msg in state['chat_history']])
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
        
        raw_response = llm_with_tools.invoke(final_messages_for_llm)

        if node_tools and raw_response.tool_calls:
            print(f"--- [Agente] El LLM ha decidido usar una herramienta: {raw_response.tool_calls} ---")
            tool_node = ToolNode(tools=node_tools)
            tool_messages = tool_node.invoke([raw_response])

            print("--- [Agente] Re-invocando LLM con el resultado de la herramienta... ---")
            final_response = llm_with_tools.invoke(final_messages_for_llm + [raw_response] + tool_messages)
            response_content = final_response.content
            final_raw_response_for_parsing = final_response
        else:
            response_content = raw_response.content
            final_raw_response_for_parsing = raw_response

        parsed_output = self._parse_llm_output(response_content)
        print(f'--- [Traza Agente] Respuesta para el usuario: {parsed_output["user_facing_message"]} ---')

        token_usage = {}
        if hasattr(final_raw_response_for_parsing, 'usage_metadata') and final_raw_response_for_parsing.usage_metadata:
            token_usage = {
                "input_tokens": final_raw_response_for_parsing.usage_metadata.get("input_tokens", 0),
                "output_tokens": final_raw_response_for_parsing.usage_metadata.get("output_tokens", 0),
            }
        
        new_structured_data = state['structured_data'].copy()
        new_structured_data.update(parsed_output["structured_data"])
        try:
            PydanticAgentState.model_validate(new_structured_data)
        except ValidationError as e:
            new_structured_data["validation_error"] = str(e)

        return {
            "structured_data": new_structured_data, 
            "chat_history": [AIMessage(content=parsed_output["user_facing_message"])],
            "token_usage": token_usage
        }
    
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
        """Enrutador genérico que lee su lógica desde la configuración."""
        routing_field = self.router_config.get("field", "route")
        routing_map = self.router_config.get("map", {})
        default_node = self.router_config.get("default_node")

        if not default_node:
            raise ValueError("El campo 'default_node' es obligatorio en la configuración del router.")

        current_value = state.get("structured_data", {}).get(routing_field)
        destination = routing_map.get(current_value, default_node)
        print(f"--- [Router] Campo: '{routing_field}', Valor: '{current_value}'. Próximo nodo: '{destination}' ---")

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
            current_structured_data["id"] = memory.chat_memory.session_id or str(uuid.uuid4())

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
