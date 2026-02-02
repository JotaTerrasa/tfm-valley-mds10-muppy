import json
import re
import os
import pydantic
from typing import Dict, Optional, Any

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from app.utils.file_loader import load_file_content
from app.schemas.structured_outputs import FinalAnswer, AgentState

class GenerativeStrategy:
    def __init__(self, llm, tools, config):
        self.llm = llm
        self.config = config
        self.prompt_template = self._create_prompt_template()
        
    def _create_prompt_template(self):
        agent_base_path = self.config.get('__agent_base_path__')
        prompt_path = self.config.get('prompt_path')
        if agent_base_path and prompt_path:
            full_prompt_path = os.path.join(agent_base_path, prompt_path)
        else:
            full_prompt_path = prompt_path
        template = load_file_content(full_prompt_path)
        return ChatPromptTemplate.from_messages([
            ("system", template),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ])

    def _parse_and_validate_output(self, raw_response_text: str, session_id: str) -> dict:
        """
        Parsea y valida la salida del LLM, extrayendo JSON estructurado si existe.
        """
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', raw_response_text, re.DOTALL)
        user_facing_message = raw_response_text
        structured_data = {}

        if json_match:
            json_string = json_match.group(1)
            user_facing_message = raw_response_text[:json_match.start()].strip()
            
            try:
                data = json.loads(json_string)
                data['id'] = session_id
                
                status = data.get("status")

                if status == "new":
                    print("--- Validando contra el esquema FinalAnswer (status='new'). ---")
                    validated_data = FinalAnswer.model_validate(data)
                else:
                    print("--- Validando contra el esquema AgentState (status='incomplete'). ---")
                    validated_data = AgentState.model_validate(data)
                
                structured_data = validated_data.model_dump(exclude_unset=True, mode='json')
                print("--- ¡ÉXITO! JSON parseado y validado con Pydantic. ---")

            except pydantic.ValidationError as e:
                print(f"--- ERROR DE VALIDACIÓN Pydantic: {e} ---")
                first_error = e.errors()[0]
                error_field = ".".join(map(str, first_error['loc'])) if first_error['loc'] else 'unknown'
                error_message = first_error['msg']
                structured_data = {"validation_error": f"Error en el campo '{error_field}': {error_message}"}
            except json.JSONDecodeError:
                print("--- ERROR: Bloque JSON inválido. ---")
                structured_data = {"validation_error": "El formato del JSON es inválido."}
        else:
            print("--- INFO: No se encontró un bloque JSON en la respuesta. ---")
            
        return {
            "user_facing_message": user_facing_message or " ",
            "structured_data": structured_data
        }

    async def invoke(self, user_input: str, memory, metadata: Optional[Dict[str, Any]] = None):
        print("--- Estrategia de Invocación con Validación Post-hoc ---")
        
        llm_to_call = self.llm

        metadata = metadata or {}
        ani = metadata.get("ani", "no_disponible")
        session_id = memory.chat_memory.session_id

        print(f"--- Inyectando en prompt: session_id='{session_id}', ani='{ani}' ---")

        prompt_messages = self.prompt_template.format_messages(
            input=user_input,
            history=memory.chat_memory.messages,
            session_id=session_id,
            ani=ani
        )
        
        print("--- Realizando llamada única al LLM... ---")
        ai_response = await llm_to_call.ainvoke(prompt_messages)
        raw_response_text = ai_response.content
        print("--- LLM respondió. ---")

        token_usage = {}
        if hasattr(ai_response, 'usage_metadata') and ai_response.usage_metadata:
            token_usage = {
                "input_tokens": ai_response.usage_metadata.get("input_tokens", 0),
                "output_tokens": ai_response.usage_metadata.get("output_tokens", 0),
            }
        elif hasattr(ai_response, 'response_metadata') and ai_response.response_metadata.get('token_usage'):
            usage = ai_response.response_metadata['token_usage']
            token_usage = {
                "input_tokens": usage.get("prompt_tokens", 0),
                "output_tokens": usage.get("completion_tokens", 0),
            }
        
        session_id = memory.chat_memory.session_id
        parsed_output = self._parse_and_validate_output(raw_response_text, session_id)

        if "validation_error" in parsed_output["structured_data"]:
            print("--- ¡Error de validación detectado! Iniciando autocorrección. ---")
            error_details = parsed_output["structured_data"]["validation_error"]
            
            correction_prompt = f"""
            El usuario ha proporcionado unos datos que han resultado en un error de validación interno. 
            Tu tarea es explicarle el problema de forma amable y pedagógica, y pedirle que lo corrija.
            No menciones que es un "error de validación". Simplemente explica el problema y pide el dato de nuevo.

            Error técnico detectado: "{error_details}"

            Responde directamente al usuario.
            """
            
            correction_response = await llm_to_call.ainvoke([HumanMessage(content=correction_prompt)])
            parsed_output["user_facing_message"] = correction_response.content

        await memory.chat_memory.aadd_messages([
            HumanMessage(content=user_input),
            AIMessage(content=parsed_output["user_facing_message"])
        ])

        return {
            "chat_history": memory.chat_memory.messages,
            "structured_data": parsed_output["structured_data"],
            "raw_agent_response": raw_response_text,
            "output": parsed_output["user_facing_message"],
            "token_usage": token_usage
        }
